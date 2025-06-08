import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from pytsetmc_api.client import TSETMCClient
from pytsetmc_api.services.stock_service import StockService
from pytsetmc_api.services.price_service import PriceService
from pytsetmc_api.services.market_service import MarketService
from pytsetmc_api.services.trading_service import TradingService
from pytsetmc_api.services.data_service import DataService


@pytest.fixture
def mock_services(mocker):
    """Fixture to mock all services."""
    mocker.patch('tsetmc.client.StockService', return_value=MagicMock(spec=StockService))
    mocker.patch('tsetmc.client.PriceService', return_value=MagicMock(spec=PriceService))
    mocker.patch('tsetmc.client.MarketService', return_value=MagicMock(spec=MarketService))
    mocker.patch('tsetmc.client.TradingService', return_value=MagicMock(spec=TradingService))
    mocker.patch('tsetmc.client.DataService', return_value=MagicMock(spec=DataService))
    mocker.patch('tsetmc.client.setup_logging')


@pytest.fixture
def client(mock_services):
    """Fixture to create a TSETMCClient with mocked services."""
    return TSETMCClient()


def test_tsetmc_client_initialization(client):
    """Test if TSETMCClient initializes correctly."""
    assert client is not None
    assert client.base_url == "http://www.tsetmc.com"
    assert client.timeout == 30
    assert client.max_retries == 3
    
    # Check if services are initialized
    assert isinstance(client.stock, MagicMock)
    assert isinstance(client.price, MagicMock)
    assert isinstance(client.market, MagicMock)
    assert isinstance(client.trading, MagicMock)
    assert isinstance(client.data, MagicMock)


def test_search_stock(client):
    """Test search_stock method."""
    query = 'پترول'
    expected_df = pd.DataFrame({'result': [1]})
    client.stock.search.return_value = expected_df
    
    result_df = client.search_stock(query)
    
    client.stock.search.assert_called_once_with(query)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_get_price_history(client):
    """Test get_price_history method."""
    args = {
        'stock': 'خودرو',
        'start_date': '1404-01-01',
        'end_date': '1403-01-01',
        'ignore_date': False,
        'adjust_price': False,
        'show_weekday': False,
        'double_date': False
    }
    expected_df = pd.DataFrame({'price': [100]})
    client.price.get_history.return_value = expected_df
    
    result_df = client.get_price_history(**args)
    
    client.price.get_history.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_get_market_index(client):
    """Test get_market_index method."""
    args = {
        'index_type': 'CWI',
        'start_date': '1404-01-01',
        'end_date': '1403-01-01',
        'ignore_date': False,
        'just_adj_close': False,
        'show_weekday': False,
        'double_date': False
    }
    expected_df = pd.DataFrame({'index': [1000]})
    client.market.get_index_history.return_value = expected_df
    
    result_df = client.get_market_index(**args)
    
    client.market.get_index_history.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_get_intraday_trades(client):
    """Test get_intraday_trades method."""
    args = {
        'stock': 'وخارزم',
        'start_date': '1404-09-15',
        'end_date': '1404-12-29',
        'jalali_date': True,
        'combined_datetime': False,
        'show_progress': True
    }
    expected_df = pd.DataFrame({'trades': [50]})
    client.trading.get_intraday_trades.return_value = expected_df
    
    result_df = client.get_intraday_trades(**args)
    
    client.trading.get_intraday_trades.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_get_market_watch(client):
    """Test get_market_watch method."""
    args = {'save_excel': True, 'save_path': 'D:/FinPy-TSE Data/MarketWatch'}
    expected_df = pd.DataFrame({'market': ['data']})
    client.market.get_market_watch.return_value = expected_df

    result_df = client.get_market_watch(**args)

    client.market.get_market_watch.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_build_stock_list(client):
    """Test build_stock_list method."""
    args = {
        'bourse': True,
        'farabourse': True,
        'payeh': True,
        'detailed_list': True,
        'show_progress': True,
        'save_excel': True,
        'save_csv': True,
        'save_path': 'D:/FinPy-TSE Data/'
    }
    expected_df = pd.DataFrame({'stocks': ['list']})
    client.data.build_stock_list.return_value = expected_df

    result_df = client.build_stock_list(**args)

    client.data.build_stock_list.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_get_bulk_price_data(client):
    """Test get_bulk_price_data method."""
    args = {
        'stock_list': ['خودرو', 'پترول', 'فولاد'],
        'param': 'Adj Final',
        'jalali_date': True,
        'save_excel': True,
        'save_path': 'D:/FinPy-TSE Data/Price Panel/'
    }
    expected_df = pd.DataFrame({'bulk': ['prices']})
    client.data.build_price_panel.return_value = expected_df

    result_df = client.get_bulk_price_data(**args)

    client.data.build_price_panel.assert_called_once_with(**args)
    pd.testing.assert_frame_equal(result_df, expected_df)

def test_client_repr(client):
    """Test the __repr__ method of the client."""
    expected_repr = "TSETMCClient(base_url='http://www.tsetmc.com', timeout=30)"
    assert repr(client) == expected_repr

def test_client_context_manager():
    """Test the client can be used as a context manager."""
    with TSETMCClient() as client:
        assert isinstance(client, TSETMCClient)

if __name__ == "__main__":
    pytest.main() 