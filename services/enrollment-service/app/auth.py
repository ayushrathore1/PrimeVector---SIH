from dataclasses import dataclass
from fastapi import Request, HTTPException, Depends

@dataclass
class AuthContext:
    actor_id: str
    actor_role: str
    tenant_id: str

async def require_tenant_admin(request: Request) -> AuthContext:
    actor_id = request.headers.get('X-Actor-Id')
    actor_role = request.headers.get('X-Actor-Role')
    tenant_id = request.headers.get('X-Tenant-Id')
    if not all([actor_id, actor_role, tenant_id]):
        raise HTTPException(status_code=401, detail='Missing auth headers')
    if actor_role != 'tenant_admin':
        raise HTTPException(status_code=403, detail='Only tenant admins can manage enrollments')
    return AuthContext(actor_id=actor_id, actor_role=actor_role, tenant_id=tenant_id)
