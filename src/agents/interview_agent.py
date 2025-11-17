"""
Interview agents for SAGA Biography Generation System.
Provides professional life story interviewing capabilities.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from src.models.client_manager import model_manager
from src.agents.user_simulation import UserSimulationAgent

class InterviewManager:
    """Manages interview sessions and agent interactions."""
    
    def __init__(self):
        self.interview_client = model_manager.create_client()
    
    async def conduct_agent_interview(self, person_data: Dict[str, Any], person_id: str) -> Dict[str, Any]:
        """Conduct agent-based interview using AutoGen agents."""
        person_info = person_data["person_info"]
        person_name = person_info["name"]
        
        print(f"Starting Agent interview mode for {person_name}, creating user simulation agent")
        
        # Create user simulation agent (based on real data)
        user_agent = self._create_user_simulation_agent(person_data, person_id)
        
        # Create specialized interview agent - clear handoff timing
        interview_agent_local = self._create_interview_agent(person_name, person_id)
        
        # Create interview team
        interview_team = Swarm(
            participants=[interview_agent_local, user_agent],
            termination_condition=(
                TextMentionTermination("INTERVIEW_COMPLETE") |
                TextMentionTermination("interview ends here") |
                TextMentionTermination("Thank you for sharing, our interview ends here") |
                TextMentionTermination("Thank you for sharing") |
                MaxMessageTermination(50)  # Maximum 50 rounds of dialogue
            )
        )
        
        # Start interview process
        print(f"🎤 Starting Agent interview with {person_name}...")
        
        try:
            # Start interview - concise task description
            interview_task = f"Start interview with {person_name}"
            
            # Run interview dialogue
            result = await Console(interview_team.run_stream(task=interview_task))
            
            # Filter and process messages
            valid_messages = []
            for message in result.messages:
                if hasattr(message, 'source') and hasattr(message, 'content'):
                    # Skip FunctionCall and Transfer messages
                    if isinstance(message.content, str) and message.content.strip():
                        # Filter system messages
                        if (not "Transferred to" in message.content and 
                            not message.content.startswith("Start with") and  # Filter task start messages
                            not message.content.startswith("Start 8-dimension")):  # Filter enhanced task messages
                            valid_messages.append(message)
            
            print(f"📊 Valid dialogue messages: {len(valid_messages)}/{len(result.messages)}")
            
            # Extract dialogue content
            interview_dialogue = []
            interview_content = f"Interview subject: {person_name}\n"
            interview_content += f"Interview time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            interview_content += f"Interview mode: AutoGen Agent Q&A\n\n"
            
            # Process valid messages
            for i, message in enumerate(valid_messages):
                speaker = person_name if message.source.startswith("user_") else "Interviewer"
                content = message.content.strip()
                
                # Handle thinking tags
                if speaker == "Interviewer" and "<thinking>" in content:
                    thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                    if thinking_match:
                        thinking_content = thinking_match.group(1).strip()
                        response_content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
                        
                        # Parse thinking parts
                        thinking_parts = {}
                        intent_match = re.search(r'<intent>(.*?)</intent>', thinking_content, re.DOTALL)
                        memory_match = re.search(r'<memory>(.*?)</memory>', thinking_content, re.DOTALL)
                        mental_state_match = re.search(r'<mental_state>(.*?)</mental_state>', thinking_content, re.DOTALL)
                        
                        if intent_match:
                            thinking_parts["intent"] = intent_match.group(1).strip()
                        if memory_match:
                            thinking_parts["memory"] = memory_match.group(1).strip()
                        if mental_state_match:
                            thinking_parts["mental_state"] = mental_state_match.group(1).strip()
                        
                        # Ensure thinking information is saved even if response_content is empty
                        interview_dialogue.append({
                            "speaker": speaker,
                            "content": response_content if response_content else "[thinking]",
                            "thinking_full": thinking_content,
                            "thinking_intent": thinking_parts.get("intent", ""),
                            "thinking_memory": thinking_parts.get("memory", ""),
                            "thinking_mental_state": thinking_parts.get("mental_state", "")
                        })
                        if response_content:
                            interview_content += f"{speaker}: {response_content}\n\n"
                    else:
                        interview_dialogue.append({
                            "speaker": speaker,
                            "content": content
                        })
                        interview_content += f"{speaker}: {content}\n\n"
                else:
                    interview_dialogue.append({
                        "speaker": speaker,
                        "content": content
                    })
                    interview_content += f"{speaker}: {content}\n\n"
                        
            print(f"✅ Agent interview completed, conducted {len(interview_dialogue)} rounds of dialogue")
            
            return {
                "dialogue": interview_dialogue,
                "content": interview_content,
                "message_count": len(valid_messages),
                "question_count": len([d for d in interview_dialogue if d["speaker"] != person_name]),
                "response_count": len([d for d in interview_dialogue if d["speaker"] == person_name]),
                "interview_mode": "agent_based"
            }
            
        except Exception as e:
            print(f"❌ Agent interview failed: {e}")
            
            # Fallback to simplified interview mode
            print("🔄 Falling back to basic interview mode...")
            return await self._fallback_simple_interview(person_data)
    
    def _create_user_simulation_agent(self, person_data: Dict[str, Any], person_id: str) -> AssistantAgent:
        """Create user simulation agent."""
        # Create system message
        person_info = person_data.get("person_info", {})
        name = person_info.get("name", "")
        basic_data = person_info.get("basic_data", {})
        personal_bg = person_info.get("personal_background", {})
        
        timeline_summary = f"My life experiences include:"
        for event in person_data.get("life_timeline", [])[:5]:  # Only list first 5 main events
            timeline_summary += f"\n- {event.get('age')} years old: {event.get('description', '')}"
        
        system_message = f"""You are {name}, a real person undergoing an in-depth interview, sharing your life story.

