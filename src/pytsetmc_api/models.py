"""
Data models for the TSETMC API package.

This module defines Pydantic models for representing financial data structures
returned by the Tehran Stock Exchange Market Center API. These models provide
type safety, validation, and serialization capabilities.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class MarketType(str, Enum):
    """Enumeration of market types in Tehran Stock Exchange."""
    
    BOURSE = "بورس"
    FARABOURSE = "فرابورس"
    PAYEH_ZARD = "پایه زرد"
    PAYEH_NARENJI = "پایه نارنجی"
    PAYEH_GHERMEZ = "پایه قرمز"
    KOCHAK_MOTAVASET = "کوچک و متوسط فرابورس"
    UNKNOWN = "نامعلوم"


class StockInfo(BaseModel):
    """Model representing basic stock information."""
    
    model_config = ConfigDict(use_enum_values=True)

    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Full company name")
    web_id: str = Field(..., description="Unique web identifier for the stock")
    market: MarketType = Field(..., description="Market where the stock is traded")
    is_active: bool = Field(True, description="Whether the stock is currently active")
    isin: Optional[str] = Field(None, description="International Securities Identification Number")
    
    @field_validator('ticker', 'name')
    @classmethod
    def clean_text_fields(cls, v: str) -> str:
        """Clean and normalize Persian text fields."""
        if not v:
            raise ValueError("Text field cannot be empty")
        return v.strip()


class PriceData(BaseModel):
    """Model representing price data for a specific date."""
    
    trade_date: date = Field(..., description="Trading date")
    open: Optional[Decimal] = Field(None, description="Opening price")
    high: Optional[Decimal] = Field(None, description="Highest price")
    low: Optional[Decimal] = Field(None, description="Lowest price")
    close: Optional[Decimal] = Field(None, description="Closing price")
    last: Optional[Decimal] = Field(None, description="Last traded price")
    volume: Optional[int] = Field(None, description="Trading volume")
    value: Optional[Decimal] = Field(None, description="Trading value")
    count: Optional[int] = Field(None, description="Number of trades")
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_numeric_fields(cls, v):
        """Convert numeric fields to appropriate types."""
        if v is None or v == '' or v == 0:
            return None
        if isinstance(v, (int, float, Decimal)):
            return v
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            return None


class PriceHistory(BaseModel):
    """Model representing historical price data for a stock."""
    
    stock_info: StockInfo = Field(..., description="Stock information")
    price_data: List[PriceData] = Field(..., description="List of historical price data")
    start_date: date = Field(..., description="Start date of the data range")
    end_date: date = Field(..., description="End date of the data range")
    adjusted: bool = Field(False, description="Whether prices are adjusted for splits/dividends")
    
    @field_validator('price_data')
    @classmethod
    def validate_price_data(cls, v: List[PriceData]) -> List[PriceData]:
        """Validate that price data is not empty."""
        if not v:
            raise ValueError("Price data cannot be empty")
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'PriceHistory':
        """Validate that start date is before end date."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
        return self


class IntradayTrade(BaseModel):
    """Model representing a single intraday trade."""
    
    time: datetime = Field(..., description="Trade timestamp")
    price: Decimal = Field(..., description="Trade price")
    volume: int = Field(..., description="Trade volume")
    value: Decimal = Field(..., description="Trade value")
    
    @field_validator('price', 'value')
    @classmethod
    def validate_positive_decimal(cls, v: Decimal) -> Decimal:
        """Validate that decimal values are positive."""
        if v <= 0:
            raise ValueError("Price and value must be positive")
        return v
    
    @field_validator('volume')
    @classmethod
    def validate_positive_volume(cls, v: int) -> int:
        """Validate that volume is positive."""
        if v <= 0:
            raise ValueError("Volume must be positive")
        return v


class IntradayData(BaseModel):
    """Model representing intraday trading data for a stock."""
    
    stock_info: StockInfo = Field(..., description="Stock information")
    trades: List[IntradayTrade] = Field(..., description="List of intraday trades")
    trade_date: date = Field(..., description="Trading date")
    
    @field_validator('trades')
    @classmethod
    def validate_trades(cls, v: List[IntradayTrade]) -> List[IntradayTrade]:
        """Validate that trades list is not empty."""
        if not v:
            raise ValueError("Trades list cannot be empty")
        return v


