"""
Complete System Fix Script - Clear database and re-seed with corrected capacities and live tracking
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import mongodb
from scripts.data_loader import DataLoader
from scripts.data_transformer import DataTransformer
from scripts.data_generator import DataGenerator
from scripts.mongo_initializer import MongoInitializer
from scripts.order_simulator import OrderSimulator
from db.collections import setup_transactions_collection
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_all_data():
    """Clear all MongoDB collections"""
    logger.info("=== CLEARING ALL DATA ===")
    
    if not mongodb.connect():
        logger.error("Failed to connect to MongoDB")
        return False
    
    db = mongodb.get_database()
    
    # Get all collection names
    collections = db.list_collection_names()
    logger.info(f"Found {len(collections)} collections: {collections}")
    
    # Clear each collection
    total_cleared = 0
    for collection_name in collections:
        count = db[collection_name].count_documents({})
        if count > 0:
            db[collection_name].delete_many({})
            logger.info(f"✓ Cleared {count:,} documents from '{collection_name}'")
            total_cleared += count
    
    logger.info(f"Total documents cleared: {total_cleared:,}")
    logger.info("✓ All data cleared successfully!")
    
    return True


def verify_capacities():
    """Verify warehouse and store capacities are correct"""
    logger.info("\n=== VERIFYING CAPACITIES ===")
    
    db = mongodb.get_database()
    
    # Check warehouses
    logger.info("Warehouses:")
    for wh in db.warehouses.find():
        capacity = wh.get('capacity', 0)
        utilization = wh.get('current_utilization', 0)
        pct = (utilization / capacity * 100) if capacity > 0 else 0
        logger.info(f"  {wh['warehouse_id']}: Capacity={capacity:,}, Utilization={utilization:,} ({pct:.1f}%)")
        
        if capacity < 100000:
            logger.warning(f"  ⚠️  WARNING: Capacity {capacity:,} is below 100,000!")
    
    # Check stores
    logger.info("\nStores:")
    for st in db.stores.find():
        capacity = st.get('capacity', 0)
        utilization = st.get('current_utilization', 0)
        pct = (utilization / capacity * 100) if capacity > 0 else 0
        logger.info(f"  {st['store_id']}: Capacity={capacity:,}, Utilization={utilization:,} ({pct:.1f}%)")
        
        if capacity < 10000:
            logger.warning(f"  ⚠️  WARNING: Capacity {capacity:,} is below 10,000!")


def verify_live_tracking():
    """Verify inventory has live tracking fields"""
    logger.info("\n=== VERIFYING LIVE TRACKING ===")
    
    db = mongodb.get_database()
    
    # Check inventory collection
    inv_count = db.inventory.count_documents({})
    logger.info(f"Total inventory records: {inv_count:,}")
    
    # Sample one inventory record
    inv = db.inventory.find_one()
    if inv:
        logger.info("\nSample inventory record:")
        logger.info(f"  SKU: {inv.get('sku', 'N/A')}")
        logger.info(f"  Location: {inv.get('location_id', 'N/A')} ({inv.get('location_type', 'N/A')})")
        logger.info(f"  Current Stock: {inv.get('current_stock', 'NOT FOUND')}")
        logger.info(f"  Available Stock: {inv.get('available_stock', 'NOT FOUND')}")
        logger.info(f"  Reserved Stock: {inv.get('reserved_stock', 'NOT FOUND')}")
        logger.info(f"  Initial Stock: {inv.get('initial_stock', 'NOT FOUND')}")
        logger.info(f"  Transactions: {inv.get('transactions_count', 'NOT FOUND')}")
        logger.info(f"  Total Sales: {inv.get('total_sales', 'NOT FOUND')}")
        logger.info(f"  Total Restock: {inv.get('total_restock', 'NOT FOUND')}")
        logger.info(f"  Last Updated: {inv.get('last_updated', 'NOT FOUND')}")
        
        # Check if fields exist
        required_fields = ['current_stock', 'available_stock', 'reserved_stock', 
                          'initial_stock', 'transactions_count', 'total_sales', 
                          'total_restock', 'last_updated']
        
        missing_fields = [f for f in required_fields if f not in inv]
        if missing_fields:
            logger.warning(f"⚠️  WARNING: Missing fields: {missing_fields}")
        else:
            logger.info("✓ All live tracking fields present!")


def main():
    """Main function to fix the system"""
    try:
        logger.info("=" * 60)
        logger.info("COMPLETE SYSTEM FIX")
        logger.info("=" * 60)
        
        # Step 1: Clear all data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: CLEAR ALL EXISTING DATA")
        logger.info("=" * 60)
        if not clear_all_data():
            logger.error("Failed to clear data")
            return False
        
        # Step 2: Load CSV data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: LOAD CSV DATA")
        logger.info("=" * 60)
        logger.info("Loading data from CSV files...")
        loader = DataLoader(
            settings.supply_chain_data_path,
            settings.fashion_boutique_data_path
        )
        supply_chain_df, fashion_boutique_df = loader.load_data()
        
        if not loader.validate_data():
            logger.error("Data validation failed")
            return False
        
        if not loader.validate_coordinates():
            logger.error("Coordinate validation failed")
            return False
        
        summary = loader.get_data_summary()
        logger.info(f"Data summary: {summary}")
        
        # Step 3: Transform data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: TRANSFORM DATA")
        logger.info("=" * 60)
        logger.info("Transforming data...")
        transformer = DataTransformer(supply_chain_df, fashion_boutique_df)
        products = transformer.transform_products()
        suppliers = transformer.extract_suppliers()
        locations = transformer.extract_locations()
        logger.info(f"✓ Extracted {len(locations)} unique locations")
        
        # Step 4: Generate data with CORRECTED capacities
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: GENERATE DATA WITH CORRECTED CAPACITIES")
        logger.info("=" * 60)
        logger.info("Generating warehouses and stores with realistic capacities...")
        generator = DataGenerator()
        warehouses = generator.generate_warehouses(locations)
        stores = generator.generate_stores(locations)
        inventory = generator.generate_inventory(products, warehouses, stores, supply_chain_df)
        
        logger.info(f"✓ Generated {len(warehouses)} warehouses")
        logger.info(f"✓ Generated {len(stores)} stores")
        logger.info(f"✓ Generated {len(inventory)} inventory records")
        
        # Step 5: Initialize MongoDB
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: INITIALIZE MONGODB")
        logger.info("=" * 60)
        logger.info("Initializing MongoDB...")
        initializer = MongoInitializer()
        
        # Clear collections (redundant but safe)
        initializer.clear_collections()
        
        # Insert data
        logger.info("Inserting data...")
        initializer.insert_products(products)
        initializer.insert_warehouses(warehouses)
        initializer.insert_stores(stores)
        initializer.insert_suppliers(suppliers)
        initializer.insert_locations(locations)
        initializer.insert_inventory(inventory)
        
        # Update utilization
        initializer.update_warehouse_utilization()
        initializer.update_store_utilization()
        
        # Setup transactions collection
        logger.info("Setting up transactions collection...")
        db = mongodb.get_database()
        setup_transactions_collection(db)
        
        # Step 6: Simulate initial orders
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6: SIMULATE INITIAL ORDERS")
        logger.info("=" * 60)
        logger.info("Simulating initial orders with live tracking...")
        simulator = OrderSimulator()
        
        # Generate and process initial orders
        orders = simulator.generate_daily_orders(50)
        logger.info(f"✓ Generated {len(orders)} initial orders")
        
        results = simulator.process_orders(orders)
        logger.info(
            f"✓ Order processing: {results['completed']} completed, "
            f"{results['cancelled']} cancelled, {results['failed']} failed"
        )
        
        # Step 7: Verify all products have inventory
        logger.info("\n" + "=" * 60)
        logger.info("STEP 7: VERIFY ALL PRODUCTS HAVE INVENTORY")
        logger.info("=" * 60)
        
        db = mongodb.get_database()
        
        # Check if all products have inventory records
        all_products = list(db.products.find({}, {'sku': 1}))
        all_skus = {p['sku'] for p in all_products}
        
        inventory_skus = {inv['sku'] for inv in db.inventory.find({}, {'sku': 1})}
        missing_skus = all_skus - inventory_skus
        
        logger.info(f"Total products: {len(all_products)}")
        logger.info(f"Products with inventory: {len(inventory_skus)}")
        logger.info(f"Products without inventory: {len(missing_skus)}")
        
        if missing_skus:
            logger.warning(f"⚠️  WARNING: {len(missing_skus)} products without inventory!")
            logger.warning(f"Missing SKUs: {list(missing_skus)[:10]}")
        else:
            logger.info("✓ All products have inventory records!")
        
        # Verify location IDs are valid
        warehouse_ids = {w['warehouse_id'] for w in db.warehouses.find({}, {'warehouse_id': 1})}
        store_ids = {s['store_id'] for s in db.stores.find({}, {'store_id': 1})}
        all_location_ids = warehouse_ids | store_ids
        
        invalid_locations = []
        for inv in db.inventory.find():
            if inv['location_id'] not in all_location_ids:
                invalid_locations.append(inv['sku'])
        
        if invalid_locations:
            logger.warning(f"⚠️  WARNING: {len(invalid_locations)} inventory records with invalid location IDs!")
        else:
            logger.info("✓ All inventory records have valid location IDs!")
        
        # Step 8: Verify all fixes
        logger.info("\n" + "=" * 60)
        logger.info("STEP 8: VERIFICATION")
        logger.info("=" * 60)
        
        # Get final statistics
        stats = initializer.get_collection_stats()
        logger.info(f"\nFinal database statistics:")
        for collection, count in stats.items():
            logger.info(f"  {collection}: {count:,} documents")
        
        # Get system metrics
        metrics = simulator.get_system_metrics()
        logger.info(f"\nSystem metrics:")
        logger.info(f"  {metrics}")
        
        # Verify capacities
        verify_capacities()
        
        # Verify live tracking
        verify_live_tracking()
        
        # Disconnect
        mongodb.disconnect()
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ SYSTEM FIX COMPLETE!")
        logger.info("=" * 60)
        logger.info("\nWhat was fixed:")
        logger.info("  1. ✓ Warehouse capacities increased to 100,000-300,000")
        logger.info("  2. ✓ Store capacities increased to 10,000-30,000")
        logger.info("  3. ✓ Live tracking fields added to inventory")
        logger.info("  4. ✓ Current/available stock tracking enabled")
        logger.info("  5. ✓ Transaction processing initialized")
        logger.info("  6. ✓ NaN values in location data handled")
        logger.info("\nNext steps:")
        logger.info("  1. Refresh your frontend dashboards")
        logger.info("  2. Check that utilization is now 50-70% (not 1000%+)")
        logger.info("  3. Verify current_stock and available_stock are displayed")
        logger.info("  4. Test transaction processing")
        
        return True
    
    except Exception as e:
        logger.error(f"\n✗ ERROR during system fix: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)