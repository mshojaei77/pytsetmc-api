import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from pytsetmc_api.services.data_service import DataService
from pytsetmc_api.services.price_service import PriceService
from pytsetmc_api.services.stock_service import StockService
from pytsetmc_api.exceptions import TSETMCDataError

@pytest.fixture
def mock_price_service():
    """Fixture for a mocked PriceService."""
    mock = MagicMock(spec=PriceService)
    # Sample history for stock 'A'
    history_a = pd.DataFrame({'Adj Close': [100, 101]}, index=['1404-01-01', '1404-01-02'])
    history_a.columns.name = 'A'
    # Sample history for stock 'B'
    history_b = pd.DataFrame({'Adj Close': [200, 202]}, index=['1404-01-01', '1404-01-02'])
    history_b.columns.name = 'B'
    
    mock.get_history.side_effect = lambda stock, **kwargs: {
        'A': history_a,
        'B': history_b
    }.get(stock, pd.DataFrame())
    return mock

@pytest.fixture
def data_service(mock_price_service):
    """Fixture to create a DataService instance with mocked dependencies."""
    with patch('logging.getLogger'), \
         patch('tsetmc.services.data_service.StockService'), \
         patch('tsetmc.services.data_service.PriceService', return_value=mock_price_service):
        service = DataService(base_url="http://test.com")
        service.price_service = mock_price_service
        return service

def test_build_stock_list_simple(data_service):
    """Test build_stock_list without fetching detailed info."""
    mock_bourse_stocks = [{'Ticker': 'A', 'Name': 'Stock A', 'WEB-ID': '1', 'Market': 'Bourse'}]
    
    with patch.object(data_service, '_get_market_stocks', return_value=mock_bourse_stocks) as mock_get_market, \
         patch.object(data_service, '_get_payeh_stocks', return_value=[]):
        
        df = data_service.build_stock_list(markets=['bourse'], detailed_list=False)
        
        mock_get_market.assert_called_once()
        assert not df.empty
        assert df.index.name == 'Ticker'
        assert df.loc['A']['Market'] == 'Bourse'

@patch('unsync.Unfuture.result')
def test_build_stock_list_detailed(mock_unsync_result, data_service):
    """Test build_stock_list with detailed_list=True."""
    mock_stocks = [{'Ticker': 'A', 'Name': 'Stock A', 'WEB-ID': '1', 'Market': 'Bourse'}]
    mock_details = [{'WEB-ID': '1', 'Sector': 'Test Sector'}]
    
    # Mock the result of the parallel fetching
    mock_unsync_result.return_value = mock_details
    
    with patch.object(data_service, '_get_market_stocks', return_value=mock_stocks), \
         patch.object(data_service, '_get_payeh_stocks', return_value=[]):
        
        df = data_service.build_stock_list(detailed_list=True)

    assert not df.empty
    assert 'Sector' in df.columns
    assert df.loc['A']['Sector'] == 'Test Sector'

def test_build_price_panel_success(data_service, mock_price_service):
    """Test a successful build_price_panel call."""
    stock_list = ['A', 'B']
    df_panel = data_service.build_price_panel(stock_list, param='Adj Close')
    
    assert isinstance(df_panel, pd.DataFrame)
    assert list(df_panel.columns) == stock_list
    assert df_panel.loc['1404-01-01']['B'] == 200

def test_build_price_panel_no_data(data_service, mock_price_service):
    """Test build_price_panel when no data can be fetched."""
    # Configure mock to return empty dfs
    mock_price_service.get_history.return_value = pd.DataFrame()
    
    with pytest.raises(TSETMCDataError):
        data_service.build_price_panel(['C', 'D'])

def test_get_market_stocks(data_service):
    """Test the parsing of market stocks from HTML."""
    html_content = """
    <table class="table1">
        <tr><td><a href="...&i=123">TickerA</a></td></tr>
        <tr><td><a href="...&i=456" title="Stock B">TickerB</a></td></tr>
    </table>
    """
    mock_response = MagicMock()
    mock_response.text = html_content
    
    with patch.object(data_service, '_make_request', return_value=mock_response):
        stocks = data_service._get_market_stocks("some_id", "some_market")
        
    assert len(stocks) == 2
    assert stocks[0]['Ticker'] == 'TickerA'
    assert stocks[1]['Name'] == 'Stock B'
    assert stocks[1]['WEB-ID'] == '456'

if __name__ == "__main__": 
    pytest.main() 