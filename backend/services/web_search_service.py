from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from loguru import logger
import re

class WebSearchService:
    """
    Service for performing web searches to supplement local knowledge.
    Integrates DuckDuckGo search for additional context.
    """
    """Service for performing web searches to supplement local knowledge."""
    
    def __init__(self):
        """
        Initialize DuckDuckGo search client.
        """
        self.ddgs = DDGS()
    
    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Perform a web search and return results.
        Args:
            query: Search query
            max_results: Maximum number of results to return
        Returns:
            List of search results with title, snippet, and URL
        """
        """
        Perform a web search and return results.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        try:
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'url': result.get('href', ''),
                    'source': 'web'
                })
            
            logger.info(f"Web search returned {len(results)} results for query: {query}")
            return results
        
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return []
    
    def enhance_query(self, query: str) -> str:
        """
        Enhance the query with network security context for better web results.
        Args:
            query: Original user query
        Returns:
            Enhanced query string
        """
        """
        Enhance the query with network security context for better web results.
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced query string
        """
        # Add network security context if not already present
        security_keywords = [
            'network security', 'cybersecurity', 'encryption', 
            'firewall', 'intrusion', 'vulnerability', 'attack'
        ]
        
        query_lower = query.lower()
        has_security_context = any(keyword in query_lower for keyword in security_keywords)
        
        if not has_security_context:
            return f"network security {query}"
        
        return query

# Singleton instance
web_search_service = WebSearchService()
