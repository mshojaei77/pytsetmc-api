"""
Price service for retrieving historical price data and related financial information.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import jdatetime
import re

from .base_service import BaseService
from .stock_service import StockService
from ..exceptions import TSETMCError, TSETMCAPIError, TSETMCDataError
from ..models import PriceData, PriceHistory
from ..utils import (
    validate_jalali_date, convert_jalali_to_gregorian, 
    safe_int_conversion, safe_float_conversion, clean_persian_text
)


class PriceService(BaseService):
    """
    Service for retrieving historical price data and related financial information.
    
    This service provides functionality to:
    - Get historical price data with various options
    - Retrieve adjusted prices for corporate actions
    - Get return index (RI) history
    - Handle different date formats and market data
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stock_service = StockService(**kwargs)
    
    def get_history(
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
            
        Raises:
            TSETMCValidationError: If parameters are invalid
            TSETMCNotFoundError: If stock not found
            TSETMCDataError: If no data available for the period
            
        Example:
            >>> service = PriceService()
            >>> prices = service.get_history('خودرو', '1404-01-01', '1403-01-01')
        """
        # Validate inputs
        self._validate_stock_name(stock)
        if not ignore_date:
            self._validate_date_range(start_date, end_date)
        
        self.logger.info(f"Getting price history for {stock} from {start_date} to {end_date}")
        
        try:
            # Get stock web ID
            web_id = self.stock_service.get_web_id(stock)
            
            # Get stock basic info for market type
            stock_info = self.stock_service.get_stock_info(stock)
            
            # Fetch price data
            price_data = self._fetch_price_data(
                web_id=web_id,
                stock_name=stock,
                market_type=stock_info.market,
                start_date=start_date,
                end_date=end_date,
                adjust_price=adjust_price
            )
            
            if price_data.empty:
                raise TSETMCDataError(f"No price data available for {stock} in the specified period")
            
            # Apply formatting options
            formatted_data = self._format_price_data(
                price_data,
                show_weekday=show_weekday,
                double_date=double_date
            )
            
            self.logger.info(f"Retrieved {len(formatted_data)} price records for {stock}")
            return self._clean_dataframe(formatted_data)
            
        except Exception as e:
            if isinstance(e, (TSETMCError,)):
                raise
            raise TSETMCAPIError(f"Failed to get price history for '{stock}': {str(e)}")
    
    def get_ri_history(
        self,
        stock: str,
        start_date: str,
        end_date: str,
        ignore_date: bool = False,
        show_weekday: bool = False,
        double_date: bool = False
    ) -> pd.DataFrame:
        """
        Get return index (RI) history for a stock.
        
        Args:
            stock: Stock name or symbol
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            ignore_date: Whether to ignore date validation
            show_weekday: Whether to show weekday names
            double_date: Whether to show both Jalali and Gregorian dates
            
        Returns:
            DataFrame with return index data
            
        Example:
            >>> service = PriceService()
            >>> ri_data = service.get_ri_history('خودرو', '1404-01-01', '1403-01-01')
        """
        # Validate inputs
        self._validate_stock_name(stock)
        if not ignore_date:
            self._validate_date_range(start_date, end_date)
        
        self.logger.info(f"Getting RI history for {stock} from {start_date} to {end_date}")
        
        try:
            # Get stock web ID
            web_id = self.stock_service.get_web_id(stock)
            stock_info = self.stock_service.get_stock_info(stock)
            
            # Fetch RI data
            ri_data = self._fetch_ri_data(
                web_id=web_id,
                stock_name=stock,
                market_type=stock_info.market,
                start_date=start_date,
                end_date=end_date
            )
            
            if ri_data.empty:
                raise TSETMCDataError(f"No RI data available for {stock} in the specified period")
            
            # Apply formatting options
            formatted_data = self._format_price_data(
                ri_data,
                show_weekday=show_weekday,
                double_date=double_date
            )
            
            self.logger.info(f"Retrieved {len(formatted_data)} RI records for {stock}")
            return self._clean_dataframe(formatted_data)
            
        except Exception as e:
            if isinstance(e, (TSETMCError,)):
                raise
            raise TSETMCAPIError(f"Failed to get RI history for '{stock}': {str(e)}")
    
    def get_usd_rial_history(
        self,
        start_date: str,
        end_date: str,
        ignore_date: bool = False,
        show_weekday: bool = False,
        double_date: bool = False
    ) -> pd.DataFrame:
        """
        Get USD/RIAL exchange rate history.
        
        Args:
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            ignore_date: Whether to ignore date validation
            show_weekday: Whether to show weekday names
            double_date: Whether to show both Jalali and Gregorian dates
            
        Returns:
            DataFrame with USD/RIAL exchange rate data
        """
        if not ignore_date:
            self._validate_date_range(start_date, end_date)
        
        self.logger.info(f"Getting USD/RIAL history from {start_date} to {end_date}")
        
        try:
            # USD/RIAL has a specific web ID in TSETMC
            usd_rial_web_id = "46348559193224090"  # This is the web ID for USD/RIAL
            
            # Fetch exchange rate data
            exchange_data = self._fetch_price_data(
                web_id=usd_rial_web_id,
                stock_name="USD/RIAL",
                market_type="Currency",
                start_date=start_date,
                end_date=end_date,
                adjust_price=False
            )
            
            if exchange_data.empty:
                raise TSETMCDataError(f"No USD/RIAL data available for the specified period")
            
            # Apply formatting options
            formatted_data = self._format_price_data(
                exchange_data,
                show_weekday=show_weekday,
                double_date=double_date
            )
            
            return self._clean_dataframe(formatted_data)
            
        except Exception as e:
            if isinstance(e, (TSETMCError,)):
                raise
            raise TSETMCAPIError(f"Failed to get USD/RIAL history: {str(e)}")
    
    def _fetch_price_data(
        self,
        web_id: str,
        stock_name: str,
        market_type: str,
        start_date: str,
        end_date: str,
        adjust_price: bool = False
    ) -> pd.DataFrame:
        """
        Fetch raw price data from TSETMC.
        
        Args:
            web_id: Stock web ID
            stock_name: Stock name
            market_type: Market type
            start_date: Start date
            end_date: End date
            adjust_price: Whether to adjust prices
            
        Returns:
            DataFrame with raw price data
        """
        try:
            # Build the price data URL
            price_url = self._build_url(f"tsev2/data/InstTradeHistory.aspx?i={web_id}&Top=999999&A=0")
            
            # Make request
            response = self._make_request(price_url)
            
            # Parse the response
            price_data = self._parse_price_response(response.text, stock_name)
            
            # Filter by date range
            filtered_data = self._filter_by_date_range(price_data, start_date, end_date)
            
            # Apply price adjustments if requested
            if adjust_price:
                filtered_data = self._apply_price_adjustments(filtered_data)
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch price data for {stock_name}: {str(e)}")
            raise
    
    def _fetch_ri_data(
        self,
        web_id: str,
        stock_name: str,
        market_type: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch return index data from TSETMC.
        
        Args:
            web_id: Stock web ID
            stock_name: Stock name
            market_type: Market type
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with return index data
        """
        try:
            # Build the RI data URL (different endpoint for RI data)
            ri_url = self._build_url(f"tsev2/data/InstTradeHistory.aspx?i={web_id}&Top=999999&A=1")
            
            # Make request
            response = self._make_request(ri_url)
            
            # Parse the response
            ri_data = self._parse_ri_response(response.text, stock_name)
            
            # Filter by date range
            filtered_data = self._filter_by_date_range(ri_data, start_date, end_date)
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch RI data for {stock_name}: {str(e)}")
            raise
    
    def _parse_price_response(self, response_text: str, stock_name: str) -> pd.DataFrame:
        """
        Parse price data response from TSETMC.
        
        Args:
            response_text: Raw response text
            stock_name: Stock name for logging
            
        Returns:
            DataFrame with parsed price data
        """
        try:
            # TSETMC price data format: date,high,low,close,last,count,volume,value,open
            lines = response_text.strip().split('\n')
            
            price_records = []
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split(',')
                if len(parts) >= 9:
                    try:
                        # Parse date (YYYYMMDD format)
                        date_str = parts[0]
                        if len(date_str) == 8:
                            year = int(date_str[:4])
                            month = int(date_str[4:6])
                            day = int(date_str[6:8])
                            
                            # Convert to Jalali date
                            jalali_date = jdatetime.date(year, month, day)
                            
                            record = {
                                'Date': jalali_date.strftime('%Y-%m-%d'),
                                'Open': safe_float_conversion(parts[8]),
                                'High': safe_float_conversion(parts[1]),
                                'Low': safe_float_conversion(parts[2]),
                                'Close': safe_float_conversion(parts[3]),
                                'Last': safe_float_conversion(parts[4]),
                                'Count': safe_int_conversion(parts[5]),
                                'Volume': safe_int_conversion(parts[6]),
                                'Value': safe_int_conversion(parts[7])
                            }
                            price_records.append(record)
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Skipping invalid price record: {line} - {str(e)}")
                        continue
            
            return pd.DataFrame(price_records)
            
        except Exception as e:
            self.logger.error(f"Failed to parse price response for {stock_name}: {str(e)}")
            return pd.DataFrame()
    
    def _parse_ri_response(self, response_text: str, stock_name: str) -> pd.DataFrame:
        """
        Parse return index response from TSETMC.
        
        Args:
            response_text: Raw response text
            stock_name: Stock name for logging
            
        Returns:
            DataFrame with parsed RI data
        """
        try:
            # Similar to price data but with RI values
            lines = response_text.strip().split('\n')
            
            ri_records = []
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split(',')
                if len(parts) >= 9:
                    try:
                        # Parse date
                        date_str = parts[0]
                        if len(date_str) == 8:
                            year = int(date_str[:4])
                            month = int(date_str[4:6])
                            day = int(date_str[6:8])
                            
                            jalali_date = jdatetime.date(year, month, day)
                            
                            record = {
                                'Date': jalali_date.strftime('%Y-%m-%d'),
                                'RI_Open': safe_float_conversion(parts[8]),
                                'RI_High': safe_float_conversion(parts[1]),
                                'RI_Low': safe_float_conversion(parts[2]),
                                'RI_Close': safe_float_conversion(parts[3]),
                                'RI_Last': safe_float_conversion(parts[4]),
                                'Count': safe_int_conversion(parts[5]),
                                'Volume': safe_int_conversion(parts[6]),
                                'Value': safe_int_conversion(parts[7])
                            }
                            ri_records.append(record)
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Skipping invalid RI record: {line} - {str(e)}")
                        continue
            
            return pd.DataFrame(ri_records)
            
        except Exception as e:
            self.logger.error(f"Failed to parse RI response for {stock_name}: {str(e)}")
            return pd.DataFrame()
    
    def _filter_by_date_range(
        self,
        data: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Filter data by date range.
        
        Args:
            data: Input DataFrame with Date column
            start_date: Start date in Jalali format
            end_date: End date in Jalali format
            
        Returns:
            Filtered DataFrame
        """
        if data.empty or 'Date' not in data.columns:
            return data
        
        try:
            # Convert date strings to datetime for comparison
            data['Date_dt'] = pd.to_datetime(data['Date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Filter data
            mask = (data['Date_dt'] >= start_dt) & (data['Date_dt'] <= end_dt)
            filtered_data = data[mask].copy()
            
            # Remove temporary column
            filtered_data = filtered_data.drop('Date_dt', axis=1)
            
            return filtered_data.sort_values('Date').reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Failed to filter by date range: {str(e)}")
            return data
    
    def _apply_price_adjustments(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply price adjustments for corporate actions.
        
        Args:
            data: Input price DataFrame
            
        Returns:
            DataFrame with adjusted prices
        """
        if data.empty:
            return data
        
        try:
            adjusted_data = data.copy()
            
            # Calculate adjustment factors (simplified approach)
            # In a real implementation, you would need corporate action data
            
            # For now, we'll just add adjusted columns that are the same as original
            # This should be enhanced with actual corporate action data
            if 'Close' in adjusted_data.columns:
                adjusted_data['Adj_Close'] = adjusted_data['Close']
            if 'Open' in adjusted_data.columns:
                adjusted_data['Adj_Open'] = adjusted_data['Open']
            if 'High' in adjusted_data.columns:
                adjusted_data['Adj_High'] = adjusted_data['High']
            if 'Low' in adjusted_data.columns:
                adjusted_data['Adj_Low'] = adjusted_data['Low']
            
            return adjusted_data
            
        except Exception as e:
            self.logger.error(f"Failed to apply price adjustments: {str(e)}")
            return data
    
    def _format_price_data(
        self,
        data: pd.DataFrame,
        show_weekday: bool = False,
        double_date: bool = False
    ) -> pd.DataFrame:
        """
        Format price data with additional options.
        
        Args:
            data: Input DataFrame
            show_weekday: Whether to show weekday names
            double_date: Whether to show both Jalali and Gregorian dates
            
        Returns:
            Formatted DataFrame
        """
        if data.empty:
            return data
        
        try:
            formatted_data = data.copy()
            
            # Add weekday if requested
            if show_weekday and 'Date' in formatted_data.columns:
                formatted_data['Weekday'] = pd.to_datetime(formatted_data['Date']).dt.day_name()
            
            # Add Gregorian date if requested
            if double_date and 'Date' in formatted_data.columns:
                gregorian_dates = []
                for date_str in formatted_data['Date']:
                    try:
                        # Convert Jalali to Gregorian
                        gregorian_date = convert_jalali_to_gregorian(date_str)
                        gregorian_dates.append(gregorian_date)
                    except:
                        gregorian_dates.append('')
                
                formatted_data['Gregorian_Date'] = gregorian_dates
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Failed to format price data: {str(e)}")
            return data 