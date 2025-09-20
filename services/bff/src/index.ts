import fastify, { FastifyInstance } from 'fastify';
import axios from 'axios';
import FormData from 'form-data';

// Extend FastifyRequest to include multipart functionality
declare module 'fastify' {
  interface FastifyRequest {
    file(): Promise<{
      filename: string;
      mimetype: string;
      toBuffer(): Promise<Buffer>;
    } | undefined>;
  }
}

// Import configuration (simplified for now)
const config = {
  PORT: parseInt(process.env.PORT || '3000'),
  NODE_ENV: process.env.NODE_ENV || 'development',
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
  USER_SERVICE_URL: process.env.USER_SERVICE_URL || 'http://user-service:8080',
  INGESTION_SERVICE_URL: process.env.INGESTION_SERVICE_URL || 'http://ingestion-service:8080',
  ANALYSIS_SERVICE_URL: process.env.ANALYSIS_SERVICE_URL || 'http://analysis-service:8080',
  CORS_ORIGIN: process.env.CORS_ORIGIN || '*',
  REQUEST_TIMEOUT: parseInt(process.env.REQUEST_TIMEOUT || '30000')
};

const startTime = Date.now();

async function buildApp(): Promise<FastifyInstance> {
  const app = fastify({
    logger: {
      level: config.LOG_LEVEL,
      transport: config.NODE_ENV === 'development' ? {
        target: 'pino-pretty',
        options: {
          translateTime: 'HH:MM:ss Z',
          ignore: 'pid,hostname'
        }
      } : undefined
    }
  });

  // Register CORS
  await app.register(require('@fastify/cors'), {
    origin: config.CORS_ORIGIN,
    credentials: true
  });

  // Register multipart support for file uploads
  await app.register(require('@fastify/multipart'), {
    limits: {
      fileSize: 1024 * 1024 * 1024 // 1GB limit for demo files
    }
  });

  // Root endpoint
  app.get('/', async () => {
    return {
      service: 'bff',
      version: '1.0.0',
      description: 'StratagemForge Backend for Frontend service',
      uptime: Date.now() - startTime,
      endpoints: {
        health: '/health',
        ready: '/ready',
        config: '/config',
        docs: '/docs',
        api: {
          users: '/api/users',
          demos: '/api/demos',
          analysis: '/api/analysis'
        }
      }
    };
  });

  // Health endpoints
  app.get('/health', async () => {
    return {
      status: 'healthy',
      service: 'bff',
      version: '1.0.0',
      uptime: Date.now() - startTime,
      timestamp: new Date().toISOString()
    };
  });

  app.get('/ready', async () => {
    return {
      status: 'ready',
      service: 'bff',
      timestamp: new Date().toISOString()
    };
  });

  app.get('/config', async () => {
    return {
      service: 'bff',
      version: '1.0.0',
      environment: config.NODE_ENV,
      uptime: Date.now() - startTime,
      services: {
        userService: config.USER_SERVICE_URL,
        ingestionService: config.INGESTION_SERVICE_URL,
        analysisService: config.ANALYSIS_SERVICE_URL
      }
    };
  });

  // Service connectivity test endpoint
  app.get('/test/connectivity', async () => {
    interface IServiceResult {
      status: 'connected' | 'failed';
      url: string;
      response?: unknown;
      responseTime?: string;
      error?: string;
      code?: string;
    }

    interface IConnectivityResults {
      bff: { status: string; timestamp: string };
      services: Record<string, IServiceResult>;
    }

    const results: IConnectivityResults = {
      bff: { status: 'healthy', timestamp: new Date().toISOString() },
      services: {}
    };

    // Test ingestion service
    try {
      const response = await axios.get(`${config.INGESTION_SERVICE_URL}/health`, {
        timeout: 5000
      });
      results.services.ingestionService = {
        status: 'connected',
        url: config.INGESTION_SERVICE_URL,
        response: response.data,
        responseTime: response.headers['x-response-time'] || 'unknown'
      };
    } catch (error) {
      results.services.ingestionService = {
        status: 'failed',
        url: config.INGESTION_SERVICE_URL,
        error: error instanceof Error ? error.message : 'Unknown error',
        code: axios.isAxiosError(error) ? error.code : 'UNKNOWN'
      };
    }

    // Test user service
    try {
      const response = await axios.get(`${config.USER_SERVICE_URL}/health`, {
        timeout: 5000
      });
      results.services.userService = {
        status: 'connected',
        url: config.USER_SERVICE_URL,
        response: response.data,
        responseTime: response.headers['x-response-time'] || 'unknown'
      };
    } catch (error) {
      results.services.userService = {
        status: 'failed',
        url: config.USER_SERVICE_URL,
        error: error instanceof Error ? error.message : 'Unknown error',
        code: axios.isAxiosError(error) ? error.code : 'UNKNOWN'
      };
    }

    // Test analysis service
    try {
      const response = await axios.get(`${config.ANALYSIS_SERVICE_URL}/health`, {
        timeout: 5000
      });
      results.services.analysisService = {
        status: 'connected',
        url: config.ANALYSIS_SERVICE_URL,
        response: response.data,
        responseTime: response.headers['x-response-time'] || 'unknown'
      };
    } catch (error) {
      results.services.analysisService = {
        status: 'failed',
        url: config.ANALYSIS_SERVICE_URL,
        error: error instanceof Error ? error.message : 'Unknown error',
        code: axios.isAxiosError(error) ? error.code : 'UNKNOWN'
      };
    }

    return results;
  });

  // API route placeholders
  app.register(async function(fastify) {
    // Users API
    fastify.get('/api/users', async () => {
      return {
        message: 'Users endpoint - will proxy to user-service',
        service: 'user-service',
        url: config.USER_SERVICE_URL
      };
    });

    // Demos API
    fastify.get('/api/demos', async () => {
      try {
        // Test actual connectivity to ingestion service
        const response = await axios.get(`${config.INGESTION_SERVICE_URL}/health`, {
          timeout: 5000
        });

        return {
          message: 'Demos endpoint - successfully connected to ingestion service',
          service: 'ingestion-service',
          url: config.INGESTION_SERVICE_URL,
          connectivity: 'SUCCESS',
          ingestionHealth: response.data,
          timestamp: new Date().toISOString()
        };
      } catch (error) {
        return {
          message: 'Demos endpoint - failed to connect to ingestion service',
          service: 'ingestion-service',
          url: config.INGESTION_SERVICE_URL,
          connectivity: 'FAILED',
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString()
        };
      }
    });

    // Demo upload endpoint
    fastify.post('/api/demos/upload', async (request, reply) => {
      try {
        // Use multipart file() method for file upload
        const data = await request.file();

        if (!data) {
          return reply.code(400).send({ error: 'No file uploaded' });
        }

        // Validate file type
        const allowedMimeTypes = ['application/zip', 'application/octet-stream', 'application/x-zip-compressed'];
        const maxFileSize = 1024 * 1024 * 1024; // 1GB

        if (!allowedMimeTypes.includes(data.mimetype)) {
          return reply.code(400).send({ error: 'Invalid file type' });
        }

        // Note: File size validation happens at the plugin level via limits configuration
        // The file stream will be truncated if it exceeds the configured limit

        // Convert the file stream to buffer for forwarding
        const buffer = await data.toBuffer();

        // Create FormData to forward to ingestion service
        const formData = new FormData();
        formData.append('file', buffer, {
          filename: data.filename,
          contentType: data.mimetype
        });

        // Forward to ingestion service
        const response = await axios.post(`${config.INGESTION_SERVICE_URL}/upload`, formData, {
          headers: {
            ...formData.getHeaders(),
          },
          maxContentLength: maxFileSize,
          maxBodyLength: maxFileSize,
          timeout: 60000 // 60 seconds
        });

        return response.data;
      } catch (error) {
        return reply.code(500).send({
          error: 'Failed to upload demo file',
          details: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    });

    // Analysis API
    fastify.post('/api/analysis', async (request) => {
      return {
        message: 'Analysis endpoint - will proxy to analysis-service',
        service: 'analysis-service',
        url: config.ANALYSIS_SERVICE_URL,
        body: request.body
      };
    });
  });

  return app;
}

async function start(): Promise<void> {
  try {
    const app = await buildApp();

    await app.listen({
      port: config.PORT,
      host: '0.0.0.0'
    });

    app.log.info(`🚀 BFF service started on port ${config.PORT}`);
    app.log.info(`🔗 Service URLs:`);
    app.log.info(`   User Service: ${config.USER_SERVICE_URL}`);
    app.log.info(`   Ingestion Service: ${config.INGESTION_SERVICE_URL}`);
    app.log.info(`   Analysis Service: ${config.ANALYSIS_SERVICE_URL}`);

  } catch (error) {
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  process.exit(0);
});

process.on('SIGTERM', async () => {
  process.exit(0);
});

// Start the application
if (require.main === module) {
  start();
}

export { buildApp, start };
export default buildApp;
