import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from pytsetmc_api.services.price_service import PriceService
from pytsetmc_api.services.stock_service import StockService
from pytsetmc_api.exceptions import TSETMCDataError, TSETMCValidationError
from pytsetmc_api.models import StockInfo, MarketType

@pytest.fixture
def mock_stock_service():
    """Fixture for a mocked StockService."""
    mock = MagicMock(spec=StockService)
    mock.get_web_id.return_value = "12345"
    mock.get_stock_info.return_value = StockInfo(
        name='Test Stock', ticker='TEST', web_id='12345',
        market=MarketType.BOURSE, isin='IRTest'
    )
    return mock

@pytest.fixture
def price_service(mock_stock_service):
    """Fixture to create a PriceService instance with mocked dependencies."""
    with patch('logging.getLogger'), patch('tsetmc.services.price_service.StockService', return_value=mock_stock_service):
        service = PriceService(base_url="http://test.com")
        service.stock_service = mock_stock_service
        return service

def test_get_history_success(price_service, mock_stock_service):
    """Test a successful call to get_history."""
    mock_df = pd.DataFrame({'Close': [1000, 1010]})
    
    with patch.object(price_service, '_fetch_price_data', return_value=mock_df) as mock_fetch:
        result_df = price_service.get_history(
            stock="test",
            start_date="1404-01-01",
            end_date="1404-01-02"
        )
        
        mock_stock_service.get_web_id.assert_called_once_with("test")
        mock_fetch.assert_called_once()
        assert not result_df.empty

def test_get_history_no_data(price_service):
    """Test get_history when no data is returned."""
    with patch.object(price_service, '_fetch_price_data', return_value=pd.DataFrame()):
        with pytest.raises(TSETMCDataError):
            price_service.get_history(
                stock="test",
                start_date="1404-01-01",
                end_date="1404-01-02"
            )

def test_get_history_invalid_date(price_service):
    """Test get_history with an invalid date range."""
    with pytest.raises(TSETMCValidationError):
        price_service.get_history(
            stock="test",
            start_date="1404-01-02",
            end_date="1404-01-01"
        )

def test_get_ri_history_success(price_service, mock_stock_service):
    """Test a successful call to get_ri_history."""
    mock_df = pd.DataFrame({'RI': [1, 1.01]})
    
    with patch.object(price_service, '_fetch_ri_data', return_value=mock_df) as mock_fetch:
        result_df = price_service.get_ri_history(
            stock="test",
            start_date="1404-01-01",
            end_date="1404-01-02"
        )
        
        mock_stock_service.get_web_id.assert_called_once_with("test")
        mock_fetch.assert_called_once()
        assert not result_df.empty

def test_get_usd_rial_history_success(price_service):
    """Test a successful call to get_usd_rial_history."""
    mock_df = pd.DataFrame({'Close': [250000, 251000]})
    
    with patch.object(price_service, '_fetch_price_data', return_value=mock_df) as mock_fetch:
        result_df = price_service.get_usd_rial_history(
            start_date="1404-01-01",
            end_date="1404-01-02"
        )
        
        mock_fetch.assert_called_once()
        # Check if the web_id for USD/RIAL was used in the call
        assert mock_fetch.call_args[1]['web_id'] == "46348559193224090"
        assert not result_df.empty

def test_format_price_data_with_options(price_service):
    """Test the _format_price_data method with all options enabled."""
    input_df = pd.DataFrame({
        'Date': ['1404-01-05', '1404-01-06'], # Thursday, Friday
        'Close': [100, 101]
    })
    
    # We need to patch the conversion utility function
    with patch('tsetmc.services.price_service.convert_jalali_to_gregorian') as mock_convert:
        mock_convert.side_effect = ['2021-03-25', '2021-03-26']
        
        formatted_df = price_service._format_price_data(
            input_df.copy(),
            show_weekday=True,
            double_date=True
        )
    
    assert 'Weekday' in formatted_df.columns
    assert 'Gregorian_Date' in formatted_df.columns
    assert formatted_df['Weekday'].iloc[0] == 'Thursday'


if __name__ == "__main__": 
    pytest.main() 