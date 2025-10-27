# Container Lifecycle Management - Complete Deployment Guide

This guide provides step-by-step instructions for deploying the complete container lifecycle management solution on Google Cloud Platform.

## 🎯 Deployment Overview

This POC demonstrates enterprise-grade container governance with:

- ✅ **Secure baseline images** with multi-stage Docker builds
- ✅ **Automated CI/CD pipeline** with GitHub Actions  
- ✅ **Comprehensive security scanning** with Trivy and policy validation
- ✅ **Kubernetes deployment** with security best practices
- ✅ **Complete lifecycle management** from build to retirement
- ✅ **Monitoring and compliance** reporting

## 🛠️ Prerequisites Setup

### 1. Install Required Tools

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install kubectl
gcloud components install kubectl

# Install Docker
# Follow instructions for your OS at https://docs.docker.com/get-docker/

# Install Node.js (for local development)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Install Python dependencies
pip3 install requests
```

### 2. Google Cloud Project Setup

```bash
# Set project ID
export PROJECT_ID="probable-cove-474504-p0"
export CLUSTER_NAME="container-lifecycle-cluster" 
export REGION="us-central1"
export ZONE="us-central1-a"

# Authenticate and set project
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  containerregistry.googleapis.com \
  compute.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudbuild.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account for CI/CD
gcloud iam service-accounts create container-lifecycle-sa \
  --description="Service account for container lifecycle management" \
  --display-name="Container Lifecycle SA"

# Assign required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.admin"

# Generate service account key
gcloud iam service-accounts keys create ~/container-lifecycle-key.json \
  --iam-account=container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## 🏗️ Infrastructure Deployment

### 1. Create GKE Cluster

```bash
# Create optimized GKE cluster
gcloud container clusters create $CLUSTER_NAME \
  --zone=$ZONE \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --machine-type=n1-standard-2 \
  --disk-size=50GB \
  --disk-type=pd-ssd \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-network-policy \
  --enable-ip-alias \
  --enable-shielded-nodes \
  --shielded-secure-boot \
  --shielded-integrity-monitoring \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --addons=HorizontalPodAutoscaling,HttpLoadBalancing,NetworkPolicy

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### 2. Configure Security Components

```bash
# Security is enforced through Kubernetes native security contexts
# Container scanning handled by Trivy in CI/CD pipeline
# Network policies and RBAC configured in Kubernetes manifests

echo "Security components configured through Kubernetes native features"
```

## 📦 Application Deployment

### 1. Clone and Configure Repository

```bash
# Clone the repository
git clone https://github.com/your-org/container-lifecycle-demo.git
cd container-lifecycle-demo

# Configuration files are already updated with your project ID
# No need to replace PROJECT_ID - already set to probable-cove-474504-p0
```

### 2. GitHub Repository Setup

1. **Create GitHub Repository**:
   ```bash
   gh repo create container-lifecycle-demo --public
   git remote add origin https://github.com/your-username/container-lifecycle-demo.git
   ```

2. **Configure GitHub Secrets**:
   - Go to repository Settings > Secrets and variables > Actions
   - Add the following secrets:

   | Secret Name | Value |
   |-------------|-------|
   | `GCP_PROJECT_ID` | Your Google Cloud project ID |
   | `GCP_SA_KEY` | Content of `~/container-lifecycle-key.json` |

### 3. Initial Build and Push

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build initial image
docker build -f docker/Dockerfile -t gcr.io/probable-cove-474504-p0/container-lifecycle-demo:v1.0.0 .

# Push to registry
docker push gcr.io/probable-cove-474504-p0/container-lifecycle-demo:v1.0.0

# Verify image in registry
gcloud container images list --repository=gcr.io/probable-cove-474504-p0
```

### 4. Deploy Kubernetes Resources

```bash
# Create namespace and RBAC
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml

# Create deployment and services
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify deployment
kubectl get all -n container-lifecycle-demo

# Check pod status
kubectl get pods -n container-lifecycle-demo -w
```

### 5. Expose Application

```bash
# Create static IP for load balancer
gcloud compute addresses create container-lifecycle-ip --global

# Get the IP address
export STATIC_IP=$(gcloud compute addresses describe container-lifecycle-ip --global --format="value(address)")
echo "Static IP: $STATIC_IP"

# Update DNS (if using custom domain)
# Point your domain to the static IP

# Apply ingress configuration
kubectl apply -f k8s/service.yaml

# Wait for load balancer to be ready
kubectl get ingress -n container-lifecycle-demo -w
```

## 📊 Monitoring Setup

### 1. Deploy Monitoring Stack

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f monitoring/prometheus.yml -n monitoring

# Port-forward to access Prometheus (in separate terminal)
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Access Prometheus at http://localhost:9090
```

### 2. Configure Grafana Dashboards

```bash
# Deploy Grafana
kubectl create -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin123"
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
EOF

# Access Grafana
kubectl get svc -n monitoring grafana
# Use the external IP to access Grafana (admin/admin123)
```

## 🔐 Security Configuration

### 1. Install Security Scanning Tools

```bash
# Install Trivy on cluster nodes or CI/CD agents
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
trivy --version

