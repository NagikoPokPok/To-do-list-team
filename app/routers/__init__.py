"""
Routers package - Export available routers
"""

try:
    from . import tasks, teams, notifications
    __all__ = ["tasks", "teams", "notifications"]
except ImportError:
    __all__ = []