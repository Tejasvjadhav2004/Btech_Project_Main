"""
Seed Data Script - Main entry point for seeding MongoDB
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_loader import DataLoader
from scripts.data_transformer import DataTransformer
from scripts.data_generator import DataGenerator
from scripts.mongo_initializer import MongoInitializer
from db.connection import mongodb
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to seed MongoDB with data"""
    try:
        logger.info("Starting data seeding process...")
        
        # Step 1: Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        if not mongodb.connect():
            logger.error("Failed to connect to MongoDB")
            return False
        
        # Step 2: Load data from CSV files
        logger.info("Loading data from CSV files...")
        loader = DataLoader(
            settings.supply_chain_data_path,
            settings.fashion_boutique_data_path
        )
        supply_chain_df, fashion_boutique_df = loader.load_data()
        
        # Validate data
        if not loader.validate_data():
            logger.error("Data validation failed")
            return False
        
        # Print data summary
        summary = loader.get_data_summary()
        logger.info(f"Data summary: {summary}")
        
        # Step 3: Transform data
        logger.info("Transforming data...")
        transformer = DataTransformer(supply_chain_df, fashion_boutique_df)
        products = transformer.transform_products()
        suppliers = transformer.extract_suppliers()
        
        # Step 4: Generate synthetic data
        logger.info("Generating synthetic data...")
        generator = DataGenerator(
            num_warehouses=settings.num_warehouses,
            num_stores=settings.num_stores,
            warehouse_cities=settings.warehouse_cities,
            store_cities=settings.store_cities
        )
        warehouses = generator.generate_warehouses()
        stores = generator.generate_stores()
        inventory = generator.generate_inventory(products, warehouses, stores)
        
        # Step 5: Initialize MongoDB
        logger.info("Initializing MongoDB...")
        initializer = MongoInitializer()
        
        # Clear existing data
        initializer.clear_collections()
        
        # Insert data
        initializer.insert_products(products)
        initializer.insert_warehouses(warehouses)
        initializer.insert_stores(stores)
        initializer.insert_suppliers(suppliers)
        initializer.insert_inventory(inventory)
        
        # Update utilization
        initializer.update_warehouse_utilization()
        initializer.update_store_utilization()
        
        # Get statistics
        stats = initializer.get_collection_stats()
        logger.info(f"Database statistics: {stats}")
        
        # Disconnect from MongoDB
        mongodb.disconnect()
        
        logger.info("Data seeding completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during data seeding: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
