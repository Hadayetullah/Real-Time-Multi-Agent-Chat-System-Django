"""
Core App Configuration
Defines the configuration for the core Django app
Contains shared utilities and management commands
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration class for the Core app
    This app provides shared utilities and management commands
    """
    
    # Default auto field type for model primary keys
    default_auto_field = 'django.db.models.BigAutoField'
    
    # App name (must match directory structure: apps.core)
    name = 'apps.core'
    
    # Human-readable app name (shown in Django admin)
    verbose_name = 'Core Utilities'
    
    def ready(self):
        """
        Runs when Django starts
        Use this for app initialization tasks like:
        - Registering signals
        - Performing startup checks
        - Loading configuration
        """
        # Currently no startup tasks needed
        pass