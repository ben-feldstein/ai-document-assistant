"""Semantic search service using pgvector and MMR reranking."""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from api.models.db import get_db_session
from api.models.entities import Doc, Embedding
from api.services.cache import cache_service
from api.services.vectorizer import vectorizer_service
from api.utils.config import settings


class SearchService:
    """Semantic search service with vector similarity and MMR reranking."""
    
    def __init__(self):
        self.embed_dims = settings.embed_dims
        self.default_k = 10
        self.mmr_lambda = 0.7  # Diversity vs relevance balance
    
    async def search(
        self, 
        query: str, 
        k: int = 10, 
        org_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with MMR reranking.
        
        Args:
            query: Search query text
            k: Number of results to return
            org_id: Organization ID for filtering
            filters: Additional metadata filters
            
        Returns:
            List of search results with scores and metadata
        """
        # Check cache first (organization-scoped)
        cached_results = await cache_service.get_search_cache(query, org_id)
        if cached_results:
            # Get full document details from cache
            docs = await self._get_documents_by_ids(cached_results[:k])
            return self._format_search_results(docs, query)
        
        # Generate query embedding
        query_embedding = await vectorizer_service.get_embedding(query)
        if not query_embedding:
            return []
        
        # Perform vector similarity search
        similar_embeddings = await self._vector_search(
            query_embedding, 
            k * 2,  # Get more results for MMR
            org_id,
            filters,
            query  # Pass the original query text
        )
        
        if not similar_embeddings:
            return []
        
        # Apply MMR reranking only if we have vector data
        if similar_embeddings and len(similar_embeddings) > 0 and "vector" in similar_embeddings[0]:
            reranked_results = self._mmr_rerank(
                query_embedding, 
                similar_embeddings, 
                k
            )
        else:
            # For text search, just take the first k results
            reranked_results = similar_embeddings[:k]
        
        # Cache results (organization-scoped)
        doc_ids = [result["doc_id"] for result in reranked_results]
        await cache_service.set_search_cache(query, doc_ids, org_id)
        
        return reranked_results
    
    async def _vector_search(
        self, 
        query_vector: List[float], 
        k: int,
        org_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        query_text: str = ""
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search using pgvector."""
        db = get_db_session()
        try:
            # For now, skip vector search and use text search directly
            # TODO: Fix pgvector integration later
            print("Using text search (vector search temporarily disabled)")
            try:
                result = await self._text_search(query_text, k, org_id, filters)
                print(f"Text search returned {len(result)} results")
                print(f"First result structure: {result[0] if result else 'No results'}")
                return result
            except Exception as e:
                print(f"Text search failed: {e}")
                import traceback
                traceback.print_exc()
                return []
        finally:
            db.close()
    
    async def _text_search(
        self, 
        query_text: str, 
        k: int,
        org_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fallback text-based search when vector search fails."""
        db = get_db_session()
        try:
            # Build the base query
            base_query = """
                SELECT 
                    d.id,
                    d.id as doc_id,
                    d.text as chunk_text,
                    0 as chunk_start,
                    LENGTH(d.text) as chunk_end,
                    '[]'::text as vector,
                    d.title,
                    d.source,
                    d.doc_metadata,
                    0.5 as similarity
                FROM doc d
                WHERE 1=1
            """
            
            # Build conditions
            conditions = []
            params = {}
            
            # CRITICAL: Always filter by organization ID for security
            if not org_id:
                print("WARNING: No org_id provided for search - this is a security risk!")
                return []
            
            # Ensure organization filter is always applied
            conditions.append("d.org_id = :org_id")
            params["org_id"] = org_id
            
            # Add text search using the actual query text
            if query_text:
                # Extract key words from query (simple approach)
                words = query_text.lower().split()
                # Filter out common words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'how', 'why', 'when', 'where', 'who'}
                search_terms = [word for word in words if word not in stop_words and len(word) > 2]
                
                if search_terms:
                    # Build search condition
                    search_conditions = []
                    for term in search_terms[:3]:  # Use up to 3 terms
                        search_conditions.append(f"(d.title ILIKE '%{term}%' OR d.text ILIKE '%{term}%')")
                    
                    if search_conditions:
                        conditions.append("(" + " OR ".join(search_conditions) + ")")
            
            # Combine all conditions
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            # Add ORDER BY and LIMIT
            base_query += " ORDER BY d.created_at DESC LIMIT :k"
            params["k"] = k
            
            # Execute the query
            query = text(base_query)
            result = db.execute(query, params)
            rows = result.fetchall()
            
            # Format results to match SearchResult schema EXACTLY
            formatted_results = []
            for row in rows:
                try:
                    # Map database fields to SearchResult schema fields
                    formatted_result = {
                        "id": row.id,                    # SearchResult.id
                        "score": float(row.similarity),  # SearchResult.score
                        "snippet": row.chunk_text,       # SearchResult.snippet
                        "metadata": self._safe_parse_metadata(row.doc_metadata),  # SearchResult.metadata
                        "doc_id": row.doc_id,            # SearchResult.doc_id
                        "title": row.title               # SearchResult.title
                    }
                    formatted_results.append(formatted_result)
                    print(f"DEBUG: Formatted result: {formatted_result}")
                except Exception as e:
                    print(f"ERROR formatting result: {e}")
                    continue
            
            print(f"DEBUG: Returning {len(formatted_results)} formatted results")
            return formatted_results
        finally:
            db.close()
    
    def _safe_parse_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Safely parse metadata string to dictionary."""
        print(f"DEBUG: Parsing metadata: '{metadata_str}' (type: {type(metadata_str)})")
        
        if not metadata_str or metadata_str in ['{}', 'null', 'None']:
            print(f"DEBUG: Returning empty dict for: '{metadata_str}'")
            return {}
        
        try:
            result = json.loads(metadata_str)
            print(f"DEBUG: Successfully parsed metadata: {result}")
            return result
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not parse metadata '{metadata_str}': {e}")
            return {}
    
    def _mmr_rerank(
        self, 
        query_vector: List[float], 
        candidates: List[Dict[str, Any]], 
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Apply Maximal Marginal Relevance (MMR) reranking.
        
        MMR balances relevance and diversity by selecting documents that are
        both relevant to the query and diverse from previously selected documents.
        """
        if not candidates:
            return []
        
        # Convert vectors to numpy arrays for efficient computation
        query_vec = np.array(query_vector)
        candidate_vectors = []
        for c in candidates:
            try:
                if isinstance(c["vector"], str):
                    vector_data = json.loads(c["vector"])
                else:
                    vector_data = c["vector"]
                candidate_vectors.append(np.array(vector_data))
            except (json.JSONDecodeError, ValueError, TypeError):
                # Skip invalid vectors
                continue
        
        if not candidate_vectors:
            return []
        
        # Calculate cosine similarities to query
        similarities_to_query = [
            np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
            for vec in candidate_vectors
        ]
        
        # Initialize selected documents
        selected = []
        remaining = list(range(len(candidates)))
        
        # Select first document (most similar to query)
        first_idx = np.argmax(similarities_to_query)
        selected.append(first_idx)
        remaining.remove(first_idx)
        
        # Select remaining documents using MMR
        for _ in range(min(k - 1, len(remaining))):
            if not remaining:
                break
            
            mmr_scores = []
            for idx in remaining:
                # Relevance to query
                relevance = similarities_to_query[idx]
                
                # Diversity from selected documents
                diversity = 0
                if selected:
                    similarities_to_selected = [
                        np.dot(candidate_vectors[idx], candidate_vectors[sel_idx]) / 
                        (np.linalg.norm(candidate_vectors[idx]) * np.linalg.norm(candidate_vectors[sel_idx]))
                        for sel_idx in selected
                    ]
                    diversity = 1 - max(similarities_to_selected)
                
                # MMR score
                mmr_score = self.mmr_lambda * relevance + (1 - self.mmr_lambda) * diversity
                mmr_scores.append((idx, mmr_score))
            
            # Select document with highest MMR score
            best_idx = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(best_idx)
            remaining.remove(best_idx)
        
        # Return reranked results
        reranked = []
        for idx in selected:
            candidate = candidates[idx].copy()
            candidate["mmr_score"] = similarities_to_query[idx]
            reranked.append(candidate)
        
        return reranked
    
    async def _get_documents_by_ids(self, doc_ids: List[int]) -> List[Dict[str, Any]]:
        """Get document details by IDs."""
        db = get_db_session()
        try:
            docs = db.query(Doc).filter(Doc.id.in_(doc_ids)).all()
            return [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "text": doc.text,
                    "metadata": self._safe_parse_metadata(doc.doc_metadata),
                    "similarity": 1.0,  # Cached results get max similarity
                    "mmr_score": 1.0
                }
                for doc in docs
            ]
        finally:
            db.close()
    
    def _format_search_results(
        self, 
        results: List[Dict[str, Any]], 
        query: str
    ) -> List[Dict[str, Any]]:
        """Format search results for API response."""
        formatted = []
        for result in results:
            # Create snippet from chunk text or full text
            text = result.get("chunk_text", result.get("text", ""))
            snippet = self._create_snippet(text, query, max_length=200)
            
            formatted.append({
                "id": result["id"],
                "score": result.get("similarity", result.get("mmr_score", 0)),
                "snippet": snippet,
                "metadata": result.get("metadata", {}),
                "doc_id": result["id"],
                "title": result.get("title", "Untitled"),
                "source": result.get("source", ""),
                "chunk_start": result.get("chunk_start"),
                "chunk_end": result.get("chunk_end")
            })
        
        return formatted
    
    def _create_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Create a snippet highlighting the query terms."""
        if len(text) <= max_length:
            return text
        
        # Simple snippet creation - find query terms and create context
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        # Find the best position for snippet
        best_pos = 0
        best_score = 0
        
        for i in range(0, len(text) - max_length, max_length // 2):
            window = text_lower[i:i + max_length]
            score = sum(1 for term in query_terms if term in window)
            if score > best_score:
                best_score = score
                best_pos = i
        
        snippet = text[best_pos:best_pos + max_length]
        
        # Add ellipsis if not at beginning/end
        if best_pos > 0:
            snippet = "..." + snippet
        if best_pos + max_length < len(text):
            snippet = snippet + "..."
        
        return snippet


# Global search service instance
search_service = SearchService()
