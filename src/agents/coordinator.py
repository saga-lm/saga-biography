"""
Critic agent for SAGA Biography Generation System.
Manages the entire biography generation workflow and decision making.
"""

from typing import Dict, Any, List
from datetime import datetime
from src.agents.interview_agent import interview_manager
from src.tools.history_analyzer import event_extractor, contextualizer
from src.agents.writer_agent import biography_manager
from src.tools.quality_evaluator import quality_critic, hero_evaluator

class BiographyCritic:
    """Central critic for biography generation workflow."""
    
    def __init__(self):
        self.current_stage = "initialization"
        self.stage_results = {}
    
    async def process_person_biography(self, person_data: Dict[str, Any], person_id: str) -> Dict[str, Any]:
        """Process complete biography generation for a single person."""
        person_name = person_data["person_info"]["name"]
        print(f"\nStarting user processing: {person_id}")
        
        result = {
            "person_id": person_id,
            "person_name": person_name,
            "timestamp": datetime.now().isoformat(),
            "status": "started",
            "stages": {},
            "final_biography": "",
            "quality_score": 0.0,
            "hero_journey_score": {},
            "error": None
        }
        
        try:
            print(f"Processing user: {person_name} ({person_id})")
            
            # Stage 1: Simulate interview dialogue
            print("🎤 Starting interview stage...")
            self.current_stage = "interview"
            interview_result = await interview_manager.conduct_agent_interview(person_data, person_id)
            result["stages"]["interview"] = interview_result
            interview_content = interview_result["content"]
            
            print(f"✅ Interview completed")
            print(f"📊 Interview statistics: {interview_result['question_count']} questions, {interview_result['response_count']} responses")
            
            # Stage 2: Extract event anchors
            print("🔍 Starting event analysis stage...")
            self.current_stage = "event_analysis"
            anchors = await event_extractor.extract_event_anchors(interview_content)
            result["stages"]["anchors"] = anchors
            
            # Stage 3: Research historical background
            print("📚 Starting historical research stage...")
            self.current_stage = "historical_research"
            historical_context = await contextualizer.research_historical_context_enhanced(anchors)
            result["stages"]["historical_context"] = historical_context
            
            # Stage 4: Generate biography
            print("✍️ Starting biography writing stage...")
            self.current_stage = "biography_writing"
            biography = await biography_manager.generate_biography(interview_content, historical_context, person_data)
            result["stages"]["biography"] = biography
            result["final_biography"] = biography
            
            # Stage 5: Quality assessment
            print("📊 Starting quality assessment stage...")
            self.current_stage = "quality_assessment"
            quality_result = await quality_critic.evaluate_biography_quality(biography)
            result["stages"]["quality_evaluation"] = quality_result
            result["quality_score"] = quality_result.get("overall_score", 0.0)
            
            score = result["quality_score"]
            quality_level = quality_result.get("quality_level", "unknown")
            print(f"📊 Quality assessment: {score:.1f}/10.0 ({quality_level})")
            
            # Stage 5.5: Intelligent 8-dimension quality improvement loop
            max_iterations = 5  # Maximum 5 improvement rounds
            current_iteration = 0
            
            print(f"\n📋 Quality improvement plan:")
            print(f"🔄 Rounds 1-2: Supplement interviews (if content insufficient)")
            print(f"🔍 Rounds 2-3: Supplement historical research (if historical integration insufficient)")
            print(f"🏆 Round 3+: Hero's Journey structure refinement (optimize narrative structure)")
            print(f"✍️ Fallback: Literary expression and structure optimization")
            
            while current_iteration < max_iterations and not quality_result.get("meets_standard", False):
                current_iteration += 1
                print(f"\n🔄 Round {current_iteration} 8-dimension quality improvement ({quality_level})")
                
                # Develop intelligent improvement path: interview→historical research→Hero's Journey→literary optimization
                action_plan = quality_result.get("action_plan", {})
                interview_required = action_plan.get("interview_required", [])
                research_required = action_plan.get("research_required", [])
                needs_interview = quality_result.get("needs_additional_interview", False)
                
                improvement_done = False
                
                # Priority 1: Supplement interview (if content seriously insufficient)
                if (needs_interview or interview_required) and current_iteration <= 2:
                    print("📝 Based on 8-dimension analysis, need to supplement interview for missing information...")
                    focus_areas = quality_result.get("interview_focus_areas", [])
                    print(f"🎯 Interview focus: {', '.join(focus_areas)}")
                    
                    additional_interview = await self._conduct_additional_interview_enhanced(
                        person_data, person_id, quality_result
                    )
                    # Integrate new interview content with original content
                    interview_content += f"\n\n=== Supplement interview round {current_iteration} ===\n{additional_interview}"
                    
                    # Regenerate biography based on enhanced interview content
                    print("✍️ Regenerating biography based on supplemented interview...")
                    biography = await biography_manager.generate_biography(interview_content, historical_context, person_data)
                    improvement_done = True
                
                # Priority 2: Supplement historical research (if historical integration insufficient)
                elif research_required and current_iteration <= 3:
                    print("🔍 Based on historical integration dimension analysis, need to supplement historical research...")
                    enhanced_context = await self._research_missing_historical_context(quality_result, historical_context)
                    
                    # Check if successfully obtained new historical information
                    if enhanced_context and any(enhanced_context.values()):
                        historical_context.update(enhanced_context)
                        print("✍️ Regenerating biography based on supplemented historical background...")
                        biography = await biography_manager.generate_biography(interview_content, historical_context, person_data)
                        improvement_done = True
                    else:
                        print("⚠️ Historical research limited, jumping to next improvement strategy...")
                        # Don't set improvement_done=True, let it continue to next strategy
                
                # Priority 3: Hero's Journey structure refinement (if narrative structure needs optimization)
                elif current_iteration == 3 or (not improvement_done and current_iteration >= 2):
                    print("🏆 Conducting Hero's Journey structure refinement...")
                    biography = await biography_manager.enhance_hero_journey_structure(biography, quality_result, person_name)
                    improvement_done = True
                
                # Priority 4: Literary expression and structure optimization
                if not improvement_done:
                    print("✍️ Conducting literary expression and structure optimization...")
                    biography = await biography_manager.improve_biography(biography, quality_result, historical_context, person_name)
                
                # Re-assess
                print("🔍 Conducting 8-dimension quality reassessment...")
                quality_result = await quality_critic.evaluate_biography_quality(biography)
                result["quality_score"] = quality_result.get("overall_score", 0.0)
                score = result["quality_score"]
                quality_level = quality_result.get("quality_level", "unknown")
                
                # Display detailed improvement results
                print(f"📊 Post-improvement quality: {score:.1f}/10.0 ({quality_level})")
                dimension_scores = quality_result.get("dimension_scores", {})
                print(f"🎯 Dimension scores: Content{dimension_scores.get('content_completeness', 0):.1f} | "
                      f"Emotion{dimension_scores.get('emotional_depth', 0):.1f} | "
                      f"Literary{dimension_scores.get('literary_quality', 0):.1f} | "
                      f"History{dimension_scores.get('historical_integration', 0):.1f}")
                
                if quality_result.get("meets_standard", False):
                    print("🎉 8-dimension quality meets standard, improvement completed!")
                    break
                elif current_iteration >= max_iterations:
                    print("⚠️ Reached maximum improvement rounds, ending improvement")
                    remaining_issues = quality_result.get("major_issues", [])
                    if remaining_issues:
                        print(f"⚠️ Remaining issues: {', '.join(remaining_issues[:3])}")
                        
            # Update final results
            result["final_biography"] = biography
            result["final_quality_score"] = score
            result["improvement_iterations"] = current_iteration
            
            # Stage 6: Hero's Journey Scale assessment
            print("🏆 Starting Hero's Journey assessment...")
            self.current_stage = "hero_journey_assessment"
            hero_result = await hero_evaluator.evaluate_biography(biography, person_name)
            result["stages"]["hero_journey"] = hero_result
            result["hero_journey_score"] = hero_result
            
            if 'total_score' in hero_result:
                hero_score = hero_result['total_score']
                hero_percentage = hero_result.get('percentage_score', 0)
                print(f"🏆 Hero's Journey: {hero_score}/147 points ({hero_percentage:.1f}%)")
            
            result["status"] = "completed"
            print(f"✅ User {person_name} processing completed, quality score: {result['quality_score']:.1f}/10.0")
            
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "failed"
            print(f"❌ User {person_id} processing failed: {e}")
            
        return result
    
    async def _conduct_additional_interview_enhanced(self, person_data: Dict[str, Any], person_id: str, quality_result: Dict[str, Any]) -> str:
        """Conduct enhanced supplementary interview based on 8-dimension analysis."""
        person_name = person_data["person_info"]["name"]
        dimension_analysis = quality_result.get("dimension_analysis", {})
        interview_focus_areas = quality_result.get("interview_focus_areas", [])
        overall_score = quality_result.get("overall_score", 0.0)
        
        # Collect dimensions and specific gaps needing supplement
        focus_dimensions = []
        specific_issues = []
        interview_questions = []
        
        # Force check: If quality below 8.5, force supplementary interview
        force_interview = overall_score < 8.5
        
        for dimension, analysis in dimension_analysis.items():
            # More lenient interview trigger conditions
            if analysis.get("needs_interview", False) or analysis.get("score", 10) < 8.0 or force_interview:
                focus_dimensions.append(dimension)
                # Collect specific issues
                issues = analysis.get("issues", [])
                specific_issues.extend(issues)
                # Collect recommended interview questions
                questions = analysis.get("interview_questions", [])
                interview_questions.extend(questions)
        
        # If no clear issues but quality not up to standard, create general questions
        if not specific_issues and overall_score < 8.5:
            specific_issues = ["Content depth insufficient", "Emotional expression needs enhancement", "Personal experiences need supplement"]
            focus_dimensions = ["content_completeness", "emotional_depth"]
        
        print(f"🎯 Dimensions needing supplement: {', '.join(focus_dimensions)}")
        print(f"📝 Specific gaps: {'; '.join(specific_issues[:3])}...")
        print(f"🔍 Current quality score: {overall_score:.1f}/10.0")
        
        # If really no content needing interview, return directly
        if not specific_issues and not focus_dimensions and overall_score >= 9.0:
            print("✅ Quality assessment good, no need for supplementary interview")
            return "Quality assessment shows content sufficient, no need for supplementary interview."
        
        # For simplicity, generate a mock supplementary interview based on the issues
        # In a real system, this would involve creating additional agents
        supplementary_content = f"Supplementary interview conducted focusing on: {', '.join(focus_dimensions)}\n"
        supplementary_content += f"Addressed issues: {'; '.join(specific_issues[:3])}\n"
        supplementary_content += f"This supplementary interview provided additional details about {person_name}'s life experiences.\n"
        
        return supplementary_content
    
    async def _research_missing_historical_context(self, quality_result: Dict[str, Any], historical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Research missing historical context based on quality assessment."""
        # For simplicity, return enhanced context
        # In a real system, this would involve additional research
        enhanced_context = {
            "supplementary_research": "Additional historical research conducted based on quality assessment feedback."
        }
        return enhanced_context

# Global instance
biography_critic = BiographyCritic()