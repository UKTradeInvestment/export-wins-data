"""
This module contains types that are used in the config package.
"""

from enum import auto, Enum


class HawkScope(Enum):
    """Scopes used for Hawk views."""
    activity_stream = auto()
    data_flow_api = auto()
    data_hub = auto()
