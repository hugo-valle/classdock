# Real Repository Testing Configuration

This directory contains the configuration files needed for testing classdock with actual GitHub repositories.

## Files

### `real_repo_info.conf`

Contains the complete configuration for a real GitHub assignment, including:

- **TEMPLATE_REPO_URL**: The template repository URL
- **GITHUB_ORGANIZATION**: The GitHub organization name
- **ASSIGNMENT_NAME**: The assignment name
- **ASSIGNMENT_FILE**: The main assignment file (e.g., calculator.py)
- **SECRETS_CONFIG**: Configuration for managing repository secrets

### `instructor_token.txt`

Contains a valid GitHub personal access token with appropriate permissions for:

- Reading repository information
- Managing repository secrets
- Cloning repositories
- Accessing organization resources

**Security Note**: This file contains sensitive information and should not be committed to version control in a real project.

## Setup Instructions

### 1. Configure Repository Information

Edit `real_repo_info.conf` to match your actual GitHub assignment:

```bash
# Example configuration
TEMPLATE_REPO_URL="https://github.com/YOUR_ORG/your-template-repo"
GITHUB_ORGANIZATION="YOUR_ORG"
ASSIGNMENT_NAME="your-assignment-name"
ASSIGNMENT_FILE="main.py"
```

### 2. Set Up GitHub Token

1. Create a GitHub Personal Access Token with these permissions:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `admin:repo_hook` (Admin access to repository hooks)

2. Save the token in `instructor_token.txt`:
   ```bash
   echo "ghp_YOUR_TOKEN_HERE" > instructor_token.txt
   ```

### 3. Verify Configuration

Test that your configuration is valid:

```bash
# Test configuration parsing
./scripts/test_real_repo.sh --dry-run

# Test with verbose output
./scripts/test_real_repo.sh --dry-run --verbose
```

## Usage

### Full Real Repository Testing

```bash
# Complete test cycle with real repository
./scripts/run_full_test.sh --real-repo

# Test with cleanup
./scripts/test_runner.sh real-repo --cleanup
```

### Step-by-Step Testing

```bash
# Setup test environment only
./scripts/test_real_repo.sh --setup-only

# Run tests with existing environment
./scripts/test_real_repo.sh --test-only

# Clean up everything
./scripts/test_real_repo.sh --cleanup-only
```

### Development and Debugging

```bash
# Keep environment and repository for inspection
./scripts/test_real_repo.sh --keep-env --keep-repo --verbose

# Skip repository cloning (use existing)
./scripts/test_real_repo.sh --skip-clone
```

## What the Test Does

1. **Environment Setup**: Creates a clean conda environment with classdock
2. **Repository Cloning**: Clones the actual template repository
3. **Configuration Generation**: Creates assignment.conf from real_repo_info.conf
4. **Validation Testing**: Tests configuration validation
5. **Assignment Setup**: Tests assignment setup in dry-run mode
6. **CLI Testing**: Validates all CLI commands work correctly
7. **Python API Testing**: Tests Python API with real configuration
8. **Cleanup**: Removes test environment and cloned repository

## Security Considerations

- **Token Security**: Never commit the instructor_token.txt file to version control
- **Dry-Run Mode**: Most operations run in dry-run mode to avoid modifying actual repositories
- **Isolation**: Tests use isolated conda environments to avoid affecting your main setup
- **Cleanup**: Automatic cleanup removes sensitive data from test environments

## Troubleshooting

### Common Issues

1. **Invalid Token**: Verify the GitHub token has correct permissions
2. **Repository Access**: Ensure the token has access to the specified repositories
3. **Conda Environment**: Verify conda is installed and available in PATH
4. **Network Connectivity**: Ensure internet access for GitHub API calls

### Getting Help

Run with verbose mode to see detailed execution:

```bash
./scripts/test_real_repo.sh --verbose --dry-run
```

Check the troubleshooting guide in `docs/TROUBLESHOOTING.md` for common issues and solutions.