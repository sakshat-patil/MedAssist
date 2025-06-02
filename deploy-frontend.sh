#!/bin/bash

# Build the frontend
cd medical-triage-frontend
npm run build

# Get the S3 bucket name from CloudFormation stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name medical-triage --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)

# Upload the build to S3
aws s3 sync build/ s3://$BUCKET_NAME --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name medical-triage --query 'Stacks[0].Outputs[?OutputKey==`FrontendDistributionId`].OutputValue' --output text)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "Frontend deployed successfully!" 