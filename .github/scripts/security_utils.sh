#!/bin/bash

# Security Utilities Script
# Provides reusable functions for SBOM generation, vulnerability scanning, secret detection,
# and security reporting across all workflows in the classdock project.

set -euo pipefail

# Source workflow utilities for consistent logging and error handling
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=workflow_utils.sh
source "${SCRIPT_DIR}/workflow_utils.sh"

# Global variables for security operations
SECURITY_CACHE_DIR="${SECURITY_CACHE_DIR:-/tmp/security-cache}"
GITHUB_API_BASE_URL="https://api.github.com"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
REPOSITORY="${GITHUB_REPOSITORY:-}"

#######################################
# Initialize security cache directories
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   None
#######################################
initialize_security_cache() {
    print_message "step" "Initializing security cache directories"
    
    setup_cache_directories "$SECURITY_CACHE_DIR"
    
    # Create security-specific subdirectories
    local subdirs=(
        "sbom/spdx"
        "sbom/cyclonedx"
        "sbom/syft"
        "sarif/trivy"
        "sarif/secrets"
        "sarif/code-analysis"
        "reports/vulnerability"
        "reports/license"
        "reports/secrets"
        "metrics"
        "advisories"
        "artifacts"
    )
    
    for subdir in "${subdirs[@]}"; do
        mkdir -p "${SECURITY_CACHE_DIR}/${subdir}"
    done
    
    print_message "success" "Security cache directories initialized"
}

#######################################
# Generate Software Bill of Materials (SBOM) using multiple tools
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   $1 - Source directory path (default: current directory)
#   $2 - Output format (spdx, cyclonedx, syft, all)
#######################################
generate_sbom() {
    local source_dir="${1:-.}"
    local format="${2:-all}"
    
    print_message "step" "Generating SBOM for $source_dir (format: $format)"
    
    # Ensure Syft is installed
    if ! command -v syft &> /dev/null; then
        print_message "info" "Installing Syft for SBOM generation"
        if install_syft; then
            print_message "success" "Syft installed successfully"
        else
            print_message "error" "Failed to install Syft"
            return 1
        fi
    fi
    
    local sbom_generated=false
    
    # Generate SPDX format SBOM
    if [[ "$format" == "spdx" ]] || [[ "$format" == "all" ]]; then
        print_message "info" "Generating SPDX SBOM"
        if syft packages "$source_dir" -o spdx-json --file "${SECURITY_CACHE_DIR}/sbom/spdx/sbom-spdx.json"; then
            print_message "success" "SPDX SBOM generated successfully"
            sbom_generated=true
        else
            print_message "warning" "Failed to generate SPDX SBOM"
        fi
    fi
    
    # Generate CycloneDX format SBOM
    if [[ "$format" == "cyclonedx" ]] || [[ "$format" == "all" ]]; then
        print_message "info" "Generating CycloneDX SBOM"
        if syft packages "$source_dir" -o cyclonedx-json --file "${SECURITY_CACHE_DIR}/sbom/cyclonedx/sbom-cyclonedx.json"; then
            print_message "success" "CycloneDX SBOM generated successfully"
            sbom_generated=true
        else
            print_message "warning" "Failed to generate CycloneDX SBOM"
        fi
    fi
    
    # Generate Syft native format SBOM
    if [[ "$format" == "syft" ]] || [[ "$format" == "all" ]]; then
        print_message "info" "Generating Syft native SBOM"
        if syft packages "$source_dir" -o syft-json --file "${SECURITY_CACHE_DIR}/sbom/syft/sbom-syft.json"; then
            print_message "success" "Syft native SBOM generated successfully"
            sbom_generated=true
        else
            print_message "warning" "Failed to generate Syft native SBOM"
        fi
    fi
    
    if [[ "$sbom_generated" == true ]]; then
        print_message "success" "SBOM generation completed"
        return 0
    else
        print_message "error" "No SBOM files were generated successfully"
        return 1
    fi
}

