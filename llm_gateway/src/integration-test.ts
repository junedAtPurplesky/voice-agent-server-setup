#!/usr/bin/env node
/**
 * Integration Test Suite
 * Tests the gateway against mock vLLM server
 */

import * as http from 'http';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';
const API_KEY = process.env.TEST_API_KEY || 'test-key';

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  duration?: number;
}

const results: TestResult[] = [];

function reportTest(result: TestResult) {
  results.push(result);
  const icon = result.passed ? '✅' : '❌';
  const duration = result.duration ? ` (${result.duration}ms)` : '';
  console.log(`${icon} ${result.name}${duration}`);
  if (!result.passed) {
    console.log(`   └─ ${result.message}`);
  }
}

// Test 1: Gateway Health Check
async function testGatewayHealth(): Promise<TestResult> {
  const startTime = Date.now();
  return new Promise((resolve) => {
    const url = new URL('/healthz', GATEWAY_URL);
    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const passed = res.statusCode === 200 && json.gateway?.gateway === 'ok';
          resolve({
            name: 'Gateway Health Check',
            passed,
            message: passed ? 'Gateway is healthy' : `Gateway unhealthy: ${data}`,
            duration: Date.now() - startTime
          });
        } catch (error: any) {
          resolve({
            name: 'Gateway Health Check',
            passed: false,
            message: `Failed to parse health response: ${error.message}`,
            duration: Date.now() - startTime
          });
        }
      });
    }).on('error', (error) => {
      resolve({
        name: 'Gateway Health Check',
        passed: false,
        message: `Connection error: ${error.message}`,
        duration: Date.now() - startTime
      });
    });
  });
}

// Test 2: Streaming Response
async function testStreamingResponse(): Promise<TestResult> {
  const startTime = Date.now();
  let firstChunkTime = 0;
  
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      model: 'test-model',  // Model-agnostic - gateway forwards any model name
      temperature: 0.7,
      max_tokens: 64,
      stream: true,
      messages: [
        { role: 'system', content: 'You are a helpful AI assistant.' },
        { role: 'user', content: 'Explain transformers in simple terms.' }
      ]
    });

    const url = new URL('/v1/chat/completions', GATEWAY_URL);
    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Authorization': `Bearer ${API_KEY}`,
      },
    };

    const req = http.request(options, (res) => {
      if (res.statusCode !== 200) {
        resolve({
          name: 'Streaming Response',
          passed: false,
          message: `HTTP ${res.statusCode}`,
          duration: Date.now() - startTime
        });
        return;
      }

      // Check headers
      const contentType = res.headers['content-type'] || '';
      if (!contentType.includes('text/event-stream')) {
        resolve({
          name: 'Streaming Response',
          passed: false,
          message: `Wrong content-type: ${contentType}`,
          duration: Date.now() - startTime
        });
        return;
      }

      let chunks = 0;
      let fullData = '';
      let hasRoleChunk = false;
      let hasContentChunks = false;
      let hasDoneMarker = false;

      res.on('data', (chunk: Buffer) => {
        if (chunks === 0) {
          firstChunkTime = Date.now() - startTime;
        }
        chunks++;
        fullData += chunk.toString();
        
        // Parse to check structure
        const lines = chunk.toString().split('\n').filter(l => l.trim().startsWith('data:'));
        for (const line of lines) {
          const jsonStr = line.replace(/^data:\s*/, '').trim();
          if (jsonStr === '[DONE]') {
            hasDoneMarker = true;
            continue;
          }
          
          try {
            const json = JSON.parse(jsonStr);
            if (json.choices?.[0]?.delta?.role) {
              hasRoleChunk = true;
            }
            if (json.choices?.[0]?.delta?.content) {
              hasContentChunks = true;
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      });

      res.on('end', () => {
        const duration = Date.now() - startTime;
        const passed = chunks > 10 && hasRoleChunk && hasContentChunks && hasDoneMarker && firstChunkTime < 100;
        
        resolve({
          name: 'Streaming Response',
          passed,
          message: passed 
            ? `Received ${chunks} chunks, first chunk in ${firstChunkTime}ms` 
            : `Failed: chunks=${chunks}, hasRole=${hasRoleChunk}, hasContent=${hasContentChunks}, hasDone=${hasDoneMarker}, firstChunk=${firstChunkTime}ms`,
          duration
        });
      });

      res.on('error', (error) => {
        resolve({
          name: 'Streaming Response',
          passed: false,
          message: `Stream error: ${error.message}`,
          duration: Date.now() - startTime
        });
      });
    });

    req.on('error', (error) => {
      resolve({
        name: 'Streaming Response',
        passed: false,
        message: `Request error: ${error.message}`,
        duration: Date.now() - startTime
      });
    });

    req.write(payload);
    req.end();
  });
}

