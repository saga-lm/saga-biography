#!/usr/bin/env python3
"""
Interactive mode for SAGA Biography Generation System.
Allows real users to participate in AI-guided interviews.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import re
import warnings

# Suppress AutoGen warnings
warnings.filterwarnings('ignore', message='Missing required field.*structured_output.*')

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import UserMessage
from config.settings import settings
from src.models.client_manager import model_manager
from src.tools.history_analyzer import event_extractor, contextualizer
from src.tools.quality_evaluator import quality_critic, hero_evaluator
from src.utils.file_manager import file_manager


class InteractiveSession:
    """Interactive interview session for real users."""
    
    def __init__(self):
        self.interview_content = ""
        self.interview_dialogue = []
        self.biography = ""
        self.quality_result = {}
        self.hero_journey_result = {}
        self.historical_context = {}
        self.current_agent = None
        
    def display_header(self):
        """Display system header."""
        print("\n" + "=" * 80)
        print("🎭 SAGA Biography Generation System - Interactive Mode")
        print("=" * 80)
        print("✨ Create your life story with AI assistance")
        print("👥 AI Team: Interview Agent | History Researcher | Writer | Evaluator")
        print("-" * 80)
    
    def display_phase(self, phase: str, description: str):
        """Display current phase."""
        phase_icons = {
            "interview": "🎤",
            "history": "📚", 
            "writing": "✍️",
            "quality": "🔍",
            "hero_journey": "🏆",
            "completed": "🎉"
        }
        icon = phase_icons.get(phase, "⚡")
        print(f"\n{icon} 【{phase.upper()} PHASE】{description}")
        print("-" * 60)
    
    def display_agent_action(self, agent_name: str, action: str, content: str = ""):
        """Display agent action with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_agent = agent_name
        
        print(f"\n[{timestamp}] 🤖 {agent_name} | {action}")
        if content:
            if len(content) > 500:
                print(f"   📝 {content[:500]}...")
            else:
                print(f"   📝 {content}")
    
    def display_thinking(self, agent_name: str, thinking_content: str):
        """Display agent's thinking process."""
        print(f"\n💭 {agent_name} 的思考过程:")
        print("-" * 50)
        print(thinking_content)
        print("-" * 50)
    
    def display_tool_call(self, agent_name: str, tool_name: str, description: str = ""):
        """Display tool usage."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🔧 {agent_name} 调用工具: {tool_name}")
        if description:
            print(f"   📌 {description}")
    
    def display_search_results(self, query: str, results: list):
        """Display search results with sources."""
        print(f"\n🔍 搜索查询: {query}")
        print("   搜索结果:")
        for i, result in enumerate(results[:3], 1):  # Show top 3 results
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('content', '')
            
            print(f"\n   {i}. {title}")
            print(f"      🔗 {url}")
            if content:
                summary = content[:150] + "..." if len(content) > 150 else content
                print(f"      📄 {summary}")
    
    def display_handoff(self, from_agent: str, to_agent: str, reason: str = ""):
        """Display agent handoff."""
        print(f"\n🔄 Handoff: {from_agent} ➜ {to_agent}")
        if reason:
            print(f"   理由: {reason}")
        
    def get_user_input(self, prompt: str) -> str:
        """Get user input."""
        print(f"\n💬 {prompt}")
        print("   (Type 'quit' to exit, 'skip' to skip current question)")
        user_input = input("👤 You: ").strip()
        return user_input
    
    async def conduct_interview(self) -> str:
        """Conduct adaptive interview with real user."""
        self.display_phase("interview", "In-depth Interview - Collecting Your Life Story")
        
        # Create interview agent
        model_client = model_manager.create_client()
        interview_agent = AssistantAgent(
            name="interactive_interview_agent",
            model_client=model_client,
            system_message="""You are a senior life story interviewer conducting in-depth dialogue with a real user to collect rich life experiences for autobiography writing.

🎯 Core Principles:
- Never use fixed question lists, generate each question based on user's specific answers
- Adjust question direction and depth based on user's answer depth and emotional state
- Sensitively capture key information and dig deeper like a psychologist
- Build trust with warm, sincere tone

🔍 Adaptive Interview Strategy:

1. **Responsive Questioning**:
   - First express understanding and empathy for user's sharing
   - Capture keywords and emotional clues from user's answers
   - Generate targeted follow-up questions based on these clues

