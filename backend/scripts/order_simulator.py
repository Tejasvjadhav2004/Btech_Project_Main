"""
Order Simulator - Generate and process realistic orders for testing
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid
import logging
from services.transaction_service import TransactionService, InsufficientStockError

logger = logging.getLogger(__name__)


class OrderSimulator:
    """Simulate realistic order generation and processing"""

    def __init__(self):
        """Initialize order simulator"""
        self.transaction_service = TransactionService()
        self.db = None

    def _get_db(self):
        """Get database connection"""
        if self.db is None:
            from db.connection import mongodb
            self.db = mongodb.get_database()
        return self.db

    def generate_daily_orders(self, num_orders: int = 100) -> List[Dict[str, Any]]:
        """
        Generate realistic daily orders
        
        Args:
            num_orders: Number of orders to generate
        
        Returns:
            List of generated orders
        """
        db = self._get_db()
        orders = []

        # Get all products
        products = list(db.products.find({}, limit=100))
        if not products:
            logger.warning("No products found for order simulation")
            return orders

        # Get all stores
        stores = list(db.stores.find())
        if not stores:
            logger.warning("No stores found for order simulation")
            return orders

        for i in range(num_orders):
            # Generate order based on time distribution
            order_time = self._generate_order_time()
            
            # Get random customer
            customer_id = f"CUST{random.randint(1, 1000):04d}"
            
            # Generate order items
            num_items = random.choices([1, 2, 3, 4, 5], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
            items = []

            for _ in range(num_items):
                # Get random product
                product = random.choice(products)
                
                # Generate quantity based on historical sales
                quantity = self._generate_order_quantity(product)
                
                # Get random store
                store = random.choice(stores)
                
                items.append({
                    'sku': product['sku'],
                    'quantity': quantity,
                    'location_id': store['store_id']
                })

            # Create order
            order = {
                'order_id': f"ORD{uuid.uuid4().hex[:8].upper()}",
                'customer_id': customer_id,
                'items': items,
                'timestamp': order_time,
                'status': 'pending',
                'total_items': len(items),
                'estimated_value': self._calculate_order_value(items, products)
            }

            orders.append(order)

        logger.info(f"Generated {len(orders)} orders")
        return orders

    def _generate_order_time(self) -> datetime:
        """Generate realistic order time within current day"""
        now = datetime.utcnow()
        
        # Distribute orders throughout the day
        hour = random.choices(
            list(range(24)),
            weights=[
                0.02, 0.01, 0.01, 0.01, 0.02, 0.05,  # 0-5
                0.10, 0.15, 0.20, 0.18, 0.12, 0.08,  # 6-11
                0.07, 0.06, 0.08, 0.10, 0.12, 0.10,  # 12-17
                0.08, 0.06, 0.04, 0.03, 0.02, 0.01   # 18-23
            ]
        )[0]
        
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        return datetime(
            now.year, now.month, now.day,
            hour, minute, second
        )

    def _generate_order_quantity(self, product: Dict[str, Any]) -> int:
        """
        Generate realistic order quantity based on product data
        
        Args:
            product: Product data
        
        Returns:
            Order quantity
        """
        # Get historical sales data
        historical_sales = product.get('historical_avg_sales', 50)
        
        # Generate quantity with variation
        base_quantity = max(1, historical_sales // 30)  # Daily average
        variation = random.uniform(0.5, 2.0)
        quantity = int(base_quantity * variation)

        # Cap at reasonable maximum
        quantity = min(quantity, 10)
        quantity = max(quantity, 1)

        return quantity

    def _calculate_order_value(self, items: List[Dict], products: List[Dict]) -> float:
        """
        Calculate estimated order value
        
        Args:
            items: Order items
            products: Product data
        
        Returns:
            Estimated value
        """
        value = 0.0
        product_map = {p['sku']: p for p in products}

        for item in items:
            product = product_map.get(item['sku'])
            if product:
                price = product.get('price', 0)
                value += price * item['quantity']

        return round(value, 2)

    def process_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process generated orders through transaction service
        
        Args:
            orders: List of orders to process
        
        Returns:
            Processing results
        """
        results = {
            'total_orders': len(orders),
            'completed': 0,
            'cancelled': 0,
            'failed': 0,
            'total_items_sold': 0,
            'total_value': 0.0,
            'errors': []
        }

        for order in orders:
            try:
                result = self.transaction_service.process_sale(order)

                if result['status'] == 'completed':
                    results['completed'] += 1
                    results['total_items_sold'] += order['total_items']
                    results['total_value'] += order['estimated_value']
                    order['status'] = 'completed'
                else:
                    results['cancelled'] += 1
                    order['status'] = 'cancelled'

            except InsufficientStockError as e:
                results['cancelled'] += 1
                order['status'] = 'cancelled'
                logger.warning(f"Order {order['order_id']} cancelled: {e}")

            except Exception as e:
                results['failed'] += 1
                order['status'] = 'failed'
                results['errors'].append({
                    'order_id': order['order_id'],
                    'error': str(e)
                })
                logger.error(f"Error processing order {order['order_id']}: {e}")

        logger.info(
            f"Order processing complete: {results['completed']} completed, "
            f"{results['cancelled']} cancelled, {results['failed']} failed"
        )

        return results

    def simulate_week(self, days: int = 7, orders_per_day: int = 100) -> List[Dict[str, Any]]:
        """
        Simulate a week of orders
        
        Args:
            days: Number of days to simulate
            orders_per_day: Number of orders per day
        
        Returns:
            Daily results
        """
        daily_results = []

        for day in range(days):
            logger.info(f"Simulating day {day + 1}/{days}")

            # Generate orders for the day
            orders = self.generate_daily_orders(orders_per_day)

            # Process orders
            results = self.process_orders(orders)

            daily_results.append({
                'day': day + 1,
                'date': (datetime.utcnow() - timedelta(days=days - day - 1)).strftime('%Y-%m-%d'),
                'orders_generated': orders_per_day,
                'orders_completed': results['completed'],
                'orders_cancelled': results['cancelled'],
                'orders_failed': results['failed'],
                'items_sold': results['total_items_sold'],
                'total_value': results['total_value'],
                'success_rate': round(results['completed'] / orders_per_day * 100, 2)
            })

        return daily_results

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics after simulation
        
        Returns:
            System metrics
        """
        db = self._get_db()

        # Get inventory stats
        inventory_stats = list(db.inventory.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_items': {'$sum': '$current_stock'},
                    'low_stock_count': {
                        '$sum': {
                            '$cond': [
                                {'$lt': ['$current_stock', '$reorder_threshold']},
                                1,
                                0
                            ]
                        }
                    },
                    'total_transactions': {'$sum': '$transactions_count'},
                    'total_sales': {'$sum': '$total_sales'}
                }
            }
        ]))

        # Get transaction stats
        transaction_stats = list(db.transactions.aggregate([
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }
            }
        ]))

        # Get system status
        system_status = self.transaction_service.get_system_status()

        return {
            'inventory': inventory_stats[0] if inventory_stats else {},
            'transactions': {t['_id']: t['count'] for t in transaction_stats},
            'system_status': system_status
        }

    def clear_simulated_data(self):
        """Clear simulated transactions and reset inventory"""
        db = self._get_db()

        try:
            # Clear transactions
            db.transactions.delete_many({})

            # Reset inventory to initial state
            db.inventory.update_many(
                {},
                {
                    '$set': {
                        'current_stock': '$initial_stock',
                        'available_stock': '$initial_stock',
                        'reserved_stock': 0,
                        'transactions_count': 0,
                        'total_sales': 0,
                        'total_restock': 0,
                        'last_updated': datetime.utcnow()
                    }
                }
            )

            logger.info("Cleared simulated data and reset inventory")

        except Exception as e:
            logger.error(f"Error clearing simulated data: {e}")
            raise


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    simulator = OrderSimulator()

    # Simulate one day
    print("Generating daily orders...")
    orders = simulator.generate_daily_orders(50)

    print(f"Generated {len(orders)} orders")

    print("Processing orders...")
    results = simulator.process_orders(orders)

    print("\nResults:")
    print(f"  Completed: {results['completed']}")
    print(f"  Cancelled: {results['cancelled']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Items sold: {results['total_items_sold']}")
    print(f"  Total value: ${results['total_value']}")

    print("\nSystem metrics:")
    metrics = simulator.get_system_metrics()
    print(f"  Total inventory items: {metrics['inventory'].get('total_items', 0)}")
    print(f"  Low stock items: {metrics['inventory'].get('low_stock_count', 0)}")
    print(f"  Total transactions: {metrics['inventory'].get('total_transactions', 0)}")