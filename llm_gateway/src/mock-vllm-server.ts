#!/usr/bin/env node
/**
 * Mock vLLM Server
 * Simulates vLLM's streaming behavior for testing the gateway
 */

import * as http from 'http';

const PORT = parseInt(process.env.MOCK_VLLM_PORT || '8000', 10);
const HOST = process.env.MOCK_VLLM_HOST || '127.0.0.1';

// Simulate the exact SSE format from vLLM
function generateStreamResponse(req: http.IncomingMessage, res: http.ServerResponse, modelName: string) {
  const chunks = [
    { role: 'assistant', content: '' },
    { content: 'Transform' },
    { content: 'ers' },
    { content: ' are' },
    { content: ' complex' },
    { content: ' artificial' },
    { content: ' intelligence' },
    { content: ' models' },
    { content: ' used' },
    { content: ' for' },
    { content: ' natural' },
    { content: ' language' },
    { content: ' processing' },
    { content: ' tasks' },
    { content: ' like' },
    { content: ' translation' },
    { content: ',' },
    { content: ' summar' },
    { content: 'ization' },
    { content: ',' },
    { content: ' and' },
    { content: ' question' },
    { content: '-' },
    { content: 'ans' },
    { content: 'w' },
    { content: 'ering' },
    { content: '.' },
    { content: ' They' },
    { content: ' work' },
    { content: ' by' },
    { content: ' using' },
    { content: ' "' },
    { content: 'transform' },
    { content: 'ations' },
    { content: '"' },
    { content: ' to' },
    { content: ' process' },
    { content: ' large' },
    { content: ' amounts' },
    { content: ' of' },
    { content: ' text' },
    { content: ' data' },
    { content: '.\n\n' },
    { content: 'In' },
    { content: ' a' },
    { content: ' transformer' },
    { content: ' model' },
    { content: ',' },
    { content: ' each' },
    { content: ' input' },
    { content: ' piece' },
    { content: ' of' },
    { content: ' text' },
    { content: ' is' },
    { content: ' broken' },
    { content: ' down' },
    { content: ' into' },
    { content: ' smaller' },
    { content: ' parts' },
    { content: ' called' },
    { content: ' "' },
    { content: 'tokens' },
    { content: '".' },
    { content: ' These' },
    { content: ' tokens' },
  ];

  const chatCompletionId = `chatcmpl-${Date.now()}${Math.random().toString(36).substr(2, 9)}`;
  const created = Math.floor(Date.now() / 1000);

  let index = 0;

  const sendChunk = () => {
    if (index >= chunks.length) {
      // Send final chunk with finish_reason
      const finalChunk = {
        id: chatCompletionId,
        object: 'chat.completion.chunk',
        created: created,
        model: modelName,
        choices: [{
          index: 0,
          delta: { content: chunks[chunks.length - 1].content },
          logprobs: null,
          finish_reason: 'length',
          token_ids: null
        }]
      };
      res.write(`data: ${JSON.stringify(finalChunk)}\n\n`);
      
      // Send [DONE]
      res.write('data: [DONE]\n\n');
      res.end();
      console.log(`[Mock vLLM] ✅ Stream completed (${chunks.length} chunks)`);
      return;
    }

    const chunk = chunks[index];
    const delta: any = {};
    
    if (index === 0) {
      delta.role = chunk.role;
      delta.content = chunk.content;
    } else {
      delta.content = chunk.content;
    }

    const sseChunk = {
      id: chatCompletionId,
      object: 'chat.completion.chunk',
      created: created,
      model: modelName,
      choices: [{
        index: 0,
        delta: delta,
        logprobs: null,
        finish_reason: null,
        token_ids: null
      }]
    };

    res.write(`data: ${JSON.stringify(sseChunk)}\n\n`);
    index++;

    // Send next chunk with slight delay to simulate real streaming
    setTimeout(sendChunk, 20); // 20ms delay between chunks
  };

  sendChunk();
}

// Create mock vLLM server
const server = http.createServer((req, res) => {
  console.log(`[Mock vLLM] ${req.method} ${req.url}`);

  // Health check
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', message: 'Mock vLLM is healthy' }));
    return;
  }

  // Chat completions endpoint
  if (req.url === '/v1/chat/completions' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        
        // Check if streaming is requested
        if (data.stream === true) {
          console.log(`[Mock vLLM] 🌊 Starting SSE stream...`);
          res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          });
          generateStreamResponse(req, res, data.model || 'default-model');
        } else {
          // Non-streaming response
          console.log(`[Mock vLLM] 📦 Sending non-streaming response`);
          const response = {
            id: `chatcmpl-${Date.now()}`,
            object: 'chat.completion',
            created: Math.floor(Date.now() / 1000),
            model: data.model || 'default-model',
            choices: [{
              index: 0,
              message: {
                role: 'assistant',
                content: 'This is a test response from the mock vLLM server.'
              },
              finish_reason: 'stop'
            }],
            usage: {
              prompt_tokens: 10,
              completion_tokens: 12,
              total_tokens: 22
            }
          };
          const responseBody = JSON.stringify(response);
          res.writeHead(200, { 
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(responseBody).toString()
          });
          res.end(responseBody);
        }
      } catch (error: any) {
        console.error('[Mock vLLM] Error:', error.message);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid request body' }));
      }
    });
    return;
  }

  // Models endpoint
  if (req.url === '/v1/models' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      object: 'list',
      data: [{
        id: 'mock-model-1',
        object: 'model',
        created: Math.floor(Date.now() / 1000),
        owned_by: 'mock'
      }, {
        id: 'mock-model-2',
        object: 'model',
        created: Math.floor(Date.now() / 1000),
        owned_by: 'mock'
      }]
    }));
    return;
  }

  // 404 for unknown endpoints
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, HOST, () => {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('🤖 Mock vLLM Server');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`📍 Listening on ${HOST}:${PORT}`);
  console.log('');
  console.log('Available endpoints:');
  console.log('  GET  /health                  - Health check');
  console.log('  POST /v1/chat/completions     - Chat completions (streaming)');
  console.log('  GET  /v1/models               - List models');
  console.log('');
  console.log('✅ Ready to simulate vLLM streaming behavior');
  console.log('═══════════════════════════════════════════════════════════');
});

// Handle shutdown gracefully
process.on('SIGTERM', () => {
  console.log('\n[Mock vLLM] Shutting down...');
  server.close(() => {
    console.log('[Mock vLLM] Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n[Mock vLLM] Shutting down...');
  server.close(() => {
    console.log('[Mock vLLM] Server closed');
    process.exit(0);
  });
});

