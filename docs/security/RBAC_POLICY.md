# Role-Based Access Control (RBAC) Security Policy

## Overview

Timeless Love implements comprehensive Role-Based Access Control (RBAC) to enforce security and permissions across all API endpoints. This document describes the RBAC implementation, security policies, and enforcement mechanisms.

## Architecture

### RBAC Components

1. **Permission Functions** (`app/services/rbac.py`): Core permission checking logic
2. **FastAPI Dependencies** (`app/dependencies/rbac.py`): Reusable dependencies for endpoint protection
3. **JWT Claims**: Role and family context embedded in authentication tokens
4. **Row Level Security (RLS)**: Database-level access control in Supabase

### Authentication Flow

1. User authenticates with Supabase Auth (email/password)
2. Backend validates Supabase token and issues custom JWT
3. Custom JWT includes:
   - `sub`: User ID
   - `role`: User role (adult, teen, child, grandparent, pet)
   - `family_unit_id`: User's family unit UUID
   - Standard JWT claims (iat, exp, jti, type)

4. All API requests include JWT in `Authorization: Bearer <token>` header
5. FastAPI dependencies validate token and extract user context
6. RBAC dependencies check permissions before allowing access

## Role Definitions

### Adult

**Full Permissions**: Complete access to all features and family management.

**Capabilities**:
- Create and manage family unit
- Invite family members (all roles)
- Provision child accounts
- Create pet profiles
- Full CRUD on all memories (own and family)
- Delete any content in family
- Manage family settings

**Restrictions**: None

### Teen

**Social Permissions**: Full social interactions, limited management.

**Capabilities**:
- View all family memories
- Create and edit own memories
- Delete own memories
- React and comment on memories
- View family members
- Update own profile

**Restrictions**:
- Cannot invite members
- Cannot provision children
- Cannot create pets
- Cannot delete others' content
- Cannot manage family settings

### Child

**Limited Permissions**: View and create with parental oversight.

**Capabilities**:
- View all family memories
- Create and edit own memories
- React and comment on memories
- View family members
- Limited profile updates

**Restrictions**:
- Cannot delete any content (including own)
- Cannot invite members
- Cannot provision children
- Cannot create pets
- Cannot manage family settings
- Cannot edit others' content

### Grandparent

**Adult-Like Permissions**: Similar to adult with accessibility focus.

