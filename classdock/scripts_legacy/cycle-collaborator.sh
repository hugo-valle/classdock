#!/usr/bin/env bash

GH=gh


if ! jq -n . > /dev/null 2>&1; then
    echo "jq does not seem to be installed, cannot continue" 1>&2
    exit 1
fi

if ! gh help > /dev/null 2>&1; then
    echo "gh does not seem to be installed, cannot continue" 1>&2
    exit 1
fi

if ! gh auth status > /dev/null 2>&1; then
    echo "gh does not seem to be authenticated, please run \`gh auth\` and try again"
    exit 1
fi

# Parse command line options
DRY_RUN=false
LIST_MODE=false
VERBOSE=false
BATCH_MODE=false
BATCH_FILE=""
CONFIG_MODE=false
CONFIG_FILE=""
REPO_URL_MODE=false
FORCE_CYCLE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --list|-l)
            LIST_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --force|-f)
            FORCE_CYCLE=true
            shift
            ;;
        --batch|-b)
            BATCH_MODE=true
            BATCH_FILE="$2"
            shift 2
            ;;
        --config|-c)
            CONFIG_MODE=true
            CONFIG_FILE="$2"
            shift 2
            ;;
        --repo-urls)
            REPO_URL_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [<assignment prefix> <ubitname|batch-file> <organization>]"
            echo "Options:"
            echo "  --dry-run, -n         Show what would be done without making changes"
            echo "  --list, -l            List repository status without making changes"
            echo "  --verbose, -v         Show detailed output"
            echo "  --force, -f           Force cycling even when access appears correct"
            echo "  --batch, -b <file>    Process multiple users from a file (one username per line)"
            echo "  --config, -c <file>   Read assignment configuration from file"
            echo "  --repo-urls           Treat batch file as repository URLs instead of usernames"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Configuration mode (recommended for assignment-orchestrator integration):"
            echo "  $0 --config assignment.conf --batch student-repos.txt --repo-urls"
            echo "  $0 --config assignment.conf --batch student-repos.txt --repo-urls --dry-run"
            echo ""
            echo "Traditional single user examples:"
            echo "  $0 homework1 student-username org-name"
            echo "  $0 --dry-run assignment2 student-github-user organization"
            echo "  $0 --list project1 github-username org-name"
            echo ""
            echo "Traditional batch mode examples:"
            echo "  $0 --batch students.txt homework1 organization"
            echo "  $0 --list --batch userlist.txt assignment2 org-name"
            echo "  $0 --dry-run --batch class-roster.txt project1 organization"
            echo ""
            echo "Batch file formats:"
            echo "  Username mode (one username per line):"
            echo "    student1-github"
            echo "    student2-username"
            echo "    student3-user"
            echo ""
            echo "  Repository URL mode (one URL per line, use with --repo-urls):"
            echo "    https://github.com/org/assignment-student1"
            echo "    https://github.com/org/assignment-student2"
            echo "  student3-user"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" 1>&2
            echo "Use --help for usage information" 1>&2
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Function to load configuration from assignment.conf
load_config() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        echo "error: Configuration file '$config_file' does not exist" 1>&2
        exit 1
    fi
    
    echo "Loading configuration from: $config_file"
    
    # Source the configuration file
    # shellcheck source=/dev/null
    source "$config_file"
    
    # Validate required configuration
    if [ -z "${GITHUB_ORGANIZATION:-}" ]; then
        echo "error: GITHUB_ORGANIZATION not set in configuration file" 1>&2
        exit 1
    fi
    
    if [ -z "${ASSIGNMENT_NAME:-}" ]; then
        echo "error: ASSIGNMENT_NAME not set in configuration file" 1>&2
        exit 1
    fi
    
    PREFIX="$ASSIGNMENT_NAME"
    ORG="$GITHUB_ORGANIZATION"
    
    echo "Loaded configuration:"
    echo "  Organization: $ORG"
    echo "  Assignment: $PREFIX"
}

