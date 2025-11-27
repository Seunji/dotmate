#!/usr/bin/env python3
"""Test alternative AkShare methods for copper price."""

import sys

try:
    import akshare as ak
    print(f"✓ AkShare version: {ak.__version__}\n")
except ImportError as e:
    print(f"✗ AkShare not installed: {e}")
    sys.exit(1)

def test_method(name, func_call):
    """Test a method and print results."""
    print("=" * 60)
    print(f"Testing: {name}")
    print("=" * 60)
    try:
        result = func_call()
        print(f"✓ SUCCESS!")
        print(f"Type: {type(result)}")
        if hasattr(result, 'shape'):
            print(f"Shape: {result.shape}")
            print(f"Columns: {result.columns.tolist()}")
            print(f"\nFirst few rows:")
            print(result.head(3))
        else:
            print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        return None
    finally:
        print()

# Test different methods
print("TESTING ALTERNATIVE AKSHARE METHODS\n")

# Method 1: futures_spot_price
result1 = test_method(
    "ak.futures_spot_price()",
    lambda: ak.futures_spot_price()
)

# Method 2: futures_spot_price_daily
result2 = test_method(
    "ak.futures_spot_price_daily(date='20231127')",
    lambda: ak.futures_spot_price_daily(date="20231127")
)

# Method 3: futures_global_spot_em
result3 = test_method(
    "ak.futures_global_spot_em()",
    lambda: ak.futures_global_spot_em()
)

# Method 4: futures_foreign_commodity_realtime (if available)
try:
    result4 = test_method(
        "ak.futures_foreign_commodity_realtime()",
        lambda: ak.futures_foreign_commodity_realtime()
    )
except:
    result4 = None

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"futures_spot_price:              {'✓' if result1 is not None else '✗'}")
print(f"futures_spot_price_daily:        {'✓' if result2 is not None else '✗'}")
print(f"futures_global_spot_em:          {'✓' if result3 is not None else '✗'}")
print(f"futures_foreign_commodity_realtime: {'✓' if result4 is not None else '✗'}")

# Try to find copper in successful results
print("\n" + "=" * 60)
print("SEARCHING FOR COPPER DATA")
print("=" * 60)

for result, name in [(result1, "futures_spot_price"),
                      (result2, "futures_spot_price_daily"),
                      (result3, "futures_global_spot_em"),
                      (result4, "futures_foreign_commodity_realtime")]:
    if result is not None and hasattr(result, 'to_string'):
        print(f"\n{name}:")
        # Search for copper-related rows
        try:
            if '品种' in result.columns:
                copper = result[result['品种'].str.contains('铜|CU|copper', case=False, na=False)]
                if not copper.empty:
                    print(f"✓ Found copper data!")
                    print(copper)
            elif 'symbol' in result.columns:
                copper = result[result['symbol'].str.contains('铜|CU|copper', case=False, na=False)]
                if not copper.empty:
                    print(f"✓ Found copper data!")
                    print(copper)
            elif '商品名称' in result.columns:
                copper = result[result['商品名称'].str.contains('铜|CU|copper', case=False, na=False)]
                if not copper.empty:
                    print(f"✓ Found copper data!")
                    print(copper)
        except Exception as e:
            print(f"  Could not search: {e}")
