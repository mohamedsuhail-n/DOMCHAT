# DOMCHAT — Local AI & Hybrid RAG Workstation

**DOMCHAT** is a completely fresh, high-performance, greenfield AI application engineered specifically for local execution on Windows 11 with resource constraints (Intel i3-1005G1 CPU, 8GB RAM, no dedicated GPU).

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │          React + Vite Frontend         │
                      │   (TypeScript, Tailwind CSS, Lucide)   │
                      └───────────────────┬────────────────────┘
                                          │ REST & SSE
                                          ▼
                      ┌────────────────────────────────────────┐
                      │              Flask Backend             │
                      │        (Modular Service Arch)          │
                      └───┬───────────────────────────────┬────┘
                          │                               │
       ┌──────────────────▼──────────┐         ┌──────────▼─────────────────┐
       │     Hybrid RAG Pipeline     │         │   Local Ollama Inference   │
       │  - Dense: all-MiniLM-L6-v2  │         │   - Model: qwen2.5:1.5b    │
       │  - Sparse: BM25 Tokenizer   │         │   - 100% CPU Execution     │
       │  - Store: ChromaDB (Disk)   │         │   - Zero Cloud Leaks       │
       │  - DB: SQLite (Relational)  │         └────────────────────────────┘
       └─────────────────────────────┘
```

---

## Key Features & Product Modules

### 1. Dashboard
- **Quick Action Center**: Start chat, upload documents, crawl websites, configure model.
- **Resource Monitoring**: Real-time CPU percent and RAM consumption against the 8GB ceiling.
- **System Health**: Ollama connection status, ChromaDB persistence status, storage paths.
- **Recent Activity**: Quick access to recent conversations and indexed sources.

### 2. AI Assistant
- **Conversational Interface**: Modern desktop chat with smooth animations, code highlighting, and one-click copy.
- **Local Qwen 2.5 1.5B**: Fast local CPU inference via Ollama.
- **Source Citations**: Interactive source citations linking directly to indexed documents (with page numbers) or website URLs.
- **Grounding Guardrails**: Prompt directives instruct Qwen to answer strictly from context and refuse fabrication.
- **Conversation Controls**: Create, switch, rename, delete conversations, and regenerate responses.
- **Exporting**: One-click download of conversations or individual messages as Markdown or JSON.

### 3. Document Intelligence
- **Supported Formats**: PDF, DOCX, TXT, Markdown, and CSV.
- **Extraction Pipeline**: Page-aware extraction with metadata preservation (filename, page numbers, row numbers).
- **Chunking**: Sentence- and paragraph-aware boundary splitting with configurable chunk size and overlap.
- **Management**: Re-indexing and document deletion with automated vector clean-up.

### 4. Domain Intelligence (Web Crawling)
- **Safe Web Crawling**: Domain-restricted HTTP crawling with configurable page limits (1–10 pages).
- **SSRF Protection**: Strictly blocks localhost, loopback (`127.0.0.1`), private RFC1918 subnets, and link-local ranges.
- **Boilerplate Stripping**: Cleans scripts, styles, navigational bars, and footers with BeautifulSoup.
- **Website Grounding**: Ground conversations specifically on crawled web domains.

### 5. Knowledge Management
- **Unified Catalog**: Central view of all indexed documents and crawled websites.
- **Hybrid Retrieval Tester**: Interactive benchmark allowing queries across varying fusion weights (Alpha: 0.0 = 100% BM25 keyword matching, 1.0 = 100% semantic vector similarity).
- **ChromaDB Chunk Inspector**: Direct examination of raw text chunks, metadata, and token boundaries.

### 6. Model Studio & Settings
- **Ollama Integration**: Live connection verification and discovery of local models.
- **Hyperparameter Controls**: Temperature, Top-P, Max Tokens, and System Prompt editing.
- **RAG Configuration**: Configurable Chunk Size, Chunk Overlap, Top-K, and Hybrid Alpha.
- **Privacy & Security**: Local-Only toggle and securely masked optional cloud API key fields.
- **Live Benchmark**: Test prompt response latency directly within the settings studio.

### 7. Project Management
- **Workspace Isolation**: Organize work into distinct projects (e.g., Default Workspace, Legal, Research).
- **Isolated Vectors**: Conversations, files, websites, and ChromaDB collections are partitioned per project.

---

## Project Structure

```
DOMCHAT/
├── backend/
│   ├── app.py                      # Flask Application entry point & CORS
│   ├── config.py                   # Central settings, constants, and defaults
│   ├── api/
│   │   ├── health.py               # System & Ollama health endpoint
│   │   ├── projects.py             # Workspace & project management
│   │   ├── conversations.py        # Conversation CRUD
│   │   ├── chat.py                 # Chat & RAG inference endpoint
│   │   ├── documents.py            # Document upload & extraction
│   │   ├── domain.py               # Website crawling & indexing
│   │   ├── knowledge.py            # Knowledge catalog & hybrid test
│   │   ├── models_api.py           # Model settings & benchmark
│   │   └── export.py               # Markdown and JSON export
│   ├── services/
│   │   ├── llm/
│   │   │   └── ollama_client.py    # Local Ollama client & streaming
│   │   ├── embeddings/
│   │   │   └── embedding_service.py# SentenceTransformer singleton with cache
│   │   ├── retrieval/
│   │   │   ├── bm25.py             # Sparse BM25 keyword retrieval
│   │   │   └── hybrid_retriever.py # Reciprocal fusion & citation builder
│   │   ├── extraction/
│   │   │   ├── extractor.py        # PDF, DOCX, TXT, CSV parser
│   │   │   └── chunker.py          # Boundary-aware text splitter
│   │   ├── crawling/
│   │   │   └── crawler.py          # SSRF-safe HTTP crawler
│   │   └── storage/
│   │       ├── vector_store.py     # ChromaDB PersistentClient
│   │       └── metadata_store.py   # SQLite metadata store
│   └── tests/
│       ├── test_backend.py         # Unit & RAG pipeline verification
│       └── test_api_flow.py        # End-to-end API integration test
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx         # Navigation & hardware monitor
│   │   │   ├── CitationBadge.tsx   # Expandable citation references
│   │   │   └── ProjectModal.tsx    # New project modal
│   │   ├── modules/
│   │   │   ├── dashboard/          # DashboardModule.tsx
│   │   │   ├── assistant/          # AssistantModule.tsx
│   │   │   ├── documents/          # DocumentModule.tsx
│   │   │   ├── domain/             # DomainModule.tsx
│   │   │   ├── knowledge/          # KnowledgeModule.tsx
│   │   │   └── settings/           # SettingsModule.tsx
│   │   ├── services/
│   │   │   └── api.ts              # Typed fetch client
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   ├── App.tsx                 # Root layout & state
│   │   ├── main.tsx                # React entry
│   │   └── index.css               # Tailwind & custom scrollbars
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── storage/
│   ├── chroma/                     # ChromaDB vector database files
│   ├── uploads/                    # Physical uploaded documents
│   ├── exports/                    # Export output cache
│   └── db/                         # SQLite metadata database (domchat.db)
│
├── requirements.txt                # Python backend dependencies
├── .env.example                    # Environment variable template
├── start.bat                       # One-click Windows startup script
└── README.md
```

---

## Hardware Optimization Highlights

- **Model Selection**: Pre-installed `qwen2.5:1.5b` (986MB). Provides crisp answers with minimal RAM footprint.
- **Embedding Efficiency**: `all-MiniLM-L6-v2` (80MB, 384 dimensions) runs directly on CPU with singleton caching. No duplicate embeddings are generated for identical chunks.
- **ChromaDB**: Persisted on disk at `storage/chroma/`, retaining index state between restarts.
- **Relational Storage**: SQLite stores conversation trees, source metadata, and configuration with sub-millisecond retrieval and zero background daemon overhead.

---

## Quick Start (Windows 11)

### Prerequisites
1. **Ollama**: Ensure Ollama is running and `qwen2.5:1.5b` is downloaded (`ollama list`).
2. **Python**: Python 3.11 installed.
3. **Node.js**: Node 18+ and npm installed.

### One-Click Startup
Double-click `start.bat` in the project root:
```bat
start.bat
```
The script will:
1. Verify Ollama is running and `qwen2.5:1.5b` is present.
2. Verify or create the Python virtual environment (`.\venv\Scripts\python.exe`).
3. Check and build frontend dependencies.
4. Launch the Flask Backend at `http://127.0.0.1:5000`.
5. Launch the React Vite frontend at `http://localhost:5173`.
6. Open your default web browser automatically.