# Function to extract usernames from repository URLs
extract_usernames_from_urls() {
    local batch_file="$1"
    local prefix="$2"
    local org="$3"
    
    echo "Extracting usernames from repository URLs..."
    
    local users=()
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Trim whitespace
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [[ -n "$line" ]]; then
                # Extract username from URL like https://github.com/org/assignment-username
                if [[ "$line" =~ ^https://github\.com/$org/$prefix-(.+)$ ]]; then
                    local username="${BASH_REMATCH[1]}"
                    users+=("$username")
                    if [ "$VERBOSE" = true ]; then
                        echo "  Extracted: $username from $line"
                    fi
                else
                    echo "warning: Cannot extract username from URL: $line" 1>&2
                fi
            fi
        fi
    done < "$batch_file"
    
    if [ ${#users[@]} -eq 0 ]; then
        echo "error: No valid repository URLs found in batch file" 1>&2
        exit 1
    fi
    
    echo "Extracted ${#users[@]} usernames from repository URLs"
    printf '%s\n' "${users[@]}"
}

# Validate arguments based on mode
if [ "$CONFIG_MODE" = true ]; then
    # Configuration mode - read from assignment.conf
    if [ $# -gt 0 ]; then
        echo "error: Extra arguments not allowed in config mode" 1>&2
        echo "Use --help for more information" 1>&2
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "error: Configuration file '$CONFIG_FILE' does not exist" 1>&2
        exit 1
    fi
    
    if [ "$BATCH_MODE" != true ]; then
        echo "error: Config mode requires --batch option" 1>&2
        exit 1
    fi
    
    load_config "$CONFIG_FILE"
    
elif [ "$BATCH_MODE" = true ]; then
    # Traditional batch mode
    if [ $# -ne 2 ]; then
        echo "usage: $0 [OPTIONS] --batch <batch-file> <assignment prefix> <organization>" 1>&2
        echo "Use --help for more information" 1>&2
        exit 1
    fi
    if [ ! -f "$BATCH_FILE" ]; then
        echo "error: Batch file '$BATCH_FILE' does not exist" 1>&2
        exit 1
    fi
    PREFIX="$1"
    ORG="$2"
    GHUSER=""  # Not used in batch mode
else
    # Traditional single user mode
    if [ $# -ne 3 ]; then
        echo "usage: $0 [OPTIONS] <assignment prefix> <ubitname> <organization>" 1>&2
        echo "Use --help for more information" 1>&2
        exit 1
    fi
    PREFIX="$1"
    GHUSER="$2"
    ORG="$3"
fi

check_repo_detailed() {
    local repo="$1"
    
    echo "Checking repository accessibility..."
    if $GH repo view "$repo" > /dev/null 2>&1; then
        echo "✓ Repository exists and is accessible"
        
        # Quick content check
        if $GH api "repos/$repo/contents" > /dev/null 2>&1; then
            echo "✓ Repository has content"
        else
            echo "⚠ Repository appears to be empty"
        fi
        
        return 0
    else
        echo "✗ Repository check failed"
        return 1
    fi
}

suggest_alternatives() {
    local org="$1"
    local prefix="$2"
    local user="$3"
    
    echo "Searching for similar repositories in organization '$org'..."
    
    # Try different variations of the repository name
    local variations=(
        "$org/$prefix$user"
        "$org/$user-$prefix"
        "$org/$prefix\_$user"
        "$org/$user\_$prefix"
        "$org/$user"
        "$org/${prefix,,}-$user"  # lowercase prefix
        "$org/$prefix-${user,,}"  # lowercase user
    )
    
    local found_repos=()
    for variation in "${variations[@]}"; do
        if $GH repo view "$variation" > /dev/null 2>&1; then
            found_repos+=("$variation")
        fi
    done
    
    if [ ${#found_repos[@]} -gt 0 ]; then
        echo "Found similar repositories:"
        for repo in "${found_repos[@]}"; do
            echo "  - https://github.com/$repo"
        done
    else
        # Search for repositories containing parts of the expected name
        echo "Searching for repositories with similar names..."
        local search_results=$($GH search repos --owner="$org" "$prefix" --limit 10 2>/dev/null | grep "^$org/" || true)
        if [ -n "$search_results" ]; then
            echo "Repositories in '$org' containing '$prefix':"
            echo "$search_results" | sed 's/^/  - https:\/\/github.com\//'
        else
            echo "No repositories found in '$org' containing '$prefix'"
        fi
    fi
}

# Function to process a single user
process_single_user() {
    local prefix="$1"
    local user="$2"
    local org="$3"
    local repo="$org/$prefix-$user"
    
    echo "=== Processing User: $user ==="
    echo "Repository: $repo"
    echo "Assignment: $prefix"
    echo "Organization: $org"
    echo
    
    # Check if repository exists
    if ! check_repo_detailed "$repo"; then
        echo
        suggest_alternatives "$org" "$prefix" "$user"
        echo "❌ SKIPPING: Repository $repo does not exist or is not accessible"
        echo
        return 1
    fi
    
    echo
    local repo_corrupted=false
    if ! check_permissions "$repo" "$user"; then
        repo_corrupted=true
    fi
    
    echo
    check_invitations "$repo" "$user"
    echo
    
    # Determine repository status
    if [ "$repo_corrupted" = true ]; then
        echo "🚨 REPOSITORY CORRUPTION DETECTED!"
        echo "   Student '$user' should be a collaborator but is not."
        echo "   This indicates the repository access is corrupted and needs to be fixed."
        echo
    else
        echo "✅ Repository access appears normal."
        echo "   Student '$user' is properly configured as a collaborator."
        echo
    fi
    
    # If in list mode, just show status
    if [ "$LIST_MODE" = true ]; then
        if [ "$repo_corrupted" = true ]; then
            echo "❌ Repository: $repo - CORRUPTED (student not a collaborator)"
        else
            echo "✅ Repository: $repo - OK (student is a collaborator)"
        fi
        echo
        return 0
    fi

    # Only cycle if there's actually a problem, unless force mode is enabled
    if [ "$repo_corrupted" = false ] && [ "$FORCE_CYCLE" = false ]; then
        echo "✅ Repository access is working correctly - no action needed."
        echo "   Student '$user' has proper collaborator access."
        echo
        echo "=== Summary ==="
        echo "Repository: $repo"
        echo "Student: $user"
        echo "Permission: write (verified)"
        echo "Status: ✅ No action required - Repository access is already correct"
        echo
        return 0
    fi

    # Explain why we're cycling
    if [ "$repo_corrupted" = true ]; then
        echo "🔄 Repository has access issues - cycling collaborator permissions..."
    elif [ "$FORCE_CYCLE" = true ]; then
        echo "🔄 Force mode enabled - cycling collaborator permissions anyway..."
    fi

    # Process the fix only if repository is corrupted or force mode is enabled
    echo "=== Fixing Repository Corruption ==="
    echo "Removing any existing access and re-inviting $user..."
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would fix corruption by removing $user from $repo"
        echo "[DRY RUN] Would check for invitation first..."
    else
        echo "Checking for invitation first..."
    fi
    
    # Get and process invitations
    local id=$(gh api -XGET "repos/$repo/invitations" | jq '.[] | select(.invitee.login == "'"$user"'").id' 2>/dev/null || echo "")
    
    if [ "x$id" != "x" ]; then
        echo "Found pending invitation (ID: $id)"
        if [ "$DRY_RUN" != true ]; then
            if gh api --silent -XDELETE "repos/$repo/invitations/$id"; then
                echo "✓ Invitation deleted successfully"
            else
                echo "✗ Failed to delete invitation" 1>&2
                echo "Try manually checking: https://github.com/$repo/settings/access" 1>&2
                return 1
            fi
        else
            echo "[DRY RUN] Would delete invitation"
        fi
    else
        echo "No pending invitation found"
        echo "Checking if user is already a collaborator..."
        
        if gh api "repos/$repo/collaborators/$user" > /dev/null 2>&1; then
            echo "User is currently a collaborator, removing..."
            if [ "$DRY_RUN" != true ]; then
                if gh api --silent -XDELETE "repos/$repo/collaborators/$user"; then
                    echo "✓ User removed successfully"
                else
                    echo "✗ Failed to remove $user from repository" 1>&2
                    echo "You may need to remove them manually from: https://github.com/$repo/settings/access" 1>&2
                    return 1
                fi
            else
                echo "[DRY RUN] Would remove user"
            fi
        else
            echo "User is not currently a collaborator"
        fi
    fi
    
    echo
    echo "Adding $user to $repo as writer..."
    if [ "$DRY_RUN" != true ]; then
        if ! gh api --silent -XPUT "repos/$repo/collaborators/$user" -f permission=write; then
            echo "✗ Failed to add $user to repository" 1>&2
            echo "Possible reasons:" 1>&2
            echo "  - User '$user' does not exist on GitHub" 1>&2
            echo "  - You don't have admin access to the repository" 1>&2
            echo "  - Organization policies prevent adding collaborators" 1>&2
            echo "  - Rate limiting or API issues" 1>&2
            echo "Try adding manually: https://github.com/$repo/settings/access" 1>&2
            return 1
        fi
        echo "✓ User added successfully!"
    else
        echo "[DRY RUN] Would add user as writer"
    fi
    
    echo
    echo "=== Summary ==="
    echo "Repository: $repo"
    echo "Student: $user"
    echo "Permission: write"
    echo "Status: ✅ Repository corruption fixed. New invitation sent to student via email"
    echo
    if [ "$DRY_RUN" != true ]; then
        echo "Next steps:"
        echo "1. User can accept the invitation at: https://github.com/$repo/invitations"
        echo "2. Or check all invitations at: https://github.com/notifications"
        echo "3. Repository access can be managed at: https://github.com/$repo/settings/access"
    fi
    echo
    
    return 0
}

# Function to process batch mode
process_batch() {
    local batch_file="$1"
    local prefix="$2"
    local org="$3"
    
    echo "=== BATCH MODE ==="
    echo "Batch file: $batch_file"
    echo "Assignment: $prefix"
    echo "Organization: $org"
    if [ "$REPO_URL_MODE" = true ]; then
        echo "Mode: Repository URLs"
    else
        echo "Mode: Usernames"
    fi
    echo
    
    # Read and validate batch file
    if [ ! -r "$batch_file" ]; then
        echo "error: Cannot read batch file '$batch_file'" 1>&2
        exit 1
    fi
    
    local users=()
    
    if [ "$REPO_URL_MODE" = true ]; then
        # Extract usernames from repository URLs
        while IFS= read -r line; do
            # Skip empty lines and comments
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # Trim whitespace
                line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [[ -n "$line" ]]; then
                    # Extract username from URL like https://github.com/org/assignment-username
                    if [[ "$line" =~ ^https://github\.com/$org/$prefix-(.+)$ ]]; then
                        local username="${BASH_REMATCH[1]}"
                        users+=("$username")
                        if [ "$VERBOSE" = true ]; then
                            echo "  Extracted: $username from $line"
                        fi
                    else
                        echo "warning: Cannot extract username from URL: $line" 1>&2
                        echo "  Expected format: https://github.com/$org/$prefix-USERNAME" 1>&2
                    fi
                fi
            fi
        done < "$batch_file"
    else
        # Traditional username mode
        while IFS= read -r line; do
            # Skip empty lines and comments
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # Trim whitespace
                line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [[ -n "$line" ]]; then
                    users+=("$line")
                fi
            fi
        done < "$batch_file"
    fi
    
    if [ ${#users[@]} -eq 0 ]; then
        if [ "$REPO_URL_MODE" = true ]; then
            echo "error: No valid repository URLs found in batch file '$batch_file'" 1>&2
            echo "Expected format: https://github.com/$org/$prefix-USERNAME" 1>&2
        else
            echo "error: No valid usernames found in batch file '$batch_file'" 1>&2
        fi
        exit 1
    fi
    
    echo "Found ${#users[@]} users to process:"
    for user in "${users[@]}"; do
        echo "  - $user"
    done
    echo
    
    # Process each user
    local success_count=0
    local failure_count=0
    local corrupted_count=0
    local ok_count=0
    
    for user in "${users[@]}"; do
        echo "────────────────────────────────────────────────────────────────"
        if process_single_user "$prefix" "$user" "$org"; then
            ((success_count++))
            # Check if it was corrupted by looking at the output
            if check_permissions "$org/$prefix-$user" "$user" > /dev/null 2>&1; then
                ((ok_count++))
            else
                ((corrupted_count++))
            fi
        else
            ((failure_count++))
        fi
        echo
    done
    
    echo "════════════════════════════════════════════════════════════════"
    echo "=== BATCH PROCESSING SUMMARY ==="
    echo "Total users processed: ${#users[@]}"
    echo "Successful operations: $success_count"
    echo "Failed operations: $failure_count"
    if [ "$LIST_MODE" = true ]; then
        echo "Repositories OK: $ok_count"
        echo "Repositories CORRUPTED: $corrupted_count"
    else
        echo "Repositories fixed/processed: $success_count"
    fi
    echo
    
    if [ $failure_count -gt 0 ]; then
        echo "⚠ Some operations failed. Check the output above for details."
        exit 1
    else
        echo "✅ All operations completed successfully!"
    fi
}

check_permissions() {
    local repo="$1"
    local user="$2"
    
    echo "Checking user permissions..."
    
    # Check if user is a collaborator
    if $GH api "repos/$repo/collaborators/$user" > /dev/null 2>&1; then
        echo "✓ $user is a collaborator"
        return 0
    else
        echo "⚠ $user is not currently a collaborator - REPOSITORY IS CORRUPTED"
        return 1
    fi
}

check_invitations() {
    local repo="$1"
    local user="$2"
    
    echo "Checking pending invitations..."
    local temp_file=$(mktemp)
    if $GH api "repos/$repo/invitations" > "$temp_file" 2>/dev/null; then
        local invitations=$(jq --arg user "$user" '.[] | select(.invitee.login == $user)' "$temp_file" 2>/dev/null || echo "")
        if [ -n "$invitations" ]; then
            local invitation_id=$(echo "$invitations" | jq -r '.id' 2>/dev/null || echo "unknown")
            local created_at=$(echo "$invitations" | jq -r '.created_at' 2>/dev/null || echo "unknown")
            echo "ℹ Found pending invitation (ID: $invitation_id, created: $created_at)"
            rm -f "$temp_file"
            return 0
        fi
    fi
    
    rm -f "$temp_file"
    echo "ℹ No pending invitations found for $user"
    return 1
}

# Main execution logic
if [ "$BATCH_MODE" = true ]; then
    # Batch mode: process multiple users from file
    process_batch "$BATCH_FILE" "$PREFIX" "$ORG"
else
    # Single mode: process one user
    process_single_user "$PREFIX" "$GHUSER" "$ORG"
fi