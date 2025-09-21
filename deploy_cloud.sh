#!/bin/bash

# GenAI Smart Contract Pro - Cloud Deployment Script
# Automated deployment to Google Cloud Run with comprehensive setup

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-genai-project-472704}"
REGION="${REGION:-europe-west4}"
SERVICE_NAME="genai-contract-pro"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Run 'gcloud auth login' first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_project() {
    log_info "Setting up Google Cloud project..."
    
    # Get or set project ID
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
        if [ -z "$PROJECT_ID" ]; then
            log_error "No project ID set. Please set GOOGLE_CLOUD_PROJECT environment variable or run 'gcloud config set project PROJECT_ID'"
            exit 1
        fi
    fi
    
    log_info "Using project: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        containerregistry.googleapis.com \
        aiplatform.googleapis.com \
        secretmanager.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com
    
    log_success "Project setup completed"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build the image
    log_info "Building Docker image..."
    docker build -t "$IMAGE_NAME:latest" .
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Push the image
    log_info "Pushing image to Google Container Registry..."
    docker push "$IMAGE_NAME:latest"
    
    log_success "Image built and pushed successfully"
}

deploy_to_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    # Deploy the service
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 1 \
        --max-instances 10 \
        --min-instances 0 \
        --timeout 300 \
        --set-env-vars "ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=$REGION" \
        --quiet
    
    log_success "Deployment completed"
}

test_deployment() {
    log_info "Testing deployment..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)")
    
    if [ -z "$SERVICE_URL" ]; then
        log_error "Failed to get service URL"
        exit 1
    fi
    
    log_info "Service URL: $SERVICE_URL"
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -f "$SERVICE_URL/health" --max-time 30 --silent; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Test analyze endpoint
    log_info "Testing analyze endpoint..."
    response=$(curl -s -X POST "$SERVICE_URL/analyze" \
        -H "Content-Type: application/json" \
        -d '{"text":"TEST AGREEMENT: This is a test contract with payment terms and governing law provisions."}' \
        --max-time 30)
    
    if echo "$response" | grep -q "summary"; then
        log_success "API endpoint test passed"
    else
        log_warning "API endpoint test returned unexpected response"
        echo "Response: $response"
    fi
    
    return 0
}

update_extension_files() {
    log_info "Updating Chrome extension files..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format="value(status.url)")
    
    # Create production versions of extension files
    if [ -f "enhanced_content.js" ]; then
        sed "s|const API_BASE_URL = 'http://localhost:5000';|const API_BASE_URL = '$SERVICE_URL';|g" \
            enhanced_content.js > enhanced_content_production.js
        log_success "Created enhanced_content_production.js"
    fi
    
    if [ -f "enhanced_popup.html" ]; then
        sed "s|const API_BASE_URL = 'http://localhost:5000';|const API_BASE_URL = '$SERVICE_URL';|g" \
            enhanced_popup.html > enhanced_popup_production.html
        log_success "Created enhanced_popup_production.html"
    fi
    
    # Create deployment info file
    cat > deployment-info.txt << EOF
GenAI Smart Contract Pro - Deployment Information
================================================

Service URL: $SERVICE_URL
Project ID: $PROJECT_ID
Region: $REGION
Deployed: $(date)

Chrome Extension Update Instructions:
1. Replace 'content.js' with 'enhanced_content_production.js'
2. Replace 'browser.html' with 'enhanced_popup_production.html'
3. Reload the extension in Chrome

Monitoring:
- Cloud Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID
- Logs: gcloud logs tail --follow --project=$PROJECT_ID

Testing:
- Health: curl $SERVICE_URL/health
- API: curl -X POST $SERVICE_URL/analyze -H "Content-Type: application/json" -d '{"text":"test contract"}'
EOF
    
    log_success "Extension files updated and deployment info created"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    # Add any cleanup tasks here
    log_success "Cleanup completed"
}

show_summary() {
    echo ""
    echo "=========================================="
    echo "🚀 DEPLOYMENT COMPLETED SUCCESSFULLY! 🚀"
    echo "=========================================="
    echo ""
    echo "📋 Deployment Summary:"
    echo "  • Project ID: $PROJECT_ID"
    echo "  • Service Name: $SERVICE_NAME"
    echo "  • Region: $REGION"
    echo "  • Service URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "N/A")"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Update your Chrome extension with the production files"
    echo "  2. Test the extension on contract websites"
    echo "  3. Monitor the service in Google Cloud Console"
    echo ""
    echo "📊 Monitoring & Logs:"
    echo "  • Cloud Console: https://console.cloud.google.com/run"
    echo "  • View logs: gcloud logs tail --follow --project=$PROJECT_ID"
    echo ""
    echo "✅ Your GenAI Smart Contract Pro extension is now live!"
}

main() {
    echo "🚀 GenAI Smart Contract Pro - Cloud Deployment Script"
    echo "===================================================="
    echo ""
    
    # Check if help is requested
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --skip-build   Skip Docker build step"
        echo "  --skip-test    Skip deployment testing"
        echo ""
        echo "Environment Variables:"
        echo "  GOOGLE_CLOUD_PROJECT  Google Cloud Project ID"
        echo "  REGION               Deployment region (default: us-central1)"
        echo ""
        exit 0
    fi
    
    # Main deployment flow
    check_prerequisites
    setup_project
    
    if [[ "${1:-}" != "--skip-build" ]]; then
        build_and_push_image
    else
        log_info "Skipping Docker build step"
    fi
    
    deploy_to_cloud_run
    
    if [[ "${1:-}" != "--skip-test" ]]; then
        test_deployment
    else
        log_info "Skipping deployment testing"
    fi
    
    update_extension_files
    cleanup
    show_summary
}

# Trap errors and cleanup
trap 'log_error "Deployment failed! Check the logs above for details."; cleanup; exit 1' ERR

# Run main function with all arguments
main "$@"
