# AskRepo

**Live Demo:** [https://askrepo.onrender.com/](https://askrepo.onrender.com/)

AskRepo is an AI-powered codebase intelligence platform designed to help developers seamlessly understand, navigate, and analyze complex GitHub repositories. By processing a GitHub URL or a ZIP archive, AskRepo autonomously parses the source code, maps its dependencies, and provides an interactive interface to query the repository using a sophisticated Multi-Agent AI system.

## Core Features

### Multi-Agent Autonomous System
AskRepo goes beyond standard prompt engineering by utilizing a multi-agent orchestration architecture. User queries are classified and routed to specialized agents, ensuring high accuracy and contextual relevance:
* **Router Agent:** Analyzes the user's prompt to determine intent and dispatches the request to the most qualified sub-agent.
* **Code Agent:** Specializes in explaining syntax, debugging logic, and retrieving highly specific function-level context using vector search.
* **Architecture Agent:** Understands the broader system design, analyzing the dependency graph to explain how different modules and files interact.
* **Repository Agent (Onboarding):** Acts as a senior engineer onboarding a new hire. It reads the repository's `README.md` and statistical metadata to explain the project's purpose and functionality in simple, human-readable terms.

### Advanced Retrieval-Augmented Generation (RAG)
To ground the AI's responses in factual, repository-specific data, AskRepo implements an advanced RAG pipeline:
* **Structural Chunking via ASTs:** Instead of arbitrary text splitting, the platform uses Tree-sitter to parse Abstract Syntax Trees (ASTs). This ensures the AI understands the structural boundaries of classes, methods, and functions.
* **Dense Vector Semantic Search:** Code chunks are converted into 3072-dimensional vectors using Google Gemini Embeddings and stored in a FAISS vector database, enabling blazing-fast nearest-neighbor semantic retrieval.

### High-Availability AI Gateway
To ensure maximum uptime and handle API rate limits gracefully, AskRepo features a custom-built AI Gateway:
* **Cascading Model Fallback:** The system automatically routes complex queries to Google's bleeding-edge models (e.g., `gemini-3.5-flash`). If the strict free-tier rate limits are hit, the gateway instantly catches the `429` error and seamlessly cascades down to higher-limit models (`gemini-2.5-pro` -> `gemini-2.5-flash`), guaranteeing uninterrupted service.
* **Bring Your Own Key (BYOK):** Users can securely input their own Gemini API key via the frontend. The system proactively checks API quota limits during repository upload and instantly falls back to the user's local storage key if the server quota is exhausted.

### Interactive Architecture Graph
AskRepo statically analyzes import statements and file dependencies across the codebase to automatically generate a full, interactive 2D network graph. This provides developers with an immediate visual understanding of the repository's architecture and module coupling.

### Git History and Hotspot Analysis
The platform analyzes the repository's commit history to identify development "hotspots" (files that are modified most frequently) and co-changing files. This analytical layer helps onboarding developers quickly identify where the core active logic of the application resides.

## Technology Stack

### Backend
* **Python & FastAPI:** High-performance asynchronous API server.
* **PostgreSQL & SQLAlchemy:** Relational database for storing repository metadata and asynchronous analysis jobs.
* **FAISS:** In-memory vector database for semantic search and RAG capabilities.
* **Google Gemini API:** Powers the multi-agent system and text embedding generation.
* **Tree-sitter:** Syntax-aware code parsing engine supporting multiple languages.

### Frontend
* **React & TypeScript:** Strongly typed, component-driven user interface.
* **Tailwind CSS:** Utility-first styling for a clean, responsive design.
* **Framer Motion:** High-performance animations and transitions.
* **Cytoscape.js:** Renders the interactive, physics-based 2D dependency graph.

## Deployment

AskRepo is containerized using Docker, allowing for seamless deployment across cloud platforms.

### Prerequisites
1. A managed PostgreSQL database (e.g., Neon.tech).
2. A Google Gemini API Key.
3. A GitHub Personal Access Token (to bypass unauthenticated rate limits during repository cloning).

### Deploying to Render
1. Create a new **Web Service** on [Render](https://render.com).
2. Connect the target GitHub repository.
3. Set the Environment to **Docker**.
4. Configure the following Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string (must use the `postgresql+asyncpg://` dialect).
   - `GOOGLE_API_KEY`: Your Gemini API key.
   - `GITHUB_TOKEN`: Your GitHub token.
   - `MAX_REPOSITORY_SIZE_MB`: (Optional) Set to `500` to allow the analysis of larger repositories.
5. Deploy the service. Render will automatically build the React frontend, package it with the FastAPI backend, and serve the application on a single unified port.

## Local Development

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`.
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## License
MIT License
