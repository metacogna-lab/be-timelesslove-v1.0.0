"""
API endpoint adapters.
"""

from adapters.api.auth import auth_adapter
from adapters.api.memories import memories_adapter
from adapters.api.feed import feed_adapter
from adapters.api.storage import storage_adapter
from adapters.api.invites import invites_adapter

__all__ = [
    "auth_adapter",
    "memories_adapter",
    "feed_adapter",
    "storage_adapter",
    "invites_adapter",
]

