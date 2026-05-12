"""
Authentication Service - Simple role-based access control
NO PASSWORDS, NO JWT - Just role selection for stakeholders
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from db.connection import mongodb
import uuid
import logging

logger = logging.getLogger(__name__)


class UserRole:
    """User role constants"""
    BUSINESS = "BUSINESS"
    WAREHOUSE_MANAGER = "WAREHOUSE_MANAGER"
    STORE_MANAGER = "STORE_MANAGER"
    LOGISTICS_MANAGER = "LOGISTICS_MANAGER"
    ADMIN = "ADMIN"
    
    @classmethod
    def all_roles(cls) -> List[str]:
        """Get all valid roles"""
        return [
            cls.BUSINESS,
            cls.WAREHOUSE_MANAGER,
            cls.STORE_MANAGER,
            cls.LOGISTICS_MANAGER,
            cls.ADMIN
        ]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Check if role is valid"""
        return role in cls.all_roles()


class AuthService:
    """Handles simple role-based access - no passwords, just role selection"""
    
    def __init__(self):
        # Don't cache database reference - get it dynamically each time
        pass
    
    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()
    
    def create_user(self, username: str, role: str, name: str, 
                   assigned_locations: List[str] = None) -> Dict[str, Any]:
        """
        Create a new user (simple - no password)
        
        Args:
            username: Unique username
            role: User role (must be valid UserRole)
            name: Display name
            assigned_locations: Optional list of location IDs user can access
        
        Returns:
            Created user data
        """
        if not UserRole.is_valid_role(role):
            raise ValueError(f"Invalid role: {role}. Must be one of {UserRole.all_roles()}")
        
        # Check if username already exists
        existing = self.db.users.find_one({"username": username})
        if existing:
            raise ValueError(f"Username '{username}' already exists")
        
        user_id = f"USER-{uuid.uuid4().hex[:8].upper()}"
        user = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "name": name,
            "assigned_locations": assigned_locations or [],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        self.db.users.insert_one(user)
        logger.info(f"Created user: {username} with role: {role}")
        
        return {
            "user_id": user_id,
            "username": username,
            "role": role,
            "name": name
        }
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username to lookup
        
        Returns:
            User data if found, None otherwise
        """
        user = self.db.users.find_one({"username": username, "is_active": True})
        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"],
                "name": user["name"],
                "assigned_locations": user.get("assigned_locations", [])
            }
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID to lookup
        
        Returns:
            User data if found, None otherwise
        """
        user = self.db.users.find_one({"user_id": user_id, "is_active": True})
        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"],
                "name": user["name"],
                "assigned_locations": user.get("assigned_locations", [])
            }
        return None
    
    def list_users(self, role: str = None) -> List[Dict[str, Any]]:
        """
        List all active users, optionally filtered by role
        
        Args:
            role: Optional role filter
        
        Returns:
            List of users
        """
        query = {"is_active": True}
        if role:
            query["role"] = role
        
        users = list(self.db.users.find(query, {
            "user_id": 1,
            "username": 1,
            "role": 1,
            "name": 1,
            "created_at": 1
        }))
        
        return list(users)
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user
        
        Args:
            user_id: User ID to deactivate
        
        Returns:
            True if successful, False otherwise
        """
        result = self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Deactivated user: {user_id}")
            return True
        return False
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user information
        
        Args:
            user_id: User ID to update
            updates: Fields to update (role, name, assigned_locations)
        
        Returns:
            True if successful, False otherwise
        """
        # Validate role if being updated
        if "role" in updates and not UserRole.is_valid_role(updates["role"]):
            raise ValueError(f"Invalid role: {updates['role']}")
        
        # Build update document
        update_doc = {}
        if "role" in updates:
            update_doc["role"] = updates["role"]
        if "name" in updates:
            update_doc["name"] = updates["name"]
        if "assigned_locations" in updates:
            update_doc["assigned_locations"] = updates["assigned_locations"]
        
        result = self.db.users.update_one(
            {"user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated user: {user_id}")
            return True
        return False
    
    def seed_default_users(self) -> Dict[str, Any]:
        """
        Seed default users for each role if they don't exist
        
        Returns:
            Summary of seeded users
        """
        default_users = [
            {
                "username": "business",
                "role": UserRole.BUSINESS,
                "name": "Business Analyst"
            },
            {
                "username": "warehouse_manager",
                "role": UserRole.WAREHOUSE_MANAGER,
                "name": "Warehouse Manager"
            },
            {
                "username": "store_manager",
                "role": UserRole.STORE_MANAGER,
                "name": "Store Manager"
            },
            {
                "username": "logistics_manager",
                "role": UserRole.LOGISTICS_MANAGER,
                "name": "Logistics Manager"
            },
            {
                "username": "admin",
                "role": UserRole.ADMIN,
                "name": "System Administrator"
            }
        ]
        
        created = []
        skipped = []
        
        for user_data in default_users:
            existing = self.db.users.find_one({"username": user_data["username"]})
            if existing:
                skipped.append(user_data["username"])
            else:
                try:
                    self.create_user(
                        username=user_data["username"],
                        role=user_data["role"],
                        name=user_data["name"]
                    )
                    created.append(user_data["username"])
                except Exception as e:
                    logger.error(f"Error creating default user {user_data['username']}: {e}")
        
        logger.info(f"Seeded default users. Created: {created}, Skipped: {skipped}")
        
        return {
            "created": created,
            "skipped": skipped,
            "total": len(default_users)
        }
