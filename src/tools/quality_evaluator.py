"""
Critic tools for SAGA Biography Generation System.
Provides biography quality assessment and Hero's Journey scale evaluation.
"""

import re
import json
from typing import Dict, Any
from src.models.client_manager import model_manager
from autogen_core.models import UserMessage

class CriticEvaluationError(Exception):
    """Critic evaluation related errors."""
    pass

class BiographyQualityCritic:
    """Biography quality critic with 8-dimension detailed analysis."""
    
    async def evaluate_biography_quality(self, biography: str) -> Dict[str, Any]:
        """Evaluate biography quality using 8-dimension detailed analysis."""
        try:
            evaluation_prompt = f"""Please conduct a comprehensive 8-dimension quality assessment of this biography and provide detailed improvement suggestions:

Biography content:
{biography}

Evaluation dimensions (10-point scale, strict scoring):

1. Content Completeness (15%): Life stage coverage, important event completeness
   Scoring criteria: 9-10 points (complete), 7-8 points (basically complete), 5-6 points (incomplete), <5 points (seriously insufficient)

2. Emotional Depth (15%): Emotional expression authenticity, infectiousness, resonance
   Scoring criteria: 9-10 points (deeply moving), 7-8 points (emotional), 5-6 points (emotionally flat), <5 points (mechanical narration)

3. Literary Quality (15%): Language expression, narrative skills, literary beauty
   Scoring criteria: 9-10 points (beautiful writing), 7-8 points (fluent language), 5-6 points (average language), <5 points (rough language)

4. Historical Integration (15%): Integration degree of personal experience with historical background
   Scoring criteria: 9-10 points (deep integration), 7-8 points (with background), 5-6 points (shallow background), <5 points (lacking historical dimension)

5. Narrative Coherence (10%): Story structure logic, timeline clarity
6. Personal Growth (15%): Growth trajectory display, transformation description, wisdom embodiment  
7. Authenticity (10%): Detail credibility, emotional authenticity
8. Uniqueness (5%): Personal characteristics, unique perspective, differentiated expression

Please provide detailed assessment in JSON format:
{{
  "overall_score": Overall score (1-10),
  "dimension_scores": {{
    "content_completeness": score,
    "emotional_depth": score,
    "literary_quality": score,
    "historical_integration": score,
    "narrative_coherence": score,
    "personal_growth": score,
    "authenticity": score,
    "uniqueness": score
  }},
  "dimension_analysis": {{
    "content_completeness": {{
      "score": score,
      "issues": ["specific missing content"],
      "suggestions": ["improvement suggestions"],
      "needs_interview": true/false,
      "interview_questions": ["suggested questions if interview needed"]
    }},
    "emotional_depth": {{
      "score": score,
      "issues": ["insufficient emotional expression"],
      "suggestions": ["how to enhance emotions"],
      "needs_interview": true/false,
      "interview_questions": ["questions to explore emotions"]
    }},
    "literary_quality": {{
      "score": score,
      "issues": ["literary expression problems"],
      "suggestions": ["language improvement suggestions"],
      "needs_interview": false,
      "interview_questions": []
    }},
    "historical_integration": {{
      "score": score,
      "issues": ["missing historical background"],
      "suggestions": ["historical research suggestions"],
      "needs_interview": true/false,
      "interview_questions": ["historical background related questions"]
    }},
    "narrative_coherence": {{
      "score": score,
      "issues": ["structural problems"],
      "suggestions": ["structural improvement suggestions"],
      "needs_interview": false,
      "interview_questions": []
    }},
    "personal_growth": {{
      "score": score,
      "issues": ["insufficient growth description"],
      "suggestions": ["growth trajectory suggestions"],
      "needs_interview": true/false,
      "interview_questions": ["growth related questions"]
    }},
    "authenticity": {{
      "score": score,
      "issues": ["authenticity problems"],
      "suggestions": ["suggestions to enhance authenticity"],
      "needs_interview": true/false,
      "interview_questions": ["detail supplement questions"]
    }},
    "uniqueness": {{
      "score": score,
      "issues": ["insufficient personalization"],
      "suggestions": ["suggestions to highlight characteristics"],
      "needs_interview": true/false,
      "interview_questions": ["personal characteristic questions"]
    }}
  }},
  "improvement_priority": ["improvement points sorted by priority"],
  "needs_additional_interview": true/false,
  "interview_focus_areas": ["focus areas if interview needed"],
  "meets_standard": Whether meets 9.0 publication standard (true/false),
  "quality_level": "Publication level/needs fine-tuning/needs rewrite/needs re-interview",
  "major_issues": ["major issue list"],
  "action_plan": {{
    "immediate_actions": ["immediately executable improvements"],
    "interview_required": ["content requiring interview supplement"],
    "research_required": ["content requiring historical research"],
    "rewrite_sections": ["sections needing rewrite"]
  }}
}}

Please score strictly, focusing on whether additional interviews are needed to supplement missing information."""
            
            client = model_manager.current_client
            response = await client.create(
                messages=[UserMessage(content=evaluation_prompt, source="user")]
            )
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Ensure returned result contains all necessary fields
                if "needs_additional_interview" not in result:
                    result["needs_additional_interview"] = False
                if "interview_focus_areas" not in result:
                    result["interview_focus_areas"] = []
                return result
            else:
                return {
                    "overall_score": 0.0,
                    "dimension_scores": {},
                    "feedback": "Assessment failed",
                    "improvement_suggestions": [],
                    "meets_standard": False,
                    "quality_level": "Assessment failed",
                    "major_issues": ["Assessment system error"],
                    "needs_additional_interview": False,
                    "interview_focus_areas": []
                }
                
        except Exception as e:
            print(f"Quality assessment error: {e}")
            return {
                "overall_score": 0.0,
                "dimension_scores": {},
                "feedback": f"Assessment error: {str(e)}",
                "improvement_suggestions": [],
                "meets_standard": False,
                "quality_level": "Assessment failed",
                "major_issues": ["System error"],
                "needs_additional_interview": False,
                "interview_focus_areas": []
            }