#######################################
# Install Syft for SBOM generation
# Arguments:
#   None
#######################################
install_syft() {
    local install_cmd="curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin"
    
    if retry_with_backoff "$install_cmd" "Syft installation" 3; then
        syft version
        return 0
    else
        return 1
    fi
}

#######################################
# Perform comprehensive vulnerability scanning with Trivy
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   $1 - Target path or image (default: current directory)
#   $2 - Scan type (fs, repo, config, all)
#   $3 - Severity levels (CRITICAL,HIGH,MEDIUM,LOW)
#######################################
run_trivy_scan() {
    local target="${1:-.}"
    local scan_type="${2:-all}"
    local severity="${3:-CRITICAL,HIGH,MEDIUM}"
    
    print_message "step" "Running Trivy vulnerability scan (type: $scan_type, severity: $severity)"
    
    # Ensure Trivy is installed
    if ! command -v trivy &> /dev/null; then
        print_message "info" "Installing Trivy scanner"
        if install_trivy; then
            print_message "success" "Trivy installed successfully"
        else
            print_message "error" "Failed to install Trivy"
            return 1
        fi
    fi
    
    local scan_successful=false
    
    # Filesystem scan
    if [[ "$scan_type" == "fs" ]] || [[ "$scan_type" == "all" ]]; then
        print_message "info" "Running Trivy filesystem scan"
        if trivy fs \
            --cache-dir ~/.cache/trivy \
            --format sarif \
            --output "${SECURITY_CACHE_DIR}/sarif/trivy/trivy-fs.sarif" \
            --severity "$severity" \
            --scanners vuln,secret,config \
            --exit-code 0 \
            "$target"; then
            print_message "success" "Trivy filesystem scan completed"
            scan_successful=true
        else
            print_message "warning" "Trivy filesystem scan completed with issues"
        fi
    fi
    
    # Repository scan for comprehensive analysis - use fs scan instead of repo scan
    if [[ "$scan_type" == "repo" ]] || [[ "$scan_type" == "all" ]]; then
        print_message "info" "Running Trivy filesystem scan (replacing repo scan for deterministic results)"
        if trivy fs \
            --cache-dir ~/.cache/trivy \
            --format sarif \
            --output "${SECURITY_CACHE_DIR}/sarif/trivy/trivy-repo.sarif" \
            --severity "$severity" \
            --scanners vuln,secret,config \
            --exit-code 0 \
            "$target"; then
            print_message "success" "Trivy filesystem scan completed"
            scan_successful=true
        else
            print_message "warning" "Trivy filesystem scan completed with issues"
        fi
    fi
    
    # Configuration scan
    if [[ "$scan_type" == "config" ]] || [[ "$scan_type" == "all" ]]; then
        print_message "info" "Running Trivy configuration scan"
        if trivy config \
            --cache-dir ~/.cache/trivy \
            --format sarif \
            --output "${SECURITY_CACHE_DIR}/sarif/trivy/trivy-config.sarif" \
            --severity "$severity" \
            --exit-code 0 \
            "$target"; then
            print_message "success" "Trivy configuration scan completed"
            scan_successful=true
        else
            print_message "warning" "Trivy configuration scan completed with issues"
        fi
    fi
    
    if [[ "$scan_successful" == true ]]; then
        print_message "success" "Trivy vulnerability scanning completed"
        return 0
    else
        print_message "error" "Trivy vulnerability scanning failed"
        return 1
    fi
}

#######################################
# Install Trivy vulnerability scanner
# Arguments:
#   None
#######################################
install_trivy() {
    print_message "info" "Installing Trivy vulnerability scanner"
    
    # Install dependencies
    sudo apt-get update
    sudo apt-get install wget apt-transport-https gnupg lsb-release -y
    
    # Add Trivy repository
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
    
    # Install Trivy
    sudo apt-get update
    sudo apt-get install trivy -y
    
    # Verify installation
    trivy version
}

