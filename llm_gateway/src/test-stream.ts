#!/usr/bin/env node
/**
 * Test script for streaming functionality
 * This tests the gateway's streaming capabilities
 */

import * as http from 'http';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';
const API_KEY = process.env.TEST_API_KEY || 'your-api-key-here';

async function testStreaming() {
  console.log('🧪 Testing Streaming...\n');
  
  const payload = JSON.stringify({
    model: 'Qwen/Qwen2.5-0.5B-Instruct-AWQ',
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

  return new Promise<void>((resolve, reject) => {
    const req = http.request(options, (res) => {
      console.log(`Status: ${res.statusCode}`);
      console.log(`Headers:`, JSON.stringify(res.headers, null, 2));
      console.log('\n--- Stream Output ---\n');

      let chunkCount = 0;
      let fullText = '';

      res.on('data', (chunk: Buffer) => {
        chunkCount++;
        const text = chunk.toString();
        process.stdout.write(text);
        fullText += text;
      });

      res.on('end', () => {
        console.log('\n\n--- Stream Complete ---');
        console.log(`Total chunks received: ${chunkCount}`);
        console.log(`Total bytes: ${Buffer.byteLength(fullText)}`);
        
        // Parse and display content
        try {
          const lines = fullText.split('\n').filter(l => l.trim().startsWith('data:'));
          console.log(`\nTotal data lines: ${lines.length}`);
          
          let assembledContent = '';
          for (const line of lines) {
            const jsonStr = line.replace(/^data:\s*/, '').trim();
            if (jsonStr === '[DONE]') {
              console.log('\n✅ Stream finished with [DONE] marker');
              break;
            }
            
            try {
              const json = JSON.parse(jsonStr);
              const content = json.choices?.[0]?.delta?.content || '';
              assembledContent += content;
            } catch (e) {
              // Skip invalid JSON
            }
          }
          
          console.log(`\n📝 Assembled Content:\n${assembledContent}`);
        } catch (error: any) {
          console.error('Error parsing stream:', error.message);
        }
        
        resolve();
      });

      res.on('error', (err) => {
        console.error('Response error:', err);
        reject(err);
      });
    });

    req.on('error', (err) => {
      console.error('Request error:', err);
      reject(err);
    });

    req.write(payload);
    req.end();
  });
}

async function testNonStreaming() {
  console.log('\n\n🧪 Testing Non-Streaming...\n');
  
  const payload = JSON.stringify({
    model: 'Qwen/Qwen2.5-0.5B-Instruct-AWQ',
    temperature: 0.7,
    max_tokens: 32,
    stream: false,
    messages: [
      { role: 'system', content: 'You are a helpful AI assistant.' },
      { role: 'user', content: 'Say hello in one sentence.' }
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

  return new Promise<void>((resolve, reject) => {
    const req = http.request(options, (res) => {
      console.log(`Status: ${res.statusCode}`);
      
      let data = '';

      res.on('data', (chunk: Buffer) => {
        data += chunk.toString();
      });

      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          console.log('\n--- Response ---');
          console.log(JSON.stringify(json, null, 2));
          console.log('\n✅ Non-streaming test passed');
          resolve();
        } catch (error: any) {
          console.error('Error parsing response:', error.message);
          console.log('Raw response:', data);
          reject(error);
        }
      });

      res.on('error', (err) => {
        console.error('Response error:', err);
        reject(err);
      });
    });

    req.on('error', (err) => {
      console.error('Request error:', err);
      reject(err);
    });

    req.write(payload);
    req.end();
  });
}

async function main() {
  console.log('🚀 LLM Gateway Streaming Test\n');
  console.log(`Gateway URL: ${GATEWAY_URL}`);
  console.log(`API Key: ${API_KEY.substring(0, 8)}...`);
  console.log('═'.repeat(60));

  try {
    await testStreaming();
    await testNonStreaming();
    
    console.log('\n\n═'.repeat(60));
    console.log('✅ All tests completed successfully!');
  } catch (error: any) {
    console.error('\n\n❌ Test failed:', error.message);
    process.exit(1);
  }
}

main();

