#!/bin/bash

# Quick Start Script for Container Lifecycle Management
# Project: probable-cove-474504-p0

set -e

echo "🚀 Container Lifecycle Management - Quick Start"
echo "Project ID: probable-cove-474504-p0"
echo ""

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with Google Cloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set project
echo "📋 Setting up Google Cloud project..."
gcloud config set project probable-cove-474504-p0

# Run the full setup
echo "🔄 Running automated setup script..."
./scripts/setup.sh --project-id probable-cove-474504-p0

echo ""
echo "✅ Setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Configure GitHub repository secrets:"
echo "   - GCP_PROJECT_ID: probable-cove-474504-p0"
echo "   - GCP_SA_KEY: (content of container-lifecycle-key.json)"
echo ""
echo "2. Push your code to trigger the CI/CD pipeline"
echo "3. Monitor deployment:"
echo "   kubectl get pods -n container-lifecycle-demo"
echo ""
echo "🔗 Useful commands:"
echo "   # Check cluster status"
echo "   kubectl get nodes"
echo ""
echo "   # Get application URL"  
echo "   kubectl get svc -n container-lifecycle-demo container-lifecycle-demo-lb"
echo ""
echo "   # View logs"
echo "   kubectl logs -l app=container-lifecycle-demo -n container-lifecycle-demo"
echo ""
echo "🎉 Happy container lifecycle management!"
