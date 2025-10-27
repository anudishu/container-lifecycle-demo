# Container Lifecycle Management POC

A comprehensive demonstration of enterprise-grade container image lifecycle management using GitHub Actions, Docker, Kubernetes, and Google Cloud Platform.

## 🎯 Project Overview

This project demonstrates complete container lifecycle management with enterprise security, governance, and compliance practices:

- ✅ **Secure baseline image creation** with multi-stage Docker builds
- ✅ **Automated CI/CD pipeline** with GitHub Actions
- ✅ **Container security scanning** and vulnerability management  
- ✅ **Policy enforcement** and compliance validation
- ✅ **Complete lifecycle management** from development to retirement
- ✅ **Google Cloud deployment** using GKE (Google Kubernetes Engine)
- ✅ **Monitoring and observability** with Prometheus integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Developer     │───▶│  GitHub Actions  │───▶│  Google Cloud   │
│   Commits Code  │    │  CI/CD Pipeline  │    │      GKE        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Container Registry│    │   Monitoring    │
                       │ Security Scanning │    │ & Compliance    │
                       └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure & File Descriptions

### 🚀 **Application Layer**
```
app/
├── package.json          # Node.js dependencies and scripts
├── server.js            # Express.js application with security features
└── tests/
    └── server.test.js   # Comprehensive test suite (7 test cases)
```

### 🐳 **Container Layer**
```
docker/
├── Dockerfile           # Multi-stage build with security scanning
├── .dockerignore       # Optimized build context
└── docker-compose.yml  # Local development environment
```

### ⚙️ **CI/CD Pipeline**
```
.github/workflows/
└── container-lifecycle.yml  # Complete GitHub Actions pipeline
    ├── Code Analysis        # Security audit & dependency checks
    ├── Container Build      # Multi-stage Docker build
    ├── Security Scan        # Trivy vulnerability assessment
    ├── Compliance Check     # Custom security validation
    └── GKE Deployment      # Automated deployment to Google Cloud
```

### ☸️ **Kubernetes Infrastructure**
```
k8s/
├── namespace.yaml       # Resource quotas and limits
├── deployment.yaml      # Secure pod deployment (3 replicas)
├── service.yaml         # Load balancer and ingress configuration
└── rbac.yaml           # Security policies and network rules
```

### 🛡️ **Security & Governance**
```
security/
└── container-structure-test.yaml  # Container security validation
```

### 📊 **Monitoring & Observability**
```
monitoring/
└── prometheus.yml       # Metrics collection configuration
```

### 🔧 **Automation Scripts**
```
scripts/
├── setup.sh                    # Automated GCP infrastructure setup
├── compliance-check.py         # Security compliance validation
├── deployment-test.py          # Application testing suite
└── generate-compliance-report.py  # Comprehensive reporting
```

### 📖 **Documentation**
```
docs/
├── GETTING_STARTED.md         # Step-by-step setup guide
└── CONTAINER_LIFECYCLE.md     # Complete lifecycle documentation
```

### 🔐 **Security Files**
```
.gitignore                     # Comprehensive credential protection
github-actions-key.json       # Service account key (PROTECTED)
```

## 🚀 **Complete Deployment Guide**

### 📋 **Prerequisites**

**Required Tools:**
- **Docker Desktop** (v4.0+)
- **Google Cloud SDK** (`gcloud` CLI)
- **kubectl** (Kubernetes CLI) 
- **Node.js** (v18+)
- **Git**
- **GitHub account**
- **Google Cloud Project** with billing enabled

**Install Tools:**
```bash
# macOS (using Homebrew)
brew install --cask docker
brew install --cask google-cloud-sdk
brew install kubectl node git

# Verify installations
docker --version
gcloud --version
kubectl version --client
node --version
```

### 🔧 **Step 1: Local Development & Testing**

**1.1 Clone and Setup:**
```bash
# Clone repository
git clone https://github.com/anudishu/container-lifecycle-demo.git
cd container-lifecycle-demo

# Install dependencies
cd app && npm install

# Run tests
npm test
# ✅ Expected: 7 tests passed

# Start application locally
npm start
# ✅ Expected: Server running on port 3000
```

**1.2 Test Local Application:**
```bash
# Test health endpoint
curl http://localhost:3000/health

# Test main API
curl http://localhost:3000/

# Test lifecycle endpoint
curl http://localhost:3000/lifecycle
```

**1.3 Build and Test Docker Image:**
```bash
# Build Docker image
docker build -f docker/Dockerfile --target production -t container-lifecycle-demo:local .

# Run container locally
docker run -d --name test-container -p 3001:3000 container-lifecycle-demo:local

# Test containerized application
curl http://localhost:3001/health

# Cleanup
docker stop test-container && docker rm test-container
```

### ☁️ **Step 2: Google Cloud Setup**

**2.1 Configure GCP Project:**
```bash
# Set project (replace with your project ID)
export PROJECT_ID="probable-cove-474504-p0"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  containerregistry.googleapis.com \
  compute.googleapis.com
```

