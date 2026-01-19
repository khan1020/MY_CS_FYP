# keyword_extractor.py
# Extract keywords and analyze document word frequency

from typing import List, Dict, Tuple
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Install with: pip install yake-rake rake-nltk
try:
    import yake
    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False
    logger.warning("YAKE not available. Install with: pip install yake-rake")

try:
    from rake_nltk import Rake
    RAKE_AVAILABLE = True
except ImportError:
    RAKE_AVAILABLE = False
    logger.warning("RAKE not available. Install with: pip install rake-nltk")


class KeywordExtractor:
    """Extract keywords from documents using RAKE or YAKE"""
    
    @staticmethod
    def extract_keywords_yake(text: str, top_n: int = 20, max_ngram: int = 3) -> List[Dict]:
        """Extract keywords using YAKE algorithm"""
        if not YAKE_AVAILABLE:
            logger.warning("YAKE not available, falling back to simple extraction")
            return KeywordExtractor.extract_keywords_simple(text, top_n)
        
        try:
            kw_extractor = yake.KeywordExtractor(
                lan="en",
                n=max_ngram,
                dedupLim=0.9,
                top=top_n,
                features=None
            )
            keywords = kw_extractor.extract_keywords(text)
            
            # Format: [(keyword, score), ...] -> [{'keyword': ..., 'score': ...}, ...]
            return [
                {
                    'keyword': kw,
                    'score': round(1 - score, 3),  # Invert YAKE score (lower is better)
                    'method': 'yake'
                }
                for kw, score in keywords
            ]
        except Exception as e:
            logger.exception(f"YAKE extraction failed: {e}")
            return KeywordExtractor.extract_keywords_simple(text, top_n)
    
    @staticmethod
    def extract_keywords_rake(text: str, top_n: int = 20) -> List[Dict]:
        """Extract keywords using RAKE algorithm"""
        if not RAKE_AVAILABLE:
            logger.warning("RAKE not available, falling back to simple extraction")
            return KeywordExtractor.extract_keywords_simple(text, top_n)
        
        try:
            rake = Rake()
            rake.extract_keywords_from_text(text)
            ranked_phrases = rake.get_ranked_phrases_with_scores()[:top_n]
            
            return [
                {
                    'keyword': phrase,
                    'score': round(score, 3),
                    'method': 'rake'
                }
                for score, phrase in ranked_phrases
            ]
        except Exception as e:
            logger.exception(f"RAKE extraction failed: {e}")
            return KeywordExtractor.extract_keywords_simple(text, top_n)
    
    @staticmethod
    def extract_keywords_simple(text: str, top_n: int = 20) -> List[Dict]:
        """Simple frequency-based keyword extraction (fallback)"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered_words = [w for w in words if w not in stop_words]
        
        # Count frequency
        word_counts = Counter(filtered_words)
        
        # Get top N
        top_words = word_counts.most_common(top_n)
        
        # Normalize scores
        max_count = top_words[0][1] if top_words else 1
        
        return [
            {
                'keyword': word,
                'score': round(count / max_count, 3),
                'frequency': count,
                'method': 'frequency'
            }
            for word, count in top_words
        ]
    
    @staticmethod
    def extract_keywords(text: str, method: str = 'auto', top_n: int = 20) -> List[Dict]:
        """
        Extract keywords using specified method
        
        Args:
            text: Text to extract from
            method: 'yake', 'rake', 'simple', or 'auto' (tries best available)
            top_n: Number of keywords to extract
        
        Returns:
            List of dicts with 'keyword' and 'score'
        """
        if method == 'yake':
            return KeywordExtractor.extract_keywords_yake(text, top_n)
        elif method == 'rake':
            return KeywordExtractor.extract_keywords_rake(text, top_n)
        elif method == 'simple':
            return KeywordExtractor.extract_keywords_simple(text, top_n)
        else:  # auto
            # Try YAKE first, then RAKE, then simple
            if YAKE_AVAILABLE:
                return KeywordExtractor.extract_keywords_yake(text, top_n)
            elif RAKE_AVAILABLE:
                return KeywordExtractor.extract_keywords_rake(text, top_n)
            else:
                return KeywordExtractor.extract_keywords_simple(text, top_n)


class WordCounter:
    """Count word frequency with page-level breakdown"""
    
    @staticmethod
    def count_word_occurrences(
        chunks,  # Can be List[Dict] or List[str]
        target_word: str,
        case_sensitive: bool = False
    ) -> Dict:
        """
        Count occurrences of a word across document chunks
        
        Args:
            chunks: List of {text, page_number, ...} OR List of strings
            target_word: Word to count
            case_sensitive: Whether to match case
        
        Returns:
            {
                'total': int,
                'pages': {page_num: count, ...},
                'chunks': {chunk_idx: count, ...}
            }
        """
        if not case_sensitive:
            target_word = target_word.lower()
        
        total_count = 0
        page_counts = {}
        chunk_counts = {}
        
        for idx, chunk in enumerate(chunks):
            # Handle both dict and string formats
            if isinstance(chunk, dict):
                text = chunk.get('text', '')
                page_num = chunk.get('page_number', idx + 1)  # Default to index if no page
            else:
                text = str(chunk)
                page_num = idx + 1  # Use index as pseudo-page for strings
            
            if not case_sensitive:
                text = text.lower()
            
            # Count occurrences in this chunk
            count = len(re.findall(r'\b' + re.escape(target_word) + r'\b', text))
            
            if count > 0:
                total_count += count
                chunk_counts[idx] = count
                page_counts[page_num] = page_counts.get(page_num, 0) + count
        
        # Sort pages by page number
        sorted_pages = dict(sorted(page_counts.items()))
        
        return {
            'total': total_count,
            'target_word': target_word,
            'case_sensitive': case_sensitive,
            'pages': sorted_pages,
            'chunk_indices': chunk_counts,
            'page_count': len(sorted_pages)  # How many pages contain the word
        }
    
    @staticmethod
    def get_document_statistics(chunks: List[Dict]) -> Dict:
        """Get overall document statistics"""
        total_words = 0
        total_chars = 0
        page_count = 0
        
        pages_seen = set()
        
        for chunk in chunks:
            text = chunk.get('text', '')
            page_num = chunk.get('page_number', 0)
            
            words = len(text.split())
            chars = len(text)
            
            total_words += words
            total_chars += chars
            pages_seen.add(page_num)
        
        # Estimate reading time (average 200 words per minute)
        reading_time_minutes = total_words / 200
        
        return {
            'total_words': total_words,
            'total_characters': total_chars,
            'total_pages': len(pages_seen),
            'total_chunks': len(chunks),
            'avg_words_per_page': round(total_words / len(pages_seen)) if pages_seen else 0,
            'estimated_reading_time_minutes': round(reading_time_minutes, 1)
        }


# Convenience functions
def extract_keywords(text: str, method: str = 'auto', top_n: int = 20) -> List[Dict]:
    """Extract keywords from text"""
    return KeywordExtractor.extract_keywords(text, method, top_n)


def count_word_frequency(
    chunks: List[Dict],
    word: str,
    case_sensitive: bool = False
) -> Dict:
    """Count word frequency across chunks"""
    return WordCounter.count_word_occurrences(chunks, word, case_sensitive)


def get_document_stats(chunks: List[Dict]) -> Dict:
    """Get document statistics"""
    return WordCounter.get_document_statistics(chunks)
