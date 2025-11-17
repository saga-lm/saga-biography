"""
Logging utilities for SAGA Biography Generation System.
Provides structured logging for agents, decisions, and actions.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class AgentLogger:
    """Logger for agent actions and decisions."""
    
    def __init__(self, log_dir: Path = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "results" / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"agent_log_{self.session_id}.json"
        self.log_entries = []
    
    def log_agent_action(self, agent_name: str, action: str, details: str = ""):
        """Log an agent action."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "action",
            "agent": agent_name,
            "action": action,
            "details": details,
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        self._write_log_entry(entry)
        
        # Also print to console for immediate feedback
        print(f"🤖 [{agent_name}] {action}: {details}")
    
    def log_decision(self, agent_name: str, decision: str, reasoning: str = ""):
        """Log a decision made by an agent."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "decision",
            "agent": agent_name,
            "decision": decision,
            "reasoning": reasoning,
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        self._write_log_entry(entry)
        
        # Also print to console for immediate feedback
        print(f"🧠 [{agent_name}] Decision: {decision} | Reason: {reasoning}")
    
    def log_error(self, agent_name: str, error: str, context: str = ""):
        """Log an error."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "agent": agent_name,
            "error": error,
            "context": context,
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        self._write_log_entry(entry)
        
        # Also print to console for immediate feedback
        print(f"❌ [{agent_name}] Error: {error} | Context: {context}")
    
    def log_stage_completion(self, stage_name: str, duration: float, status: str = "success", details: str = ""):
        """Log stage completion."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "stage_completion",
            "stage": stage_name,
            "duration_seconds": duration,
            "status": status,
            "details": details,
            "session_id": self.session_id
        }
        
        self.log_entries.append(entry)
        self._write_log_entry(entry)
        
        # Also print to console for immediate feedback
        status_emoji = "✅" if status == "success" else "❌"
        print(f"{status_emoji} Stage [{stage_name}] completed in {duration:.2f}s: {details}")
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write a log entry to file."""
        try:
            # Append to log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ Failed to write log entry: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        actions = [e for e in self.log_entries if e["type"] == "action"]
        decisions = [e for e in self.log_entries if e["type"] == "decision"]
        errors = [e for e in self.log_entries if e["type"] == "error"]
        stages = [e for e in self.log_entries if e["type"] == "stage_completion"]
        
        return {
            "session_id": self.session_id,
            "total_entries": len(self.log_entries),
            "actions_count": len(actions),
            "decisions_count": len(decisions),
            "errors_count": len(errors),
            "stages_count": len(stages),
            "agents_involved": list(set([e.get("agent", "") for e in self.log_entries if e.get("agent")])),
            "session_duration": self._calculate_session_duration(),
            "log_file": str(self.log_file)
        }
    
    def _calculate_session_duration(self) -> float:
        """Calculate session duration in seconds."""
        if not self.log_entries:
            return 0.0
        
        first_entry = datetime.fromisoformat(self.log_entries[0]["timestamp"])
        last_entry = datetime.fromisoformat(self.log_entries[-1]["timestamp"])
        
        return (last_entry - first_entry).total_seconds()
    
    def save_session_summary(self) -> Path:
        """Save session summary to file."""
        summary = self.get_session_summary()
        summary_file = self.log_dir / f"session_summary_{self.session_id}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Session summary saved: {summary_file}")
        return summary_file

class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation_name: str):
        """Start timing an operation."""
        self.start_times[operation_name] = datetime.now()
    
    def end_timer(self, operation_name: str) -> float:
        """End timing an operation and return duration."""
        if operation_name not in self.start_times:
            print(f"⚠️ No start time found for operation: {operation_name}")
            return 0.0
        
        start_time = self.start_times[operation_name]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        
        self.metrics[operation_name].append({
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration
        })
        
        # Clean up start time
        del self.start_times[operation_name]
        
        return duration
    
    def get_average_duration(self, operation_name: str) -> float:
        """Get average duration for an operation."""
        if operation_name not in self.metrics:
            return 0.0
        
        durations = [m["duration_seconds"] for m in self.metrics[operation_name]]
        return sum(durations) / len(durations) if durations else 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        for operation, measurements in self.metrics.items():
            durations = [m["duration_seconds"] for m in measurements]
            summary[operation] = {
                "count": len(measurements),
                "total_duration": sum(durations),
                "average_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations)
            }
        
        return summary

# Global logger instances
agent_logger = AgentLogger()
performance_logger = PerformanceLogger()