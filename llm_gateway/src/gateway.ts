import express, { Request, Response, NextFunction } from 'express';
import * as http from 'http';
import * as https from 'https';
import * as dotenv from 'dotenv';
import { URL } from 'url';

// Load environment variables
dotenv.config();

// --- Configuration ---
const API_KEYS = (process.env.ALLOWED_API_KEYS || '')
  .split(',')
  .map(k => k.trim())
  .filter(k => k.length > 0);

const VLLM_BASE = (process.env.VLLM_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');
const GATEWAY_HOST = process.env.GATEWAY_HOST || '0.0.0.0';
const GATEWAY_PORT = parseInt(process.env.GATEWAY_PORT || '8080', 10);

// --- Express App ---
const app = express();

// Disable buffering for all responses
app.disable('x-powered-by');
app.disable('etag');

// Parse JSON body (but with a large limit for potential large payloads)
app.use(express.json({ limit: '50mb' }));

// --- Auth Middleware ---
function checkAuth(req: Request, res: Response, next: NextFunction) {
  const authorization = req.headers.authorization;
  
  if (!authorization) {
    return res.status(401).json({ detail: 'Missing Authorization header' });
  }
  
  if (!authorization.toLowerCase().startsWith('bearer ')) {
    return res.status(401).json({ detail: 'Invalid Authorization format' });
  }
  
  const token = authorization.substring(7).trim();
  
  if (!API_KEYS.includes(token)) {
    return res.status(403).json({ detail: 'Invalid API key' });
  }
  
  next();
}

// --- Forward Request Handler ---
async function forwardRequest(
  req: Request,
  res: Response,
  method: string,
  path: string
) {
  try {
    // Construct target URL
    const targetUrl = new URL(path, VLLM_BASE);
    
    // Copy query parameters
    Object.keys(req.query).forEach(key => {
      targetUrl.searchParams.append(key, req.query[key] as string);
    });

    // Prepare headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Copy relevant headers from client (exclude host, content-length)
    Object.keys(req.headers).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (lowerKey !== 'host' && lowerKey !== 'content-length') {
        const value = req.headers[key];
        if (typeof value === 'string') {
          headers[key] = value;
        }
      }
    });

    // Prepare request body
    let body: string | undefined;
    if (method !== 'GET' && method !== 'HEAD') {
      body = JSON.stringify(req.body);
      headers['Content-Length'] = Buffer.byteLength(body).toString();
    }

    // Use native http/https modules for proper streaming
    const urlObj = new URL(targetUrl.toString());
    const isHttps = urlObj.protocol === 'https:';
    const httpModule = isHttps ? https : http;

    const options: http.RequestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: headers,
    };

    const proxyReq = httpModule.request(options, (proxyRes) => {
      const contentType = proxyRes.headers['content-type'] || '';
      
      // Set response status
      res.status(proxyRes.statusCode || 200);
      
      // Copy response headers
      Object.keys(proxyRes.headers).forEach(key => {
        const value = proxyRes.headers[key];
        if (value !== undefined) {
          res.setHeader(key, value);
        }
      });

      // --- Handle Streaming Response (SSE) ---
      if (contentType.includes('text/event-stream')) {
        console.log('[Stream] Detected SSE response, proxying stream...');
        
        // Critical: Set headers for SSE streaming
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering
        
        // Disable compression for streaming
        res.removeHeader('Content-Encoding');
        res.removeHeader('Content-Length');
        
        // Pipe the response directly - this is the key!
        proxyRes.pipe(res, { end: true });
        
        // Handle stream errors
        proxyRes.on('error', (err) => {
          console.error('[Stream Error]', err);
          if (!res.headersSent) {
            res.status(500).json({ error: 'Stream error' });
          } else {
            res.end();
          }
        });
        
        // Handle client disconnect
        req.on('close', () => {
          console.log('[Stream] Client disconnected, destroying proxy stream');
          proxyRes.destroy();
        });
        
        return;
      }

      // --- Handle Regular Response ---
      let chunks: Buffer[] = [];
      
      proxyRes.on('data', (chunk: Buffer) => {
        chunks.push(chunk);
      });
      
      proxyRes.on('end', () => {
        const data = Buffer.concat(chunks);
        
        if (contentType.includes('application/json')) {
          try {
            const parsed = JSON.parse(data.toString('utf-8'));
            res.json(parsed);
          } catch (err) {
            res.json({ error: 'Invalid JSON response' });
          }
        } else {
          res.send(data);
        }
      });
      
      proxyRes.on('error', (err) => {
        console.error('[Response Error]', err);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Proxy error' });
        }
      });
    });

    // Handle request errors
    proxyReq.on('error', (err) => {
      console.error('[Request Error]', err);
      if (!res.headersSent) {
        res.status(502).json({ error: 'Bad Gateway', detail: err.message });
      }
    });

    // Send request body
    if (body) {
      proxyReq.write(body);
    }
    
    proxyReq.end();

  } catch (error: any) {
    console.error('[Forward Error]', error);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Internal server error', detail: error.message });
    }
  }
}

