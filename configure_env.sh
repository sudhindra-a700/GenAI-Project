#!/bin/bash

# GenAI Smart Contract Pro - Environment Configuration Script
# Comprehensive environment setup for development, staging, and production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"
ENVIRONMENTS=("development" "staging" "production" "testing")
DEFAULT_ENVIRONMENT="development"

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

log_config() {
    echo -e "${PURPLE}[CONFIG]${NC} $1"
}

show_help() {
    cat << EOF
GenAI Smart Contract Pro - Environment Configuration Script

USAGE:
    $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development     Local development environment (default)
    staging         Staging environment for testing
    production      Production environment
    testing         Testing environment for CI/CD

OPTIONS:
    --project-id PROJECT_ID     Google Cloud project ID
    --region REGION             Google Cloud region (default: us-central1)
    --service-account FILE      Path to service account JSON file
    --create-secrets           Create Google Cloud Secret Manager secrets
    --update-extension         Update Chrome extension configuration
    --interactive              Interactive configuration mode
    --validate                 Validate configuration without applying
    --backup                   Backup existing configuration
    --restore FILE             Restore configuration from backup
    --help, -h                 Show this help message

EXAMPLES:
    $0 development                                    # Setup development environment
    $0 production --project-id my-project            # Setup production with project ID
    $0 staging --create-secrets --interactive        # Interactive staging setup
    $0 --validate                                    # Validate current configuration

CONFIGURATION FILES:
    .env                       Main environment file
    .env.development          Development-specific variables
    .env.staging              Staging-specific variables
    .env.production           Production-specific variables
    .env.testing              Testing-specific variables

EOF
}

detect_environment() {
    local env="$DEFAULT_ENVIRONMENT"
    
    # Detect from environment variables
    if [[ -n "${ENVIRONMENT:-}" ]]; then
        env="$ENVIRONMENT"
    elif [[ -n "${NODE_ENV:-}" ]]; then
        env="$NODE_ENV"
    elif [[ -n "${FLASK_ENV:-}" ]]; then
        env="$FLASK_ENV"
    elif [[ "${CI:-false}" == "true" ]]; then
        env="testing"
    fi
    
    # Detect from Git branch
    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        local branch
        branch=$(git branch --show-current 2>/dev/null || echo "")
        
        case "$branch" in
            main|master)
                env="production"
                ;;
            staging|stage)
                env="staging"
                ;;
            develop|development)
                env="development"
                ;;
            test|testing)
                env="testing"
                ;;
        esac
    fi
    
    echo "$env"
}

validate_environment() {
    local env="$1"
    
    if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${env} " ]]; then
        log_error "Invalid environment: $env"
        log_info "Available environments: ${ENVIRONMENTS[*]}"
        exit 1
    fi
}

backup_configuration() {
    log_info "Backing up existing configuration..."
    
    local backup_dir="config-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup environment files
    for file in .env .env.* config.json; do
        if [[ -f "$file" ]]; then
            cp "$file" "$backup_dir/"
            log_info "Backed up: $file"
        fi
    done
    
    # Backup extension files
    if [[ -d "extension" ]]; then
        cp -r extension "$backup_dir/"
        log_info "Backed up: extension/"
    fi
    
    # Create backup manifest
    cat > "$backup_dir/backup-manifest.json" << EOF
{
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "${ENVIRONMENT:-unknown}",
    "project_root": "$PROJECT_ROOT",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')"
}
EOF
    
    log_success "Configuration backed up to: $backup_dir"
    echo "$backup_dir"
}

restore_configuration() {
    local backup_dir="$1"
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    log_info "Restoring configuration from: $backup_dir"
    
    # Restore environment files
    for file in "$backup_dir"/.env*; do
        if [[ -f "$file" ]]; then
            local filename
            filename=$(basename "$file")
            cp "$file" "$filename"
            log_info "Restored: $filename"
        fi
    done
    
    # Restore extension files
    if [[ -d "$backup_dir/extension" ]]; then
        rm -rf extension
        cp -r "$backup_dir/extension" .
        log_info "Restored: extension/"
    fi
    
    log_success "Configuration restored successfully"
}

