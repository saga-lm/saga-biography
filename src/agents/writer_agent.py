"""
Bio Manager for SAGA Biography Generation System.
Provides professional biography writing capabilities using Hero's Journey framework.
"""

from typing import Dict, Any
from src.models.client_manager import model_manager
from autogen_core.models import UserMessage

class BiographyManager:
    """Professional biography manager using Hero's Journey framework."""
    
    def __init__(self):
        self.client = model_manager.current_client
    
    async def generate_biography(self, interview_content: str, historical_context: Dict[str, Any], person_data: Dict[str, Any]) -> str:
        """Generate biography using Hero's Journey structure."""
        
        person_info = person_data["person_info"]
        person_name = person_info["name"]
        basic_data = person_info.get("basic_data", {})
        personal_bg = person_info.get("personal_background", {})
        
        person_summary = f"""
Basic information:
- Name: {person_info.get('name', '')}
- Age: {basic_data.get('current_age', '')} years old
- Gender: {basic_data.get('gender', '')}
- Birth year: {basic_data.get('birth_year', '')}

Family background:
- Father's occupation: {basic_data.get('father_occupation', '')}
- Mother's occupation: {basic_data.get('mother_occupation', '')}
- Economic status: {personal_bg.get('family_details', {}).get('economic_status', '')}

Personal characteristics:
- Personality: {personal_bg.get('personality', {}).get('main_trait', '')}
- Appearance: {personal_bg.get('appearance', {}).get('description', '')}

Main life events:"""

        # Build writing prompt
        historical_summary = ""
        for time_period, context in historical_context.get("historical_events", {}).items():
            historical_summary += f"\n{time_period} period background: {context}\n"
        
        for location, context in historical_context.get("social_context", {}).items():
            historical_summary += f"\n{location} regional background: {context}\n"
        
        writing_prompt = f"""Please create a deeply moving personal biography for {person_name} based on the following interview content and historical background.

Hero's Journey structure requirements:
- Protagonist: Recognition of oneself as the hero/main character of life
- Shift: Key turning points and new experiences  
- Quest: Clear goals and life missions
- Allies: Support from others and mentors
- Challenge: Obstacles and difficulties faced
- Transformation: Personal growth and change
- Legacy: Lasting impact on others

Character profile:
{person_summary}

Interview content:
{interview_content}

Historical background:
{historical_summary}

Writing requirements:
1. Organize content according to Hero's Journey 7-dimension structure
2. First-person perspective, authentic and moving language
3. Naturally integrate personal experiences with historical background
4. Highlight personal growth, resilient qualities and life wisdom
5. Rich emotional expression and psychological description
6. Beautiful literary language and narrative rhythm
7. Complete structure, clear logic, engaging
8. Word count controlled to 2000-3000 words

Please create a high-quality personal biography:"""
        
        try:
            response = await self.client.create(
                messages=[UserMessage(content=writing_prompt, source="user")]
            )
            
            biography = response.content
            return biography
            
        except Exception as e:
            print(f"Biography generation error: {e}")
            return f"Biography generation failed: {str(e)}"
    
    async def improve_biography(self, biography: str, quality_result: Dict[str, Any], historical_context: Dict[str, Any], person_name: str) -> str:
        """Improve biography based on quality assessment results."""
        feedback = quality_result.get("feedback", "")
        suggestions = quality_result.get("improvement_suggestions", [])
        major_issues = quality_result.get("major_issues", [])
        dimension_scores = quality_result.get("dimension_scores", {})
        
        # Analyze dimensions most needing improvement
        low_score_dimensions = [dim for dim, score in dimension_scores.items() if score < 7.5]
        
        improvement_prompt = f"""Please comprehensively improve this personal biography based on the following quality assessment feedback:

Original biography:
{biography}

Quality assessment feedback:
{feedback}

Major issues:
{chr(10).join([f"- {issue}" for issue in major_issues])}

Specific improvement suggestions:
{chr(10).join([f"- {suggestion}" for suggestion in suggestions])}

Dimensions needing key improvement:
{chr(10).join([f"- {dim}: {dimension_scores.get(dim, 0):.1f} points" for dim in low_score_dimensions])}

Improvement requirements:
1. Address each specific issue, don't speak generally
2. Enhance emotional depth, add more personal insights and inner experiences
3. Enrich historical background integration, reflect era characteristics
4. Improve narrative structure, ensure clear logic and timeline
5. Enhance literary quality, use more beautiful language expression
6. Maintain first-person authenticity, avoid over-literariness
7. Ensure content completeness and coherence

Please recreate a high-quality personal biography, word count 2500-3500 words:"""
        
        try:
            response = await self.client.create(
                messages=[UserMessage(content=improvement_prompt, source="user")]
            )
            
            improved_biography = response.content.strip()
            
            return improved_biography
            
        except Exception as e:
            print(f"Biography improvement failed: {e}")
            return biography  # Return original version
    
    async def enhance_hero_journey_structure(self, biography: str, quality_result: Dict[str, Any], person_name: str) -> str:
        """Enhance Hero's Journey structure based on quality assessment."""
        dimension_scores = quality_result.get("dimension_scores", {})
        major_issues = quality_result.get("major_issues", [])
        
        enhancement_prompt = f"""Please enhance this biography's Hero's Journey structure based on quality assessment results:

Current biography:
{biography}

Quality assessment results:
- Content completeness: {dimension_scores.get('content_completeness', 0):.1f}/10
- Emotional depth: {dimension_scores.get('emotional_depth', 0):.1f}/10
- Literary quality: {dimension_scores.get('literary_quality', 0):.1f}/10
- Historical integration: {dimension_scores.get('historical_integration', 0):.1f}/10
- Narrative coherence: {dimension_scores.get('narrative_coherence', 0):.1f}/10
- Personal growth: {dimension_scores.get('personal_growth', 0):.1f}/10

Major issues: {'; '.join(major_issues[:3])}

Hero's Journey structure enhancement requirements:
1. **Protagonist**: Strengthen {person_name}'s role as life's protagonist, highlight personal agency and initiative
2. **Shift**: Enhance description of life turning points, make transitions more dramatic and meaningful
3. **Quest**: Clarify life goals and missions, show pursuit process and motivation
4. **Allies**: Highlight support from important people, mentors and friends, show their impact
5. **Challenge**: Deepen description of difficulties faced, show struggle process and coping strategies
6. **Transformation**: Emphasize personal growth and change, show inner transformation process
7. **Legacy**: Highlight impact on others and meaning left behind, show life value

Structure optimization requirements:
- Each Hero's Journey element should have specific life events corresponding
- Ensure clear progression: challenge → struggle → growth → transformation → legacy
- Maintain emotional continuity and narrative tension
- Don't mention "Hero's Journey" terminology in text
- Use rich details and emotional description to make each stage vivid
- Ensure biography reads naturally and fluently, not mechanical

Please recreate an enhanced biography that better embodies Hero's Journey structure:"""
        
        try:
            response = await self.client.create(
                messages=[UserMessage(content=enhancement_prompt, source="user")]
            )
            
            enhanced_biography = response.content.strip()
            return enhanced_biography
            
        except Exception as e:
            print(f"Hero's Journey structure enhancement failed: {e}")
            return biography

# Global instance
biography_manager = BiographyManager()