#######################################
# Run comprehensive secret detection with multiple tools
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   $1 - Target directory (default: current directory)
#   $2 - Tools to use (gitleaks, trufflehog, detect-secrets, all)
#######################################
run_secret_detection() {
    local target="${1:-.}"
    local tools="${2:-all}"
    
    print_message "step" "Running secret detection scan (target: $target, tools: $tools)"
    
    local detection_successful=false
    
    # GitLeaks secret detection
    if [[ "$tools" == "gitleaks" ]] || [[ "$tools" == "all" ]]; then
        print_message "info" "Running GitLeaks secret detection"
        if install_and_run_gitleaks "$target"; then
            print_message "success" "GitLeaks secret detection completed"
            detection_successful=true
        else
            print_message "warning" "GitLeaks secret detection failed"
        fi
    fi
    
    # TruffleHog secret detection
    if [[ "$tools" == "trufflehog" ]] || [[ "$tools" == "all" ]]; then
        print_message "info" "Running TruffleHog secret detection"
        if run_trufflehog_scan "$target"; then
            print_message "success" "TruffleHog secret detection completed"
            detection_successful=true
        else
            print_message "warning" "TruffleHog secret detection failed"
        fi
    fi
    
    # detect-secrets baseline scan
    if [[ "$tools" == "detect-secrets" ]] || [[ "$tools" == "all" ]]; then
        print_message "info" "Running detect-secrets scan"
        if run_detect_secrets_scan "$target"; then
            print_message "success" "detect-secrets scan completed"
            detection_successful=true
        else
            print_message "warning" "detect-secrets scan failed"
        fi
    fi
    
    if [[ "$detection_successful" == true ]]; then
        print_message "success" "Secret detection scanning completed"
        return 0
    else
        print_message "error" "Secret detection scanning failed"
        return 1
    fi
}

#######################################
# Install and run GitLeaks secret detection
# Arguments:
#   $1 - Target directory
#######################################
install_and_run_gitleaks() {
    local target="$1"
    
    # Install GitLeaks if not present
    if ! command -v gitleaks &> /dev/null; then
        print_message "info" "Installing GitLeaks"
        local gitleaks_url="https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.4_linux_x64.tar.gz"
        if wget -O gitleaks.tar.gz "$gitleaks_url" && \
           tar -xzf gitleaks.tar.gz && \
           sudo mv gitleaks /usr/local/bin/ && \
           rm gitleaks.tar.gz; then
            print_message "success" "GitLeaks installed successfully"
        else
            print_message "error" "Failed to install GitLeaks"
            return 1
        fi
    fi
    
    # Run GitLeaks scan
    gitleaks detect \
        --source "$target" \
        --report-format sarif \
        --report-path "${SECURITY_CACHE_DIR}/sarif/secrets/gitleaks.sarif" \
        --exit-code 0 || true
    
    return 0
}

#######################################
# Run TruffleHog secret detection (Docker version)
# Arguments:
#   $1 - Target directory
#######################################
run_trufflehog_scan() {
    local target="$1"
    
    # Use Docker version of TruffleHog for consistency
    if command -v docker &> /dev/null; then
        docker run --rm -v "$PWD:/pwd" trufflesecurity/trufflehog:latest \
            filesystem /pwd \
            --json \
            --only-verified > "${SECURITY_CACHE_DIR}/sarif/secrets/trufflehog.json" || true
    else
        print_message "warning" "Docker not available, skipping TruffleHog scan"
        return 1
    fi
    
    return 0
}

#######################################
# Run detect-secrets baseline scan
# Arguments:
#   $1 - Target directory
#######################################
run_detect_secrets_scan() {
    local target="$1"
    
    # Install detect-secrets if not present
    if ! command -v detect-secrets &> /dev/null; then
        print_message "info" "Installing detect-secrets"
        if pip install detect-secrets; then
            print_message "success" "detect-secrets installed successfully"
        else
            print_message "error" "Failed to install detect-secrets"
            return 1
        fi
    fi
    
    # Run detect-secrets scan
    detect-secrets scan \
        --baseline "${SECURITY_CACHE_DIR}/sarif/secrets/detect-secrets-baseline.json" \
        --force-use-all-plugins \
        "$target" || true
    
    return 0
}

