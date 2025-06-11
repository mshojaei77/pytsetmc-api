# PyTSETMC API

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust Python client for Tehran Stock Exchange Market Center (TSETMC) data retrieval. This package provides a comprehensive interface for accessing Iranian stock market data, including historical prices, real-time information, market indices, and trading statistics.

## 🚀 Features

- 📈 **Stock Data**: Comprehensive stock information and price history
- 📊 **Market Indices**: Access to various market indices (CWI, EWI, etc.)
- ⚡ **Intraday Data**: Real-time trading data and transaction history
- 🔍 **Search**: Advanced stock search with fallback mechanisms
- 🛡️ **Robust Error Handling**: Production-ready error handling and validation
- 🔧 **Type Safety**: Full type hints and validation with Pydantic
- 🌐 **Cross-Platform**: Windows-compatible async handling
- 📚 **Rich Documentation**: Comprehensive examples and API documentation
- ✨ **2025 Best Practices**: Modern Python patterns and robust implementation

## 📦 Installation

### Requirements

- Python 3.9 or higher
- Windows/Linux/macOS compatible

### Install latest (GitHub HEAD)

```bash
# Development snapshot — requires git installed
uv pip install "git+https://github.com/mshojaei77/pytsetmc-api.git@main"
# or
pip install "git+https://github.com/mshojaei77/pytsetmc-api.git@main"
```

After installation you get the `pytsetmc` command-line tool:

```bash
pytsetmc --help             # list available commands
pytsetmc search پترول       # quick stock search
```

### For Development

```bash
git clone https://github.com/mshojaei77/pytsetmc-api.git
cd pytsetmc-api
uv pip install -e .
```

## 🚀 Quick Start

```python
from pytsetmc_api import TSETMCClient
from pytsetmc_api.exceptions import TSETMCError, TSETMCNotFoundError

# Initialize the client with robust settings
client = TSETMCClient(
    timeout=30,
    max_retries=3,
    enable_logging=True
)

# Search for stocks with error handling
try:
    stocks = client.search_stock("پترول")
    print(f"Found {len(stocks)} stocks:")
    print(stocks[['Name', 'Symbol', 'Market']].head())
except TSETMCError as e:
    print(f"Search failed: {e}")

# Get detailed stock information
try:
    stock_info = client.stock.get_stock_info("پترول")
    print(f"Stock: {stock_info.name} ({stock_info.ticker})")
    print(f"Market: {stock_info.market}")
    print(f"ISIN: {stock_info.isin}")
except TSETMCNotFoundError:
    print("Stock not found")
except TSETMCError as e:
    print(f"Error: {e}")
```

## 📊 Working Examples

### Stock Price History

```python
from pytsetmc_api import TSETMCClient

client = TSETMCClient()

# Get historical price data
try:
    price_history = client.get_price_history(
        stock="پترول",
        start_date="1403-10-01",
        end_date="1403-10-29",
        adjust_price=True,
        show_weekday=True,
        double_date=True  # Shows both Jalali and Gregorian dates
    )
    
    if not price_history.empty:
        print(f"Retrieved {len(price_history)} price records")
        print(price_history.head())
        
        # Calculate returns
        if 'Close' in price_history.columns:
            returns = price_history['Close'].pct_change()
            print(f"Average daily return: {returns.mean():.4f}")
    else:
        print("No price data available for the specified period")
        
except Exception as e:
    print(f"Price history error: {e}")
```

### Market Indices

```python
# Get market index data (This works reliably!)
try:
    market_index = client.get_market_index(
        index_type="CWI",  # Total market index
        start_date="1403-10-01",
        end_date="1403-10-29"
    )
    
    print(f"CWI Index History ({len(market_index)} days):")
    print(market_index.head())
    
    # Calculate index statistics
    if not market_index.empty and 'Close' in market_index.columns:
        start_value = market_index['Close'].iloc[0]
        end_value = market_index['Close'].iloc[-1]
        total_return = ((end_value - start_value) / start_value) * 100
        print(f"Period Return: {total_return:.2f}%")
        
except Exception as e:
    print(f"Market index error: {e}")
```

