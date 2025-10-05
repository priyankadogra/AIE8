"""
Configuration file for the Custom Semantic Chunker

Adjust these parameters to fine-tune your chunking strategy.
"""

# Chunking Strategy Configuration
CHUNKING_CONFIG = {
    # Semantic similarity threshold (0.0 to 1.0)
    # Higher values = more strict similarity requirements
    # Lower values = more lenient grouping
    "similarity_threshold": 0.7,
    
    # Maximum characters per chunk
    # Adjust based on your model's context window
    "max_chunk_size": 1000,
    
    # Minimum characters per chunk
    # Ensures no chunk is smaller than a single sentence
    "min_chunk_size": 50,
    
    # Overlap between consecutive chunks
    # 0 = no overlap, higher values = more overlap
    "chunk_overlap": 0,
    
    # Embedding model configuration
    "embedding_model": {
        "model": "text-embedding-3-small",  # OpenAI embedding model
        "batch_size": 100  # Process embeddings in batches
    }
}

# Alternative configurations for different use cases
CONFIGURATIONS = {
    "conservative": {
        "similarity_threshold": 0.8,
        "max_chunk_size": 800,
        "min_chunk_size": 100,
        "chunk_overlap": 50
    },
    
    "aggressive": {
        "similarity_threshold": 0.6,
        "max_chunk_size": 1500,
        "min_chunk_size": 30,
        "chunk_overlap": 0
    },
    
    "balanced": {
        "similarity_threshold": 0.7,
        "max_chunk_size": 1000,
        "min_chunk_size": 50,
        "chunk_overlap": 0
    }
}

def get_chunking_config(config_name: str = "balanced") -> dict:
    """
    Get chunking configuration by name.
    
    Args:
        config_name: Name of the configuration ("conservative", "aggressive", "balanced")
        
    Returns:
        Dictionary with chunking parameters
    """
    return CONFIGURATIONS.get(config_name, CONFIGURATIONS["balanced"])

def create_chunker_from_config(config_name: str = "balanced"):
    """
    Create a CustomSemanticChunker using a predefined configuration.
    
    Args:
        config_name: Name of the configuration to use
        
    Returns:
        Configured CustomSemanticChunker instance
    """
    from semantic_chunker import create_semantic_chunker
    
    config = get_chunking_config(config_name)
    return create_semantic_chunker(**config)