🔄 Important dialogue rules:
- This is a real two-way interview dialogue
- When the interviewer asks you questions, you must actively answer
- Whenever it's your turn to speak, naturally share your experiences
- Don't stay silent or skip answering

⚠️ Key constraints: You must strictly answer based on the following real personal profile, never fabricate or deviate from these facts!

Personal profile:
- Name: {name}
- Age: {basic_data.get('current_age', '')} years old
- Gender: {basic_data.get('gender', '')}
- Birth year: {basic_data.get('birth_year', '')}
- Personality: {personal_bg.get('personality', {}).get('main_trait', '')}
- Behavioral traits: {personal_bg.get('personality', {}).get('behavior', '')}
- Family background: {personal_bg.get('family_details', {}).get('economic_status', '')}
- Father's occupation: {personal_bg.get('family_details', {}).get('father_job', '')}
- Mother's occupation: {personal_bg.get('family_details', {}).get('mother_job', '')}

{timeline_summary}

⚠️ Important: You are the interviewee, need to actively respond to every question from the interviewer. When the interviewer asks you questions, answer in detail and share your real experiences.

Data constraints:
1. Can only answer based on the above real profile and life experiences
2. If asked about things you haven't experienced, honestly say "I haven't had such experiences"
3. Absolutely cannot fabricate false age, birthplace, educational experiences, etc.
4. All answers must be consistent with your real data

Your conversation style:
- 🗣️ First-person natural expression, like a real person chatting
- 💭 Based on question content, select relevant events from above real experiences to share
- ❤️ With real emotional color, not too formal
- 🎯 Answers should be focused but maintain casual conversation
- ⏰ Mention specific time, place, people to make stories more vivid
- 🔄 Will reference previously discussed content to maintain dialogue coherence

Dialogue principles:
1. Natural like friends chatting, but always based on real data
2. Actively participate in every round of dialogue, don't quit or stay silent midway
3. Adjust answer detail level based on question depth
4. Show corresponding emotions for touching topics
5. Can show hesitation or change topics for sensitive topics
6. Occasionally mention personal feelings under historical background
7. Language should match your age, educational background and life experiences
8. Only answer interviewer's questions, don't actively ask questions or start new topics
9. When interviewer waits for your answer, actively respond to maintain dialogue continuity
10. After answering each question, stop and wait for interviewer's next question
11. Absolutely don't answer continuously or repeatedly answer the same question

