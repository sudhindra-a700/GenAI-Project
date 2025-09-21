#!/bin/bash

# GenAI Smart Contract Pro - Setup Script
# Organizes repository structure and prepares for development

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

create_directory_structure() {
    log_info "Creating directory structure..."
    
    # Create main directories
    mkdir -p backend
    mkdir -p extension
    mkdir -p docs
    mkdir -p scripts
    mkdir -p tests
    mkdir -p .github/workflows
    mkdir -p terraform
    mkdir -p k8s
    
    log_success "Directory structure created"
}

organize_backend_files() {
    log_info "Organizing backend files..."
    
    # Move backend files
    [ -f "main_workflow.py" ] && mv main_workflow.py backend/ || log_warning "main_workflow.py not found"
    [ -f "main_workflow_production.py" ] && mv main_workflow_production.py backend/ || log_warning "main_workflow_production.py not found"
    [ -f "contract_summarizer.py" ] && mv contract_summarizer.py backend/ || log_warning "contract_summarizer.py not found"
    [ -f "rag_retriever.py" ] && mv rag_retriever.py backend/ || log_warning "rag_retriever.py not found"
    
    # Copy requirements files
    [ -f "requirements.txt" ] && cp requirements.txt backend/ || log_warning "requirements.txt not found"
    [ -f "requirements_production.txt" ] && cp requirements_production.txt backend/ || log_warning "requirements_production.txt not found"
    
    # Copy Docker files
    [ -f "Dockerfile" ] && cp Dockerfile backend/ || log_warning "Dockerfile not found"
    [ -f ".dockerignore" ] && cp .dockerignore backend/ || log_warning ".dockerignore not found"
    
    log_success "Backend files organized"
}

organize_extension_files() {
    log_info "Organizing extension files..."
    
    # Move extension files
    [ -f "browser.html" ] && mv browser.html extension/ || log_warning "browser.html not found"
    [ -f "enhanced_popup.html" ] && mv enhanced_popup.html extension/ || log_warning "enhanced_popup.html not found"
    [ -f "content.js" ] && mv content.js extension/ || log_warning "content.js not found"
    [ -f "enhanced_content.js" ] && mv enhanced_content.js extension/ || log_warning "enhanced_content.js not found"
    [ -f "manifest.json" ] && mv manifest.json extension/ || log_warning "manifest.json not found"
    [ -f "enhanced_manifest.json" ] && mv enhanced_manifest.json extension/ || log_warning "enhanced_manifest.json not found"
    [ -f "background.js" ] && mv background.js extension/ || log_warning "background.js not found"
    [ -f "enhanced_background.js" ] && mv enhanced_background.js extension/ || log_warning "enhanced_background.js not found"
    
    log_success "Extension files organized"
}

organize_deployment_files() {
    log_info "Organizing deployment files..."
    
    # Move scripts
    [ -f "deploy.sh" ] && mv deploy.sh scripts/ || log_warning "deploy.sh not found"
    [ -f "deploy_cloud.sh" ] && mv deploy_cloud.sh scripts/ || log_warning "deploy_cloud.sh not found"
    [ -f "test.sh" ] && mv test.sh scripts/ || log_warning "test.sh not found"
    
    # Move CI/CD files
    [ -f "cloudbuild.yaml" ] && cp cloudbuild.yaml . || log_warning "cloudbuild.yaml not found"
    [ -f "docker-compose.yml" ] && cp docker-compose.yml . || log_warning "docker-compose.yml not found"
    
    # Move Kubernetes files
    [ -f "k8s-deployment.yaml" ] && mv k8s-deployment.yaml k8s/ || log_warning "k8s-deployment.yaml not found"
    
    # Move Terraform files
    [ -f "terraform/main.tf" ] && log_info "Terraform files already in place" || log_warning "Terraform files not found"
    
    log_success "Deployment files organized"
}

