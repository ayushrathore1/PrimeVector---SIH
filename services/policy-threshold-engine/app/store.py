"""
Versioned tenant policy store for the policy-threshold-engine.

Manages per-tenant policy configurations with version tracking.
Every mutation increments the policy_version and generates audit log
entries for each changed field, ensuring:
  1. Past assessments are not retroactively reinterpreted (the
     policy_version stamped on each PolicyDecision is immutable).
  2. Every change is auditable with actor identity, old/new values,
     and timestamp (DESIGN.md §4.8).

Implementation note: In-memory store for this reference implementation.
Production would use a database with the same interface.
"""

import threading
import uuid
from datetime import datetime, timezone

from models import TenantPolicyConfig, TenantPolicyUpdate, AuditLogEntry


# Fields that are auditable (i.e., policy config fields that can be changed
# by a tenant admin). Internal fields like policy_version and updated_at
# are managed by the store, not directly editable.
_AUDITABLE_FIELDS = [
    "callback_verification_threshold",
    "supervisor_escalation_threshold",
    "block_threshold",
    "auto_block_enabled",
]


class TenantPolicyStore:
    """
    In-memory versioned tenant policy store.

    Thread-safe. Every mutation bumps policy_version and returns audit
    entries for all changed fields.
    """

    def __init__(self) -> None:
        self._policies: dict[str, TenantPolicyConfig] = {}
        self._lock = threading.Lock()

    def get_policy(self, tenant_id: str) -> TenantPolicyConfig | None:
        """Return the current policy for a tenant, or None if not configured."""
        with self._lock:
            return self._policies.get(tenant_id)

    def get_or_create_default(self, tenant_id: str) -> TenantPolicyConfig:
        """
        Return the current policy for a tenant, creating a default one if
        none exists.

        The default policy has auto_block_enabled=False (load-bearing
        default per DESIGN.md §4.7).
        """
        with self._lock:
            if tenant_id not in self._policies:
                self._policies[tenant_id] = TenantPolicyConfig(
                    tenant_id=tenant_id,
                )
            return self._policies[tenant_id]

    def upsert_policy(
        self,
        tenant_id: str,
        updates: TenantPolicyUpdate,
        actor: str,
    ) -> tuple[TenantPolicyConfig, list[AuditLogEntry]]:
        """
        Apply partial updates to a tenant's policy configuration.

        Returns (new_config, audit_entries). The caller is responsible for
        persisting the audit entries via the AuditLog.

        Behaviour:
        - Creates a default policy if none exists for this tenant.
        - Only updates fields that are explicitly provided (not None) in
          the TenantPolicyUpdate.
        - Generates one AuditLogEntry per changed field (fields set to
          their current value are not logged — no noise).
        - Bumps policy_version on any actual change.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            audit_entries: list[AuditLogEntry] = []

            # Get or create existing config
            if tenant_id in self._policies:
                old_config = self._policies[tenant_id]
            else:
                old_config = TenantPolicyConfig(tenant_id=tenant_id)

            # Build updated config, tracking changes
            new_data = old_config.model_dump()
            update_data = updates.model_dump(exclude_none=True)

            for field_name in _AUDITABLE_FIELDS:
                if field_name not in update_data:
                    continue

                old_val = getattr(old_config, field_name)
                new_val = update_data[field_name]

                if old_val == new_val:
                    continue  # No actual change, don't log noise

                # Determine the audit action label
                if field_name == "auto_block_enabled":
                    action_label = "TOGGLE_AUTO_BLOCK"
                else:
                    action_label = "UPDATE_THRESHOLD"

                audit_entries.append(AuditLogEntry(
                    entry_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    actor=actor,
                    action=action_label,
                    field_changed=field_name,
                    old_value=str(old_val),
                    new_value=str(new_val),
                    timestamp=now,
                ))

                new_data[field_name] = new_val

            # Bump version only if something actually changed
            if audit_entries:
                new_data["policy_version"] = old_config.policy_version + 1
                new_data["updated_at"] = now

            new_config = TenantPolicyConfig(**new_data)
            self._policies[tenant_id] = new_config

            return new_config, audit_entries
