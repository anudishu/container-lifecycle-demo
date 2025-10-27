const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true
}));

// Compression and logging
app.use(compression());
app.use(morgan('combined'));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.get('/', (req, res) => {
  res.json({
    message: 'Container Lifecycle Demo API',
    version: '1.0.0',
    environment: NODE_ENV,
    timestamp: new Date().toISOString(),
    container: {
      hostname: require('os').hostname(),
      platform: process.platform,
      nodeVersion: process.version
    }
  });
});

app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    pid: process.pid
  });
});

app.get('/readiness', (req, res) => {
  // Add your readiness checks here (database connections, etc.)
  res.status(200).json({
    status: 'ready',
    timestamp: new Date().toISOString(),
    checks: {
      server: 'ok',
      dependencies: 'ok'
    }
  });
});

app.get('/metrics', (req, res) => {
  res.json({
    requests: {
      total: 0, // Implement actual metrics
      errors: 0,
      avgResponseTime: 0
    },
    system: {
      memory: process.memoryUsage(),
      uptime: process.uptime(),
      cpu: process.cpuUsage()
    },
    timestamp: new Date().toISOString()
  });
});

// Container lifecycle endpoints
app.get('/lifecycle', (req, res) => {
  res.json({
    stage: 'runtime',
    image: {
      tag: process.env.IMAGE_TAG || 'latest',
      digest: process.env.IMAGE_DIGEST || 'unknown',
      buildTime: process.env.BUILD_TIME || 'unknown'
    },
    deployment: {
      environment: NODE_ENV,
      namespace: process.env.K8S_NAMESPACE || 'default',
      pod: process.env.HOSTNAME || 'unknown'
    },
    security: {
      scanned: process.env.SECURITY_SCANNED === 'true',
      vulnerabilities: process.env.VULNERABILITIES || 'unknown',
      compliance: process.env.COMPLIANCE_STATUS || 'unknown'
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err.stack);
  res.status(500).json({
    error: NODE_ENV === 'production' ? 'Internal Server Error' : err.message,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    path: req.path,
    timestamp: new Date().toISOString()
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
    process.exit(0);
  });
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT} in ${NODE_ENV} mode`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Readiness check: http://localhost:${PORT}/readiness`);
});

module.exports = app;
