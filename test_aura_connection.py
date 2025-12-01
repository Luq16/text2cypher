"""
Test script to verify Neo4j Aura DB connection
Run this to ensure your Aura credentials are configured correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Neo4j Aura DB Connection Test")
print("=" * 60)

# Check environment variables
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

print(f"\nConfiguration:")
print(f"  URI: {uri}")
print(f"  Username: {username}")
print(f"  Database: {database}")
print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")

if not all([uri, username, password]):
    print("\n❌ ERROR: Missing required environment variables!")
    print("Please configure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env")
    exit(1)

# Test connection
print("\n" + "=" * 60)
print("Testing Connection...")
print("=" * 60)

try:
    from src.utils import get_neo4j_connector

    connector = get_neo4j_connector()

    # Verify connectivity
    print("\n1. Testing basic connectivity...")
    if connector.verify_connectivity():
        print("   ✓ Successfully connected to Neo4j Aura!")
    else:
        print("   ✗ Connection failed!")
        exit(1)

    # Get database info
    print("\n2. Retrieving database schema...")
    schema = connector.get_schema()
    print(f"   ✓ Found {len(schema['node_labels'])} node types")
    print(f"   ✓ Found {len(schema['relationship_types'])} relationship types")

    if schema['node_labels']:
        print(f"\n   Sample node types: {', '.join(schema['node_labels'][:5])}")

    if schema['relationship_types']:
        print(f"   Sample relationships: {', '.join(schema['relationship_types'][:5])}")

    # Test query execution
    print("\n3. Testing query execution...")
    result = connector.execute_query("MATCH (n) RETURN count(n) as total_nodes LIMIT 1")
    if result:
        total_nodes = result[0]['total_nodes']
        print(f"   ✓ Query successful! Total nodes in database: {total_nodes:,}")

    # Close connection
    connector.close()

    print("\n" + "=" * 60)
    print("✓ All tests passed! Your Aura DB is ready to use.")
    print("=" * 60)
    print("\nYou can now run the main application:")
    print("  python -m src.main")

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements.txt")
    exit(1)

except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Verify your Aura instance is running (check console.neo4j.io)")
    print("  2. Check that your URI uses 'neo4j+s://' protocol")
    print("  3. Verify your password is correct (generated when DB was created)")
    print("  4. Ensure your IP is allowed in Aura firewall settings")
    print("  5. Check that database name is correct (usually 'neo4j')")
    exit(1)
