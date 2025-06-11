"""
Utility functions for the TSETMC API package.

This module provides various utility functions for date validation,
text processing, and other common operations used throughout the package.
"""

import re
import logging
from datetime import date, datetime
from typing import Optional, Dict, Any, Union

import jdatetime
from persiantools import characters
from rich.console import Console
from rich.logging import RichHandler

from .exceptions import TSETMCValidationError


# Setup rich console for better output formatting
console = Console()


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    show_time: bool = True,
    show_path: bool = False,
) -> logging.Logger:
    """Set up logging with rich formatting.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom format string for log messages.
        show_time: Whether to show timestamp in log messages.
        show_path: Whether to show file path in log messages.
        
    Returns:
        Configured logger instance.
        
    Example:
        >>> logger = setup_logging(level="DEBUG", show_time=True)
        >>> logger.info("Application started")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        markup=True,
    )
    
    # Set format if provided
    if format_string:
        rich_handler.setFormatter(logging.Formatter(format_string))
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
        force=True,
    )
    
    return logging.getLogger(__name__)


def validate_jalali_date(date_string: str, field_name: str = "date") -> str:
    """Validate and normalize a Jalali (Persian) date string.
    
    Args:
        date_string: Date string in YYYY-MM-DD format.
        field_name: Name of the field being validated (for error messages).
        
    Returns:
        Normalized date string in YYYY-MM-DD format.
        
    Raises:
        TSETMCValidationError: If the date format is invalid.
        
    Example:
        >>> validate_jalali_date("1404-01-01")
        '1404-01-01'
        >>> validate_jalali_date("1403/1/1")
        '1404-01-01'
    """
    if not date_string or not isinstance(date_string, str):
        raise TSETMCValidationError(
            f"Invalid {field_name}: date string cannot be empty",
            field_name=field_name,
            field_value=date_string,
        )
    
    # Clean the date string
    date_string = date_string.strip()
    
    # Replace common separators with hyphens
    date_string = re.sub(r'[/.]', '-', date_string)
    
    # Split the date parts
    parts = date_string.split('-')
    
    if len(parts) != 3:
        raise TSETMCValidationError(
            f"Invalid {field_name}: expected format YYYY-MM-DD, got {date_string}",
            field_name=field_name,
            field_value=date_string,
        )
    
    try:
        year, month, day = map(int, parts)
        
        # Validate year range (reasonable range for stock market data)
        if year < 1300 or year > 1450:  # Jalali years roughly 1921-2071
            raise TSETMCValidationError(
                f"Invalid {field_name}: year {year} is out of reasonable range",
                field_name=field_name,
                field_value=date_string,
            )
        
        # Create jdatetime object to validate the date
        jalali_date = jdatetime.date(year=year, month=month, day=day)
        
        # Return normalized format
        return f'{jalali_date.year:04d}-{jalali_date.month:02d}-{jalali_date.day:02d}'
        
    except ValueError as e:
        raise TSETMCValidationError(
            f"Invalid {field_name}: {str(e)}",
            field_name=field_name,
            field_value=date_string,
        ) from e


def convert_jalali_to_gregorian(jalali_date_string: str) -> date:
    """Convert a Jalali date string to a Gregorian date object.
    
    Args:
        jalali_date_string: Jalali date string in YYYY-MM-DD format.
        
    Returns:
        Gregorian date object.
        
    Raises:
        TSETMCValidationError: If the date format is invalid.
        
    Example:
        >>> convert_jalali_to_gregorian("1404-01-01")
        datetime.date(2021, 3, 21)
    """
    # Validate the Jalali date first
    normalized_date = validate_jalali_date(jalali_date_string)
    
    # Parse the normalized date
    year, month, day = map(int, normalized_date.split('-'))
    
    try:
        # Create Jalali date object
        jalali_date = jdatetime.date(year=year, month=month, day=day)
        
        # Convert to Gregorian
        gregorian_date = jalali_date.togregorian()
        
        return gregorian_date
        
    except Exception as e:
        raise TSETMCValidationError(
            f"Failed to convert Jalali date to Gregorian: {str(e)}",
            field_name="jalali_date",
            field_value=jalali_date_string,
        ) from e


def convert_gregorian_to_jalali(gregorian_date: Union[date, datetime]) -> str:
    """Convert a Gregorian date to a Jalali date string.
    
    Args:
        gregorian_date: Gregorian date or datetime object.
        
    Returns:
        Jalali date string in YYYY-MM-DD format.
        
    Example:
        >>> from datetime import date
        >>> convert_gregorian_to_jalali(date(2021, 3, 21))
        '1404-01-01'
    """
    if isinstance(gregorian_date, datetime):
        gregorian_date = gregorian_date.date()
    
    # Convert to Jalali
    jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
    
    return f'{jalali_date.year:04d}-{jalali_date.month:02d}-{jalali_date.day:02d}'


def clean_persian_text(text: str) -> str:
    """Clean and normalize Persian text.
    
    This function normalizes Persian characters, removes extra whitespace,
    and applies other common text cleaning operations.
    
    Args:
        text: The text to clean.
        
    Returns:
        Cleaned and normalized text.
        
    Example:
        >>> clean_persian_text("  پتروشیمی\u200c پارس  ")
        'پتروشیمی پارس'
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convert Arabic characters to Persian
    text = characters.ar_to_fa(text)
    
    # Remove zero-width non-joiner characters and replace with space
    text = text.replace('\u200c', ' ')
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    return text


