"""
Historical analysis tools for SAGA Biography Generation System.
Provides event anchor extraction and historical context research.
"""

import re
import json
from typing import Dict, Any, List
from src.tools.search import search_tool
from src.models.client_manager import model_manager
from autogen_core.models import UserMessage

class HistoryAnalysisError(Exception):
    """History analysis related errors."""
    pass

class EventAnchorExtractor:
    """Intelligent extraction of meaningful event anchors from interview content."""
    
    async def extract_event_anchors(self, interview_content: str) -> Dict[str, Any]:
        """Extract meaningful event anchors from interview content intelligently."""
        try:
            print(f"Starting intelligent event extraction, analyzing interview content, length: {len(interview_content)} chars")
            
            # Use model to intelligently analyze interview content to extract meaningful event anchors
            prompt = f"""Please intelligently analyze the following interview content and extract truly historically significant event anchors.

Interview content:
{interview_content}

Extraction rules:
1. Time anchors: Only extract periods with historical research value
   - ✅ Valid: 1970s, Cultural Revolution period, early reform era, 1990s, new century, pandemic period
   - ❌ Invalid: after full moon, 3 years old, childhood, when grown up (too vague or without historical value)

2. Location anchors: Only extract specific geographical locations related to historical background
   - ✅ Valid: Beijing, Shanghai, Shenzhen, rural areas, certain province certain city
   - ❌ Invalid: home, school, company (too generalized)

3. Historical event anchors: Extract major events that can be searched for historical background
   - ✅ Valid: college entrance exam restoration, layoff wave, state enterprise reform, housing allocation, one-child policy
   - ❌ Invalid: personal life trivia, family internal events

4. Social phenomenon anchors: Social phenomena that can reflect characteristics of the era
   - ✅ Valid: educated youth going to countryside, worker layoffs, college expansion, housing price rise
   - ❌ Invalid: personal character traits, family relationships

Extraction standards:
- Must be content that can find relevant historical materials through Google search
- Must be information with research value for historical background
- Must be specific and clear time, place, events

Please return in JSON format, only including valuable anchors:
{{
  "temporal_anchors": ["Specific periods, e.g.: 1980s", "early reform era"],
  "location_anchors": ["Specific locations, e.g.: Beijing", "Northeast industrial zone"],  
  "historical_events": ["Specific historical events, e.g.: college entrance exam restoration", "state enterprise reform"],
  "social_phenomena": ["Social phenomena, e.g.: layoff wave", "housing reform"],
  "search_queries": [
    {{
      "query": "Search keyword combination",
      "period": "Time range",
      "location": "Location",
      "focus": "Research focus"
    }}
  ]
}}

Note: Strictly filter according to standards, prefer extracting less rather than extracting valueless information."""
            
            client = model_manager.current_client
            response = await client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )
            
            # Parse GPT response
            content = response.content
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Log detailed extraction content
                temporal_anchors = result.get('temporal_anchors', [])
                location_anchors = result.get('location_anchors', [])
                historical_events = result.get('historical_events', [])
                social_phenomena = result.get('social_phenomena', [])
                search_queries = result.get('search_queries', [])
                
                detail_log = f"""Intelligent event anchor extraction details:
🕐 Time anchors({len(temporal_anchors)}): {', '.join(temporal_anchors[:3])}{'...' if len(temporal_anchors) > 3 else ''}
📍 Location anchors({len(location_anchors)}): {', '.join(location_anchors[:3])}{'...' if len(location_anchors) > 3 else ''}
📜 Historical events({len(historical_events)}): {', '.join(historical_events[:3])}{'...' if len(historical_events) > 3 else ''}
🌍 Social phenomena({len(social_phenomena)}): {', '.join(social_phenomena[:2])}{'...' if len(social_phenomena) > 2 else ''}
🔍 Search queries({len(search_queries)}): Precise search strategy generated"""
                
                print(f"\n{detail_log}")
                
                # Compatible with original format while preserving new structure
                final_result = {
                    "temporal_anchors": temporal_anchors,
                    "location_anchors": location_anchors,
                    "experience_anchors": historical_events + social_phenomena,  # Merge as experience anchors for compatibility
                    "extracted_events": [
                        {
                            "time": anchor.get("period", ""),
                            "location": anchor.get("location", ""),
                            "event": anchor.get("focus", "")
                        } for anchor in search_queries
                    ],
                    # New fields
                    "historical_events": historical_events,
                    "social_phenomena": social_phenomena,
                    "search_queries": search_queries
                }
                
                return final_result
            else:
                # If no JSON found, create default structure
                print("Intelligent event extraction failed: Unable to parse JSON format")
                return {
                    "temporal_anchors": [],
                    "location_anchors": [],
                    "experience_anchors": [],
                    "extracted_events": [],
                    "historical_events": [],
                    "social_phenomena": [],
                    "search_queries": []
                }
                
        except Exception as e:
            print(f"Intelligent event extraction error: {e}")
            return {
                "temporal_anchors": [],
                "location_anchors": [],
                "experience_anchors": [],
                "extracted_events": [],
                "historical_events": [],
                "social_phenomena": [],
                "search_queries": []
            }

