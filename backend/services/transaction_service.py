"""
Transaction Service - Process sales, restocks, and inventory transfers
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from db.connection import mongodb

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Raised when insufficient stock is available"""
    pass


class TransactionService:
    """Service for processing inventory transactions"""

    def __init__(self):
        """Initialize transaction service"""
        self.db = mongodb.get_database()

    def process_sale(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process customer order/sale transaction
        
        Args:
            order: Order dictionary with items, customer_id, etc.
        
        Returns:
            Transaction result with transaction_id and status
        """
        transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Check stock availability for all items
            for item in order['items']:
                if not self._check_stock(item['sku'], item['quantity'], item.get('location_id')):
                    raise InsufficientStockError(
                        f"Insufficient stock for {item['sku']}"
                    )
            
            # Process each item
            for item in order['items']:
                # Update inventory
                self._update_stock(
                    sku=item['sku'],
                    quantity=-item['quantity'],
                    location_id=item.get('location_id'),
                    transaction_type='sale'
                )
                
                # Record transaction
                self._record_transaction({
                    'transaction_id': transaction_id,
                    'type': 'sale',
                    'sku': item['sku'],
                    'quantity': item['quantity'],
                    'location_id': item.get('location_id'),
                    'order_id': order.get('order_id'),
                    'customer_id': order.get('customer_id'),
                    'timestamp': datetime.utcnow(),
                    'status': 'completed'
                })
            
            logger.info(f"Sale transaction {transaction_id} completed successfully")
            
            return {
                'transaction_id': transaction_id,
                'status': 'completed',
                'message': 'Sale processed successfully'
            }
        
        except InsufficientStockError as e:
            logger.warning(f"Sale transaction {transaction_id} failed: {e}")
            return {
                'transaction_id': transaction_id,
                'status': 'cancelled',
                'message': str(e)
            }
        
        except Exception as e:
            logger.error(f"Error processing sale transaction {transaction_id}: {e}")
            raise

    def process_restock(self, restock_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inventory restock transaction
        
        Args:
            restock_order: Restock order with sku, quantity, location_id
        
        Returns:
            Transaction result
        """
        transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Update inventory
            self._update_stock(
                sku=restock_order['sku'],
                quantity=restock_order['quantity'],
                location_id=restock_order['location_id'],
                transaction_type='restock'
            )
            
            # Record transaction
            self._record_transaction({
                'transaction_id': transaction_id,
                'type': 'restock',
                'sku': restock_order['sku'],
                'quantity': restock_order['quantity'],
                'location_id': restock_order['location_id'],
                'supplier_id': restock_order.get('supplier_id'),
                'timestamp': datetime.utcnow(),
                'status': 'completed'
            })
            
            logger.info(f"Restock transaction {transaction_id} completed successfully")
            
            return {
                'transaction_id': transaction_id,
                'status': 'completed',
                'message': 'Restock processed successfully'
            }
        
        except Exception as e:
            logger.error(f"Error processing restock transaction {transaction_id}: {e}")
            raise

    def process_transfer(self, transfer_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inventory transfer between locations
        
        Args:
            transfer_order: Transfer order with sku, quantity, from_location, to_location
        
        Returns:
            Transaction result
        """
        transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Check stock availability at source location
            if not self._check_stock(
                transfer_order['sku'],
                transfer_order['quantity'],
                transfer_order['from_location']
            ):
                raise InsufficientStockError(
                    f"Insufficient stock at source location {transfer_order['from_location']}"
                )
            
            # Decrease stock at source location
            self._update_stock(
                sku=transfer_order['sku'],
                quantity=-transfer_order['quantity'],
                location_id=transfer_order['from_location'],
                transaction_type='transfer_out'
            )
            
            # Increase stock at destination location
            self._update_stock(
                sku=transfer_order['sku'],
                quantity=transfer_order['quantity'],
                location_id=transfer_order['to_location'],
                transaction_type='transfer_in'
            )
            
            # Record transactions
            self._record_transaction({
                'transaction_id': transaction_id,
                'type': 'transfer',
                'sku': transfer_order['sku'],
                'quantity': transfer_order['quantity'],
                'location_id': transfer_order['from_location'],
                'transfer_to': transfer_order['to_location'],
                'timestamp': datetime.utcnow(),
                'status': 'completed'
            })
            
            logger.info(f"Transfer transaction {transaction_id} completed successfully")
            
            return {
                'transaction_id': transaction_id,
                'status': 'completed',
                'message': 'Transfer processed successfully'
            }
        
        except Exception as e:
            logger.error(f"Error processing transfer transaction {transaction_id}: {e}")
            raise

    def _check_stock(self, sku: str, quantity: int, location_id: str) -> bool:
        """
        Check if sufficient stock is available
        
        Args:
            sku: Product SKU
            quantity: Required quantity
            location_id: Location ID
        
        Returns:
            True if stock is available, False otherwise
        """
        try:
            inventory = self.db.inventory.find_one({
                'sku': sku,
                'location_id': location_id
            })
            
            if not inventory:
                logger.warning(f"No inventory found for {sku} at {location_id}")
                return False
            
            available_stock = inventory.get('available_stock', 0)
            return available_stock >= quantity
        
        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            return False

    def _update_stock(self, sku: str, quantity: int, location_id: str, transaction_type: str):
        """
        Update stock levels for a product at a location
        
        Args:
            sku: Product SKU
            quantity: Quantity to add (positive) or subtract (negative)
            location_id: Location ID
            transaction_type: Type of transaction (sale, restock, transfer)
        """
        try:
            # Find inventory record
            inventory = self.db.inventory.find_one({
                'sku': sku,
                'location_id': location_id
            })
            
            if not inventory:
                logger.warning(f"Creating new inventory record for {sku} at {location_id}")
                # Create new inventory record
                new_inventory = {
                    'sku': sku,
                    'location_id': location_id,
                    'location_type': 'store' if location_id.startswith('ST') else 'warehouse',
                    'current_stock': max(0, quantity),
                    'available_stock': max(0, quantity),
                    'reserved_stock': 0,
                    'initial_stock': max(0, quantity),
                    'transactions_count': 1,
                    'total_sales': 0,
                    'total_restock': 0,
                    'last_updated': datetime.utcnow(),
                    'created_at': datetime.utcnow()
                }
                self.db.inventory.insert_one(new_inventory)
                return
            
            # Update existing inventory
            old_stock = inventory['current_stock']
            new_stock = max(0, old_stock + quantity)
            
            # Update stock levels
            update_data = {
                'current_stock': new_stock,
                'available_stock': new_stock - inventory.get('reserved_stock', 0),
                'last_updated': datetime.utcnow(),
                'transactions_count': inventory.get('transactions_count', 0) + 1,
            }
            
            # Update sales/restock totals
            if transaction_type == 'sale':
                update_data['total_sales'] = inventory.get('total_sales', 0) + abs(quantity)
            elif transaction_type == 'restock':
                update_data['total_restock'] = inventory.get('total_restock', 0) + quantity
            
            self.db.inventory.update_one(
                {'sku': sku, 'location_id': location_id},
                {'$set': update_data}
            )
            
            logger.info(f"Updated stock for {sku} at {location_id}: {old_stock} → {new_stock}")
        
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            raise

    def _record_transaction(self, transaction: Dict[str, Any]):
        """
        Record transaction in transactions collection
        
        Args:
            transaction: Transaction data
        """
        try:
            self.db.transactions.insert_one(transaction)
            logger.info(f"Recorded transaction {transaction.get('transaction_id')}")
        
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            raise

    def get_current_inventory(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get current inventory status for a product
        
        Args:
            sku: Product SKU
        
        Returns:
            Inventory data or None if not found
        """
        try:
            inventory = self.db.inventory.find_one({'sku': sku})
            
            if not inventory:
                return None
            
            return {
                'sku': inventory['sku'],
                'current_stock': inventory.get('current_stock', 0),
                'available_stock': inventory.get('available_stock', 0),
                'reserved_stock': inventory.get('reserved_stock', 0),
                'initial_stock': inventory.get('initial_stock', 0),
                'transactions_count': inventory.get('transactions_count', 0),
                'total_sales': inventory.get('total_sales', 0),
                'total_restock': inventory.get('total_restock', 0),
                'last_updated': inventory.get('last_updated')
            }
        
        except Exception as e:
            logger.error(f"Error getting current inventory: {e}")
            return None

    def get_transaction_history(self, sku: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get transaction history for a product
        
        Args:
            sku: Product SKU
            limit: Maximum number of transactions to return
        
        Returns:
            List of transactions
        """
        try:
            transactions = list(self.db.transactions.find(
                {'sku': sku}
            ).sort('timestamp', -1).limit(limit))
            
            # Convert ObjectId to string
            for txn in transactions:
                txn['_id'] = str(txn['_id'])
            
            return transactions
        
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []

    def get_low_stock_items(self, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get items with low stock levels
        
        Args:
            threshold: Stock threshold (uses reorder_threshold if not provided)
        
        Returns:
            List of low stock items
        """
        try:
            if threshold is None:
                # Get items where current_stock < reorder_threshold
                pipeline = [
                    {
                        '$match': {
                            '$expr': {'$lt': ['$current_stock', '$reorder_threshold']}
                        }
                    }
                ]
            else:
                pipeline = [
                    {'$match': {'current_stock': {'$lt': threshold}}}
                ]
            
            low_stock_items = list(self.db.inventory.aggregate(pipeline))
            
            # Convert ObjectId to string and assess urgency
            for item in low_stock_items:
                item['_id'] = str(item['_id'])
                item['urgency'] = self._assess_urgency(item)
            
            return low_stock_items
        
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            return []

    def _assess_urgency(self, inventory: Dict[str, Any]) -> str:
        """
        Assess urgency level for low stock item
        
        Args:
            inventory: Inventory data
        
        Returns:
            Urgency level: 'critical', 'high', 'medium', 'low'
        """
        current_stock = inventory.get('current_stock', 0)
        reorder_threshold = inventory.get('reorder_threshold', 10)
        
        if current_stock == 0:
            return 'critical'
        elif current_stock < reorder_threshold // 2:
            return 'high'
        elif current_stock < reorder_threshold:
            return 'medium'
        else:
            return 'low'

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        
        Returns:
            System status summary
        """
        try:
            total_inventory = self.db.inventory.count_documents({})
            total_transactions = self.db.transactions.count_documents({})
            
            low_stock_count = len(self.get_low_stock_items())
            
            return {
                'total_inventory_items': total_inventory,
                'total_transactions': total_transactions,
                'low_stock_items': low_stock_count,
                'system_status': 'healthy' if low_stock_count < 10 else 'warning',
                'timestamp': datetime.utcnow()
            }
        
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow()
            }