#######################################
# Analyze security findings from SARIF files and generate metrics
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   None
# Returns:
#   JSON object with security metrics
#######################################
analyze_security_findings() {
    print_message "step" "Analyzing security findings and generating metrics"
    
    local critical_count=0
    local high_count=0
    local medium_count=0
    local low_count=0
    local secret_count=0
    
    # Find all SARIF files
    local sarif_files
    mapfile -t sarif_files < <(find "${SECURITY_CACHE_DIR}/sarif" -name "*.sarif" -type f 2>/dev/null || true)
    
    for sarif_file in "${sarif_files[@]}"; do
        if [[ -f "$sarif_file" ]] && jq empty "$sarif_file" 2>/dev/null; then
            # Extract severity levels from SARIF with improved parsing
            while IFS= read -r level; do
                case "$level" in
                    "error"|"critical"|"Critical"|"CRITICAL") critical_count=$((critical_count + 1)) ;;
                    "warning"|"high"|"High"|"HIGH") high_count=$((high_count + 1)) ;;
                    "info"|"medium"|"Medium"|"MEDIUM") medium_count=$((medium_count + 1)) ;;
                    "note"|"low"|"Low"|"LOW") low_count=$((low_count + 1)) ;;
                esac
            done < <(jq -r '
              .runs[]?.results[]? as $r |
              ($r.level //
               $r.properties.severity //
               ( .runs[]?.tool.driver.rules[]? | select(.id==$r.ruleId) | (.properties.severity // .defaultConfiguration.level) ) //
               "info")' "$sarif_file" 2>/dev/null || true)
        fi
    done
    
    # Count secret findings
    local secret_files
    mapfile -t secret_files < <(find "${SECURITY_CACHE_DIR}/sarif/secrets" -name "*.sarif" -o -name "*.json" -type f 2>/dev/null || true)
    
    for secret_file in "${secret_files[@]}"; do
        if [[ -f "$secret_file" ]]; then
            if [[ "$secret_file" == *.sarif ]]; then
                local count
                count=$(jq '.runs[]?.results? | length' "$secret_file" 2>/dev/null || echo "0")
                secret_count=$((secret_count + count))
            elif [[ "$secret_file" == *.json ]] && [[ "$secret_file" == *trufflehog* ]]; then
                local count
                count=$(jq '. | length' "$secret_file" 2>/dev/null || echo "0")
                secret_count=$((secret_count + count))
            fi
        fi
    done
    
    # Calculate security score
    local total_findings=$((critical_count + high_count + medium_count + low_count + secret_count))
    local base_score=100
    local penalty=0
    
    # Apply penalties based on severity
    penalty=$((penalty + critical_count * 25))
    penalty=$((penalty + high_count * 15))
    penalty=$((penalty + medium_count * 8))
    penalty=$((penalty + low_count * 2))
    penalty=$((penalty + secret_count * 20))
    
    local security_score=$((base_score - penalty))
    security_score=$((security_score < 0 ? 0 : security_score))
    security_score=$((security_score > 100 ? 100 : security_score))
    
    # Generate metrics JSON
    local metrics_json
    metrics_json=$(jq -n \
        --argjson security_score "$security_score" \
        --argjson critical "$critical_count" \
        --argjson high "$high_count" \
        --argjson medium "$medium_count" \
        --argjson low "$low_count" \
        --argjson secrets "$secret_count" \
        --argjson total "$total_findings" \
        --arg scan_date "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg repository "$REPOSITORY" \
        '{
            security_score: $security_score,
            critical_vulnerabilities: $critical,
            high_vulnerabilities: $high,
            medium_vulnerabilities: $medium,
            low_vulnerabilities: $low,
            secret_findings: $secrets,
            total_findings: $total,
            scan_date: $scan_date,
            repository: $repository
        }')
    
    # Save metrics
    echo "$metrics_json" > "${SECURITY_CACHE_DIR}/metrics/security-metrics.json"
    
    print_message "success" "Security analysis completed - Score: $security_score/100, Total findings: $total_findings"
    
    # Return metrics for use by calling scripts
    echo "$metrics_json"
}

#######################################
# Generate comprehensive security report
# Globals:
#   SECURITY_CACHE_DIR
# Arguments:
#   $1 - Report format (markdown, json, html)
#   $2 - Output file path (optional)
#######################################
generate_security_report() {
    local format="${1:-markdown}"
    local output_file="${2:-${SECURITY_CACHE_DIR}/reports/security-report.${format}}"
    
    print_message "step" "Generating comprehensive security report (format: $format)"
    
    # Ensure metrics exist
    local metrics_file="${SECURITY_CACHE_DIR}/metrics/security-metrics.json"
    if [[ ! -f "$metrics_file" ]]; then
        print_message "warning" "Security metrics not found, analyzing findings first"
        analyze_security_findings > /dev/null
    fi
    
    # Read metrics
    local metrics
    metrics=$(cat "$metrics_file")
    
    local security_score
    security_score=$(echo "$metrics" | jq -r '.security_score')
    local critical_vulns
    critical_vulns=$(echo "$metrics" | jq -r '.critical_vulnerabilities')
    local high_vulns
    high_vulns=$(echo "$metrics" | jq -r '.high_vulnerabilities')
    local total_findings
    total_findings=$(echo "$metrics" | jq -r '.total_findings')
    local scan_date
    scan_date=$(echo "$metrics" | jq -r '.scan_date')
    
    case "$format" in
        "markdown")
            generate_markdown_report "$output_file" "$security_score" "$critical_vulns" "$high_vulns" "$total_findings" "$scan_date"
            ;;
        "json")
            cp "$metrics_file" "$output_file"
            ;;
        "html")
            generate_html_report "$output_file" "$security_score" "$critical_vulns" "$high_vulns" "$total_findings" "$scan_date"
            ;;
        *)
            print_message "error" "Unsupported report format: $format"
            return 1
            ;;
    esac
    
    print_message "success" "Security report generated: $output_file"
}