def normalize_stock_symbol(symbol: str) -> str:
    """Normalize a stock symbol for consistent matching.
    
    Args:
        symbol: The stock symbol to normalize.
        
    Returns:
        Normalized symbol.
        
    Example:
        >>> normalize_stock_symbol("  پترول\u200c ")
        'پترول'
    """
    if not symbol or not isinstance(symbol, str):
        raise TSETMCValidationError(
            "Stock symbol cannot be empty",
            field_name="symbol",
            field_value=symbol,
        )
    
    # Clean the text
    normalized = clean_persian_text(symbol)
    
    # Remove all spaces for symbol matching
    normalized = ''.join(normalized.split())
    
    if not normalized:
        raise TSETMCValidationError(
            "Stock symbol cannot be empty after normalization",
            field_name="symbol",
            field_value=symbol,
        )
    
    return normalized


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """Validate a date range and ensure start_date <= end_date.
    
    Args:
        start_date: Start date string in Jalali format.
        end_date: End date string in Jalali format.
        
    Returns:
        Tuple of normalized (start_date, end_date) strings.
        
    Raises:
        TSETMCValidationError: If dates are invalid or start > end.
        
    Example:
        >>> validate_date_range("1404-01-01", "1404-12-29")
        ('1404-01-01', '1404-12-29')
    """
    # Validate both dates
    start_normalized = validate_jalali_date(start_date, "start_date")
    end_normalized = validate_jalali_date(end_date, "end_date")
    
    # Convert to date objects for comparison
    start_date_obj = convert_jalali_to_gregorian(start_normalized)
    end_date_obj = convert_jalali_to_gregorian(end_normalized)
    
    if start_date_obj > end_date_obj:
        raise TSETMCValidationError(
            f"Start date ({start_normalized}) must be before or equal to end date ({end_normalized})",
            details={
                "start_date": start_normalized,
                "end_date": end_normalized,
            }
        )
    
    return start_normalized, end_normalized


def format_number(number: Union[int, float], locale: str = "fa") -> str:
    """Format a number according to Persian locale conventions.
    
    Args:
        number: The number to format.
        locale: Locale for formatting ("fa" for Persian, "en" for English).
        
    Returns:
        Formatted number string.
        
    Example:
        >>> format_number(1234567.89, "fa")
        '۱,۲۳۴,۵۶۷.۸۹'
    """
    if number is None:
        return ""
    
    # Format with commas
    formatted = f"{number:,.2f}" if isinstance(number, float) else f"{number:,}"
    
    if locale == "fa":
        # Convert to Persian digits
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"
        
        for i, digit in enumerate(english_digits):
            formatted = formatted.replace(digit, persian_digits[i])
    
    return formatted


def create_http_headers(user_agent: Optional[str] = None) -> Dict[str, str]:
    """Create HTTP headers for API requests.
    
    Args:
        user_agent: Custom user agent string.
        
    Returns:
        Dictionary of HTTP headers.
    """
    default_user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    
    return {
        "User-Agent": user_agent or default_user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fa,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def safe_float_conversion(value: Any) -> Optional[float]:
    """Safely convert a value to float, returning None for invalid values.
    
    Args:
        value: The value to convert.
        
    Returns:
        Float value or None if conversion fails.
        
    Example:
        >>> safe_float_conversion("123.45")
        123.45
        >>> safe_float_conversion("invalid")
        None
    """
    if value is None or value == "" or value == "N/A":
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int_conversion(value: Any) -> Optional[int]:
    """Safely convert a value to int, returning None for invalid values.
    
    Args:
        value: The value to convert.
        
    Returns:
        Integer value or None if conversion fails.
        
    Example:
        >>> safe_int_conversion("123")
        123
        >>> safe_int_conversion("123.45")
        123
        >>> safe_int_conversion("invalid")
        None
    """
    if value is None or value == "" or value == "N/A":
        return None
    
    try:
        # First convert to float to handle strings like "123.0"
        float_value = float(value)
        return int(float_value)
    except (ValueError, TypeError):
        return None


def chunk_list(data: list, chunk_size: int) -> list[list]:
    """Split a list into chunks of specified size.
    
    Args:
        data: The list to chunk.
        chunk_size: Maximum size of each chunk.
        
    Returns:
        List of chunks.
        
    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying function calls on failure.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff_factor: Factor to multiply delay by after each retry.
        exceptions: Tuple of exception types to catch and retry on.
        
    Returns:
        Decorator function.
        
    Example:
        >>> @retry_on_failure(max_retries=3, delay=1.0)
        ... def unstable_function():
        ...     # Function that might fail
        ...     pass
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    
    return decorator


if __name__ == "__main__": 
    # Example usage and testing
    logger = setup_logging(level="INFO")
    
    # Test date validation
    try:
        validated_date = validate_jalali_date("1404-01-01")
        logger.info(f"Validated date: {validated_date}")
        
        # Test date conversion
        gregorian = convert_jalali_to_gregorian("1404-01-01")
        logger.info(f"Gregorian conversion: {gregorian}")
        
        # Test text cleaning
        cleaned = clean_persian_text("  پتروشیمی\u200c پارس  ")
        logger.info(f"Cleaned text: '{cleaned}'")
        
        # Test number formatting
        formatted = format_number(1234567.89, "fa")
        logger.info(f"Formatted number: {formatted}")
        
    except TSETMCValidationError as e:
        logger.error(f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}") 