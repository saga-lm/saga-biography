"""
Setup script for SAGA Biography Generation System.
Handles installation and configuration.
"""

import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    """Set up environment and create necessary files."""
    print("🔧 Setting up SAGA Biography Generation System...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("config/env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📄 Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created. Please edit it with your API keys.")
    elif env_file.exists():
        print("✅ .env file already exists.")
    else:
        print("⚠️ No .env template found. Creating basic template...")
        create_basic_env_file()
    
    # Create data directory structure
    print("📁 Creating directory structure...")
    directories = [
        "results",
        "results/interviews",
        "results/biographies", 
        "results/evaluations",
        "results/hero_journey",
        "results/final",
        "results/batch_results",
        "results/logs",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created.")
    
    # Copy example data if no main data exists
    example_data = Path("examples/example_data.json")
    main_data = Path("all_people_timelines.json")
    
    if not main_data.exists() and example_data.exists():
        print("📋 Copying example data for testing...")
        shutil.copy(example_data, main_data)
        print("✅ Example data copied. You can now run tests.")
    
    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run setup check: python main.py setup")
    print("4. Try example: python run_example.py")

def create_basic_env_file():
    """Create a basic .env file template."""
    env_content = """# SAGA Biography Generation System - Environment Configuration
# Fill in your API keys below

# Azure OpenAI Configuration (Required if using Azure models)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# OpenRouter API Configuration (Required if using Claude/Gemini/DeepSeek)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Search API Configuration (Required)
TAVILY_API_KEY=your_tavily_search_api_key_here

# Application Settings
DEFAULT_MODEL=openai-gpt4
MAX_CONCURRENT_WORKERS=10
DEFAULT_PEOPLE_COUNT=100
"""
    
    with open(".env", "w") as f:
        f.write(env_content)

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "autogen-agentchat",
        "tavily-python",
        "requests",
        "PyPDF2"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed.")
        return True

def main():
    """Main setup function."""
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Check dependencies only
        return check_dependencies()
    else:
        # Full setup
        setup_environment()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)