class HeroJourneyScaleEvaluator:
    """Hero's Journey Scale evaluation tool."""
    
    def __init__(self):
        self.items = {
            "Protagonist": [
                "I consider myself the hero/main character of my life journey",
                "In my life story, I play an important leading role", 
                "I see myself as the central figure of my own life story"
            ],
            "Shift": [
                "My life is full of adventures and new experiences",
                "I have experienced important life turning points and changes",
                "My life has many unexpected transformations"
            ],
            "Quest": [
                "My life has clear goals and missions",
                "I know what I want to pursue in life",
                "I have a clear life direction and purpose"
            ],
            "Allies": [
                "I have mentors and friends to guide and support me",
                "Important people have helped me in my life journey",
                "I have received guidance and support from key figures"
            ],
            "Challenge": [
                "I have worked hard to overcome difficulties and obstacles in life",
                "I have faced major challenges and tests",
                "I have conquered important difficulties on my life path"
            ],
            "Transformation": [
                "I have become a better version of myself",
                "Through life experiences, I have gained important growth and change",
                "I have undergone profound personal transformation in my life journey"
            ],
            "Legacy": [
                "I will have a lasting positive impact on others",
                "My life experiences will inspire and help others",
                "I will leave a meaningful life legacy"
            ]
        }
    
    async def evaluate_biography(self, biography: str, person_name: str) -> Dict[str, Any]:
        """Evaluate Hero's Journey score based on biography content."""
        try:
            evaluation_prompt = f"""Please score the Hero's Journey Scale based on the following biography content, from the first-person perspective (as {person_name} themselves):

Biography content:
{biography}

Hero's Journey Scale items (1-7 points, 1=strongly disagree, 7=strongly agree):

Protagonist:
1. I consider myself the hero/main character of my life journey
2. In my life story, I play an important leading role
3. I see myself as the central figure of my own life story

Shift:
4. My life is full of adventures and new experiences
5. I have experienced important life turning points and changes
6. My life has many unexpected transformations

Quest:
7. My life has clear goals and missions
8. I know what I want to pursue in life
9. I have a clear life direction and purpose

Allies:
10. I have mentors and friends to guide and support me
11. Important people have helped me in my life journey
12. I have received guidance and support from key figures

Challenge:
13. I have worked hard to overcome difficulties and obstacles in life
14. I have faced major challenges and tests
15. I have conquered important difficulties on my life path

Transformation:
16. I have become a better version of myself
17. Through life experiences, I have gained important growth and change
18. I have undergone profound personal transformation in my life journey

Legacy:
19. I will have a lasting positive impact on others
20. My life experiences will inspire and help others
21. I will leave a meaningful life legacy

Please return scoring results in JSON format:
{{
  "person_name": "{person_name}",
  "dimension_scores": {{
    "Protagonist": [score1, score2, score3],
    "Shift": [score4, score5, score6],
    "Quest": [score7, score8, score9],
    "Allies": [score10, score11, score12],
    "Challenge": [score13, score14, score15],
    "Transformation": [score16, score17, score18],
    "Legacy": [score19, score20, score21]
  }},
  "dimension_averages": {{
    "Protagonist": average score,
    "Shift": average score,
    "Quest": average score,
    "Allies": average score,
    "Challenge": average score,
    "Transformation": average score,
    "Legacy": average score
  }},
  "total_score": total score (sum of all 21 items),
  "percentage_score": percentage score (total score/147*100),
  "interpretation": "interpretation based on score"
}}"""
            
            client = model_manager.current_client
            response = await client.create(
                messages=[UserMessage(content=evaluation_prompt, source="user")]
            )
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Assessment failed"}
                
        except Exception as e:
            print(f"Hero's Journey Scale assessment error: {e}")
            return {"error": str(e)}

# Global instances
quality_critic = BiographyQualityCritic()
hero_evaluator = HeroJourneyScaleEvaluator()