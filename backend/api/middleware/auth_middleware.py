"""
Authentication Middleware - Simple role validation for API endpoints
NO TOKENS, NO PASSWORDS - Just role-based access control
"""
from fastapi import Header, HTTPException, status, Depends
from services.auth_service import AuthService, UserRole

auth_service = AuthService()


async def get_current_user(x_user_role: str = Header(..., description="User role header")) -> dict:
    """
    Get current user from role header.
    Simplified: No tokens, just pass role in header.
    
    Args:
        x_user_role: Role from X-User-Role header
    
    Returns:
        User object with role information
    
    Raises:
        HTTPException: If role is invalid
    """
    # Validate role
    if not UserRole.is_valid_role(x_user_role):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid role. Must be one of: {', '.join(UserRole.all_roles())}"
        )
    
    # Return a simple user object with the role
    return {
        "user_id": "SIMPLE-USER",
        "username": "stakeholder",
        "role": x_user_role,
        "name": x_user_role.replace('_', ' ').title(),
        "assigned_locations": []
    }


def require_role(allowed_roles: list):
    """
    Dependency factory for role-based access
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
    
    Returns:
        Dependency function that checks user role
    """
    async def check_role(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return user
    return check_role


# Role-specific dependencies for convenience
require_admin = require_role([UserRole.ADMIN])
require_business = require_role([UserRole.BUSINESS, UserRole.ADMIN])
require_warehouse_manager = require_role([UserRole.WAREHOUSE_MANAGER, UserRole.ADMIN])
require_store_manager = require_role([UserRole.STORE_MANAGER, UserRole.ADMIN])
require_logistics_manager = require_role([UserRole.LOGISTICS_MANAGER, UserRole.ADMIN])


def filter_by_location(user: dict, query: dict) -> dict:
    """
    Add location-based filtering to a query based on user's assigned locations
    
    Args:
        user: User object with assigned_locations
        query: Query dictionary to modify
    
    Returns:
        Modified query with location filter if applicable
    """
    if user.get("assigned_locations"):
        query["location_id"] = {"$in": user["assigned_locations"]}
    return query