create_configuration_files() {
    log_info "Creating configuration files..."
    
    # Create .env.example
    cat > .env.example << 'EOF'
# GenAI Smart Contract Pro - Environment Variables

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_LOCATION=us-central1

# Application Configuration
ENVIRONMENT=development
DEBUG=True
PORT=5000
SECRET_KEY=your-secret-key-here

# API Configuration
MAX_TEXT_LENGTH=8000
CONFIDENCE_THRESHOLD=35
API_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Optional: Redis Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
EOF

    # Create .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
.venv/

# Environment Variables
.env
.env.local
.env.production

# Google Cloud
service-account*.json
credentials.json
key.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
.tmp/

# Docker
.dockerignore

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Node modules (if any)
node_modules/

# Coverage reports
htmlcov/
.coverage
.pytest_cache/

# Backup files
*_backup_*
*.bak
EOF

    # Create .gcloudignore
    cat > .gcloudignore << 'EOF'
# Git
.git/
.gitignore

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Development
.env
.env.local
*.log
logs/
tmp/
temp/

# Documentation
docs/
*.md
README*

# Tests
tests/
test_*
*_test.py

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Backup files
*_backup_*
*.bak

# Terraform
terraform/
*.tfstate*
.terraform/

# Kubernetes
k8s/

# Scripts (except production ones)
scripts/test*
scripts/dev*
EOF

    log_success "Configuration files created"
}

create_documentation() {
    log_info "Creating documentation..."
    
    # Create README.md
    cat > README.md << 'EOF'
# GenAI Smart Contract Pro

An intelligent Chrome extension for contract analysis using Google Cloud Vertex AI, featuring constitutional compliance checking, contract summarization, and legal verification.

## 🎯 Features

- **Automatic Contract Detection**: Intelligently detects contract content on web pages
- **Constitutional Analysis**: RAG-based matching with Indian Constitution
- **Contract Summarization**: AI-powered key terms extraction
- **Legal Verification**: IndianLegalBERT-based compliance checking
- **Professional UI**: Grammarly-inspired user experience with Lucide icons

## 🏗️ Architecture

### Backend Components
- **RAG Retriever**: Constitutional analysis using Vertex AI Matching Engine
- **Contract Summarizer**: Gemini-powered contract analysis
- **Main Workflow**: Flask API orchestrating all components

### Frontend Components
- **Chrome Extension**: Professional popup interface
- **Content Script**: Intelligent page content detection
- **Background Service**: Extension lifecycle management

## 🚀 Quick Start

### Local Development
```bash
# Setup repository
./scripts/setup.sh

# Install dependencies
cd backend
pip install -r requirements.txt

# Start backend
python main_workflow.py

# Load extension in Chrome
# 1. Go to chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select the extension/ directory
```

### Cloud Deployment
```bash
# Deploy to Google Cloud Run
./scripts/deploy_cloud.sh

# Update extension with production URL
# Replace files as instructed in deployment output
```

## 📁 Project Structure

```
GenAI-Smart-Contract-Pro/
├── backend/                 # Flask API backend
│   ├── main_workflow.py     # Main application
│   ├── contract_summarizer.py
│   ├── rag_retriever.py
│   └── requirements.txt
├── extension/               # Chrome extension
│   ├── enhanced_popup.html
│   ├── enhanced_content.js
│   ├── enhanced_manifest.json
│   └── enhanced_background.js
├── scripts/                 # Deployment scripts
├── docs/                    # Documentation
├── tests/                   # Test suite
└── terraform/               # Infrastructure as code
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_LOCATION=us-central1
```

## 🧪 Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Run extension tests
cd extension
# Load in Chrome Developer mode for testing
```

## 📊 Monitoring

- **Cloud Console**: Monitor Cloud Run service
- **Logs**: `gcloud logs tail --follow`
- **Metrics**: Built-in Cloud Run monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue in this repository
- Check the documentation in the `docs/` directory
- Review deployment logs for troubleshooting
EOF

    # Create docs/DEPLOYMENT.md
    mkdir -p docs
    cat > docs/DEPLOYMENT.md << 'EOF'
# Deployment Guide

## Prerequisites

1. Google Cloud Project with billing enabled
2. gcloud CLI installed and authenticated
3. Docker installed
4. Required APIs enabled (handled by deployment script)

## Local Development

1. **Setup Environment**:
   ```bash
   ./scripts/setup.sh
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start Backend**:
   ```bash
   python main_workflow.py
   ```

4. **Load Extension**:
   - Open Chrome
   - Go to chrome://extensions/
   - Enable Developer mode
   - Click "Load unpacked"
   - Select the extension/ directory

## Cloud Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# Deploy to Cloud Run
./scripts/deploy_cloud.sh
```

### Option 2: Manual Deployment

1. **Build and Push Image**:
   ```bash
   docker build -t gcr.io/$PROJECT_ID/genai-contract-pro .
   docker push gcr.io/$PROJECT_ID/genai-contract-pro
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy genai-contract-pro \
     --image gcr.io/$PROJECT_ID/genai-contract-pro \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Option 3: CI/CD with GitHub Actions

1. **Setup Secrets** in GitHub repository:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account JSON key

2. **Push to main branch** - automatic deployment will trigger

## Post-Deployment

1. **Update Extension**: Replace local files with production versions
2. **Test Functionality**: Verify all components work correctly
3. **Monitor Service**: Check Cloud Console for metrics and logs

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure service account has proper permissions
2. **API Quota Errors**: Check Vertex AI quotas in Cloud Console
3. **Extension Not Loading**: Verify manifest.json syntax
4. **Backend Errors**: Check Cloud Run logs

### Useful Commands

```bash
# View logs
gcloud logs tail --follow

# Check service status
gcloud run services describe genai-contract-pro --region=us-central1

# Test endpoints
curl https://your-service-url/health
```
EOF

    log_success "Documentation created"
}

