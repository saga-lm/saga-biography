"""
File management utilities for SAGA Biography Generation System.
Handles file operations, directory management, and result storage.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class FileManager:
    """Manages file operations and result storage."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize file manager with base directory."""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.data_dir = self.base_dir / "data"
        
        # Create directory structure
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directory structure."""
        directories = [
            self.results_dir,
            self.results_dir / "interviews",
            self.results_dir / "biographies",
            self.results_dir / "evaluations",
            self.results_dir / "hero_journey",
            self.results_dir / "final",
            self.results_dir / "batch_results",
            self.data_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_interview(self, person_id: str, person_name: str, interview_content: str) -> Path:
        """Save interview content to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{person_id}_{person_name}_{timestamp}.txt"
        file_path = self.results_dir / "interviews" / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(interview_content)
        
        print(f"📁 Interview saved: {file_path}")
        return file_path
    
    def save_biography(self, person_id: str, person_name: str, biography: str, version: str = "1") -> Path:
        """Save biography to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"biography_{person_id}_{person_name}_v{version}_{timestamp}.txt"
        file_path = self.results_dir / "biographies" / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(biography)
        
        print(f"📁 Biography saved: {file_path}")
        return file_path
    
    def save_evaluation(self, person_id: str, person_name: str, evaluation_result: Dict[str, Any]) -> Path:
        """Save quality evaluation to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{person_id}_{person_name}_{timestamp}.json"
        file_path = self.results_dir / "evaluations" / filename
        
        # Ensure JSON serializable
        serializable_result = self._make_json_serializable(evaluation_result)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Evaluation saved: {file_path}")
        return file_path
    
    def save_hero_journey(self, person_id: str, person_name: str, hero_result: Dict[str, Any]) -> Path:
        """Save Hero's Journey evaluation to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hero_journey_{person_id}_{person_name}_{timestamp}.json"
        file_path = self.results_dir / "hero_journey" / filename
        
        # Ensure JSON serializable
        serializable_result = self._make_json_serializable(hero_result)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Hero's Journey evaluation saved: {file_path}")
        return file_path
    
    def save_final_biography(self, person_id: str, person_name: str, biography: str) -> Path:
        """Save final biography to final directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_biography_{person_id}_{person_name}_{timestamp}.txt"
        file_path = self.results_dir / "final" / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(biography)
        
        print(f"📁 Final biography saved: {file_path}")
        return file_path
    
    def get_batch_result_path(self, batch_id: str) -> Path:
        """Get batch result file path."""
        filename = f"batch_result_{batch_id}.json"
        return self.results_dir / "batch_results" / filename
    
    def save_batch_result(self, batch_result: Dict[str, Any]) -> Path:
        """Save batch processing results."""
        batch_id = batch_result.get('batch_id', f'batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        file_path = self.get_batch_result_path(batch_id)
        
        # Ensure JSON serializable
        serializable_result = self._make_json_serializable(batch_result)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Batch result saved: {file_path}")
        return file_path
    
    def load_people_data(self, data_file: str = "all_people_timelines.json") -> Dict[str, Any]:
        """Load people data from JSON file."""
        data_path = self.base_dir / data_file
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert object to JSON serializable format."""
        if hasattr(obj, '__dict__'):
            # If it's an object, convert to dictionary
            result = {}
            for key, value in obj.__dict__.items():
                try:
                    json.dumps(value)  # Test if serializable
                    result[key] = value
                except (TypeError, ValueError):
                    result[key] = str(value)  # Convert non-serializable to string
            return result
        elif isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self._make_json_serializable(value)
            return result
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            try:
                json.dumps(obj)  # Test if serializable
                return obj
            except (TypeError, ValueError):
                return str(obj)  # Convert non-serializable to string
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up files older than specified days."""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        for directory in [self.results_dir / "interviews", self.results_dir / "biographies", 
                         self.results_dir / "evaluations"]:
            for file_path in directory.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    print(f"🗑️ Cleaned up old file: {file_path}")

# Global file manager instance
file_manager = FileManager()