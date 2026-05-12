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
    
    def __init__(self, supply_chain_df: pd.DataFrame):
        self.supply_chain_df = supply_chain_df
    
    def transform_products(self) -> List[Dict[str, Any]]:
        """Transform product data from supply chain dataset"""
        products = []
        
        # Process supply chain data
        for _, row in self.supply_chain_df.iterrows():
            sku = row['SKU']
            
            # Map product type to category
            category_mapping = {
                'haircare': 'haircare',
                'skincare': 'skincare',
                'cosmetics': 'cosmetics',
                'fashion': 'fashion'
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
                # Add location data
                'location': {
                    'city': row['City'],
                    'state': row['State'],
                    'country': row['Country'],
                    'coordinates': {
                        'lat': row['Coordinates_Lat'],
                        'lng': row['Coordinates_Lng']
                    }
                },
                # Add allocation data
                'primary_warehouse': row['Primary_Warehouse_ID'],
                'secondary_warehouse': row['Secondary_Warehouse_ID'],
                'store_allocations': self._parse_store_allocations(row['Store_Allocations']),
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

    def extract_locations(self) -> Dict[str, Any]:
        """Extract unique locations with coordinates from supply chain data"""
        locations = {}

        for _, row in self.supply_chain_df.iterrows():
            city = row['City']

            if city not in locations:
                # Handle NaN values by providing defaults
                state = row['State'] if pd.notna(row['State']) else 'Unknown'
                country = row['Country'] if pd.notna(row['Country']) else 'India'
                lat = row['Coordinates_Lat'] if pd.notna(row['Coordinates_Lat']) else 0
                lng = row['Coordinates_Lng'] if pd.notna(row['Coordinates_Lng']) else 0

                locations[city] = {
                    'city': city,
                    'state': state,
                    'country': country,
                    'lat': lat,
                    'lng': lng
                }

        logger.info(f"Extracted {len(locations)} unique locations")
        return list(locations.values())

    def extract_warehouse_allocations(self) -> Dict[str, Any]:
        """Extract warehouse and store allocations from CSV"""
        allocations = {}

        for _, row in self.supply_chain_df.iterrows():
            sku = row['SKU']

            # Parse store allocations
            store_allocs = {}
            if row['Store_Allocations']:
                for alloc_str in str(row['Store_Allocations']).split(';'):
                    if ':' in alloc_str:
                        store_id, percentage = alloc_str.split(':')
                        store_allocs[store_id.strip()] = float(percentage.strip())

            allocations[sku] = {
                'primary_warehouse': row['Primary_Warehouse_ID'],
                'secondary_warehouse': row['Secondary_Warehouse_ID'],
                'store_allocations': store_allocs
            }

        logger.info(f"Extracted allocations for {len(allocations)} products")
        return allocations

    def _parse_store_allocations(self, allocation_str) -> Dict[str, float]:
        """Parse store allocation string into dictionary"""
        allocations = {}
        if allocation_str and pd.notna(allocation_str):
            for alloc in str(allocation_str).split(';'):
                if ':' in alloc:
                    store_id, percentage = alloc.split(':')
                    allocations[store_id.strip()] = float(percentage.strip())
        return allocations
