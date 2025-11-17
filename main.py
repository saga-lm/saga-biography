"""
Main entry point for SAGA Biography Generation System.
Provides command-line interface for various operations.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.batch_processor import batch_processor
from src.models.client_manager import model_manager
from config.settings import settings

# Import interactive modes
try:
    from interactive import start_interactive_mode
    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False

try:
    from interactive_smart import start_smart_interactive
    SMART_INTERACTIVE_AVAILABLE = True
except ImportError:
    SMART_INTERACTIVE_AVAILABLE = False

def setup_environment():
    """Setup environment and check configuration."""
    print("🔧 Setting up SAGA Biography Generation System...")
    
    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️ .env file not found. Please create one based on config/env.example")
        print("📄 Copy config/env.example to .env and fill in your API keys")
        return False
    
    try:
        # Test model availability
        available_models = settings.get_available_models()
        if not available_models:
            print("❌ No models available. Please check your API key configuration.")
            return False
        
        print(f"✅ Configuration valid. Available models: {', '.join(available_models)}")
        print(f"🤖 Current model: {model_manager.current_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def run_single_test(person_id: str):
    """Run single person biography generation test."""
    print(f"🧪 Running single test for person: {person_id}")
    
    try:
        result = await batch_processor.run_single_test(person_id)
        
        if result["status"] == "completed":
            print(f"\n✅ Test completed successfully!")
            print(f"📊 Quality Score: {result.get('quality_score', 0):.1f}/10.0")
            print(f"⏱️ Processing Time: {result.get('processing_duration', 0):.1f} seconds")
        else:
            print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error running single test: {e}")

async def run_batch_test(max_people: int, person_ids: list = None):
    """Run batch biography generation test."""
    print(f"🚀 Running batch test for {max_people} people")
    
    try:
        result = await batch_processor.run_batch_processing(person_ids, max_people)
        
        print(f"\n📊 Batch Test Summary:")
        print(f"✅ Completed: {result['completed']}/{result['total_people']}")
        print(f"❌ Failed: {result['failed']}/{result['total_people']}")
        print(f"📈 Success Rate: {(result['completed']/result['total_people']*100):.1f}%")
        
        if 'summary' in result and 'avg_quality_score' in result['summary']:
            print(f"🎯 Average Quality: {result['summary']['avg_quality_score']:.1f}/10.0")
            print(f"🏆 High Quality (≥9.0): {result['summary']['high_quality_count']}")
        
        print(f"⏱️ Total Duration: {result.get('duration_seconds', 0):.1f} seconds")
        
    except Exception as e:
        print(f"❌ Error running batch test: {e}")

def list_models():
    """List available models."""
    model_manager.list_models()

def set_model(model_name: str):
    """Set the current model."""
    success = model_manager.set_model(model_name)
    if not success:
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SAGA Biography Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Smart Interactive mode - AI coordinator controls workflow (推荐)
  python main.py smart-interactive
  
  # Interactive mode - fixed pipeline
  python main.py interactive
  
  # Run single person test
  python main.py single --person-id person_001
  
  # Run batch test with 5 people
  python main.py batch --max-people 5
  
  # Run batch test with specific people
  python main.py batch --person-ids person_001,person_002,person_003
  
  # List available models
  python main.py models --list
  
  # Set current model
  python main.py models --set openai-gpt4
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Smart Interactive mode command (recommended)
    smart_interactive_parser = subparsers.add_parser('smart-interactive', help='Smart interactive mode with AI coordinator (推荐)')
    
    # Interactive mode command (fixed pipeline)
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode with fixed pipeline')
    
    # Single test command
    single_parser = subparsers.add_parser('single', help='Run single person test')
    single_parser.add_argument('--person-id', required=True, help='Person ID to test')
    
    # Batch test command
    batch_parser = subparsers.add_parser('batch', help='Run batch test')
    batch_group = batch_parser.add_mutually_exclusive_group(required=True)
    batch_group.add_argument('--max-people', type=int, help='Maximum number of people to process')
    batch_group.add_argument('--person-ids', help='Comma-separated list of person IDs')
    
    # Model management command
    model_parser = subparsers.add_parser('models', help='Model management')
    model_group = model_parser.add_mutually_exclusive_group(required=True)
    model_group.add_argument('--list', action='store_true', help='List available models')
    model_group.add_argument('--set', help='Set current model')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup and check configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup command
    if args.command == 'setup':
        success = setup_environment()
        sys.exit(0 if success else 1)
    
    # Check environment for other commands
    if not setup_environment():
        print("❌ Environment setup failed. Run 'python main.py setup' for details.")
        sys.exit(1)
    
    # Handle commands
    if args.command == 'smart-interactive':
        if not SMART_INTERACTIVE_AVAILABLE:
            print("❌ Smart interactive mode not available. Please ensure interactive_smart.py exists.")
            sys.exit(1)
        asyncio.run(start_smart_interactive())
    
    elif args.command == 'interactive':
        if not INTERACTIVE_AVAILABLE:
            print("❌ Interactive mode not available. Please ensure interactive.py exists.")
            sys.exit(1)
        asyncio.run(start_interactive_mode())
    
    elif args.command == 'single':
        asyncio.run(run_single_test(args.person_id))
    
    elif args.command == 'batch':
        if args.person_ids:
            person_ids = [pid.strip() for pid in args.person_ids.split(',')]
            asyncio.run(run_batch_test(len(person_ids), person_ids))
        else:
            asyncio.run(run_batch_test(args.max_people))
    
    elif args.command == 'models':
        if args.list:
            list_models()
        elif args.set:
            set_model(args.set)

if __name__ == "__main__":
    main()