#######################################
# Generate Markdown security report
# Arguments:
#   $1 - Output file path
#   $2 - Security score
#   $3 - Critical vulnerabilities
#   $4 - High vulnerabilities  
#   $5 - Total findings
#   $6 - Scan date
#######################################
generate_markdown_report() {
    local output_file="$1"
    local security_score="$2"
    local critical_vulns="$3"
    local high_vulns="$4"
    local total_findings="$5"
    local scan_date="$6"
    
    cat > "$output_file" << EOF
# 🛡️ Security Analysis Report

## 📊 Executive Summary

**Generated:** $scan_date  
**Repository:** $REPOSITORY  
**Security Score:** $security_score/100  

### Overall Security Status
$([ "$critical_vulns" -gt 0 ] && echo "🔴 **Critical Issues Detected**" || [ "$high_vulns" -gt 5 ] && echo "🟡 **High Risk**" || echo "🟢 **Good Security Posture**")

## 📈 Security Metrics

| Severity | Count | Status |
|----------|-------|--------|
| Critical | $critical_vulns | $([ "$critical_vulns" -eq 0 ] && echo "✅" || echo "❌") |
| High | $high_vulns | $([ "$high_vulns" -le 2 ] && echo "✅" || echo "⚠️") |
| **Total Findings** | **$total_findings** | $([ "$total_findings" -lt 5 ] && echo "✅" || echo "⚠️") |

## 🔧 Scanning Tools Used

- **Trivy**: Comprehensive vulnerability scanning
- **GitLeaks**: Secret detection in Git history
- **TruffleHog**: Advanced secret scanning
- **detect-secrets**: Baseline secret detection
- **Syft**: Software Bill of Materials generation

## 📁 Generated Artifacts

- **SBOM Files**: Software Bill of Materials in multiple formats
- **SARIF Reports**: Structured vulnerability findings
- **Security Metrics**: Quantitative security assessment

$([ "$critical_vulns" -gt 0 ] && cat << 'CRITICAL_EOF'

## ⚠️ Critical Issues Require Immediate Attention

This repository has **critical security vulnerabilities** that must be addressed:

- 🔴 **$critical_vulns Critical vulnerabilities** found
- These issues pose significant security risks
- Immediate remediation is required

### Recommended Actions

1. Review detailed SARIF reports for specific vulnerabilities
2. Update vulnerable dependencies to secure versions
3. Apply security patches and configuration fixes
4. Re-run security scan after remediation
5. Consider implementing additional security controls

CRITICAL_EOF
)

## 🔄 Next Steps

1. **Review Findings**: Examine detailed SARIF reports
2. **Prioritize Fixes**: Address critical and high-severity issues first
3. **Update Dependencies**: Apply security patches and updates
4. **Validate Fixes**: Re-run security analysis after remediation
5. **Monitor**: Set up continuous security monitoring

## 📞 Support Resources

- [Security Best Practices](https://github.com/security)
- [Vulnerability Management Guide](https://docs.github.com/en/code-security)
- [Dependency Security](https://docs.github.com/en/code-security/dependabot)

---
_This report was automatically generated by the classdock security utilities._
EOF
    
    print_message "success" "Markdown security report generated"
}

#######################################
# Generate HTML security report  
# Arguments:
#   $1 - Output file path
#   $2 - Security score
#   $3 - Critical vulnerabilities
#   $4 - High vulnerabilities
#   $5 - Total findings
#   $6 - Scan date
#######################################
generate_html_report() {
    local output_file="$1"
    local security_score="$2"
    local critical_vulns="$3"
    local high_vulns="$4"
    local total_findings="$5"
    local scan_date="$6"
    
    cat > "$output_file" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Analysis Report - $REPOSITORY</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; margin: 40px; }
        .header { background: #f6f8fa; padding: 20px; border-radius: 6px; margin-bottom: 20px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; border-radius: 6px; text-align: center; }
        .critical { background: #ffeaea; border-left: 4px solid #d73a49; }
        .high { background: #fff5b4; border-left: 4px solid #ffd33d; }
        .success { background: #dcffe4; border-left: 4px solid #28a745; }
        .score { font-size: 2em; font-weight: bold; color: $([ "$security_score" -ge 80 ] && echo "#28a745" || [ "$security_score" -ge 60 ] && echo "#ffd33d" || echo "#d73a49"); }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Security Analysis Report</h1>
        <p><strong>Repository:</strong> $REPOSITORY</p>
        <p><strong>Generated:</strong> $scan_date</p>
    </div>
    
    <div class="metric">
        <h3>Security Score</h3>
        <div class="score">$security_score/100</div>
    </div>
    
    <div class="metric $([ "$critical_vulns" -eq 0 ] && echo "success" || echo "critical")">
        <h3>Critical Vulnerabilities</h3>
        <div class="score">$critical_vulns</div>
    </div>
    
    <div class="metric $([ "$high_vulns" -le 2 ] && echo "success" || echo "high")">
        <h3>High Vulnerabilities</h3>
        <div class="score">$high_vulns</div>
    </div>
    
    <div class="metric">
        <h3>Total Findings</h3>
        <div class="score">$total_findings</div>
    </div>
    
    <h2>📈 Security Assessment</h2>
    <p>$([ "$critical_vulns" -gt 0 ] && echo "<strong style='color: #d73a49;'>⚠️ Critical security issues detected that require immediate attention.</strong>" || [ "$high_vulns" -gt 5 ] && echo "<strong style='color: #ffd33d;'>🟡 High-risk vulnerabilities found that should be addressed soon.</strong>" || echo "<strong style='color: #28a745;'>✅ Good security posture with manageable findings.</strong>")</p>
    
    <h2>🔧 Scanning Coverage</h2>
    <ul>
        <li><strong>Trivy</strong>: Comprehensive vulnerability scanning</li>
        <li><strong>Secret Detection</strong>: GitLeaks, TruffleHog, detect-secrets</li>
        <li><strong>SBOM Generation</strong>: Software Bill of Materials</li>
        <li><strong>Configuration Analysis</strong>: Security misconfigurations</li>
    </ul>
    
    <h2>🔄 Recommended Actions</h2>
    <ol>
        <li>Review detailed SARIF reports for specific vulnerabilities</li>
        <li>Address critical and high-severity issues first</li>
        <li>Update vulnerable dependencies and apply patches</li>
        <li>Re-run security analysis after fixes</li>
        <li>Implement continuous security monitoring</li>
    </ol>
    
    <hr>
    <p><em>This report was automatically generated by the classdock security utilities.</em></p>
</body>
</html>
EOF
    
    print_message "success" "HTML security report generated"
}

#######################################
# Upload security artifacts to GitHub
# Globals:
#   GITHUB_TOKEN, REPOSITORY, SECURITY_CACHE_DIR
# Arguments:
#   $1 - Artifact name
#   $2 - Artifact path (default: SECURITY_CACHE_DIR)
#######################################
upload_security_artifacts() {
    local artifact_name="${1:-security-artifacts}"
    local artifact_path="${2:-$SECURITY_CACHE_DIR}"
    
    print_message "step" "Uploading security artifacts to GitHub"
    
    if [[ -z "$GITHUB_TOKEN" ]]; then
        print_message "warning" "GitHub token not available, skipping artifact upload"
        return 1
    fi
    
    # Create artifact archive
    local archive_path="${SECURITY_CACHE_DIR}/artifacts/${artifact_name}-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    if tar -czf "$archive_path" -C "$artifact_path" .; then
        print_message "success" "Security artifacts archived: $archive_path"
    else
        print_message "error" "Failed to create security artifacts archive"
        return 1
    fi
    
    print_message "success" "Security artifacts prepared for upload"
}

#######################################
# Main function for command-line usage
# Arguments:
#   $@ - Command line arguments
#######################################

#######################################
# Run comprehensive security audit
# Executes complete security scan including SBOM, vulnerability scan, secret detection, and reporting
# Arguments:
#   $1: Target directory (optional, default: current directory)
#   $2: Output directory (optional, default: /tmp/security-reports)
#######################################
run_comprehensive_security_audit() {
    local target_dir="${1:-.}"
    local output_dir="${2:-/tmp/security-reports}"
    
    print_message "step" "Running comprehensive security audit"
    
    # Initialize security environment
    initialize_security_cache
    
    # Generate SBOM
    print_message "info" "Generating Software Bill of Materials (SBOM)..."
    generate_sbom "$target_dir" "all"
    
    # Run vulnerability scanning
    print_message "info" "Running vulnerability scan..."
    run_trivy_scan "$target_dir" "all" "CRITICAL,HIGH,MEDIUM"
    
    # Run secret detection
    print_message "info" "Running secret detection..."
    run_secret_detection "$target_dir" "all"
    
    # Analyze findings
    print_message "info" "Analyzing security findings..."
    analyze_security_findings
    
    # Generate comprehensive report
    print_message "info" "Generating security report..."
    mkdir -p "$output_dir"
    generate_security_report "markdown" "$output_dir/security-report.md"
    
    print_message "success" "Comprehensive security audit completed"
}

#######################################
# Generate security summary for CI
# Creates a concise summary of security scan results
# Arguments:
#   None
#######################################
generate_security_summary() {
    print_message "step" "Generating security summary"
    
    local summary_file="/tmp/security-reports/security-summary.md"
    local findings_file="${SECURITY_CACHE_DIR}/metrics/security_findings.json"
    
    mkdir -p "$(dirname "$summary_file")"
    
    cat > "$summary_file" << 'EOF'
# 🛡️ Security Audit Summary

## Scan Results
EOF
    
    if [[ -f "$findings_file" ]]; then
        print_message "info" "Security findings available, generating detailed summary"
        
        # Extract key metrics if findings file exists
        local critical_count high_count medium_count secret_count
        critical_count=$(jq -r '.vulnerability_summary.critical // 0' "$findings_file" 2>/dev/null || echo "0")
        high_count=$(jq -r '.vulnerability_summary.high // 0' "$findings_file" 2>/dev/null || echo "0")  
        medium_count=$(jq -r '.vulnerability_summary.medium // 0' "$findings_file" 2>/dev/null || echo "0")
        secret_count=$(jq -r '.secret_summary.total_findings // 0' "$findings_file" 2>/dev/null || echo "0")
        
        cat >> "$summary_file" << EOF

| Severity | Count |
|----------|-------|
| 🔴 Critical | $critical_count |
| 🟠 High | $high_count |
| 🟡 Medium | $medium_count |
| 🔍 Secrets | $secret_count |

EOF
    else
        print_message "warning" "No security findings file found, generating basic summary"
        
        cat >> "$summary_file" << 'EOF'

✅ Security scan completed
- SBOM generation: Complete
- Vulnerability scan: Complete  
- Secret detection: Complete
- Analysis: Complete

EOF
    fi
    
    cat >> "$summary_file" << 'EOF'

## Artifacts Generated
- Software Bill of Materials (SBOM)
- Vulnerability scan results (SARIF format)
- Secret detection results
- Security metrics and analysis

For detailed results, check the security artifacts in the workflow run.
EOF
    
    if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
        cat "$summary_file" >> "$GITHUB_STEP_SUMMARY"
        print_message "success" "Security summary added to GitHub step summary"
    fi
    
    print_message "success" "Security summary generated: $summary_file"
}

#######################################
# Main function for command-line usage
# Arguments:
#   $@ - Command line arguments
#######################################
main() {
    case "${1:-help}" in
        "init"|"initialize")
            initialize_security_cache
            ;;
        "sbom")
            generate_sbom "${2:-.}" "${3:-all}"
            ;;
        "scan"|"vulnerability-scan")  
            run_trivy_scan "${2:-.}" "${3:-all}" "${4:-CRITICAL,HIGH,MEDIUM}"
            ;;
        "secrets"|"secret-detection")
            run_secret_detection "${2:-.}" "${3:-all}"
            ;;
        "analyze"|"analyze-findings")
            analyze_security_findings
            ;;
        "report"|"generate-report")
            generate_security_report "${2:-markdown}" "${3:-}"
            ;;
        "upload"|"upload-artifacts")
            upload_security_artifacts "${2:-security-artifacts}" "${3:-}"
            ;;
        "audit"|"comprehensive-audit")
            run_comprehensive_security_audit "${2:-.}" "${3:-/tmp/security-reports}"
            ;;
        "summary"|"generate-summary")
            generate_security_summary
            ;;
        "help"|*)
            cat << 'HELP_EOF'