2. **Progressive Depth**:
   - From surface facts to deep feelings
   - From general descriptions to specific details
   - From events themselves to personal impact

3. **Context Awareness**:
   - If user answers briefly, use more specific guiding questions
   - If user is emotionally rich, explore emotional level deeply
   - If turning points mentioned, focus on before/after comparison

📋 Interview Areas (as inspiration, not fixed order):
- Childhood memories: family environment, important events, character formation
- Growing up: education, friendships, first love, rebellion
- Life turning points: major decisions, relocations, career choices
- Relationships: family, friends, lovers, colleagues
- Challenges: failures, low points, coping methods
- Achievements: proud moments, milestones, growth moments
- Values: life insights, beliefs, principles
- Era impact: how social changes affected you personally

💬 Dialogue Style Examples:
User: "Born in 1994, moved to Beijing after full moon, started learning art and calligraphy at age 3"
Your response: "Wow, started art at 3! There must be a special reason for being exposed to art and calligraphy so young. Was it parents' arrangement or your own interest? Was learning these things joyful or stressful for you at that time?"

User: "OK" (brief answer)
Your response: "I sense this topic might not be easy to discuss. We can start from another angle - how about telling me about your most memorable childhood memory? Could be a special birthday, or a family trip, anything."

🎨 Interview Techniques:
- Use open-ended questions like "Can you elaborate on...", "How did you feel then...", "What did this mean to you"
- Summarize user's sharing periodically to show you're listening carefully
- When users mention time, place, people, ask for more details
- Show empathy for emotional sharing: "That period sounds very important to you"
- Guide users to recall from different perspectives: "Looking back now, do you think..."

🧠 Thinking Process (Important):
Before each reply, you need to think deeply in this format:
<thinking>
  <intent>What information to collect this round</intent>
  <memory>Key content user has shared and connections to previous dialogue</memory>
  <mental_state>User's current emotion and openness level</mental_state>
</thinking>
<response>Based on thinking and dialogue history, reply to user with an empathetic question that shows deep understanding and inspires new thinking or recalls key details. Can also be encouragement, empathy, opening or closing.</response>

Special Handling:
- If user says "quit", respond "Thank you for sharing, our interview ends here"
- If user says "skip", say "Okay, let's talk about something else" and change topic
- If user answers very briefly, use more specific guidance and examples to help user open up

Remember: Each question should be a natural continuation of user's previous answer, don't jump to unrelated topics. When interview is rich enough (about 10-15 rounds), thank warmly and conclude."""
        )
        
        # Start interview
        conversation_history = ""
        question_count = 0
        
        # Opening question
        opening_question = """Hello! I'm a professional life story interviewer, honored to listen to your story.

Today's goal is to review your life journey together, uncover precious memories and experiences, and collect materials for creating your personal autobiography.

Please start by briefly introducing yourself - your name, age, and current life situation. We can begin wherever you're comfortable sharing.

Please relax, just like chatting with an old friend."""

        print("\n🎤 Interview Agent:")
        print(opening_question)
        
        while question_count < 15:  # Maximum 15 rounds
            question_count += 1
            
            try:
                # First round uses preset opening, subsequent rounds use AI-generated questions
                if question_count == 1:
                    agent_question = opening_question
                    # Get user's first answer
                    user_response = input("\n👤 You: ").strip()
                else:
                    # Generate next question based on conversation history
                    prompt = f"""You are a professional life story interviewer conducting in-depth interview. Based on the following conversation history, generate the next natural, targeted interview question:

Conversation history:{conversation_history}

Based on user's latest answer "{user_response}", generate a targeted follow-up or new topic.

Requirements:
1. If user answers in detail, dig deeper into details or emotions
2. If user answers briefly, use more specific guiding questions
3. Naturally transition between different life stages
4. Focus on keywords and emotional clues mentioned by user
5. Don't repeat previously asked questions

Generate format:
<thinking>
  <intent>Analyze core motivation of user's expression</intent>
  <memory>Find connections and clues with previous dialogue</memory>
  <mental_state>Analyze user's possible emotional state and unexpressed thoughts</mental_state>
