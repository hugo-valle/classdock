# Makefile for ClassDock Python Wrapper

.PHONY: help install test test-quick test-full test-unit test-integration clean lint format check-all dev

# Default target
help:
	@echo "ClassDock Python Wrapper - Development Commands"
	@echo "===================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  help            Show this help message"
	@echo "  install         Install package in development mode"
	@echo "  test            Run quick tests"
	@echo "  test-unit       Run unit tests with pytest"
	@echo "  test-full       Run comprehensive test suite"
	@echo "  test-integration Run integration tests"
	@echo "  test-local      Run local development test script (pytest-based)"
	@echo "  clean           Clean up build artifacts"
	@echo "  lint            Run linting checks"
	@echo "  format          Format code with black"
	@echo "  check-all       Run all checks (lint, format, test)"
	@echo "  dev             Set up development environment"
	@echo ""

# Install package in development mode
install:
	@echo "🔧 Installing package in development mode..."
	pip install -e .

# Basic functionality test (quick test)
.PHONY: test
test:
	@echo "🧪 Running quick functionality tests..."
	@echo "Testing CLI import..."
	@python -c "from classdock.cli import app; print('✅ CLI import successful')"
	@echo "Testing BashWrapper import..."
	@python -c "from classdock.bash_wrapper import BashWrapper; print('✅ BashWrapper import successful')"
	@echo "Testing Configuration import..."
	@python -c "from classdock.config import ConfigLoader; print('✅ ConfigLoader import successful')"
	@echo "🎉 All basic tests passed!"

# Unit tests with pytest
test-unit:
	@echo "🧪 Running unit tests with pytest..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		echo "⚠️  pytest not installed. Installing..."; \
		pip install pytest; \
		pytest tests/ -v; \
	fi

# Comprehensive test suite
test-full:
	@echo "🧪 Running comprehensive test suite..."
	python tests/test_comprehensive.py

# Integration tests - test actual CLI commands
test-integration:
	@echo "🧪 Running integration tests..."
	@make test-all-commands

# Run local test script
test-local:
	@echo "🧪 Running local test script..."
	./test_local.sh

# Clean up build artifacts
clean:
	@echo "🧹 Cleaning up build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf classdock/__pycache__/
	rm -rf classdock/**/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf tests/**/__pycache__/
	rm -rf .pytest_cache/
	rm -f test_report.json
	@echo "✅ Cleanup complete!"

# Linting (if tools are available)
lint:
	@echo "🔍 Running linting checks..."
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "Running flake8..."; \
		flake8 classdock/ tests/; \
	else \
		echo "⚠️  flake8 not installed, skipping"; \
	fi
	@if command -v pylint >/dev/null 2>&1; then \
		echo "Running pylint..."; \
		pylint classdock/; \
	else \
		echo "⚠️  pylint not installed, skipping"; \
	fi

# Code formatting
format:
	@echo "🎨 Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		echo "Running black..."; \
		black classdock/ tests/; \
		echo "✅ Code formatted!"; \
	else \
		echo "⚠️  black not installed, skipping formatting"; \
		echo "Install with: pip install black"; \
	fi

# Check all - comprehensive checks
check-all: lint test-unit test-integration
	@echo "✅ All checks completed!"

# Development environment setup
dev:
	@echo "🚀 Setting up development environment..."
	pip install -e .
	@if [ -f requirements-dev.txt ]; then \
		echo "Installing development dependencies..."; \
		pip install -r requirements-dev.txt; \
	fi
	@echo "Installing pytest for testing..."; \
	pip install pytest pytest-cov
	@echo "✅ Development environment ready!"

# Test specific commands
test-sync:
	@echo "🔄 Testing sync command..."
	python -m classdock --dry-run --verbose sync

test-discover:
	@echo "🔍 Testing discover command..."
	python -m classdock --dry-run --verbose discover

test-cycle:
	@echo "🔄 Testing cycle command..."
	python -m classdock --dry-run cycle --list test-assignment

test-all-commands:
	@echo "🧪 Testing all commands..."
	@make test-sync
	@make test-discover
	@make test-cycle
	python -m classdock --dry-run --verbose run
	python -m classdock --dry-run --verbose secrets
	python -m classdock --dry-run --verbose assist
	@echo "✅ All command tests completed!"

# Installation test
test-install:
	@echo "📦 Testing package installation..."
	pip uninstall -y classdock || true
	pip install .
	classdock --help
	classdock version
	@echo "✅ Installation test passed!"

# Package building
build:
	@echo "📦 Building package..."
	python -m build
	@echo "✅ Package built successfully!"

# Show package info
info:
	@echo "📋 Package Information"
	@echo "===================="
	@python -c "import classdock; print(f'Version: {classdock.__version__}')"
	@python -c "import classdock; print(f'Author: {classdock.__author__}')"
	@python -c "import classdock; print(f'Description: {classdock.__description__}')"
