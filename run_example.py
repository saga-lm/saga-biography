#!/usr/bin/env python3
"""
Example runner for SAGA Biography Generation System.
Demonstrates basic usage with example data.
"""

import asyncio
import sys
import shutil
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def run_example():
    """Run example biography generation."""
    print("🚀 SAGA Biography Generation System - Example Runner")
    print("=" * 60)
    
    # Check if example data exists
    example_data = Path(__file__).parent / "examples" / "example_data.json"
    main_data = Path(__file__).parent / "all_people_timelines.json"
    
    if not main_data.exists() and example_data.exists():
        print("📋 Copying example data for demonstration...")
        shutil.copy(example_data, main_data)
        print("✅ Example data copied successfully")
    
    # Import after path setup
    from src.batch_processor import batch_processor
    from config.settings import settings
    
    print(f"\n🔧 Configuration Status:")
    print(f"Available models: {len(settings.get_available_models())}")
    print(f"Current model: {settings.default_model}")
    
    try:
        print(f"\n🧪 Running example with person_001...")
        result = await batch_processor.run_single_test("person_001")
        
        if result["status"] == "completed":
            print(f"\n✅ Example completed successfully!")
            print(f"📊 Quality Score: {result.get('quality_score', 0):.1f}/10.0")
            print(f"⏱️ Processing Time: {result.get('processing_duration', 0):.1f} seconds")
            
            if 'hero_journey_score' in result and 'total_score' in result['hero_journey_score']:
                hero_score = result['hero_journey_score']['total_score']
                hero_percentage = result['hero_journey_score'].get('percentage_score', 0)
                print(f"🏆 Hero's Journey: {hero_score}/147 ({hero_percentage:.1f}%)")
            
            print(f"\n📁 Results saved in 'results/' directory")
            print(f"📖 Biography: results/final/")
            print(f"📊 Evaluation: results/evaluations/")
            print(f"🏆 Hero's Journey: results/hero_journey/")
        else:
            print(f"\n❌ Example failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error running example: {e}")
        print(f"\n💡 Please check:")
        print(f"1. .env file exists with valid API keys")
        print(f"2. Required dependencies are installed")
        print(f"3. Internet connection is available")
        
        return False
    
    return True

def main():
    """Main entry point for example runner."""
    try:
        success = asyncio.run(run_example())
        if success:
            print(f"\n🎉 Example completed! Check the results/ directory for outputs.")
        else:
            print(f"\n⚠️ Example encountered issues. Please check configuration.")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️ Example interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()