setup_git() {
    log_info "Setting up Git configuration..."
    
    # Initialize git if not already done
    if [ ! -d ".git" ]; then
        git init
        log_info "Git repository initialized"
    fi
    
    # Add all files
    git add .
    
    log_success "Git setup completed"
}

make_scripts_executable() {
    log_info "Making scripts executable..."
    
    chmod +x scripts/*.sh 2>/dev/null || log_warning "No shell scripts found in scripts/"
    
    log_success "Scripts made executable"
}

show_summary() {
    echo ""
    echo "=========================================="
    echo "🎉 SETUP COMPLETED SUCCESSFULLY! 🎉"
    echo "=========================================="
    echo ""
    echo "📁 Repository Structure:"
    echo "  ├── backend/          # Flask API backend"
    echo "  ├── extension/        # Chrome extension"
    echo "  ├── scripts/          # Deployment scripts"
    echo "  ├── docs/             # Documentation"
    echo "  ├── tests/            # Test suite"
    echo "  └── terraform/        # Infrastructure as code"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Configure environment: cp .env.example .env"
    echo "  2. Install dependencies: cd backend && pip install -r requirements.txt"
    echo "  3. Start development: python backend/main_workflow.py"
    echo "  4. Load extension in Chrome"
    echo ""
    echo "🚀 Deployment Options:"
    echo "  • Local: Follow docs/DEPLOYMENT.md"
    echo "  • Cloud: ./scripts/deploy_cloud.sh"
    echo "  • CI/CD: Push to main branch"
    echo ""
    echo "📚 Documentation:"
    echo "  • README.md - Project overview"
    echo "  • docs/DEPLOYMENT.md - Deployment guide"
    echo "  • .env.example - Configuration template"
    echo ""
    echo "✅ Your GenAI Smart Contract Pro repository is ready!"
}

main() {
    echo "🛠️  GenAI Smart Contract Pro - Setup Script"
    echo "==========================================="
    echo ""
    
    create_directory_structure
    organize_backend_files
    organize_extension_files
    organize_deployment_files
    create_configuration_files
    create_documentation
    setup_git
    make_scripts_executable
    show_summary
}

# Run main function
main "$@"