create_base_env_file() {
    local env="$1"
    local env_file=".env"
    
    log_config "Creating base environment file: $env_file"
    
    cat > "$env_file" << EOF
# GenAI Smart Contract Pro - Environment Configuration
# Generated on: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Environment: $env

# Application Configuration
ENVIRONMENT=$env
DEBUG=$([ "$env" == "development" ] && echo "true" || echo "false")
LOG_LEVEL=$([ "$env" == "development" ] && echo "DEBUG" || echo "INFO")
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-me-in-production")

# Server Configuration
PORT=5000
HOST=0.0.0.0
WORKERS=$([ "$env" == "production" ] && echo "4" || echo "1")
TIMEOUT=300

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=
GOOGLE_APPLICATION_CREDENTIALS=
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro
VERTEX_AI_TEMPERATURE=0.1

# API Configuration
MAX_TEXT_LENGTH=8000
CONFIDENCE_THRESHOLD=35
API_TIMEOUT=30
RATE_LIMIT_PER_MINUTE=60

# Database Configuration (if needed)
DATABASE_URL=
REDIS_URL=

# Monitoring and Logging
ENABLE_METRICS=$([ "$env" == "production" ] && echo "true" || echo "false")
ENABLE_TRACING=$([ "$env" == "production" ] && echo "true" || echo "false")
LOG_FORMAT=$([ "$env" == "development" ] && echo "text" || echo "json")

# Security Configuration
CORS_ORIGINS=$([ "$env" == "development" ] && echo "*" || echo "")
ALLOWED_HOSTS=
CSRF_PROTECTION=$([ "$env" == "production" ] && echo "true" || echo "false")

# Feature Flags
ENABLE_RAG=true
ENABLE_SUMMARIZATION=true
ENABLE_CONSTITUTIONAL_ANALYSIS=true
ENABLE_CACHING=true

# Extension Configuration
EXTENSION_UPDATE_URL=
EXTENSION_VERSION=1.0.0

# Notification Configuration
SLACK_WEBHOOK=
TEAMS_WEBHOOK=
EMAIL_NOTIFICATIONS=false

# Backup and Recovery
BACKUP_ENABLED=false
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30
EOF
    
    log_success "Base environment file created"
}

create_environment_specific_file() {
    local env="$1"
    local env_file=".env.$env"
    
    log_config "Creating environment-specific file: $env_file"
    
    case "$env" in
        "development")
            cat > "$env_file" << EOF
# Development Environment Overrides

# Development Server
DEBUG=true
LOG_LEVEL=DEBUG
FLASK_ENV=development
FLASK_DEBUG=1

# Development URLs
API_BASE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:8080

# Development Features
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_PROFILING=true

# Development Security (relaxed)
CORS_ORIGINS=*
CSRF_PROTECTION=false
ALLOWED_HOSTS=localhost,127.0.0.1

# Development Database
DATABASE_URL=sqlite:///dev.db
REDIS_URL=redis://localhost:6379/0

# Development Monitoring
ENABLE_METRICS=false
ENABLE_TRACING=false
LOG_FORMAT=text

# Development API Limits (relaxed)
RATE_LIMIT_PER_MINUTE=1000
API_TIMEOUT=60
EOF
            ;;
        "staging")
            cat > "$env_file" << EOF
# Staging Environment Overrides

# Staging Server
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=staging

# Staging URLs
API_BASE_URL=https://staging-api.example.com
FRONTEND_URL=https://staging.example.com

# Staging Features
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_TOOLBAR=false
ENABLE_PROFILING=false

# Staging Security
CORS_ORIGINS=https://staging.example.com
CSRF_PROTECTION=true
ALLOWED_HOSTS=staging-api.example.com,staging.example.com

# Staging Database
DATABASE_URL=postgresql://user:pass@staging-db:5432/genai_contract_pro
REDIS_URL=redis://staging-redis:6379/0

# Staging Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
LOG_FORMAT=json

# Staging API Limits
RATE_LIMIT_PER_MINUTE=100
API_TIMEOUT=45
EOF
            ;;
        "production")
            cat > "$env_file" << EOF
# Production Environment Overrides

# Production Server
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production
WORKERS=4

# Production URLs
API_BASE_URL=https://api.genai-contract-pro.com
FRONTEND_URL=https://genai-contract-pro.com

# Production Features
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_TOOLBAR=false
ENABLE_PROFILING=false

# Production Security
CORS_ORIGINS=https://genai-contract-pro.com
CSRF_PROTECTION=true
ALLOWED_HOSTS=api.genai-contract-pro.com

# Production Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/genai_contract_pro
REDIS_URL=redis://prod-redis:6379/0

# Production Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
LOG_FORMAT=json
ENABLE_ALERTS=true

