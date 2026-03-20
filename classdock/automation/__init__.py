"""
Automation and scheduling package.

This package handles:
- Cron job management and scheduling
- Automated workflow execution
- Batch processing operations
- Background task coordination
"""

from .cron_manager import CronManager
from .scheduler import AutomationScheduler

__all__ = ["AutomationScheduler", "CronManager"]
