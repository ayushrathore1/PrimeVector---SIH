"""
Tests for the audit log system.

Verifies that every policy configuration change produces the correct
audit trail — this is the code path a bank's compliance team will
inspect (DESIGN.md §4.8).

REVIEW FLAG: These tests and the audit module they test are flagged
for human review before merge.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from models import TenantPolicyUpdate
from store import TenantPolicyStore
from audit import AuditLog


def _fresh_store_and_log():
    """Return clean store and audit log for each test."""
    return TenantPolicyStore(), AuditLog()


# =====================================================================
# Audit entry generation
# =====================================================================

def test_threshold_change_produces_audit_entry():
    """Changing a threshold produces an audit entry with old/new values."""
    store, audit_log = _fresh_store_and_log()

    # Create default config
    store.get_or_create_default("bank-A")

    # Update callback threshold from 0.40 (default) to 0.60
    new_config, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.60),
        actor="admin@bank-a.com",
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.tenant_id == "bank-A"
    assert entry.actor == "admin@bank-a.com"
    assert entry.action == "UPDATE_THRESHOLD"
    assert entry.field_changed == "callback_verification_threshold"
    assert entry.old_value == "0.4"
    assert entry.new_value == "0.6"
    assert entry.timestamp is not None
    assert entry.entry_id  # UUID is present


def test_auto_block_toggle_produces_audit_entry():
    """Toggling auto_block_enabled produces an audit entry."""
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    _, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(auto_block_enabled=True),
        actor="ciso@bank-a.com",
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.action == "TOGGLE_AUTO_BLOCK"
    assert entry.field_changed == "auto_block_enabled"
    assert entry.old_value == "False"
    assert entry.new_value == "True"
    assert entry.actor == "ciso@bank-a.com"


def test_multiple_field_changes_produce_multiple_entries():
    """Changing multiple fields at once produces one entry per field."""
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    _, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(
            callback_verification_threshold=0.50,
            supervisor_escalation_threshold=0.80,
            auto_block_enabled=True,
        ),
        actor="admin@bank-a.com",
    )

    assert len(entries) == 3
    changed_fields = {e.field_changed for e in entries}
    assert changed_fields == {
        "callback_verification_threshold",
        "supervisor_escalation_threshold",
        "auto_block_enabled",
    }


def test_no_change_produces_no_audit_entry():
    """Setting a field to its current value produces no audit entry (no noise)."""
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    # Update with the same default values
    _, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.40),
        actor="admin@bank-a.com",
    )

    assert len(entries) == 0


def test_audit_entries_have_actor_and_timestamp():
    """Every audit entry must have actor identity and timestamp."""
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    _, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(block_threshold=0.85),
        actor="compliance-officer@bank-a.com",
    )

    for entry in entries:
        assert entry.actor == "compliance-officer@bank-a.com"
        assert entry.timestamp is not None


# =====================================================================
# Audit log append-only property
# =====================================================================

def test_audit_log_append_only():
    """
    Audit entries are append-only. The AuditLog class has no delete or
    update operations — this test verifies that entries accumulate and
    cannot be removed through the public API.
    """
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    _, entries1 = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.50),
        actor="admin1@bank-a.com",
    )
    for e in entries1:
        audit_log.append(e)

    _, entries2 = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.60),
        actor="admin2@bank-a.com",
    )
    for e in entries2:
        audit_log.append(e)

    all_entries = audit_log.get_entries(tenant_id="bank-A")
    assert len(all_entries) == 2
    assert all_entries[0].actor == "admin1@bank-a.com"
    assert all_entries[1].actor == "admin2@bank-a.com"

    # Verify no delete/update methods exist on AuditLog
    assert not hasattr(audit_log, "delete")
    assert not hasattr(audit_log, "update")
    assert not hasattr(audit_log, "remove")
    assert not hasattr(audit_log, "clear")


def test_audit_log_returns_copies():
    """
    get_entries returns a copy, so external mutation cannot corrupt
    the log.
    """
    _, audit_log = _fresh_store_and_log()
    store = TenantPolicyStore()
    store.get_or_create_default("bank-A")

    _, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.50),
        actor="admin@bank-a.com",
    )
    for e in entries:
        audit_log.append(e)

    result = audit_log.get_entries()
    result.clear()  # Mutate the returned list

    # Original log should be unaffected
    assert len(audit_log.get_entries()) == 1


# =====================================================================
# Policy versioning
# =====================================================================

def test_version_bumps_on_change():
    """Each actual change bumps the policy version."""
    store, _ = _fresh_store_and_log()
    config = store.get_or_create_default("bank-A")
    assert config.policy_version == 1

    new_config, _ = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.50),
        actor="admin@bank-a.com",
    )
    assert new_config.policy_version == 2

    new_config2, _ = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(supervisor_escalation_threshold=0.80),
        actor="admin@bank-a.com",
    )
    assert new_config2.policy_version == 3


def test_version_does_not_bump_on_no_change():
    """Version stays the same when no field actually changes."""
    store, _ = _fresh_store_and_log()
    store.get_or_create_default("bank-A")

    new_config, entries = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.40),  # same as default
        actor="admin@bank-a.com",
    )
    assert new_config.policy_version == 1  # unchanged
    assert len(entries) == 0


def test_audit_log_filters_by_tenant():
    """get_entries filters correctly by tenant_id."""
    store, audit_log = _fresh_store_and_log()
    store.get_or_create_default("bank-A")
    store.get_or_create_default("bank-B")

    _, entries_a = store.upsert_policy(
        "bank-A",
        TenantPolicyUpdate(callback_verification_threshold=0.50),
        actor="admin@bank-a.com",
    )
    for e in entries_a:
        audit_log.append(e)

    _, entries_b = store.upsert_policy(
        "bank-B",
        TenantPolicyUpdate(callback_verification_threshold=0.60),
        actor="admin@bank-b.com",
    )
    for e in entries_b:
        audit_log.append(e)

    assert len(audit_log.get_entries(tenant_id="bank-A")) == 1
    assert len(audit_log.get_entries(tenant_id="bank-B")) == 1
    assert len(audit_log.get_entries()) == 2
