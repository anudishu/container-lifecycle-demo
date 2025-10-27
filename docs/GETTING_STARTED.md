# Getting Started with Container Lifecycle Management

This guide will walk you through setting up and deploying the container lifecycle management POC project.

## 📋 Prerequisites

Before you begin, ensure you have the following tools installed and configured:

### Required Tools

- **Docker Desktop** (v4.0+)
- **Google Cloud SDK** (gcloud CLI)
- **kubectl** (Kubernetes CLI)
- **Git**
- **Node.js** (v18+)
- **Python** (v3.8+)

### Optional Tools (for advanced features)

- **Trivy** (vulnerability scanner)
- **Cosign** (image signing)
- **Syft** (SBOM generation)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/container-lifecycle-demo.git
cd container-lifecycle-demo
```

### 2. Set Up Google Cloud

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable compute.googleapis.com
```

### 3. Create GKE Cluster

```bash
# Create GKE cluster
gcloud container clusters create container-lifecycle-cluster \
    --zone us-central1-a \
    --num-nodes 3 \
    --enable-autoscaling \
    --min-nodes 1 \
    --max-nodes 5 \
    --enable-autorepair \
    --enable-autoupgrade \
    --machine-type n1-standard-2 \
    --disk-size 50GB

# Get cluster credentials
gcloud container clusters get-credentials container-lifecycle-cluster --zone us-central1-a
```

### 4. Local Development Setup

```bash
# Navigate to application directory
cd app

# Install dependencies
npm install

# Run tests
npm test

# Start development server
npm run dev
```

### 5. Build and Test Locally

```bash
# Build Docker image
docker build -f docker/Dockerfile -t container-lifecycle-demo:local .

# Run locally with Docker Compose
cd docker
docker-compose up --build

# Test the application
curl http://localhost:3000/health
```

### 6. Deploy to Google Cloud

Update the GitHub repository secrets with your GCP credentials:

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account JSON key with appropriate permissions

Push your code to trigger the CI/CD pipeline:

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for local development:

```bash
# Application
NODE_ENV=development
PORT=3000

# Google Cloud
PROJECT_ID=your-gcp-project-id
CLUSTER_NAME=container-lifecycle-cluster
CLUSTER_ZONE=us-central1-a

# Security
SECURITY_SCAN_ENABLED=true
VULNERABILITY_THRESHOLD=high
```

### GitHub Secrets

Required secrets for CI/CD pipeline:

| Secret Name | Description |
|-------------|-------------|
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `GCP_SA_KEY` | Service Account JSON key |
| `REGISTRY_URL` | Container registry URL (optional) |

### Service Account Permissions

Your GCP service account needs the following roles:

- `roles/container.admin` - For GKE management
- `roles/storage.admin` - For Container Registry
- `roles/compute.admin` - For compute resources
- `roles/iam.serviceAccountUser` - For service account usage

## 🛡️ Security Setup

### 1. Install Security Tools

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install Cosign
go install github.com/sigstore/cosign/cmd/cosign@latest

# Install OPA
curl -L -o opa https://openpolicyagent.org/downloads/v0.57.0/opa_linux_amd64_static
chmod 755 ./opa
sudo mv opa /usr/local/bin
```

### 2. Configure Security Policies

```bash
# Validate security configurations
echo "Security enforced through Kubernetes native security contexts"

# Test container structure
container-structure-test test --image container-lifecycle-demo:local --config security/container-structure-test.yaml
```

## 📊 Monitoring Setup

### 1. Deploy Monitoring Stack

```bash
# Deploy Prometheus and Grafana
kubectl apply -f k8s/monitoring/

# Port-forward to access dashboards
kubectl port-forward svc/prometheus 9090:9090 &
kubectl port-forward svc/grafana 3001:3000 &
```

### 2. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Application**: Use the LoadBalancer IP or port-forward

## 🧪 Testing

### Unit Tests

```bash
cd app
npm test
npm run test:coverage
```

### Integration Tests

```bash
# Test deployed application
python3 scripts/deployment-test.py --url http://your-app-url

# Run compliance checks
python3 scripts/compliance-check.py --image gcr.io/PROJECT_ID/container-lifecycle-demo:latest
```

### Security Tests

```bash
# Vulnerability scan
trivy image gcr.io/PROJECT_ID/container-lifecycle-demo:latest

# Security validation
trivy image container-lifecycle-demo:local
```

## 🚨 Troubleshooting

### Common Issues

#### 1. GKE Cluster Creation Fails

```bash
# Check quotas
gcloud compute project-info describe --project=$PROJECT_ID

# Verify permissions
gcloud auth list
gcloud config list
```

#### 2. Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a

# Check Dockerfile syntax
docker build --no-cache -f docker/Dockerfile .
```

#### 3. Application Won't Start

```bash
# Check logs
kubectl logs -l app=container-lifecycle-demo -n container-lifecycle-demo

# Check pod status
kubectl get pods -n container-lifecycle-demo
kubectl describe pod <pod-name> -n container-lifecycle-demo
```

#### 4. Security Scan Failures

```bash
# Update Trivy database
trivy image --download-db-only

# Check image exists
docker images | grep container-lifecycle-demo
```

### Getting Help

1. Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Review application logs
3. Validate configuration files
4. Check GitHub Actions workflow logs
5. Verify GCP permissions and quotas

## 📚 Next Steps

1. **Customize Security Policies**: Modify `security/policies/` to match your requirements
2. **Set Up Monitoring**: Configure alerts and dashboards in Grafana
3. **Implement Lifecycle Policies**: Customize image cleanup and retention policies
4. **Scale the Application**: Adjust replica counts and resource limits
5. **Add Custom Metrics**: Extend monitoring with application-specific metrics

## 🔗 Useful Links

- [Container Security Best Practices](docs/SECURITY.md)
- [Kubernetes Deployment Guide](docs/KUBERNETES.md)
- [CI/CD Pipeline Documentation](docs/CICD.md)
- [Monitoring and Alerting](docs/MONITORING.md)
- [Compliance and Governance](docs/COMPLIANCE.md)

---

**Need help?** Check our [FAQ](docs/FAQ.md) or open an issue on GitHub.
