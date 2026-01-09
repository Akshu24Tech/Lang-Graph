"""
Utility functions for managing Long Term Memory (LTM) storage.
Provides functions to view, search, and delete user memories.
"""
from typing import List, Dict, Optional
from langgraph.store.base import BaseStore


def get_user_memories(store: BaseStore, user_id: str) -> List[Dict]:
    """
    Retrieve all memories for a specific user.
    
    Args:
        store: The LTM store instance (PostgresStore or InMemoryStore)
        user_id: The user identifier
        
    Returns:
        List of dictionaries containing memory information:
        [
            {
                "id": "memory_id",
                "data": "memory content",
                "namespace": ("user", user_id, "details")
            },
            ...
        ]
    """
    try:
        namespace = ("user", user_id, "details")
        items = store.search(namespace)
        
        memories = []
        for item in items:
            # Handle both dict and object-style value access
            if hasattr(item, 'value'):
                if isinstance(item.value, dict):
                    memory_data = item.value.get("data", "")
                else:
                    memory_data = str(item.value)
            else:
                memory_data = str(item)
            
            # Get the key/id
            memory_id = item.key if hasattr(item, 'key') else str(item)
            
            memories.append({
                "id": memory_id,
                "data": memory_data,
                "namespace": namespace
            })
        
        return memories
    except Exception as e:
        print(f"Error retrieving memories: {str(e)}")
        return []


def delete_memory(store: BaseStore, user_id: str, memory_id: str) -> bool:
    """
    Delete a specific memory by its ID.
    
    Args:
        store: The LTM store instance
        user_id: The user identifier
        memory_id: The ID of the memory to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        namespace = ("user", user_id, "details")
        store.delete(namespace, memory_id)
        return True
    except Exception as e:
        print(f"Error deleting memory: {str(e)}")
        return False


def delete_all_memories(store: BaseStore, user_id: str) -> bool:
    """
    Delete all memories for a specific user.
    
    Args:
        store: The LTM store instance
        user_id: The user identifier
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        namespace = ("user", user_id, "details")
        memories = get_user_memories(store, user_id)
        
        for memory in memories:
            store.delete(namespace, memory["id"])
        
        return True
    except Exception as e:
        print(f"Error deleting all memories: {str(e)}")
        return False


def search_memories(store: BaseStore, user_id: str, search_term: str) -> List[Dict]:
    """
    Search memories for a specific user by content.
    
    Args:
        store: The LTM store instance
        user_id: The user identifier
        search_term: The term to search for in memory content
        
    Returns:
        List of matching memories
    """
    all_memories = get_user_memories(store, user_id)
    search_term_lower = search_term.lower()
    
    matching_memories = [
        memory for memory in all_memories
        if search_term_lower in memory["data"].lower()
    ]
    
    return matching_memories


def get_memory_count(store: BaseStore, user_id: str) -> int:
    """
    Get the total number of memories for a user.
    
    Args:
        store: The LTM store instance
        user_id: The user identifier
        
    Returns:
        Number of memories
    """
    memories = get_user_memories(store, user_id)
    return len(memories)
