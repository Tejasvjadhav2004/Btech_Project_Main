"""
Location Service - Manage geographic locations and coordinates
"""
from typing import Dict, Any, List, Optional, Tuple
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location management"""

    def __init__(self):
        pass

    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()

    def get_location_by_city(self, city: str) -> Optional[Dict[str, Any]]:
        """Get location data for a city"""
        return self.db.locations.find_one({"city": city})

    def get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all locations"""
        return list(self.db.locations.find({}, {"_id": 0}))

    def get_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a city"""
        location = self.get_location_by_city(city)
        if location:
            return location["lat"], location["lng"]
        return None

    def get_warehouses_in_region(self, region: str) -> List[Dict[str, Any]]:
        """Get warehouses in a specific region"""
        return list(self.db.warehouses.find({"region": region}, {"_id": 0}))

    def get_stores_in_region(self, region: str) -> List[Dict[str, Any]]:
        """Get stores in a specific region"""
        return list(self.db.stores.find({"region": region}, {"_id": 0}))
