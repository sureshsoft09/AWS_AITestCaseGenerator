# PowerShell script to create OpenSearch Serverless VECTORSEARCH collection for mem0 memory

$CollectionName = "medassure-agents-memory"
$Region = "us-east-1"

Write-Host "Creating VECTORSEARCH collection: $CollectionName" -ForegroundColor Green

# Create the collection
aws opensearchserverless create-collection `
    --name $CollectionName `
    --type VECTORSEARCH `
    --description "Vector search collection for MedAssureAI agent memory (mem0)" `
    --region $Region

Write-Host "`nCollection creation initiated. It may take a few minutes to become active." -ForegroundColor Yellow
Write-Host "`nTo check status, run:"
Write-Host "aws opensearchserverless batch-get-collection --names $CollectionName --region $Region" -ForegroundColor Cyan
Write-Host "`nOnce ACTIVE, get the endpoint:"
Write-Host "aws opensearchserverless batch-get-collection --names $CollectionName --region $Region --query 'collectionDetails[0].collectionEndpoint'" -ForegroundColor Cyan
Write-Host "`nThen update your .env file with the new endpoint." -ForegroundColor Yellow