// Test 3: Non-Streaming Response
async function testNonStreamingResponse(): Promise<TestResult> {
  const startTime = Date.now();
  
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      model: 'test-model',  // Model-agnostic - gateway forwards any model name
      temperature: 0.7,
      max_tokens: 32,
      stream: false,
      messages: [
        { role: 'user', content: 'Say hello' }
      ]
    });

    const url = new URL('/v1/chat/completions', GATEWAY_URL);
    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Authorization': `Bearer ${API_KEY}`,
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const passed = res.statusCode === 200 
            && json.choices?.[0]?.message?.content 
            && json.object === 'chat.completion';
          
          resolve({
            name: 'Non-Streaming Response',
            passed,
            message: passed ? 'Got valid completion' : `Invalid response: ${data.substring(0, 100)}`,
            duration: Date.now() - startTime
          });
        } catch (error: any) {
          resolve({
            name: 'Non-Streaming Response',
            passed: false,
            message: `Parse error: ${error.message}`,
            duration: Date.now() - startTime
          });
        }
      });
    });

    req.on('error', (error) => {
      resolve({
        name: 'Non-Streaming Response',
        passed: false,
        message: `Request error: ${error.message}`,
        duration: Date.now() - startTime
      });
    });

    req.write(payload);
    req.end();
  });
}

// Test 4: Authentication Test
async function testAuthentication(): Promise<TestResult> {
  const startTime = Date.now();
  
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      model: 'test',
      messages: []
    });

    const url = new URL('/v1/chat/completions', GATEWAY_URL);
    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Authorization': 'Bearer invalid-key-12345',
      },
    };

    const req = http.request(options, (res) => {
      const passed = res.statusCode === 403 || res.statusCode === 401;
      resolve({
        name: 'Authentication Rejection',
        passed,
        message: passed ? 'Invalid key rejected' : `Wrong status: ${res.statusCode}`,
        duration: Date.now() - startTime
      });
    });

    req.on('error', (error) => {
      resolve({
        name: 'Authentication Rejection',
        passed: false,
        message: `Request error: ${error.message}`,
        duration: Date.now() - startTime
      });
    });

    req.write(payload);
    req.end();
  });
}

// Test 5: First Chunk Latency Test
async function testFirstChunkLatency(): Promise<TestResult> {
  const startTime = Date.now();
  let firstChunkTime = 0;
  
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      model: 'test-model',  // Model-agnostic - gateway forwards any model name
      stream: true,
      messages: [{ role: 'user', content: 'Hi' }]
    });

    const url = new URL('/v1/chat/completions', GATEWAY_URL);
    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'Authorization': `Bearer ${API_KEY}`,
      },
    };

    const req = http.request(options, (res) => {
      let receivedFirstChunk = false;
      
      res.on('data', (chunk: Buffer) => {
        if (!receivedFirstChunk) {
          firstChunkTime = Date.now() - startTime;
          receivedFirstChunk = true;
          res.destroy(); // We only need first chunk
          
          const passed = firstChunkTime < 150; // Should be under 150ms
          resolve({
            name: 'First Chunk Latency',
            passed,
            message: `${firstChunkTime}ms ${passed ? '(fast!)' : '(too slow)'}`,
            duration: firstChunkTime
          });
        }
      });

      res.on('error', () => {
        // Expected when we destroy the connection
      });
    });

    req.on('error', (error) => {
      if (firstChunkTime > 0) return; // Already resolved
      resolve({
        name: 'First Chunk Latency',
        passed: false,
        message: `Request error: ${error.message}`,
        duration: Date.now() - startTime
      });
    });

    req.write(payload);
    req.end();
  });
}

// Main test runner
async function runTests() {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('🧪 Gateway Integration Test Suite');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`Gateway URL: ${GATEWAY_URL}`);
  console.log(`API Key: ${API_KEY.substring(0, 8)}...`);
  console.log('');

  console.log('Running tests...\n');

  // Run tests sequentially
  reportTest(await testGatewayHealth());
  reportTest(await testStreamingResponse());
  reportTest(await testNonStreamingResponse());
  reportTest(await testAuthentication());
  reportTest(await testFirstChunkLatency());

  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('📊 Test Results');
  console.log('═══════════════════════════════════════════════════════════');

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const total = results.length;

  console.log(`Total:  ${total}`);
  console.log(`Passed: ${passed} ✅`);
  console.log(`Failed: ${failed} ${failed > 0 ? '❌' : '✅'}`);
  console.log('');

  if (failed === 0) {
    console.log('🎉 All tests passed! Gateway is working correctly.');
    console.log('✅ Safe to deploy to cloud!');
  } else {
    console.log('❌ Some tests failed. Please fix issues before deploying.');
    process.exit(1);
  }
}

runTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