// --- OpenAI-compatible routes ---
app.post('/v1/chat/completions', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/chat/completions');
});

app.post('/v1/completions', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/completions');
});

app.post('/v1/embeddings', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/embeddings');
});

app.get('/v1/models', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', '/v1/models');
});

app.post('/v1/responses', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/responses');
});

app.get('/v1/responses/:response_id', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', `/v1/responses/${req.params.response_id}`);
});

app.post('/v1/responses/:response_id/cancel', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', `/v1/responses/${req.params.response_id}/cancel`);
});

app.post('/v1/audio/transcriptions', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/audio/transcriptions');
});

app.post('/v1/audio/translations', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/audio/translations');
});

app.post('/v1/rerank', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/rerank');
});

// --- Internal + Utility Routes ---
app.get('/health', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', '/health');
});

app.get('/load', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', '/load');
});

app.post('/ping', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/ping');
});

app.get('/ping', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', '/ping');
});

app.post('/tokenize', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/tokenize');
});

app.post('/detokenize', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/detokenize');
});

app.post('/classify', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/classify');
});

app.post('/score', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/score');
});

app.post('/v1/score', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/v1/score');
});

app.post('/pooling', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/pooling');
});

app.post('/scale_elastic_ep', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/scale_elastic_ep');
});

app.post('/is_scaling_elastic_ep', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/is_scaling_elastic_ep');
});

app.post('/invocations', checkAuth, (req, res) => {
  forwardRequest(req, res, 'POST', '/invocations');
});

app.get('/metrics', checkAuth, (req, res) => {
  forwardRequest(req, res, 'GET', '/metrics');
});

// --- Health Check (Gateway + vLLM) ---
app.get('/healthz', async (req, res) => {
  const gatewayStatus = { gateway: 'ok' };
  
  try {
    const response = await fetch(`${VLLM_BASE}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    
    if (response.ok) {
      let vllmStatus: any;
      try {
        vllmStatus = await response.json();
      } catch {
        vllmStatus = { raw: await response.text() };
      }
      
      res.json({
        gateway: gatewayStatus,
        vllm: vllmStatus,
        vllm_status: 'ok',
      });
    } else {
      res.json({
        gateway: gatewayStatus,
        vllm_status: `unhealthy (${response.status})`,
      });
    }
  } catch (error: any) {
    res.json({
      gateway: gatewayStatus,
      vllm_status: `unreachable: ${error.name || 'Error'}`,
    });
  }
});

// --- Start Server ---
app.listen(GATEWAY_PORT, GATEWAY_HOST, () => {
  console.log(`🚀 vLLM Gateway v1.3.1`);
  console.log(`📍 Listening on ${GATEWAY_HOST}:${GATEWAY_PORT}`);
  console.log(`🔗 Proxying to ${VLLM_BASE}`);
  console.log(`🔑 API Keys configured: ${API_KEYS.length}`);
});

