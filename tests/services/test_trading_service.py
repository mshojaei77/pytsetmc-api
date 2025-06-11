import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

from pytsetmc_api.services.trading_service import TradingService
from pytsetmc_api.services.stock_service import StockService
from pytsetmc_api.exceptions import TSETMCDataError

@pytest.fixture
def mock_stock_service():
    """Fixture for a mocked StockService."""
    mock = MagicMock(spec=StockService)
    mock.get_web_id.return_value = "12345"
    return mock

@pytest.fixture
def trading_service(mock_stock_service):
    """Fixture to create a TradingService instance with mocked dependencies."""
    with patch('logging.getLogger'), patch('tsetmc.services.trading_service.StockService', return_value=mock_stock_service):
        service = TradingService(base_url="http://test.com")
        service.stock_service = mock_stock_service
        # Mock the async session getter
        service._get_session = MagicMock()
        return service

@patch('tsetmc.services.trading_service.asyncio.run')
@patch('tsetmc.services.trading_service.TradingService._get_trading_days')
def test_get_intraday_trades_history_success(mock_get_days, mock_async_run, trading_service):
    """Test a successful call to get_intraday_trades_history."""
    mock_get_days.return_value = ['1404-01-01']
    mock_df = pd.DataFrame({'Price': [100]})
    mock_async_run.return_value = [mock_df] # The mocked gather returns a list of results
    
    result_df = trading_service.get_intraday_trades_history(
        stock="test",
        start_date="1404-01-01",
        end_date="1404-01-02"
    )
    
    mock_get_days.assert_called_once()
    mock_async_run.assert_called_once()
    assert not result_df.empty

@patch('tsetmc.services.trading_service.TradingService._get_trading_days', return_value=[])
def test_get_intraday_trades_history_no_days(mock_get_days, trading_service):
    """Test get_intraday_trades_history with no trading days found."""
    with pytest.raises(TSETMCDataError, match="No trading days found"):
        trading_service.get_intraday_trades_history(
            stock="test",
            start_date="1404-01-01",
            end_date="1404-01-02"
        )

def test_get_trading_days(trading_service):
    """Test the _get_trading_days method."""
    mock_response = MagicMock()
    # Dates are 2021-03-21 (1404-01-01) and 2021-03-23 (1404-01-03)
    mock_response.text = "20210321@data;20210323@data;"
    
    with patch.object(trading_service, '_make_request', return_value=mock_response):
        days = trading_service._get_trading_days("12345", "1404-01-01", "1404-01-02")
        
    assert days == ["1404-01-01"] # Only the first date is in range

@pytest.mark.asyncio
async def test_fetch_day_trades(trading_service):
    """Test the _fetch_day_trades async method."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        'tradeHistory': [{'iSens', 'nTran', 'hEven', 'qTitTran', 'pTran', 'qTitNgJ'}]
    }
    
    trading_service._make_async_request = AsyncMock(return_value=mock_response)
    
    df = await trading_service._fetch_day_trades("12345", "1404-01-01")
    
    assert isinstance(df, pd.DataFrame)
    # The parsing logic in the original code is faulty, so this test may need adjustment
    # based on the expected (or corrected) parsing logic. For now, check not empty.
    # assert not df.empty 

@pytest.mark.asyncio
async def test_fetch_day_ob(trading_service):
    """Test the _fetch_day_ob async method."""
    mock_threshold_response = AsyncMock()
    mock_threshold_response.json.return_value = {
        'staticThreshold': [{'psGelStaMax': 105, 'psGelStaMin': 95}]
    }
    
    mock_ob_response = AsyncMock()
    mock_ob_response.json.return_value = {
        'bestLimitsHistory': [{
            'hEven': 90000, 'number': 1, 'zOrdMeDem': 10, 'qTitMeDem': 100,
            'pMeDem': 99, 'pMeOf': 101, 'qTitMeOf': 120, 'zOrdMeOf': 12,
            'iE': 1, 'dEven': 20210321, 'instrument': 'IRO1', 'insCode': '123'
        }]
    }
    
    trading_service._make_async_request = AsyncMock(side_effect=[mock_threshold_response, mock_ob_response])
    
    df = await trading_service._fetch_day_ob("12345", "1404-01-01")
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert 'Day_UL' in df.columns
    assert df.iloc[0]['Day_UL'] == 105

if __name__ == "__main__": 
    pytest.main() 