# Production API Limits
RATE_LIMIT_PER_MINUTE=60
API_TIMEOUT=30

# Production Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=90
EOF
            ;;
        "testing")
            cat > "$env_file" << EOF
# Testing Environment Overrides

# Testing Server
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=testing

# Testing URLs
API_BASE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:8080

# Testing Features
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_TOOLBAR=false
ENABLE_PROFILING=false

# Testing Security (relaxed for CI)
CORS_ORIGINS=*
CSRF_PROTECTION=false
ALLOWED_HOSTS=*

# Testing Database
DATABASE_URL=sqlite:///test.db
REDIS_URL=redis://localhost:6379/1

# Testing Monitoring
ENABLE_METRICS=false
ENABLE_TRACING=false
LOG_FORMAT=text

# Testing API Limits (relaxed)
RATE_LIMIT_PER_MINUTE=1000
API_TIMEOUT=10

# Testing Features
SKIP_AUTH=true
MOCK_EXTERNAL_APIS=true
FAST_TESTS=true
EOF
            ;;
    esac
    
    log_success "Environment-specific file created: $env_file"
}

setup_google_cloud_config() {
    local env="$1"
    local project_id="${2:-}"
    local region="${3:-us-central1}"
    local service_account="${4:-}"
    
    log_config "Setting up Google Cloud configuration..."
    
    # Prompt for project ID if not provided
    if [[ -z "$project_id" ]]; then
        if [[ "${INTERACTIVE:-false}" == "true" ]]; then
            read -p "Enter Google Cloud Project ID: " project_id
        else
            project_id=$(gcloud config get-value project 2>/dev/null || echo "")
        fi
    fi
    
    if [[ -z "$project_id" ]]; then
        log_warning "No Google Cloud project ID provided"
        return 0
    fi
    
    # Update environment files with Google Cloud config
    local env_files=(".env" ".env.$env")
    for file in "${env_files[@]}"; do
        if [[ -f "$file" ]]; then
            # Update or add Google Cloud configuration
            if grep -q "GOOGLE_CLOUD_PROJECT=" "$file"; then
                sed -i "s/GOOGLE_CLOUD_PROJECT=.*/GOOGLE_CLOUD_PROJECT=$project_id/" "$file"
            else
                echo "GOOGLE_CLOUD_PROJECT=$project_id" >> "$file"
            fi
            
            if grep -q "VERTEX_AI_LOCATION=" "$file"; then
                sed -i "s/VERTEX_AI_LOCATION=.*/VERTEX_AI_LOCATION=$region/" "$file"
            else
                echo "VERTEX_AI_LOCATION=$region" >> "$file"
            fi
            
            if [[ -n "$service_account" ]] && [[ -f "$service_account" ]]; then
                local abs_path
                abs_path=$(realpath "$service_account")
                if grep -q "GOOGLE_APPLICATION_CREDENTIALS=" "$file"; then
                    sed -i "s|GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$abs_path|" "$file"
                else
                    echo "GOOGLE_APPLICATION_CREDENTIALS=$abs_path" >> "$file"
                fi
            fi
        fi
    done
    
    log_success "Google Cloud configuration updated"
}

create_secrets_in_gcp() {
    local env="$1"
    local project_id="$2"
    
    if [[ -z "$project_id" ]]; then
        log_warning "No project ID provided, skipping secret creation"
        return 0
    fi
    
    log_config "Creating secrets in Google Cloud Secret Manager..."
    
    # Enable Secret Manager API
    gcloud services enable secretmanager.googleapis.com --project="$project_id" --quiet
    
    # Read environment file
    local env_file=".env.$env"
    if [[ ! -f "$env_file" ]]; then
        env_file=".env"
    fi
    
    if [[ ! -f "$env_file" ]]; then
        log_error "No environment file found"
        return 1
    fi
    
    # Create secrets for sensitive variables
    local secret_vars=("SECRET_KEY" "DATABASE_URL" "REDIS_URL" "SLACK_WEBHOOK" "TEAMS_WEBHOOK")
    
    for var in "${secret_vars[@]}"; do
        local value
        value=$(grep "^$var=" "$env_file" | cut -d'=' -f2- | tr -d '"' || echo "")
        
        if [[ -n "$value" && "$value" != "" ]]; then
            local secret_name="${var,,}-${env}"  # lowercase with environment suffix
            
            log_info "Creating secret: $secret_name"
            
            # Create secret if it doesn't exist
            if ! gcloud secrets describe "$secret_name" --project="$project_id" &>/dev/null; then
                echo -n "$value" | gcloud secrets create "$secret_name" \
                    --data-file=- \
                    --project="$project_id" \
                    --quiet
                log_success "Created secret: $secret_name"
            else
                # Update existing secret
                echo -n "$value" | gcloud secrets versions add "$secret_name" \
                    --data-file=- \
                    --project="$project_id" \
                    --quiet
                log_success "Updated secret: $secret_name"
            fi
        fi
    done
}

