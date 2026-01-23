"""
Automation and scheduling package.

This package handles:
- Cron job management and scheduling
- Automated workflow execution
- Batch processing operations
- Background task coordination
"""

from .scheduler import AutomationScheduler
from .cron_manager import CronManager

__all__ = ["AutomationScheduler", "CronManager"]
