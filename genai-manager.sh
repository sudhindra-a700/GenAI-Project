#!/bin/bash

# GenAI Smart Contract Pro - Master Management Script
# Central script to manage all project operations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script version
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Available scripts
declare -A SCRIPTS=(
    ["setup"]="setup.sh"
    ["dev-setup"]="dev_setup.sh"
    ["configure-env"]="configure_env.sh"
    ["manage-secrets"]="manage_secrets.sh"
    ["deploy-cloud"]="deploy_cloud.sh"
    ["deploy-advanced"]="deploy_advanced.sh"
    ["deploy-ci"]="deploy_ci.sh"
    ["deploy-local"]="deploy_local.sh"
    ["test"]="test.sh"
    ["test-comprehensive"]="test_comprehensive.sh"
    ["test-load"]="test_load.sh"
    ["monitor"]="monitor.sh"
    ["maintenance"]="maintenance.sh"
    ["utils"]="utils.sh"
    ["database"]="database.sh"
)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_manager() {
    echo -e "${PURPLE}[MANAGER]${NC} $1"
}

show_banner() {
    cat << 'EOF'
   ____            _    ___   ____            _                  _     ____            
  / ___| ___ _ __ / \  |_ _| / ___|___  _ __ | |_ _ __ __ _  ___| |_  |  _ \ _ __ ___  
 | |  _ / _ \ '_ \/ _ \  | | | |   / _ \| '_ \| __| '__/ _` |/ __| __| | |_) | '__/ _ \ 
 | |_| |  __/ | | / ___ \| | | |__| (_) | | | | |_| | | (_| | (__| |_  |  __/| | | (_) |
  \____|\___|_| |_/_/   \_\___|\____\___/|_| |_|\__|_|  \__,_|\___|\__| |_|   |_|  \___/ 
                                                                                        
EOF
    echo -e "${CYAN}GenAI Smart Contract Pro - Master Management Script v$VERSION${NC}"
    echo -e "${BLUE}Comprehensive automation for deployment, testing, and operations${NC}"
    echo ""
}

show_help() {
    show_banner
    cat << EOF
USAGE:
    $0 [COMMAND] [SCRIPT_OPTIONS...]

COMMANDS:
    setup                   Initial project setup
    dev-setup              Development environment setup
    configure-env          Environment configuration management
    manage-secrets         Secure secrets management
    
    deploy-cloud           Deploy to Google Cloud Run
    deploy-advanced        Advanced deployment strategies
    deploy-ci              CI/CD pipeline deployment
    deploy-local           Local development deployment
    
    test                   Basic testing
    test-comprehensive     Complete testing suite
    test-load              Load testing and performance
    
    monitor                System monitoring and health checks
    maintenance            Routine maintenance tasks
    
    utils                  General utilities and tools
    database               Database management operations
    
    list                   List all available scripts
    status                 Show project status
    health                 Quick health check
    info                   Show project information
    validate               Validate complete setup
    
    help, --help, -h       Show this help message
    version, --version     Show version information

WORKFLOW COMMANDS:
    init                   Complete initial setup (setup + configure + database)
    dev                    Start development environment
    deploy                 Deploy to production
    test-all               Run all tests
    monitor-start          Start monitoring
    maintenance-run        Run maintenance tasks

EXAMPLES:
    $0 init                                    # Complete project initialization
    $0 dev                                     # Start development environment
    $0 deploy --environment production         # Deploy to production
    $0 test-all --coverage                     # Run all tests with coverage
    $0 monitor status                          # Check monitoring status
    $0 utils info                              # Show project information

SCRIPT OPTIONS:
    All options after the command are passed directly to the underlying script.
    Use '$0 [COMMAND] --help' to see script-specific options.

ENVIRONMENT VARIABLES:
    GENAI_ENVIRONMENT      Environment (development/staging/production)
    GENAI_PROJECT_ID       Google Cloud project ID
    GENAI_REGION           Google Cloud region
    GENAI_SERVICE_NAME     Cloud Run service name
    GENAI_BACKEND_URL      Backend URL for testing

For detailed documentation, see: SHELL_SCRIPTS_README.md

EOF
}

check_script_exists() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"
    
    if [[ ! -f "$script_path" ]]; then
        log_error "Script not found: $script_path"
        return 1
    fi
    
    if [[ ! -x "$script_path" ]]; then
        log_warning "Script not executable: $script_path"
        log_info "Making script executable..."
        chmod +x "$script_path"
    fi
    
    return 0
}

run_script() {
    local script_key="$1"
    shift
    
    if [[ -z "${SCRIPTS[$script_key]:-}" ]]; then
        log_error "Unknown script: $script_key"
        log_info "Available scripts: ${!SCRIPTS[*]}"
        return 1
    fi
    
    local script_name="${SCRIPTS[$script_key]}"
    local script_path="$SCRIPT_DIR/$script_name"
    
    if ! check_script_exists "$script_name"; then
        return 1
    fi
    
    log_manager "Running: $script_name $*"
    echo ""
    
    # Execute the script with all remaining arguments
    "$script_path" "$@"
    local exit_code=$?
    
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "Script completed successfully: $script_name"
    else
        log_error "Script failed with exit code $exit_code: $script_name"
    fi
    
    return $exit_code
}

list_scripts() {
    log_manager "Available Scripts"
    echo "=================================="
    echo ""
    
    # Group scripts by category
    echo "🚀 Deployment Scripts:"
    for key in deploy-cloud deploy-advanced deploy-ci deploy-local; do
        if [[ -n "${SCRIPTS[$key]:-}" ]]; then
            local script_name="${SCRIPTS[$key]}"
            local description=""
            case "$key" in
                "deploy-cloud") description="Deploy to Google Cloud Run" ;;
                "deploy-advanced") description="Advanced deployment strategies" ;;
                "deploy-ci") description="CI/CD pipeline deployment" ;;
                "deploy-local") description="Local development deployment" ;;
            esac
            printf "  %-20s %s\n" "$key" "$description"
        fi
    done
    echo ""
    
    echo "⚙️ Setup & Configuration:"
    for key in setup dev-setup configure-env manage-secrets; do
        if [[ -n "${SCRIPTS[$key]:-}" ]]; then
            local description=""
            case "$key" in
                "setup") description="Initial project setup" ;;
                "dev-setup") description="Development environment setup" ;;
                "configure-env") description="Environment configuration" ;;
                "manage-secrets") description="Secure secrets management" ;;
            esac
            printf "  %-20s %s\n" "$key" "$description"
        fi
    done
    echo ""
    
    echo "🧪 Testing Scripts:"
    for key in test test-comprehensive test-load; do
        if [[ -n "${SCRIPTS[$key]:-}" ]]; then
            local description=""
            case "$key" in
                "test") description="Basic testing" ;;
                "test-comprehensive") description="Complete testing suite" ;;
                "test-load") description="Load testing and performance" ;;
            esac
            printf "  %-20s %s\n" "$key" "$description"
        fi
    done
    echo ""
    
    echo "📊 Operations Scripts:"
    for key in monitor maintenance utils database; do
        if [[ -n "${SCRIPTS[$key]:-}" ]]; then
            local description=""
            case "$key" in
                "monitor") description="System monitoring and health checks" ;;
                "maintenance") description="Routine maintenance tasks" ;;
                "utils") description="General utilities and tools" ;;
                "database") description="Database management operations" ;;
            esac
            printf "  %-20s %s\n" "$key" "$description"
        fi
    done
    echo ""
    
    echo "Use '$0 [SCRIPT_NAME] --help' for script-specific options."
}

