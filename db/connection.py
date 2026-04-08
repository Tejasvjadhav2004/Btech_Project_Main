"""
MongoDB connection management
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(settings.mongodb_uri)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[settings.mongodb_database_name]
            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_database_name}")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_database(self):
        """Get the database instance"""
        if self.db is None:
            self.connect()
        return self.db
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        db = self.get_database()
        return db[collection_name]


# Global MongoDB instance
mongodb = MongoDB()


def get_db():
    """Dependency function to get database instance"""
    db = mongodb.get_database()
    return db


def get_collection(collection_name: str):
    """Dependency function to get specific collection"""
    db = mongodb.get_database()
    return db[collection_name]
