# AskRepo

AskRepo is an AI-powered codebase intelligence tool that allows developers to understand, navigate, and analyze any GitHub repository in minutes. By providing a GitHub URL or uploading a ZIP file, AskRepo autonomously parses the codebase, maps its dependencies, and allows you to chat with a sophisticated Multi-Agent AI system that has deep, contextual knowledge of the code.

## Core Features

###  Multi-Agent AI System
AskRepo features a sophisticated autonomous routing system that classifies your query and delegates it to specialized AI agents:
* **Router Agent:** Analyzes the user's prompt to determine intent and dispatches the request to the most qualified sub-agent.
* **Code Agent:** Expert at explaining syntax, debugging logic, and retrieving highly specific function-level context using vector search.
* **Architecture Agent:** Understands the broader system design, analyzing the dependency graph to explain how different modules and files interact.
* **Repository Agent:** Answers high-level questions about the repository's purpose, tech stack, and overall statistics without needing to search the code.

###  Retrieval-Augmented Generation (RAG)
When you ask a question, AskRepo doesn't guess. It uses an advanced RAG pipeline to ground the AI in reality:
* **Semantic Search:** Uses Google Gemini Embeddings and a FAISS vector database to instantly retrieve the exact files and functions relevant to your question.
* **Tree-Sitter Parsing:** Extracts Abstract Syntax Trees (ASTs) from the raw code, allowing the AI to understand the structural boundaries of classes, methods, and variables rather than just reading raw text.

###  Interactive Architecture Graph
AskRepo automatically analyzes import statements and file dependencies across the codebase to generate a full, interactive 2D network graph of the repository's architecture. 

###  Git History & Hotspot Analysis
The platform acts as a Git Archaeologist, analyzing the repository's commit history to identify "hotspots" (files that are modified most frequently) and co-changing files. This helps new developers instantly understand where the core active logic of the application resides.

## Tech Stack

### Backend
* **Python & FastAPI:** High-performance async API server.
* **PostgreSQL & SQLAlchemy:** Relational database for storing repository metadata and analysis results.
* **FAISS:** Vector database for semantic search and RAG capabilities.
* **Google Gemini AI:** Powers the multi-agent system and text embeddings.
* **Tree-sitter:** Used for syntax-aware code parsing across multiple languages.

### Frontend
* **React & TypeScript:** Strongly typed modern UI framework.
* **Tailwind CSS:** Utility-first styling for a clean and responsive design.
* **Framer Motion:** Smooth animations and transitions.
* **Cytoscape.js:** Renders the interactive 2D dependency graph.

## Deployment

AskRepo is designed to be deployed as a unified Docker container, making it easy to host the entire application on platforms like Render.

### Prerequisites for Deployment
1. A free PostgreSQL database (e.g., Neon.tech).
2. A Google Gemini API Key.
3. A GitHub Personal Access Token (for bypassing unauthenticated rate limits).

### Deploying to Render
1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository.
3. Set the Environment to **Docker**.
4. Add the following Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string (must use `postgresql+asyncpg://`).
   - `GOOGLE_API_KEY`: Your Gemini API key.
   - `GITHUB_TOKEN`: Your GitHub token.
   - `MAX_REPOSITORY_SIZE_MB`: (Optional) Set to `500` to allow larger repositories.
5. Deploy the service. Render will automatically build the frontend, package it with the FastAPI backend, and serve it on a single URL.

## Local Development

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
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