### Intraday Trading Data

```python
# Get intraday trading data
try:
    trades = client.get_intraday_trades(
        stock="پترول",
        start_date="1403-10-15",
        end_date="1403-10-16",
        show_progress=True
    )
    
    if not trades.empty:
        print(f"Retrieved {len(trades):,} intraday trades")
        print(trades.head())
        
        # Trading statistics
        total_volume = trades['Volume'].sum()
        avg_price = trades['Price'].mean()
        print(f"Total Volume: {total_volume:,}")
        print(f"Average Price: {avg_price:.2f}")
    else:
        print("No intraday data available")
        
except Exception as e:
    print(f"Intraday data error: {e}")
```

### Market Watch (Real-time Data)

```python
# Get current market watch data
try:
    market_data, order_book = client.get_market_watch()
    
    if not market_data.empty:
        print(f"Market Watch: {len(market_data)} stocks")
        print("Available columns:", list(market_data.columns))
        
        # Find percentage change columns
        pct_columns = [col for col in market_data.columns if '%' in col]
        if pct_columns:
            print(f"Percentage columns: {pct_columns}")
        
    if not order_book.empty:
        print(f"Order Book: {len(order_book)} entries")
        
except Exception as e:
    print(f"Market watch error: {e}")
    print("Market watch may require additional configuration")
```

## 🛠️ Advanced Usage

### Robust Error Handling

```python
from pytsetmc_api import TSETMCClient
from pytsetmc_api.exceptions import (
    TSETMCError, 
    TSETMCNotFoundError, 
    TSETMCValidationError,
    TSETMCAPIError,
    TSETMCNetworkError
)

client = TSETMCClient()

def safe_stock_search(query: str):
    """Example of robust stock search with comprehensive error handling"""
    try:
        # Validate input
        if not query or len(query.strip()) < 2:
            raise TSETMCValidationError("Query must be at least 2 characters")
            
        results = client.search_stock(query.strip())
        
        if results.empty:
            print(f"No stocks found for '{query}'")
            return None
            
        print(f"Found {len(results)} stocks for '{query}'")
        return results
        
    except TSETMCValidationError as e:
        print(f"Validation error: {e}")
    except TSETMCNotFoundError as e:
        print(f"Not found: {e}")
    except TSETMCNetworkError as e:
        print(f"Network error: {e}")
    except TSETMCAPIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

# Usage
results = safe_stock_search("پترول")
if results is not None:
    print(results.head())
```

### Batch Operations

```python
# Get data for multiple stocks safely
def get_multiple_stocks_info(stock_names: list):
    """Get information for multiple stocks with error handling"""
    results = {}
    
    for stock in stock_names:
        try:
            stock_info = client.stock.get_stock_info(stock)
            results[stock] = {
                'name': stock_info.name,
                'ticker': stock_info.ticker,
                'market': stock_info.market,
                'web_id': stock_info.web_id
            }
            print(f"✓ {stock}: {stock_info.name}")
            
        except Exception as e:
            print(f"✗ {stock}: {e}")
            results[stock] = None
    
    return results

# Usage
stocks = ["پترول", "خودرو", "فولاد", "بانک"]
stock_info = get_multiple_stocks_info(stocks)
```

### Custom Configuration

```python
# Initialize client with custom settings
client = TSETMCClient(
    timeout=60,           # Longer timeout for slow networks
    max_retries=5,        # More retries for unreliable connections
    enable_logging=True,  # Enable detailed logging
    log_level="DEBUG"     # Detailed debug information
)

# Use context manager for automatic cleanup
with TSETMCClient() as client:
    try:
        data = client.search_stock("پترول")
        print(data)
    except Exception as e:
        print(f"Error: {e}")
# Client automatically cleaned up
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set custom timeouts and limits
export TSETMC_TIMEOUT=60
export TSETMC_MAX_RETRIES=5
export TSETMC_LOG_LEVEL=INFO
```

