#!/usr/bin/env python3
"""Test script to debug AkShare copper price fetching with multiple methods."""

import sys

try:
    import akshare as ak
    print(f"✓ AkShare version: {ak.__version__}")
except ImportError as e:
    print(f"✗ AkShare not installed: {e}")
    sys.exit(1)

def test_method(method_name, func, *args, **kwargs):
    """Test a single AkShare method."""
    print("\n" + "=" * 60)
    print(f"Testing {method_name}")
    print("=" * 60 + "\n")

    try:
        print(f"Calling {func.__name__}...")
        df = func(*args, **kwargs)

        print(f"\n✓ Success! Returned type: {type(df)}")
        print(f"  DataFrame shape: {df.shape}")
        print(f"  Columns: {df.columns.tolist()}")

        print("\n--- First 3 rows ---")
        print(df.head(3))

        print("\n--- Last 3 rows ---")
        print(df.tail(3))

        return df, None

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, e

# Test Method 1: futures_main_sina
df1, err1 = test_method(
    "Method 1: ak.futures_main_sina(symbol='CU')",
    ak.futures_main_sina,
    symbol="CU"
)

# Test Method 2: futures_zh_spot
df2, err2 = test_method(
    "Method 2: ak.futures_zh_spot(symbol='沪铜主连')",
    ak.futures_zh_spot,
    symbol="沪铜主连"
)

# Test Method 3: futures_display_main_sina
df3, err3 = test_method(
    "Method 3: ak.futures_display_main_sina(symbol='CU0')",
    ak.futures_display_main_sina,
    symbol="CU0"
)

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Method 1 (futures_main_sina):       {'✓ SUCCESS' if df1 is not None else '✗ FAILED'}")
print(f"Method 2 (futures_zh_spot):         {'✓ SUCCESS' if df2 is not None else '✗ FAILED'}")
print(f"Method 3 (futures_display_main_sina): {'✓ SUCCESS' if df3 is not None else '✗ FAILED'}")

# Try to extract price from successful method
success_df = df1 or df2 or df3

if success_df is not None:
    print("\n" + "=" * 60)
    print("EXTRACTING PRICE DATA FROM SUCCESSFUL METHOD")
    print("=" * 60)

    try:
        latest = success_df.iloc[-1] if len(success_df) > 0 else success_df.iloc[0]
        print(f"\nLatest row:\n{latest}")

        # Try different column names
        if 'close' in latest.index:
            price = float(latest['close'])
            print(f"\n✓ Extracted price from 'close': {price} 元")
        elif '最新价' in latest.index:
            price = float(latest['最新价'])
            print(f"\n✓ Extracted price from '最新价': {price} 元")
        else:
            print("\n✗ Could not find price column")

    except Exception as e:
        print(f"\n✗ Error extracting price: {type(e).__name__}: {e}")
else:
    print("\n✗ All methods failed!")
    sys.exit(1)

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
