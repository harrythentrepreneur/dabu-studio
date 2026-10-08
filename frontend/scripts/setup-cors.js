#!/usr/bin/env node

/**
 * Setup CORS configuration for Digital Ocean Spaces bucket
 * Run this once to configure your bucket for browser uploads
 */

const { S3Client, PutBucketCorsCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const corsConfiguration = {
  CORSRules: [
    {
      AllowedHeaders: ['*'],
      AllowedMethods: ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
      AllowedOrigins: [
        'http://localhost:3000',
        'http://localhost:3001', 
        'http://localhost:3002',
        'https://dabu.ai',
        'https://*.dabu.ai'
      ],
      ExposeHeaders: ['ETag', 'x-amz-server-side-encryption'],
      MaxAgeSeconds: 3000
    }
  ]
};

async function setupCORS() {
  try {
    const s3Client = new S3Client({
      endpoint: process.env.DO_SPACES_ENDPOINT || 'https://sfo3.digitaloceanspaces.com',
      region: process.env.DO_SPACES_REGION || 'sfo3',
      credentials: {
        accessKeyId: process.env.DO_SPACES_KEY,
        secretAccessKey: process.env.DO_SPACES_SECRET,
      },
    });

    const command = new PutBucketCorsCommand({
      Bucket: process.env.DO_SPACES_BUCKET || '',
      CORSConfiguration: corsConfiguration,
    });

    await s3Client.send(command);
    console.log('✅ CORS configuration applied successfully!');
    console.log('Allowed origins:', corsConfiguration.CORSRules[0].AllowedOrigins);
  } catch (error) {
    console.error('❌ Failed to apply CORS configuration:', error);
    process.exit(1);
  }
}

setupCORS();