#!/usr/bin/env python3
"""
Gradio Web UI for SAGA Biography Generation System.
Provides interactive interface for biography creation with real-time agent visualization.

Architecture:
- Uses interview_manager agent for structured interview methodology
- Uses biography_manager agent for biography writing and refinement
- Uses event_extractor and contextualizer tools for historical analysis
- Uses quality_critic and hero_evaluator tools for quality assessment
- Coordinator logic implemented inline for Gradio interactive workflow
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import gradio as gr
from typing import Optional, List, Tuple
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from session_manager import SessionManager
from autogen_core.models import UserMessage
from config.settings import settings
from src.models.client_manager import model_manager
from src.agents import interview_manager, biography_manager
from src.tools import event_extractor, contextualizer, quality_critic, hero_evaluator

# Initialize session manager
session_manager = SessionManager()


class GradioSAGASession:
    """SAGA session adapted for Gradio UI."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_data = session_manager.get_session(session_id)
    
    def log(self, level: str, message: str):
        """Add log entry."""
        session_manager.add_log(self.session_id, level, message)
        session_manager.save_session(self.session_id)
    
    def update(self, **kwargs):
        """Update session data."""
        session_manager.update_session(self.session_id, kwargs)
    
    def get_logs(self) -> str:
        """Get formatted logs."""
        return session_manager.get_logs(self.session_id)
    
    async def coordinator_decide_next_action(self) -> dict:
        """Coordinator decides what to do next."""
        self.log("INFO", "🧠 Coordinator正在分析并决策下一步行动...")
        
        coordinator_client = model_manager.create_client()
        
        # Get recent action history
        action_history = self.session_data.get("action_history", [])
        recent_actions = action_history[-10:] if action_history else []
        action_summary = "\n".join([
            f"  迭代{iter}: {action} - {reason}"
            for iter, action, reason in recent_actions
        ]) if recent_actions else "  尚未执行任何action"
        
        # Build context
        interview_dialogue = self.session_data.get("interview_dialogue", [])
        biography = self.session_data.get("biography", "")
        quality_result = self.session_data.get("quality_result", {})
        extracted_anchors = self.session_data.get("extracted_anchors")
        historical_context = self.session_data.get("historical_context", {})
        current_phase = self.session_data.get("current_phase", "starting")
        conversation_history = self.session_data.get("conversation_history", "")
        
        context = f"""当前状态快照:
- 当前阶段: {current_phase}
- 访谈轮数: {len(interview_dialogue) // 2}
- 已有自传: {'是' if biography else '否'} ({len(biography)} 字)
- 质量评估: {'是' if quality_result else '否'} ({quality_result.get('overall_score', 0):.1f}/10)
- 事件提取: {'是' if extracted_anchors else '否'}
- 历史研究: {'是' if historical_context else '否'}

📊 最近执行的Actions:
{action_summary}

📝 最近对话:
{conversation_history[-800:] if conversation_history else '尚未开始'}
"""
        
        prompt = f"""{context}

You are the intelligent Coordinator of the SAGA system, responsible for orchestrating multiple AI agents and tools to complete biography creation.

🎯 Your Role:
- Analyze current progress and decide the optimal next action
- Ensure logical workflow progression
- Balance information collection with quality output
- Coordinate between Interview, History Research, Writing, and Evaluation agents

📋 Available Actions and When to Use Them:

1. **continue_interview** - Continue collecting user's life story
   - Use when: Interview rounds < 8, or answers are rich but coverage incomplete
   - Don't use when: User responses become repetitive or very brief

2. **end_interview** - Conclude the interview phase
   - Use when: Interview rounds >= 10 and sufficient content collected
   - Signals transition to biography creation phase

3. **extract_events** - Extract temporal and location anchors from interview
   - Use when: Interview has substantial content but events not yet extracted
   - Required before historical research

4. **research_history** - Research historical context for extracted events
   - Use when: Events extracted but historical context not yet researched
   - Enriches biography with era background

5. **write_biography** - Create the autobiography using collected materials
   - Use when: Interview complete (6+ rounds) and ideally after history research
   - Can proceed without history research if anchors are sparse

6. **evaluate_quality** - Assess biography quality with 8-dimension evaluation
   - Use when: Biography exists but not yet evaluated
   - Always evaluate before refinement

7. **refine_biography** - Improve biography based on evaluation feedback
   - Use when: Biography evaluated and score < 9.0
   - Consider quality score and specific feedback

8. **complete** - Finish the entire process
   - Use when: Biography exists, evaluated, and quality score >= 8.5
   - Or after refinement attempt

🧠 Decision Strategy:
- Prioritize interview depth over speed (aim for 8-12 rounds)
- Always extract events if interview is substantial
- Historical research is valuable but optional (depends on anchor quality)
- Always evaluate before considering refinement
- One refinement attempt is usually sufficient

Return your decision in JSON format:
{{
  "next_action": "action_name",
  "reasoning": "detailed reasoning for this decision based on current state",
  "confidence": 0.0-1.0
}}"""
        
        try:
            response = await coordinator_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )
            
            response_text = response.content.strip()
            
            # Extract JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            decision = json.loads(response_text)
            
            self.log("SUCCESS", f"✅ Coordinator决策: {decision.get('next_action')} (置信度: {decision.get('confidence', 0):.2f})")
            self.log("INFO", f"   决策理由: {decision.get('reasoning', 'N/A')}")
            
            return decision
            
        except Exception as e:
            self.log("WARNING", f"⚠️ Coordinator决策失败，使用fallback逻辑: {e}")
            
            # Fallback logic
            if biography and not quality_result:
                return {"next_action": "evaluate_quality", "reasoning": "有自传但未评估", "confidence": 0.9}
            elif len(interview_dialogue) >= 6 and not biography:
                return {"next_action": "write_biography", "reasoning": "访谈充足，可以创作", "confidence": 0.85}
            elif len(interview_dialogue) < 3:
                return {"next_action": "continue_interview", "reasoning": "访谈内容太少", "confidence": 0.95}
            else:
                return {"next_action": "continue_interview", "reasoning": "继续收集信息", "confidence": 0.7}
    
    async def conduct_interview_round(self, user_response: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """Conduct one round of interview using interview agent's methodology."""
        if not user_response:
            return "", None
        
        model_client = model_manager.create_client()
        interview_dialogue = self.session_data.get("interview_dialogue", [])
        conversation_history = self.session_data.get("conversation_history", "")
        
        # Record user's previous answer first
        interview_dialogue.append({"speaker": "You", "content": user_response})
        conversation_history += f"\nYou: {user_response}"
        
        self.update(
            interview_dialogue=interview_dialogue,
            conversation_history=conversation_history,
            interview_content=self.session_data.get("interview_content", "") + f"You: {user_response}\n\n"
        )
        
        self.log("INFO", f"👤 User response ({len(user_response)} chars)")
        
        # Calculate interview round to guide questioning strategy
        interview_round = len(interview_dialogue) // 2
        person_name = self.session_data.get("person_name", "User")
        
        # Stage-based interview strategy (from interview_agent)
        stage_guide = ""
        if interview_round <= 5:
            stage_guide = "Focus on: childhood, family background, early memories"
        elif interview_round <= 10:
            stage_guide = "Focus on: education, work experiences, career development"
        elif interview_round <= 15:
            stage_guide = "Focus on: relationships, marriage, family life"
        else:
            stage_guide = "Focus on: challenges, achievements, life reflections, wisdom"
        
        # Generate next question with interview agent's structured thinking
        prompt = f"""You are a senior life story interview expert conducting in-depth dialogue with {person_name}.

🎯 Interview goal: Collect complete life story including childhood, education, work, marriage, challenges and achievements.

Interview round: {interview_round}
Current stage strategy: {stage_guide}

Conversation history:
{conversation_history[-1500:]}

User's latest answer: "{user_response}"

🧠 Thinking process (strictly follow):
<thinking>
  <intent>What information to collect this round, what to explore based on user's answer</intent>
  <memory>Key content user has shared, connections with previous dialogue</memory>
  <mental_state>User's current emotion and openness, unexpressed thoughts</mental_state>
</thinking>

Then generate ONE natural, warm, targeted follow-up question.

🎨 Interview strategy:
1. If user answers in detail → dig deeper into emotions and details
2. If user answers briefly → use more specific guiding questions  
3. Naturally transition between life stages
4. Focus on keywords and emotional clues in user's answer
5. Don't repeat previously asked questions
6. Build trust through warm, sincere tone

⚠️ Important: 
- Your response MUST include <thinking> tags with intent, memory, mental_state
- Then ask ONE clear question
- No multiple questions, no repeated questions
- Natural conversation style, not mechanical

Format:
<thinking>
  <intent>...</intent>
  <memory>...</memory>
  <mental_state>...</mental_state>
</thinking>

[Your single interview question]"""
        
        self.log("INFO", "🎤 Interview Agent generating next question...")
        
        response = await model_client.create(
            messages=[UserMessage(content=prompt, source="user")]
        )
        
        agent_response = response.content.strip()
        
        # Extract thinking and question (same parsing logic from interview_agent)
        thinking_content = None
        question = agent_response
        
        import re
        # Parse thinking tags
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', agent_response, re.DOTALL)
        if thinking_match:
            thinking_content = thinking_match.group(1).strip()
            
            # Parse thinking components
            intent_match = re.search(r'<intent>(.*?)</intent>', thinking_content, re.DOTALL)
            memory_match = re.search(r'<memory>(.*?)</memory>', thinking_content, re.DOTALL)
            mental_match = re.search(r'<mental_state>(.*?)</mental_state>', thinking_content, re.DOTALL)
            
            thinking_parts = []
            if intent_match:
                thinking_parts.append(f"Intent: {intent_match.group(1).strip()}")
            if memory_match:
                thinking_parts.append(f"Memory: {memory_match.group(1).strip()}")
            if mental_match:
                thinking_parts.append(f"Mental: {mental_match.group(1).strip()}")
            
            if thinking_parts:
                self.log("INFO", f"💭 {' | '.join(thinking_parts[:80])}")
            
            # Remove thinking from question
            question = re.sub(r'<thinking>.*?</thinking>', '', agent_response, flags=re.DOTALL).strip()
        
        # Remove any remaining XML tags
        question = re.sub(r'</?thinking>|</?intent>|</?memory>|</?mental_state>|</?response>', '', question).strip()
        
        # Fallback if extraction failed
        if not question or len(question) < 10:
            question = agent_response
        
        # Record question
        interview_dialogue.append({"speaker": "Interviewer", "content": question})
        conversation_history += f"\nInterviewer: {question}"
        
        self.update(
            interview_dialogue=interview_dialogue,
            conversation_history=conversation_history,
            interview_content=self.session_data.get("interview_content", "") + f"Interviewer: {question}\n\n"
        )
        
        self.log("SUCCESS", f"✅ Interview Agent sent question #{len(interview_dialogue)//2}")
        
        return question, None
    
    async def extract_events(self):
        """Extract event anchors."""
        self.log("INFO", "📚 History Analyzer正在提取事件锚点...")
        self.update(current_phase="history_analysis")
        
        interview_content = self.session_data.get("interview_content", "")
        extracted_anchors = await event_extractor.extract_event_anchors(interview_content)
        
        self.update(extracted_anchors=extracted_anchors)
        
        if extracted_anchors:
            temporal = extracted_anchors.get('temporal_anchors', [])
            location = extracted_anchors.get('location_anchors', [])
            self.log("SUCCESS", f"✅ 提取到 {len(temporal)} 个时间锚点，{len(location)} 个地点锚点")
        else:
            self.log("WARNING", "⚠️ 未提取到明显的历史事件锚点")
    
    async def research_history(self):
        """Research historical context."""
        self.log("INFO", "📚 History Researcher正在搜索历史背景...")
        self.update(current_phase="historical_research")
        
        extracted_anchors = self.session_data.get("extracted_anchors")
        
        if extracted_anchors:
            historical_context = await contextualizer.research_historical_context_enhanced(
                extracted_anchors
            )
            
            self.update(historical_context=historical_context)
            
            search_results = historical_context.get('search_results', [])
            if search_results:
                self.log("SUCCESS", f"✅ 完成 {len(search_results)} 次历史背景搜索")
                for search_result in search_results[:2]:
                    query = search_result.get('query', '')
                    self.log("INFO", f"   🔍 搜索: {query}")
            else:
                self.log("WARNING", "⚠️ 历史背景搜索未返回结果")
        else:
            self.log("WARNING", "⚠️ 没有事件锚点可供研究")
    
    async def write_biography(self):
        """Write or update biography using biography_manager agent."""
        self.log("INFO", "✍️ Biography Writer Agent正在创作自传...")
        self.update(current_phase="writing")
        
        interview_content = self.session_data.get("interview_content", "")
        historical_context = self.session_data.get("historical_context", {})
        
        # Build minimal person_data for biography_manager
        person_data = {
            "person_info": {
                "name": self.session_data.get("person_name", "User"),
                "basic_data": self.session_data.get("basic_data", {}),
                "personal_background": self.session_data.get("personal_background", {})
            }
        }
        
        # Use biography_manager agent to generate biography
        biography = await biography_manager.generate_biography(
            interview_content=interview_content,
            historical_context=historical_context,
            person_data=person_data
        )
        
        biography_versions = self.session_data.get("biography_versions", [])
        biography_versions.append({
            "version": len(biography_versions) + 1,
            "content": biography,
            "timestamp": datetime.now().isoformat()
        })
        
        self.update(
            biography=biography,
            biography_versions=biography_versions
        )
        
        self.log("SUCCESS", f"✅ Biography created by agent (v{len(biography_versions)}, {len(biography)} chars)")
    
    async def evaluate_quality(self):
        """Evaluate biography quality."""
        self.log("INFO", "🔍 Quality Evaluator正在评估质量...")
        self.update(current_phase="quality_assessment")
        
        biography = self.session_data.get("biography", "")
        
        if not biography:
            self.log("ERROR", "❌ 没有自传内容可供评估")
            return
        
        quality_result = await quality_critic.evaluate_biography_quality(biography)
        self.update(quality_result=quality_result)
        
        score = quality_result.get("overall_score", 0)
        quality_level = quality_result.get("quality_level", "unknown")
        
        self.log("SUCCESS", f"✅ 质量评分: {score:.1f}/10.0 ({quality_level})")
        
        if "dimension_scores" in quality_result:
            dims = quality_result["dimension_scores"]
            self.log("INFO", f"   📊 维度得分: 内容{dims.get('content_completeness', 0):.1f} | "
                     f"情感{dims.get('emotional_depth', 0):.1f} | "
                     f"文学{dims.get('literary_quality', 0):.1f} | "
                     f"历史{dims.get('historical_integration', 0):.1f}")
    
    async def refine_biography(self):
        """Refine biography using biography_manager agent's improvement methods."""
        self.log("INFO", "🔄 Biography Writer Agent正在优化自传...")
        self.update(current_phase="refinement")
        
        biography = self.session_data.get("biography", "")
        quality_result = self.session_data.get("quality_result", {})
        historical_context = self.session_data.get("historical_context", {})
        person_name = self.session_data.get("person_name", "User")
        
        overall_score = quality_result.get("overall_score", 0.0)
        dimension_scores = quality_result.get("dimension_scores", {})
        
        # Decide refinement strategy based on quality score and dimension analysis
        if overall_score < 7.5:
            # Low score: use comprehensive improvement
            self.log("INFO", "📊 Score below 7.5, applying comprehensive improvement...")
            biography = await biography_manager.improve_biography(
                biography=biography,
                quality_result=quality_result,
                historical_context=historical_context,
                person_name=person_name
            )
        else:
            # Medium score: focus on Hero's Journey structure enhancement
            self.log("INFO", "📊 Score 7.5+, enhancing Hero's Journey structure...")
            biography = await biography_manager.enhance_hero_journey_structure(
                biography=biography,
                quality_result=quality_result,
                person_name=person_name
            )
        
        biography_versions = self.session_data.get("biography_versions", [])
        biography_versions.append({
            "version": len(biography_versions) + 1,
            "content": biography,
            "timestamp": datetime.now().isoformat(),
            "refined": True,
            "refinement_strategy": "comprehensive" if overall_score < 7.5 else "hero_journey"
        })
        
        self.update(
            biography=biography,
            biography_versions=biography_versions
        )
        
        self.log("SUCCESS", f"✅ Biography refined by agent (v{len(biography_versions)})")


# ============================================================================
# Gradio Interface Functions
# ============================================================================

def create_new_session():
    """Create new session with proper initialization."""
    session_id, session_data = session_manager.create_session()
    session_manager.add_log(session_id, "INFO", f"🚀 System initialized, Session ID: {session_id}")
    session_manager.add_log(session_id, "INFO", f"🤖 AI Model: {settings.default_model}")
    
    # Initialize person info (will be updated when user introduces themselves)
    session_data['person_name'] = "User"
    session_data['basic_data'] = {}
    session_data['personal_background'] = {}
    
    # Generate opening question (aligned with interview_agent style)
    opening_question = """Hello! I'm a professional life story interviewer, honored to listen to your story.

Today's goal is to review your life journey together, uncover precious memories and experiences, and collect materials for creating your personal autobiography.

Please start by briefly introducing yourself - your name, age, and current life situation. We can begin wherever you're comfortable sharing.

Please relax, just like chatting with an old friend."""
    
    # Record opening question in session
    session_data['interview_dialogue'] = [{"speaker": "Interviewer", "content": opening_question}]
    session_data['conversation_history'] = f"Interviewer: {opening_question}"
    session_data['interview_content'] = f"Interviewer: {opening_question}\n\n"
    session_manager.update_session(session_id, session_data)
    session_manager.add_log(session_id, "INFO", "🎤 Interview Agent sent opening question")
    session_manager.save_session(session_id)
    
    logs = session_manager.get_logs(session_id)
    
    # Display opening question in chatbot
    chatbot_initial = [(None, opening_question)]
    
    return (
        session_id,  # session_id_display
        gr.update(visible=True),  # main_interface
        gr.update(visible=False),  # start_interface
        chatbot_initial,  # chatbot with opening question
        "",  # user_input
        {},  # coordinator_output
        "当前阶段: starting\n访谈轮数: 0",  # agent_status
        "",  # biography_display
        logs,  # log_display
        []  # version_dropdown
    )


def resume_existing_session(resume_session_id):
    """Resume existing session."""
    if not resume_session_id:
        return (
            gr.update(),
            gr.update(value="⚠️ 请输入会话ID"),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )
    
    session_data = session_manager.get_session(resume_session_id)
    
    if not session_data:
        return (
            gr.update(),
            gr.update(value=f"❌ 会话ID不存在: {resume_session_id}"),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )
    
    # Reconstruct chatbot history
    dialogue = session_data.get("interview_dialogue", [])
    chatbot_history = []
    
    # 对话格式：[(user_msg, bot_msg), (user_msg, bot_msg), ...]
    # dialogue中是交替的 Interviewer 和 You
    i = 0
    while i < len(dialogue):
        if i == 0 and dialogue[0]["speaker"] == "Interviewer":
            # 第一条是开场问题，没有用户输入
            chatbot_history.append((None, dialogue[0]["content"]))
            i += 1
        elif i + 1 < len(dialogue):
            # 正常的一问一答
            if dialogue[i]["speaker"] == "You" and dialogue[i + 1]["speaker"] == "Interviewer":
                chatbot_history.append((dialogue[i]["content"], dialogue[i + 1]["content"]))
                i += 2
            else:
                i += 1
        else:
            # 最后一条用户消息还没有回复
            if dialogue[i]["speaker"] == "You":
                chatbot_history.append((dialogue[i]["content"], None))
            i += 1
    
    # Get biography
    biography = session_data.get("biography", "*自传尚未生成*")
    
    # Get versions
    versions = session_data.get("biography_versions", [])
    version_choices = [f"版本 {v['version']} - {v['timestamp'][:19]}" for v in versions]
    
    # Get logs
    logs = session_manager.get_logs(resume_session_id)
    
    session_manager.add_log(resume_session_id, "INFO", f"🔄 会话已恢复: {resume_session_id}")
    session_manager.save_session(resume_session_id)
    logs = session_manager.get_logs(resume_session_id)
    
    return (
        resume_session_id,  # session_id_display
        gr.update(visible=True),  # main_interface
        gr.update(visible=False),  # start_interface
        chatbot_history,  # chatbot
        biography,  # biography_display
        version_choices,  # version_dropdown
        logs,  # log_display
        "✅ 会话已成功恢复！"  # status_message
    )


async def handle_send_message(user_input, session_id, chatbot_history):
    """Handle user sending a message."""
    if not user_input or not session_id:
        return (chatbot_history, "", gr.update(), gr.update(), gr.update(), 
                gr.update(), gr.update(), gr.update())
    
    session = GradioSAGASession(session_id)
    
    # Add user message to chatbot
    chatbot_history.append((user_input, None))
    
    # Conduct interview round
    question, _ = await session.conduct_interview_round(user_response=user_input)
    
    # Add interviewer response
    if chatbot_history:
        chatbot_history[-1] = (user_input, question)
    
    # Get coordinator decision
    decision = await session.coordinator_decide_next_action()
    
    # Record action
    action_history = session.session_data.get("action_history", [])
    action_history.append((len(action_history) + 1, decision.get("next_action"), decision.get("reasoning")))
    session.update(action_history=action_history)
    
    logs = session.get_logs()
    
    # Get Agent工作成果
    extracted_anchors = session.session_data.get("extracted_anchors")
    historical_context = session.session_data.get("historical_context", {})
    quality_result = session.session_data.get("quality_result", {})
    
    # 格式化历史研究显示
    if historical_context and historical_context.get('search_results'):
        history_md = "## 历史背景研究\n\n"
        for idx, result in enumerate(historical_context.get('search_results', [])[:3], 1):
            query = result.get('query', '未知查询')
            summary = result.get('summary', '无摘要')
            history_md += f"### 🔍 查询 {idx}: {query}\n\n{summary}\n\n---\n\n"
    else:
        history_md = "*尚未进行历史研究*"
    
    return (
        chatbot_history,
        "",  # Clear input
        decision,  # coordinator_output
        f"当前阶段: {session.session_data.get('current_phase', 'interview')}\n访谈轮数: {len(session.session_data.get('interview_dialogue', [])) // 2}",
        logs,
        extracted_anchors,  # extracted_events_display
        history_md,  # historical_research_display
        quality_result  # quality_evaluation_display
    )


async def handle_coordinator_action(action_name, session_id):
    """Execute coordinator action manually."""
    if not session_id:
        return "❌ 没有活动会话", gr.update()
    
    session = GradioSAGASession(session_id)
    
    try:
        if action_name == "extract_events":
            await session.extract_events()
        elif action_name == "research_history":
            await session.research_history()
        elif action_name == "write_biography":
            await session.write_biography()
        elif action_name == "evaluate_quality":
            await session.evaluate_quality()
        elif action_name == "refine_biography":
            await session.refine_biography()
        elif action_name == "write_and_evaluate":
            # 创作传记并自动评估
            await session.write_biography()
            await session.evaluate_quality()
        else:
            return f"❌ 未知操作: {action_name}", gr.update()
        
        logs = session.get_logs()
        biography = session.session_data.get("biography", "*自传尚未生成*")
        
        return logs, biography
        
    except Exception as e:
        session.log("ERROR", f"❌ 执行操作失败: {e}")
        logs = session.get_logs()
        return logs, gr.update()


def copy_to_clipboard(session_id):
    """Copy biography to clipboard."""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return "❌ 会话不存在"
    
    biography = session_data.get("biography", "")
    if not biography:
        return "⚠️ 还没有自传内容"
    
    return biography  # Gradio will handle clipboard


def export_biography(session_id, format_type):
    """Export biography to file for browser download."""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        return None
    
    biography = session_data.get("biography", "")
    if not biography:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 使用临时目录
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    
    if format_type == "TXT":
        filename = f"biography_{timestamp}.txt"
        filepath = temp_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(biography)
        return str(filepath)
    
    elif format_type == "JSON":
        filename = f"biography_{timestamp}.json"
        filepath = temp_dir / filename
        export_data = session_manager.export_session_data(session_id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return str(filepath)
    
    return None


def export_logs(session_id):
    """Export logs to file for browser download."""
    logs = session_manager.get_logs(session_id)
    if not logs:
        return gr.update(visible=False)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    filename = f"saga_logs_{timestamp}.txt"
    filepath = temp_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(logs)
    
    # 返回文件路径并显示下载组件
    return gr.update(value=filepath.absolute().__str__(), visible=True)


def export_session(session_id):
    """Export complete session data as JSON."""
    if not session_id:
        return gr.update(visible=False)
    
    export_data = session_manager.export_session_data(session_id)
    if not export_data:
        return gr.update(visible=False)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    filename = f"saga_session_{timestamp}.json"
    filepath = temp_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    # 返回文件路径并显示下载组件
    return gr.update(value=filepath.absolute().__str__(), visible=True)


def import_session(file_path):
    """Import session from JSON file."""
    if not file_path:
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            "⚠️ 请选择文件"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # 创建新的会话ID
        session_id, session_data = session_manager.create_session()
        
        # 从导入数据中提取信息并更新会话
        updates = {}
        
        # 处理不同的导出格式
        if "metadata" in import_data:
            # 新格式（使用export_session_data导出的）
            if "interview" in import_data:
                updates["interview_dialogue"] = import_data["interview"].get("dialogue", [])
                updates["interview_content"] = import_data["interview"].get("content", "")
            
            if "biography" in import_data:
                updates["biography"] = import_data["biography"].get("final_version", "")
                updates["biography_versions"] = import_data["biography"].get("all_versions", [])
            
            if "evaluation" in import_data:
                updates["quality_result"] = import_data["evaluation"].get("quality", {})
                updates["hero_journey_result"] = import_data["evaluation"].get("hero_journey", {})
            
            if "research" in import_data:
                updates["extracted_anchors"] = import_data["research"].get("extracted_anchors")
                updates["historical_context"] = import_data["research"].get("historical_context", {})
            
            if "workflow" in import_data:
                updates["current_phase"] = import_data["workflow"].get("current_phase", "starting")
                updates["action_history"] = import_data["workflow"].get("action_history", [])
        else:
            # 旧格式（直接的session数据）
            updates = import_data
        
        # 更新会话
        session_manager.update_session(session_id, updates)
        session_data = session_manager.get_session(session_id)
        
        # 重建对话历史
        dialogue = session_data.get("interview_dialogue", [])
        chatbot_history = []
        
        i = 0
        while i < len(dialogue):
            if i == 0 and dialogue[0]["speaker"] == "Interviewer":
                chatbot_history.append((None, dialogue[0]["content"]))
                i += 1
            elif i + 1 < len(dialogue):
                if dialogue[i]["speaker"] == "You" and dialogue[i + 1]["speaker"] == "Interviewer":
                    chatbot_history.append((dialogue[i]["content"], dialogue[i + 1]["content"]))
                    i += 2
                else:
                    i += 1
            else:
                if dialogue[i]["speaker"] == "You":
                    chatbot_history.append((dialogue[i]["content"], None))
                i += 1
        
        # 获取传记
        biography = session_data.get("biography", "*自传尚未生成*")
        
        # 获取版本
        versions = session_data.get("biography_versions", [])
        version_choices = [f"版本 {v['version']} - {v['timestamp'][:19]}" for v in versions]
        
        # 添加日志
        session_manager.add_log(session_id, "INFO", f"📥 已从JSON文件导入会话（包含{len(dialogue)}条对话）")
        session_manager.save_session(session_id)
        logs = session_manager.get_logs(session_id)
        
        # Get Agent工作成果
        extracted_anchors = session_data.get("extracted_anchors")
        historical_context = session_data.get("historical_context", {})
        quality_result = session_data.get("quality_result", {})
        
        # 格式化历史研究显示
        if historical_context and historical_context.get('search_results'):
            history_md = "## 历史背景研究\n\n"
            for idx, result in enumerate(historical_context.get('search_results', [])[:3], 1):
                query = result.get('query', '未知查询')
                summary = result.get('summary', '无摘要')
                history_md += f"### 🔍 查询 {idx}: {query}\n\n{summary}\n\n---\n\n"
        else:
            history_md = "*尚未进行历史研究*"
        
        return (
            session_id,  # session_id_display
            chatbot_history,  # chatbot
            biography,  # biography_display
            version_choices,  # version_dropdown
            logs,  # log_display
            f"当前阶段: {session_data.get('current_phase', 'starting')}\n访谈轮数: {len(dialogue) // 2}",  # agent_status
            {},  # coordinator_output
            "✅ 会话已成功导入！",  # status_message
            extracted_anchors,  # extracted_events_display
            history_md,  # historical_research_display
            quality_result  # quality_evaluation_display
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Import error: {error_detail}")
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            f"❌ 导入失败: {str(e)}",
            gr.update(),
            gr.update(),
            gr.update()
        )


# ============================================================================
# Gradio UI Layout
# ============================================================================

def create_gradio_interface():
    """Create Gradio interface."""
    
    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange"),
        title="SAGA传记生成系统",
        css="""
        /* 全局样式优化 */
        .gradio-container {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif !important;
        }
        
        /* 圆角美化 */
        .gr-button {
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }
        
        .gr-button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }
        
        .gr-box, .gr-input, .gr-text-input, textarea {
            border-radius: 16px !important;
            border: 1px solid #e0e0e0 !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        }
        
        .gr-panel {
            border-radius: 20px !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
        }
        
        .gr-accordion {
            border-radius: 16px !important;
            overflow: hidden !important;
        }
        
        /* Chatbot美化 - 蓝绿浅色配色 */
        .message-wrap {
            border-radius: 18px !important;
            padding: 12px !important;
            margin: 8px 0 !important;
        }
        
        .message.user {
            background: linear-gradient(135deg, #a8e6cf 0%, #81c784 100%) !important;
            border-radius: 18px 18px 4px 18px !important;
            color: #2e5d4e !important;
        }
        
        .message.bot {
            background: linear-gradient(135deg, #b3d9ff 0%, #81b3ff 100%) !important;
            border-radius: 18px 18px 18px 4px !important;
            color: #1a4d7a !important;
        }
        
        /* Agent状态标签美化 */
        .agent-coordinator { 
            border-left: 5px solid #FF8C00 !important;
            border-radius: 0 12px 12px 0 !important;
            padding-left: 16px !important;
        }
        .agent-interview { 
            border-left: 5px solid #4169E1 !important;
            border-radius: 0 12px 12px 0 !important;
            padding-left: 16px !important;
        }
        .agent-history { 
            border-left: 5px solid #9370DB !important;
            border-radius: 0 12px 12px 0 !important;
            padding-left: 16px !important;
        }
        .agent-writer { 
            border-left: 5px solid #32CD32 !important;
            border-radius: 0 12px 12px 0 !important;
            padding-left: 16px !important;
        }
        .agent-evaluator { 
            border-left: 5px solid #DC143C !important;
            border-radius: 0 12px 12px 0 !important;
            padding-left: 16px !important;
        }
        
        /* 输入框增强 */
        textarea:focus, input:focus {
            outline: none !important;
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        
        /* 卡片容器 */
        .gr-group {
            border-radius: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
            border: none !important;
        }
        
        /* 主要按钮强化 */
        .gr-button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            font-weight: 600 !important;
        }
        
        .gr-button-primary:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        }
        
        /* 滚动条美化 */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* 标题美化 - 增强版 */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
            font-size: 2.2em !important;
            margin-bottom: 0.5em !important;
        }
        
        h2 {
            color: #4a5568 !important;
            font-weight: 600 !important;
            font-size: 1.5em !important;
            margin-top: 1.5em !important;
            margin-bottom: 0.8em !important;
            padding-bottom: 0.5em !important;
            border-bottom: 2px solid #e2e8f0 !important;
        }
        
        h3 {
            background: linear-gradient(135deg, #4299e1 0%, #667eea 100%);
            color: white !important;
            font-weight: 600 !important;
            font-size: 1.1em !important;
            padding: 10px 16px !important;
            border-radius: 12px !important;
            margin-top: 1.2em !important;
            margin-bottom: 0.8em !important;
            box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3) !important;
            display: inline-block !important;
            width: 100% !important;
        }
        
        /* 让emoji在标题中更好看 */
        h3::before {
            margin-right: 8px;
        }
        
        /* 会话ID样式优化 */
        .session-id-label {
            margin-bottom: 8px !important;
        }
        
        .session-id-label p {
            margin: 0 !important;
            font-size: 0.85em !important;
            color: #718096 !important;
            font-weight: 500 !important;
        }
        
        .session-id-text input {
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace !important;
            font-size: 0.85em !important;
            color: #2d3748 !important;
            background: #f7fafc !important;
            border: 1px solid #cbd5e0 !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
            height: 42px !important;
            line-height: 1.5 !important;
        }
        
        .session-id-text input:hover {
            border-color: #a0aec0 !important;
        }
        
        /* 统一按钮高度 */
        .gr-button-sm {
            height: 42px !important;
            min-height: 42px !important;
        }
        
        /* 大按钮样式优化 */
        .gr-button-lg {
            font-size: 1.05em !important;
            font-weight: 600 !important;
            padding: 14px 28px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .gr-button-lg:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15) !important;
        }
        """
    ) as demo:
        
        # Header
        gr.Markdown("""
        # 🎭 SAGA传记生成系统
        
        智能多Agent协作，为您创作专属传记
        """)
        
        # Start Interface
        with gr.Group(visible=True) as start_interface:
            gr.Markdown("""
            ## 欢迎使用SAGA系统！
            
            您可以：
            - 🆕 创建新会话，开始传记创作
            - 🔄 恢复历史会话，继续之前的创作
            - 📥 导入JSON文件，断点续传
            """)
            
            with gr.Row(equal_height=True):
                with gr.Column():
                    gr.Markdown("### 🆕 开始新会话")
                    start_btn = gr.Button("开始新会话", variant="primary", size="lg")
                
                with gr.Column():
                    gr.Markdown("### 🔄 恢复历史会话")
                    resume_input = gr.Textbox(
                        label="输入会话ID",
                        placeholder="例如: user_20241114_123456_abc12345",
                        show_label=False
                    )
                    resume_btn = gr.Button("恢复会话", size="lg")
                
                with gr.Column():
                    gr.Markdown("### 📥 导入会话JSON")
                    import_start_file = gr.UploadButton(
                        "选择JSON文件",
                        file_types=[".json"],
                        file_count="single",
                        size="lg"
                    )
        
        # Main Interface
        with gr.Group(visible=False) as main_interface:
            # Session ID Display 和 导入/导出（紧凑布局）
            gr.Markdown("**📌 当前会话ID**", elem_classes=["session-id-label"])
            with gr.Row():
                session_id_display = gr.Textbox(
                    value="",
                    interactive=False,
                    show_label=False,
                    container=False,
                    lines=1,
                    scale=6,
                    elem_classes=["session-id-text"]
                )
                import_session_btn = gr.UploadButton(
                    "📥 导入",
                    file_types=[".json"],
                    file_count="single",
                    size="sm",
                    variant="secondary",
                    scale=1
                )
                export_session_btn = gr.Button(
                    "💾 导出",
                    size="sm",
                    variant="secondary",
                    scale=1
                )
            
            # 下载文件组件（初始隐藏，导出后显示）
            download_session_file = gr.File(label="📦 点击下载导出文件", visible=False, height=60, interactive=False)
            
            # Main Layout
            with gr.Row():
                # Left Column: 对话交互 + 传记内容
                with gr.Column(scale=1):
                    gr.Markdown("### 💬 对话交互")
                    
                    chatbot = gr.Chatbot(
                        label="访谈对话",
                        height=400,
                        show_label=False
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            label="您的回答",
                            placeholder="请输入您的回答，按Enter发送...",
                            lines=3,
                            scale=4
                        )
                        send_btn = gr.Button("📤 发送", variant="primary", scale=1, size="lg")
                    
                    gr.Markdown("### 📖 传记内容")
                    
                    biography_display = gr.Markdown(
                        value="*传记将在创作完成后显示*",
                        label="传记",
                        show_label=False
                    )
                    
                    with gr.Row():
                        version_dropdown = gr.Dropdown(
                            label="选择版本",
                            choices=[],
                            scale=2
                        )
                        word_count = gr.Textbox(
                            label="字数",
                            value="0",
                            interactive=False,
                            scale=1
                        )
                    
                    # 复制区域
                    copy_textbox = gr.Textbox(
                        label="📋 点击下方按钮复制传记内容",
                        lines=3,
                        visible=True,
                        interactive=True
                    )
                    
                    copy_bio_btn = gr.Button("📋 加载到复制框", size="sm")
                
                # Right Column: Agent状态 + 系统日志
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 Agent状态")
                    
                    with gr.Accordion("🧠 Coordinator决策", open=True, elem_classes=["agent-coordinator"]):
                        coordinator_output = gr.JSON(label="决策详情")
                    
                    agent_status = gr.Textbox(
                        label="当前状态",
                        lines=2,
                        interactive=False
                    )
                    
                    # Agent工作成果展示
                    with gr.Accordion("📚 提取事件", open=False):
                        extracted_events_display = gr.JSON(label="事件锚点", show_label=False)
                    
                    with gr.Accordion("🔍 历史研究", open=False):
                        historical_research_display = gr.Markdown(
                            value="*尚未进行历史研究*",
                            show_label=False
                        )
                    
                    with gr.Accordion("📊 质量评估", open=False):
                        quality_evaluation_display = gr.JSON(label="评估结果", show_label=False)
                    
                    gr.Markdown("### 📋 系统日志")
                    
                    log_display = gr.Textbox(
                        label="日志",
                        lines=15,
                        max_lines=20,
                        interactive=False,
                        show_label=False
                    )
                    
                    download_log_btn = gr.Button("📥 下载日志", size="sm")
                    download_log_file = gr.File(label="📦 点击下载日志文件", visible=False, height=50, interactive=False)
        
        # Hidden status message
        status_message = gr.Textbox(visible=False)
        download_file = gr.File(visible=False)
        copy_output = gr.Textbox(visible=False)
        
        # ====================================================================
        # Event Bindings
        # ====================================================================
        
        # Start new session
        start_btn.click(
            fn=create_new_session,
            inputs=[],
            outputs=[
                session_id_display,
                main_interface,
                start_interface,
                chatbot,
                user_input,
                coordinator_output,
                agent_status,
                biography_display,
                log_display,
                version_dropdown
            ]
        )
        
        # Resume session
        resume_btn.click(
            fn=resume_existing_session,
            inputs=[resume_input],
            outputs=[
                session_id_display,
                main_interface,
                start_interface,
                chatbot,
                biography_display,
                version_dropdown,
                log_display,
                status_message
            ]
        )
        
        # Import session from start interface
        def import_and_show(file_path):
            result = import_session(file_path)
            # result是11个值（增加了3个Agent成果显示），我们需要在末尾添加界面显示状态
            return result + (gr.update(visible=True), gr.update(visible=False))
        
        import_start_file.upload(
            fn=import_and_show,
            inputs=[import_start_file],
            outputs=[
                session_id_display,
                chatbot,
                biography_display,
                version_dropdown,
                log_display,
                agent_status,
                coordinator_output,
                status_message,
                extracted_events_display,
                historical_research_display,
                quality_evaluation_display,
                main_interface,
                start_interface
            ]
        )
        
        # Send message - 点击按钮
        send_btn.click(
            fn=handle_send_message,
            inputs=[user_input, session_id_display, chatbot],
            outputs=[
                chatbot, 
                user_input, 
                coordinator_output, 
                agent_status, 
                log_display,
                extracted_events_display,
                historical_research_display,
                quality_evaluation_display
            ]
        )
        
        # Send message - 按Enter键
        user_input.submit(
            fn=handle_send_message,
            inputs=[user_input, session_id_display, chatbot],
            outputs=[
                chatbot, 
                user_input, 
                coordinator_output, 
                agent_status, 
                log_display,
                extracted_events_display,
                historical_research_display,
                quality_evaluation_display
            ]
        )
        
        # Copy biography
        copy_bio_btn.click(
            fn=copy_to_clipboard,
            inputs=[session_id_display],
            outputs=[copy_textbox]
        )
        
        # 导入会话
        import_session_btn.upload(
            fn=import_session,
            inputs=[import_session_btn],
            outputs=[
                session_id_display,
                chatbot,
                biography_display,
                version_dropdown,
                log_display,
                agent_status,
                coordinator_output,
                status_message,
                extracted_events_display,
                historical_research_display,
                quality_evaluation_display
            ]
        )
        
        # 导出完整会话
        export_session_btn.click(
            fn=export_session,
            inputs=[session_id_display],
            outputs=[download_session_file]
        )
        
        # Download logs
        download_log_btn.click(
            fn=export_logs,
            inputs=[session_id_display],
            outputs=[download_log_file]
        )
    
    return demo


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    import os
    
    port = int(os.getenv("PORT", 7860))
    
    print("🚀 启动SAGA传记生成系统...")
    print(f"🤖 当前模型: {settings.default_model}")
    print(f"💾 会话存储路径: sessions/")
    print(f"🌐 服务端口: {port}")
    
    demo = create_gradio_interface()
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        show_api=False
    )


if __name__ == "__main__":
    main()

