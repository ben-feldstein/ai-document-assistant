"""Vector embedding service using sentence-transformers."""

import asyncio
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from api.services.cache import cache_service
from api.utils.config import settings


class VectorizerService:
    """Service for generating and managing text embeddings."""
    
    def __init__(self):
        self.model_name = settings.embed_model
        self.model: Optional[SentenceTransformer] = None
        self.embed_dims = settings.embed_dims
        self.batch_size = settings.embed_batch_size
        
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for a single text string."""
        # Check cache first
        cached_embedding = await cache_service.get_embedding_cache(text)
        if cached_embedding:
            return cached_embedding
        
        # Generate new embedding
        embedding = await self._generate_embedding(text)
        if embedding:
            # Cache the embedding
            await cache_service.set_embedding_cache(text, embedding)
        
        return embedding
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for a batch of texts."""
        if not texts:
            return []
        
        # Check cache for each text
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached = await cache_service.get_embedding_cache(text)
            if cached:
                embeddings.append(cached)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await self._generate_embeddings_batch(uncached_texts)
            
            # Cache new embeddings and update results
            for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                if embedding:
                    await cache_service.set_embedding_cache(text, embedding)
                    embeddings[uncached_indices[i]] = embedding
        
        return embeddings
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text string."""
        try:
            # Ensure model is loaded
            await self._ensure_model_loaded()
            
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.model.encode, 
                text
            )
            
            # Convert to list and normalize
            embedding_list = embedding.tolist()
            return self._normalize_embedding(embedding_list)
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts."""
        try:
            # Ensure model is loaded
            await self._ensure_model_loaded()
            
            # Run batch embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                texts,
                batch_size=self.batch_size
            )
            
            # Convert to list format and normalize
            results = []
            for embedding in embeddings:
                embedding_list = embedding.tolist()
                normalized = self._normalize_embedding(embedding_list)
                results.append(normalized)
            
            return results
            
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    async def _ensure_model_loaded(self):
        """Ensure the embedding model is loaded."""
        if self.model is None:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                SentenceTransformer,
                self.model_name
            )
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding vector to unit length."""
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            normalized = embedding_array / norm
            return normalized.tolist()
        return embedding
    
    async def get_model_info(self) -> dict:
        """Get information about the loaded embedding model."""
        await self._ensure_model_loaded()
        
        return {
            "model_name": self.model_name,
            "embedding_dimensions": self.embed_dims,
            "batch_size": self.batch_size,
            "model_loaded": self.model is not None,
            "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown') if self.model else 'unknown'
        }
    
    async def close(self):
        """Clean up resources."""
        if self.model:
            # Clear model from memory
            del self.model
            self.model = None


# Global vectorizer service instance
vectorizer_service = VectorizerService()