update_extension_config() {
    local env="$1"
    local api_url="$2"
    
    log_config "Updating Chrome extension configuration..."
    
    # Determine API URL
    if [[ -z "$api_url" ]]; then
        case "$env" in
            "development")
                api_url="http://localhost:5000"
                ;;
            "staging")
                api_url="https://staging-api.example.com"
                ;;
            "production")
                api_url="https://api.genai-contract-pro.com"
                ;;
            "testing")
                api_url="http://localhost:5000"
                ;;
        esac
    fi
    
    # Update content script
    local content_files=("enhanced_content.js" "extension/enhanced_content.js")
    for file in "${content_files[@]}"; do
        if [[ -f "$file" ]]; then
            # Create environment-specific version
            local env_file="${file%.*}_${env}.js"
            sed "s|const API_BASE_URL = '[^']*';|const API_BASE_URL = '$api_url';|g" \
                "$file" > "$env_file"
            log_success "Updated extension file: $env_file"
        fi
    done
    
    # Update popup HTML
    local popup_files=("enhanced_popup.html" "extension/enhanced_popup.html")
    for file in "${popup_files[@]}"; do
        if [[ -f "$file" ]]; then
            # Create environment-specific version
            local env_file="${file%.*}_${env}.html"
            sed "s|const API_BASE_URL = '[^']*';|const API_BASE_URL = '$api_url';|g" \
                "$file" > "$env_file"
            log_success "Updated extension file: $env_file"
        fi
    done
    
    # Update manifest for environment
    local manifest_files=("enhanced_manifest.json" "extension/enhanced_manifest.json" "manifest.json" "extension/manifest.json")
    for file in "${manifest_files[@]}"; do
        if [[ -f "$file" ]]; then
            local env_file="${file%.*}_${env}.json"
            
            # Update name and description for environment
            if command -v jq &> /dev/null; then
                jq --arg env "$env" \
                   --arg api_url "$api_url" \
                   '.name = (.name + " (" + ($env | ascii_upcase) + ")") | 
                    .description = (.description + " [" + $env + " environment]") |
                    .version = (.version + "." + $env)' \
                   "$file" > "$env_file"
            else
                cp "$file" "$env_file"
            fi
            
            log_success "Updated manifest: $env_file"
        fi
    done
}

validate_configuration() {
    local env="$1"
    
    log_info "Validating configuration for environment: $env"
    
    local errors=0
    local warnings=0
    
    # Check environment files
    local env_files=(".env" ".env.$env")
    for file in "${env_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Found: $file"
            
            # Check for required variables
            local required_vars=("ENVIRONMENT" "GOOGLE_CLOUD_PROJECT" "VERTEX_AI_LOCATION")
            for var in "${required_vars[@]}"; do
                if ! grep -q "^$var=" "$file"; then
                    log_warning "Missing variable in $file: $var"
                    ((warnings++))
                fi
            done
            
            # Check for empty critical variables
            local critical_vars=("SECRET_KEY" "GOOGLE_CLOUD_PROJECT")
            for var in "${critical_vars[@]}"; do
                local value
                value=$(grep "^$var=" "$file" | cut -d'=' -f2- | tr -d '"' || echo "")
                if [[ -z "$value" || "$value" == "change-me-in-production" ]]; then
                    if [[ "$env" == "production" ]]; then
                        log_error "Critical variable not set in $file: $var"
                        ((errors++))
                    else
                        log_warning "Variable needs attention in $file: $var"
                        ((warnings++))
                    fi
                fi
            done
        else
            log_warning "Environment file not found: $file"
            ((warnings++))
        fi
    done
    
    # Check Google Cloud authentication
    if command -v gcloud &> /dev/null; then
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
            log_success "Google Cloud authentication: OK"
        else
            log_warning "Google Cloud not authenticated"
            ((warnings++))
        fi
    else
        log_warning "gcloud CLI not installed"
        ((warnings++))
    fi
    
    # Check extension files
    local extension_files=("enhanced_content_${env}.js" "enhanced_popup_${env}.html" "enhanced_manifest_${env}.json")
    for file in "${extension_files[@]}"; do
        if [[ -f "$file" ]] || [[ -f "extension/$file" ]]; then
            log_success "Found extension file: $file"
        else
            log_warning "Extension file not found: $file"
            ((warnings++))
        fi
    done
    
    # Summary
    echo ""
    log_info "Validation Summary:"
    echo "  • Errors: $errors"
    echo "  • Warnings: $warnings"
    
    if [[ $errors -gt 0 ]]; then
        log_error "Configuration validation failed with $errors errors"
        return 1
    elif [[ $warnings -gt 0 ]]; then
        log_warning "Configuration validation completed with $warnings warnings"
        return 0
    else
        log_success "Configuration validation passed"
        return 0
    fi
}

