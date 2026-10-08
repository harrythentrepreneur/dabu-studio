#!/usr/bin/env node

/**
 * Setup bucket policy for Digital Ocean Spaces
 * Makes uploaded files publicly readable
 */

const { S3Client, PutBucketPolicyCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const bucketName = process.env.DO_SPACES_BUCKET || '';

const bucketPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Sid: 'PublicReadGetObject',
      Effect: 'Allow',
      Principal: '*',
      Action: 's3:GetObject',
      Resource: `arn:aws:s3:::${bucketName}/uploads/*`
    }
  ]
};

async function setupBucketPolicy() {
  try {
    const s3Client = new S3Client({
      endpoint: process.env.DO_SPACES_ENDPOINT || 'https://sfo3.digitaloceanspaces.com',
      region: process.env.DO_SPACES_REGION || 'sfo3',
      credentials: {
        accessKeyId: process.env.DO_SPACES_KEY,
        secretAccessKey: process.env.DO_SPACES_SECRET,
      },
    });

    const command = new PutBucketPolicyCommand({
      Bucket: bucketName,
      Policy: JSON.stringify(bucketPolicy),
    });

    await s3Client.send(command);
    console.log('✅ Bucket policy applied successfully!');
    console.log('Files in uploads/ folder will be publicly readable');
  } catch (error) {
    console.error('❌ Failed to apply bucket policy:', error);
    if (error.Code === 'AccessDenied') {
      console.log('\nNote: You may need to configure this in the DO Spaces dashboard instead.');
      console.log('Go to Settings > Permissions and make the bucket public or configure the policy there.');
    }
    process.exit(1);
  }
}

setupBucketPolicy();