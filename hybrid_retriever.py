# hybrid_retriever.py
# Hybrid retrieval combining semantic search (FAISS) + keyword search (BM25)

from typing import List, Dict, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

# BM25 for keyword search
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("BM25 not available. Install with: pip install rank-bm25")


class HybridRetriever:
    """Combine semantic and keyword search for better retrieval"""
    
    @staticmethod
    def create_bm25_index(chunks: List[Dict]) -> 'BM25Okapi':
        """Create BM25 index from document chunks"""
        if not BM25_AVAILABLE:
            return None
        
        try:
            # Tokenize all chunks
            tokenized_chunks = [
                chunk.get('text', '').lower().split()
                for chunk in chunks
            ]
            
            # Create BM25 index
            bm25 = BM25Okapi(tokenized_chunks)
            logger.info(f"Created BM25 index with {len(chunks)} chunks")
            return bm25
        except Exception as e:
            logger.exception(f"Failed to create BM25 index: {e}")
            return None
    
    @staticmethod
    def bm25_search(
        bm25_index: 'BM25Okapi',
        chunks: List[Dict],
        query: str,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Perform BM25 keyword search
        
        Returns:
            List of (chunk_index, score) tuples
        """
        if not BM25_AVAILABLE or bm25_index is None:
            return []
        
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = bm25_index.get_scores(tokenized_query)
            
            # Get top K indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Return (index, score) pairs
            results = [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
            
            logger.debug(f"BM25 search found {len(results)} results for query: {query[:50]}")
            return results
        except Exception as e:
            logger.exception(f"BM25 search failed: {e}")
            return []
    
    @staticmethod
    def reciprocal_rank_fusion(
        semantic_results: List[Tuple[int, float]],
        keyword_results: List[Tuple[int, float]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Fuse semantic and keyword search results using Reciprocal Rank Fusion (RRF)
        
        RRF score = Σ 1 / (k + rank_i)
        
        Args:
            semantic_results: [(chunk_idx, score), ...]
            keyword_results: [(chunk_idx, score), ...]  
            k: RRF constant (default 60)
        
        Returns:
            Fused results sorted by RRF score
        """
        rrf_scores = {}
        
        # Process semantic results
        for rank, (idx, score) in enumerate(semantic_results, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank)
        
        # Process keyword results
        for rank, (idx, score) in enumerate(keyword_results, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (k + rank)
        
        # Sort by RRF score
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.debug(f"RRF fusion produced {len(fused)} unique results")
        return fused
    
    @staticmethod
    def filter_by_metadata(
        results: List[Tuple[int, float]],
        chunks: List[Dict],
        page_number: int = None,
        section: str = None,
        min_words: int = None
    ) -> List[Tuple[int, float]]:
        """Filter search results by metadata"""
        if not any([page_number, section, min_words]):
            return results
        
        filtered = []
        for idx, score in results:
            if idx >= len(chunks):
                continue
            
            chunk = chunks[idx]
            
            # Filter by page number
            if page_number and chunk.get('page_number') != page_number:
                continue
            
            # Filter by section
            if section and section.lower() not in chunk.get('section_title', '').lower():
                continue
            
            # Filter by minimum words
            if min_words and chunk.get('word_count', 0) < min_words:
                continue
            
            filtered.append((idx, score))
        
        logger.debug(f"Metadata filtering: {len(results)} -> {len(filtered)} results")
        return filtered
    
    @staticmethod
    def hybrid_search(
        query: str,
        chunks: List[Dict],
        faiss_index,
        sentence_transformer,
        bm25_index = None,
        top_k: int = 5,
        page_number: int = None,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[Dict]:
        """
        Perform hybrid search combining semantic + keyword + metadata
        
        Args:
            query: Search query
            chunks: Document chunks
            faiss_index: FAISS semantic index
            sentence_transformer: SentenceTransformer model
            bm25_index: BM25 index (optional)
            top_k: Number of results
            page_number: Filter by specific page
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        
        Returns:
            List of matching chunks with metadata
        """
        import faiss as faiss_lib
        
        # 1. Semantic search (FAISS)
        try:
            q_vec = sentence_transformer.encode([query], convert_to_numpy=True).astype('float32')
            faiss_lib.normalize_L2(q_vec)
            q_vec = np.ascontiguousarray(q_vec)
            
            distances, indices = faiss_index.search(q_vec, top_k * 2)  # Get more candidates
            
            semantic_results = [
                (int(idx), float(dist))
                for idx, dist in zip(indices[0], distances[0])
                if idx >= 0 and idx < len(chunks)
            ]
        except Exception as e:
            logger.exception(f"Semantic search failed: {e}")
            semantic_results = []
        
        # 2. Keyword search (BM25) - if available
        keyword_results = []
        if BM25_AVAILABLE and bm25_index:
            keyword_results = HybridRetriever.bm25_search(
                bm25_index, chunks, query, top_k * 2
            )
        
        # 3. Fuse results
        if keyword_results:
            fused_results = HybridRetriever.reciprocal_rank_fusion(
                semantic_results, keyword_results
            )
        else:
            # Just use semantic if BM25 unavailable
            fused_results = semantic_results
        
        # 4. Filter by metadata if specified
        if page_number:
            fused_results = HybridRetriever.filter_by_metadata(
                fused_results, chunks, page_number=page_number
            )
        
        # 5. Get top K chunks
        top_results = fused_results[:top_k]
        
        # 6. Retrieve actual chunks
        retrieved_chunks = []
        for idx, score in top_results:
            if idx < len(chunks):
                chunk_data = chunks[idx].copy()
                chunk_data['retrieval_score'] = round(score, 4)
                chunk_data['chunk_index'] = idx
                retrieved_chunks.append(chunk_data)
        
        logger.info(f"Hybrid search returned {len(retrieved_chunks)} chunks for query: {query[:50]}")
        return retrieved_chunks


# Convenience function
def hybrid_search(
    query: str,
    chunks: List[Dict],
    faiss_index,
    sentence_transformer,
    bm25_index=None,
    top_k: int = 5,
    page_number: int = None
) -> List[Dict]:
    """Perform hybrid search"""
    return HybridRetriever.hybrid_search(
        query, chunks, faiss_index, sentence_transformer,
        bm25_index, top_k, page_number
    )
