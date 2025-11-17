"""
Batch processing for SAGA Biography Generation System.
Handles batch biography generation with parallel processing support.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.agents.coordinator import biography_critic
from src.utils.file_manager import file_manager
from src.utils.logger import agent_logger, performance_logger
from config.settings import settings

class BiographyBatchProcessor:
    """Batch biography generation processor with parallel processing support."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize batch processor."""
        self.max_workers = max_workers or settings.max_concurrent_workers
        self.batch_results = []
        
        # Set up experiment limit (for research purposes)
        self.EXPERIMENT_LIMIT = 200
        
        print(f"🚀 Batch processor initialized with {self.max_workers} max workers")
        print(f"🔬 Experiment limit: {self.EXPERIMENT_LIMIT} people")
    
    async def process_single_person(self, person_id: str, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process biography generation for a single person."""
        performance_logger.start_timer(f"person_{person_id}")
        
        try:
            result = await biography_critic.process_person_biography(person_data, person_id)
            
            duration = performance_logger.end_timer(f"person_{person_id}")
            result["processing_duration"] = duration
            
            agent_logger.log_stage_completion(
                f"person_{person_id}", 
                duration, 
                "success" if result["status"] == "completed" else "failed",
                f"Quality: {result.get('quality_score', 0):.1f}/10.0"
            )
            
            return result
            
        except Exception as e:
            duration = performance_logger.end_timer(f"person_{person_id}")
            agent_logger.log_error("batch_processor", str(e), f"Processing person {person_id}")
            
            return {
                "person_id": person_id,
                "status": "failed",
                "error": str(e),
                "processing_duration": duration
            }
    
    async def run_batch_processing(self, person_ids: List[str] = None, max_people: int = 5) -> Dict[str, Any]:
        """Run batch biography generation processing."""
        performance_logger.start_timer("batch_processing")
        
        print("🚀 Starting batch biography generation test")
        agent_logger.log_decision("batch_processor", "Starting batch processing", f"Max people: {max_people}")
        
        # Load data
        try:
            data = file_manager.load_people_data()
        except FileNotFoundError:
            # Try to load from parent directory (for compatibility)
            parent_data_path = Path(__file__).parent.parent.parent / "all_people_timelines.json"
            if parent_data_path.exists():
                with open(parent_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                raise FileNotFoundError("all_people_timelines.json not found")
        
        total_people = len(data["people"])
        print(f"📊 Total data: {total_people} people")
        
        # Determine people IDs to process
        if person_ids is None:
            # 🔬 Experiment limitation: Only use first 200 people dataset
            max_people = min(max_people, self.EXPERIMENT_LIMIT)
            
            all_person_ids = list(data["people"].keys())
            person_ids = all_person_ids[:max_people]  # Limit within experiment dataset
            
            print(f"🔬 Experiment dataset: Limited to first {self.EXPERIMENT_LIMIT} people")
            print(f"🎯 Current processing: {len(person_ids)} people (ID range: {person_ids[0]} - {person_ids[-1]})")
            
            if max_people > self.EXPERIMENT_LIMIT:
                print(f"⚠️ Note: Requested {max_people} people, but experiment limited to {self.EXPERIMENT_LIMIT} people")
        else:
            print(f"📋 Using specified {len(person_ids)} user IDs")
        
        print(f"📋 Planning to process {len(person_ids)} users")
        
        batch_start_time = datetime.now()
        batch_result = {
            "batch_id": f"batch_{batch_start_time.strftime('%Y%m%d_%H%M%S')}",
            "start_time": batch_start_time.isoformat(),
            "total_people": len(person_ids),
            "completed": 0,
            "failed": 0,
            "results": [],
            "summary": {},
            "processing_mode": "sequential"  # Can be extended to "parallel" in future
        }
        
        agent_logger.log_agent_action("batch_processor", "Batch processing started", 
                                    f"Processing {len(person_ids)} people")
        
        # Process each user (sequential for now, can be made parallel)
        for i, person_id in enumerate(person_ids, 1):
            print(f"\n📊 Progress: {i}/{len(person_ids)}")
            
            person_data = data["people"].get(person_id)
            if not person_data:
                print(f"⚠️ Person {person_id} not found in data")
                continue
            
            result = await self.process_single_person(person_id, person_data)
            batch_result["results"].append(result)
            
            if result["status"] == "completed":
                batch_result["completed"] += 1
            else:
                batch_result["failed"] += 1
        
        # Complete batch processing
        batch_end_time = datetime.now()
        batch_duration = performance_logger.end_timer("batch_processing")
        
        batch_result["end_time"] = batch_end_time.isoformat()
        batch_result["duration_seconds"] = batch_duration
        batch_result["duration"] = str(batch_end_time - batch_start_time)
        
        # Generate statistical summary
        quality_scores = [r["quality_score"] for r in batch_result["results"] if r["status"] == "completed" and "quality_score" in r]
        if quality_scores:
            batch_result["summary"] = {
                "avg_quality_score": sum(quality_scores) / len(quality_scores),
                "max_quality_score": max(quality_scores),
                "min_quality_score": min(quality_scores),
                "high_quality_count": len([s for s in quality_scores if s >= 9.0]),
                "performance_metrics": performance_logger.get_performance_summary()
            }
        
        # Save batch results
        batch_file = file_manager.save_batch_result(batch_result)
        
        print(f"\n🎉 Batch processing completed!")
        print(f"✅ Success: {batch_result['completed']}")
        print(f"❌ Failed: {batch_result['failed']}")
        if quality_scores:
            print(f"📊 Average quality score: {batch_result['summary']['avg_quality_score']:.2f}")
            print(f"🏆 High quality works(≥9.0): {batch_result['summary']['high_quality_count']}")
        print(f"⏱️ Total duration: {batch_duration:.1f} seconds")
        print(f"📁 Results saved in: results/")
        
        agent_logger.log_stage_completion("batch_processing", batch_duration, "success", 
                                        f"Processed {batch_result['completed']}/{batch_result['total_people']} people")
        
        # Save session summary
        agent_logger.save_session_summary()
        
        return batch_result
    
    async def run_single_test(self, person_id: str) -> Dict[str, Any]:
        """Run single person test."""
        print(f"🧪 Running single person test: {person_id}")
        
        try:
            data = file_manager.load_people_data()
        except FileNotFoundError:
            # Try to load from parent directory (for compatibility)
            parent_data_path = Path(__file__).parent.parent.parent / "all_people_timelines.json"
            if parent_data_path.exists():
                with open(parent_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                raise FileNotFoundError("all_people_timelines.json not found")
        
        person_data = data["people"].get(person_id)
        if not person_data:
            raise ValueError(f"Person {person_id} not found in data")
        
        result = await self.process_single_person(person_id, person_data)
        
        print(f"🧪 Single test completed")
        print(f"📊 Status: {result['status']}")
        if result["status"] == "completed":
            print(f"📊 Quality score: {result.get('quality_score', 0):.1f}/10.0")
            if 'hero_journey_score' in result and 'total_score' in result['hero_journey_score']:
                hero_score = result['hero_journey_score']['total_score']
                hero_percentage = result['hero_journey_score'].get('percentage_score', 0)
                print(f"🏆 Hero's Journey: {hero_score}/147 ({hero_percentage:.1f}%)")
        
        return result

# Global batch processor instance
batch_processor = BiographyBatchProcessor()