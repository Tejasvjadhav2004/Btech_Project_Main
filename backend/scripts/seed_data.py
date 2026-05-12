"""
Seed Data Script - Main entry point for seeding MongoDB with initial inventory state
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.initial_state_loader import InitialStateLoader
from scripts.mongo_initializer import MongoInitializer
from scripts.order_simulator import OrderSimulator
from db.connection import mongodb
from api.config import settings
from db.collections import setup_transactions_collection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to seed MongoDB with initial inventory state"""
    try:
        logger.info("Starting data seeding process...")
        
        # Step 1: Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        if not mongodb.connect():
            logger.error("Failed to connect to MongoDB")
            return False
        
        # Step 2: Load initial inventory state from CSV
        logger.info("Loading initial inventory state from CSV...")
        enhanced_data_path = getattr(settings, 'enhanced_supply_chain_data_path', None)
        initial_loader = InitialStateLoader(settings.initial_inventory_state_path, enhanced_data_path)
        initial_df = initial_loader.load_initial_state()
        
        # Load enhanced data if available
        if enhanced_data_path:
            logger.info("Loading enhanced supply chain data...")
            enhanced_df = initial_loader.load_enhanced_data()
            if enhanced_df is not None:
                logger.info(f"Enhanced data loaded successfully")
        
        # Validate initial state
        if not initial_loader.validate_initial_state():
            logger.error("Initial state validation failed")
            return False
        
        # Print data summary
        summary = initial_loader.get_data_summary()
        logger.info(f"Initial state summary: {summary}")
        
        # Step 3: Extract data from CSV
        logger.info("Extracting data from initial state CSV...")
        inventory = initial_loader.get_initial_inventory_records()
        warehouses = initial_loader.get_warehouses_from_csv()
        stores = initial_loader.get_stores_from_csv()
        products = initial_loader.get_products_from_csv()

        logger.info(f"Extracted {len(inventory)} inventory records")
        logger.info(f"Extracted {len(warehouses)} warehouses")
        logger.info(f"Extracted {len(stores)} stores")
        logger.info(f"Extracted {len(products)} products")

        # Step 4: Initialize MongoDB
        logger.info("Initializing MongoDB...")
        initializer = MongoInitializer()

        # Clear existing data
        initializer.clear_collections()

        # Create warehouses if none exist from CSV
        if not warehouses:
            logger.info("No warehouses in CSV, creating default warehouses...")
            warehouses = initializer.create_default_warehouses()

        # Insert data
        initializer.insert_products(products)
        initializer.insert_warehouses(warehouses)
        initializer.insert_stores(stores)

        # Create warehouse inventory if it doesn't exist
        warehouse_inventory = initializer.create_warehouse_inventory(products, warehouses)

        # Insert both store and warehouse inventory
        all_inventory = inventory + warehouse_inventory
        initializer.insert_inventory(all_inventory)
        
        # Update utilization
        initializer.update_warehouse_utilization()
        initializer.update_store_utilization()
        
        # Get statistics
        stats = initializer.get_collection_stats()
        logger.info(f"Database statistics: {stats}")

        # Step 5: Setup transactions collection
        logger.info("Setting up transactions collection...")
        db = mongodb.get_database()
        setup_transactions_collection(db)
        logger.info("Transactions collection setup complete")

        # Step 6: Simulate initial orders to create realistic system state
        logger.info("Simulating initial orders...")
        simulator = OrderSimulator()
        
        # Generate and process initial orders
        orders = simulator.generate_daily_orders(50)
        logger.info(f"Generated {len(orders)} initial orders")
        
        results = simulator.process_orders(orders)
        logger.info(
            f"Order processing results: {results['completed']} completed, "
            f"{results['cancelled']} cancelled, {results['failed']} failed"
        )

        # Get final statistics
        final_stats = initializer.get_collection_stats()
        logger.info(f"Final database statistics: {final_stats}")
        
        # Get system metrics
        metrics = simulator.get_system_metrics()
        logger.info(f"System metrics: {metrics}")
        
        logger.info("Initial inventory state loaded successfully!")
        logger.info("System is ready for orchestration operations.")
        
        # Disconnect from MongoDB
        mongodb.disconnect()
        
        return True
    
    except Exception as e:
        logger.error(f"Error during data seeding: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
