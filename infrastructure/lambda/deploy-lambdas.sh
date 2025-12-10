#!/bin/bash
# Deployment script for MedAssureAI Lambda functions
# This script packages and deploys Lambda functions to AWS

set -e

# Configuration
ENVIRONMENT=${1:-development}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Deploying Lambda functions for environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"

# Function to package and update Lambda
package_and_deploy() {
    local FUNCTION_DIR=$1
    local FUNCTION_NAME=$2
    
    echo "Packaging $FUNCTION_NAME..."
    
    cd "$FUNCTION_DIR"
    
    # Create deployment package
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt -t package/
        cd package
        zip -r ../deployment.zip .
        cd ..
        zip -g deployment.zip lambda_function.py
        rm -rf package
    else
        zip deployment.zip lambda_function.py
    fi
    
    # Update Lambda function
    echo "Updating Lambda function: $FUNCTION_NAME..."
    aws lambda update-function-code \
        --function-name "${ENVIRONMENT}-${FUNCTION_NAME}" \
        --zip-file fileb://deployment.zip \
        --region "$AWS_REGION"
    
    # Clean up
    rm deployment.zip
    
    echo "Successfully deployed $FUNCTION_NAME"
    cd - > /dev/null
}

# Deploy Textract Trigger Lambda
package_and_deploy \
    "$(dirname "$0")/textract-trigger" \
    "medassure-textract-trigger"

# Deploy Textract Completion Lambda
package_and_deploy \
    "$(dirname "$0")/textract-completion" \
    "medassure-textract-completion"

echo "All Lambda functions deployed successfully!"
