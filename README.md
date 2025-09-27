# DOMCHAT
Domain Conversational Hub for Analytical Tasks

DOMCHAT is a Flask-based web application that combines web scraping, document analysis, and conversational AI to provide intelligent insights from both web domains and uploaded documents. It features a modern chat interface powered by advanced LLM models for interactive data exploration.

## 🚀 Features

### 🌐 Domain Analysis
- **Web Crawling**: Automatically crawl and analyze entire domains or specific URLs
- **Content Extraction**: Extract and process text content from web pages
- **Intelligent Summarization**: Get AI-powered summaries and insights from crawled data
- **Real-time Chat**: Ask questions about analyzed domain content

### 📄 Document Analysis  
- **Multi-format Support**: Upload and analyze PDF, DOCX, HTML, and TXT files
- **RAG (Retrieval-Augmented Generation)**: Chat with your documents using vector similarity search
- **Chunk Processing**: Intelligent document chunking for optimal context retrieval
- **Document Status Tracking**: Monitor processing status and document metrics

### 💬 Interactive Chat Interface
- **Session Management**: Create multiple analysis sessions for different projects
- **Auto-detection**: Automatically switches between domain and document chat modes
- **Chat History**: Persistent conversation history per session
- **Real-time UI**: Modern, responsive chat interface with typing indicators

### 🔧 Flexible LLM Support
- **Local Models**: Support for local GGUF models via llama-cpp-python
- **Groq API**: Cloud-based LLM inference with Groq's fast API
- **Model Switching**: Easy configuration between local and cloud providers

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Git
- Virtual environment support

### Quick Setup

1. **Clone the repository**:
```bash
git clone https://github.com/mohamedsuhail-n/DOMCHAT.git
cd DOMCHAT
```

2. **Run the automated setup script**:
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Update your system packages
- Install Python dependencies
- Create a virtual environment
- Install Playwright browsers
- Set up all required components

### Manual Setup

If you prefer manual installation:

1. **Create virtual environment**:
```bash
python3 -m venv dcenv
source dcenv/bin/activate  # On Windows: dcenv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
playwright install
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env file with your API keys and settings
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required for Groq API (if using cloud LLM)
GROQ_API_KEY=your_groq_api_key_here

# Optional: Database paths (will use defaults if not specified)
CHROMA_DB_PATH=./storage/chroma_storage
LLAMA_MODEL_PATH=./storage/models/model.gguf
```

### Configuration Options

Edit `config.py` to customize:

- **LLM Provider**: Choose between `"local"` or `"groq"`
- **Model Paths**: Specify paths to local GGUF models
- **Crawling Settings**: Max pages, delays, content limits
- **Processing Settings**: Chunk sizes, embedding models
- **Storage Paths**: Database and file storage locations

Example configuration:
```python
class Config:
    LLM_PROVIDER = "groq"  # or "local"
    GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
    MAX_PAGES = 25
    CHUNK_SIZE = 1000
    # ... other settings
```

## 🚀 Usage

### Starting the Application

1. **Activate your virtual environment**:
```bash
source dcenv/bin/activate  # On Windows: dcenv\Scripts\activate
```

2. **Start the server**:
```bash
python api.py
```

3. **Open your browser** to: `http://localhost:5000`

### Using the Interface

#### 1. Domain Analysis
- Click "Analyze Domain" button
- Enter a domain name (e.g., `example.com`)
- Wait for crawling and analysis to complete
- Start chatting with the analyzed content

#### 2. Document Analysis
- Click "Analyze Files" button
- Upload PDF, DOCX, HTML, or TXT files
- Documents are automatically processed and indexed
- Chat with your documents using natural language

#### 3. Session Management
- Create multiple sessions for different projects
- Switch between sessions in the sidebar
- Rename sessions for better organization
- Each session maintains separate chat history and context

### API Endpoints

DOMCHAT provides a REST API for programmatic access:

#### Session Management
- `POST /api/initialize` - Create new analysis session
- `GET /api/sessions` - List all sessions
- `DELETE /api/session/<id>` - Delete session
- `POST /api/session/<id>/rename` - Rename session

#### Analysis
- `POST /api/analyze_domain` - Analyze domain/website
- `POST /api/analyze_urls` - Analyze specific URLs
- `POST /api/upload_file` - Upload document for analysis

#### Chat
- `POST /api/chat` - Send chat message (auto-detects context type)
- `POST /api/document_chat` - Chat specifically with documents
- `GET /api/history/<session_id>` - Get chat history
- `POST /api/clear-chat` - Clear chat history

#### Status & Diagnostics
- `GET /api/status` - Get API status and diagnostics
- `POST /api/load_model` - Load/reload LLM model

## 📁 Project Structure

```
DOMCHAT/
├── api.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── setup.sh             # Automated setup script
├── core/                # Core functionality modules
│   ├── analyzer.py      # Main domain analyzer
│   ├── crawler.py       # Web crawling logic
│   ├── doc_*.py         # Document processing modules
│   ├── llm_*.py         # LLM provider implementations
│   └── utils.py         # Utility functions
├── static/              # CSS, JS, and static assets
├── templates/           # HTML templates
└── storage/             # Data storage directory (created automatically)
    ├── chroma_storage/  # Vector database
    └── models/          # Local model storage
```

## 🔧 Troubleshooting

### Common Issues

**1. Groq API Key Error**
```
Error: GROQ_API_KEY not found
```
Solution: Add your Groq API key to the `.env` file.

**2. Model Loading Failed**
```
Error loading local model
```
Solution: Check the `LLAMA_MODEL_PATH` in `config.py` and ensure the GGUF model file exists.

**3. Port Already in Use**
```
Address already in use
```
Solution: Kill existing processes on port 5000 or change the port in `api.py`.

**4. Playwright Installation Issues**
```
Playwright browsers not installed
```
Solution: Run `playwright install` after installing requirements.

### Performance Tips

- **For large documents**: Adjust `CHUNK_SIZE` in config for optimal processing
- **For better crawling**: Increase `CRAWL_DELAY` to be respectful to target sites
- **For faster responses**: Use Groq API instead of local models
- **For privacy**: Use local models instead of cloud APIs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or need help:

1. Check the troubleshooting section above
2. Review the configuration settings
3. Check the application logs for error messages
4. Open an issue on GitHub with detailed information

---

**Built with**: Flask, ChromaDB, Sentence Transformers, Playwright, and modern web technologies.