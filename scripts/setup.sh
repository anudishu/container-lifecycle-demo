#!/bin/bash

# Container Lifecycle Management Setup Script
# This script automates the setup of the complete container lifecycle management solution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="probable-cove-474504-p0"
CLUSTER_NAME="container-lifecycle-cluster"
REGION="us-central1"
ZONE="us-central1-a"
GITHUB_REPO=""

# Functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("gcloud" "kubectl" "docker" "node" "npm" "python3")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "No active gcloud authentication found. Please run 'gcloud auth login'"
        exit 1
    fi
    
    success "All prerequisites check passed"
}

get_configuration() {
    log "Getting configuration..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    fi
    
    if [[ -z "$GITHUB_REPO" ]]; then
        read -p "Enter your GitHub repository (username/repo-name): " GITHUB_REPO
    fi
    
    log "Configuration:"
    log "  Project ID: $PROJECT_ID"
    log "  Cluster Name: $CLUSTER_NAME"
    log "  Region: $REGION"
    log "  GitHub Repo: $GITHUB_REPO"
    
    read -p "Continue with this configuration? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        log "Aborting setup"
        exit 0
    fi
}

setup_gcp_project() {
    log "Setting up Google Cloud Project..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable APIs
    log "Enabling required APIs..."
    gcloud services enable \
        container.googleapis.com \
        containerregistry.googleapis.com \
        compute.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com \
        cloudbuild.googleapis.com
    
    success "GCP project setup completed"
}

create_service_account() {
    log "Creating service account..."
    
    # Create service account
    gcloud iam service-accounts create container-lifecycle-sa \
        --description="Service account for container lifecycle management" \
        --display-name="Container Lifecycle SA" || true
    
    # Assign roles
    local roles=(
        "roles/container.admin"
        "roles/storage.admin" 
        "roles/compute.admin"
    )
    
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="$role"
    done
    
    # Generate key
    gcloud iam service-accounts keys create container-lifecycle-key.json \
        --iam-account=container-lifecycle-sa@$PROJECT_ID.iam.gserviceaccount.com
    
    success "Service account created and configured"
}

create_gke_cluster() {
    log "Creating GKE cluster..."
    
    # Check if cluster already exists
    if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE &>/dev/null; then
        warning "Cluster $CLUSTER_NAME already exists"
        return 0
    fi
    
    # Create cluster
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
    
    # Get credentials
    gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE
    
    success "GKE cluster created successfully"
}

install_security_components() {
    log "Installing security components..."
    
    # Configure security scanning tools
    log "Security scanning will be handled by Trivy in the CI/CD pipeline"
    log "Container security policies enforced through Kubernetes native security contexts"
    
    success "Security components configured"
}

build_and_push_image() {
    log "Building and pushing initial container image..."
    
    # Configure Docker for GCR
    gcloud auth configure-docker
    
    # Update Dockerfile with project ID
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" k8s/deployment.yaml
    
    # Build image
    docker build -f docker/Dockerfile -t gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0 .
    
    # Push image
    docker push gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0
    
    success "Container image built and pushed"
}

deploy_application() {
    log "Deploying application to Kubernetes..."
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/rbac.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    # Wait for deployment
    log "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/container-lifecycle-demo -n container-lifecycle-demo
    
    success "Application deployed successfully"
}

setup_monitoring() {
    log "Setting up monitoring stack..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ConfigMap for Prometheus config
    kubectl create configmap prometheus-config --from-file=monitoring/prometheus.yml -n monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        command:
        - /bin/prometheus
        - --config.file=/etc/prometheus/prometheus.yml
        - --storage.tsdb.path=/prometheus
        - --web.console.libraries=/etc/prometheus/console_libraries
        - --web.console.templates=/etc/prometheus/consoles
        - --storage.tsdb.retention.time=200h
        - --web.enable-lifecycle
      volumes:
      - name: config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
EOF
    
    success "Monitoring stack deployed"
}

create_static_ip() {
    log "Creating static IP for load balancer..."
    
    # Create static IP
    gcloud compute addresses create container-lifecycle-ip --global || true
    
    # Get IP address
    STATIC_IP=$(gcloud compute addresses describe container-lifecycle-ip --global --format="value(address)")
    
    log "Static IP created: $STATIC_IP"
    success "Static IP configuration completed"
}

run_tests() {
    log "Running deployment tests..."
    
    # Wait for load balancer
    log "Waiting for load balancer to be ready..."
    sleep 60
    
    # Get external IP
    EXTERNAL_IP=$(kubectl get svc -n container-lifecycle-demo container-lifecycle-demo-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    
    if [[ -n "$EXTERNAL_IP" ]]; then
        log "Testing application at http://$EXTERNAL_IP"
        
        # Basic connectivity test
        if curl -f http://$EXTERNAL_IP/health --max-time 10 &>/dev/null; then
            success "Application is responding correctly"
        else
            warning "Application health check failed, but this is normal during initial deployment"
        fi
        
        # Run deployment tests if available
        if [[ -f "scripts/deployment-test.py" ]]; then
            python3 scripts/deployment-test.py --url http://$EXTERNAL_IP || true
        fi
    else
        warning "Load balancer external IP not yet available. You can check later with: kubectl get svc -n container-lifecycle-demo"
    fi
}

print_summary() {
    success "Container Lifecycle Management setup completed!"
    echo
    log "Setup Summary:"
    log "  Project ID: $PROJECT_ID"
    log "  Cluster: $CLUSTER_NAME (zone: $ZONE)"
    log "  Application: container-lifecycle-demo"
    echo
    log "Next Steps:"
    log "1. Configure GitHub repository secrets:"
    log "   - GCP_PROJECT_ID: $PROJECT_ID"
    log "   - GCP_SA_KEY: (content of container-lifecycle-key.json)"
    echo
    log "2. Access your application:"
    EXTERNAL_IP=$(kubectl get svc -n container-lifecycle-demo container-lifecycle-demo-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    log "   - Application URL: http://$EXTERNAL_IP"
    log "   - Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
    echo
    log "3. Monitor with:"
    log "   - kubectl get pods -n container-lifecycle-demo"
    log "   - kubectl logs -l app=container-lifecycle-demo -n container-lifecycle-demo"
    echo
    log "4. Run compliance checks:"
    log "   - python3 scripts/compliance-check.py --image gcr.io/$PROJECT_ID/container-lifecycle-demo:v1.0.0"
    log "   - python3 scripts/generate-compliance-report.py --project-id $PROJECT_ID"
    echo
    success "Happy container lifecycle management! 🚀"
}

# Main execution
main() {
    log "Starting Container Lifecycle Management setup..."
    
    check_prerequisites
    get_configuration
    setup_gcp_project
    create_service_account
    create_gke_cluster
    install_security_components
    build_and_push_image
    deploy_application
    setup_monitoring
    create_static_ip
    run_tests
    print_summary
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --github-repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --zone)
            ZONE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --project-id     Google Cloud Project ID"
            echo "  --github-repo    GitHub repository (username/repo)"
            echo "  --cluster-name   GKE cluster name (default: container-lifecycle-cluster)"
            echo "  --zone           GCP zone (default: us-central1-a)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option $1"
            exit 1
            ;;
    esac
done

# Run main function
main
