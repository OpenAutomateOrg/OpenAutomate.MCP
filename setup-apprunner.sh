#!/bin/bash

# OpenAutomate MCP Server - AWS App Runner Setup Script
echo "=========================================="
echo "Setting up AWS App Runner for MCP Server"
echo "=========================================="

# Variables
REGION="ap-southeast-1"
ACCOUNT_ID="961341552373"
ECR_REPOSITORY="openautomate-mcp"
SERVICE_NAME="openautomate-mcp-service"
API_URL="https://api.openautomate.io"

echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "ECR Repository: $ECR_REPOSITORY"
echo "Service Name: $SERVICE_NAME"
echo ""

# Step 1: Create ECR repository
echo "Step 1: Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ ECR repository ready"
else
    echo "✗ Failed to create ECR repository"
    exit 1
fi

# Step 2: Build and push Docker image
echo ""
echo "Step 2: Building and pushing Docker image..."
cd "$(dirname "$0")"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build image
docker build -t $ECR_REPOSITORY:latest .

# Tag for ECR
docker tag $ECR_REPOSITORY:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Push to ECR
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:latest

if [ $? -eq 0 ]; then
    echo "✓ Docker image pushed to ECR"
else
    echo "✗ Failed to push Docker image"
    exit 1
fi

# Step 3: Create App Runner service
echo ""
echo "Step 3: Creating App Runner service..."

# Check if service already exists
SERVICE_ARN=$(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text --region $REGION)

if [ -z "$SERVICE_ARN" ]; then
    echo "Creating new App Runner service..."
    
    aws apprunner create-service \
        --service-name $SERVICE_NAME \
        --source-configuration '{
            "ImageRepository": {
                "ImageIdentifier": "'$ACCOUNT_ID'.dkr.ecr.'$REGION'.amazonaws.com/'$ECR_REPOSITORY':latest",
                "ImageConfiguration": {
                    "Port": "8000",
                    "RuntimeEnvironmentVariables": {
                        "OPENAUTOMATE_API_BASE_URL": "'$API_URL'"
                    }
                },
                "ImageRepositoryType": "ECR"
            },
            "AutoDeploymentsEnabled": true
        }' \
        --instance-configuration '{
            "Cpu": "0.25 vCPU",
            "Memory": "0.5 GB"
        }' \
        --health-check-configuration '{
            "Protocol": "HTTP",
            "Path": "/health",
            "Interval": 10,
            "Timeout": 5,
            "HealthyThreshold": 1,
            "UnhealthyThreshold": 5
        }' \
        --region $REGION

    if [ $? -eq 0 ]; then
        echo "✓ App Runner service created successfully"
    else
        echo "✗ Failed to create App Runner service"
        exit 1
    fi
else
    echo "App Runner service already exists: $SERVICE_ARN"
    echo "Triggering deployment..."
    
    aws apprunner start-deployment \
        --service-arn $SERVICE_ARN \
        --region $REGION
    
    if [ $? -eq 0 ]; then
        echo "✓ Deployment triggered successfully"
    else
        echo "✗ Failed to trigger deployment"
        exit 1
    fi
fi

# Step 4: Wait for service to be ready and get URL
echo ""
echo "Step 4: Waiting for service to be ready..."
echo "This may take 3-5 minutes..."

sleep 30

for i in {1..20}; do
    SERVICE_STATUS=$(aws apprunner describe-service --service-arn $(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text --region $REGION) --query "Service.Status" --output text --region $REGION 2>/dev/null)
    
    if [ "$SERVICE_STATUS" = "RUNNING" ]; then
        echo "✓ Service is running!"
        break
    else
        echo "Service status: $SERVICE_STATUS (attempt $i/20)"
        sleep 15
    fi
done

# Get service URL
SERVICE_ARN=$(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text --region $REGION)
SERVICE_URL=$(aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceUrl" --output text --region $REGION)

echo ""
echo "=========================================="
echo "✅ MCP Server Deployment Complete!"
echo "=========================================="
echo "Service URL: https://$SERVICE_URL"
echo "Health Check: https://$SERVICE_URL/health"
echo "MCP Endpoint: https://$SERVICE_URL/sse"
echo ""
echo "For n8n integration, use:"
echo "SSE Endpoint: https://$SERVICE_URL/sse"
echo "=========================================="

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s "https://$SERVICE_URL/health" | jq . || echo "Health check endpoint not responding yet"
