import pytest
import requests
import asyncio
from unittest.mock import MagicMock, patch
import time

from pytsetmc_api.services.base_service import BaseService
from pytsetmc_api.exceptions import TSETMCNetworkError, TSETMCAPIError, TSETMCRateLimitError, TSETMCValidationError

# A concrete implementation of BaseService for testing
class ConcreteService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@pytest.fixture
def service():
    """Fixture to create a ConcreteService instance."""
    return ConcreteService(base_url="http://test.com")

def test_base_service_initialization(service):
    """Test if BaseService initializes correctly."""
    assert service.base_url == "http://test.com"
    assert service.timeout == 30
    assert service.max_retries == 3
    assert service.logger is not None

def test_get_session(service):
    """Test that a requests.Session is created and reused."""
    session1 = service._get_session()
    session2 = service._get_session()
    assert isinstance(session1, requests.Session)
    assert session1 is session2

@patch('time.sleep')
@patch('time.time')
def test_rate_limit(mock_time, mock_sleep, service):
    """Test the rate limiting logic."""
    service._min_request_interval = 0.5
    
    # First call, no sleep
    mock_time.return_value = 1000.0
    service._rate_limit()
    mock_sleep.assert_not_called()
    assert service._last_request_time == 1000.0

    # Second call, too soon
    mock_time.return_value = 1000.2
    service._rate_limit()
    mock_sleep.assert_called_once()
    assert mock_sleep.call_args[0][0] == pytest.approx(0.3)
    assert service._last_request_time == 1000.2
    
    # Third call, after interval
    mock_sleep.reset_mock()
    mock_time.return_value = 1001.0
    service._rate_limit()
    mock_sleep.assert_not_called()
    assert service._last_request_time == 1001.0

@patch('requests.Session.request')
def test_make_request_success(mock_request, service):
    """Test a successful synchronous request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_request.return_value = mock_response
    
    response = service._make_request("http://test.com/api")
    
    mock_request.assert_called_once()
    assert response == mock_response

@patch('requests.Session.request', side_effect=requests.exceptions.Timeout)
def test_make_request_timeout(mock_request, service):
    """Test a synchronous request that times out."""
    with pytest.raises(TSETMCNetworkError, match="Request timeout"):
        service._make_request("http://test.com/api")

@patch('requests.Session.request')
def test_make_request_http_error(mock_request, service):
    """Test a synchronous request with an HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.ok = False
    mock_response.reason = "Server Error"
    mock_request.return_value = mock_response

    with pytest.raises(TSETMCAPIError, match="HTTP 500: Server Error"):
        service._make_request("http://test.com/api")

@patch('requests.Session.request')
def test_make_request_rate_limit_error(mock_request, service):
    """Test a synchronous request with a rate limit error."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_request.return_value = mock_response

    with pytest.raises(TSETMCRateLimitError, match="Rate limit exceeded"):
        service._make_request("http://test.com/api")

@pytest.mark.asyncio
async def test_make_async_request_success(service, mocker):
    """Test a successful asynchronous request."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    
    # The response from session.request is an async context manager
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_session.request.return_value = AsyncContextManager()
    
    response = await service._make_async_request(mock_session, "http://test.com/api")
    
    assert response == mock_response
    mock_session.request.assert_called_once()

def test_validate_date_range(service):
    """Test date range validation."""
    # Valid (start date should be before end date)
    service._validate_date_range("1403-01-01", "1404-01-01")
    
    # Valid (with slash separator - should be normalized)
    service._validate_date_range("1403/01/01", "1403-01-01")
    
    # Invalid format (really invalid)
    with pytest.raises(TSETMCValidationError, match="Invalid start date format"):
        service._validate_date_range("invalid-date", "1403-01-01")
    
    # Start after end
    with pytest.raises(TSETMCValidationError, match="Start date must be before end date"):
        service._validate_date_range("1402-01-01", "1403-01-01")

def test_validate_stock_name(service):
    """Test stock name validation."""
    # Valid
    service._validate_stock_name("خودرو")
    
    # Invalid (empty)
    with pytest.raises(TSETMCValidationError, match="Stock name cannot be empty"):
        service._validate_stock_name("  ")
        
    # Invalid (None)
    with pytest.raises(TSETMCValidationError, match="Stock name must be a non-empty string"):
        service._validate_stock_name(None)

def test_build_url(service):
    """Test URL building."""
    assert service._build_url("/api/test") == "http://test.com/api/test"
    assert service._build_url("api/test") == "http://test.com/api/test"


if __name__ == "__main__": 
    pytest.main() 