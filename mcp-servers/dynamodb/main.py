"""
DynamoDB MCP Server
Provides Model Context Protocol tools for DynamoDB operations.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from config import config
from logger import logger
from dynamodb_client import dynamodb_client

# Load environment variables
load_dotenv()

app = FastAPI(
    title="DynamoDB MCP Server",
    description="Model Context Protocol server for DynamoDB operations",
    version="1.0.0"
)


# Request/Response Models
class PutItemRequest(BaseModel):
    """Request model for put_item."""
    item: Dict[str, Any] = Field(..., description="Item to store in DynamoDB")


class GetItemRequest(BaseModel):
    """Request model for get_item."""
    key: Dict[str, str] = Field(..., description="Primary key (PK and SK)")


class UpdateItemRequest(BaseModel):
    """Request model for update_item."""
    key: Dict[str, str] = Field(..., description="Primary key (PK and SK)")
    updates: Dict[str, Any] = Field(..., description="Fields to update")


class DeleteItemRequest(BaseModel):
    """Request model for delete_item."""
    key: Dict[str, str] = Field(..., description="Primary key (PK and SK)")


class QueryRequest(BaseModel):
    """Request model for query."""
    key_condition: str = Field(..., description="Key condition expression")
    expression_values: Dict[str, Any] = Field(..., description="Expression attribute values")
    index_name: Optional[str] = Field(None, description="GSI name")
    filter_expression: Optional[str] = Field(None, description="Filter expression")
    limit: Optional[int] = Field(None, description="Max items to return")
    last_evaluated_key: Optional[Dict[str, str]] = Field(None, description="For pagination")


class ScanRequest(BaseModel):
    """Request model for scan."""
    filter_expression: Optional[str] = Field(None, description="Filter expression")
    expression_values: Optional[Dict[str, Any]] = Field(None, description="Expression attribute values")
    limit: Optional[int] = Field(None, description="Max items to return")
    last_evaluated_key: Optional[Dict[str, str]] = Field(None, description="For pagination")


# Health Check Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "DynamoDB MCP Server",
        "status": "running",
        "version": "1.0.0",
        "table": config.DYNAMODB_TABLE_NAME
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dynamodb-mcp-server",
        "table": config.DYNAMODB_TABLE_NAME
    }


# MCP Tools
@app.post("/tools/put_item")
async def put_item(request: PutItemRequest):
    """
    Store an item in DynamoDB.
    
    Args:
        request: Item to store
        
    Returns:
        Success status and response
    """
    logger.info("put_item called")
    result = dynamodb_client.put_item(request.item)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/get_item")
async def get_item(request: GetItemRequest):
    """
    Retrieve an item from DynamoDB.
    
    Args:
        request: Primary key
        
    Returns:
        Item if found, None otherwise
    """
    logger.info(f"get_item called: {request.key}")
    result = dynamodb_client.get_item(request.key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/update_item")
async def update_item(request: UpdateItemRequest):
    """
    Update an item in DynamoDB.
    
    Args:
        request: Primary key and updates
        
    Returns:
        Updated item
    """
    logger.info(f"update_item called: {request.key}")
    result = dynamodb_client.update_item(request.key, request.updates)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/delete_item")
async def delete_item(request: DeleteItemRequest):
    """
    Delete an item from DynamoDB.
    
    Args:
        request: Primary key
        
    Returns:
        Success status
    """
    logger.info(f"delete_item called: {request.key}")
    result = dynamodb_client.delete_item(request.key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/query")
async def query(request: QueryRequest):
    """
    Query DynamoDB table or index.
    
    Args:
        request: Query parameters
        
    Returns:
        Query results with items and pagination info
    """
    logger.info(f"query called: {request.key_condition}")
    result = dynamodb_client.query(
        key_condition=request.key_condition,
        expression_values=request.expression_values,
        index_name=request.index_name,
        filter_expression=request.filter_expression,
        limit=request.limit,
        last_evaluated_key=request.last_evaluated_key
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/scan")
async def scan(request: ScanRequest):
    """
    Scan DynamoDB table.
    
    Args:
        request: Scan parameters
        
    Returns:
        Scan results with items and pagination info
    """
    logger.info("scan called")
    result = dynamodb_client.scan(
        filter_expression=request.filter_expression,
        expression_values=request.expression_values,
        limit=request.limit,
        last_evaluated_key=request.last_evaluated_key
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("DynamoDB MCP Server starting up")
    logger.info(f"Table: {config.DYNAMODB_TABLE_NAME}")
    logger.info(f"Region: {config.AWS_REGION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("DynamoDB MCP Server shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