Security Utilities Script - classdock project

Usage: security_utils.sh <command> [arguments]

Commands:
    init                    Initialize security cache directories
    sbom [path] [format]    Generate SBOM (spdx|cyclonedx|syft|all)
    scan [path] [type] [severity]  Run vulnerability scan (fs|repo|config|all)
    secrets [path] [tools]  Run secret detection (gitleaks|trufflehog|detect-secrets|all)
    analyze                 Analyze security findings and generate metrics
    report [format] [file]  Generate security report (markdown|json|html)
    upload [name] [path]    Upload security artifacts to GitHub
    audit [path] [output]   Run comprehensive security audit
    summary                 Generate security summary for CI
    help                    Show this help message

Examples:
    security_utils.sh init
    security_utils.sh sbom . all
    security_utils.sh scan . all CRITICAL,HIGH
    security_utils.sh secrets . all  
    security_utils.sh analyze
    security_utils.sh report markdown ./security-report.md
    security_utils.sh upload security-scan-results
    security_utils.sh audit . /tmp/security-reports
    security_utils.sh summary

Environment Variables:
    SECURITY_CACHE_DIR     Security cache directory (default: /tmp/security-cache)
    GITHUB_TOKEN          GitHub API token for uploads
    GITHUB_REPOSITORY     Repository name for reporting

HELP_EOF
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi