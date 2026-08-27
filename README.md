# AskRepo

AskRepo is an AI-powered codebase intelligence tool that allows developers to understand, analyze, and interact with any repository in minutes. By providing a GitHub URL or uploading a ZIP file, developers can chat with an intelligent multi-agent system that understands the codebase architecture, file contents, git history, and code complexity.

## Features & Capabilities

The project was developed in seven distinct phases, culminating in a robust, production-ready application:

*   **Repository Scanning (Phase 1):** Ingests codebases via GitHub URL cloning or ZIP upload. It scans directories, extracts metadata, identifies programming languages, and detects configuration and entry point files.
*   **Code Parsing & Intelligence (Phase 2):** Utilizes Tree-sitter to parse source code into Abstract Syntax Trees (AST). It extracts classes, functions, methods, and imports, calculating complexity metrics (like Cyclomatic Complexity) for deeper code understanding.
*   **AI Chat & RAG Pipeline (Phase 3):** Employs a Retrieval-Augmented Generation (RAG) pipeline. Code chunks and documentation are embedded and indexed using FAISS, allowing the LLM to answer natural language questions about the code accurately and with source citations.
*   **Architecture Visualization (Phase 4):** Analyzes import statements to build a dependency graph using NetworkX. The frontend renders this interactive architecture diagram using React Flow, helping visualize module relationships and structural bottlenecks.
*   **Git Archaeology (Phase 5):** Parses the repository's commit history to track file changes over time. It identifies code hotspots (frequently modified files) and provides a timeline of the repository's evolution.
*   **Multi-Agent System (Phase 6):** Enhances the AI chat by routing user queries through an intelligent Orchestrator. Depending on the question, the query is delegated to specialized agents (e.g., Code Analyst, Architecture Analyst, Git Historian, Quality Analyst). Deterministic queries bypass the LLM entirely for faster, exact answers.
*   **Production Hardening (Phase 7):** Secures the application for public deployment with IP-based rate limiting, asynchronous usage tracking, structured error handling, JSON logging, and a background workspace cleanup service.

## Architecture Overview

AskRepo uses a modern web stack designed for scalability and performance:

*   **Frontend:** Built with React, TypeScript, and Vite. The user interface is styled with Tailwind CSS, providing a responsive and accessible dashboard with specialized tabs for Files, Symbols, Architecture, Dependencies, Git History, and the AI Chat.
*   **Backend:** Powered by Python and FastAPI. The backend handles asynchronous API requests, file processing, and agent orchestration.
*   **Database:** PostgreSQL with SQLAlchemy and asyncpg for storing repository metadata, extracted symbols, git commits, and usage logs.
*   **Vector Search:** FAISS (Facebook AI Similarity Search) is used for fast, local semantic search over code embeddings.
*   **AI Provider:** Google Gemini API (via google-genai SDK) powers the underlying language models for reasoning and synthesis.

## Quick Start

### Prerequisites

*   Docker and Docker Compose

### Running with Docker (Recommended)

1.  Clone the repository and copy the environment configuration template:
    ```bash
    cp .env.example .env
    ```
2.  Add your Gemini API key to the `.env` file under `GOOGLE_API_KEY`.
3.  Start all services (Frontend, Backend, and PostgreSQL) using Docker Compose:
    ```bash
    docker-compose up --build -d
    ```
4.  Access the application:
    *   Frontend Dashboard: `http://localhost:5173`
    *   Backend API Docs: `http://localhost:8000/docs`

### Manual Local Setup

1.  Start a local PostgreSQL instance (ensure it is running on port 5432).
2.  Copy the `.env.example` file to `backend/.env` and configure your database URL and API keys.
3.  Start the Backend:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    ```
4.  Start the Frontend:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Environment Variables

Key configurations found in `.env`:

*   `DATABASE_URL`: Connection string for PostgreSQL.
*   `GOOGLE_API_KEY`: API key for Google Gemini models (Required for AI chat).
*   `AI_MODEL`: The specific LLM model to use (default: `gemini-3.6-flash`).
*   `GITHUB_TOKEN`: Optional token to increase GitHub cloning rate limits.
*   `MAX_REPOSITORY_SIZE_MB`: Maximum size of repositories allowed for ingestion (default: 50MB).
*   `MAX_AI_REQUESTS_PER_DAY`: Rate limit for AI chat queries per IP address.

## License

This project is licensed under the MIT License.
