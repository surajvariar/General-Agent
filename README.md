# General-Agent

An AI-powered research agent that leverages Ollama-supported models to conduct thorough research and generate polished reports. Built with deep agentic capabilities and real-time internet search functionality.

**🌐 Live Demo:** [general-agent.streamlit.app](https://general-agent.streamlit.app/)

---

## 📋 Overview

General-Agent is a conversational research agent that:
- Connects to any Ollama-supported LLM model
- Conducts web searches using the Tavily API
- Supports deep agentic workflows with tool calling
- Provides a Streamlit-based chat interface
- Streams real-time thinking and tool execution results

---

## 📦 Dependencies

The project requires Python 3.13 or higher and the following packages:

| Package | Version | Purpose |
|---------|---------|---------|
| `deepagents` | ≥0.4.4 | Deep agentic framework for multi-level agent orchestration |
| `dotenv` | ≥0.9.9 | Environment variable management |
| `langchain-ollama` | ≥1.0.1 | LangChain integration with Ollama |
| `streamlit` | ≥1.54.0 | Web UI framework for chat interface |
| `tavily-python` | ≥0.7.22 | Internet search API client |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** installed on your system
- **Ollama Setup:** Choose one option:
  - **Ollama Cloud (Default):** Current implementation uses Ollama Cloud at `https://ollama.com`
    - Get API key from [ollama.com](https://ollama.com)
  - **Local Ollama:** To use local Ollama instead, see [Local Setup](#local-ollama-setup) section below
- **API Keys:**
  - `TAVILY_API_KEY` - Get from [tavily.com](https://tavily.com)
  - `OLLAMA_API_KEY` - Required for Ollama Cloud (get from [ollama.com](https://ollama.com))

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd General-Agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```
   Or install manually:
   ```bash
   pip install deepagents>=0.4.4 dotenv>=0.9.9 langchain-ollama>=1.0.1 streamlit>=1.54.0 tavily-python>=0.7.22
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   OLLAMA_API_KEY=your_ollama_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

### Running with Ollama Cloud (Default)

1. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Access the app:**
   Open your browser and navigate to `http://localhost:8501`

### Local Ollama Setup

To use local Ollama instead of Ollama Cloud:

1. **Install and start Ollama locally:**
   - Download from [ollama.com](https://ollama.com)
   - Start the server: `ollama serve`

2. **Update the endpoint in `agent/deep_agent.py`:**
   Change the `OLLAMA_URL` from:
   ```python
   self.OLLAMA_URL="https://ollama.com"
   ```
   To:
   ```python
   self.OLLAMA_URL="http://localhost:11434"
   ```

3. **Remove OLLAMA_API_KEY from `.env`** (not needed for local setup)

4. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

---

## 📂 Project Structure

```
General-Agent/
├── app.py                 # Main Streamlit chat interface
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # Documentation
├── agent/
│   ├── deep_agent.py      # Agent configuration and model initialization
│   ├── tools.py           # Tool definitions (internet_search)
└── utils/
    ├── util.py            # Utility functions (model fetching)
```

### Key Files

- **app.py** - Streamlit application with chat interface, model selection, and real-time response streaming
- **agent/deep_agent.py** - Creates and configures the deep agent with LLM and tools
- **agent/tools.py** - Implements `internet_search` tool using Tavily API
- **utils/util.py** - Fetches available Ollama models from the public registry

---

## 💬 Usage

1. **Select a Model:** Choose from available Ollama models in the sidebar dropdown
2. **Enter a Query:** Type your research question in the chat input
3. **View Results:** Watch real-time streaming of agent thinking, tool calls, and final responses
4. **Clear Chat:** Use the "Clear chat" button to reset conversation history

### Example Queries

- "Research the latest developments in AI and summarize them"
- "What are the best practices for machine learning model deployment?"
- "Find information about renewable energy trends in 2025"

---

## 🔧 Features

- **Model Selection:** Switch between any available Ollama model
- **Real-time Streaming:** View agent thinking process and tool execution
- **Web Search Integration:** Use Tavily API for current information
- **Deep Agent Support:** Multi-level agentic workflows with tool orchestration
- **Chat History:** Maintain conversation context throughout session
- **Expandable Details:** Inspect tool calls and search results

---

## 🌐 Live Deployment

The application is deployed and available at: [general-agent.streamlit.app](https://general-agent.streamlit.app/)

---

## 🛠️ Development

To extend the agent with new tools:

1. Define the tool function in `agent/tools.py`
2. Add it to the tools list in `agent/deep_agent.py` `config_agent()` method
3. Update system instructions in `deep_agent.py` to describe the tool

---

## 📝 License

This project is for learning and development purposes.
