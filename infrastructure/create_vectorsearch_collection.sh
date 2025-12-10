#!/bin/bash
# Create OpenSearch Serverless VECTORSEARCH collection for mem0 memory

COLLECTION_NAME="medassure-memory"
REGION="us-east-1"

echo "Creating VECTORSEARCH collection: $COLLECTION_NAME"

# Create the collection
aws opensearchserverless create-collection \
    --name "$COLLECTION_NAME" \
    --type VECTORSEARCH \
    --description "Vector search collection for MedAssureAI agent memory (mem0)" \
    --region "$REGION"

echo "Collection creation initiated. It may take a few minutes to become active."
echo ""
echo "To check status, run:"
echo "aws opensearchserverless batch-get-collection --names $COLLECTION_NAME --region $REGION"
echo ""
echo "Once ACTIVE, update your .env file with the new endpoint:"
echo "OPENSEARCH_ENDPOINT=https://<collection-id>.$REGION.aoss.amazonaws.com"