</thinking>
<response>Your interview question (warm, empathetic, inspiring question)</response>
"""
                    
                    response = await model_client.create(
                        messages=[UserMessage(content=prompt, source="user")]
                    )
                    agent_question = response.content.strip()
                    
                    # Extract thinking and response
                    thinking_content = None
                    response_content = agent_question
                    
                    # Parse XML structure
                    if "<thinking>" in agent_question and "<response>" in agent_question:
                        # Extract thinking
                        thinking_match = re.search(r'<thinking>(.*?)</thinking>', agent_question, re.DOTALL)
                        if thinking_match:
                            thinking_content = thinking_match.group(1).strip()
                            self.display_thinking("Interview Agent", thinking_content)
                        
                        # Extract response
                        response_match = re.search(r'<response>(.*?)</response>', agent_question, re.DOTALL)
                        if response_match:
                            response_content = response_match.group(1).strip()
                        else:
                            # Fallback: remove thinking and use rest
                            response_content = re.sub(r'<thinking>.*?</thinking>', '', agent_question, flags=re.DOTALL).strip()
                            response_content = re.sub(r'</?response>', '', response_content).strip()
                    elif "<thinking>" in agent_question:
                        # Only thinking tag
                        thinking_match = re.search(r'<thinking>(.*?)</thinking>', agent_question, re.DOTALL)
                        if thinking_match:
                            thinking_content = thinking_match.group(1).strip()
                            self.display_thinking("Interview Agent", thinking_content)
                            # Remove thinking from response
                            response_content = re.sub(r'<thinking>.*?</thinking>', '', agent_question, flags=re.DOTALL).strip()
                    elif "<response>" in agent_question:
                        # Only response tag
                        response_match = re.search(r'<response>(.*?)</response>', agent_question, re.DOTALL)
                        if response_match:
                            response_content = response_match.group(1).strip()
                    
                    # Final cleanup - remove any remaining XML tags
                    response_content = re.sub(r'</?thinking>', '', response_content).strip()
                    response_content = re.sub(r'</?response>', '', response_content).strip()
                    response_content = re.sub(r'</?intent>', '', response_content).strip()
                    response_content = re.sub(r'</?memory>', '', response_content).strip()
                    response_content = re.sub(r'</?mental_state>', '', response_content).strip()
                    
                    # If response_content is empty or too short, use original
                    if not response_content or len(response_content) < 10:
                        response_content = agent_question
                    
                    self.display_agent_action("Interview Agent", f"访谈问题 ({question_count}/15)", response_content)
                    
                    # Get user answer
                    user_response = input("\n👤 You: ").strip()
                
                if user_response.lower() == 'quit':
                    print("\n👋 Interview ended, thank you for sharing!")
                    break
                elif user_response.lower() == 'skip':
                    user_response = "I'd like to talk about something else"
                
                # Record dialogue
                self.interview_dialogue.append({
                    "speaker": "Interviewer",
                    "content": opening_question if question_count == 1 else response_content
                })
                self.interview_dialogue.append({
                    "speaker": "You",
                    "content": user_response
                })
                
                # Update interview content
                self.interview_content += f"Interviewer: {opening_question if question_count == 1 else response_content}\nYou: {user_response}\n\n"
                
                # Update conversation history for next question
                conversation_history += f"\nInterviewer: {opening_question if question_count == 1 else response_content}\nYou: {user_response}"
                
                # Check if enough information collected
                if question_count >= 10 and len(user_response.strip()) > 50:
                    if any(phrase in user_response.lower() for phrase in ["that's about it", "that's all", "nothing more", "enough"]):
                        print("\n✅ User indicated interview can end")
                        break
                        
            except Exception as e:
                print(f"❌ Interview interrupted: {e}")
                break
        
        # Display interview summary
        total_words = sum(len(item["content"]) for item in self.interview_dialogue if item["speaker"] == "You")
        print(f"\n📊 Interview Statistics:")
        print(f"   - Dialogue rounds: {len(self.interview_dialogue)//2}")
        print(f"   - Total words: {total_words}")
        print(f"   - Interview mode: Adaptive AI Interview")
        
        return self.interview_content
    
    async def generate_biography(self):
        """Generate biography from interview content."""
        self.display_phase("writing", "Creating Your Personal Biography")
        
        # Step 1: Extract event anchors
        self.display_agent_action("History Analyzer", "开始提取事件锚点")
        self.display_tool_call("History Analyzer", "extract_event_anchors", "智能分析访谈内容，提取有研究价值的时间、地点和历史事件")
        
        anchors = await event_extractor.extract_event_anchors(self.interview_content)
        
        # Display extracted anchors
        if anchors:
            print(f"\n✅ 提取到事件锚点:")
            if 'temporal_anchors' in anchors and anchors['temporal_anchors']:
                print(f"   ⏰ 时间锚点 ({len(anchors['temporal_anchors'])}个): {', '.join(anchors['temporal_anchors'][:5])}")
            if 'location_anchors' in anchors and anchors['location_anchors']:
                print(f"   📍 地点锚点 ({len(anchors['location_anchors'])}个): {', '.join(anchors['location_anchors'][:5])}")
            if 'experience_anchors' in anchors and anchors['experience_anchors']:
                print(f"   🎯 体验锚点 ({len(anchors['experience_anchors'])}个): {', '.join(anchors['experience_anchors'][:3])}")
        
        # Step 2: Research historical context
        if anchors:
            self.display_agent_action("History Researcher", "开始历史背景研究")
            self.display_tool_call("History Researcher", "research_historical_context_enhanced", "通过网络搜索研究相关历史背景")
            
            self.historical_context = await contextualizer.research_historical_context_enhanced(anchors)
            
            # Display search results
            search_results = self.historical_context.get('search_results', [])
            if search_results:
                print(f"\n✅ 完成 {len(search_results)} 次历史背景搜索")
                for search_result in search_results[:3]:  # Show first 3 searches
                    query = search_result.get('query', 'Unknown query')
                    results = search_result.get('results', [])
                    self.display_search_results(query, results)
        
        # Step 3: Write biography
        self.display_agent_action("Biography Writer", "开始创作自传")
        model_client = model_manager.create_client()
        
        writing_prompt = f"""Based on the following interview content and historical context, create a touching personal autobiography of 2000-3000 words.