class OrderBookLevel(BaseModel):
    """Model representing a single level in the order book."""
    
    price: Decimal = Field(..., description="Price level")
    volume: int = Field(..., description="Volume at this price level")
    count: int = Field(..., description="Number of orders at this price level")


class OrderBookData(BaseModel):
    """Model representing order book data for a stock."""
    
    stock_info: StockInfo = Field(..., description="Stock information")
    bid_levels: List[OrderBookLevel] = Field(..., description="Bid side of order book")
    ask_levels: List[OrderBookLevel] = Field(..., description="Ask side of order book")
    timestamp: datetime = Field(..., description="Order book timestamp")
    
    @field_validator('bid_levels', 'ask_levels')
    @classmethod
    def validate_order_levels(cls, v: List[OrderBookLevel]) -> List[OrderBookLevel]:
        """Validate that order book levels are not empty."""
        if not v:
            raise ValueError("Order book levels cannot be empty")
        return v


class MarketIndex(BaseModel):
    """Model representing market index data."""
    
    name: str = Field(..., description="Index name")
    value: Decimal = Field(..., description="Index value")
    change: Optional[Decimal] = Field(None, description="Index change")
    change_percent: Optional[Decimal] = Field(None, description="Index change percentage")
    timestamp: datetime = Field(..., description="Index data timestamp")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that index name is not empty."""
        if not v.strip():
            raise ValueError("Index name cannot be empty")
        return v.strip()


class SectorData(BaseModel):
    """Model representing sector/industry data."""
    
    sector_name: str = Field(..., description="Sector name")
    web_id: str = Field(..., description="Sector web identifier")
    index_value: Optional[Decimal] = Field(None, description="Sector index value")
    stocks: List[StockInfo] = Field(default_factory=list, description="Stocks in this sector")
    
    @field_validator('sector_name')
    @classmethod
    def validate_sector_name(cls, v: str) -> str:
        """Validate that sector name is not empty."""
        if not v.strip():
            raise ValueError("Sector name cannot be empty")
        return v.strip()


class TradingStatistics(BaseModel):
    """Model representing trading statistics for a period."""
    
    total_volume: int = Field(..., description="Total trading volume")
    total_value: Decimal = Field(..., description="Total trading value")
    total_trades: int = Field(..., description="Total number of trades")
    active_stocks: int = Field(..., description="Number of active stocks")
    advancing_stocks: int = Field(0, description="Number of advancing stocks")
    declining_stocks: int = Field(0, description="Number of declining stocks")
    unchanged_stocks: int = Field(0, description="Number of unchanged stocks")


class TradingData(BaseModel):
    """Model representing comprehensive trading data."""
    
    trade_date: date = Field(..., description="Trading date")
    statistics: TradingStatistics = Field(..., description="Trading statistics")
    top_gainers: List[StockInfo] = Field(default_factory=list, description="Top gaining stocks")
    top_losers: List[StockInfo] = Field(default_factory=list, description="Top losing stocks")
    most_active: List[StockInfo] = Field(default_factory=list, description="Most active stocks")


class MarketWatch(BaseModel):
    """Model representing market watch data."""
    
    timestamp: datetime = Field(..., description="Market watch timestamp")
    indices: List[MarketIndex] = Field(..., description="Market indices")
    trading_data: TradingData = Field(..., description="Trading data")
    currency_rates: Dict[str, Decimal] = Field(default_factory=dict, description="Currency exchange rates")


class SearchResult(BaseModel):
    """Model representing search results for stocks."""
    
    query: str = Field(..., description="Original search query")
    results: List[StockInfo] = Field(..., description="List of matching stocks")
    total_results: int = Field(..., description="Total number of results")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate that search query is not empty."""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_results_count(self) -> 'SearchResult':
        """Validate that total results matches the length of results list."""
        if len(self.results) != self.total_results:
            self.total_results = len(self.results)
        return self


class APIResponse(BaseModel):
    """Model representing a generic API response."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp") 