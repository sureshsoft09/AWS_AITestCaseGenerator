"""
OpenSearch client for MedAssureAI session management.
Handles connection, index creation, and basic operations.
"""
import json
import time
from typing import Dict, Optional
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from opensearchpy.exceptions import OpenSearchException
from backend.config import config
from backend.logger import logger


class OpenSearchClient:
    """Client for OpenSearch operations."""
    
    # Session index name
    SESSION_INDEX = 'medassure_sessions'
    
    # Session index mapping
    SESSION_INDEX_MAPPING = {
        'mappings': {
            'properties': {
                'session_id': {'type': 'keyword'},
                'session_type': {'type': 'keyword'},
                'project_id': {'type': 'keyword'},
                'user_id': {'type': 'keyword'},
                'context': {'type': 'object', 'enabled': True},
                'messages': {
                    'type': 'nested',
                    'properties': {
                        'role': {'type': 'keyword'},
                        'content': {'type': 'text'},
                        'timestamp': {'type': 'date'}
                    }
                },
                'status': {'type': 'keyword'},
                'created_at': {'type': 'date'},
                'updated_at': {'type': 'date'},
                'expires_at': {'type': 'date'}
            }
        }
    }
    
    # Settings for regular OpenSearch domain (not used for Serverless)
    SESSION_INDEX_SETTINGS = {
        'number_of_shards': 1,
        'number_of_replicas': 1,
        'refresh_interval': '1s',
        'index': {
            'max_result_window': 10000
        }
    }
    
    def __init__(self):
        """Initialize OpenSearch client."""
        self.client = None
        self.is_serverless = False
        self._connect()
    
    def _connect(self):
        """Establish connection to OpenSearch."""
        try:
            # Parse endpoint (remove https:// if present)
            endpoint = config.OPENSEARCH_ENDPOINT.replace('https://', '').replace('http://', '')
            
            if not endpoint:
                logger.warning("OpenSearch endpoint not configured")
                return
            
            # Determine if this is OpenSearch Serverless (aoss) or regular OpenSearch
            self.is_serverless = '.aoss.' in endpoint
            
            if self.is_serverless:
                # Use AWS IAM authentication for OpenSearch Serverless
                logger.info("Detected OpenSearch Serverless, using AWS IAM authentication")
                
                # Get AWS credentials from boto3 session (uses credential chain)
                credentials = boto3.Session().get_credentials()
                auth = AWSV4SignerAuth(credentials, config.AWS_REGION, 'aoss')
                
                self.client = OpenSearch(
                    hosts=[{'host': endpoint, 'port': 443}],
                    http_auth=auth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection,
                    timeout=30
                )
            else:
                # Use basic authentication for regular OpenSearch domain
                logger.info("Detected OpenSearch domain, using basic authentication")
                
                self.client = OpenSearch(
                    hosts=[{'host': endpoint, 'port': 443}],
                    http_auth=(config.OPENSEARCH_USERNAME, config.OPENSEARCH_PASSWORD),
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection,
                    timeout=30
                )
            
            # Test connection
            # Note: OpenSearch Serverless doesn't support cluster.info() API
            if self.is_serverless:
                logger.info(
                    "Connected to OpenSearch Serverless",
                    extra={
                        'endpoint': endpoint,
                        'serverless': True
                    }
                )
            else:
                info = self.client.info()
                logger.info(
                    "Connected to OpenSearch",
                    extra={
                        'cluster_name': info.get('cluster_name', 'N/A'),
                        'version': info.get('version', {}).get('number', 'N/A'),
                        'serverless': False
                    }
                )
            
        except Exception as e:
            logger.error(
                "Failed to connect to OpenSearch",
                extra={'error': str(e), 'endpoint': config.OPENSEARCH_ENDPOINT}
            )
            self.client = None
    
    def ensure_index_exists(self, index_name: str = None) -> bool:
        """
        Ensure the session index exists, create if not.
        
        Args:
            index_name: Name of the index (defaults to SESSION_INDEX)
            
        Returns:
            True if index exists or was created successfully
        """
        if not self.client:
            logger.error("OpenSearch client not initialized")
            return False
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            # Check if index exists
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return True
            
            # Determine if this is serverless
            endpoint = config.OPENSEARCH_ENDPOINT
            is_serverless = '.aoss.' in endpoint
            
            # Create index body
            index_body = self.SESSION_INDEX_MAPPING.copy()
            
            # Add settings only for regular OpenSearch (not Serverless)
            if not is_serverless:
                index_body['settings'] = self.SESSION_INDEX_SETTINGS
            
            # Create index with mapping
            self.client.indices.create(
                index=index_name,
                body=index_body
            )
            
            logger.info(
                "Created OpenSearch index",
                extra={'index_name': index_name, 'serverless': is_serverless}
            )
            return True
            
        except OpenSearchException as e:
            logger.error(
                "Failed to create index",
                extra={'index_name': index_name, 'error': str(e)}
            )
            return False
    
    def index_document(
        self,
        document: Dict,
        doc_id: str,
        index_name: str = None
    ) -> bool:
        """
        Index a document in OpenSearch.
        
        Args:
            document: Document to index
            doc_id: Document ID
            index_name: Index name (defaults to SESSION_INDEX)
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("OpenSearch client not initialized - cannot index document")
            return False
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            # OpenSearch Serverless doesn't support refresh parameter
            index_params = {
                'index': index_name,
                'id': doc_id,
                'body': document
            }
            if not self.is_serverless:
                index_params['refresh'] = True
            
            response = self.client.index(**index_params)
            
            # For Serverless, add delay for eventual consistency
            if self.is_serverless:
                time.sleep(3.0)
            
            logger.info(
                "Indexed document",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'result': response.get('result')
                }
            )
            return True
            
        except OpenSearchException as e:
            logger.error(
                "Failed to index document - OpenSearch error",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
            return False
        except Exception as e:
            logger.error(
                "Failed to index document - unexpected error",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
            return False
    
    def get_document(
        self,
        doc_id: str,
        index_name: str = None
    ) -> Optional[Dict]:
        """
        Retrieve a document from OpenSearch.
        
        Args:
            doc_id: Document ID
            index_name: Index name (defaults to SESSION_INDEX)
            
        Returns:
            Document dict or None if not found
        """
        if not self.client:
            logger.error("OpenSearch client not initialized")
            return None
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            response = self.client.get(
                index=index_name,
                id=doc_id
            )
            
            return response.get('_source')
            
        except OpenSearchException as e:
            if 'not_found' in str(e).lower():
                logger.info(
                    "Document not found",
                    extra={'index_name': index_name, 'doc_id': doc_id}
                )
            else:
                logger.error(
                    "Failed to get document",
                    extra={
                        'index_name': index_name,
                        'doc_id': doc_id,
                        'error': str(e)
                    }
                )
            return None
    
    def update_document(
        self,
        doc_id: str,
        updates: Dict,
        index_name: str = None
    ) -> bool:
        """
        Update a document in OpenSearch.
        
        Args:
            doc_id: Document ID
            updates: Fields to update
            index_name: Index name (defaults to SESSION_INDEX)
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("OpenSearch client not initialized")
            return False
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            # OpenSearch Serverless doesn't support refresh parameter
            update_params = {
                'index': index_name,
                'id': doc_id,
                'body': {'doc': updates}
            }
            if not self.is_serverless:
                update_params['refresh'] = True
            
            response = self.client.update(**update_params)
            
            logger.info(
                "Updated document",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'result': response.get('result')
                }
            )
            return True
            
        except OpenSearchException as e:
            logger.error(
                "Failed to update document",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'error': str(e)
                }
            )
            return False
    
    def delete_document(
        self,
        doc_id: str,
        index_name: str = None
    ) -> bool:
        """
        Delete a document from OpenSearch.
        
        Args:
            doc_id: Document ID
            index_name: Index name (defaults to SESSION_INDEX)
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("OpenSearch client not initialized")
            return False
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            # OpenSearch Serverless doesn't support refresh parameter
            delete_params = {
                'index': index_name,
                'id': doc_id
            }
            if not self.is_serverless:
                delete_params['refresh'] = True
            
            response = self.client.delete(**delete_params)
            
            logger.info(
                "Deleted document",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'result': response.get('result')
                }
            )
            return True
            
        except OpenSearchException as e:
            logger.error(
                "Failed to delete document",
                extra={
                    'index_name': index_name,
                    'doc_id': doc_id,
                    'error': str(e)
                }
            )
            return False
    
    def search(
        self,
        query: Dict,
        index_name: str = None,
        size: int = 10
    ) -> list:
        """
        Search documents in OpenSearch.
        
        Args:
            query: OpenSearch query DSL
            index_name: Index name (defaults to SESSION_INDEX)
            size: Maximum number of results
            
        Returns:
            List of matching documents
        """
        if not self.client:
            logger.error("OpenSearch client not initialized")
            return []
        
        index_name = index_name or self.SESSION_INDEX
        
        try:
            response = self.client.search(
                index=index_name,
                body={'query': query, 'size': size}
            )
            
            hits = response.get('hits', {}).get('hits', [])
            documents = [hit['_source'] for hit in hits]
            
            logger.info(
                "Search completed",
                extra={
                    'index_name': index_name,
                    'results_count': len(documents)
                }
            )
            
            return documents
            
        except OpenSearchException as e:
            logger.error(
                "Search failed",
                extra={
                    'index_name': index_name,
                    'error': str(e)
                }
            )
            return []
    
    def health_check(self) -> Dict:
        """
        Check OpenSearch cluster health.
        
        Returns:
            Health status dict
        """
        if not self.client:
            return {
                'status': 'unavailable',
                'message': 'OpenSearch client not initialized'
            }
        
        try:
            health = self.client.cluster.health()
            return {
                'status': health.get('status'),
                'cluster_name': health.get('cluster_name'),
                'number_of_nodes': health.get('number_of_nodes'),
                'active_shards': health.get('active_shards')
            }
            
        except OpenSearchException as e:
            logger.error(
                "Health check failed",
                extra={'error': str(e)}
            )
            return {
                'status': 'error',
                'message': str(e)
            }


# Create singleton instance
opensearch_client = OpenSearchClient()