class Contextualizer:
    """Enhanced historical background researcher using intelligent search strategies."""
    
    async def research_historical_context_enhanced(self, anchors: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced historical background research using intelligent search strategies."""
        historical_context = {
            "historical_events": {},
            "social_context": {},
            "search_results": [],
            "crawled_summaries": []
        }
        
        try:
            print(f"Starting intelligent historical research: Processing intelligently extracted event anchors")
            
            # Prioritize using intelligently generated search queries
            search_queries = anchors.get("search_queries", [])
            if search_queries:
                print(f"🎯 Using intelligent search strategy, {len(search_queries)} precise queries total")
                for i, query_info in enumerate(search_queries, 1):
                    search_query = query_info.get("query", "")
                    period = query_info.get("period", "")
                    location = query_info.get("location", "")
                    focus = query_info.get("focus", "")
                    
                    print(f"🔍 Executing query {i}: {search_query}")
                    search_results = await search_tool.search_enhanced(search_query, 3, 2)
                    
                    if search_results.get("results"):
                        # Integrate search results and crawled content
                        all_content = f"Search topic: {focus}\nTime range: {period}\nGeographic scope: {location}\n\n"
                        crawled_summaries = []
                        
                        for result in search_results["results"][:3]:
                            all_content += f"Title: {result.get('title', '')}\n"
                            all_content += f"Summary: {result.get('snippet', '')}\n"
                            
                            if result.get("has_crawled_content"):
                                original_content = result.get("content", "") or ""
                                # Summarize content
                                if original_content and len(original_content) > 300:
                                    print(f"📝 Summarizing web content: {result.get('title', '')[:50]}...")
                                    # Limit input content length to 100000 characters to avoid context overflow
                                    truncated_content = original_content[:100000] if len(original_content) > 100000 else original_content
                                    if len(original_content) > 100000:
                                        print(f"⚠️ Content too long({len(original_content)} chars), truncated to first 100000 chars")
                                    content_summary = await search_tool.summarize_search_content(truncated_content, result.get('title', ''))
                                    all_content += f"Content summary: {content_summary}\n"
                                else:
                                    content_summary = original_content
                                    all_content += f"Detailed content: {content_summary}\n"
                                    
                                crawled_summaries.append({
                                    "url": result.get("link", ""),
                                    "title": result.get("title", ""),
                                    "summary": content_summary,
                                    "original_length": len(original_content) if original_content else 0
                                })
                            all_content += "\n"
                        
                        # Generate professional historical background analysis
                        analysis_prompt = f"""Based on the following search results and detailed web content, provide professional historical background analysis for personal biography:

Search content:
{all_content}

Analysis requirements:
1. Focus on analyzing historical background of {period} period in {location} region
2. In-depth research on specific impacts of {focus} on ordinary people's lives
3. Provide detailed description of era characteristics and social environment
4. Analyze policy background, economic environment, cultural atmosphere
5. Elaborate on the meaning and value of personal experiences in historical currents

Please provide in-depth historical background analysis (800-1200 words):"""
                        
                        client = model_manager.current_client
                        response = await client.create(
                            messages=[UserMessage(content=analysis_prompt, source="user")]
                        )
                        
                        key = f"{period}_{location}_{focus}"
                        historical_context["historical_events"][key] = response.content
                        historical_context["search_results"].append({
                            "anchor": key,
                            "query": search_query,
                            "results": search_results["results"][:3]
                        })
                        historical_context["crawled_summaries"].extend(crawled_summaries)
                        
                        crawled_count = len(crawled_summaries)
                        search_log = f"""Intelligent historical research - {focus}:
🔍 Search query: {search_query}
⏰ Time range: {period}
📍 Geographic scope: {location}
📚 Search results: {len(search_results["results"])}
🕷️ Crawled pages: {crawled_count}
📖 Analysis length: {len(response.content)} chars"""
                        
                        print(f"\n{search_log}")
            
            # Supplementary research: Handle traditional time anchors (if intelligent search results insufficient)
            if len(search_queries) < 2:  # If intelligent search queries are few, supplement with traditional approach
                temporal_anchors = anchors.get("temporal_anchors", [])
                for time_anchor in temporal_anchors:
                    if time_anchor and len(time_anchor) > 3:  # Filter out too short meaningless anchors
                        search_query = f"China {time_anchor} historical background social changes policy impact"
                        search_results = await search_tool.search_enhanced(search_query, 2, 1)
                        
                        if search_results.get("results"):
                            all_content = ""
                            for result in search_results["results"][:2]:
                                all_content += f"Title: {result.get('title', '')}\n"
                                all_content += f"Summary: {result.get('snippet', '')}\n"
                                if result.get("has_crawled_content"):
                                    original_content = result.get("content", "") or ""
                                    if original_content and len(original_content) > 300:
                                        print(f"📝 Summarizing time anchor content: {result.get('title', '')[:50]}...")
                                        # Limit input content length to 100000 characters to avoid context overflow
                                        truncated_content = original_content[:100000] if len(original_content) > 100000 else original_content
                                        if len(original_content) > 100000:
                                            print(f"⚠️ Time anchor content too long({len(original_content)} chars), truncated to first 100000 chars")
                                        content_summary = await search_tool.summarize_search_content(truncated_content, result.get('title', ''))
                                        all_content += f"Content summary: {content_summary}\n"
                                    else:
                                        all_content += f"Detailed content: {original_content}\n"
                                all_content += "\n"
                            
                            analysis_prompt = f"""Supplementary research on {time_anchor} period historical background:

{all_content}

Please provide social background analysis for this period, focusing on impacts on ordinary people's lives."""
                            
                            client = model_manager.current_client
                            response = await client.create(
                                messages=[UserMessage(content=analysis_prompt, source="user")]
                            )
                            
                            historical_context["social_context"][time_anchor] = response.content
            
            # Handle location anchors (only process specific geographical locations)
            location_anchors = anchors.get("location_anchors", [])
            for location_anchor in location_anchors:
                if location_anchor and len(location_anchor) > 1 and location_anchor not in ["home", "school", "company"]:
                    search_query = f"{location_anchor} history culture development changes local characteristics"
                    search_results = await search_tool.search_enhanced(search_query, 2, 1)
                    
                    if search_results.get("results"):
                        all_content = ""
                        for result in search_results["results"][:2]:
                            all_content += f"Title: {result.get('title', '')}\n"
                            all_content += f"Summary: {result.get('snippet', '')}\n"
                            if result.get("has_crawled_content"):
                                original_content = result.get("content", "") or ""
                                if original_content and len(original_content) > 300:
                                    print(f"📝 Summarizing location anchor content: {result.get('title', '')[:50]}...")
                                    # Limit input content length to 100000 characters to avoid context overflow
                                    truncated_content = original_content[:100000] if len(original_content) > 100000 else original_content
                                    if len(original_content) > 100000:
                                        print(f"⚠️ Location anchor content too long({len(original_content)} chars), truncated to first 100000 chars")
                                    content_summary = await search_tool.summarize_search_content(truncated_content, result.get('title', ''))
                                    all_content += f"Content summary: {content_summary}\n"
                                else:
                                    all_content += f"Detailed content: {original_content}\n"
                            all_content += "\n"
                        
                        analysis_prompt = f"""Analyze regional background of {location_anchor}:

{all_content}

Please provide historical and cultural background and local characteristics of this region, as well as impacts on local people's lives."""
                        
                        client = model_manager.current_client
                        response = await client.create(
                            messages=[UserMessage(content=analysis_prompt, source="user")]
                        )
                        
                        historical_context["social_context"][location_anchor] = response.content
                        
            return historical_context
            
        except Exception as e:
            print(f"Intelligent historical research error: {e}")
            return historical_context

# Global instances
event_extractor = EventAnchorExtractor()
contextualizer = Contextualizer()