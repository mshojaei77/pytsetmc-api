"""
Main TSETMC client class providing unified access to all TSE market data services.
"""

import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime

from .services.stock_service import StockService
from .services.price_service import PriceService
from .services.market_service import MarketService
from .services.trading_service import TradingService
from .services.data_service import DataService
from .exceptions import TSETMCError, TSETMCValidationError
from .utils import setup_logging, validate_jalali_date


class TSETMCClient:
    """
    Main client for accessing Tehran Stock Exchange Market Center (TSETMC) data.
    
    This class provides a unified interface to all TSE market data services including
    stock information, price history, market indices, trading data, and bulk operations.
    
    Attributes:
        stock: StockService for stock search and basic operations
        price: PriceService for price history and related data
        market: MarketService for market indices and sector data
        trading: TradingService for intraday trades and order book data
        data: DataService for bulk operations and parallel data fetching
        
    Example:
        >>> client = TSETMCClient()
        >>> # Search for a stock
        >>> stock_info = client.stock.search('پترول')
        >>> # Get price history
        >>> prices = client.price.get_history('خودرو', '1404-01-01', '1403-01-01')
        >>> # Get market index
        >>> index = client.market.get_cwi_history('1404-01-01', '1403-01-01')
    """
    
    def __init__(
        self,
        base_url: str = "http://www.tsetmc.com",
        timeout: int = 30,
        max_retries: int = 3,
        enable_logging: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize the TSETMC client.
        
        Args:
            base_url: Base URL for TSETMC website
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_logging: Whether to enable logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup logging
        if enable_logging:
            setup_logging(log_level)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self._init_services()
        
        self.logger.info("TSETMC client initialized successfully")
    
    def _init_services(self) -> None:
        """Initialize all service classes."""
        service_config = {
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'logger': self.logger
        }
        
        self.stock = StockService(**service_config)
        self.price = PriceService(**service_config)
        self.market = MarketService(**service_config)
        self.trading = TradingService(**service_config)
        self.data = DataService(**service_config)
    
    def search_stock(self, query: str) -> pd.DataFrame:
        """
        Search for stocks by name or symbol.
        
        Args:
            query: Stock name or symbol to search for
            
        Returns:
            DataFrame with search results
            
        Example:
            >>> client = TSETMCClient()
            >>> results = client.search_stock('پترول')
        """
        return self.stock.search(query)
    
    def get_price_history(
        self,
        stock: str,
        start_date: str,
        end_date: str,
        ignore_date: bool = False,
        adjust_price: bool = False,
        show_weekday: bool = False,
        double_date: bool = False
    ) -> pd.DataFrame:
        """
        Get historical price data for a stock.
        
        Args:
            stock: Stock name or symbol
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            ignore_date: Whether to ignore date validation
            adjust_price: Whether to adjust prices for corporate actions
            show_weekday: Whether to show weekday names
            double_date: Whether to show both Jalali and Gregorian dates
            
        Returns:
            DataFrame with historical price data
            
        Example:
            >>> client = TSETMCClient()
            >>> prices = client.get_price_history('خودرو', '1404-01-01', '1403-01-01')
        """
        return self.price.get_history(
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            ignore_date=ignore_date,
            adjust_price=adjust_price,
            show_weekday=show_weekday,
            double_date=double_date
        )
    
    def get_market_index(
        self,
        index_type: str,
        start_date: str,
        end_date: str,
        ignore_date: bool = False,
        just_adj_close: bool = False,
        show_weekday: bool = False,
        double_date: bool = False
    ) -> pd.DataFrame:
        """
        Get historical data for market indices.
        
        Args:
            index_type: Type of index (CWI, EWI, CWPI, EWPI, FFI, MKT1I, MKT2I, INDI, LCI30, ACT50)
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            ignore_date: Whether to ignore date validation
            just_adj_close: Whether to return only adjusted close prices
            show_weekday: Whether to show weekday names
            double_date: Whether to show both Jalali and Gregorian dates
            
        Returns:
            DataFrame with market index data
            
        Example:
            >>> client = TSETMCClient()
            >>> index = client.get_market_index('CWI', '1404-01-01', '1403-01-01')
        """
        return self.market.get_index_history(
            index_type=index_type,
            start_date=start_date,
            end_date=end_date,
            ignore_date=ignore_date,
            just_adj_close=just_adj_close,
            show_weekday=show_weekday,
            double_date=double_date
        )
    
    def get_intraday_trades(
        self,
        stock: str,
        start_date: str,
        end_date: str,
        jalali_date: bool = True,
        combined_datetime: bool = False,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Get intraday trading data for a stock.
        
        Args:
            stock: Stock name or symbol
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            jalali_date: Whether to use Jalali dates
            combined_datetime: Whether to combine date and time
            show_progress: Whether to show progress bar
            
        Returns:
            DataFrame with intraday trading data
            
        Example:
            >>> client = TSETMCClient()
            >>> trades = client.get_intraday_trades('وخارزم', '1404-09-15', '1404-12-29')
        """
        return self.trading.get_intraday_trades(
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            jalali_date=jalali_date,
            combined_datetime=combined_datetime,
            show_progress=show_progress
        )
    
    def get_market_watch(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get current market watch data.
        
        Returns:
            Tuple of (market_data, order_book) DataFrames
            
        Example:
            >>> client = TSETMCClient()
            >>> market_data, order_book = client.get_market_watch()
        """
        return self.market.get_market_watch()
    
    def build_stock_list(
        self,
        bourse: bool = True,
        farabourse: bool = True,
        payeh: bool = True,
        detailed_list: bool = True,
        show_progress: bool = True,
        save_excel: bool = True,
        save_csv: bool = True,
        save_path: str = 'D:/FinPy-TSE Data/'
    ) -> pd.DataFrame:
        """
        Build comprehensive stock list from all markets.
        
        Args:
            bourse: Include main bourse stocks
            farabourse: Include farabourse stocks
            payeh: Include payeh market stocks
            detailed_list: Include detailed information
            show_progress: Show progress during operation
            save_excel: Save as Excel file
            save_csv: Save as CSV file
            save_path: Path to save files
            
        Returns:
            DataFrame with stock list
            
        Example:
            >>> client = TSETMCClient()
            >>> stocks = client.build_stock_list()
        """
        return self.data.build_stock_list(
            bourse=bourse,
            farabourse=farabourse,
            payeh=payeh,
            detailed_list=detailed_list,
            show_progress=show_progress,
            save_excel=save_excel,
            save_csv=save_csv,
            save_path=save_path
        )
    
    def get_bulk_price_data(
        self,
        stock_list: List[str],
        param: str = 'Adj Final',
        jalali_date: bool = True,
        save_excel: bool = True,
        save_path: str = 'D:/FinPy-TSE Data/Price Panel/'
    ) -> pd.DataFrame:
        """
        Get bulk price data for multiple stocks.
        
        Args:
            stock_list: List of stock names or symbols
            param: Price parameter to extract
            jalali_date: Use Jalali dates
            save_excel: Save as Excel file
            save_path: Path to save the file
            
        Returns:
            DataFrame with bulk price data
            
        Example:
            >>> client = TSETMCClient()
            >>> prices = client.get_bulk_price_data(['خودرو', 'پترول', 'فولاد'])
        """
        return self.data.build_price_panel(
            stock_list=stock_list,
            param=param,
            jalali_date=jalali_date,
            save_excel=save_excel,
            save_path=save_path
        )
    
    def __repr__(self) -> str:
        """String representation of the client."""
        return f"TSETMCClient(base_url='{self.base_url}', timeout={self.timeout})"
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logger.info("TSETMC client session ended") 