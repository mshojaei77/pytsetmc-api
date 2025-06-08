"""
Base service class providing common functionality for all TSETMC services.
"""

import logging
import asyncio
import aiohttp
import requests
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
import time

from ..exceptions import (
    TSETMCError, TSETMCAPIError, TSETMCNetworkError, 
    TSETMCRateLimitError, TSETMCValidationError
)
from ..utils import create_http_headers, retry_on_failure, safe_int_conversion, safe_float_conversion


class BaseService(ABC):
    """
    Abstract base class for all TSETMC services.
    
    Provides common functionality including:
    - HTTP request handling (sync and async)
    - Error handling and retries
    - Rate limiting
    - Logging
    - Data validation
    """
    
    def __init__(
        self,
        base_url: str = "http://www.tsetmc.com",
        timeout: int = 30,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the base service.
        
        Args:
            base_url: Base URL for TSETMC website
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            logger: Logger instance
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Session for connection pooling
        self._session = None
    
    def _get_session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(create_http_headers())
        return self._session
    
    def _rate_limit(self) -> None:
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    @retry_on_failure(max_retries=3)
    def _make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Make HTTP request with error handling and retries.
        
        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            data: Request data (will be JSON encoded if Content-Type is application/json)
            headers: Additional headers
            
        Returns:
            Response object
            
        Raises:
            TSETMCNetworkError: For network-related errors
            TSETMCAPIError: For API-related errors
            TSETMCRateLimitError: For rate limiting errors
        """
        self._rate_limit()
        
        session = self._get_session()
        
        # Merge headers
        request_headers = session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Handle JSON data
        json_data = None
        form_data = data
        if data and request_headers.get('Content-Type') == 'application/json':
            import json
            json_data = json.dumps(data)
            form_data = None
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            response = session.request(
                method=method,
                url=url,
                params=params,
                data=json_data or form_data,
                headers=request_headers,
                timeout=self.timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                raise TSETMCRateLimitError("Rate limit exceeded")
            
            # Check for other HTTP errors
            if not response.ok:
                raise TSETMCAPIError(
                    f"HTTP {response.status_code}: {response.reason}",
                    status_code=response.status_code
                )
            
            return response
            
        except requests.exceptions.Timeout:
            raise TSETMCNetworkError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise TSETMCNetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise TSETMCNetworkError(f"Request error: {str(e)}")
    
    async def _make_async_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> aiohttp.ClientResponse:
        """
        Make asynchronous HTTP request.
        
        Args:
            session: aiohttp session
            url: Request URL
            method: HTTP method
            params: Query parameters
            data: Request data
            headers: Additional headers
            
        Returns:
            Response object
            
        Raises:
            TSETMCNetworkError: For network-related errors
            TSETMCAPIError: For API-related errors
        """
        try:
            self.logger.debug(f"Making async {method} request to {url}")
            
            async with session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                # Check for rate limiting
                if response.status == 429:
                    raise TSETMCRateLimitError("Rate limit exceeded")
                
                # Check for other HTTP errors
                if response.status >= 400:
                    raise TSETMCAPIError(
                        f"HTTP {response.status}: {response.reason}",
                        status_code=response.status
                    )
                
                return response
                
        except asyncio.TimeoutError:
            raise TSETMCNetworkError(f"Request timeout after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise TSETMCNetworkError(f"Request error: {str(e)}")
    
    def _validate_date_range(self, start_date: str, end_date: str) -> None:
        """
        Validate date range parameters.
        
        Args:
            start_date: Start date in Jalali format
            end_date: End date in Jalali format
            
        Raises:
            TSETMCValidationError: If dates are invalid
        """
        from ..utils import validate_jalali_date
        
        # Validate and normalize both dates
        try:
            normalized_start = validate_jalali_date(start_date)
            normalized_end = validate_jalali_date(end_date)
        except TSETMCValidationError as e:
            # Re-raise with more specific message
            if "start" not in str(e).lower():
                if start_date in str(e):
                    raise TSETMCValidationError(f"Invalid start date format: {start_date}")
                else:
                    raise TSETMCValidationError(f"Invalid end date format: {end_date}")
            raise
        
        # Check if start_date is before end_date using normalized dates
        start_parts = [int(x) for x in normalized_start.split('-')]
        end_parts = [int(x) for x in normalized_end.split('-')]
        
        if start_parts > end_parts:
            raise TSETMCValidationError("Start date must be before end date")
    
    def _validate_stock_name(self, stock: str) -> None:
        """
        Validate stock name parameter.
        
        Args:
            stock: Stock name or symbol
            
        Raises:
            TSETMCValidationError: If stock name is invalid
        """
        if not stock or not isinstance(stock, str):
            raise TSETMCValidationError("Stock name must be a non-empty string")
        
        if len(stock.strip()) == 0:
            raise TSETMCValidationError("Stock name cannot be empty")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize DataFrame columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        cleaned_df = df.copy()
        
        # Convert numeric columns with proper error handling
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                # Try to convert to numeric, keeping non-numeric as-is
                try:
                    numeric_series = pd.to_numeric(cleaned_df[col], errors='coerce')
                    # Only replace if we have valid numeric data
                    if not numeric_series.isna().all():
                        cleaned_df[col] = numeric_series
                except (ValueError, TypeError):
                    # If conversion fails, keep original data
                    continue
        
        # Remove completely empty rows and columns
        cleaned_df = cleaned_df.dropna(how='all', axis=0)
        cleaned_df = cleaned_df.dropna(how='all', axis=1)
        
        return cleaned_df
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full URL
        """
        if endpoint.startswith('http'):
            return endpoint
        
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}"
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        if self._session:
            self._session.close()