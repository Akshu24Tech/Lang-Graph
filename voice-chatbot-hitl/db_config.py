"""
Database configuration for LTM (Long Term Memory) storage.
Supports both PostgreSQL (persistent) and InMemory (development) stores.
"""
import os
from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

load_dotenv()

# Global store instance and context manager to reuse across the application
_ltm_store_instance = None
_ltm_context_manager = None

def get_ltm_store() -> BaseStore:
    """
    Get the LTM store based on environment configuration.
    Uses singleton pattern to ensure the same store instance is reused.
    
    Returns:
        BaseStore: PostgresStore if DATABASE_URL is set, otherwise InMemoryStore
        
    Environment Variables:
        DATABASE_URL: PostgreSQL connection string
            Format: postgresql://user:password@host:port/database?sslmode=disable
            Example: postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable
    """
    global _ltm_store_instance, _ltm_context_manager
    
    # Return cached instance if available
    if _ltm_store_instance is not None:
        return _ltm_store_instance
    
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        try:
            from langgraph.store.postgres import PostgresStore
            
            # PostgresStore.from_conn_string() returns a context manager
            # We need to enter it to get the actual store instance
            # Keep the context manager alive for the application lifetime
            _ltm_context_manager = PostgresStore.from_conn_string(database_url)
            store = _ltm_context_manager.__enter__()
            
            # Setup database tables (idempotent - safe to call multiple times)
            # This creates the necessary tables if they don't exist
            try:
                store.setup()
                print("✅ Database tables initialized")
            except Exception as e:
                # If setup fails, it might already be set up, which is fine
                # Some errors are expected if tables already exist
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Database setup note: {str(e)}")
            
            print("✅ Using PostgreSQL for LTM (Long Term Memory) - persistent storage")
            _ltm_store_instance = store
            return store
        except ImportError:
            print("⚠️  PostgreSQL dependencies not installed. Install with: pip install 'psycopg[binary,pool]' langgraph-checkpoint-postgres")
            print("📦 Falling back to InMemoryStore (non-persistent)")
            _ltm_store_instance = InMemoryStore()
            return _ltm_store_instance
        except Exception as e:
            print(f"⚠️  Error connecting to PostgreSQL: {str(e)}")
            print("📦 Falling back to InMemoryStore (non-persistent)")
            _ltm_store_instance = InMemoryStore()
            return _ltm_store_instance
    else:
        print("📦 Using InMemoryStore for LTM (non-persistent) - set DATABASE_URL for PostgreSQL")
        _ltm_store_instance = InMemoryStore()
        return _ltm_store_instance