show_project_status() {
    log_manager "Project Status Overview"
    echo "=================================="
    echo ""
    
    # Check if utils script exists and run project info
    if check_script_exists "utils.sh" &>/dev/null; then
        "$SCRIPT_DIR/utils.sh" info
    else
        log_warning "Utils script not available for detailed status"
        
        # Basic status check
        echo "Basic Status Check:"
        echo "  • Working Directory: $(pwd)"
        echo "  • Scripts Directory: $SCRIPT_DIR"
        echo "  • Available Scripts: ${#SCRIPTS[@]}"
        echo ""
        
        # Check key files
        local key_files=("requirements.txt" "Dockerfile" ".env.example" "README.md")
        echo "Key Files:"
        for file in "${key_files[@]}"; do
            if [[ -f "$file" ]] || [[ -f "backend/$file" ]]; then
                echo "  ✓ $file"
            else
                echo "  ✗ $file (missing)"
            fi
        done
        echo ""
    fi
}

quick_health_check() {
    log_manager "Quick Health Check"
    echo "=================================="
    echo ""
    
    local health_status="HEALTHY"
    local issues=()
    
    # Check script availability
    local missing_scripts=()
    for script_name in "${SCRIPTS[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$script_name" ]]; then
            missing_scripts+=("$script_name")
        fi
    done
    
    if [[ ${#missing_scripts[@]} -gt 0 ]]; then
        health_status="DEGRADED"
        issues+=("Missing scripts: ${missing_scripts[*]}")
    fi
    
    # Check key dependencies
    local missing_deps=()
    local deps=("python3" "curl" "git")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        health_status="UNHEALTHY"
        issues+=("Missing dependencies: ${missing_deps[*]}")
    fi
    
    # Check environment
    if [[ ! -f ".env" ]] && [[ ! -f ".env.example" ]]; then
        health_status="DEGRADED"
        issues+=("No environment configuration found")
    fi
    
    # Display results
    case "$health_status" in
        "HEALTHY")
            log_success "System Status: $health_status"
            ;;
        "DEGRADED")
            log_warning "System Status: $health_status"
            ;;
        "UNHEALTHY")
            log_error "System Status: $health_status"
            ;;
    esac
    
    if [[ ${#issues[@]} -gt 0 ]]; then
        echo ""
        echo "Issues Found:"
        for issue in "${issues[@]}"; do
            echo "  • $issue"
        done
        echo ""
        echo "Run '$0 validate' for detailed validation."
    fi
    
    echo ""
}

validate_setup() {
    log_manager "Validating Complete Setup"
    echo "=================================="
    echo ""
    
    if check_script_exists "utils.sh" &>/dev/null; then
        "$SCRIPT_DIR/utils.sh" validate all "$@"
    else
        log_error "Utils script not available for validation"
        return 1
    fi
}

# Workflow commands
workflow_init() {
    log_manager "Complete Project Initialization"
    echo "=================================="
    echo ""
    
    log_info "Step 1: Initial Setup"
    run_script "setup" "$@" || return 1
    
    log_info "Step 2: Environment Configuration"
    run_script "configure-env" "create" || return 1
    
    log_info "Step 3: Database Initialization"
    run_script "database" "init" || return 1
    
    log_success "Project initialization completed!"
    log_info "Next steps:"
    echo "  1. Edit .env file with your configuration"
    echo "  2. Run '$0 dev' to start development environment"
    echo "  3. Run '$0 test-all' to validate setup"
}

workflow_dev() {
    log_manager "Starting Development Environment"
    echo "=================================="
    echo ""
    
    log_info "Step 1: Development Setup"
    run_script "dev-setup" "$@" || return 1
    
    log_info "Step 2: Database Setup"
    run_script "database" "seed" || return 1
    
    log_info "Step 3: Starting Local Deployment"
    run_script "deploy-local" "start" "$@" || return 1
    
    log_success "Development environment started!"
}

workflow_deploy() {
    log_manager "Production Deployment"
    echo "=================================="
    echo ""
    
    log_info "Step 1: Pre-deployment Validation"
    run_script "utils" "validate" "all" || return 1
    
    log_info "Step 2: Running Tests"
    run_script "test-comprehensive" "all" || return 1
    
    log_info "Step 3: Cloud Deployment"
    run_script "deploy-cloud" "$@" || return 1
    
    log_success "Production deployment completed!"
}

workflow_test_all() {
    log_manager "Running All Tests"
    echo "=================================="
    echo ""
    
    log_info "Step 1: Comprehensive Tests"
    run_script "test-comprehensive" "all" "$@" || return 1
    
    log_info "Step 2: Load Tests"
    run_script "test-load" "mixed" "$@" || return 1
    
    log_success "All tests completed!"
}

workflow_monitor_start() {
    log_manager "Starting Monitoring"
    echo "=================================="
    echo ""
    
    run_script "monitor" "continuous" "$@"
}

workflow_maintenance_run() {
    log_manager "Running Maintenance Tasks"
    echo "=================================="
    echo ""
    
    run_script "maintenance" "all" "$@"
}

main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        # Individual scripts
        "setup"|"dev-setup"|"configure-env"|"manage-secrets")
            run_script "$command" "$@"
            ;;
        "deploy-cloud"|"deploy-advanced"|"deploy-ci"|"deploy-local")
            run_script "$command" "$@"
            ;;
        "test"|"test-comprehensive"|"test-load")
            run_script "$command" "$@"
            ;;
        "monitor"|"maintenance"|"utils"|"database")
            run_script "$command" "$@"
            ;;
        
        # Management commands
        "list")
            list_scripts
            ;;
        "status")
            show_project_status
            ;;
        "health")
            quick_health_check
            ;;
        "info")
            run_script "utils" "info" "$@"
            ;;
        "validate")
            validate_setup "$@"
            ;;
        
        # Workflow commands
        "init")
            workflow_init "$@"
            ;;
        "dev")
            workflow_dev "$@"
            ;;
        "deploy")
            workflow_deploy "$@"
            ;;
        "test-all")
            workflow_test_all "$@"
            ;;
        "monitor-start")
            workflow_monitor_start "$@"
            ;;
        "maintenance-run")
            workflow_maintenance_run "$@"
            ;;
        
        # Help and version
        "help"|"--help"|"-h")
            show_help
            ;;
        "version"|"--version")
            echo "GenAI Smart Contract Pro Manager v$VERSION"
            ;;
        
        # Default
        *)
            if [[ -n "$command" ]]; then
                log_error "Unknown command: $command"
                echo ""
            fi
            show_help
            exit 1
            ;;
    esac
}

# Check if running directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
