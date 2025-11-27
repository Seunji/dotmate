#!/usr/bin/env python3
"""Test script to debug AkShare copper price fetching."""

import sys

try:
    import akshare as ak
    print(f"✓ AkShare version: {ak.__version__}")
except ImportError as e:
    print(f"✗ AkShare not installed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Testing AkShare futures_main_sina for copper (CU)")
print("=" * 60 + "\n")

try:
    print("Calling ak.futures_main_sina(symbol='CU')...")
    df = ak.futures_main_sina(symbol="CU")

    print(f"\n✓ Success! Returned type: {type(df)}")
    print(f"  DataFrame shape: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")

    print("\n--- First 5 rows ---")
    print(df.head())

    print("\n--- Last 5 rows ---")
    print(df.tail())

    print("\n--- Latest row details ---")
    latest = df.iloc[-1]
    print(latest)

    print("\n--- Extracting price data ---")
    current_price = float(latest['close'])
    open_price = float(latest['open'])

    # Check for pre_close column
    if 'pre_close' in latest.index:
        prev_close = float(latest['pre_close'])
        print(f"  Using 'pre_close': {prev_close}")
    else:
        print(f"  'pre_close' not found in columns")
        if len(df) > 1:
            prev_close = float(df.iloc[-2]['close'])
            print(f"  Using previous day's close: {prev_close}")
        else:
            prev_close = open_price
            print(f"  Using open price: {prev_close}")

    change = current_price - prev_close
    change_percent = (change / prev_close * 100) if prev_close != 0 else 0.0

    print(f"\n✓ Final result:")
    print(f"  Current price: {current_price} 元")
    print(f"  Change: {change:+.2f} 元")
    print(f"  Change %: {change_percent:+.2f}%")

except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Test completed successfully!")
print("=" * 60)
