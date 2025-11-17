"""
Search tools for SAGA Biography Generation System.
Provides web search capabilities using Tavily API and content crawling.
"""

import re
from typing import Dict, Any
from tavily import TavilyClient
from config.settings import settings

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    print("⚠️ crawl4ai not installed, using basic search mode")
    CRAWL4AI_AVAILABLE = False

class SearchToolError(Exception):
    """Search tool related errors."""
    pass

class WebSearchTool:
    """Web search functionality using Tavily API."""
    
    def __init__(self):
        if not settings.tavily_api_key:
            raise SearchToolError("Tavily API key not configured")
        self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    async def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform web search using Tavily API."""
        try:
            response = self.client.search(
                query, 
                max_results=min(num_results, 10), 
                include_raw_content=True
            )
            
            # Convert to unified format
            results = []
            if "results" in response:
                for item in response["results"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "content": item.get("raw_content", item.get("content", "")),
                        "displayLink": item.get("url", ""),
                        "has_crawled_content": True  # Tavily already includes content
                    })
            
            return {
                "results": results,
                "searchInformation": {"totalResults": len(results)},
                "queries": {"request": [{"searchTerms": query}]}
            }
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {"results": [], "error": str(e)}

class ContentCrawler:
    """Web content crawling functionality."""
    
    async def crawl_and_summarize_url(self, url: str) -> str:
        """Crawl URL and generate summary, supports PDF files."""
        
        # Check if it's a PDF file
        if url.lower().endswith('.pdf') or 'pdf' in url.lower():
            print(f"📄 PDF file detected, extracting: {url}")
            pdf_content = self._extract_pdf_text(url)
            
            if pdf_content and not pdf_content.startswith("PDF extraction failed"):
                # Limit PDF content length and generate summary
                content = pdf_content[:4000]  # PDFs usually longer than web pages
                content_length = len(content)
                
                if content_length < 500:
                    summary_length = "100-200 words"
                elif content_length < 2000:
                    summary_length = "200-400 words"
                else:
                    summary_length = "400-600 words"
                
                summary_prompt = f"""Please generate a detailed summary of the following PDF document content, focusing on historical background information:

PDF document content ({content_length} characters):
{content}

Please provide:
1. Main content summary ({summary_length})
2. Key historical events or background information
3. Important time points and data
4. Potential impact on personal life

Summary:"""

                try:
                    from src.models.client_manager import model_manager
                    client = model_manager.current_client
                    from autogen_core.models import UserMessage
                    
                    response = await client.create(
                        messages=[UserMessage(content=summary_prompt, source="user")]
                    )
                    
                    summary_result = response.content
                    print(f"📄 PDF processing completed: {url[:50]}...")
                    print(f"📝 PDF summary length: {len(summary_result)} characters")
                    
                    return f"PDF document summary: {summary_result}"
                except Exception as e:
                    return f"PDF summary generation failed: {str(e)}"
            else:
                return pdf_content  # Return error message
        
        # Handle regular web pages
        if not CRAWL4AI_AVAILABLE:
            return "Web content retrieval failed: crawl4ai not installed"
        
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    css_selector="p, article, .content, .main, .post",
                    exclude_tags=['nav', 'footer', 'header', 'aside', 'script', 'style']
                )
                
                if result.success and result.markdown:
                    # Use model to generate content summary
                    content = result.markdown[:3000]  # Limit length to avoid token limit
                    
                    # Adjust summary requirements based on content length
                    content_length = len(content)
                    if content_length < 500:
                        summary_length = "50-100 words"
                    elif content_length < 1500:
                        summary_length = "100-200 words"
                    else:
                        summary_length = "200-400 words"
                    
                    summary_prompt = f"""Please generate a concise and accurate summary of the following web content, focusing on historical background information:

Web content ({content_length} characters):
{content}

Please provide:
1. Main content summary ({summary_length})
2. Key historical events or background information  
3. Time points and important details

Requirements:
- Adjust summary length based on original content richness
- If original is short, summary should be correspondingly brief
- If original is long and informative, summary can be more detailed
- Avoid generating fixed-length templated content

Summary:"""

                    try:
                        from src.models.client_manager import model_manager
                        client = model_manager.current_client
                        from autogen_core.models import UserMessage
                        
                        response = await client.create(
                            messages=[UserMessage(content=summary_prompt, source="user")]
                        )
                        
                        summary_result = response.content
                        print(f"🔍 Crawler debug: URL={url[:50]}...")
                        print(f"📄 Original length: {content_length} characters")
                        print(f"📝 Summary length: {len(summary_result)} characters")
                        print(f"🎯 Target length: {summary_length}")
                        
                        return f"Web summary: {summary_result}"
                    except Exception as e:
                        return f"Summary generation failed: {str(e)}"
                else:
                    return f"Web content retrieval failed: {result.error if hasattr(result, 'error') else 'Unknown error'}"
                    
        except Exception as e:
            return f"Web crawling error: {str(e)}"
    
    def _extract_pdf_text(self, pdf_url: str) -> str:
        """Extract text content from PDF file."""
        try:
            import PyPDF2
            import requests
            from io import BytesIO
            
            # Download PDF file
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Use PyPDF2 to extract text
            pdf_reader = PyPDF2.PdfReader(BytesIO(response.content))
            text_content = ""
            
            # Extract content from first 10 pages to avoid excessive length
            max_pages = min(len(pdf_reader.pages), 10)
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            return text_content
            
        except ImportError:
            return "PDF extraction failed: PyPDF2 not installed, please run pip install PyPDF2"
        except Exception as e:
            return f"PDF extraction error: {str(e)}"

class EnhancedSearchTool:
    """Enhanced search tool combining web search and content crawling."""
    
    def __init__(self):
        self.search_tool = WebSearchTool()
        self.crawler = ContentCrawler()
    
    async def search_enhanced(self, query: str, num_results: int = 5, crawl_top: int = 2) -> Dict[str, Any]:
        """Enhanced search with automatic content crawling."""
        try:
            # Use basic search function to get search results (actually Tavily)
            data = await self.search_tool.search(query, num_results)
            
            # Tavily already provides content, no additional crawling needed
            print(f"✅ Tavily search completed: {len(data.get('results', []))} results, content included")
            
            return data
            
        except Exception as e:
            print(f"Enhanced search error: {e}")
            return {"results": [], "error": str(e)}
    
    async def summarize_search_content(self, content: str, title: str = "") -> str:
        """Summarize search result content using model, extract 100-200 words of key event info and social impact."""
        if not content or len(content) < 100:
            return content
        
        # Limit input content length to avoid context overflow (safety protection)
        if len(content) > 100000:
            print(f"⚠️ Summary function received overly long content({len(content)} chars), auto-truncating to first 100000 chars")
            content = content[:100000]
        
        try:
            summary_prompt = f"""Please summarize the following search result content, extracting key event information and social impact:

Title: {title}
Content: {content}

Summary requirements:
1. Word count controlled to 100-200 words
2. Focus on extracting historical events, policy changes, social impact
3. Highlight specific impacts on ordinary people's lives
4. Preserve core information like time, place, key data
5. Use concise and clear language

Please provide summary:"""
            
            from src.models.client_manager import model_manager
            client = model_manager.current_client
            from autogen_core.models import UserMessage
            
            response = await client.create(
                messages=[UserMessage(content=summary_prompt, source="user")]
            )
            
            summary = response.content.strip()
            return summary if summary else content[:200] + "..."
            
        except Exception as e:
            print(f"Content summary failed: {e}")
            return content[:200] + "..."

# Global instances
search_tool = EnhancedSearchTool()