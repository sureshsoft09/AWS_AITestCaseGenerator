"""
Initialize OpenSearch indexes for mem0_memory tool.
Run this script to create the necessary indexes for the mem0 memory system.
"""
import sys
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.config import agent_config
from agents.logger import logger


def create_mem0_index():
    """Create the mem0 index in OpenSearch."""
    
    print("Initializing mem0 OpenSearch index...")
    
    # Parse endpoint
    endpoint = agent_config.OPENSEARCH_ENDPOINT.replace('https://', '').replace('http://', '')
    
    if not endpoint:
        print("ERROR: OPENSEARCH_ENDPOINT not configured")
        return 1
    
    print(f"Connecting to OpenSearch: {endpoint}")
    
    # Check if serverless
    is_serverless = '.aoss.' in endpoint
    
    try:
        # Connect to OpenSearch
        if is_serverless:
            print("Detected OpenSearch Serverless, using AWS IAM authentication")
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, agent_config.AWS_REGION, 'aoss')
            
            client = OpenSearch(
                hosts=[{'host': endpoint, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30
            )
        else:
            print("Detected OpenSearch domain, using basic authentication")
            # Get credentials from agent config if available
            username = getattr(agent_config, 'OPENSEARCH_USERNAME', 'admin')
            password = getattr(agent_config, 'OPENSEARCH_PASSWORD', '')
            client = OpenSearch(
                hosts=[{'host': endpoint, 'port': 443}],
                http_auth=(username, password),
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30
            )
        
        print("✓ Connected to OpenSearch")
        
        # Define mem0 index name
        index_name = 'mem0_memories'
        
        # Check if index exists
        if client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists")
            return 0
        
        # Create index mapping for mem0 with vector support
        # Using 1024 dimensions for Titan Embed Text v2
        index_body = {
            'mappings': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'user_id': {'type': 'keyword'},
                    'content': {'type': 'text'},
                    'metadata': {'type': 'object', 'enabled': True},
                    'embedding': {
                        'type': 'knn_vector',
                        'dimension': 1024  # Titan embed text v2 dimension
                    },
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                    'hash': {'type': 'keyword'},
                    'memory_id': {'type': 'keyword'}
                }
            }
        }
        
        # Create the index
        print(f"Creating index: {index_name}")
        client.indices.create(index=index_name, body=index_body)
        print(f"✓ Index '{index_name}' created successfully")
        
        # Test write and read
        test_doc = {
            'id': 'test-memory-001',
            'user_id': 'test-user',
            'content': 'This is a test memory entry',
            'metadata': {'type': 'test', 'source': 'init_script'},
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'hash': 'test-hash',
            'memory_id': 'test-001'
        }
        
        print("\nTesting index operations...")
        
        # Index test document (without specifying ID for Serverless)
        response = client.index(index=index_name, body=test_doc, refresh=True)
        doc_id = response['_id']
        print(f"✓ Test document indexed with ID: {doc_id}")
        
        # Retrieve test document
        result = client.get(index=index_name, id=doc_id)
        if result['found']:
            print("✓ Test document retrieved")
        else:
            print("✗ Failed to retrieve test document")
            return 1
        
        # Delete test document
        client.delete(index=index_name, id=doc_id, refresh=True)
        print("✓ Test document deleted")
        
        print("\n✓ mem0 index initialization complete!")
        print(f"\nIndex: {index_name}")
        print(f"Endpoint: {endpoint}")
        print(f"Serverless: {is_serverless}")
        print(f"Vector dimensions: 1024 (Titan Embed Text v2)")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        logger.error(f"Failed to initialize mem0 index: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(create_mem0_index())
