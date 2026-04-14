"""
Test script to verify API fixes
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.monitoring_service import MonitoringService
from services.analytics_service import AnalyticsService
from db.connection import mongodb
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_monitoring_service():
    """Test monitoring service methods"""
    logger.info("Testing MonitoringService...")
    
    monitoring_service = MonitoringService()
    
    # Test get_product_distribution
    logger.info("Testing get_product_distribution()...")
    distribution = monitoring_service.get_product_distribution()
    logger.info(f"Result: {len(distribution)} distribution items found")
    if distribution:
        logger.info(f"Sample item: {distribution[0]}")
    
    # Test warehouse_utilization
    logger.info("Testing warehouse_utilization()...")
    utilization = monitoring_service.warehouse_utilization()
    logger.info(f"Result: {len(utilization)} warehouse utilization records")
    if utilization:
        logger.info(f"Sample: {utilization[0]}")
    
    # Test get_kpis
    logger.info("Testing get_kpis()...")
    kpis = monitoring_service.get_kpis()
    logger.info(f"KPIs: {kpis}")
    
    # Test get_stock_by_category
    logger.info("Testing get_stock_by_category()...")
    stock_by_category = monitoring_service.get_stock_by_category()
    logger.info(f"Result: {len(stock_by_category)} category records")
    if stock_by_category:
        logger.info(f"Sample: {stock_by_category[0]}")
    
    # Test get_top_products_by_revenue
    logger.info("Testing get_top_products_by_revenue()...")
    top_products = monitoring_service.get_top_products_by_revenue(5)
    logger.info(f"Result: {len(top_products)} top products")
    if top_products:
        logger.info(f"Sample: {top_products[0]}")
    
    return True


def test_analytics_service():
    """Test analytics service methods"""
    logger.info("Testing AnalyticsService...")
    
    analytics_service = AnalyticsService()
    
    # Test generate_alerts
    logger.info("Testing generate_alerts()...")
    alerts = analytics_service.generate_alerts()
    logger.info(f"Result: {len(alerts)} alerts generated")
    if alerts:
        logger.info(f"Sample alert: {alerts[0]}")
    
    # Test get_inventory_value
    logger.info("Testing get_inventory_value()...")
    inventory_value = analytics_service.get_inventory_value()
    logger.info(f"Inventory value: {inventory_value}")
    
    # Test get_category_performance
    logger.info("Testing get_category_performance()...")
    category_performance = analytics_service.get_category_performance()
    logger.info(f"Result: {len(category_performance)} category performance records")
    if category_performance:
        logger.info(f"Sample: {category_performance[0]}")
    
    return True


def main():
    """Main test function"""
    try:
        logger.info("Starting API fixes test...")
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        if not mongodb.connect():
            logger.error("Failed to connect to MongoDB")
            return False
        
        # Run tests
        test_monitoring_service()
        test_analytics_service()
        
        logger.info("All tests completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close connection
        try:
            mongodb.close()
        except AttributeError:
            # close() method may not exist, that's fine
            pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