**Capabilities**:
- Create and manage family unit
- Invite family members
- Create pet profiles
- Full CRUD on all memories
- Delete own content (not others')
- Manage family settings

**Restrictions**:
- Cannot provision child accounts (adults only)

### Pet

**Read-Only**: No active interactions, read-only access.

**Capabilities**:
- Appear in family member list
- Can be tagged in memories

**Restrictions**:
- Cannot authenticate
- Cannot create content
- Cannot react or comment
- Cannot edit or delete
- No active interactions

## Permission Matrix

### Family Management

| Operation | Adult | Teen | Child | Grandparent | Pet |
|-----------|-------|------|-------|-------------|-----|
| Create family | ✅ | ✅* | ❌ | ✅* | ❌ |
| Update family | ✅ | ❌ | ❌ | ✅ | ❌ |
| Invite members | ✅ | ❌ | ❌ | ✅ | ❌ |
| Provision children | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create pets | ✅ | ❌ | ❌ | ✅ | ❌ |

*Only if creating new family (first user)

### Content Management

| Operation | Adult | Teen | Child | Grandparent | Pet |
|-----------|-------|------|-------|-------------|-----|
| View memories | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create memory | ✅ | ✅ | ✅ | ✅ | ❌ |
| Edit own memory | ✅ | ✅ | ✅ | ✅ | ❌ |
| Edit any memory | ✅ | ❌ | ❌ | ✅ | ❌ |
| Delete own memory | ✅ | ✅ | ❌ | ✅ | ❌ |
| Delete any memory | ✅ | ❌ | ❌ | ❌ | ❌ |

### Interactions

| Operation | Adult | Teen | Child | Grandparent | Pet |
|-----------|-------|------|-------|-------------|-----|
| React to memory | ✅ | ✅ | ✅ | ✅ | ❌ |
| Create comment | ✅ | ✅ | ✅ | ✅ | ❌ |
| Edit own comment | ✅ | ✅ | ✅ | ✅ | ❌ |
| Delete own comment | ✅ | ✅ | ❌ | ✅ | ❌ |
| Delete any comment | ✅ | ❌ | ❌ | ✅ | ❌ |

## RBAC Dependencies

### Available Dependencies

All dependencies are in `app/dependencies/rbac.py`:

#### Role-Based Dependencies

- `require_roles(*allowed_roles)`: Require specific role(s)
- `require_adult`: Require adult role
- `require_adult_or_grandparent`: Require adult or grandparent role

#### Permission-Based Dependencies

- `require_family_manager`: Require role that can manage family
- `require_invite_permission`: Require role that can invite members
- `require_child_provision_permission`: Require role that can provision children
- `require_pet_creation_permission`: Require role that can create pets

#### Content-Based Dependencies

- `require_content_owner_or_adult`: Require ownership or adult role
- `require_content_editor`: Require permission to edit content
- `exclude_pets`: Exclude pet role (pets are read-only)

#### Family Access Dependencies

- `require_family_member(family_unit_id)`: Ensure user is in same family

### Usage Examples

```python
from app.dependencies.rbac import require_adult, exclude_pets

@router.post("/auth/provision-child")
async def provision_child(
    request: ChildProvisionRequest,
    current_user: TokenClaims = Depends(require_child_provision_permission)
):
    """Only adults can provision children."""
    ...

@router.post("/memories")
async def create_memory(
    request: CreateMemoryRequest,
    current_user: TokenClaims = Depends(exclude_pets)
):
    """Pets cannot create memories."""
    ...

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    memory: Memory = Depends(get_memory),
    current_user: TokenClaims = Depends(require_content_owner_or_adult)
):
    """Only owner or adult can delete."""
    ...
```

## Security Enforcement Layers

### 1. Endpoint Level (FastAPI Dependencies)

RBAC dependencies are applied at the endpoint level using FastAPI's dependency injection:

```python
@router.post("/endpoint")
async def endpoint(
    current_user: TokenClaims = Depends(require_adult)
):
    # Only adults can access this endpoint
    ...
```

**Benefits**:
- Centralized permission logic
- Reusable across endpoints
- Automatic error handling (403 Forbidden)
- Type-safe with FastAPI

### 2. Service Level (Business Logic)

Permission checks in service layer for complex operations:

```python
def can_delete_content(role: str, is_owner: bool) -> bool:
    if role == "adult":
        return True
    if role in ("teen", "grandparent") and is_owner:
        return True
    return False
```

**Benefits**:
- Fine-grained control
- Context-aware decisions
- Business logic separation

### 3. Database Level (Row Level Security)

Supabase RLS policies enforce family boundaries:

```sql
CREATE POLICY "Users can view memories in their family"
  ON memories FOR SELECT
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
  );
```

**Benefits**:
- Defense in depth
- Prevents data leakage
- Enforced at database level

## Security Considerations

### Role Escalation Prevention

1. **Role Immutability**: Roles are set during registration/invitation and cannot be self-modified
2. **Token Validation**: JWT tokens are validated on every request
3. **Role Verification**: Backend verifies role from database, not just token claims
4. **Audit Trail**: All role-sensitive operations are logged

### Family Boundary Enforcement

1. **Family Unit Validation**: All operations validate `family_unit_id` matches user's family
2. **Cross-Family Prevention**: Strict enforcement prevents cross-family access
3. **RLS Policies**: Database-level policies enforce family boundaries

### Token Security

1. **Short-Lived Access Tokens**: 15-minute expiration
2. **Refresh Token Rotation**: Server-side rotation on refresh
3. **Token Revocation**: Refresh tokens can be revoked
4. **Secure Storage**: Tokens stored securely (not in localStorage for production)

### Content Ownership

1. **Ownership Validation**: Content operations verify ownership
2. **Adult Override**: Adults can manage any content in their family
3. **Soft Deletes**: Comments use soft deletes to preserve thread structure

## Error Responses

### 401 Unauthorized

Returned when:
- Missing or invalid JWT token
- Expired token
- Malformed token

**Response**:
```json
{
  "detail": "Invalid or expired token: ..."
}
```

### 403 Forbidden

Returned when:
- User lacks required role
- User lacks required permission
- Access to different family unit
- Operation not allowed for role

**Response**:
```json
{
  "detail": "Operation requires adult role"
}
```

## Testing

### Unit Tests

Test permission functions in `backend/tests/test_rbac.py`:
- Permission matrix tests
- Role behavior tests
- Endpoint protection tests

### Integration Tests

Test RBAC enforcement on actual endpoints:
- Verify 403 responses for unauthorized roles
- Verify successful access for authorized roles
- Test family boundary enforcement

## Best Practices

1. **Always Use Dependencies**: Use RBAC dependencies instead of manual checks
2. **Defense in Depth**: Combine endpoint, service, and database-level checks
3. **Explicit Permissions**: Be explicit about required permissions
4. **Error Messages**: Provide clear error messages for permission denials
5. **Logging**: Log all permission checks and denials
6. **Testing**: Test all role combinations and edge cases

## Future Enhancements

1. **Role Hierarchies**: Support for role inheritance
2. **Custom Permissions**: Per-user custom permissions
3. **Temporary Permissions**: Time-limited permission grants
4. **Permission Delegation**: Allow users to delegate permissions
5. **Audit Dashboard**: UI for viewing permission audit logs

