"""
Simplified test script to verify the enhanced supply chain dataset integration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up paths
BACKEND_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BACKEND_DIR, 'data', 'raw')

def test_enhanced_data():
    """Test that enhanced data can be loaded and processed"""
    
    print("=" * 60)
    print("Testing Enhanced Supply Chain Dataset Integration")
    print("=" * 60)
    
    # Check file paths
    initial_state_path = os.path.join(DATA_DIR, 'initial_inventory_state.csv')
    enhanced_data_path = os.path.join(DATA_DIR, 'enhanced_supply_chain_data.csv')
    
    print(f"\n1. Checking file paths:")
    print(f"   - Initial state: {initial_state_path}")
    print(f"   - Enhanced data: {enhanced_data_path}")
    
    # Verify files exist
    initial_state_exists = os.path.exists(initial_state_path)
    enhanced_data_exists = os.path.exists(enhanced_data_path)
    
    print(f"   - Initial state file exists: {initial_state_exists}")
    print(f"   - Enhanced data file exists: {enhanced_data_exists}")
    
    if not enhanced_data_exists:
        print(f"\n✗ Enhanced data file not found!")
        print(f"   Expected: {enhanced_data_path}")
        return False
    
    # Try to import pandas and load data
    try:
        import pandas as pd
        print(f"\n2. Loading enhanced supply chain data...")
        df = pd.read_csv(enhanced_data_path)
        
        print(f"   - Loaded {len(df)} rows")
        print(f"   - Columns: {list(df.columns)}")
        
        # Check required columns
        required_columns = ['SKU', 'Number of products sold', 'Revenue generated']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"\n✗ Missing required columns: {missing_columns}")
            return False
        
        print(f"   - ✓ All required columns present")
        
        # Show sample data
        print(f"\n3. Sample enhanced data (first 3 rows):")
        print(df.head(3).to_string())
        
        # Aggregate by SKU
        print(f"\n4. Aggregating transaction data by SKU...")
        sku_stats = df.groupby('SKU').agg({
            'Number of products sold': ['sum', 'count'],
            'Revenue generated': 'sum'
        }).reset_index()
        
        sku_stats.columns = ['SKU', 'total_sales', 'transactions_count', 'total_revenue']
        
        print(f"   - Aggregated {len(sku_stats)} SKUs")
        
        # Show sample aggregates
        print(f"\n5. Sample aggregated data (first 5 SKUs):")
        for _, row in sku_stats.head(5).iterrows():
            print(f"   SKU: {row['SKU']}")
            print(f"     - Transactions: {int(row['transactions_count'])}")
            print(f"     - Total Sales: {int(row['total_sales'])}")
            print(f"     - Total Revenue: ${row['total_revenue']:.2f}")
        
        # Check if initial state has matching SKUs
        if initial_state_exists:
            print(f"\n6. Checking SKU overlap with initial state...")
            initial_df = pd.read_csv(initial_state_path)
            
            if 'SKU' in initial_df.columns:
                initial_skus = set(initial_df['SKU'].unique())
                enhanced_skus = set(sku_stats['SKU'].unique())
                
                overlapping_skus = initial_skus & enhanced_skus
                print(f"   - Initial state SKUs: {len(initial_skus)}")
                print(f"   - Enhanced data SKUs: {len(enhanced_skus)}")
                print(f"   - Overlapping SKUs: {len(overlapping_skus)}")
                
                if overlapping_skus:
                    print(f"   - ✓ Found {len(overlapping_skus)} matching SKUs")
                else:
                    print(f"   - ⚠ No matching SKUs found!")
        
        print(f"\n" + "=" * 60)
        print("✓ Enhanced integration test PASSED")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_data()
    sys.exit(0 if success else 1)
