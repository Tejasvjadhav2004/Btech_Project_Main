"""
Test script to verify the enhanced supply chain dataset integration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.config import settings
from scripts.initial_state_loader import InitialStateLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_integration():
    """Test that enhanced data is properly loaded and integrated"""
    
    logger.info("=" * 60)
    logger.info("Testing Enhanced Supply Chain Dataset Integration")
    logger.info("=" * 60)
    
    # Check configuration
    logger.info(f"\n1. Checking configuration:")
    logger.info(f"   - Initial inventory state path: {settings.initial_inventory_state_path}")
    logger.info(f"   - Enhanced data path: {settings.enhanced_supply_chain_data_path}")
    
    # Verify files exist
    initial_state_exists = os.path.exists(settings.initial_inventory_state_path)
    enhanced_data_exists = os.path.exists(settings.enhanced_supply_chain_data_path)
    
    logger.info(f"   - Initial state file exists: {initial_state_exists}")
    logger.info(f"   - Enhanced data file exists: {enhanced_data_exists}")
    
    if not initial_state_exists:
        logger.error(f"Initial state file not found: {settings.initial_inventory_state_path}")
        return False
    
    if not enhanced_data_exists:
        logger.error(f"Enhanced data file not found: {settings.enhanced_supply_chain_data_path}")
        return False
    
    # Initialize loader with enhanced data
    logger.info(f"\n2. Initializing InitialStateLoader with enhanced data...")
    loader = InitialStateLoader(
        settings.initial_inventory_state_path,
        settings.enhanced_supply_chain_data_path
    )
    
    # Load enhanced data
    logger.info(f"\n3. Loading enhanced supply chain data...")
    enhanced_df = loader.load_enhanced_data()
    
    if enhanced_df is None:
        logger.error("Failed to load enhanced data")
        return False
    
    logger.info(f"   - Enhanced data loaded successfully")
    logger.info(f"   - Rows: {len(enhanced_df)}")
    logger.info(f"   - Columns: {list(enhanced_df.columns)}")
    
    # Check required columns
    required_columns = ['SKU', 'Number of products sold', 'Revenue generated']
    missing_columns = [col for col in required_columns if col not in enhanced_df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    logger.info(f"   - All required columns present: {required_columns}")
    
    # Aggregate historical data
    logger.info(f"\n4. Aggregating historical data by SKU...")
    sku_aggregates = loader.aggregate_historical_data()
    
    if not sku_aggregates:
        logger.error("Failed to aggregate historical data")
        return False
    
    logger.info(f"   - Aggregated data for {len(sku_aggregates)} SKUs")
    
    # Show sample aggregates
    logger.info(f"\n5. Sample aggregated data (first 5 SKUs):")
    for i, (sku, data) in enumerate(list(sku_aggregates.items())[:5]):
        logger.info(f"   SKU: {sku}")
        logger.info(f"     - Transactions: {data['transactions_count']}")
        logger.info(f"     - Total Sales: {data['total_sales']}")
        logger.info(f"     - Total Revenue: ${data['total_revenue']:.2f}")
    
    # Load initial state
    logger.info(f"\n6. Loading initial inventory state...")
    initial_df = loader.load_initial_state()
    
    if initial_df is None:
        logger.error("Failed to load initial state")
        return False
    
    logger.info(f"   - Initial state loaded successfully")
    logger.info(f"   - Rows: {len(initial_df)}")
    
    # Generate inventory records
    logger.info(f"\n7. Generating inventory records with historical data...")
    records = loader.get_initial_inventory_records()
    
    if not records:
        logger.error("Failed to generate inventory records")
        return False
    
    logger.info(f"   - Generated {len(records)} inventory records")
    
    # Verify historical data in records
    logger.info(f"\n8. Verifying historical data in inventory records...")
    records_with_transactions = 0
    records_with_sales = 0
    
    for record in records:
        if record.get('transactions_count', 0) > 0:
            records_with_transactions += 1
        if record.get('total_sales', 0) > 0:
            records_with_sales += 1
    
    logger.info(f"   - Records with transactions > 0: {records_with_transactions}/{len(records)}")
    logger.info(f"   - Records with sales > 0: {records_with_sales}/{len(records)}")
    
    # Show sample records
    logger.info(f"\n9. Sample inventory records (first 3):")
    for i, record in enumerate(records[:3]):
        logger.info(f"   Record {i+1}:")
        logger.info(f"     - SKU: {record.get('sku')}")
        logger.info(f"     - Product: {record.get('product_name')}")
        logger.info(f"     - Transactions: {record.get('transactions_count')}")
        logger.info(f"     - Total Sales: {record.get('total_sales')}")
        logger.info(f"     - Total Revenue: ${record.get('total_revenue', 0):.2f}")
    
    logger.info(f"\n" + "=" * 60)
    logger.info("✓ Enhanced integration test PASSED")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_enhanced_integration()
    sys.exit(0 if success else 1)
