import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from pytsetmc_api.services.stock_service import StockService
from pytsetmc_api.exceptions import TSETMCNotFoundError, TSETMCValidationError
from pytsetmc_api.models import StockInfo, MarketType

@pytest.fixture
def stock_service():
    """Fixture to create a StockService instance with a mocked logger."""
    with patch('logging.getLogger') as mock_logger:
        service = StockService(base_url="http://test.com")
        service.logger = mock_logger
        return service

def test_search_success(stock_service):
    """Test a successful stock search."""
    mock_response = MagicMock()
    mock_response.text = "پترول,پترول,12345,بازار اول,شیمیایی,IR123"
    
    with patch.object(stock_service, '_make_request', return_value=mock_response) as mock_make_request:
        result_df = stock_service.search("پترول")
        
        mock_make_request.assert_called_once()
        assert not result_df.empty
        assert 'Name' in result_df.columns
        assert result_df.iloc[0]['Symbol'] == 'پترول'

def test_search_not_found(stock_service):
    """Test a stock search that returns no results."""
    mock_response = MagicMock()
    mock_response.text = ""
    
    with patch.object(stock_service, '_make_request', return_value=mock_response):
        with pytest.raises(TSETMCNotFoundError):
            stock_service.search("없는주식")

def test_search_invalid_query(stock_service):
    """Test a stock search with an invalid query."""
    with pytest.raises(TSETMCValidationError):
        stock_service.search(" ")

def test_get_stock_info_success(stock_service):
    """Test successfully getting stock info."""
    search_result = pd.DataFrame([{
        'Name': 'پترول جم',
        'Symbol': 'پترول',
        'WebID': '12345',
        'Market': 'بازار اول',
        'Sector': 'شیمیایی',
        'ISIN': 'IR123'
    }])
    
    with patch.object(stock_service, 'search', return_value=search_result) as mock_search:
        stock_info = stock_service.get_stock_info("پترول")
        
        mock_search.assert_called_once_with("پترول")
        assert isinstance(stock_info, StockInfo)
        assert stock_info.name == 'پترول جم'
        assert stock_info.web_id == '12345'

def test_get_stock_info_not_found(stock_service):
    """Test getting info for a stock that is not found."""
    with patch.object(stock_service, 'search', return_value=pd.DataFrame()):
        with pytest.raises(TSETMCNotFoundError):
            stock_service.get_stock_info("없는주식")

def test_get_web_id_success(stock_service):
    """Test successfully getting a stock's web ID."""
    mock_stock_info = StockInfo(
        name='پترول جم', ticker='پترول', web_id='12345',
        market=MarketType.BOURSE, isin='IR123'
    )
    
    with patch.object(stock_service, 'get_stock_info', return_value=mock_stock_info) as mock_get_info:
        web_id = stock_service.get_web_id("پترول")
        
        mock_get_info.assert_called_once_with("پترول")
        assert web_id == '12345'

def test_parse_search_response(stock_service):
    """Test the parsing of a search response."""
    response_text = "نام شرکت,نماد,وب‌آی‌دی,بازار;شرکت دوم,نماد۲,وب۲,بازار۲"
    df = stock_service._parse_search_response(response_text)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.iloc[1]['Symbol'] == 'نماد۲'

def test_parse_search_response_empty(stock_service):
    """Test parsing of an empty search response."""
    df = stock_service._parse_search_response("")
    assert isinstance(df, pd.DataFrame)
    assert df.empty

if __name__ == "__main__":
    pytest.main() 