### Logging Configuration

```python
import logging
from pytsetmc_api import TSETMCClient

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

client = TSETMCClient(enable_logging=True, log_level="INFO")
```

## 📋 API Reference

### `TSETMCClient`

The main entry point for all API operations.

```python
client = TSETMCClient(
    base_url: str = "http://www.tsetmc.com",
    timeout: int = 30,
    max_retries: int = 3,
    enable_logging: bool = True,
    log_level: str = "INFO"
)
```

#### Main Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `search_stock(query)` | Search for stocks by name/symbol | `pd.DataFrame` |
| `get_price_history(stock, start_date, end_date, **kwargs)` | Get historical prices | `pd.DataFrame` |
| `get_market_index(index_type, start_date, end_date, **kwargs)` | Get market index data | `pd.DataFrame` |
| `get_intraday_trades(stock, start_date, end_date, **kwargs)` | Get intraday trading data | `pd.DataFrame` |
| `get_market_watch()` | Get real-time market data | `Tuple[pd.DataFrame, pd.DataFrame]` |

#### Service Objects

- `client.stock`: Stock information and searching
- `client.price`: Historical price data
- `client.market`: Market indices and market watch
- `client.trading`: Intraday trades and order book
- `client.data`: Bulk operations and stock lists

### Available Market Indices

| Index | Description |
|-------|-------------|
| `CWI` | Total Market Index (Cap-Weighted) |
| `EWI` | Equal-Weighted Index |
| `CWPI` | Price Index (Cap-Weighted) |
| `EWPI` | Equal-Weighted Price Index |
| `FFI` | Free Float Index |
| `MKT1I` | First Market Index |
| `MKT2I` | Second Market Index |

## 🧪 Testing

```bash
# Run the main demo to test all functionality
python main.py

# Expected output:
# - Stock search results
# - Market index data
# - Intraday trading data
# - Error handling demonstrations
```

## 🐛 Troubleshooting

### Common Issues

1. **Network Timeouts**: Increase timeout settings
   ```python
   client = TSETMCClient(timeout=60)
   ```

2. **No Data Available**: Check date ranges and stock symbols
   ```python
   # Use recent dates
   start_date = "1403-10-01"
   end_date = "1403-10-29"
   ```

3. **API Endpoint Changes**: The library includes fallback mechanisms
   ```python
   # Robust search with fallbacks
   results = client.search_stock("پترول")
   ```

### Windows-Specific Issues

The library is optimized for Windows compatibility:
- Uses synchronous operations where needed
- Handles Windows async event loop policies
- Compatible with PowerShell and Command Prompt

## 📄 Data Models

### StockInfo
```python
@dataclass
class StockInfo:
    name: str
    ticker: str
    web_id: str
    market: str
    isin: str
    active: bool = True
```

### Key DataFrame Columns

**Price History:**
- `Date`: Date in Jalali format
- `Open`, `High`, `Low`, `Close`: Price data
- `Volume`: Trading volume
- `Adj Close`: Adjusted closing price

**Intraday Trades:**
- `J-Date`: Jalali date
- `Time`: Trade time
- `Volume`: Trade volume
- `Price`: Trade price

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/mshojaei77/pytsetmc-api.git
cd pytsetmc-api
uv pip install -e .
python main.py  # Test the installation
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This package is not officially affiliated with Tehran Stock Exchange Market Center (TSETMC). It is an independent client library for accessing publicly available data.

**Important Notes:**
- Use responsibly and respect rate limits
- Data may have delays or inaccuracies
- For production use, implement additional error handling
- Consider caching frequently accessed data

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/mshojaei77/pytsetmc-api/issues)
- 📚 **Documentation**: This README and inline code documentation
- 💬 **Questions**: Open a GitHub Discussion

## 🏆 Acknowledgments

- Tehran Stock Exchange Market Center for providing public data access
- Iranian developer community for feedback and contributions
- All contributors who help improve this library

---

**Made with ❤️ for the Iranian developer community**

*Last updated: 2025 - Robust, production-ready implementation*