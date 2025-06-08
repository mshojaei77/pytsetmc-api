"""
Market service for retrieving market-level data like indices and market watch.
"""

import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import re
import jdatetime

from .base_service import BaseService
from ..exceptions import TSETMCError, TSETMCAPIError, TSETMCDataError, TSETMCValidationError
from ..models import MarketIndex, TradingData
from ..utils import (
    safe_int_conversion as safe_int, 
    safe_float_conversion as safe_float, 
    clean_persian_text
)


class IndexType(str, Enum):
    """Enumeration for different market index types."""
    CWI = "CWI"          # شاخص کل
    EWI = "EWI"          # شاخص کل هم‌وزن
    CWPI = "CWPI"        # شاخص قیمت وزنی-ارزشی
    EWPI = "EWPI"        # شاخص قیمت هم‌وزن
    FFI = "FFI"          # شاخص شناور آزاد
    MKT1I = "MKT1I"      # شاخص بازار اول
    MKT2I = "MKT2I"      # شاخص بازار دوم
    INDI = "INDI"        # شاخص صنعت
    LCI30 = "LCI30"      # شاخص 30 شرکت بزرگ
    ACT50 = "ACT50"      # شاخص 50 شرکت فعال تر


class MarketService(BaseService):
    """
    Service for retrieving market-level data, including market indices and market watch.

    This service provides functionality to:
    - Get historical data for various market indices
    - Get the current market watch data
    - Retrieve data for all stocks in a specific sector
    """

    _INDEX_WEB_IDS = {
        IndexType.CWI: "32097828799138957",    # شاخص كل
        IndexType.EWI: "67130298613737946",    # شاخص كل (هم وزن)
        IndexType.CWPI: "5798407779416661",     # شاخص قيمت (وزني-ارزشي)
        IndexType.EWPI: "8384385859414435",     # شاخص قيمت (هم وزن)
        IndexType.FFI: "49579049405614711",    # شاخص آزاد شناور
        IndexType.MKT1I: "62752761908615603",    # شاخص بازار اول
        IndexType.MKT2I: "71704845530629737",    # شاخص بازار دوم
        IndexType.INDI: "43754960038275285",    # شاخص صنعت
        IndexType.LCI30: "10523825119011581",    # شاخص 30 شركت بزرگ
        IndexType.ACT50: "46342955726788357",    # شاخص 50 شركت فعال تر
    }

    def get_index_history(
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
        Get historical data for a specified market index.

        Args:
            index_type: The type of index to retrieve (e.g., 'CWI', 'EWI').
            start_date: Start date in Jalali format (YYYY-MM-DD).
            end_date: End date in Jalali format (YYYY-MM-DD).
            ignore_date: If True, ignores date range and fetches all available data.
            just_adj_close: If True, returns only the adjusted close values.
            show_weekday: If True, adds a 'Weekday' column.
            double_date: If True, adds a Gregorian 'Date' column.

        Returns:
            DataFrame with historical index data.

        Raises:
            TSETMCValidationError: If index_type or dates are invalid.
            TSETMCDataError: If no data is available for the index.
        """
        try:
            index_enum = IndexType(index_type.upper())
        except ValueError:
            raise TSETMCValidationError(f"Invalid index_type '{index_type}'. Valid options are: {[e.value for e in IndexType]}")

        if not ignore_date:
            self._validate_date_range(start_date, end_date)

        self.logger.info(f"Getting history for index '{index_enum.value}' from {start_date} to {end_date}")

        try:
            index_web_id = self._INDEX_WEB_IDS[index_enum]
            
            # Fetch adjusted close data (available from new API)
            adj_close_url = f"http://cdn.tsetmc.com/api/Index/GetIndexB2History/{index_web_id}"
            adj_close_response = self._make_request(adj_close_url)
            df_adj_close = pd.DataFrame(adj_close_response.json()['indexB2'])
            df_adj_close = df_adj_close[['dEven', 'xNivInuClMresIbs']]
            df_adj_close.columns = ["Date", "Adj Close"]
            df_adj_close['Date'] = df_adj_close['Date'].astype(str).apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:]}')
            df_adj_close['Date'] = pd.to_datetime(df_adj_close['Date'])
            df_adj_close['J-Date'] = df_adj_close['Date'].apply(lambda d: str(jdatetime.date.fromgregorian(date=d)))
            
            if just_adj_close:
                result_df = df_adj_close[['J-Date', 'Date', 'Adj Close']]
            else:
                # Fetch other OHLCV data from old API
                ohlc_url = f"http://old.tsetmc.com/tsev2/chart/data/IndexFinancial.aspx?i={index_web_id}&t=ph"
                ohlc_response = self._make_request(ohlc_url)
                
                ohlc_data = [row.split(',') for row in ohlc_response.text.split(';')]
                df_ohlc = pd.DataFrame(ohlc_data, columns=['Date', 'High', 'Low', 'Open', 'Close', 'Volume', 'D'])
                df_ohlc = df_ohlc.dropna().drop(columns=['D'])
                df_ohlc['Date'] = pd.to_datetime(df_ohlc['Date'])
                
                # Merge dataframes
                result_df = pd.merge(df_ohlc, df_adj_close, on='Date', how='inner')
                numeric_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                result_df[numeric_cols] = result_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            result_df = result_df.sort_values('Date').set_index('J-Date')

            if not ignore_date:
                result_df = result_df.loc[start_date:end_date]

            if result_df.empty:
                raise TSETMCDataError(f"No data available for index '{index_enum.value}' in the specified period.")

            # Formatting
            if 'Date' in result_df.columns:
                result_df['Weekday'] = result_df['Date'].dt.day_name()
            if not show_weekday:
                result_df = result_df.drop(columns=['Weekday'], errors='ignore')
            if not double_date:
                result_df = result_df.drop(columns=['Date'], errors='ignore')

            return self._clean_dataframe(result_df)

        except Exception as e:
            if isinstance(e, TSETMCError):
                raise
            self.logger.error(f"Failed to get history for index '{index_enum.value}': {str(e)}")
            raise TSETMCAPIError(f"Could not retrieve data for index '{index_enum.value}'.")
            
    def get_market_watch(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get the current market watch data, including price, RI, and order book data.

        Returns:
            A tuple of two DataFrames:
            1. Market Watch DataFrame: Contains comprehensive data for all stocks.
            2. Order Book DataFrame: Contains the full order book for all stocks.
        """
        self.logger.info("Getting market watch data.")
        try:
            # Main market watch data URL
            mw_url = "http://old.tsetmc.com/tsev2/data/MarketWatchPlus.aspx"
            mw_response = self._make_request(mw_url)
            main_text = mw_response.text

            # Parse main data
            parts = main_text.split('@')
            price_data_raw = parts[2]
            ob_data_raw = parts[3]

            # Get RI data
            ri_url = "http://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx"
            ri_response = self._make_request(ri_url)
            ri_data_raw = ri_response.text

            # Process price data
            df_price = self._parse_mw_price_data(price_data_raw)
            
            # Process RI data
            df_ri = self._parse_mw_ri_data(ri_data_raw)
            
            # Process Order Book data
            df_ob_full = self._parse_mw_ob_data(ob_data_raw)
            df_ob1 = df_ob_full[df_ob_full['OB-Depth'] == 1].set_index('WEB-ID').drop(columns=['OB-Depth'])

            # Join dataframes
            df_market = df_price.join(df_ri).join(df_ob1)

            # Calculate additional fields
            df_market = self._calculate_mw_fields(df_market)
            
            # Get Sector names
            df_market = self._map_sector_names(df_market)

            # Final formatting
            df_market = self._format_market_watch(df_market)
            df_ob_final = self._format_order_book(df_ob_full, df_price)
            
            self.logger.info(f"Successfully retrieved market watch data for {len(df_market)} stocks.")
            return self._clean_dataframe(df_market), self._clean_dataframe(df_ob_final)

        except Exception as e:
            if isinstance(e, TSETMCError):
                raise
            self.logger.error(f"Failed to get market watch data: {str(e)}")
            raise TSETMCAPIError("Could not retrieve market watch data.")

    def _parse_mw_price_data(self, price_data_raw: str) -> pd.DataFrame:
        price_cols = ['WEB-ID', 'Ticker-Code', 'Ticker', 'Name', 'Time', 'Open', 'Final', 'Close', 'No', 'Volume', 'Value',
                      'Low', 'High', 'Y-Final', 'EPS', 'Base-Vol', 'Unknown1', 'Unknown2', 'Sector-Code', 'Day_UL', 'Day_LL', 'Share-No', 'Mkt-ID']
        data = [row.split(',') for row in price_data_raw.split(';')]
        df = pd.DataFrame(data)
        df = df.iloc[:, :len(price_cols)]
        df.columns = price_cols
        
        numeric_cols = ['Open', 'Final', 'Close', 'No', 'Volume', 'Value', 'Low', 'High', 'Y-Final', 'EPS', 'Base-Vol', 'Day_UL', 'Day_LL', 'Share-No']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df['WEB-ID'] = df['WEB-ID'].str.strip()
        df = df.set_index('WEB-ID')
        df['Name'] = df['Name'].apply(clean_persian_text)
        df['Ticker'] = df['Ticker'].apply(clean_persian_text)
        return df

    def _parse_mw_ri_data(self, ri_data_raw: str) -> pd.DataFrame:
        ri_cols = ['WEB-ID', 'No_Buy_R', 'No_Buy_I', 'Vol_Buy_R', 'Vol_Buy_I', 'No_Sell_R', 'No_Sell_I', 'Vol_Sell_R', 'Vol_Sell_I']
        data = [row.split(',') for row in ri_data_raw.split(';')]
        df = pd.DataFrame(data, columns=ri_cols).dropna()
        numeric_cols = ri_cols[1:]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df['WEB-ID'] = df['WEB-ID'].str.strip()
        df = df.set_index('WEB-ID')
        return df

    def _parse_mw_ob_data(self, ob_data_raw: str) -> pd.DataFrame:
        ob_cols = ['WEB-ID', 'OB-Depth', 'Sell-No', 'Buy-No', 'Buy-Price', 'Sell-Price', 'Buy-Vol', 'Sell-Vol']
        data = [row.split(',') for row in ob_data_raw.split(';')]
        df = pd.DataFrame(data, columns=ob_cols).dropna()
        numeric_cols = ob_cols[1:]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df['WEB-ID'] = df['WEB-ID'].str.strip()
        return df
        
    def _calculate_mw_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        df['Close(%)'] = ((df['Close'] - df['Y-Final']) / df['Y-Final'] * 100).round(2)
        df['Final(%)'] = ((df['Final'] - df['Y-Final']) / df['Y-Final'] * 100).round(2)
        df['Market Cap'] = df['Share-No'] * df['Final']
        
        df['BQ-Value'] = df.apply(lambda r: r['Buy-Vol'] * r['Buy-Price'] if r['Buy-Price'] == r['Day_UL'] else 0, axis=1)
        df['SQ-Value'] = df.apply(lambda r: r['Sell-Vol'] * r['Sell-Price'] if r['Sell-Price'] == r['Day_LL'] else 0, axis=1)
        
        df['BQPC'] = (df['BQ-Value'] / df['Buy-No']).fillna(0).round(0).astype(int)
        df['SQPC'] = (df['SQ-Value'] / df['Sell-No']).fillna(0).round(0).astype(int)
        return df

    def _map_sector_names(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            static_data_url = "https://cdn.tsetmc.com/api/StaticData/GetStaticData"
            response = self._make_request(static_data_url)
            sec_df = pd.DataFrame(response.json()['staticData'])
            sec_df['code'] = sec_df['code'].astype(str).str.zfill(2)
            sec_df = sec_df[sec_df['type'] == 'IndustrialGroup'][['code', 'name']]
            sec_df['name'] = sec_df['name'].apply(clean_persian_text)
            sector_map = dict(sec_df.values)
            df['Sector'] = df['Sector-Code'].map(sector_map)
        except Exception as e:
            self.logger.warning(f"Could not map sector names: {e}")
            df['Sector'] = df['Sector-Code'] # fallback
        return df

    def _format_market_watch(self, df: pd.DataFrame) -> pd.DataFrame:
        mkt_map = {'300':'بورس','303':'فرابورس','305':'صندوق قابل معامله','309':'پایه','400':'حق تقدم بورس','403':'حق تقدم فرابورس','404':'حق تقدم پایه'}
        df['Market'] = df['Mkt-ID'].map(mkt_map)
        
        final_cols = ['Ticker', 'Name', 'Time', 'Open', 'High', 'Low', 'Close', 'Final', 'Close(%)', 'Final(%)',
                      'Value', 'Volume', 'No', 'Day_UL', 'Day_LL', 'BQ-Value', 'SQ-Value', 'BQPC', 'SQPC',
                      'Vol_Buy_R', 'Vol_Buy_I', 'Vol_Sell_R', 'Vol_Sell_I', 'No_Buy_R', 'No_Buy_I', 'No_Sell_R', 'No_Sell_I',
                      'Market', 'Sector', 'Market Cap', 'EPS', 'Base-Vol', 'Share-No']
        
        df['Time'] = df['Time'].astype(str).str.pad(6, 'left', '0').apply(lambda x: f"{x[:2]}:{x[2:4]}:{x[4:]}")
        
        return df.reset_index().set_index('Ticker')[final_cols]

    def _format_order_book(self, df_ob: pd.DataFrame, df_price: pd.DataFrame) -> pd.DataFrame:
        df = df_ob.join(df_price[['Ticker', 'Day_LL', 'Day_UL']], on='WEB-ID')
        df = df.sort_values(['Ticker', 'OB-Depth'])
        return df.set_index(['Ticker', 'OB-Depth']) 