"""
Session Manager for SAGA Biography Generation System.
Handles user session creation, storage, and recovery.
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio


class SessionManager:
    """Manages user sessions with persistence and recovery."""
    
    def __init__(self, storage_path: str = "sessions"):
        """
        Initialize session manager.
        
        Args:
            storage_path: Directory to store session data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_sessions = {}  # session_id -> session_data
        
    def generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(
            f"{timestamp}_{os.urandom(8)}".encode()
        ).hexdigest()[:8]
        return f"user_{timestamp}_{random_hash}"
    
    def create_session(self) -> tuple[str, Dict[str, Any]]:
        """
        Create new session.
        
        Returns:
            Tuple of (session_id, session_data)
        """
        session_id = self.generate_session_id()
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "interview_dialogue": [],
            "interview_content": "",
            "biography": "",
            "biography_versions": [],
            "quality_result": {},
            "hero_journey_result": {},
            "historical_context": {},
            "extracted_anchors": None,
            "current_phase": "starting",
            "conversation_history": "",
            "action_history": [],
            "logs": []
        }
        
        self.active_sessions[session_id] = session_data
        self.save_session(session_id)
        
        return session_id, session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from disk
        if self.load_session(session_id):
            return self.active_sessions[session_id]
        
        return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """
        Update session data.
        
        Args:
            session_id: Session ID
            updates: Dictionary of fields to update
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update(updates)
            self.active_sessions[session_id]["last_active"] = datetime.now().isoformat()
            self.save_session(session_id)
    
    def save_session(self, session_id: str) -> bool:
        """
        Save session to disk.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[session_id]
            file_path = self.storage_path / f"{session_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> bool:
        """
        Load session from disk.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            file_path = self.storage_path / f"{session_id}.json"
            
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.active_sessions[session_id] = session_data
            return True
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> list[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session summaries
        """
        sessions = []
        
        for file_path in self.storage_path.glob("user_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                summary = {
                    "session_id": session_data["session_id"],
                    "created_at": session_data["created_at"],
                    "last_active": session_data["last_active"],
                    "current_phase": session_data.get("current_phase", "unknown"),
                    "dialogue_count": len(session_data.get("interview_dialogue", [])),
                    "biography_versions": len(session_data.get("biography_versions", [])),
                    "biography_length": len(session_data.get("biography", ""))
                }
                sessions.append(summary)
            except Exception as e:
                print(f"Error reading session file {file_path}: {e}")
        
        # Sort by last active, most recent first
        sessions.sort(key=lambda x: x["last_active"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Delete file
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def add_log(self, session_id: str, level: str, message: str):
        """
        Add log entry to session.
        
        Args:
            session_id: Session ID
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
            message: Log message
        """
        if session_id in self.active_sessions:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "level": level,
                "message": message
            }
            
            self.active_sessions[session_id]["logs"].append(log_entry)
            
            # Keep only last 1000 logs
            if len(self.active_sessions[session_id]["logs"]) > 1000:
                self.active_sessions[session_id]["logs"] = \
                    self.active_sessions[session_id]["logs"][-1000:]
    
    def get_logs(self, session_id: str, format_colored: bool = True) -> str:
        """
        Get formatted logs.
        
        Args:
            session_id: Session ID
            format_colored: Whether to add color markers
            
        Returns:
            Formatted log string
        """
        if session_id not in self.active_sessions:
            return ""
        
        logs = self.active_sessions[session_id].get("logs", [])
        
        if not logs:
            return "暂无日志"
        
        formatted_logs = []
        for log in logs:
            timestamp = log["timestamp"]
            level = log["level"]
            message = log["message"]
            
            if format_colored:
                # Add ANSI color codes (will be stripped in Gradio)
                # Just use markers for now
                level_marker = {
                    "INFO": "ℹ️",
                    "SUCCESS": "✅",
                    "WARNING": "⚠️",
                    "ERROR": "❌"
                }.get(level, "•")
                
                formatted_logs.append(f"[{timestamp}] {level_marker} {message}")
            else:
                formatted_logs.append(f"[{timestamp}] [{level}] {message}")
        
        return "\n".join(formatted_logs)
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export complete session data for download.
        
        Args:
            session_id: Session ID
            
        Returns:
            Complete session data
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        export_data = {
            "metadata": {
                "session_id": session_data["session_id"],
                "created_at": session_data["created_at"],
                "last_active": session_data["last_active"],
                "export_time": datetime.now().isoformat()
            },
            "interview": {
                "dialogue": session_data.get("interview_dialogue", []),
                "content": session_data.get("interview_content", "")
            },
            "biography": {
                "final_version": session_data.get("biography", ""),
                "all_versions": session_data.get("biography_versions", [])
            },
            "evaluation": {
                "quality": session_data.get("quality_result", {}),
                "hero_journey": session_data.get("hero_journey_result", {})
            },
            "research": {
                "extracted_anchors": session_data.get("extracted_anchors", None),
                "historical_context": session_data.get("historical_context", {})
            },
            "workflow": {
                "current_phase": session_data.get("current_phase", ""),
                "action_history": session_data.get("action_history", [])
            },
            "logs": session_data.get("logs", [])
        }
        
        return export_data
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Delete sessions older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta
        
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file_path in self.storage_path.glob("user_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                last_active = datetime.fromisoformat(session_data["last_active"])
                
                if last_active < cutoff_date:
                    session_id = session_data["session_id"]
                    if self.delete_session(session_id):
                        deleted_count += 1
            except Exception as e:
                print(f"Error during cleanup of {file_path}: {e}")
        
        return deleted_count


# Global instance
session_manager = SessionManager()

