"""
Custom exceptions for the TSETMC API package.

This module defines custom exception classes for different types of errors
that can occur when interacting with the Tehran Stock Exchange Market Center API.
"""

from typing import Any, Dict, Optional


class TSETMCError(Exception):
    """Base exception class for all TSETMC-related errors.
    
    This is the base class for all exceptions raised by the TSETMC package.
    All other exceptions inherit from this class.
    
    Attributes:
        message: A human-readable description of the error.
        details: Optional dictionary containing additional error information.
    """

    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the TSETMCError.
        
        Args:
            message: A human-readable description of the error.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.details:
            return f"{self.message}. Details: {self.details}"
        return self.message


class TSETMCAPIError(TSETMCError):
    """Exception raised when the TSETMC API returns an error.
    
    This exception is raised when the API returns an error response,
    such as a 404, 500, or other HTTP error codes.
    
    Attributes:
        status_code: The HTTP status code returned by the API.
        response_data: The raw response data from the API.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCAPIError.
        
        Args:
            message: A human-readable description of the error.
            status_code: The HTTP status code returned by the API.
            response_data: The raw response data from the API.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.status_code:
            error_msg += f" (Status: {self.status_code})"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg


class TSETMCValidationError(TSETMCError):
    """Exception raised when input validation fails.
    
    This exception is raised when the provided input parameters
    do not meet the required validation criteria.
    
    Attributes:
        field_name: The name of the field that failed validation.
        field_value: The value that failed validation.
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCValidationError.
        
        Args:
            message: A human-readable description of the error.
            field_name: The name of the field that failed validation.
            field_value: The value that failed validation.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.field_name:
            error_msg += f" (Field: {self.field_name}"
            if self.field_value is not None:
                error_msg += f", Value: {self.field_value}"
            error_msg += ")"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg


class TSETMCNetworkError(TSETMCError):
    """Exception raised when network communication fails.
    
    This exception is raised when there are network-related issues
    such as connection timeouts, DNS resolution failures, etc.
    
    Attributes:
        original_exception: The original exception that caused the network error.
    """

    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCNetworkError.
        
        Args:
            message: A human-readable description of the error.
            original_exception: The original exception that caused the network error.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.original_exception = original_exception

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.original_exception:
            error_msg += f" (Original: {self.original_exception})"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg


class TSETMCNotFoundError(TSETMCError):
    """Exception raised when a requested resource is not found.
    
    This exception is raised when a requested stock, sector, or other
    financial instrument cannot be found in the TSETMC system.
    
    Attributes:
        resource_type: The type of resource that was not found.
        resource_identifier: The identifier used to search for the resource.
    """

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_identifier: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCNotFoundError.
        
        Args:
            message: A human-readable description of the error.
            resource_type: The type of resource that was not found.
            resource_identifier: The identifier used to search for the resource.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_identifier = resource_identifier

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.resource_type and self.resource_identifier:
            error_msg += f" ({self.resource_type}: {self.resource_identifier})"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg


class TSETMCDataError(TSETMCError):
    """Exception raised when data processing or parsing fails.
    
    This exception is raised when there are issues with processing
    or parsing the data received from the TSETMC API.
    
    Attributes:
        data_type: The type of data that failed to process.
        raw_data: The raw data that failed to process.
    """

    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        raw_data: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCDataError.
        
        Args:
            message: A human-readable description of the error.
            data_type: The type of data that failed to process.
            raw_data: The raw data that failed to process.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.data_type = data_type
        self.raw_data = raw_data

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.data_type:
            error_msg += f" (Data Type: {self.data_type})"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg


class TSETMCRateLimitError(TSETMCError):
    """Exception raised when API rate limits are exceeded.
    
    This exception is raised when the client has exceeded the
    rate limits imposed by the TSETMC API.
    
    Attributes:
        retry_after: The number of seconds to wait before retrying.
        limit_type: The type of rate limit that was exceeded.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the TSETMCRateLimitError.
        
        Args:
            message: A human-readable description of the error.
            retry_after: The number of seconds to wait before retrying.
            limit_type: The type of rate limit that was exceeded.
            details: Optional dictionary containing additional error information.
        """
        super().__init__(message, details)
        self.retry_after = retry_after
        self.limit_type = limit_type

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_msg = self.message
        if self.retry_after:
            error_msg += f" (Retry after: {self.retry_after}s)"
        if self.limit_type:
            error_msg += f" (Limit type: {self.limit_type})"
        if self.details:
            error_msg += f". Details: {self.details}"
        return error_msg 