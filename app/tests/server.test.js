const request = require('supertest');
const app = require('../server');

describe('Container Lifecycle Demo API', () => {
  describe('GET /', () => {
    it('returns API metadata and container hints', async () => {
      const res = await request(app).get('/');

      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({
        message: 'Container Lifecycle Demo API',
        environment: expect.any(String),
      });
      expect(res.body).toHaveProperty('version');
      expect(res.body.container).toMatchObject({
        hostname: expect.any(String),
        platform: expect.any(String),
        nodeVersion: expect.any(String),
      });
    });
  });

  describe('GET /health', () => {
    it('returns healthy status and runtime stats', async () => {
      const res = await request(app).get('/health');

      expect(res.status).toBe(200);
      expect(res.body.status).toBe('healthy');
      expect(res.body).toHaveProperty('timestamp');
      expect(res.body).toHaveProperty('uptime');
      expect(res.body).toHaveProperty('memory');
    });
  });

  describe('GET /readiness', () => {
    it('returns ready when dependency checks pass', async () => {
      const res = await request(app).get('/readiness');

      expect(res.status).toBe(200);
      expect(res.body.status).toBe('ready');
      expect(res.body.checks.server).toBe('ok');
    });
  });

  describe('GET /metrics', () => {
    it('returns request counters and system snapshot', async () => {
      await request(app).get('/health');
      const res = await request(app).get('/metrics');

      expect(res.status).toBe(200);
      expect(res.body.requests).toMatchObject({
        total: expect.any(Number),
        errors4xx: expect.any(Number),
        errors5xx: expect.any(Number),
        avgResponseTimeMs: expect.any(Number),
      });
      expect(res.body.system).toHaveProperty('memory');
      expect(res.body.system).toHaveProperty('uptime');
    });
  });

  describe('GET /lifecycle', () => {
    it('returns image, deployment, and security fields', async () => {
      const res = await request(app).get('/lifecycle');

      expect(res.status).toBe(200);
      expect(res.body.stage).toBe('runtime');
      expect(res.body.image).toHaveProperty('tag');
      expect(res.body.image).toHaveProperty('gitCommit');
      expect(res.body.deployment).toHaveProperty('namespace');
      expect(res.body.security).toHaveProperty('scanned');
    });
  });

  describe('Security headers', () => {
    it('sets common hardening headers', async () => {
      const res = await request(app).get('/');

      expect(res.headers['x-content-type-options']).toBeDefined();
      expect(res.headers['x-frame-options']).toBeDefined();
    });
  });

  describe('404 handling', () => {
    it('returns JSON for unknown routes', async () => {
      const res = await request(app).get('/no-such-route');

      expect(res.status).toBe(404);
      expect(res.body.error).toBe('Not Found');
      expect(res.body.path).toBe('/no-such-route');
    });
  });
});