interactive_configuration() {
    local env="$1"
    
    log_config "Starting interactive configuration for: $env"
    echo ""
    
    # Project configuration
    echo "=== Google Cloud Configuration ==="
    read -p "Google Cloud Project ID: " project_id
    read -p "Google Cloud Region [us-central1]: " region
    region=${region:-us-central1}
    
    read -p "Service Account JSON file path (optional): " service_account
    
    # API configuration
    echo ""
    echo "=== API Configuration ==="
    read -p "API Base URL (leave empty for auto-detection): " api_url
    
    # Security configuration
    echo ""
    echo "=== Security Configuration ==="
    read -p "Generate new secret key? [y/N]: " generate_secret
    
    local secret_key=""
    if [[ "$generate_secret" =~ ^[Yy]$ ]]; then
        secret_key=$(openssl rand -hex 32 2>/dev/null || echo "$(date +%s | sha256sum | head -c 64)")
        log_success "Generated new secret key"
    fi
    
    # Feature configuration
    echo ""
    echo "=== Feature Configuration ==="
    read -p "Enable RAG analysis? [Y/n]: " enable_rag
    enable_rag=${enable_rag:-Y}
    
    read -p "Enable contract summarization? [Y/n]: " enable_summarization
    enable_summarization=${enable_summarization:-Y}
    
    read -p "Enable constitutional analysis? [Y/n]: " enable_constitutional
    enable_constitutional=${enable_constitutional:-Y}
    
    # Notification configuration
    echo ""
    echo "=== Notification Configuration ==="
    read -p "Slack webhook URL (optional): " slack_webhook
    read -p "Teams webhook URL (optional): " teams_webhook
    
    # Apply configuration
    echo ""
    log_config "Applying interactive configuration..."
    
    # Update environment files
    local env_files=(".env" ".env.$env")
    for file in "${env_files[@]}"; do
        if [[ -f "$file" ]]; then
            # Update values
            [[ -n "$project_id" ]] && sed -i "s/GOOGLE_CLOUD_PROJECT=.*/GOOGLE_CLOUD_PROJECT=$project_id/" "$file"
            [[ -n "$region" ]] && sed -i "s/VERTEX_AI_LOCATION=.*/VERTEX_AI_LOCATION=$region/" "$file"
            [[ -n "$secret_key" ]] && sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" "$file"
            [[ -n "$slack_webhook" ]] && sed -i "s|SLACK_WEBHOOK=.*|SLACK_WEBHOOK=$slack_webhook|" "$file"
            [[ -n "$teams_webhook" ]] && sed -i "s|TEAMS_WEBHOOK=.*|TEAMS_WEBHOOK=$teams_webhook|" "$file"
            
            # Update feature flags
            sed -i "s/ENABLE_RAG=.*/ENABLE_RAG=$([ "$enable_rag" = "Y" ] || [ "$enable_rag" = "y" ] && echo "true" || echo "false")/" "$file"
            sed -i "s/ENABLE_SUMMARIZATION=.*/ENABLE_SUMMARIZATION=$([ "$enable_summarization" = "Y" ] || [ "$enable_summarization" = "y" ] && echo "true" || echo "false")/" "$file"
            sed -i "s/ENABLE_CONSTITUTIONAL_ANALYSIS=.*/ENABLE_CONSTITUTIONAL_ANALYSIS=$([ "$enable_constitutional" = "Y" ] || [ "$enable_constitutional" = "y" ] && echo "true" || echo "false")/" "$file"
        fi
    done
    
    log_success "Interactive configuration completed"
}

