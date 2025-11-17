"""
User simulation agent for SAGA Biography Generation System.
Simulates users based on all_people_timelines.json data.
"""

from typing import Dict, Any, List
from src.models.client_manager import model_manager
from autogen_core.models import UserMessage

class UserSimulationAgent:
    """User simulation agent based on all_people_timelines.json data."""
    
    def __init__(self, user_data: Dict[str, Any]):
        self.user_data = user_data
        self.person_info = user_data.get("person_info", {})
        self.life_timeline = user_data.get("life_timeline", [])
        self.current_question_count = 0
        self.revealed_info = []  # Information already revealed
        # User simulation agent fixed to use openai-gpt4 model
        self.model_client = model_manager.create_client("openai-gpt4")
        
    def get_basic_intro(self) -> str:
        """Generate basic self-introduction."""
        name = self.person_info.get("name", "")
        basic_data = self.person_info.get("basic_data", {})
        personal_bg = self.person_info.get("personal_background", {})
        
        age = basic_data.get("current_age", "")
        gender = basic_data.get("gender", "")
        personality = personal_bg.get("personality", {})
        
        intro = f"Hello, my name is {name}"
        if age:
            intro += f", I'm {age} years old"
        if gender:
            intro += f", {gender}"
        if personality.get("main_trait"):
            intro += f". My personality trait is {personality.get('main_trait')}, {personality.get('behavior', '')}"
            
        return intro
    
    async def respond_to_question(self, question: str) -> str:
        """Generate intelligent responses based on questions and personal data."""
        self.current_question_count += 1
        
        # Build personal background information
        person_info = self.user_data.get("person_info", {})
        name = person_info.get("name", "")
        basic_data = person_info.get("basic_data", {})
        personal_bg = person_info.get("personal_background", {})
        
        # Prepare life timeline information
        timeline_context = ""
        for event in self.life_timeline[:10]:  # Use first 10 important events
            timeline_context += f"- {event.get('age')} years old: {event.get('description', '')}\n"
            if event.get('details'):
                timeline_context += f"  Details: {event.get('details', '')}\n"
        
        # Build intelligent response prompt
        response_prompt = f"""You are {name}, undergoing a life story interview. Please answer the interviewer's questions naturally in first person.

Personal basic information:
- Name: {name}
- Age: {basic_data.get('current_age', '')} years old
- Personality: {personal_bg.get('personality', {}).get('main_trait', '')}
- Behavioral traits: {personal_bg.get('personality', {}).get('behavior', '')}

Important life experiences:
{timeline_context}

Interviewer's question: "{question}"

Response requirements:
1. Use first person, natural and simple language
2. Based on question content, select relevant events and feelings from your real experiences
3. Maintain authentic emotional expression, not too literary
4. If the question involves things you have experienced, provide specific details
5. If the question involves things you haven't experienced, honestly explain
6. Keep length between 50-200 words, like normal conversation

Please give your response directly, without extra explanations:"""

        try:
            # Use fixed openai-gpt4 model to generate intelligent response
            response = await self.model_client.create(
                messages=[UserMessage(content=response_prompt, source="user")]
            )
            
            answer = response.content.strip()
            
            # Record answered content to avoid repetition
            self.revealed_info.append(f"q{self.current_question_count}_{question[:20]}")
            
            return answer
            
        except Exception as e:
            print(f"Intelligent response generation failed, using basic response: {e}")
            # Fallback to basic response mode
            return self._fallback_basic_response(question)
    
    def _fallback_basic_response(self, question: str) -> str:
        """Fallback basic response mode."""
        # Decide what to answer based on question type and revealed information
        if any(keyword in question for keyword in ["childhood", "young", "growing up", "family", "parents"]):
            return self._respond_about_childhood()
        elif any(keyword in question for keyword in ["work", "career", "job"]):
            return self._respond_about_career()
        elif any(keyword in question for keyword in ["marriage", "wedding", "spouse", "partner"]):
            return self._respond_about_marriage()
        elif any(keyword in question for keyword in ["children", "kids", "birth"]):
            return self._respond_about_children()
        elif any(keyword in question for keyword in ["difficulty", "challenge", "problem", "hard"]):
            return self._respond_about_challenges()
        elif any(keyword in question for keyword in ["achievement", "proud", "success", "happy"]):
            return self._respond_about_achievements()
        else:
            return self._respond_general()
    
    def _respond_about_childhood(self) -> str:
        """Respond to childhood-related questions."""
        basic_data = self.person_info.get("basic_data", {})
        personal_bg = self.person_info.get("personal_background", {})
        family_details = personal_bg.get("family_details", {})
        
        birth_year = basic_data.get("birth_year", "")
        father_job = family_details.get("father_job", "")
        mother_job = family_details.get("mother_job", "")
        economic_status = family_details.get("economic_status", "")
        
        response = f"I was born in {birth_year}."
        if father_job and mother_job:
            response += f"My father {father_job}, mother {mother_job}."
        if economic_status:
            response += f"Our family conditions were {economic_status}."
            
        # Add some specific childhood events, ensure first person
        childhood_events = [event for event in self.life_timeline if event.get("age", 100) < 18]
        if childhood_events:
            event = childhood_events[0]
            details = event.get('details', '').replace(self.person_info.get("name", ""), "I")
            response += f"At that time {details}"
            
        self.revealed_info.append("childhood")
        return response
    
    def _respond_about_career(self) -> str:
        """Respond to career-related questions."""
        work_events = [event for event in self.life_timeline if event.get("type") == "work change"]
        if not work_events:
            return "I mainly do some farm work at home, no fixed job."
            
        # Select a work experience not yet discussed in detail
        for event in work_events:
            if f"work_{event.get('age')}" not in self.revealed_info:
                work_details = event.get("work_details", {})
                response = f"When I was {event.get('age')} years old, I started {event.get('description', '').replace(self.person_info.get('name', ''), 'I')}."
                
                if work_details:
                    workplace = work_details.get("workplace_name", "")
                    job_title = work_details.get("job_title", "")
                    daily_routine = work_details.get("daily_routine", "")
                    income = work_details.get("income", "")
                    challenge = work_details.get("main_challenge", "")
                    
                    response += f"At {workplace} as {job_title}, {daily_routine}."
                    if income:
                        response += f"Income was about {income}."
                    if challenge:
                        response += f"The main difficulty was {challenge}."
                
                self.revealed_info.append(f"work_{event.get('age')}")
                return response
                
        return "I've told you everything about work."
    
    def _respond_about_marriage(self) -> str:
        """Respond to marriage-related questions."""
        marriage_events = [event for event in self.life_timeline if event.get("type") == "marriage"]
        if not marriage_events:
            return "I'm not married yet."
            
        for event in marriage_events:
            if f"marriage_{event.get('age')}" not in self.revealed_info:
                details = event.get('details', '').replace(self.person_info.get('name', ''), 'I')
                response = f"I got married when I was {event.get('age')} years old. {details}"
                self.revealed_info.append(f"marriage_{event.get('age')}")
                return response
                
        return "I've told you everything about marriage."
    
    def _respond_about_children(self) -> str:
        """Respond to children-related questions."""
        birth_events = [event for event in self.life_timeline if event.get("type") == "birth"]
        if not birth_events:
            return "We don't have children yet."
            
        for event in birth_events:
            if f"child_{event.get('age')}" not in self.revealed_info:
                child_details = event.get("child_details", {})
                child_name = child_details.get("name", "child")
                personality = child_details.get("personality", "")
                behavior = child_details.get("behavior", "")
                issue = child_details.get("main_issue", "")
                
                response = f"I gave birth to {child_name} when I was {event.get('age')} years old."
                if personality:
                    response += f"This child is {personality}, {behavior}."
                if issue:
                    response += f"But {issue}, which makes us a bit worried."
                    
                self.revealed_info.append(f"child_{event.get('age')}")
                return response
                
        return "I've told you everything about the children."
    
    def _respond_about_challenges(self) -> str:
        """Respond to difficulty challenge-related questions."""
        challenge_events = [event for event in self.life_timeline 
                          if event.get("type") in ["accidents", "relationships"] 
                          and "challenge" not in str(event)]
        
        if challenge_events:
            event = challenge_events[0]
            response = f"Speaking of difficulties, when I was {event.get('age')} years old {event.get('description', '')}. {event.get('details', '')}"
            return response
        else:
            return "Life always has some unsatisfactory things, but we got through them all. Family economic conditions weren't great, sometimes we worried about money."
    
    def _respond_about_achievements(self) -> str:
        """Respond to achievement-related questions."""
        achievement_events = [event for event in self.life_timeline if event.get("type") == "achievements"]
        if achievement_events:
            event = achievement_events[0]
            return f"What makes me proud is that when I was {event.get('age')} years old {event.get('description', '')}. {event.get('details', '')}"
        else:
            return "The biggest achievement is raising the children, although we're not wealthy, the whole family is safe and sound."
    
    def _respond_general(self) -> str:
        """General response."""
        # Randomly select an event not yet mentioned
        unused_events = [event for event in self.life_timeline 
                        if f"general_{event.get('age')}" not in self.revealed_info]
        
        if unused_events:
            event = unused_events[0]
            self.revealed_info.append(f"general_{event.get('age')}")
            return f"When I was {event.get('age')} years old {event.get('description', '')}. {event.get('details', '')}"
        else:
            return "I think I've said everything I should say, what else would you like to know?"