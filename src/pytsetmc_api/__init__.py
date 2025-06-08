"""
PyTSETMC API - A robust Python client for Tehran Stock Exchange Market Center data retrieval.

This package provides a comprehensive interface for accessing financial data
from the Tehran Stock Exchange Market Center (TSETMC), including:

- Stock price history and real-time data
- Market indices and sector information  
- Intraday trading data and order books
- Financial instrument search and metadata
- Market watch and trading statistics

The package is designed with modern Python best practices, following OOP and
SOLID principles for maintainable and extensible code.

Example:
    Basic usage for getting stock information:
    
    >>> from pytsetmc_api import TSETMCClient
    >>> client = TSETMCClient()
    >>> stock_info = client.get_stock_info("پترول")
    >>> price_history = client.get_price_history("پترول", "1404-01-01", "1403-01-01")
"""

__version__ = "0.1.0"
__author__ = "Mohammad Shojaei"
__email__ = "shojaei.dev@gmail.com"

# Core client imports
from .client import TSETMCClient

# Data model imports
from .models import (
    MarketType,
    StockInfo,
    PriceData,
    PriceHistory,
    IntradayTrade,
    IntradayData,
    OrderBookData,
    MarketIndex,
    SectorData,
    TradingData,
    SearchResult,
    APIResponse,
)

# Exception imports
from .exceptions import (
    TSETMCError,
    TSETMCAPIError,
    TSETMCValidationError,
    TSETMCNetworkError,
    TSETMCNotFoundError,
    TSETMCDataError,
    TSETMCRateLimitError,
)

# Service imports
from .services import (
    StockService,
    PriceService,
    MarketService,
    TradingService,
    DataService,
)

# Utility imports
from .utils import (
    validate_jalali_date,
    convert_jalali_to_gregorian,
    clean_persian_text,
)

# Main client already imported above

# Define public API
__all__ = [
    # Main client
    "TSETMCClient",
    # Core services
    "StockService",
    "PriceService",
    "MarketService",
    "TradingService",
    "DataService",
    # Custom exceptions
    "TSETMCError",
    "TSETMCAPIError",
    "TSETMCValidationError",
    "TSETMCNetworkError",
    "TSETMCNotFoundError",
    "TSETMCDataError",
    "TSETMCRateLimitError",
    # Core data models
    "MarketType",
    "StockInfo",
    "PriceData",
    "PriceHistory",
    "IntradayTrade",
    "IntradayData",
    "OrderBookData",
    "MarketIndex",
    "SectorData",
    "TradingData",
    "SearchResult",
    "APIResponse",
]

# Configure logging
# ... existing code ... 