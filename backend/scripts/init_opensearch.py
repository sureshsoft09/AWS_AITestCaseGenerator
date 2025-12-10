"""
Initialize OpenSearch indexes for MedAssureAI.
Run this script after deploying OpenSearch cluster.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.opensearch_client import opensearch_client
from backend.logger import logger


def main():
    """Initialize OpenSearch indexes."""
    print("Initializing OpenSearch indexes...")
    
    # Check connection
    health = opensearch_client.health_check()
    print(f"OpenSearch Status: {health.get('status')}")
    
    if health.get('status') == 'unavailable':
        print("ERROR: Cannot connect to OpenSearch")
        print(f"Message: {health.get('message')}")
        return 1
    
    # Create session index
    print(f"\nCreating session index: {opensearch_client.SESSION_INDEX}")
    success = opensearch_client.ensure_index_exists()
    
    if success:
        print("✓ Session index created successfully")
    else:
        print("✗ Failed to create session index")
        return 1
    
    # Verify index
    print("\nVerifying index...")
    test_doc = {
        'session_id': 'test-session',
        'session_type': 'test',
        'project_id': 'test-project',
        'user_id': 'test-user',
        'context': {},
        'messages': [],
        'status': 'test',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z'
    }
    
    # Index test document
    if opensearch_client.index_document(test_doc, 'test-session'):
        print("✓ Test document indexed")
        
        # Retrieve test document
        retrieved = opensearch_client.get_document('test-session')
        if retrieved:
            print("✓ Test document retrieved")
            
            # Delete test document
            if opensearch_client.delete_document('test-session'):
                print("✓ Test document deleted")
            else:
                print("✗ Failed to delete test document")
        else:
            print("✗ Failed to retrieve test document")
    else:
        print("✗ Failed to index test document")
        return 1
    
    print("\n✓ OpenSearch initialization complete!")
    print(f"\nCluster Info:")
    print(f"  Status: {health.get('status')}")
    print(f"  Cluster: {health.get('cluster_name')}")
    print(f"  Nodes: {health.get('number_of_nodes')}")
    print(f"  Active Shards: {health.get('active_shards')}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
