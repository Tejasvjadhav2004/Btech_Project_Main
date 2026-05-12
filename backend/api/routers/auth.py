"""
Authentication Router - Simple user management (no login, just role selection)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.auth_service import AuthService, UserRole
from api.middleware.auth_middleware import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
auth_service = AuthService()


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    username: str
    role: str
    name: str
    assigned_locations: Optional[List[str]] = []


class UpdateUserRequest(BaseModel):
    """Request model for updating a user"""
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_locations: Optional[List[str]] = None


@router.post("/users")
async def create_user(request: CreateUserRequest, current_user: dict = Depends(require_admin)):
    """
    Create a new user (Admin only) - no password required
    
    Args:
        request: User creation data
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        Created user information
    """
    if request.role not in UserRole.all_roles():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(UserRole.all_roles())}"
        )
    
    try:
        result = auth_service.create_user(
            username=request.username,
            role=request.role,
            name=request.name,
            assigned_locations=request.assigned_locations
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information (from header)
    
    Args:
        current_user: Current authenticated user from header
    
    Returns:
        Current user information
    """
    return current_user


@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """
    List all users (Admin only), optionally filtered by role
    
    Args:
        role: Optional role filter
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        List of users
    """
    # Validate role filter if provided
    if role and not UserRole.is_valid_role(role):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(UserRole.all_roles())}"
        )
    
    users = auth_service.list_users(role=role)
    return {"users": users, "count": len(users)}


@router.get("/users/{username}")
async def get_user(username: str, current_user: dict = Depends(require_admin)):
    """
    Get user by username (Admin only)
    
    Args:
        username: Username to lookup
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        User information
    """
    user = auth_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    return user


@router.put("/users/{username}")
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Update user information (Admin only)
    
    Args:
        username: Username to update
        request: Update data
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        Success status
    """
    # Validate role if being updated
    if request.role and not UserRole.is_valid_role(request.role):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(UserRole.all_roles())}"
        )
    
    # Check if user exists
    existing = auth_service.get_user_by_username(username)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    # Build updates dict
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.role is not None:
        updates["role"] = request.role
    if request.assigned_locations is not None:
        updates["assigned_locations"] = request.assigned_locations
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        updated = auth_service.update_user(existing["user_id"], updates)
        if updated:
            return {"message": f"User '{username}' updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update user")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/users/{username}")
async def deactivate_user(username: str, current_user: dict = Depends(require_admin)):
    """
    Deactivate a user (Admin only)
    
    Args:
        username: Username to deactivate
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        Success status
    """
    # Check if user exists
    existing = auth_service.get_user_by_username(username)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    deactivated = auth_service.deactivate_user(existing["user_id"])
    if deactivated:
        return {"message": f"User '{username}' deactivated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to deactivate user")


@router.post("/seed-default-users")
async def seed_default_users(current_user: dict = Depends(require_admin)):
    """
    Seed default users for each role if they don't exist (Admin only)
    
    Args:
        current_user: Current authenticated user (must be ADMIN)
    
    Returns:
        Seeding summary
    """
    result = auth_service.seed_default_users()
    return result


@router.get("/roles")
async def list_roles(current_user: dict = Depends(get_current_user)):
    """
    List all available roles
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        List of available roles
    """
    return {
        "roles": UserRole.all_roles(),
        "count": len(UserRole.all_roles())
    }
