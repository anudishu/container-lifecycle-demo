const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');
const os = require('os');

const PORT = Number(process.env.PORT) || 3000;
const NODE_ENV = process.env.NODE_ENV || 'development';

/** In-process counters for the /metrics endpoint (resets on restart). */
const metrics = {
  requestsTotal: 0,
  errors4xx: 0,
  errors5xx: 0,
  responseTimeMsSum: 0,
};

function buildApp() {
  const app = express();

  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", 'data:', 'https:'],
        },
      },
      hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true,
      },
    })
  );

  const allowedOrigins = process.env.ALLOWED_ORIGINS
    ? process.env.ALLOWED_ORIGINS.split(',').map((s) => s.trim())
    : ['http://localhost:3000'];

  app.use(
    cors({
      origin: allowedOrigins,
      credentials: true,
    })
  );

  if (NODE_ENV === 'production') {
    app.use(compression());
  }
  app.use(morgan(NODE_ENV === 'production' ? 'combined' : 'dev'));

  app.use((req, res, next) => {
    const start = Date.now();
    res.on('finish', () => {
      metrics.requestsTotal += 1;
      metrics.responseTimeMsSum += Date.now() - start;
      if (res.statusCode >= 500) metrics.errors5xx += 1;
      else if (res.statusCode >= 400) metrics.errors4xx += 1;
    });
    next();
  });

  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  app.get('/', (req, res) => {
    res.json({
      message: 'Container Lifecycle Demo API',
      version: process.env.VERSION || '1.0.0',
      environment: NODE_ENV,
      timestamp: new Date().toISOString(),
      container: {
        hostname: os.hostname(),
        platform: process.platform,
        nodeVersion: process.version,
      },
    });
  });

  app.get('/health', (req, res) => {
    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      pid: process.pid,
    });
  });

  app.get('/readiness', (req, res) => {
    res.status(200).json({
      status: 'ready',
      timestamp: new Date().toISOString(),
      checks: {
        server: 'ok',
        dependencies: 'ok',
      },
    });
  });

  app.get('/metrics', (req, res) => {
    const n = metrics.requestsTotal;
    const avgMs = n > 0 ? metrics.responseTimeMsSum / n : 0;
    res.json({
      requests: {
        total: n,
        errors4xx: metrics.errors4xx,
        errors5xx: metrics.errors5xx,
        avgResponseTimeMs: Math.round(avgMs * 100) / 100,
      },
      system: {
        memory: process.memoryUsage(),
        uptime: process.uptime(),
        cpu: process.cpuUsage(),
      },
      timestamp: new Date().toISOString(),
    });
  });

  app.get('/lifecycle', (req, res) => {
    res.json({
      stage: 'runtime',
      image: {
        tag: process.env.IMAGE_TAG || 'latest',
        digest: process.env.IMAGE_DIGEST || 'unknown',
        buildTime: process.env.BUILD_TIME || 'unknown',
        gitCommit: process.env.GIT_COMMIT || 'unknown',
      },
      deployment: {
        environment: NODE_ENV,
        namespace: process.env.K8S_NAMESPACE || 'default',
        pod: process.env.K8S_POD_NAME || process.env.HOSTNAME || 'unknown',
      },
      security: {
        scanned: process.env.SECURITY_SCANNED === 'true',
        vulnerabilities: process.env.VULNERABILITIES || 'unknown',
        compliance: process.env.COMPLIANCE_STATUS || 'unknown',
      },
    });
  });

  app.use(express.static(path.join(__dirname, 'public')));

  app.use((err, _req, res, next) => {
    if (res.headersSent) {
      next(err);
      return;
    }
    console.error(err.stack);
    res.status(500).json({
      error: NODE_ENV === 'production' ? 'Internal Server Error' : err.message,
      timestamp: new Date().toISOString(),
    });
  });

  app.use((req, res) => {
    res.status(404).json({
      error: 'Not Found',
      path: req.path,
      timestamp: new Date().toISOString(),
    });
  });

  return app;
}

const app = buildApp();

function startServer() {
  const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Listening on ${PORT} (${NODE_ENV})`);
    console.log(`Health: http://localhost:${PORT}/health`);
  });

  function shutdown(signal) {
    console.log(`${signal} received, closing server`);
    server.close(() => {
      process.exit(0);
    });
    setTimeout(() => process.exit(1), 10_000).unref();
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  return server;
}

if (require.main === module) {
  startServer();
}

module.exports = app;
