"""
DynamoDB client with connection pooling and error handling.
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Any, Optional
from config import config
from logger import logger


class DynamoDBClient:
    """DynamoDB client wrapper with connection pooling and retry logic."""
    
    def __init__(self):
        """Initialize DynamoDB client."""
        session_config = {
            'region_name': config.AWS_REGION
        }
        
        if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            session_config['aws_access_key_id'] = config.AWS_ACCESS_KEY_ID
            session_config['aws_secret_access_key'] = config.AWS_SECRET_ACCESS_KEY
        
        self.session = boto3.Session(**session_config)
        
        client_config = {}
        if config.DYNAMODB_ENDPOINT_URL:
            client_config['endpoint_url'] = config.DYNAMODB_ENDPOINT_URL
        
        self.client = self.session.client('dynamodb', **client_config)
        self.table_name = config.DYNAMODB_TABLE_NAME
        
        logger.info(f"DynamoDB client initialized for table: {self.table_name}")
    
    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Put an item into DynamoDB.
        
        Args:
            item: Item to store (Python dict format)
            
        Returns:
            Response from DynamoDB
        """
        try:
            response = self.client.put_item(
                TableName=self.table_name,
                Item=self._python_to_dynamodb(item)
            )
            logger.info(f"Item stored successfully: PK={item.get('PK')}, SK={item.get('SK')}")
            return {"success": True, "response": response}
        except ClientError as e:
            logger.error(f"Error putting item: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error putting item: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_item(self, key: Dict[str, str]) -> Dict[str, Any]:
        """
        Get an item from DynamoDB.
        
        Args:
            key: Primary key (e.g., {"PK": "PROJECT#123", "SK": "EPIC#E001"})
            
        Returns:
            Item if found, None otherwise
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key=self._python_to_dynamodb(key)
            )
            
            if 'Item' in response:
                item = self._dynamodb_to_python(response['Item'])
                logger.info(f"Item retrieved: PK={key.get('PK')}, SK={key.get('SK')}")
                return {"success": True, "item": item}
            else:
                logger.info(f"Item not found: PK={key.get('PK')}, SK={key.get('SK')}")
                return {"success": True, "item": None}
        except ClientError as e:
            logger.error(f"Error getting item: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error getting item: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_item(self, key: Dict[str, str], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an item in DynamoDB.
        
        Args:
            key: Primary key
            updates: Fields to update
            
        Returns:
            Updated item
        """
        try:
            # Build update expression
            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}
            
            for field, value in updates.items():
                # Use attribute names to handle reserved keywords
                attr_name = f"#{field}"
                attr_value = f":{field}"
                update_expr_parts.append(f"{attr_name} = {attr_value}")
                expr_attr_names[attr_name] = field
                expr_attr_values[attr_value] = value
            
            update_expression = "SET " + ", ".join(update_expr_parts)
            
            response = self.client.update_item(
                TableName=self.table_name,
                Key=self._python_to_dynamodb(key),
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=self._python_to_dynamodb(expr_attr_values),
                ReturnValues="ALL_NEW"
            )
            
            updated_item = self._dynamodb_to_python(response['Attributes'])
            logger.info(f"Item updated: PK={key.get('PK')}, SK={key.get('SK')}")
            return {"success": True, "item": updated_item}
        except ClientError as e:
            logger.error(f"Error updating item: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error updating item: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_item(self, key: Dict[str, str]) -> Dict[str, Any]:
        """
        Delete an item from DynamoDB.
        
        Args:
            key: Primary key
            
        Returns:
            Success status
        """
        try:
            self.client.delete_item(
                TableName=self.table_name,
                Key=self._python_to_dynamodb(key)
            )
            logger.info(f"Item deleted: PK={key.get('PK')}, SK={key.get('SK')}")
            return {"success": True}
        except ClientError as e:
            logger.error(f"Error deleting item: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error deleting item: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def query(
        self,
        key_condition: str,
        expression_values: Dict[str, Any],
        index_name: Optional[str] = None,
        filter_expression: Optional[str] = None,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query DynamoDB table or index.
        
        Args:
            key_condition: Key condition expression
            expression_values: Expression attribute values
            index_name: GSI name (optional)
            filter_expression: Filter expression (optional)
            limit: Max items to return (optional)
            last_evaluated_key: For pagination (optional)
            
        Returns:
            Query results with items and pagination info
        """
        try:
            query_params = {
                'TableName': self.table_name,
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': self._python_to_dynamodb(expression_values)
            }
            
            if index_name:
                query_params['IndexName'] = index_name
            if filter_expression:
                query_params['FilterExpression'] = filter_expression
            if limit:
                query_params['Limit'] = limit
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = self._python_to_dynamodb(last_evaluated_key)
            
            response = self.client.query(**query_params)
            
            items = [self._dynamodb_to_python(item) for item in response.get('Items', [])]
            
            result = {
                "success": True,
                "items": items,
                "count": response.get('Count', 0),
                "scanned_count": response.get('ScannedCount', 0)
            }
            
            if 'LastEvaluatedKey' in response:
                result['last_evaluated_key'] = self._dynamodb_to_python(response['LastEvaluatedKey'])
            
            logger.info(f"Query executed: returned {len(items)} items")
            return result
        except ClientError as e:
            logger.error(f"Error querying table: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error querying table: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def scan(
        self,
        filter_expression: Optional[str] = None,
        expression_values: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scan DynamoDB table.
        
        Args:
            filter_expression: Filter expression (optional)
            expression_values: Expression attribute values (optional)
            limit: Max items to return (optional)
            last_evaluated_key: For pagination (optional)
            
        Returns:
            Scan results with items and pagination info
        """
        try:
            scan_params = {'TableName': self.table_name}
            
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            if expression_values:
                scan_params['ExpressionAttributeValues'] = self._python_to_dynamodb(expression_values)
            if limit:
                scan_params['Limit'] = limit
            if last_evaluated_key:
                scan_params['ExclusiveStartKey'] = self._python_to_dynamodb(last_evaluated_key)
            
            response = self.client.scan(**scan_params)
            
            items = [self._dynamodb_to_python(item) for item in response.get('Items', [])]
            
            result = {
                "success": True,
                "items": items,
                "count": response.get('Count', 0),
                "scanned_count": response.get('ScannedCount', 0)
            }
            
            if 'LastEvaluatedKey' in response:
                result['last_evaluated_key'] = self._dynamodb_to_python(response['LastEvaluatedKey'])
            
            logger.info(f"Scan executed: returned {len(items)} items")
            return result
        except ClientError as e:
            logger.error(f"Error scanning table: {e.response['Error']['Message']}")
            return {"success": False, "error": e.response['Error']['Message']}
        except Exception as e:
            logger.error(f"Unexpected error scanning table: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _python_to_dynamodb(self, obj: Any) -> Any:
        """Convert Python object to DynamoDB format."""
        if isinstance(obj, dict):
            return {k: self._python_to_dynamodb(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return {'L': [self._python_to_dynamodb(item) for item in obj]}
        elif isinstance(obj, str):
            return {'S': obj}
        elif isinstance(obj, (int, float)):
            return {'N': str(obj)}
        elif isinstance(obj, bool):
            return {'BOOL': obj}
        elif obj is None:
            return {'NULL': True}
        else:
            return {'S': str(obj)}
    
    def _dynamodb_to_python(self, obj: Any) -> Any:
        """Convert DynamoDB format to Python object."""
        if isinstance(obj, dict):
            if len(obj) == 1:
                key, value = list(obj.items())[0]
                if key == 'S':
                    return value
                elif key == 'N':
                    return float(value) if '.' in value else int(value)
                elif key == 'BOOL':
                    return value
                elif key == 'NULL':
                    return None
                elif key == 'L':
                    return [self._dynamodb_to_python(item) for item in value]
                elif key == 'M':
                    return {k: self._dynamodb_to_python(v) for k, v in value.items()}
            return {k: self._dynamodb_to_python(v) for k, v in obj.items()}
        return obj


# Singleton instance
dynamodb_client = DynamoDBClient()
