#!/usr/bin/env python3
"""
Main entry point for running classdock as a module.

This allows the package to be executed with:
    python -m classdock [command] [options]
"""

from .cli import app

if __name__ == "__main__":
    app()
