# Container Lifecycle Management POC

A comprehensive demonstration of container image lifecycle management using GitHub Actions, Docker, Kubernetes, and Google Cloud Platform.

## 🎯 Project Overview

This project demonstrates enterprise-grade container governance practices including:

- **Secure baseline image creation** with multi-stage builds
- **Automated CI/CD pipeline** with GitHub Actions
- **Container security scanning** and vulnerability management
- **Policy enforcement** and compliance checks
- **Complete lifecycle management** from development to retirement
- **Google Cloud deployment** using GKE (Google Kubernetes Engine)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Developer     │───▶│  GitHub Actions  │───▶│  Google Cloud   │
│   Commits Code  │    │  CI/CD Pipeline  │    │      GKE        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Container Registry│
                       │ Security Scanning │
                       └──────────────────┘
```

## 📁 Project Structure

```
├── app/                    # Application source code
├── docker/                 # Docker configurations
├── .github/workflows/      # GitHub Actions workflows
├── k8s/                   # Kubernetes manifests
├── security/              # Security policies and configurations
├── scripts/               # Automation scripts
└── docs/                  # Documentation
```

## 🚀 Getting Started

### Prerequisites

- Docker Desktop
- Google Cloud SDK
- kubectl
- GitHub account
- Google Cloud Project with billing enabled

### Quick Setup

1. Clone the repository
2. Configure GCP credentials: `gcloud auth login`
3. Run setup script: `./quick-start.sh`
4. Configure GitHub secrets and push code to trigger CI/CD

## 🛡️ Security Features

- **Multi-stage Docker builds** for minimal attack surface
- **Vulnerability scanning** with Trivy and Google Cloud Security Scanner
- **SBOM generation** for supply chain transparency
- **Security enforcement** with Kubernetes security contexts
- **Runtime security** with admission controllers

## 📋 Container Lifecycle Stages

1. **Development** - Secure coding and local testing
2. **Build** - Multi-stage Docker builds with security scanning
3. **Test** - Automated testing and security validation
4. **Registry** - Secure image storage with vulnerability management
5. **Deploy** - Secure deployment to GKE (Google Kubernetes Engine)
6. **Runtime** - Monitoring and security enforcement
7. **Retirement** - Automated cleanup and archival

## 🔧 Configuration

See individual component documentation in the `docs/` directory for detailed configuration instructions.

## 📊 Monitoring & Compliance

- Container image scanning reports
- Compliance dashboard
- Security policy violations
- Lifecycle stage tracking

---

**Built with ❤️ for enterprise container governance**
