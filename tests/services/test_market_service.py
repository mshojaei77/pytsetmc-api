import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from pytsetmc_api.services.market_service import MarketService, IndexType
from pytsetmc_api.exceptions import TSETMCValidationError, TSETMCDataError

@pytest.fixture
def market_service():
    """Fixture to create a MarketService instance."""
    with patch('logging.getLogger'):
        service = MarketService(base_url="http://test.com")
        return service

@patch('tsetmc.services.market_service.MarketService._make_request')
def test_get_index_history_success(mock_make_request, market_service):
    """Test a successful call to get_index_history."""
    # Mock response for new API (adj close)
    # Use dates that correspond to Jalali 1404-01-01 to 1404-01-03 (March 2025)
    mock_adj_close_response = MagicMock()
    mock_adj_close_json = {
        'indexB2': [
            {'dEven': 20250321, 'xNivInuClMresIbs': 1300000},
            {'dEven': 20250322, 'xNivInuClMresIbs': 1310000},
            {'dEven': 20250323, 'xNivInuClMresIbs': 1320000}
        ]
    }
    mock_adj_close_response.json.return_value = mock_adj_close_json
    
    # Mock response for old API (OHLC)
    mock_ohlc_response = MagicMock()
    mock_ohlc_response.text = "2025-03-21,1305000,1295000,1300000,1302000,1000,d;2025-03-22,1315000,1305000,1310000,1312000,1200,d;2025-03-23,1325000,1315000,1320000,1322000,1300,d"
    
    mock_make_request.side_effect = [mock_adj_close_response, mock_ohlc_response]
    
    df = market_service.get_index_history(
        index_type='CWI',
        start_date='1404-01-01',
        end_date='1404-01-03',
        double_date=True
    )
    
    assert mock_make_request.call_count == 2
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'Adj Close' in df.columns
    assert 'Date' in df.columns # from double_date=True

def test_get_index_history_invalid_type(market_service):
    """Test get_index_history with an invalid index type."""
    with pytest.raises(TSETMCValidationError):
        market_service.get_index_history(
            index_type='INVALID',
            start_date='1404-01-01',
            end_date='1404-01-02'
        )

@patch('tsetmc.services.market_service.MarketService._make_request')
def test_get_market_watch_success(mock_make_request, market_service):
    """Test a successful call to get_market_watch."""
    # Mock responses for the three requests in get_market_watch
    mock_mw_response = MagicMock()
    mock_mw_response.text = "Header@SomeSettings@1234,CODE,Ticker,Name,10:30,1,2,3,4,5,6,7,8,9,10,11,12,3,4@ob_data"
    
    mock_ri_response = MagicMock()
    mock_ri_response.text = "1234,1,2,3,4,5,6,7,8"
    
    mock_ob_response = MagicMock() # This is inside the main response now
    # The third part of the main response is the order book data
    price_data = "1234,CODE,Ticker,Name,10:30,100,102,101,10,1000,100000,99,103,98,1.0,20000,x,y,SCTOR,105,95,5000000,MKTID"
    ob_data = "1234,1,1,1,100,101,50,60"
    ri_data = "1234,10,5,100,50,8,4,90,40"
    
    mock_make_request.side_effect = [
        MagicMock(text=f"@@{price_data}@{ob_data}"),
        MagicMock(text=ri_data)
    ]
    
    # Mock sector mapping to avoid another request
    with patch.object(market_service, '_map_sector_names', side_effect=lambda df: df):
        df_market, df_ob = market_service.get_market_watch()

    assert mock_make_request.call_count == 2
    assert isinstance(df_market, pd.DataFrame)
    assert isinstance(df_ob, pd.DataFrame)
    assert not df_market.empty
    assert not df_ob.empty
    
    # Check for calculated columns
    assert 'Market Cap' in df_market.columns
    assert 'Final(%)' in df_market.columns
    assert 'Vol_Buy_I_Ratio' in df_market.columns
    
    # Check that OB data was parsed
    assert df_ob.iloc[0]['Buy-Price'] == 100

if __name__ == "__main__": 
    pytest.main() 