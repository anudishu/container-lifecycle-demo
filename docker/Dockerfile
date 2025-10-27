# Multi-stage Dockerfile for secure container lifecycle management
# Stage 1: Build stage with security scanning and dependency validation

FROM node:18-alpine AS base
LABEL maintainer="Container Lifecycle Team"
LABEL org.opencontainers.image.title="Container Lifecycle Demo"
LABEL org.opencontainers.image.description="Demo application for enterprise container governance"
LABEL org.opencontainers.image.vendor="Container Governance Team"

# Install security updates and required packages
RUN apk update && apk upgrade && \
    apk add --no-cache \
    dumb-init \
    curl \
    ca-certificates && \
    rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nodejs

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY --chown=nodejs:nodejs app/package*.json ./

# Stage 2: Dependencies installation and vulnerability scanning
FROM base AS dependencies

# Install dependencies with security audit
RUN npm ci --only=production --no-audit --no-fund && \
    npm audit --audit-level=high && \
    npm cache clean --force

# Stage 3: Development dependencies for testing
FROM base AS dev-dependencies

# Install all dependencies including dev dependencies
RUN npm ci --no-audit --no-fund

COPY --chown=nodejs:nodejs app/ ./

# Run security audit and tests
RUN npm run security:audit && \
    npm run test && \
    npm run test:coverage

# Stage 4: Production build
FROM base AS production

# Copy production dependencies from dependencies stage
COPY --from=dependencies --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy application source code
COPY --chown=nodejs:nodejs app/ ./

# Remove unnecessary files for production
RUN rm -rf tests/ *.md && \
    find . -name "*.test.js" -delete

# Set build-time arguments for lifecycle tracking
ARG BUILD_TIME
ARG GIT_COMMIT
ARG VERSION=1.0.0
ARG IMAGE_TAG=latest

# Set environment variables for runtime
ENV NODE_ENV=production \
    PORT=3000 \
    BUILD_TIME=${BUILD_TIME} \
    GIT_COMMIT=${GIT_COMMIT} \
    VERSION=${VERSION} \
    IMAGE_TAG=${IMAGE_TAG}

# Switch to non-root user
USER nodejs

# Expose port (non-privileged)
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Use dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

# Stage 5: Security scanning stage (for CI/CD pipeline)
FROM base AS security-scan

# Install Trivy as root user before switching to nodejs user
USER root
RUN apk add --no-cache wget && \
    wget -qO- https://github.com/aquasecurity/trivy/releases/latest/download/trivy_Linux-64bit.tar.gz | tar xz -C /tmp && \
    mv /tmp/trivy /usr/local/bin/ && \
    chmod +x /usr/local/bin/trivy && \
    trivy --version

# Copy the application from production stage
COPY --from=production --chown=nodejs:nodejs /app /app
WORKDIR /app

# Switch back to nodejs user for security
USER nodejs

# Metadata for image lifecycle management
LABEL org.opencontainers.image.created=${BUILD_TIME}
LABEL org.opencontainers.image.revision=${GIT_COMMIT}
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.source="https://github.com/your-org/container-lifecycle-demo"
LABEL lifecycle.stage="runtime"
LABEL security.scanned="true"
LABEL compliance.policy="enterprise-baseline"
