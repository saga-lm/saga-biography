"""
Basic tests for SAGA Biography Generation System.
Tests core functionality and configuration.
"""

import unittest
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestConfiguration(unittest.TestCase):
    """Test configuration management."""
    
    def test_settings_import(self):
        """Test that settings can be imported."""
        try:
            from config.settings import settings
            self.assertIsNotNone(settings)
        except Exception as e:
            self.fail(f"Failed to import settings: {e}")
    
    def test_model_configs_structure(self):
        """Test model configuration structure."""
        from config.settings import settings
        
        model_configs = settings.model_configs
        self.assertIsInstance(model_configs, dict)
        
        # Test that each model config has required fields
        for model_name, config in model_configs.items():
            self.assertIsInstance(model_name, str)
            self.assertIsInstance(config, dict)
            self.assertIn('type', config)
            self.assertIn('model', config)
            self.assertIn('api_key', config)

class TestFileManager(unittest.TestCase):
    """Test file management functionality."""
    
    def test_file_manager_import(self):
        """Test that file manager can be imported."""
        try:
            from src.utils.file_manager import file_manager
            self.assertIsNotNone(file_manager)
        except Exception as e:
            self.fail(f"Failed to import file_manager: {e}")
    
    def test_directory_creation(self):
        """Test that required directories are created."""
        from src.utils.file_manager import file_manager
        
        # Check that base directories exist
        self.assertTrue(file_manager.results_dir.exists())
        self.assertTrue((file_manager.results_dir / "interviews").exists())
        self.assertTrue((file_manager.results_dir / "biographies").exists())
        self.assertTrue((file_manager.results_dir / "evaluations").exists())

class TestAgents(unittest.TestCase):
    """Test agent imports and basic functionality."""
    
    def test_coordinator_import(self):
        """Test coordinator agent import."""
        try:
            from src.agents.coordinator import biography_critic
            self.assertIsNotNone(biography_critic)
        except Exception as e:
            self.fail(f"Failed to import coordinator: {e}")
    
    def test_writer_agent_import(self):
        """Test writer agent import."""
        try:
            from src.agents.writer_agent import biography_manager
            self.assertIsNotNone(biography_manager)
        except Exception as e:
            self.fail(f"Failed to import writer agent: {e}")

class TestTools(unittest.TestCase):
    """Test tool imports and basic functionality."""
    
    def test_search_tools_import(self):
        """Test search tools import."""
        try:
            from src.tools.search import search_tool
            self.assertIsNotNone(search_tool)
        except Exception as e:
            self.fail(f"Failed to import search tools: {e}")
    
    def test_quality_evaluator_import(self):
        """Test quality evaluator import."""
        try:
            from src.tools.quality_evaluator import quality_critic
            self.assertIsNotNone(quality_critic)
        except Exception as e:
            self.fail(f"Failed to import quality evaluator: {e}")

class TestBatchProcessor(unittest.TestCase):
    """Test batch processor functionality."""
    
    def test_batch_processor_import(self):
        """Test batch processor import."""
        try:
            from src.batch_processor import batch_processor
            self.assertIsNotNone(batch_processor)
            self.assertIsInstance(batch_processor.max_workers, int)
            self.assertGreater(batch_processor.max_workers, 0)
        except Exception as e:
            self.fail(f"Failed to import batch processor: {e}")

class TestDataStructures(unittest.TestCase):
    """Test data structure handling."""
    
    def test_json_serialization(self):
        """Test JSON serialization utility."""
        from src.utils.file_manager import file_manager
        
        # Test with simple data
        test_data = {"name": "test", "value": 123}
        result = file_manager._make_json_serializable(test_data)
        self.assertEqual(result, test_data)
        
        # Test with complex data (object with __dict__)
        class TestObj:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = 42
        
        test_obj = TestObj()
        result = file_manager._make_json_serializable(test_obj)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["attr1"], "value1")
        self.assertEqual(result["attr2"], 42)

def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    run_tests()