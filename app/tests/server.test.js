const request = require('supertest');
const app = require('../server');

describe('Container Lifecycle Demo API', () => {
  let server;

  beforeAll((done) => {
    server = app.listen(0, done); // Use port 0 for testing
  });

  afterAll((done) => {
    server.close(done);
  });

  describe('GET /', () => {
    it('should return API information', async () => {
      const response = await request(app).get('/');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('message');
      expect(response.body).toHaveProperty('version');
      expect(response.body).toHaveProperty('environment');
      expect(response.body).toHaveProperty('container');
    });
  });

  describe('GET /health', () => {
    it('should return health status', async () => {
      const response = await request(app).get('/health');
      
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('memory');
    });
  });

  describe('GET /readiness', () => {
    it('should return readiness status', async () => {
      const response = await request(app).get('/readiness');
      
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('ready');
      expect(response.body).toHaveProperty('checks');
      expect(response.body.checks.server).toBe('ok');
    });
  });

  describe('GET /metrics', () => {
    it('should return system metrics', async () => {
      const response = await request(app).get('/metrics');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('requests');
      expect(response.body).toHaveProperty('system');
      expect(response.body.system).toHaveProperty('memory');
      expect(response.body.system).toHaveProperty('uptime');
    });
  });

  describe('GET /lifecycle', () => {
    it('should return container lifecycle information', async () => {
      const response = await request(app).get('/lifecycle');
      
      expect(response.status).toBe(200);
      expect(response.body.stage).toBe('runtime');
      expect(response.body).toHaveProperty('image');
      expect(response.body).toHaveProperty('deployment');
      expect(response.body).toHaveProperty('security');
    });
  });

  describe('Security headers', () => {
    it('should include security headers', async () => {
      const response = await request(app).get('/');
      
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('x-frame-options');
      expect(response.headers).toHaveProperty('x-xss-protection');
    });
  });

  describe('404 handling', () => {
    it('should return 404 for non-existent routes', async () => {
      const response = await request(app).get('/non-existent');
      
      expect(response.status).toBe(404);
      expect(response.body.error).toBe('Not Found');
    });
  });
});