# Run initial security scan
trivy image gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0
```

### 2. Configure Policy Enforcement

```bash
# Apply OPA Gatekeeper policies
kubectl apply -f security/policies/

# Test policy enforcement
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-policy
  namespace: container-lifecycle-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: test
        image: nginx:latest  # This should be blocked by policy
EOF
```

## 🚀 CI/CD Pipeline Setup

### 1. Trigger First Deployment

```bash
# Commit and push code
git add .
git commit -m "Initial container lifecycle management deployment"
git push origin main

# Monitor GitHub Actions workflow
# Go to your repository > Actions tab to see the workflow progress
```

### 2. Verify Pipeline Stages

The CI/CD pipeline will:

1. **Code Analysis**: Run security audit and tests
2. **Container Build**: Build secure Docker image
3. **Security Scanning**: Scan for vulnerabilities  
4. **Policy Validation**: Check OPA policies
5. **Deployment**: Deploy to GKE
6. **Testing**: Run deployment tests

### 3. Monitor Deployment

```bash
# Watch deployment progress
kubectl rollout status deployment/container-lifecycle-demo -n container-lifecycle-demo

# Check application health
export APP_URL=$(kubectl get svc -n container-lifecycle-demo container-lifecycle-demo-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$APP_URL/health

# Run deployment tests
python3 scripts/deployment-test.py --url http://$APP_URL
```

## 🧪 Testing and Validation

### 1. Application Testing

```bash
# Health check
curl http://$APP_URL/health
# Expected: {"status":"healthy",...}

# Main application endpoint
curl http://$APP_URL/
# Expected: {"message":"Container Lifecycle Demo API",...}

# Lifecycle information
curl http://$APP_URL/lifecycle
# Expected: {"stage":"runtime","image":{...},...}
```

### 2. Security Testing

```bash
# Run compliance check
python3 scripts/compliance-check.py --image gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0

# Generate compliance report
python3 scripts/generate-compliance-report.py --project-id $PROJECT_ID

# Check security scan results
trivy image --format json gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0
```

### 3. Security Testing

```bash
# Test container structure and security
container-structure-test test \
  --image gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0 \
  --config security/container-structure-test.yaml

# Run vulnerability scan
trivy image gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0
```

## 📈 Monitoring and Maintenance

### 1. Set Up Automated Reports

```bash
# Schedule compliance reports (add to crontab)
# Daily security scan
0 2 * * * /usr/local/bin/trivy image gcr.io/$PROJECT_ID/container-lifecycle-demo:latest

# Weekly compliance report  
0 6 * * 1 python3 /opt/scripts/generate-compliance-report.py --project-id $PROJECT_ID

# Monthly cleanup
0 3 1 * * gcloud container images list-tags gcr.io/$PROJECT_ID/container-lifecycle-demo --filter="timestamp.datetime < '-P30D'" --format="get(digest)" | xargs -I {} gcloud container images delete gcr.io/$PROJECT_ID/container-lifecycle-demo@{} --quiet
```

### 2. Monitor Application Performance

```bash
# Check application metrics
kubectl top pods -n container-lifecycle-demo

# View logs
kubectl logs -l app=container-lifecycle-demo -n container-lifecycle-demo --tail=100

# Monitor resource usage
kubectl describe hpa container-lifecycle-demo -n container-lifecycle-demo
```

## 🎉 Deployment Verification

### Success Criteria Checklist

- ✅ GKE cluster created and configured
- ✅ Application deployed and accessible
- ✅ Security scanning integrated and passing
- ✅ Monitoring stack operational
- ✅ CI/CD pipeline functioning
- ✅ Policy enforcement active
- ✅ Compliance reporting working
- ✅ All tests passing

### Access Points

- **Application**: `http://$APP_URL` (LoadBalancer IP)
- **Prometheus**: `http://localhost:9090` (port-forward)
- **Grafana**: `http://<grafana-lb-ip>:3000` (admin/admin123)
- **GitHub Actions**: Repository > Actions tab

### Next Steps

1. **Customize Security Policies**: Modify policies in `security/policies/`
2. **Set Up Alerting**: Configure Grafana alerts and notifications
3. **Implement Image Signing**: Set up Cosign for image verification
4. **Add Custom Metrics**: Extend application with business metrics
5. **Scale Resources**: Adjust cluster and application sizing based on needs

## 🆘 Troubleshooting

### Common Issues

1. **Pod Not Starting**: Check `kubectl describe pod <pod-name>` and security contexts
2. **Load Balancer Pending**: Verify GCP quotas and firewall rules
3. **CI/CD Failing**: Check GitHub secrets and service account permissions
4. **Security Scan Failures**: Update Trivy database and check image accessibility

### Support Resources

- **Documentation**: See `docs/` directory for detailed guides
- **GitHub Issues**: Create issue in repository for bugs
- **Monitoring**: Check Grafana dashboards for system health
- **Logs**: Use `kubectl logs` for application debugging

---

🎊 **Congratulations!** You have successfully deployed a complete container lifecycle management solution with enterprise-grade security, monitoring, and governance capabilities.
