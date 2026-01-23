#!/bin/bash
# Assignment Update Script
# Run this script to get the latest template updates from GitHub Classroom

echo "🔄 Updating assignment from template..."
echo "📚 GitHub Classroom Environment Detected"
echo ""

# Source shared config utility
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/config.sh"

# Get template repo and organization from config
TEMPLATE_REPO="$(get_config_value TEMPLATE_REPO_URL)"
GITHUB_ORGANIZATION="$(get_config_value GITHUB_ORGANIZATION)"

# Check if template repository is private and needs authentication
echo "📖 IMPORTANT: This template repository is PRIVATE"
echo "   You need a GitHub Personal Access Token to access updates."
echo "   📋 See docs/UPDATE-GUIDE.md for detailed instructions"
echo "   🔗 Quick link: https://github.com/settings/tokens"
echo ""
echo "⚠️  If you don't have a token yet:"
echo "   1. Press Ctrl+C to exit this script"
echo "   2. Follow the docs/UPDATE-GUIDE.md guide"
echo "   3. Come back and run this script again"
echo ""

# Check if upstream remote exists
if ! git remote | grep -q "upstream"; then
    echo "Adding template repository as upstream..."
    
    # Try without authentication first
    if ! git remote add upstream $TEMPLATE_REPO 2>/dev/null; then
        echo "🔒 Template repository requires authentication."
        echo ""
        echo "Please enter your GitHub credentials:"
        read -p "📧 GitHub username: " USERNAME
        
        # Validate username
        if [ -z "$USERNAME" ]; then
            echo "❌ Username cannot be empty"
            exit 1
        fi
        
        echo "🔑 Personal access token (will be hidden as you type):"
        read -s -p "   Token: " TOKEN
        echo ""
        
        # Validate token format
        if [[ ! "$TOKEN" =~ ^ghp_ ]]; then
            echo "⚠️  Warning: Token should start with 'ghp_'"
            echo "   Make sure you copied the entire token"
        fi
        
        if [ -z "$TOKEN" ]; then
            echo "❌ Token cannot be empty"
            exit 1
        fi
        
        # Use authenticated URL - get repository name from template URL
        if [[ -z "$TEMPLATE_REPO" ]]; then
            echo "❌ TEMPLATE_REPO_URL not found in configuration"
            exit 1
        fi
        
        # Extract the repo path from the template URL and create authenticated URL
        REPO_PATH=$(echo "$TEMPLATE_REPO" | sed 's|https://github.com/||' | sed 's|\.git$||')
        AUTH_REPO="https://${USERNAME}:${TOKEN}@github.com/${REPO_PATH}.git"
        
        echo "🔐 Adding authenticated remote..."
        if ! git remote add upstream "$AUTH_REPO"; then
            echo "❌ Failed to add remote with authentication"
            echo "   Please check your username and token"
            exit 1
        fi
        
        echo "✅ Authenticated remote added successfully"
    fi
else
    echo "Updating upstream remote URL..."
    git remote set-url upstream $TEMPLATE_REPO
fi

# Fetch latest changes
echo "Fetching latest template changes..."
if ! git fetch upstream; then
    echo "❌ Failed to fetch from template repository."
    echo "Please check:"
    echo "1. Template repository exists at: $TEMPLATE_REPO"
    echo "2. You have access to the repository"
    echo "3. Your internet connection is working"
    exit 1
fi

# Check if there are any changes
if git rev-parse upstream/main >/dev/null 2>&1; then
    # Show what will be updated
    echo "📋 Template changes available:"
    git log --oneline HEAD..upstream/main
    
    # Check if there are actually changes
    if [ -z "$(git log --oneline HEAD..upstream/main)" ]; then
        echo "✅ Your repository is already up to date!"
        exit 0
    fi
else
    echo "❌ Could not find upstream/main branch"
    exit 1
fi

# Ask for confirmation
read -p "Do you want to apply these updates? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying updates..."
    
    # Create a backup branch before merging
    echo "🔄 Creating backup branch..."
    git branch "backup-$(date +%Y%m%d-%H%M%S)" 2>/dev/null
    
    # Try to merge automatically
    if git merge upstream/main --no-edit; then
        echo "✅ Updates applied successfully!"
        echo "💡 Tip: Test your assignment to make sure everything still works"
        echo "📝 Your previous state is saved in a backup branch"
    else
        echo "⚠️  Merge conflicts detected. Please resolve them manually:"
        echo "1. Edit conflicted files (look for <<<<<<< ======= >>>>>>> markers)"
        echo "2. Run: git add <resolved-files>"
        echo "3. Run: git commit"
        echo "4. Run: git push"
        echo ""
        echo "🆘 Need help? See docs/UPDATE-GUIDE.md or ask your instructor"
    fi
else
    echo "❌ Update cancelled"
fi

echo "Done!"