**2.2 Create Service Account for GitHub Actions:**
```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --description="Service account for GitHub Actions CI/CD" \
  --display-name="GitHub Actions SA"

# Assign required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.admin"

# Create service account key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### 🔐 **Step 3: GitHub Repository Setup**

**3.1 Configure GitHub Secrets:**

Go to: `https://github.com/YOUR-USERNAME/container-lifecycle-demo/settings/secrets/actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `probable-cove-474504-p0` |
| `GCP_SA_KEY` | *(Entire content of `github-actions-key.json`)* |

**3.2 Push Code to Trigger Pipeline:**
```bash
# Add all changes
git add .

# Commit with descriptive message
git commit -m "Deploy container lifecycle management to GCP"

# Push to trigger CI/CD pipeline
git push origin main
```

### ☸️ **Step 4: GKE Cluster Deployment** (Optional)

**4.1 Automated Setup:**
```bash
# Run automated setup (creates cluster + deploys app)
./scripts/setup.sh --project-id probable-cove-474504-p0
```

**4.2 Manual GKE Setup:**
```bash
# Create GKE cluster
gcloud container clusters create container-lifecycle-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --machine-type n1-standard-2

# Get cluster credentials
gcloud container clusters get-credentials container-lifecycle-cluster --zone us-central1-a

# Deploy application
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n container-lifecycle-demo
kubectl get services -n container-lifecycle-demo
```

## 📊 **Monitoring & Verification**

### ✅ **Pipeline Verification:**
- Visit: `https://github.com/YOUR-USERNAME/container-lifecycle-demo/actions`
- Monitor: "Container Lifecycle Management" workflow
- Check: All stages complete successfully

### ✅ **Application Verification:**
```bash
# Get external IP (if deployed to GKE)
kubectl get svc -n container-lifecycle-demo container-lifecycle-demo-lb

# Test deployed application
export APP_URL="http://EXTERNAL-IP"
curl $APP_URL/health
curl $APP_URL/lifecycle

# Run deployment tests
python3 scripts/deployment-test.py --url $APP_URL
```

### ✅ **Security Verification:**
```bash
# Run compliance check
python3 scripts/compliance-check.py --image gcr.io/probable-cove-474504-p0/container-lifecycle-demo:latest

# Generate compliance report
python3 scripts/generate-compliance-report.py --project-id probable-cove-474504-p0
```

## 🔄 **Container Lifecycle Stages**

| Stage | Description | Tools & Processes |
|-------|-------------|-------------------|
| **1. Development** | Secure coding & local testing | Node.js, Jest, ESLint, Local Docker |
| **2. Build** | Multi-stage Docker builds | Docker, Alpine Linux, Non-root user |
| **3. Test** | Automated testing & validation | Jest, Supertest, Container structure tests |
| **4. Scan** | Security & vulnerability scanning | Trivy, npm audit, SBOM generation |
| **5. Registry** | Secure image storage | Google Container Registry, Image signing |
| **6. Deploy** | Policy-compliant deployment | Kubernetes, Security contexts, RBAC |
| **7. Runtime** | Monitoring & security enforcement | Prometheus, Health checks, Log aggregation |
| **8. Retire** | Automated cleanup & archival | Lifecycle policies, Storage optimization |

## 🛡️ **Security Features**

- ✅ **Multi-stage builds** - Minimal attack surface
- ✅ **Non-root execution** - Container security
- ✅ **Read-only filesystem** - Runtime protection  
- ✅ **Security scanning** - Vulnerability assessment
- ✅ **SBOM generation** - Supply chain transparency
- ✅ **Network policies** - Traffic isolation
- ✅ **Resource limits** - Resource governance
- ✅ **Credential protection** - Comprehensive .gitignore

## 📈 **Compliance & Reporting**

The project includes automated compliance reporting:

- **Daily**: Security scan results
- **Weekly**: Vulnerability assessments  
- **Monthly**: Comprehensive compliance reports
- **On-demand**: Custom compliance checks

## 🚨 **Troubleshooting**

### Common Issues:

**1. Docker Build Fails:**
```bash
# Clean Docker cache
docker system prune -a
docker build --no-cache -f docker/Dockerfile .
```

**2. GKE Deployment Issues:**
```bash
# Check cluster status
kubectl get nodes
kubectl describe pod POD-NAME -n container-lifecycle-demo
```

**3. GitHub Actions Failures:**
- Verify GitHub secrets are configured correctly
- Check service account permissions in GCP
- Review workflow logs in GitHub Actions tab

## 🔗 **Additional Resources**

- **Detailed Setup**: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
- **Lifecycle Guide**: [docs/CONTAINER_LIFECYCLE.md](docs/CONTAINER_LIFECYCLE.md)
- **Complete Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 📊 **Project Statistics**

- **Languages**: JavaScript, Python, Bash, YAML
- **Files**: 22 files, 5000+ lines of code
- **Tests**: 7 comprehensive test cases
- **Security Checks**: 9 validation categories
- **Deployment Targets**: Local Docker, GKE, Container Registry

**Built with ❤️ for enterprise container governance and lifecycle management**
