"""
Data service for handling bulk data operations and parallel fetching.
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from unsync import unsync

from .base_service import BaseService
from .stock_service import StockService
from .price_service import PriceService
from ..exceptions import TSETMCError, TSETMCAPIError, TSETMCDataError
from ..utils import clean_persian_text


class DataService(BaseService):
    """
    Service for bulk data operations.

    This service provides functionality to:
    - Build a comprehensive list of all stocks
    - Build a price panel for a list of stocks
    - Fetch data for the last 60 trading days
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stock_service = StockService(**kwargs)
        self.price_service = PriceService(**kwargs)

    def build_stock_list(
        self,
        markets: List[str] = ['bourse', 'farabourse', 'payeh'],
        detailed_list: bool = True,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Build a comprehensive list of stocks from specified markets.

        Args:
            markets: A list of markets to include ('bourse', 'farabourse', 'payeh').
            detailed_list: If True, fetches detailed information for each stock.
            show_progress: If True, displays a progress bar.

        Returns:
            DataFrame containing the list of stocks.
        """
        self.logger.info(f"Building stock list for markets: {markets}. Detailed: {detailed_list}")
        
        all_stocks = []
        
        if 'bourse' in markets:
            if show_progress: print("Gathering Bourse market stock list...")
            all_stocks.extend(self._get_market_stocks("32097828799138957", "بورس"))
        
        if 'farabourse' in markets:
            if show_progress: print("Gathering Fara-Bourse market stock list...")
            all_stocks.extend(self._get_market_stocks("43685683301327984", "فرابورس"))
        
        if 'payeh' in markets:
            if show_progress: print("Gathering Payeh market stock list...")
            all_stocks.extend(self._get_payeh_stocks())
            
        df_stocks = pd.DataFrame(all_stocks)
        df_stocks = df_stocks.drop_duplicates(subset=['Ticker']).set_index('Ticker')

        if detailed_list:
            if show_progress: print("Gathering detailed data...")
            df_stocks = self._get_detailed_stock_info(df_stocks, show_progress)

        self.logger.info(f"Successfully built stock list with {len(df_stocks)} stocks.")
        return self._clean_dataframe(df_stocks)

    def build_price_panel(
        self,
        stock_list: List[str],
        param: str = 'Adj Close',
        jalali_date: bool = True,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Build a panel of historical price data for a list of stocks.

        Args:
            stock_list: List of stock names or symbols.
            param: The price parameter to include in the panel (e.g., 'Close', 'Adj Close').
            jalali_date: If True, the index will be Jalali dates.
            show_progress: If True, displays a progress bar.

        Returns:
            DataFrame with stock prices as columns and dates as the index.
        """
        self.logger.info(f"Building price panel for {len(stock_list)} stocks with param '{param}'.")
        
        all_prices = []
        
        # Directly use tqdm if show_progress is True
        iterator = stock_list
        if show_progress:
            from tqdm import tqdm
            iterator = tqdm(stock_list, desc="Building Price Panel")

        for stock in iterator:
            try:
                hist = self.price_service.get_history(stock, ignore_date=True, adjust_price=True)
                if not hist.empty and param in hist.columns:
                    stock_prices = hist[[param]].rename(columns={param: stock})
                    all_prices.append(stock_prices)
            except Exception as e:
                self.logger.warning(f"Could not fetch price history for {stock}: {e}")
        
        if not all_prices:
            raise TSETMCDataError("Could not fetch any price data for the given stock list.")
            
        df_panel = pd.concat(all_prices, axis=1)
        
        if not jalali_date:
            df_panel.index = df_panel.index.map(lambda d: jdatetime.datetime.strptime(d, '%Y-%m-%d').togregorian().strftime('%Y-%m-%d'))
            
        return self._clean_dataframe(df_panel)

    def _get_market_stocks(self, market_id: str, market_name: str) -> List[Dict]:
        """Helper to get stocks for Bourse and FaraBourse."""
        url = f"http://old.tsetmc.com/Loader.aspx?ParTree=15131J&i={market_id}"
        response = self._make_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"class": "table1"})
        
        stocks = []
        for a in table.find_all('a'):
            stocks.append({
                'Ticker': clean_persian_text(a.text),
                'Name': clean_persian_text(a.get('title', '')),
                'WEB-ID': a['href'].split('&i=')[1],
                'Market': market_name
            })
        return stocks

    def _get_payeh_stocks(self) -> List[Dict]:
        """Helper to get stocks for Payeh market."""
        url = "https://www.ifb.ir/StockQoute.aspx"
        # This might require special headers or handling if it's a POST request with form data
        response = self._make_request(url, method='POST', headers={"__EVENTTARGET": "exportbtn"})
        df = pd.read_html(response.text)[0]
        df = df.iloc[2:, :3]
        df.columns = ['Ticker', 'Name', 'Market']
        df = df[df['Market'].isin(['تابلو پایه زرد', 'تابلو پایه نارنجی', 'تابلو پایه قرمز'])]
        df['Market'] = df['Market'].str.replace('تابلو ', '')
        df['Ticker'] = df['Ticker'].apply(clean_persian_text)
        df['Name'] = df['Name'].apply(clean_persian_text)
        df = df[~df['Ticker'].str.endswith('ح')]
        df['WEB-ID'] = '' # Needs to be fetched separately
        return df.to_dict('records')
        
    def _get_detailed_stock_info(self, df_stocks: pd.DataFrame, show_progress: bool) -> pd.DataFrame:
        """Fetch detailed information for a dataframe of stocks."""
        
        # Fill missing WEB-IDs for Payeh stocks
        for ticker, row in df_stocks[df_stocks['WEB-ID'] == ''].iterrows():
            try:
                df_stocks.loc[ticker, 'WEB-ID'] = self.stock_service.get_web_id(ticker)
            except Exception as e:
                self.logger.warning(f"Could not find WEB-ID for Payeh stock {ticker}: {e}")

        df_stocks = df_stocks[df_stocks['WEB-ID'] != '']

        @unsync
        async def get_details_parallel(web_ids):
            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                tasks = [self._fetch_detail(session, web_id) for web_id in web_ids]
                if show_progress:
                    from tqdm.asyncio import tqdm
                    details = await tqdm.gather(*tasks, desc="Fetching Detailed Info")
                else:
                    details = await asyncio.gather(*tasks)
            return [d for d in details if d is not None]

        details = get_details_parallel(df_stocks['WEB-ID'].tolist()).result()
        
        df_details = pd.DataFrame(details).set_index('WEB-ID')
        df_stocks = df_stocks.join(df_details, on='WEB-ID')

        return df_stocks

    async def _fetch_detail(self, session: aiohttp.ClientSession, web_id: str) -> Optional[Dict]:
        """Async helper to fetch detailed info for one stock."""
        url = f'http://old.tsetmc.com/Loader.aspx?Partree=15131M&i={web_id}'
        try:
            async with session.get(url) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                table = soup.find("table", {"class": "table1"})
                df_id = pd.read_html(str(table))[0].T
                df_id.columns = df_id.iloc[0]
                df_id = df_id.iloc[1]
                return {
                    'WEB-ID': web_id,
                    'Panel': clean_persian_text(df_id.get('تابلو اعلانات', '')),
                    'Sector': clean_persian_text(df_id.get('گروه صنعت', '')),
                    'Sub-Sector': clean_persian_text(df_id.get('زیر گروه صنعت', '')),
                    'Name(EN)': df_id.get('نام لاتین', ''),
                    'Company Code(12)': df_id.get('کد شرکت', '')
                }
        except Exception as e:
            self.logger.warning(f"Failed to fetch details for WEB-ID {web_id}: {e}")
            return None 