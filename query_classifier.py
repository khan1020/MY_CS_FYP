# query_classifier.py
# Intelligent query classification for routing and tool selection

import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classify user queries and extract intent/entities"""
    
    # Intent patterns
    PAGE_PATTERNS = [
        r'page\s+(\d+)',
        r'pg\s+(\d+)', 
        r'on\s+page\s+(\d+)',
        r'what\s+does\s+page\s+(\d+)\s+say',
        r'show\s+me\s+page\s+(\d+)'
    ]
    
    WORD_COUNT_PATTERNS = [
        # "how many times word/the word 'string' appears"
        r'how\s+many\s+times?\s+(?:does\s+)?(?:the\s+)?(?:word\s+)?["\']?(\w+)["\']?\s+(?:appear|occur)',
        # "count word/the word 'string'"
        r'count\s+(?:the\s+)?(?:occurrence[s]?\s+(?:of\s+)?)?(?:word\s+)?["\']?(\w+)["\']?',
        # "count occurrence of word 'string'"
        r'count\s+(?:the\s+)?occurrence[s]?\s+of\s+(?:the\s+)?(?:word\s+)?["\']?(\w+)["\']?',
        # "frequency of word 'string'"
        r'frequency\s+of\s+(?:the\s+)?(?:word\s+)?["\']?(\w+)["\']?',
        # "how often does 'string' appear"
        r'how\s+often\s+(?:does\s+)?["\']?(\w+)["\']?\s+(?:appear|occur)',
        # "'string' appears how many"
        r'["\']?(\w+)["\']?\s+appear[s]?\s+how\s+many',
        # "word 'string' in document"
        r'(?:word|term)\s+["\']?(\w+)["\']?\s+(?:in\s+)?(?:the\s+)?(?:document|pdf|file)',
        # Simple: "count 'string' in document"
        r'count\s+["\'](\w+)["\']',
    ]
    
    KEYWORD_PATTERNS = [
        r'extract\s+keywords?',
        r'main\s+keywords?',
        r'key\s+terms?',
        r'important\s+words?'
    ]
    
    REAL_TIME_PATTERNS = [
        # Flexible patterns - matches any variation:
        r'weath\w*',  # Matches: weather, wheather, wether, weathers, etc.
        r'temp\w*',   # Matches: temp, temperature, temprature, temps, etc.
        r'climat\w*',  # Matches: climate, climatic, etc.
        r'(?:current|today|now|latest)\s+(?:weath|temp|climat)',
        r'(?:what|check|tell|show).*(?:weath|temp|climat)',
        r'who\s+is\s+(\w+)',  # Wikipedia queries
        r'what\s+is\s+(?:the\s+)?definition\s+of',
    ]
    
    @classmethod
    def classify_query(cls, query: str, has_documents: bool = False) -> Dict:
        """
        Classify query and extract relevant information
        
        Returns:
            {
                'type': 'document_specific' | 'general_knowledge' | 'real_time_info' | 'analytical',
                'page_number': int | None,
                'target_word': str | None,
                'keywords': List[str],
                'requires_web': bool,
                'requires_rag': bool,
                'requires_calculation': bool
            }
        """
        query_lower = query.lower().strip()
        
        result = {
            'type': 'general_knowledge',
            'page_number': None,
            'target_word': None,
            'keywords': [],
            'requires_web': False,
            'requires_rag': has_documents,
            'requires_calculation': False,
            'analysis_type': None
        }
        
        # Check for page-specific queries
        page_number = cls.extract_page_number(query_lower)
        if page_number:
            result['type'] = 'page_specific'
            result['page_number'] = page_number
            result['requires_rag'] = True
            return result
        
        # Check for word counting queries
        target_word = cls.extract_target_word(query_lower)
        if target_word:
            result['type'] = 'analytical'
            result['analysis_type'] = 'word_count'
            result['target_word'] = target_word
            result['requires_rag'] = True
            return result
        
        # Check for keyword extraction queries
        if cls.is_keyword_extraction_query(query_lower):
            result['type'] = 'analytical'
            result['analysis_type'] = 'keyword_extraction'
            result['requires_rag'] = True
            return result
        
        # Check for real-time information queries
        if cls.is_real_time_query(query_lower):
            result['type'] = 'real_time_info'
            result['requires_web'] = True
            result['requires_rag'] = False
            return result
        
        # Check if it's document-specific
        if has_documents and cls.is_document_query(query_lower):
            result['type'] = 'document_specific'
            result['requires_rag'] = True
        else:
            result['type'] = 'general_knowledge'
            result['requires_rag'] = False
        
        # Extract keywords from query
        result['keywords'] = cls.extract_query_keywords(query)
        
        return result
    
    @classmethod
    def extract_page_number(cls, query: str) -> Optional[int]:
        """Extract page number from query"""
        for pattern in cls.PAGE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    @classmethod
    def extract_target_word(cls, query: str) -> Optional[str]:
        """Extract target word for counting"""
        for pattern in cls.WORD_COUNT_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip('"\'')
        return None
    
    @classmethod
    def is_keyword_extraction_query(cls, query: str) -> bool:
        """Check if query is asking for keyword extraction"""
        for pattern in cls.KEYWORD_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def is_real_time_query(cls, query: str) -> bool:
        """Check if query needs real-time information"""
        for pattern in cls.REAL_TIME_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def is_document_query(cls, query: str) -> bool:
        """Check if query is about uploaded documents"""
        doc_keywords = [
            'document', 'paper', 'file', 'pdf', 'thesis', 'report',
            'chapter', 'section', 'paragraph', 'methodology', 'conclusion',
            'abstract', 'introduction', 'results', 'discussion',
            'my document', 'this document', 'uploaded', 'my file'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in doc_keywords)
    
    @classmethod
    def extract_query_keywords(cls, query: str) -> List[str]:
        """Extract important keywords from the query itself"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were',
            'what', 'how', 'why', 'when', 'where', 'who', 'which',
            'does', 'do', 'did', 'can', 'could', 'should', 'would',
            'my', 'me', 'i', 'you', 'this', 'that', 'these', 'those'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:10]  # Return top 10 keywords


# Convenience function for easy import
def classify_query(query: str, has_documents: bool = False) -> Dict:
    """Main entry point for query classification"""
    return QueryClassifier.classify_query(query, has_documents)
