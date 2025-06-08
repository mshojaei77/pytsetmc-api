"""
Trading service for retrieving intraday trades, order book, and queue history.
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
import jdatetime
import asyncio
import aiohttp
import platform
import sys

from .base_service import BaseService
from .stock_service import StockService
from ..exceptions import TSETMCError, TSETMCAPIError, TSETMCDataError
from ..models import IntradayTrade, OrderBookData
from ..utils import (
    validate_jalali_date, convert_jalali_to_gregorian, 
    safe_int_conversion, safe_float_conversion
)


class TradingService(BaseService):
    """
    Service for retrieving intraday trading data.

    This service provides functionality to:
    - Get historical intraday trades
    - Get historical order book data
    - Get queue history at market close
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stock_service = StockService(**kwargs)

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
        
        This method is an alias for get_intraday_trades_history with compatible parameters.
        
        Args:
            stock: Stock name or symbol
            start_date: Start date in Jalali format (YYYY-MM-DD)
            end_date: End date in Jalali format (YYYY-MM-DD)
            jalali_date: Whether to use Jalali dates (always True for now)
            combined_datetime: Whether to combine date and time (not used currently)
            show_progress: Whether to show progress bar
            
        Returns:
            DataFrame with intraday trading data
            
        Example:
            >>> service = TradingService()
            >>> trades = service.get_intraday_trades('وخارزم', '1404-09-15', '1404-12-29')
        """
        return self.get_intraday_trades_history(
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            show_progress=show_progress
        )

    def get_intraday_trades_history(
        self,
        stock: str,
        start_date: str,
        end_date: str,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Get historical intraday trades for a stock between two dates.

        Args:
            stock: Stock name or symbol.
            start_date: Start date in Jalali format (YYYY-MM-DD).
            end_date: End date in Jalali format (YYYY-MM-DD).
            show_progress: If True, displays a progress bar.

        Returns:
            DataFrame with intraday trade data.
        """
        self._validate_stock_name(stock)
        self._validate_date_range(start_date, end_date)
        
        self.logger.info(f"Getting intraday trades for {stock} from {start_date} to {end_date}")
        
        try:
            web_id = self.stock_service.get_web_id(stock)
            trading_days = self._get_trading_days(web_id, start_date, end_date)
            
            if not trading_days:
                raise TSETMCDataError(f"No trading days found for {stock} in the specified period.")

            # Use synchronous approach for better reliability on Windows
            results = []
            max_days = min(len(trading_days), 5)  # Limit to 5 days for demo
            
            if show_progress:
                self.logger.info(f"Fetching intraday trades for {max_days} days...")
            
            for i, day in enumerate(trading_days[:max_days]):
                try:
                    if show_progress:
                        self.logger.info(f"Processing day {i+1}/{max_days}: {day}")
                    
                    result = self._fetch_day_trades_sync(web_id, day)
                    if not result.empty:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Could not fetch trades for {day}: {e}")
                    continue
            
            if results:
                df = pd.concat(results, ignore_index=True)
            else:
                df = pd.DataFrame()
            
            if df.empty:
                raise TSETMCDataError("No intraday trade data found.")
            
            return self._clean_dataframe(df)

        except Exception as e:
            if isinstance(e, TSETMCError):
                raise
            self.logger.error(f"Failed to get intraday trades history for {stock}: {e}")
            raise TSETMCAPIError(f"Could not retrieve intraday trades for {stock}.")
    
    def _fetch_day_trades_sync(self, web_id: str, j_date: str) -> pd.DataFrame:
        """Synchronous fallback for fetching intraday trades."""
        try:
            g_date = jdatetime.datetime.strptime(j_date, '%Y-%m-%d').togregorian().strftime('%Y%m%d')
            url = f"http://cdn.tsetmc.com/api/Trade/GetTradeHistory/{web_id}/{g_date}/false"
            
            response = self._make_request(url)
            data = response.json()
            
            if 'tradeHistory' not in data or not data['tradeHistory']:
                return pd.DataFrame()
                
            df = pd.DataFrame(data['tradeHistory'])
            
            if df.empty or len(df.columns) < 6:
                return pd.DataFrame()
            
            # Take the expected columns (adjust based on actual API response)
            df = df.iloc[:, 2:6]
            df.columns = ['Time', 'Volume', 'Price', 'nTran']
            df = df.sort_values(by='nTran').drop(columns=['nTran'])
            
            # Format time properly
            df['Time'] = df['Time'].astype(str).str.pad(6, 'left', '0').apply(
                lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}" if len(x) >= 6 else x
            )
            df['J-Date'] = j_date
            
            # Ensure numeric columns
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
            
            return df[['J-Date', 'Time', 'Volume', 'Price']].dropna()
            
        except Exception as e:
            self.logger.warning(f"Sync fetch failed for {web_id} on {j_date}: {e}")
            return pd.DataFrame()

    def get_intraday_ob_history(
        self,
        stock: str,
        start_date: str,
        end_date: str,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Get historical intraday order book data for a stock between two dates.

        Args:
            stock: Stock name or symbol.
            start_date: Start date in Jalali format (YYYY-MM-DD).
            end_date: End date in Jalali format (YYYY-MM-DD).
            show_progress: If True, displays a progress bar.

        Returns:
            DataFrame with intraday order book data.
        """
        self._validate_stock_name(stock)
        self._validate_date_range(start_date, end_date)

        self.logger.info(f"Getting intraday order book for {stock} from {start_date} to {end_date}")

        try:
            web_id = self.stock_service.get_web_id(stock)
            trading_days = self._get_trading_days(web_id, start_date, end_date)

            if not trading_days:
                raise TSETMCDataError(f"No trading days found for {stock} in the specified period.")
            
            tasks = [self._fetch_day_ob(web_id, day) for day in trading_days]
            results = asyncio.run(self._run_tasks_with_progress(tasks, show_progress, "Fetching Order Book Data"))

            df = pd.concat(results, ignore_index=True)

            if df.empty:
                raise TSETMCDataError("No intraday order book data found.")
                
            return self._clean_dataframe(df)
            
        except Exception as e:
            if isinstance(e, TSETMCError):
                raise
            self.logger.error(f"Failed to get intraday order book history for {stock}: {e}")
            raise TSETMCAPIError(f"Could not retrieve intraday order book data for {stock}.")

    def _get_trading_days(self, web_id: str, start_date: str, end_date: str) -> List[str]:
        """Get the list of trading days for a stock in a given period."""
        url = f"http://old.tsetmc.com/tsev2/data/InstTradeHistory.aspx?i={web_id}&Top=999999&A=0"
        response = self._make_request(url)
        
        days = []
        for item in response.text.split(';'):
            if not item: continue
            date_str = item.split('@')[0]
            greg_date = datetime.strptime(date_str, '%Y%m%d').date()
            jalali_date = str(jdatetime.date.fromgregorian(date=greg_date))
            
            if start_date <= jalali_date <= end_date:
                days.append(jalali_date)
        return days

    async def _run_tasks_with_progress(self, tasks: List, show_progress: bool, description: str):
        """Run asyncio tasks, optionally with a progress bar."""
        if show_progress:
            try:
                from tqdm.asyncio import tqdm
                return await tqdm.gather(*tasks, desc=description)
            except ImportError:
                # Fallback if tqdm is not available
                self.logger.info(f"{description}...")
                return await asyncio.gather(*tasks)
        else:
            return await asyncio.gather(*tasks)

    async def _get_async_session(self):
        """Create and return an aiohttp session."""
        from ..utils import create_http_headers
        headers = create_http_headers()
        return aiohttp.ClientSession(headers=headers)
    
    async def _fetch_day_trades(self, web_id: str, j_date: str) -> pd.DataFrame:
        """Fetch intraday trades for a single day."""
        g_date = jdatetime.datetime.strptime(j_date, '%Y-%m-%d').togregorian().strftime('%Y%m%d')
        url = f"http://cdn.tsetmc.com/api/Trade/GetTradeHistory/{web_id}/{g_date}/false"
        
        try:
            async with await self._get_async_session() as session:
                response = await self._make_async_request(session, url)
                data = await response.json()
                df = pd.DataFrame(data['tradeHistory'])
                if df.empty: 
                    return df
                
                df = df.iloc[:, 2:6]
                df.columns = ['Time', 'Volume', 'Price', 'nTran']
                df = df.sort_values(by='nTran').drop(columns=['nTran'])
                df['Time'] = df['Time'].astype(str).str.pad(6, 'left', '0').apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
                df['J-Date'] = j_date
                return df[['J-Date', 'Time', 'Volume', 'Price']]
        except Exception as e:
            self.logger.warning(f"Could not fetch trades for {web_id} on {j_date}: {e}")
            return pd.DataFrame()

    async def _fetch_day_ob(self, web_id: str, j_date: str) -> pd.DataFrame:
        """Fetch order book data for a single day."""
        g_date = jdatetime.datetime.strptime(j_date, '%Y-%m-%d').togregorian().strftime('%Y%m%d')
        
        try:
            async with await self._get_async_session() as session:
                # Get day's static thresholds (price limits)
                threshold_url = f"http://cdn.tsetmc.com/api/MarketData/GetStaticThreshold/{web_id}/{g_date}"
                threshold_res = await self._make_async_request(session, threshold_url)
                threshold_data = await threshold_res.json()
                day_ul = threshold_data['staticThreshold'][-1]['psGelStaMax']
                day_ll = threshold_data['staticThreshold'][-1]['psGelStaMin']

                # Get order book history
                ob_url = f"http://cdn.tsetmc.com/api/BestLimits/{web_id}/{g_date}"
                ob_res = await self._make_async_request(session, ob_url)
                ob_data = await ob_res.json()
                df = pd.DataFrame(ob_data['bestLimitsHistory'])
                if df.empty: 
                    return df

                df = df[(df['hEven'] >= 84500) & (df['hEven'] < 123000)]
                df = df.sort_values(['hEven', 'number'])
                df.columns = ['Time', 'Depth', 'Buy_Vol', 'Buy_No', 'Buy_Price', 'Sell_Price', 'Sell_No', 'Sell_Vol', 'idn', 'dEven', 'refID', 'insCode']
                df['Time'] = df['Time'].astype(str).str.pad(6, 'left', '0').apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
                df['J-Date'] = j_date
                df['Day_UL'] = day_ul
                df['Day_LL'] = day_ll
                
                return df[['J-Date', 'Time', 'Depth', 'Sell_No', 'Sell_Vol', 'Sell_Price', 'Buy_Price', 'Buy_Vol', 'Buy_No', 'Day_LL', 'Day_UL']]

        except Exception as e:
            self.logger.warning(f"Could not fetch order book for {web_id} on {j_date}: {e}")
            return pd.DataFrame() 