Structure using the Hero's Journey framework:
- Protagonist: Recognition of oneself as hero/main character
- Shift: Pivotal changes or new experiences
- Quest: Clear objectives and missions
- Allies: Support from others and mentors
- Challenge: Obstacles and difficulties faced
- Transformation: Personal growth and change
- Legacy: Lasting impact on others

Interview Content:
{self.interview_content}

Historical Context:
{self.historical_context}

Writing Requirements:
1. Use Hero's Journey narrative framework
2. First-person perspective, authentic and touching language
3. Naturally integrate personal experience with historical context
4. Highlight personal growth, resilience, and life wisdom
5. Rich emotional expression and psychological description
6. Beautiful literary language and narrative rhythm
7. Complete structure, clear logic, engaging

Please create a high-quality personal autobiography:"""
        
        try:
            self.display_tool_call("Biography Writer", "generate_biography", "使用英雄之旅框架创作2000-3000字自传")
            
            response = await model_client.create(
                messages=[UserMessage(content=writing_prompt, source="user")]
            )
            self.biography = response.content.strip()
            
            # Display the biography
            print(f"\n✅ 自传创作完成，共 {len(self.biography)} 字")
            print("\n" + "=" * 80)
            print("📖 生成的自传内容:")
            print("=" * 80)
            if len(self.biography) > 1000:
                print(self.biography[:1000] + "...")
                print("\n[...省略中间部分...]")
                print(self.biography[-500:])
            else:
                print(self.biography)
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 自传生成错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    async def evaluate_quality(self):
        """Evaluate biography quality."""
        self.display_phase("quality", "Evaluating Biography Quality")
        
        self.display_agent_action("Quality Evaluator", "开始质量评估")
        self.display_tool_call("Quality Evaluator", "evaluate_biography_quality", "使用8维度详细分析评估自传质量")
        
        self.quality_result = await quality_critic.evaluate_biography_quality(self.biography)
        
        score = self.quality_result.get("overall_score", 0)
        print(f"\n✅ 质量评估完成，总分: {score}/10.0")
        
        if score >= 9.0:
            print("🎉 恭喜！您的自传达到了优秀标准！")
        elif score >= 8.0:
            print("👍 很好！您的自传质量良好！")
        else:
            print("📝 建议进一步改进自传内容")
        
        # Display dimension scores
        if "dimension_scores" in self.quality_result:
            print("\n📊 维度得分:")
            for dimension, dim_score in self.quality_result["dimension_scores"].items():
                print(f"   {dimension}: {dim_score}/10.0")
        
        # Display feedback
        if "feedback" in self.quality_result:
            print("\n💡 评估反馈:")
            print(self.quality_result["feedback"][:500] + "..." if len(self.quality_result["feedback"]) > 500 else self.quality_result["feedback"])
    
    async def evaluate_hero_journey(self):
        """Evaluate using Hero's Journey scale."""
        self.display_phase("hero_journey", "Hero's Journey Scale Evaluation")
        
        self.display_agent_action("Hero's Journey Evaluator", "开始英雄之旅量表评估")
        self.display_tool_call("Hero's Journey Evaluator", "evaluate_biography_with_hero_journey_scale", "评估自传的7个英雄之旅维度")
        
        self.hero_journey_result = await hero_evaluator.evaluate_biography(
            self.biography,
            "User"
        )
        
        if 'total_score' in self.hero_journey_result:
            total = self.hero_journey_result['total_score']
            percentage = self.hero_journey_result.get('percentage_score', 0)
            print(f"\n✅ 英雄之旅评估完成: {total}/147分 ({percentage:.1f}%)")
            
            # Display dimension averages
            if "dimension_averages" in self.hero_journey_result:
                print("\n🏆 英雄之旅维度分析:")
                for dimension, avg in self.hero_journey_result["dimension_averages"].items():
                    print(f"   {dimension}: {avg:.1f}/7.0")
            
            # Display detailed scores
            if "dimension_scores" in self.hero_journey_result:
                print("\n📋 各题目得分:")
                for dimension, items in self.hero_journey_result["dimension_scores"].items():
                    print(f"\n   {dimension}:")
                    for item_num, item_score in items.items():
                        print(f"      题目{item_num}: {item_score}/7")
    
    async def save_results(self):
        """Save all results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        person_id = f"interactive_{timestamp}"
        
        # Save interview
        interview_file = file_manager.save_interview(
            person_id=person_id,
            interview_content=self.interview_content,
            dialogue=self.interview_dialogue
        )
        
        # Save biography
        biography_file = file_manager.save_biography(
            person_id=person_id,
            biography_content=self.biography,
            version="final"
        )
        
        # Save evaluation
        evaluation_file = file_manager.save_evaluation(
            person_id=person_id,
            quality_result=self.quality_result,
            hero_journey_result=self.hero_journey_result
        )
        
        print(f"\n💾 Results saved:")
        print(f"   - Interview: {interview_file}")
        print(f"   - Biography: {biography_file}")
        print(f"   - Evaluation: {evaluation_file}")
        
        return biography_file
    
    async def display_final_results(self):
        """Display final results."""
        self.display_phase("completed", "Biography Creation Completed!")
        
        print("\n📖 Your Personal Biography:")
        print("-" * 60)
        if len(self.biography) > 500:
            print(self.biography[:500] + "...")
            show_full = input("\n   View full content? (y/n): ").lower()
            if show_full == 'y':
                print(f"\n{self.biography}")
        else:
            print(self.biography)
        
        # Save results
        await self.save_results()
    
    async def run(self):
        """Run interactive session."""
        try:
            self.display_header()
            
            # Display current model
            print(f"\n🤖 Current AI Model: {settings.default_model}")
            print(f"   Available models: {', '.join(settings.get_available_models())}")
            
            # Confirm user ready
            ready = input("\n🚀 Ready to create your life story? (y/n): ").lower()
            if ready != 'y':
                print("👋 Looking forward to serving you next time!")
                return
            
            # Conduct interview
            interview_content = await self.conduct_interview()
            
            if not interview_content.strip():
                print("❌ No interview content collected, cannot continue.")
                return
            
            # Generate biography
            success = await self.generate_biography()
            if not success:
                return
            
            # Evaluate quality
            await self.evaluate_quality()
            
            # Evaluate hero's journey
            await self.evaluate_hero_journey()
            
            # Display final results
            await self.display_final_results()
            
            print("\n🎉 Thank you for using SAGA Biography Generation System!")
            
        except KeyboardInterrupt:
            print("\n⚠️ User interrupted the process")
        except Exception as e:
            print(f"\n❌ System error: {e}")
            import traceback
            traceback.print_exc()


async def start_interactive_mode():
    """Start interactive mode."""
    session = InteractiveSession()
    await session.run()


def main():
    """Main entry point."""
    try:
        asyncio.run(start_interactive_mode())
    except KeyboardInterrupt:
        print("\n⏹️ Interactive session interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

