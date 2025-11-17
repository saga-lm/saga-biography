# SAGA

## Project Structure

```
saga_submission/
├── src/                          # Source code
│   ├── agents/                   # AI agents
│   │   ├── coordinator.py        # Main coordination agent
│   │   ├── interview_agent.py    # Interview management
│   │   ├── user_simulation.py    # User simulation
│   │   └── writer_agent.py       # Biography writing
│   ├── tools/                    # Utility tools
│   │   ├── search.py            # Web search and crawling
│   │   ├── history_analyzer.py  # Historical analysis
│   │   └── quality_evaluator.py # Quality assessment
│   ├── models/                   # Model management
│   │   └── client_manager.py    # Model client management
│   ├── utils/                    # Utilities
│   │   ├── file_manager.py      # File operations
│   │   └── logger.py            # Logging system
│   └── batch_processor.py       # Batch processing
├── config/                       # Configuration
│   ├── settings.py              # Settings management
│   └── env.example              # Environment template
├── main.py                      # Main entry point
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Installation

1. **Clone the repository**
   ```bash
   cd saga_submission
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment configuration**
   ```bash
   cp config/env.example .env
   ```

4. **Configure API keys in .env file**
   ```bash
   # Required: At least one model API key
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
   
   # Or OpenRouter for Claude/Gemini/DeepSeek
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   # Required: Search API
   TAVILY_API_KEY=your_tavily_search_api_key_here
   ```

5. **Verify setup**
   ```bash
   python main.py setup
   ```

## Usage

### Command Line Interface

The system provides a comprehensive CLI for various operations:

```bash
# Check system setup and configuration
python main.py setup

# 🧠 Smart Interactive mode - AI Coordinator (推荐)
python main.py smart-interactive

# 🎭 Interactive mode - Fixed pipeline
python main.py interactive

# List available models
python main.py models --list

# Set current model
python main.py models --set openai-gpt4

# Run single person test
python main.py single --person-id person_001

# Run batch test with multiple people
python main.py batch --max-people 10

# Run batch test with specific people
python main.py batch --person-ids person_001,person_002,person_003
```

### Interactive Modes

#### 🧠 Smart Interactive Mode (推荐)

**AI Coordinator dynamically controls the entire workflow:**

```bash
python main.py smart-interactive
# or directly run
python interactive_smart.py
```

**Key Features:**
- 🧠 **AI Coordinator** makes intelligent decisions at each step
- ⚡ **Adaptive interview length** (3-20 rounds based on content quality)
- 🎯 **Dynamic workflow** - extract events, search, and evaluate only when needed
- 🔄 **Automatic refinement** - improves biographies scoring <8/10
- ✅ **Smart completion** - ends when quality standards are met
- 📊 **Version tracking** - saves all biography iterations

**How it works:**
1. Coordinator decides: continue interview or move to next phase
2. Dynamically extracts events and researches history when beneficial
3. Writes biography and evaluates quality
4. Automatically refines if quality <8/10
5. Completes when quality targets achieved

**See detailed documentation:** [SMART_INTERACTIVE.md](SMART_INTERACTIVE.md)

---

#### 🎭 Interactive Mode (Fixed Pipeline)

**Fixed workflow for consistent processing:**

```bash
python main.py interactive
```

**Features:**
- 🎤 Fixed 15-round interview
- 📚 Always extracts events and researches history
- ✍️ Creates one biography version
- 🔍 Single quality evaluation

**Tips for Both Modes:**
- Type naturally as if chatting with a friend
- Share specific details, emotions, and personal reflections
- Type `quit` or `end` to end interview early

### Data Requirements

The system requires a `all_people_timelines.json` file in the root directory with the following structure:

```json
{
  "people": {
    "person_001": {
      "person_info": {
        "name": "John Doe",
        "basic_data": {
          "current_age": 45,
          "gender": "male",
          "birth_year": "1978"
        },
        "personal_background": {
          "personality": {
            "main_trait": "optimistic",
            "behavior": "hardworking"
          },
          "family_details": {
            "economic_status": "middle class",
            "father_job": "teacher",
            "mother_job": "nurse"
          }
        }
      },
      "life_timeline": [
        {
          "age": 18,
          "type": "education",
          "description": "Started university",
          "details": "Enrolled in Computer Science program..."
        }
      ]
    }
  }
}
```

## Output Files

The system generates organized output files in the `results/` directory:

- `interviews/`: Interview transcripts
- `biographies/`: Generated biographies (with versions)
- `evaluations/`: Quality assessment results
- `hero_journey/`: Hero's Journey scale evaluations
- `final/`: Final approved biographies
- `batch_results/`: Batch processing summaries
- `logs/`: System logs and session summaries

## Requirements

### System Requirements
- Python 3.8+
- Internet connection for web search and AI APIs
- Minimum 4GB RAM for batch processing

### API Requirements
- At least one AI model API key (Azure OpenAI or OpenRouter)
- Tavily search API key for historical research
- Optional: crawl4ai for enhanced web content extraction

### Dependencies
See `requirements.txt` for complete list:
- autogen-agentchat: Multi-agent conversation framework
- autogen-ext: Extended model support
- tavily-python: Web search API
- PyPDF2: PDF text extraction
- crawl4ai: Web content crawling (optional)


## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   python main.py setup
   ```
   Verify all required API keys are configured in `.env`

2. **Data File Not Found**
   Ensure `all_people_timelines.json` is in the root directory

3. **Model Errors**
   ```bash
   python main.py models --list
   ```
   Check available models and switch if needed

4. **Memory Issues**
   Reduce batch size or max_workers in configuration

### Logs and Debugging

- Check `results/logs/` for detailed execution logs
- Use `python main.py setup` to verify configuration
- Monitor console output for real-time status

## License

This project is part of AAAI research submission. Please refer to the associated research paper for citation and usage guidelines.

## Support

For technical issues or questions about the system, please refer to the documentation or contact the development team.