Interview progress:
- Start relatively reserved, become more relaxed as conversation deepens
- Actively expand on topics of interest
- May briefly pass over difficult experiences
- When feeling everything should be said, naturally express "I think that's about it" or similar

You are now ready for the interview, waiting for interviewer's questions, then share your life story in the most authentic state. Remember: All answers must be based on your real profile!

⚠️ Dialogue principles:
- Only share your experiences when the interviewer explicitly asks you questions
- If the received message is not a question, simply respond "OK" or "I'm ready", then handoff
- Only answer interviewer's questions, don't ask back or actively question
- Answers should be based on your real profile but natural like conversation
- Only answer one question each time, then immediately handoff
- If interviewer is just greeting or saying other things, don't give long responses

🚫 Absolutely don't do:
- 🚫 Don't speak continuously or multiple times
- 🚫 Don't ask interviewer "what else would you like to know?"
- 🚫 Don't say mechanical replies like "received your question"
- 🚫 Don't actively ask questions or guide topics
- 🚫 Don't repeatedly answer the same question
- 🚫 Don't say multiple sentences in the same round
- 🚫 Don't spontaneously share long experiences when not receiving specific questions
- 🚫 Don't repeat the same content

✅ Correct way:
- Hear specific question→answer once→immediately handoff→wait quietly
- Hear non-question content→simple response→immediately handoff→wait quietly
- Like chatting with friends, real and casual
- Only speak once each time, never speak continuously
- Let interviewer control dialogue pace
- Wait for interviewer's clear guidance and questions"""
        
        # User agent fixed to use openai-gpt4 model
        user_model_client = model_manager.create_client("openai-gpt4")
        user_agent = AssistantAgent(
            name=f"user_{person_id}",
            model_client=user_model_client,
            handoffs=["interview_agent_local"],
            system_message=system_message
        )
        
        return user_agent
    
    def _create_interview_agent(self, person_name: str, person_id: str) -> AssistantAgent:
        """Create specialized interview agent."""
        interview_model_client = model_manager.create_client()
        interview_agent_local = AssistantAgent(
            name="interview_agent_local",
            model_client=interview_model_client,
            handoffs=[f"user_{person_id}"],
            system_message=f"""You are a senior life story interview expert conducting in-depth dialogue with {person_name}.

🎯 Interview goal: Collect complete life story, including childhood, education, work, marriage, challenges and achievements.

⚠️ Strict dialogue rules:
- This is Q&A interview dialogue
- After asking a question, immediately handoff to {person_name}
- Wait for {person_name} to answer, then ask the next question
- 🚫 Absolutely forbidden: continuous questioning, repeated questioning, saying multiple sentences at once
- ⭐ Iron rule: Each reply can only contain one question, say it then immediately handoff

🔄 Handoff timing (important):
1. After asking question → immediately handoff to user_{person_id}
2. Wait for user answer
3. After receiving answer → ask next question based on answer content → handoff again
4. Repeat this cycle

🎨 Interview strategy:
- Plan by rounds: 1-5 rounds (childhood family), 6-10 rounds (education work), 11-15 rounds (marriage family), 16-20 rounds (challenges achievements)
- Generate next question based on {person_name}'s specific answers
- Use warm, sincere tone to build trust
- Deeply explore emotional level and life insights

🧠 Thinking process (must strictly execute):
⚠️ Every reply must include thinking tags, format as follows:
<thinking>
  <intent>What information to collect this round</intent>
  <memory>Key content user has shared</memory>
  <mental_state>User's current emotion and openness</mental_state>
</thinking>

🚨 Important: thinking is mandatory, not optional! Must include every time!
Then ask one question, immediately handoff.

🚨 End interview:
- Only end when user explicitly says "that's about it", "said everything I should say", "I think that's enough"
- Don't actively end because of many rounds, continue deep exploration
- Ensure collecting information about childhood, education, work, marriage, challenges, achievements, etc.
- Closing: "Thank you for sharing, our interview ends here. INTERVIEW_COMPLETE"

💡 Key reminders:
- Must immediately handoff after each question
- Absolutely don't add any handoff prompts or "please answer" text after questions
- Only say the question itself, then directly handoff
- Wait for user answer before continuing

🚨 Absolutely forbidden behaviors:
- 🚫 Can't say multiple questions at once
- 🚫 Can't repeat the same question
- 🚫 Can't speak continuously multiple times without handoff
- 🚫 Can't say multiple sentences in the same round

⭐ Important: When receiving interview task, you should actively start the interview!
Strictly follow thinking → question → handoff order, absolutely can't directly handoff without question!

🎯 Startup process:
1. Receive "start interview" task → write thinking tags → ask first question → handoff to user  
2. User answers → write thinking tags → ask next question based on answer → handoff
3. Repeat this cycle

⚠️ Key: Must first write thinking, then ask question, finally handoff
Absolutely can't skip question and directly handoff!

⭐ Mandatory format for each reply:
<thinking>
  <intent>...</intent>
  <memory>...</memory>
  <mental_state>...</mental_state>
</thinking>

[Your question content]

🚨 thinking is mandatory requirement, must have every time! Then ask question, then handoff!

First round mandatory example:
<thinking>
  <intent>Start interview, build trust, understand {person_name}'s basic situation</intent>
  <memory>This is the start of interview</memory>
  <mental_state>User ready for interview</mental_state>
</thinking>

Hello {person_name}, nice to chat with you. Could you please briefly introduce yourself? For example, how old are you now and what work do you mainly do?

Important: Absolutely don't include "【handoff to xxx】" text in your reply!
Must follow: thinking tags → specific question → auto handoff order every time!"""
        )
        
        return interview_agent_local
    
    async def _fallback_simple_interview(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback simplified interview mode."""
        person_info = person_data["person_info"]
        person_name = person_info["name"]
        
        # Create simulated user
        user_sim = UserSimulationAgent(person_data)
        
        # More natural interview questions
        interview_questions = [
            f"Hello {person_name}! Could you first introduce yourself to me?",
            "Tell me about your childhood family environment, what's your deepest childhood memory?",
            "How was your educational experience? Any special teachers or classmates who impressed you?",
            "When was your first job? How did you feel then?",
            "Can you talk about your love life? How did you meet your current partner?",
            "After having children, what changes happened in your life?",
            "Looking back, when do you think was the most difficult period in your life?",
            "What moments made you feel particularly proud or satisfied?",
            "If you could give advice to your younger self, what would you say?",
            "Looking back now, what do you think influenced you the most?"
        ]
        
        interview_dialogue = []
        
        for question in interview_questions:
            # Generate more natural answers
            answer = await user_sim.respond_to_question(question)
            
            interview_dialogue.append({
                "speaker": "Interviewer",
                "content": question
            })
            interview_dialogue.append({
                "speaker": person_name,
                "content": answer
            })
            
            # If user indicates no more to say, end interview
            if any(phrase in answer for phrase in ["said everything I should say", "nothing more", "that's it", "that's about it"]):
                break
        
        # Generate interview content text
        interview_content = f"Interview subject: {person_name}\n"
        interview_content += f"Interview time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        interview_content += f"Interview mode: Simplified dialogue mode\n\n"
        
        for dialogue in interview_dialogue:
            interview_content += f"{dialogue['speaker']}: {dialogue['content']}\n\n"
        
        return {
            "dialogue": interview_dialogue,
            "content": interview_content,
            "question_count": len(interview_questions),
            "response_count": len([d for d in interview_dialogue if d["speaker"] == person_name]),
            "interview_mode": "fallback"
        }

# Global instance
interview_manager = InterviewManager()