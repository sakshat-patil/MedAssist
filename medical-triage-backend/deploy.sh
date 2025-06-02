#!/bin/bash

# Create a temporary directory for packaging
mkdir -p package

# Install dependencies into the package directory
pip install -r requirements.txt -t package/

# Copy application code into the package directory
cp *.py package/
cp -r reports package/

# Create deployment package
cd package
zip -r ../deployment.zip .
cd ..

# Clean up
rm -rf package

echo "Deployment package created: deployment.zip"
echo "Upload this to AWS Lambda and set the handler to: lambda_function.handler" 