### Manual Launch
If you prefer running components manually in separate terminals:

**Terminal 1 (Backend):**
```bash
.\venv\Scripts\python.exe backend\app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

---

## Test Results

All verification suites pass with 100% success:

```
=== TEST 1: Database Operations ===
Projects found: 1
PASS: Database init and default project exists.

=== TEST 2: Ollama Connectivity & Model ===
Ollama connected: True
Models: ['qwen2.5:1.5b']
PASS: Ollama is running and qwen2.5:1.5b is detected.

=== TEST 3: Text Chunking ===
Chunks generated: 1
PASS: Chunker functions correctly.

=== TEST 4: SSRF Security Validation ===
PASS: SSRF protection properly blocks localhost and private IPs.

=== TEST 5: Vector Store & Hybrid Retrieval ===
Retrieved 2 chunks (Fused score: 0.8654)
PASS: Vector store and hybrid retrieval successfully retrieved relevant knowledge.

=== TEST 6: RAG Prompt Construction & Local Inference ===
Sending grounded question to qwen2.5:1.5b...
Model response: DOMCHAT uses ChromaDB for persistent vector embeddings storage on disk.
PASS: Local Qwen 2.5 1.5B generated grounded response!

ALL BACKEND TESTS PASSED SUCCESSFULLY!
```

---

## Known Limitations

1. **Hardware Ceiling**: On dual-core CPUs (Intel i3-1005G1), concurrent inference is limited to 1 stream at a time to prevent CPU throttling.
2. **Context Window**: While Qwen 2.5 supports large context lengths, maintaining Top-K between 2 and 6 chunks provides the lowest latency on 8GB RAM systems.
3. **Single Domain Web Crawling**: The crawler follows same-host HTTP links to adhere to security boundaries and avoid unbounded crawl loops.
