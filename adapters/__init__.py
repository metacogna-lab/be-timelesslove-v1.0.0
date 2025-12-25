"""
Adapter layer for interfacing between frontend and backend.

This module provides a clean, validated interface that transforms requests
and responses between the React frontend and FastAPI backend, ensuring
data consistency, security, and proper error handling.
"""

from adapters.config import AdapterConfig, get_adapter_config
from adapters.client import AdapterClient

__all__ = [
    "AdapterConfig",
    "get_adapter_config",
    "AdapterClient",
]

__version__ = "1.0.0"

