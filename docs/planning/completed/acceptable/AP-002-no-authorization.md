# AP-002: No Authorization/RBAC

## Status: OPEN - Depends on AP-001

## Priority: High (after AP-001 is resolved)

---

## Current State

| Dependency | Status |
|------------|--------|
| Authentication (AP-001) | ❌ Not implemented |
| Authorization/RBAC | ❌ Not implemented |

**Location**: `src/api/app.py` - No role checks on any endpoint

---

## The Problem

Even after authentication is added, there's no mechanism to control **what** authenticated users can do:

- All authenticated users have identical permissions
- No admin vs regular user distinction
- No way to restrict access to sensitive operations
- No audit trail of who did what

---

## Do You Need RBAC?

### You DON'T need RBAC if:

- Single user or small team (< 5 people)
- Everyone should have the same access
- No sensitive admin operations
- Internal tool only

### You DO need RBAC if:

- Multiple user tiers (free/paid, viewer/editor/admin)
- Compliance requirements (SOC 2, HIPAA)
- Need to restrict who can start research vs view results
- Plan to add admin panel or user management

---

## Option Analysis

### Option 1: No RBAC (Acceptable for Now)

**How it works**: All authenticated users have full access.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | None |
| **Security** | Acceptable for internal tools |
| **Scalability** | Limited |
| **Maintenance** | Zero |

**When to use**: Internal tools, single-user, MVP stage

---

### Option 2: Simple Role-Based (Recommended if Needed)

**How it works**: Users have a role field, endpoints check role.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Low - 4-8 hours |
| **Security** | Good for most apps |
| **Scalability** | Good |
| **Maintenance** | Low |

**Roles**:

| Role | Permissions |
|------|-------------|
| `viewer` | Read research results only |
| `researcher` | Start research + view results |
| `admin` | All operations + user management |

```python
# Implementation sketch
from enum import Enum
from functools import wraps

class Role(str, Enum):
    VIEWER = "viewer"
    RESEARCHER = "researcher"
    ADMIN = "admin"

def require_roles(*allowed_roles: Role):
    """Decorator to restrict endpoint access by role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{current_user.role}' not authorized for this action"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/api/v1/research")
@require_roles(Role.RESEARCHER, Role.ADMIN)
async def start_research(request: ResearchRequest):
    ...

@app.get("/api/v1/research/{task_id}")
@require_roles(Role.VIEWER, Role.RESEARCHER, Role.ADMIN)
async def get_results(task_id: str):
    ...

@app.delete("/api/v1/users/{user_id}")
@require_roles(Role.ADMIN)
async def delete_user(user_id: str):
    ...
```

---

### Option 3: Permission-Based (Fine-Grained)

**How it works**: Users have specific permissions, not roles.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Medium - 1-2 days |
| **Security** | Excellent granularity |
| **Scalability** | Excellent |
| **Maintenance** | Higher |

**Permissions**:

```python
class Permission(str, Enum):
    RESEARCH_CREATE = "research:create"
    RESEARCH_READ = "research:read"
    RESEARCH_DELETE = "research:delete"
    USERS_MANAGE = "users:manage"
    SETTINGS_EDIT = "settings:edit"
```

**When to use**: Complex apps with many distinct operations

---

### Option 4: Attribute-Based (ABAC)

**How it works**: Access based on user attributes, resource attributes, and context.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | High - 3-5 days |
| **Security** | Maximum flexibility |
| **Scalability** | Excellent |
| **Maintenance** | High |

**Example rules**:

- "User can only view research they created"
- "Premium users can run unlimited research"
- "Users can only access research for their department"

**When to use**: Enterprise apps with complex access rules

---

## Decision Matrix

| Criteria | No RBAC | Simple Roles | Permissions | ABAC |
|----------|---------|--------------|-------------|------|
| Implementation Time | 0 | 4-8 hours | 1-2 days | 3-5 days |
| Granularity | None | Coarse | Fine | Maximum |
| Complexity | None | Low | Medium | High |
| Multi-tenant Ready | ❌ | ⚠️ | ✅ | ✅ |
| Fits Current Use Case | ✅ | ⚠️ | ❌ | ❌ |

---

## Recommendation

### For Now: **Defer / No RBAC**

**Rationale**:

1. AP-001 (Authentication) must be solved first
2. Current use case is single-user / small team
3. All endpoints do similar operations (research)
4. No admin panel or user management exists
5. Adding complexity without need is wasteful

### When to Revisit

Implement Simple Roles (Option 2) when:

- Adding user management features
- Multiple customers/tenants
- Need viewer-only access for stakeholders
- Compliance audit requires it

---

## Implementation Checklist (When Ready)

If you choose **Simple Roles**:

- [ ] Add `role` field to User model
- [ ] Create `require_roles` decorator
- [ ] Apply decorator to endpoints
- [ ] Add role to JWT token claims
- [ ] Create admin endpoint to change user roles
- [ ] Add audit logging for role changes
- [ ] Update API documentation

---

## References

- [FastAPI Dependencies for Auth](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)
- [Role-Based Access Control Patterns](https://auth0.com/docs/manage-users/access-control/rbac)

---

## Related Issues

- [AP-001](AP-001-no-authentication.md) - Authentication (prerequisite)
