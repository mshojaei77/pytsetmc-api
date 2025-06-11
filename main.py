#!/usr/bin/env python3
"""
TSETMC Library Usage Example

This example demonstrates how to use the Tehran Stock Exchange Market Center (TSETMC) API client
to retrieve stock data, market information, and trading statistics.

Features demonstrated:
- Stock search and information retrieval
- Historical price data
- Market indices
- Intraday trading data
- Market watch data
- Bulk data operations
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, date
from typing import List, Optional

# Add the package path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the main client and models
from pytsetmc_api import TSETMCClient, MarketType
from pytsetmc_api.exceptions import TSETMCError, TSETMCNotFoundError, TSETMCDataError


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_dataframe(df: pd.DataFrame, title: str, max_rows: int = 10) -> None:
    """Print a DataFrame with formatting."""
    print(f"\n{title}:")
    print("-" * len(title))
    if df.empty:
        print("No data available")
    else:
        print(f"Shape: {df.shape}")
        print(df.head(max_rows).to_string())
        if len(df) > max_rows:
            print(f"... and {len(df) - max_rows} more rows")


def demonstrate_stock_search(client: TSETMCClient) -> None:
    """Demonstrate stock search functionality."""
    print_section("Stock Search Examples")
    
    # Search for popular stocks
    search_terms = ["پترول", "خودرو", "فولاد", "بانک"]
    
    for term in search_terms:
        try:
            print(f"\nSearching for '{term}'...")
            results = client.search_stock(term)
            print_dataframe(results, f"Search results for '{term}'", max_rows=3)
        except TSETMCNotFoundError:
            print(f"No results found for '{term}'")
        except TSETMCError as e:
            print(f"Error searching for '{term}': {e}")


def demonstrate_stock_info(client: TSETMCClient) -> None:
    """Demonstrate getting detailed stock information."""
    print_section("Stock Information")
    
    try:
        # Get information for a popular stock
        stock_name = "پترول"
        print(f"\nGetting detailed information for '{stock_name}'...")
        
        stock_info = client.stock.get_stock_info(stock_name)
        print(f"Name: {stock_info.name}")
        print(f"Ticker: {stock_info.ticker}")
        print(f"Web ID: {stock_info.web_id}")
        print(f"Market: {stock_info.market}")
        print(f"ISIN: {stock_info.isin}")
        print(f"Active: {stock_info.is_active}")
        
    except TSETMCNotFoundError:
        print(f"Stock '{stock_name}' not found")
    except TSETMCError as e:
        print(f"Error getting stock info: {e}")


def demonstrate_price_history(client: TSETMCClient) -> None:
    """Demonstrate historical price data retrieval."""
    print_section("Historical Price Data")
    
    try:
        # Get price history for a stock
        stock_name = "پترول"
        start_date = "1403-10-01"  # More recent date range
        end_date = "1403-10-29"
        
        print(f"\nGetting price history for '{stock_name}' from {start_date} to {end_date}...")
        
        price_history = client.get_price_history(
            stock=stock_name,
            start_date=start_date,
            end_date=end_date,
            adjust_price=True,
            show_weekday=True,
            double_date=True  # Show both Jalali and Gregorian dates
        )
        
        print_dataframe(price_history, "Price History", max_rows=5)
        
        if not price_history.empty:
            # Calculate some basic statistics
            print(f"\nPrice Statistics:")
            print(f"Average Close Price: {price_history['Close'].mean():.2f}")
            print(f"Highest Price: {price_history['High'].max():.2f}")
            print(f"Lowest Price: {price_history['Low'].min():.2f}")
            print(f"Total Volume: {price_history['Volume'].sum():,}")
            
    except TSETMCNotFoundError:
        print(f"Stock '{stock_name}' not found")
    except TSETMCDataError:
        print(f"No price data available for the specified period")
    except TSETMCError as e:
        print(f"Error getting price history: {e}")


def demonstrate_market_indices(client: TSETMCClient) -> None:
    """Demonstrate market index data retrieval."""
    print_section("Market Indices")
    
    try:
        # Get market index data
        index_type = "CWI"  # Total market index
        start_date = "1403-10-01"  # More recent date range
        end_date = "1403-10-29"
        
        print(f"\nGetting {index_type} index history from {start_date} to {end_date}...")
        
        index_data = client.get_market_index(
            index_type=index_type,
            start_date=start_date,
            end_date=end_date,
            show_weekday=True,
            double_date=True
        )
        
        print_dataframe(index_data, f"{index_type} Index History", max_rows=5)
        
        if not index_data.empty:
            print(f"\nIndex Statistics:")
            print(f"Period Return: {((index_data['Adj Close'].iloc[-1] / index_data['Adj Close'].iloc[0]) - 1) * 100:.2f}%")
            print(f"Highest Value: {index_data['High'].max():.2f}")
            print(f"Lowest Value: {index_data['Low'].min():.2f}")
        
    except TSETMCDataError:
        print(f"No index data available for the specified period")
    except TSETMCError as e:
        print(f"Error getting market index: {e}")


def demonstrate_intraday_data(client: TSETMCClient) -> None:
    """Demonstrate intraday trading data."""
    print_section("Intraday Trading Data")
    
    try:
        # Get intraday trades for a stock
        stock_name = "پترول"
        start_date = "1403-10-15"  # Recent single date range
        end_date = "1403-10-16"
        
        print(f"\nGetting intraday trades for '{stock_name}' from {start_date} to {end_date}...")
        
        intraday_data = client.get_intraday_trades(
            stock=stock_name,
            start_date=start_date,
            end_date=end_date,
            show_progress=False  # Disable progress bar for demo
        )
        
        print_dataframe(intraday_data, "Intraday Trades", max_rows=5)
        
        if not intraday_data.empty:
            print(f"\nTrading Statistics:")
            print(f"Total Trades: {len(intraday_data):,}")
            print(f"Total Volume: {intraday_data['Volume'].sum():,}")
            print(f"Average Trade Size: {intraday_data['Volume'].mean():.2f}")
            print(f"Price Range: {intraday_data['Price'].min():.2f} - {intraday_data['Price'].max():.2f}")
        
    except TSETMCNotFoundError:
        print(f"Stock '{stock_name}' not found")
    except TSETMCDataError:
        print(f"No intraday data available for the specified period")
    except TSETMCError as e:
        print(f"Error getting intraday data: {e}")


def demonstrate_bulk_operations(client: TSETMCClient) -> None:
    """Demonstrate bulk data operations."""
    print_section("Bulk Data Operations")
    
    try:
        # Get stock list for multiple stocks
        stock_symbols = ["پترول", "خودرو", "فولاد"]
        print(f"\nBuilding stock list for markets: bourse, farabourse...")
        
        try:
            stock_list = client.build_stock_list(
                bourse=True,         # Correct parameter name 
                farabourse=False,    # Keep it simple for demo
                payeh=False,
                detailed_list=False,
                show_progress=False,
                save_excel=False,
                save_csv=False
            )
            
            print_dataframe(stock_list, "Stock List", max_rows=10)
        except Exception as e:
            print(f"Stock list building failed: {e}")
            print("Creating a simple demo stock list...")
            
            # Create a demo stock list for demonstration
            demo_stocks = pd.DataFrame([
                {'Name': 'شرکت ملی صنایع پتروشیمی', 'Market': 'بورس', 'WEB-ID': '46348559193224090'},
                {'Name': 'ایران خودرو', 'Market': 'بورس', 'WEB-ID': '65883838195688438'},
                {'Name': 'فولاد مبارکه اصفهان', 'Market': 'بورس', 'WEB-ID': '35700344742835695'}
            ])
            print_dataframe(demo_stocks, "Demo Stock List", max_rows=10)
        
        # Demonstrate bulk price concept (simplified)
        print(f"\nDemonstrating bulk price concept...")
        try:
            bulk_prices = client.get_bulk_price_data(
                stock_list=stock_symbols[:2],  # Limit to 2 stocks for demo
                param='Adj Final',             # Use correct default parameter
                jalali_date=True,
                save_excel=False
            )
            
            print_dataframe(bulk_prices, "Bulk Price Data", max_rows=5)
        except Exception as e:
            print(f"Bulk price data failed: {e}")
            print("This feature may require additional implementation for the current stock data.")
        
    except TSETMCError as e:
        print(f"Error in bulk operations: {e}")
    except Exception as e:
        print(f"Unexpected error in bulk operations: {e}")


def demonstrate_market_watch(client: TSETMCClient) -> None:
    """Demonstrate current market watch data."""
    print_section("Current Market Watch")
    
    try:
        print("\nGetting current market watch data...")
        
        market_data, order_book = client.get_market_watch()
        
        print_dataframe(market_data, "Market Watch Data", max_rows=5)
        
        if not market_data.empty:
            print(f"\nMarket Watch Summary:")
            print(f"Total stocks: {len(market_data)}")
            
            # Check available columns and show statistics accordingly
            available_columns = market_data.columns.tolist()
            print(f"Available columns: {', '.join(available_columns[:10])}...")  # Show first 10 columns
            
            # Try to find percentage change columns
            pct_columns = [col for col in available_columns if '%' in col or 'percent' in col.lower()]
            if pct_columns:
                print(f"\nPercentage change columns found: {', '.join(pct_columns)}")
                
                # Use the first percentage column for top gainers/losers
                pct_col = pct_columns[0]
                try:
                    top_gainers = market_data.nlargest(3, pct_col)
                    top_losers = market_data.nsmallest(3, pct_col)
                    
                    print(f"\nTop 3 Gainers (by {pct_col}):")
                    print(top_gainers[['Name', pct_col] + [col for col in ['Final', 'Close', 'Volume'] if col in available_columns]].to_string())
                    
                    print(f"\nTop 3 Losers (by {pct_col}):")
                    print(top_losers[['Name', pct_col] + [col for col in ['Final', 'Close', 'Volume'] if col in available_columns]].to_string())
                except Exception as e:
                    print(f"Could not calculate top gainers/losers: {e}")
            else:
                print("\nNo percentage change columns found, showing basic statistics...")
                if 'Volume' in available_columns:
                    print(f"Total volume traded: {market_data['Volume'].sum():,}")
                if 'Value' in available_columns:
                    print(f"Total value traded: {market_data['Value'].sum():,}")
        
        # Order book information
        if not order_book.empty:
            print_dataframe(order_book, "Order Book Sample", max_rows=3)
        else:
            print("\nOrder book data is empty")
        
    except TSETMCError as e:
        print(f"Error getting market watch data: {e}")
    except Exception as e:
        print(f"Unexpected error in market watch: {e}")
        print("Market watch feature may need additional configuration or network access.")


def demonstrate_error_handling(client: TSETMCClient) -> None:
    """Demonstrate proper error handling."""
    print_section("Error Handling Examples")
    
    # Example 1: Non-existent stock
    try:
        print("\nTrying to search for a non-existent stock...")
        result = client.search_stock("NonExistentStock123XYZ")
        if result.empty:
            print("✓ Correctly handled non-existent stock search")
        else:
            print(f"Found unexpected results: {len(result)} stocks")
    except TSETMCNotFoundError as e:
        print(f"✓ Caught expected error: {e}")
    except Exception as e:
        print(f"✓ Handled unexpected error: {e}")
    
    # Example 2: Invalid date range  
    try:
        print("\nTrying to get data with invalid date range...")
        client.get_price_history(
            stock="پترول",
            start_date="1404-01-01", 
            end_date="1403-01-01"  # End before start
        )
    except TSETMCError as e:
        print(f"✓ Caught expected error: {e}")
    except Exception as e:
        print(f"✓ Handled unexpected error: {e}")
    
    # Example 3: Empty stock name
    try:
        print("\nTrying to get info for empty stock name...")
        client.stock.get_stock_info("")
    except TSETMCError as e:
        print(f"✓ Caught expected error: {e}")
    except Exception as e:
        print(f"✓ Handled unexpected error: {e}")


def main() -> None:
    """Main function demonstrating TSETMC library usage."""
    print("TSETMC Library Usage Example")
    print("Tehran Stock Exchange Market Center API Client")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize the client
    print("\n🌐 Running live demo with real API calls...")
    client = TSETMCClient(
        timeout=30,  # 30 seconds timeout
        max_retries=3  # Retry failed requests up to 3 times
    )
    
    print(f"\nClient initialized: {client}")
    
    try:
        # Run all demonstrations with robust error handling
        print("\n" + "="*60)
        print("Starting comprehensive API demonstration...")
        print("="*60)
        
        demonstrate_stock_search(client)
        demonstrate_stock_info(client)
        demonstrate_price_history(client)
        demonstrate_market_indices(client)
        demonstrate_intraday_data(client)
        demonstrate_market_watch(client)
        demonstrate_bulk_operations(client)
        demonstrate_error_handling(client)
        
        print_section("Demo Complete")
        print("All examples completed successfully!")
        print("\nFor more information, check the documentation:")
        print("- Stock search: client.search_stock()")
        print("- Price history: client.get_price_history()")
        print("- Market indices: client.get_market_index()")
        print("- Intraday data: client.get_intraday_trades()")
        print("- Market watch: client.get_market_watch()")
        print("- Bulk operations: client.build_stock_list() and client.get_bulk_price_data()")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error occurred: {e}")
        print("This might be due to network issues or API unavailability")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up resources
        print("\nCleaning up...")


if __name__ == "__main__": 
    main()
