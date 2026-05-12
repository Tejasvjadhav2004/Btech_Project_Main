"""
Clear all MongoDB data
"""
from db.connection import mongodb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_all_data():
    """Clear all collections in MongoDB"""
    try:
        logger.info("Connecting to MongoDB...")
        if not mongodb.connect():
            logger.error("Failed to connect to MongoDB")
            return False
        
        db = mongodb.get_database()
        
        # Get all collection names
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collections: {collections}")
        
        # Clear each collection
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            db[collection_name].delete_many({})
            logger.info(f"Cleared {count} documents from '{collection_name}'")
        
        logger.info("All data cleared successfully!")
        
        # Disconnect
        mongodb.disconnect()
        
        return True
    
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return False

if __name__ == "__main__":
    success = clear_all_data()
    exit(0 if success else 1)
