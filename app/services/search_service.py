"""
Web Search Service using Exa API for enhanced AI-powered search.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import asyncio
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    score: Optional[float] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
            "published_date": self.published_date,
            "author": self.author
        }

@dataclass
class SearchService:
    """Service for web search functionality using Exa API."""
    
    api_key: Optional[str] = field(default_factory=lambda: settings.EXA_API_KEY)
    enabled: bool = field(default_factory=lambda: settings.EXA_SEARCH_ENABLED)
    
    def __post_init__(self):
        """Initialize the search client."""
        self.client = None
        if self.enabled and self.api_key:
            try:
                from exa_py import Exa
                self.client = Exa(api_key=self.api_key)
                logger.info("Exa search client initialized successfully")
            except ImportError:
                logger.error("exa_py package not installed. Run: pip install exa_py")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Exa client: {str(e)}")
                self.enabled = False
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5,
        use_autoprompt: bool = True,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        category: Optional[str] = None,
        include_text: bool = True
    ) -> List[SearchResult]:
        """
        Perform a web search using Exa API.
        
        Args:
            query: Search query
            num_results: Number of results to return
            use_autoprompt: Whether to use Exa's autoprompt feature
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            start_published_date: Filter by start date (YYYY-MM-DD)
            end_published_date: Filter by end date (YYYY-MM-DD)
            category: Category filter (e.g., "news", "papers", "company")
            include_text: Whether to include text content
            
        Returns:
            List of SearchResult objects
        """
        if not self.enabled or not self.client:
            logger.warning("Search service is not enabled or initialized")
            return []
        
        try:
            # Build search parameters
            search_params = {
                "num_results": num_results,
                "use_autoprompt": use_autoprompt,
            }
            
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            if start_published_date:
                search_params["start_published_date"] = start_published_date
            if end_published_date:
                search_params["end_published_date"] = end_published_date
            if category:
                search_params["category"] = category
                
            # Perform search with optional content retrieval
            if include_text:
                # Use search_and_contents for efficiency
                response = await asyncio.to_thread(
                    self.client.search_and_contents,
                    query,
                    text={"max_characters": 500},  # Limit text for snippets
                    **search_params
                )
            else:
                response = await asyncio.to_thread(
                    self.client.search,
                    query,
                    **search_params
                )
            
            # Parse results
            results = []
            for result in response.results:
                snippet = ""
                if hasattr(result, 'text'):
                    snippet = result.text[:500] if result.text else ""
                elif hasattr(result, 'snippet'):
                    snippet = result.snippet
                    
                results.append(SearchResult(
                    title=getattr(result, 'title', 'No title'),
                    url=result.url,
                    snippet=snippet,
                    score=getattr(result, 'score', None),
                    published_date=getattr(result, 'published_date', None),
                    author=getattr(result, 'author', None)
                ))
            
            logger.info(f"Search completed: {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    async def find_similar(self, url: str, num_results: int = 5) -> List[SearchResult]:
        """
        Find similar pages to a given URL.
        
        Args:
            url: URL to find similar pages for
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.enabled or not self.client:
            logger.warning("Search service is not enabled or initialized")
            return []
        
        try:
            response = await asyncio.to_thread(
                self.client.find_similar,
                url,
                num_results=num_results
            )
            
            results = []
            for result in response.results:
                results.append(SearchResult(
                    title=getattr(result, 'title', 'No title'),
                    url=result.url,
                    snippet=getattr(result, 'text', '')[:500] if hasattr(result, 'text') else '',
                    score=getattr(result, 'score', None),
                    published_date=getattr(result, 'published_date', None),
                    author=getattr(result, 'author', None)
                ))
            
            logger.info(f"Found {len(results)} similar pages for: {url}")
            return results
            
        except Exception as e:
            logger.error(f"Find similar failed: {str(e)}")
            return []
    
    async def get_contents(self, urls: List[str]) -> Dict[str, str]:
        """
        Get full text content for a list of URLs.
        
        Args:
            urls: List of URLs to get content for
            
        Returns:
            Dictionary mapping URLs to their text content
        """
        if not self.enabled or not self.client:
            logger.warning("Search service is not enabled or initialized")
            return {}
        
        try:
            response = await asyncio.to_thread(
                self.client.get_contents,
                urls
            )
            
            contents = {}
            for result in response.results:
                if hasattr(result, 'text'):
                    contents[result.url] = result.text
            
            logger.info(f"Retrieved content for {len(contents)} URLs")
            return contents
            
        except Exception as e:
            logger.error(f"Get contents failed: {str(e)}")
            return {}
    
    def format_for_llm(self, results: List[SearchResult], max_results: int = 3) -> str:
        """
        Format search results for LLM consumption.
        
        Args:
            results: List of search results
            max_results: Maximum number of results to include
            
        Returns:
            Formatted string for LLM context
        """
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        for i, result in enumerate(results[:max_results], 1):
            formatted += f"{i}. **{result.title}**\n"
            formatted += f"   URL: {result.url}\n"
            if result.snippet:
                formatted += f"   Summary: {result.snippet}\n"
            if result.published_date:
                formatted += f"   Published: {result.published_date}\n"
            formatted += "\n"
        
        return formatted

# Create tool definition for Ollama function calling
def get_search_tool_definition() -> Dict[str, Any]:
    """Get the tool definition for Ollama function calling."""
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information using Exa's AI-powered search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter: news, papers, company, etc.",
                        "enum": ["news", "papers", "company", "tweet", "github", "personal_site"]
                    },
                    "include_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of domains to include in search"
                    },
                    "exclude_domains": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of domains to exclude from search"
                    }
                },
                "required": ["query"]
            }
        }
    }

# Global instance
search_service = SearchService()