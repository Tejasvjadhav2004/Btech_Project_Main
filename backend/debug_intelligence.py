"""
Debug script to investigate Intelligence page data issues
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db.connection import mongodb
from services.signal_service import SignalService
from services.scheduler_service import scheduler_service
from services.decision_service import decision_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection and collections"""
    logger.info("=" * 60)
    logger.info("Testing Database Connection and Collections")
    logger.info("=" * 60)
    
    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        if not mongodb.connect():
            logger.error("❌ Failed to connect to MongoDB")
            return False
        
        db = mongodb.get_database()
        if not db:
            logger.error("❌ Failed to get database")
            return False
        
        logger.info("✅ Database connection successful")
        
        # Check database name
        logger.info(f"Database name: {db.name}")
        
        # List all collections
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check for signals collection
        if "signals" in collections:
            logger.info("✅ 'signals' collection exists")
            signal_count = db.signals.count_documents({})
            logger.info(f"   Total signals in database: {signal_count}")
            
            # Check active signals
            active_count = db.signals.count_documents({"status": "active"})
            logger.info(f"   Active signals: {active_count}")
            
            # Sample signal
            if signal_count > 0:
                sample = db.signals.find_one()
                logger.info(f"   Sample signal structure:")
                for key, value in sample.items():
                    if key not in ['_id']:
                        logger.info(f"     {key}: {value}")
        else:
            logger.error("❌ 'signals' collection does NOT exist")
        
        # Check for other collections
        for collection in ["event_logs", "alerts", "replenishment_orders"]:
            if collection in collections:
                count = db[collection].count_documents({})
                logger.info(f"✅ '{collection}' collection exists with {count} documents")
            else:
                logger.warning(f"⚠️  '{collection}' collection does NOT exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_service():
    """Test SignalService methods"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing SignalService")
    logger.info("=" * 60)
    
    try:
        signal_service = SignalService()
        
        # Test get_signal_stats
        logger.info("Testing get_signal_stats()...")
        stats = signal_service.get_signal_stats()
        logger.info(f"   Signal stats: {stats}")
        
        # Test get_active_signals
        logger.info("Testing get_active_signals()...")
        active_signals = signal_service.get_active_signals()
        logger.info(f"   Active signals count: {len(active_signals)}")
        if active_signals:
            logger.info(f"   Sample active signal:")
            for key, value in active_signals[0].items():
                if key not in ['_id', 'details', 'threshold']:
                    logger.info(f"     {key}: {value}")
        
        # Test get_signals
        logger.info("Testing get_signals()...")
        all_signals = signal_service.get_signals()
        logger.info(f"   All signals count: {len(all_signals)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing SignalService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler_service():
    """Test SchedulerService"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing SchedulerService")
    logger.info("=" * 60)
    
    try:
        status = scheduler_service.get_status()
        logger.info(f"   Scheduler status: {status}")
        return True
    except Exception as e:
        logger.error(f"❌ Error testing SchedulerService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decision_service():
    """Test DecisionService"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing DecisionService")
    logger.info("=" * 60)
    
    try:
        # Test get_decision_stats
        logger.info("Testing get_decision_stats()...")
        stats = decision_service.get_decision_stats()
        logger.info(f"   Decision stats: {stats}")
        
        # Test get_pending_replenishment_orders
        logger.info("Testing get_pending_replenishment_orders()...")
        orders = decision_service.get_pending_replenishment_orders()
        logger.info(f"   Pending replenishment orders: {len(orders)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing DecisionService: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main debug function"""
    logger.info("Starting Intelligence Page Debug Investigation")
    logger.info("=" * 60)
    
    try:
        # Test database connection
        if not test_database_connection():
            logger.error("❌ Database connection test failed")
            return False
        
        # Test services
        test_signal_service()
        test_scheduler_service()
        test_decision_service()
        
        logger.info("\n" + "=" * 60)
        logger.info("Debug Investigation Complete")
        logger.info("=" * 60)
        return True
    
    except Exception as e:
        logger.error(f"❌ Error during debug investigation: {e}")
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