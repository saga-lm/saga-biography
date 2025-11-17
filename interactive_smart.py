#!/usr/bin/env python3
"""
Smart Interactive mode for SAGA Biography Generation System.
Uses Coordinator Agent to dynamically control the workflow.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import re
import json
import warnings

# Suppress AutoGen warnings
warnings.filterwarnings('ignore', message='Missing required field.*structured_output.*')

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from autogen_core.models import UserMessage
from config.settings import settings
from src.models.client_manager import model_manager
from src.tools.history_analyzer import event_extractor, contextualizer
from src.tools.quality_evaluator import quality_critic, hero_evaluator
from src.utils.file_manager import file_manager


class SmartInteractiveSession:
    """Smart interactive session with dynamic coordinator control."""
    
    def __init__(self):
        self.interview_content = ""
        self.interview_dialogue = []
        self.biography = ""
        self.biography_versions = []  # Track all versions
        self.quality_result = {}
        self.hero_journey_result = {}
        self.historical_context = {}
        self.current_phase = "starting"
        self.conversation_history = ""
        self.extracted_anchors = None
        
        # Action history to prevent loops
        self.action_history = []  # List of (iteration, action, reasoning)
        
    def display_header(self):
        """Display system header."""
        print("\n" + "=" * 80)
        print("🎭 SAGA Biography Generation System - Smart Interactive Mode")
        print("=" * 80)
        print("✨ AI Coordinator dynamically manages the biography creation process")
        print("🧠 Coordinator | Interview Agent | History Researcher | Writer | Evaluator")
        print("-" * 80)
    
    def display_phase(self, phase: str, description: str):
        """Display current phase."""
        phase_icons = {
            "interview": "🎤",
            "history": "📚", 
            "writing": "✍️",
            "quality": "🔍",
            "refine": "🔄",
            "completed": "🎉"
        }
        icon = phase_icons.get(phase, "⚡")
        self.current_phase = phase
        print(f"\n{icon} 【{phase.upper()} PHASE】{description}")
        print("-" * 60)
    
    def display_agent_action(self, agent_name: str, action: str, content: str = ""):
        """Display agent action with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
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
    
    def display_coordinator_decision(self, decision: dict):
        """Display coordinator's decision."""
        print(f"\n🧠 Coordinator 决策:")
        print("-" * 50)
        print(f"   下一步行动: {decision.get('next_action', 'unknown')}")
        print(f"   原因: {decision.get('reasoning', 'N/A')}")
        if decision.get('parameters'):
            print(f"   参数: {decision.get('parameters')}")
        print("-" * 50)
    
    def display_search_results(self, query: str, results: list):
        """Display search results with sources."""
        print(f"\n🔍 搜索查询: {query}")
        print("   搜索结果:")
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('content', '')
            print(f"\n   {i}. {title}")
            print(f"      🔗 {url}")
            if content:
                summary = content[:150] + "..." if len(content) > 150 else content
                print(f"      📄 {summary}")
    
    async def coordinator_decide_next_action(self) -> dict:
        """Coordinator decides what to do next."""
        coordinator_client = model_manager.create_client()
        
        # Get recent action history
        recent_actions = self.action_history[-10:] if self.action_history else []
        action_summary = "\n".join([
            f"  迭代{iter}: {action} - {reason[:50]}..."
            for iter, action, reason in recent_actions
        ]) if recent_actions else "  尚未执行任何 action"
        
        # Count action frequencies
        action_counts = {}
        for _, action, _ in recent_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Check if stuck in a loop
        last_3_actions = [action for _, action, _ in recent_actions[-3:]]
        is_repeating = len(set(last_3_actions)) == 1 and len(last_3_actions) == 3
        
        # Build rich context for coordinator
        context = f"""当前状态快照:
- 当前阶段: {self.current_phase}
- 访谈轮数: {len(self.interview_dialogue) // 2}
- 访谈内容: {len(self.interview_content)} 字符
- 自传版本: {len(self.biography_versions)} 个
- 已有自传: {'是' if self.biography else '否'} ({len(self.biography)} 字)
- 质量评估: {'是' if self.quality_result else '否'} ({self.quality_result.get('overall_score', 0):.1f}/10)
- 事件提取: {'是' if self.extracted_anchors else '否'}
- 历史研究: {'是' if self.historical_context else '否'}

📊 最近执行的 Actions (最近10次):
{action_summary}

⚠️ Action 频率统计:
{', '.join([f'{action}({count}次)' for action, count in action_counts.items()]) if action_counts else '无'}

🚨 警告: {'正在重复同一个action！必须换一个！' if is_repeating else '运行正常'}

📝 最近3轮对话:
{self.conversation_history[-800:] if self.conversation_history else '尚未开始'}

📖 当前自传内容（如有）:
{self.biography[:300] + '...' if len(self.biography) > 300 else self.biography if self.biography else '尚未生成'}

🎯 关键信息点:
- 用户最后一句话: {self.interview_dialogue[-1]['content'][:100] if self.interview_dialogue else '无'}
"""
        
        prompt = f"""{context}

你是SAGA系统的智能协调者（Coordinator），负责协调多个 AI agents 和 tools 完成自传创作。

📋 可用的 Agents 和 Tools:

1. **Interview Agent** (访谈代理)
   - 作用：与用户对话，收集人生故事
   - 能力：提出深入问题，引导用户分享
   - 输出：访谈对话记录
   
2. **Event Extractor** (事件提取器)
   - 作用：从访谈中提取历史事件锚点
   - 能力：识别时间、地点、历史事件
   - 输出：结构化的历史事件列表
   - Tool: `event_extractor.extract_historical_anchors()`
   
3. **History Contextualizer** (历史背景研究器)
   - 作用：搜索和分析历史背景
   - 能力：使用 Tavily API 搜索互联网
   - 输出：相关历史事件的详细背景
   - Tool: `contextualizer.contextualize_events()`
   
4. **Biography Writer** (自传作者)
   - 作用：基于访谈和历史背景创作自传
   - 能力：运用英雄之旅框架编织故事
   - 输出：完整的自传文本
   - 使用：通过 model_client 调用 AI 创作
   
5. **Quality Evaluator** (质量评估器)
   - 作用：评估自传质量和英雄之旅契合度
   - 能力：多维度评分（叙事、情感、历史、语言）
   - 输出：质量分数 (0-10) 和改进建议
   - Tool: `quality_critic.evaluate()`, `hero_evaluator.evaluate_biography()`

🔄 推荐的 Workflow（灵活执行）:

**阶段 1: 信息收集**
```
Interview Agent (3-10轮)
  ↓ 如果用户提到历史事件（如"文革"）
  ↓→ 立即调用 History Contextualizer
  ↓ 继续 Interview
  ↓ 信息充足时
  ↓
结束访谈
```

**阶段 2: 信息处理**
```
调用 Event Extractor
  → 提取历史事件锚点
  
如果有新事件需要背景
  → 调用 History Contextualizer
  → 搜索历史背景
```

**阶段 3: 创作与优化**
```
调用 Biography Writer
  → 创作初稿
  ↓
调用 Quality Evaluator
  → 评估质量
  ↓
如果分数 < 8
  → 调用 Biography Writer（带改进建议）
  → 优化自传
  → 重新评估
  ↓
质量达标 → 完成
```

🎯 可用 Actions 及对应的 Agent/Tool:

1. **continue_interview** 
   - Agent: Interview Agent
   - 场景：信息不足，需要更多细节
   - 场景：用户分享不够深入
   - 场景：重要领域（童年、工作、转折点）还未涉及
   - 询问策略：开放式问题 → 具体细节 → 情感体验

2. **end_interview**
   - 标记访谈结束
   - 场景：已收集足够信息（通常5-10轮）
   - 场景：用户表示想结束
   - 场景：覆盖了主要人生阶段

3. **extract_events**
   - Tool: Event Extractor (event_extractor.extract_historical_anchors)
   - 场景：访谈中提到了时间、地点、历史事件
   - 场景：需要识别可研究的历史背景
   - 场景：准备创作前的信息整理
   - ⚡ 提取一次即可，不需要重复

4. **research_history**
   - Tool: History Contextualizer (contextualizer.contextualize_events)
   - 触发条件：
     * 用户提到具体历史事件（如"文革"、"下岗潮"、"改革开放"）
     * 提到特定年代（如"90年代"、"2008年"）
     * Event Extractor 识别出历史锚点
   - 能力：使用 Tavily API 搜索互联网获取历史背景
   - ⚡ 可以随时触发！不需要等访谈结束
   - ⚡ 搜索一次即可，不需要重复（除非有新事件）

5. **write_biography**
   - Agent: Biography Writer (使用 AI model)
   - 前置条件：
     * 有足够访谈内容（通常≥5轮）
     * 最好有历史背景（不是必须）
   - 能力：运用英雄之旅框架编织个人故事
   - 可以先写初稿，后续继续完善

6. **evaluate_quality**
   - Tool: Quality Evaluator (quality_critic + hero_evaluator)
   - 场景：有自传内容需要评估
   - 输出：质量分数(0-10) + 英雄之旅契合度 + 改进建议
   - 评估维度：叙事质量、情感深度、历史融合、语言表达

7. **refine_biography**
   - Agent: Biography Writer (带改进建议)
   - 触发条件：质量评估 < 8分
   - 输入：原自传 + 质量评估的改进建议
   - 输出：优化后的新版本

8. **complete**
   - 完成整个流程
   - 条件：质量达标（≥8分）或已多轮优化

🧠 智能决策原则:

1. **理解 Agent/Tool 的作用**：
   - Interview Agent → 收集信息（对话）
   - Event Extractor → 分析信息（提取结构）
   - History Contextualizer → 补充背景（搜索）
   - Biography Writer → 创作内容（写作）
   - Quality Evaluator → 评估质量（打分）

2. **反应式触发**：
   - 用户提到"文革" → 立即 research_history (调用 History Contextualizer)
   - 用户说"就这些" → 考虑 end_interview
   - 发现信息空缺 → continue_interview (调用 Interview Agent)
   - 访谈内容丰富 → extract_events (调用 Event Extractor)

3. **Agent 调用顺序指引**：
   ```
   典型流程:
   Interview Agent (收集) 
     → Event Extractor (分析)
     → History Contextualizer (搜索)
     → Biography Writer (创作)
     → Quality Evaluator (评估)
     → Biography Writer (优化)
   
   灵活变化:
   - 访谈过程中可随时调用 History Contextualizer
   - 可以边访谈边提取事件
   - 可以先写初稿，再继续访谈补充
   ```

4. **质量优先**：
   - 宁可多问几轮，确保 Interview Agent 收集足够信息
   - Quality Evaluator 评分 < 8 → 必须调用 Biography Writer 优化
   - 有疑问就继续 Interview

5. **避免重复调用**：
   - Event Extractor: 提取一次即可
   - History Contextualizer: 搜索一次即可（除非有新事件）
   - Quality Evaluator: 评估后应该优化或完成，不是再评估

⚠️ 关键约束:
1. **禁止连续重复同一个 action**
   - 如果刚执行了 research_history，下次不要再选 research_history
   - 如果刚执行了 extract_events，下次不要再选 extract_events
   - 查看"最近执行的 Actions"避免重复

2. **各 action 通常只需执行一次**
   - extract_events: 提取一次即可，不需要重复
   - research_history: 搜索一次即可，不需要重复搜索
   - evaluate_quality: 评估后应该 refine 或 complete，不是再评估
   
3. **正确的流程推进**
   - extract_events → research_history → write_biography
   - 不是 extract_events → extract_events → extract_events
   - 不是 research_history → research_history → research_history

4. **如果发现重复**
   - 立即选择不同的 action
   - 推进到下一个阶段
   - 例如：已经 research_history → 应该 write_biography 或 continue_interview

请以JSON格式返回决策:
{{
  "next_action": "行动名称",
  "reasoning": "基于当前对话内容和状态的详细决策理由",
  "trigger": "触发这个决策的具体内容或条件",
  "confidence": 0.0-1.0
}}"""
        
        try:
            response = await coordinator_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )
            
            # Parse JSON response
            response_text = response.content.strip()
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            decision = json.loads(response_text)
            
            # Validate decision to prevent loops
            next_action = decision.get("next_action")
            
            # Check if repeating the same action
            if len(self.action_history) >= 2:
                last_action = self.action_history[-1][1]
                second_last_action = self.action_history[-2][1] if len(self.action_history) >= 2 else None
                
                # If same action 2 times in a row, force change
                if next_action == last_action == second_last_action:
                    print(f"⚠️ 检测到连续3次相同action '{next_action}'，强制切换！")
                    
                    # Force different action based on state
                    if self.biography and not self.quality_result:
                        decision = {
                            "next_action": "evaluate_quality",
                            "reasoning": "检测到重复action，强制切换到评估质量",
                            "confidence": 0.9
                        }
                    elif self.extracted_anchors and self.historical_context and not self.biography:
                        decision = {
                            "next_action": "write_biography",
                            "reasoning": "检测到重复action，强制切换到创作自传",
                            "confidence": 0.9
                        }
                    elif self.extracted_anchors and not self.historical_context:
                        decision = {
                            "next_action": "write_biography",
                            "reasoning": "检测到重复research，跳过继续创作",
                            "confidence": 0.85
                        }
                    elif len(self.interview_dialogue) < 5:
                        decision = {
                            "next_action": "continue_interview",
                            "reasoning": "检测到重复action，回到访谈",
                            "confidence": 0.8
                        }
                    else:
                        # Default: move to write biography
                        decision = {
                            "next_action": "write_biography",
                            "reasoning": "检测到重复action，强制推进到创作阶段",
                            "confidence": 0.75
                        }
            
            return decision
            
        except Exception as e:
            print(f"⚠️ Coordinator决策解析失败: {e}")
            print(f"   使用智能fallback逻辑...")
            
            # Intelligent fallback - prioritize based on context, not rigid flow
            
            # Priority 1: If we have biography and it's low quality, improve it
            if self.biography and self.quality_result:
                if self.quality_result.get("overall_score", 0) < 8.0:
                    return {
                        "next_action": "refine_biography",
                        "reasoning": f"自传质量{self.quality_result.get('overall_score', 0):.1f}分，需要优化",
                        "confidence": 0.9
                    }
                else:
                    return {
                        "next_action": "complete",
                        "reasoning": f"质量达标({self.quality_result.get('overall_score', 0):.1f}分)，可以完成",
                        "confidence": 0.95
                    }
            
            # Priority 2: If we have biography but no evaluation, evaluate it
            if self.biography and not self.quality_result:
                return {
                    "next_action": "evaluate_quality",
                    "reasoning": "有自传但未评估，需要了解质量水平",
                    "confidence": 0.88
                }
            
            # Priority 3: If we have enough interview data and context, write biography
            if len(self.interview_dialogue) >= 6 and (self.historical_context or len(self.interview_content) > 1500):
                if not self.biography:
                    return {
                        "next_action": "write_biography",
                        "reasoning": "访谈内容充足，可以开始创作",
                        "confidence": 0.85
                    }
            
            # Priority 4: If interview has events mentioned but not extracted
            if len(self.interview_dialogue) >= 3 and not self.extracted_anchors:
                return {
                    "next_action": "extract_events",
                    "reasoning": "访谈中可能有历史事件，先提取分析",
                    "confidence": 0.75
                }
            
            # Priority 5: If we have events but no historical context
            if self.extracted_anchors and not self.historical_context:
                return {
                    "next_action": "research_history",
                    "reasoning": "已提取事件，需要搜索历史背景",
                    "confidence": 0.82
                }
            
            # Priority 6: If interview is too short, continue
            if len(self.interview_dialogue) < 3:
                return {
                    "next_action": "continue_interview",
                    "reasoning": "访谈内容太少，需要更多信息",
                    "confidence": 0.95
                }
            
            # Priority 7: If stuck in post_interview phase, move forward
            if self.current_phase == "post_interview":
                if not self.extracted_anchors:
                    return {
                        "next_action": "extract_events",
                        "reasoning": "访谈已结束，开始提取事件",
                        "confidence": 0.8
                    }
                elif not self.biography:
                    return {
                        "next_action": "write_biography",
                        "reasoning": "信息已收集，开始创作",
                        "confidence": 0.78
                    }
            
            # Default: continue interview if unsure
            return {
                "next_action": "continue_interview",
                "reasoning": "不确定下一步，继续访谈收集更多信息",
                "confidence": 0.6
            }
    
    async def conduct_interview_round(self) -> tuple[str, str]:
        """Conduct one round of interview."""
        model_client = model_manager.create_client()
        
        if len(self.interview_dialogue) == 0:
            # First question
            question = """你好！我是专业的人生故事访谈师，很高兴能够倾听您的故事。

今天的目标是一起回顾您的人生历程，挖掘珍贵的记忆和经历，为创作您的个人自传收集素材。

请先简单介绍一下自己吧，比如姓名、年龄，以及现在的生活状况。我们可以从任何您愿意分享的地方开始。

请放轻松，就像和老朋友聊天一样。"""
            
            self.display_agent_action("Interview Agent", "开场问题", question)
            
        else:
            # Generate next question
            prompt = f"""你是专业的人生故事访谈师，正在进行深度访谈。

对话历史:
{self.conversation_history[-1500:]}

用户最新回答: {self.interview_dialogue[-1]['content'] if self.interview_dialogue else ''}

基于用户回答，生成下一个有针对性的访谈问题。

要求:
1. 根据用户回答深度调整问题
2. 捕捉情感线索和关键词
3. 自然过渡不同人生阶段
4. 温暖、共情、启发性

格式:
<thinking>
  <intent>意图分析</intent>
  <memory>记忆关联</memory>
  <mental_state>心理状态</mental_state>
</thinking>
<response>你的问题</response>"""
            
            response = await model_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )
            
            full_response = response.content.strip()
            
            # Extract thinking and question
            thinking_content = None
            question = full_response
            
            # First check if there are XML tags
            if "<thinking>" in full_response and "<response>" in full_response:
                # Extract thinking
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
                if thinking_match:
                    thinking_content = thinking_match.group(1).strip()
                    self.display_thinking("Interview Agent", thinking_content)
                
                # Extract response
                response_match = re.search(r'<response>(.*?)</response>', full_response, re.DOTALL)
                if response_match:
                    question = response_match.group(1).strip()
                else:
                    # Fallback: remove thinking tags and use rest
                    question = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
                    question = re.sub(r'</?response>', '', question).strip()
            elif "<thinking>" in full_response:
                # Only thinking, no response tag - extract what's outside thinking
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
                if thinking_match:
                    thinking_content = thinking_match.group(1).strip()
                    self.display_thinking("Interview Agent", thinking_content)
                    # Remove thinking tags from question
                    question = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
            elif "<response>" in full_response:
                # Only response tag
                response_match = re.search(r'<response>(.*?)</response>', full_response, re.DOTALL)
                if response_match:
                    question = response_match.group(1).strip()
            
            # Final cleanup - remove any remaining XML tags
            question = re.sub(r'</?thinking>', '', question).strip()
            question = re.sub(r'</?response>', '', question).strip()
            question = re.sub(r'</?intent>', '', question).strip()
            question = re.sub(r'</?memory>', '', question).strip()
            question = re.sub(r'</?mental_state>', '', question).strip()
            
            # If question is still empty or too short, use original
            if not question or len(question) < 10:
                question = full_response
            
            self.display_agent_action("Interview Agent", f"访谈问题 (第{len(self.interview_dialogue)//2 + 1}轮)", question)
        
        # Get user response
        user_response = input("\n👤 You: ").strip()
        
        # Record dialogue
        self.interview_dialogue.append({"speaker": "Interviewer", "content": question})
        self.interview_dialogue.append({"speaker": "You", "content": user_response})
        
        # Update content and history
        self.interview_content += f"Interviewer: {question}\nYou: {user_response}\n\n"
        self.conversation_history += f"\nInterviewer: {question}\nYou: {user_response}"
        
        return question, user_response
    
    async def extract_events(self):
        """Extract event anchors."""
        self.display_phase("history", "提取历史事件锚点")
        self.display_agent_action("History Analyzer", "开始提取事件锚点")
        
        self.extracted_anchors = await event_extractor.extract_event_anchors(self.interview_content)
        
        if self.extracted_anchors:
            print(f"\n✅ 提取到事件锚点:")
            if 'temporal_anchors' in self.extracted_anchors:
                print(f"   ⏰ 时间锚点: {', '.join(self.extracted_anchors['temporal_anchors'][:5])}")
            if 'location_anchors' in self.extracted_anchors:
                print(f"   📍 地点锚点: {', '.join(self.extracted_anchors['location_anchors'][:5])}")
    
    async def research_history(self):
        """Research historical context."""
        self.display_phase("history", "研究历史背景")
        self.display_agent_action("History Researcher", "开始历史背景研究")
        
        if self.extracted_anchors:
            self.historical_context = await contextualizer.research_historical_context_enhanced(
                self.extracted_anchors
            )
            
            search_results = self.historical_context.get('search_results', [])
            if search_results:
                print(f"\n✅ 完成 {len(search_results)} 次搜索")
                for search_result in search_results[:2]:
                    query = search_result.get('query', '')
                    results = search_result.get('results', [])
                    self.display_search_results(query, results)
    
    async def write_biography(self):
        """Write or update biography."""
        self.display_phase("writing", "创作自传")
        self.display_agent_action("Biography Writer", "开始创作自传")
        
        model_client = model_manager.create_client()
        
        prompt = f"""基于以下访谈内容和历史背景，创作一篇2000-3000字的个人自传。

使用英雄之旅框架:
- Protagonist: 认识自己作为英雄/主角
- Shift: 关键转变或新体验
- Quest: 明确的目标和使命
- Allies: 来自他人和导师的支持
- Challenge: 面临的障碍和困难
- Transformation: 个人成长和变化
- Legacy: 对他人的持久影响

访谈内容:
{self.interview_content}

历史背景:
{self.historical_context}

要求:
1. 第一人称视角
2. 真实感人的语言
3. 融合个人经历与时代背景
4. 突出成长、坚韧和智慧
5. 丰富的情感表达
6. 优美的文学语言
7. 结构完整，逻辑清晰

请创作高质量自传:"""
        
        response = await model_client.create(
            messages=[UserMessage(content=prompt, source="user")]
        )
        
        self.biography = response.content.strip()
        self.biography_versions.append({
            "version": len(self.biography_versions) + 1,
            "content": self.biography,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"\n✅ 自传创作完成 (版本{len(self.biography_versions)}), {len(self.biography)}字")
        print("\n" + "=" * 80)
        print("📖 自传内容:")
        print("=" * 80)
        if len(self.biography) > 800:
            print(self.biography[:800] + "...")
        else:
            print(self.biography)
        print("=" * 80)
    
    async def evaluate_quality(self):
        """Evaluate biography quality."""
        self.display_phase("quality", "质量评估")
        self.display_agent_action("Quality Evaluator", "开始评估")
        
        self.quality_result = await quality_critic.evaluate_biography_quality(self.biography)
        
        score = self.quality_result.get("overall_score", 0)
        print(f"\n✅ 质量评分: {score}/10.0")
        
        if "dimension_scores" in self.quality_result:
            print("\n📊 维度得分:")
            for dim, s in self.quality_result["dimension_scores"].items():
                print(f"   {dim}: {s}/10.0")
    
    async def refine_biography(self):
        """Refine biography based on evaluation."""
        self.display_phase("refine", "优化自传")
        self.display_agent_action("Biography Writer", "根据评估反馈优化")
        
        model_client = model_manager.create_client()
        
        feedback = self.quality_result.get("feedback", "")
        
        prompt = f"""请根据以下评估反馈优化这篇自传:

当前自传:
{self.biography}

质量评分: {self.quality_result.get('overall_score', 0)}/10.0

评估反馈:
{feedback}

请优化并返回改进版本:"""
        
        response = await model_client.create(
            messages=[UserMessage(content=prompt, source="user")]
        )
        
        self.biography = response.content.strip()
        self.biography_versions.append({
            "version": len(self.biography_versions) + 1,
            "content": self.biography,
            "timestamp": datetime.now().isoformat(),
            "refined": True
        })
        
        print(f"\n✅ 自传已优化 (版本{len(self.biography_versions)})")
    
    async def save_results(self):
        """Save all results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        person_id = f"smart_interactive_{timestamp}"
        
        # Save interview
        interview_file = file_manager.save_interview(
            person_id=person_id,
            interview_content=self.interview_content,
            dialogue=self.interview_dialogue
        )
        
        # Save final biography
        biography_file = file_manager.save_biography(
            person_id=person_id,
            biography_content=self.biography,
            version="final"
        )
        
        # Save all versions
        versions_file = file_manager.results_dir / "biographies" / f"{person_id}_all_versions.json"
        versions_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(versions_file, 'w', encoding='utf-8') as f:
            json.dump(self.biography_versions, f, ensure_ascii=False, indent=2)
        
        # Save evaluation
        evaluation_file = file_manager.save_evaluation(
            person_id=person_id,
            quality_result=self.quality_result,
            hero_journey_result=self.hero_journey_result
        )
        
        print(f"\n💾 结果已保存:")
        print(f"   - 访谈: {interview_file}")
        print(f"   - 自传: {biography_file}")
        print(f"   - 所有版本: {versions_file}")
        print(f"   - 评估: {evaluation_file}")
    
    async def run(self):
        """Run smart interactive session with coordinator control."""
        try:
            self.display_header()
            
            print(f"\n🤖 当前AI模型: {settings.default_model}")
            print(f"🧠 使用智能协调者动态管理流程")
            
            ready = input("\n🚀 准备开始吗？(y/n): ").lower()
            if ready != 'y':
                print("👋 期待下次为您服务！")
                return
            
            # Main loop controlled by coordinator
            max_iterations = 50  # Safety limit
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Coordinator decides next action
                self.display_agent_action("Coordinator", f"决策下一步行动 (迭代{iteration})")
                decision = await self.coordinator_decide_next_action()
                self.display_coordinator_decision(decision)
                
                action = decision.get("next_action", "complete")
                reasoning = decision.get("reasoning", "无")
                
                # Record action in history
                self.action_history.append((iteration, action, reasoning))
                
                # Execute action
                if action == "continue_interview":
                    self.display_phase("interview", "继续访谈")
                    question, answer = await self.conduct_interview_round()
                    
                    if answer.lower() in ['quit', '结束', 'end']:
                        print("\n✅ 用户请求结束访谈")
                        continue
                
                elif action == "end_interview":
                    self.display_phase("interview", "访谈结束")
                    print(f"✅ 访谈完成，共{len(self.interview_dialogue)//2}轮对话")
                    # Soft phase update - Coordinator can still make other decisions
                    if self.current_phase == "interview":
                        self.current_phase = "post_interview"
                
                elif action == "extract_events":
                    await self.extract_events()
                    # Don't force phase - let Coordinator decide
                
                elif action == "research_history":
                    await self.research_history()
                    # Don't force phase - let Coordinator decide
                
                elif action == "write_biography":
                    await self.write_biography()
                    # Don't force phase - let Coordinator decide
                
                elif action == "evaluate_quality":
                    await self.evaluate_quality()
                    # Don't force phase - let Coordinator decide
                
                elif action == "refine_biography":
                    await self.refine_biography()
                    # Re-evaluate after refinement
                    await self.evaluate_quality()
                
                elif action == "complete":
                    self.display_phase("completed", "流程完成！")
                    break
                
                else:
                    print(f"⚠️ 未知行动: {action}")
                    break
                
                # Small delay
                await asyncio.sleep(0.5)
            
            # Save results
            await self.save_results()
            
            # Final display
            print("\n" + "=" * 80)
            print("📖 最终自传:")
            print("=" * 80)
            print(self.biography)
            print("=" * 80)
            
            print(f"\n🎉 感谢使用SAGA系统！")
            print(f"📊 共生成了{len(self.biography_versions)}个版本")
            
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断")
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
            import traceback
            traceback.print_exc()


async def start_smart_interactive():
    """Start smart interactive mode."""
    session = SmartInteractiveSession()
    await session.run()


def main():
    """Main entry point."""
    try:
        asyncio.run(start_smart_interactive())
    except KeyboardInterrupt:
        print("\n⏹️ 会话中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

