"""
Trading system configuration module.

This module loads and validates environment variables for the trading system.
It provides a singleton pattern to access configuration settings throughout
the application.
"""

import os
from typing import Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required variables."""
    pass


class Settings:
    """
    Configuration settings for the trading system.
    
    Attributes:
        api_key: API key for trading platform authentication
        api_secret: API secret for trading platform authentication
        base_url: Base URL for the trading platform API
    """
    
    def __init__(self) -> None:
        """Initialize settings by loading environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Load and validate required environment variables
        self.api_key: str = self._get_required_env("API_KEY")
        self.api_secret: str = self._get_required_env("API_SECRET")
        self.base_url: str = self._get_required_env("BASE_URL")
    
    def _get_required_env(self, var_name: str) -> str:
        """
        Get a required environment variable.
        
        Args:
            var_name: Name of the environment variable
            
        Returns:
            Value of the environment variable
            
        Raises:
            ConfigurationError: If the environment variable is not set or is empty
        """
        value = os.getenv(var_name)
        if not value or not value.strip():
            raise ConfigurationError(
                f"Required environment variable '{var_name}' is not set or is empty. "
                f"Please ensure it is defined in your .env file."
            )
        return value.strip()
    
    def __repr__(self) -> str:
        """Return a string representation with masked sensitive data."""
        return (
            f"Settings(api_key='***', api_secret='***', "
            f"base_url='{self.base_url}')"
        )


# Singleton instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the singleton Settings instance.
    
    This function implements the singleton pattern to ensure only one
    Settings instance exists throughout the application lifecycle.
    
    Returns:
        The singleton Settings instance
        
    Raises:
        ConfigurationError: If required environment variables are not set
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.base_url)
        https://api.example.com
    """
    global _settings_instance
    
    if _settings_instance is None:
        _settings_instance = Settings()
    
    return _settings_instance


def reset_settings() -> None:
    """
    Reset the singleton Settings instance.
    
    This function is primarily useful for testing purposes to allow
    reloading configuration with different environment variables.
    """
    global _settings_instance
    _settings_instance = None