show_configuration_summary() {
    local env="$1"
    
    echo ""
    echo "=========================================="
    echo "🔧 CONFIGURATION SUMMARY"
    echo "=========================================="
    echo ""
    echo "Environment: $env"
    echo "Project Root: $PROJECT_ROOT"
    echo ""
    
    # Show environment files
    echo "Configuration Files:"
    for file in .env .env.*; do
        if [[ -f "$file" ]]; then
            echo "  ✅ $file"
        fi
    done
    echo ""
    
    # Show key configuration values
    local env_file=".env.$env"
    if [[ ! -f "$env_file" ]]; then
        env_file=".env"
    fi
    
    if [[ -f "$env_file" ]]; then
        echo "Key Configuration:"
        local display_vars=("ENVIRONMENT" "GOOGLE_CLOUD_PROJECT" "VERTEX_AI_LOCATION" "DEBUG" "LOG_LEVEL")
        for var in "${display_vars[@]}"; do
            local value
            value=$(grep "^$var=" "$env_file" | cut -d'=' -f2- | tr -d '"' || echo "Not set")
            echo "  • $var: $value"
        done
    fi
    
    echo ""
    echo "Extension Files:"
    for file in enhanced_*_${env}.*; do
        if [[ -f "$file" ]]; then
            echo "  ✅ $file"
        fi
    done
    
    echo ""
    echo "Next Steps:"
    echo "  1. Review configuration files"
    echo "  2. Test with: ./deploy_local.sh start --environment $env"
    echo "  3. Deploy with: ./deploy_cloud.sh --environment $env"
    echo ""
}

main() {
    local environment="${1:-}"
    shift || true
    
    # Parse arguments
    local project_id=""
    local region="us-central1"
    local service_account=""
    local create_secrets=false
    local update_extension=false
    local interactive=false
    local validate_only=false
    local backup_config=false
    local restore_file=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project-id)
                project_id="$2"
                shift 2
                ;;
            --region)
                region="$2"
                shift 2
                ;;
            --service-account)
                service_account="$2"
                shift 2
                ;;
            --create-secrets)
                create_secrets=true
                shift
                ;;
            --update-extension)
                update_extension=true
                shift
                ;;
            --interactive)
                interactive=true
                shift
                ;;
            --validate)
                validate_only=true
                shift
                ;;
            --backup)
                backup_config=true
                shift
                ;;
            --restore)
                restore_file="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Auto-detect environment if not provided
    if [[ -z "$environment" ]]; then
        environment=$(detect_environment)
        log_info "Auto-detected environment: $environment"
    fi
    
    # Validate environment
    validate_environment "$environment"
    
    echo "🔧 GenAI Smart Contract Pro - Environment Configuration"
    echo "======================================================"
    echo ""
    echo "Environment: $environment"
    echo "Project Root: $PROJECT_ROOT"
    echo ""
    
    # Handle special operations
    if [[ -n "$restore_file" ]]; then
        restore_configuration "$restore_file"
        exit 0
    fi
    
    if [[ "$backup_config" == "true" ]]; then
        backup_configuration
        exit 0
    fi
    
    if [[ "$validate_only" == "true" ]]; then
        validate_configuration "$environment"
        exit $?
    fi
    
    # Main configuration flow
    log_info "Starting configuration for environment: $environment"
    
    # Backup existing configuration
    if [[ -f ".env" ]] || [[ -f ".env.$environment" ]]; then
        log_info "Backing up existing configuration..."
        backup_configuration > /dev/null
    fi
    
    # Create configuration files
    create_base_env_file "$environment"
    create_environment_specific_file "$environment"
    
    # Setup Google Cloud configuration
    setup_google_cloud_config "$environment" "$project_id" "$region" "$service_account"
    
    # Interactive configuration
    if [[ "$interactive" == "true" ]]; then
        interactive_configuration "$environment"
    fi
    
    # Create secrets in Google Cloud
    if [[ "$create_secrets" == "true" ]] && [[ -n "$project_id" ]]; then
        create_secrets_in_gcp "$environment" "$project_id"
    fi
    
    # Update extension configuration
    if [[ "$update_extension" == "true" ]]; then
        update_extension_config "$environment"
    fi
    
    # Validate final configuration
    validate_configuration "$environment"
    
    # Show summary
    show_configuration_summary "$environment"
    
    log_success "Environment configuration completed successfully!"
}

# Run main function
main "$@"
