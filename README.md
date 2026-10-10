# 🤖 Multi-Agent Research System

An AI-powered research assistant that uses multiple specialized agents to research a topic, gather information from web sources, extract relevant content, generate a structured report, and evaluate the report with critic feedback.

## 🚀 Live Demo

**Try the application here:**  
[Multi-Agent Research System — Live App](https://multi-agent-research-system-mruutv3xcxkcyf9ualxwrc.streamlit.app/)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://multi-agent-research-system-mruutv3xcxkcyf9ualxwrc.streamlit.app/)

## 📌 Project Overview

Researching a topic manually can require visiting multiple websites, collecting information, organizing findings, and reviewing the final output. This project explores how a multi-agent AI workflow can automate these tasks.

The system coordinates specialized AI components to perform research in stages. Each component contributes to the overall workflow, from gathering information to generating a report and reviewing its quality.

The application provides an interactive Streamlit interface where users can enter a research topic and view the generated results.

## ✨ Key Features

- **🔎 Automated Web Search:** Finds relevant information using web-search tools.
- **📄 Content Extraction:** Retrieves and processes content from selected web pages.
- **🧠 AI-Powered Report Generation:** Organizes research findings into a readable report.
- **📝 Critic Agent:** Reviews the generated report and provides feedback.
- **🔗 Multi-Agent Workflow:** Coordinates specialized components across multiple research stages.
- **🖥️ Interactive Web Interface:** Provides a browser-based interface built with Streamlit.
- **🌐 Online Deployment:** Makes the application accessible through a public Streamlit URL.

## ⚙️ How It Works

1. **User Input:** The user enters a research topic.
2. **Search Agent:** Searches for relevant web information.
3. **Reader Agent:** Extracts useful content from selected sources.
4. **Writer Component:** Generates a structured research report using the collected information.
5. **Critic Component:** Evaluates the report and provides feedback.
6. **Results:** The application presents the research output and feedback to the user.

## 🏗️ Project Architecture

```text
User Research Topic
        |
        v
   Search Agent
        |
        v
   Search Results
        |
        v
   Reader Agent
        |
        v
 Extracted Content
        |
        v
   Writer Chain
        |
        v
 Generated Report
        |
        v
   Critic Chain
        |
        v
 Report + Feedback
        |
        v
  Streamlit Interface
```

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| LangChain | LLM integration and agent components |
| OpenAI API | Language-model capabilities, if configured |
| Tavily Search | Web search integration |
| Beautiful Soup | HTML content extraction |
| Requests | HTTP requests |
| lxml | HTML/XML parsing |
| python-dotenv | Local environment variable management |
| Git & GitHub | Version control and source code hosting |
| Streamlit Community Cloud | Application deployment |

*The technology list reflects the project's intended dependencies. Actual providers and integrations depend on the configuration in the source code.*

## 📂 Project Structure

```text
multi-agent-research-system/
│
├── app.py              # Streamlit application
├── agents.py           # Specialized AI agents and chains
├── pipeline.py         # Research pipeline orchestration
├── tools.py            # Search and research tools
├── requirements.txt    # Python dependencies
├── .gitignore          # Excluded files and secrets
└── history/            # Research history, if enabled
```

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/amar9198/multi-agent-research-system.git
cd multi-agent-research-system
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `.env` file in the project root and add the API keys required by your implementation:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholders with your own valid keys. If your code uses different providers or environment variable names, configure those instead.

**Security:** Never commit `.env` or publish API keys to GitHub.

### 5. Launch the application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

`http://localhost:8501`

## 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Access to OpenAI models, if used |
| `TAVILY_API_KEY` | Access to Tavily search, if used |

For deployment, configure the required secrets through Streamlit Community Cloud's app settings rather than committing credentials to the repository.

## 🌍 Deployment

The application is deployed using Streamlit Community Cloud and connected to its GitHub repository.

**Live application:**  
https://multi-agent-research-system-mruutv3xcxkcyf9ualxwrc.streamlit.app/

## 🎯 Use Cases

- Exploring unfamiliar technical topics
- Collecting information from multiple web sources
- Generating preliminary research summaries
- Organizing web research into structured reports
- Reviewing AI-generated content for potential gaps or improvements
- Experimenting with multi-agent AI architectures

## ⚠️ Limitations

- Search quality depends on the available search service and retrieved sources.
- Generated reports may contain inaccuracies and should be independently verified.
- API usage may incur costs or be subject to provider quotas.
- Critic feedback is AI-generated and does not guarantee factual correctness.
- The system should be treated as a research aid, not a substitute for expert review.

## 🔮 Future Improvements

- Add source citations and direct links throughout generated reports.
- Introduce parallel agent execution to improve efficiency.
- Add report export options such as PDF and Markdown.
- Improve source relevance ranking and duplicate-content handling.
- Add configurable research depth and output formats.
- Enhance error handling, logging, and evaluation metrics.
- Add persistent research history and downloadable reports.

## 👨‍💻 Author

**Amar**

GitHub: [@amar9198](https://github.com/amar9198)

Project Repository: [Multi-Agent Research System](https://github.com/amar9198/multi-agent-research-system)

---

⭐ If you find this project interesting, consider exploring the repository and trying the live application.

**Built to explore the potential of multi-agent AI for automated research and report generation.**
