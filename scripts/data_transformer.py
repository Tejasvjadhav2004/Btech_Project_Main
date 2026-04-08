"""
Data Transformer - Transform CSV data to MongoDB schema format
"""
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform CSV data to MongoDB schema format"""
    
    def __init__(self, supply_chain_df: pd.DataFrame, fashion_boutique_df: pd.DataFrame):
        self.supply_chain_df = supply_chain_df
        self.fashion_boutique_df = fashion_boutique_df
    
    def transform_products(self) -> List[Dict[str, Any]]:
        """Transform and merge product data from both datasets"""
        products = []
        
        # Create a map from fashion_boutique for quick lookup
        fb_map = {}
        for _, row in self.fashion_boutique_df.iterrows():
            fb_map[row['product_id']] = {
                'category': row['category'],
                'brand': row['brand'],
                'original_price': row['original_price'],
                'current_price': row['current_price'],
                'stock_quantity': row['stock_quantity'],
                'customer_rating': row.get('customer_rating', None)
            }
        
        # Process supply chain data
        for _, row in self.supply_chain_df.iterrows():
            sku = row['SKU']
            
            # Map product type to category
            category_mapping = {
                'haircare': 'haircare',
                'skincare': 'skincare',
                'cosmetics': 'cosmetics'
            }
            product_type = row['Product type'].lower() if 'Product type' in row else 'other'
            category = category_mapping.get(product_type, product_type)
            
            product = {
                'sku': sku,
                'name': f"{category.title()} Product {sku}",
                'category': category,
                'brand': row['Supplier name'],
                'product_type': product_type,
                'original_price': float(row['Price']),
                'current_price': float(row['Price']),
                'average_rating': None,
                'total_sales': int(row['Number of products sold']) if 'Number of products sold' in row and pd.notna(row['Number of products sold']) else 0,
                'total_revenue': float(row['Revenue generated']) if 'Revenue generated' in row and pd.notna(row['Revenue generated']) else 0.0,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'demand_forecast': None,
                'optimization_score': None,
                'tags': [category]
            }
            products.append(product)
        
        logger.info(f"Transformed {len(products)} products")
        return products
    
    def extract_suppliers(self) -> List[Dict[str, Any]]:
        """Extract unique suppliers from supply chain data"""
        suppliers = {}
        
        for _, row in self.supply_chain_df.iterrows():
            supplier_name = row['Supplier name']
            location = row['Location']
            
            if supplier_name not in suppliers:
                suppliers[supplier_name] = {
                    'supplier_id': f"SUP_{len(suppliers) + 1:03d}",
                    'name': supplier_name,
                    'location': {
                        'city': location,
                        'state': None,
                        'country': 'India'
                    },
                    'contact': None,
                    'products_supplied': [],
                    'lead_time_days': 7,
                    'reliability_score': 0.8,
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'performance_metrics': None
                }
        
        # Add product SKUs to suppliers
        for _, row in self.supply_chain_df.iterrows():
            supplier_name = row['Supplier name']
            sku = row['SKU']
            if supplier_name in suppliers:
                suppliers[supplier_name]['products_supplied'].append(sku)
        
        logger.info(f"Extracted {len(suppliers)} suppliers")
        return list(suppliers.values())
