# AskRepo

AskRepo is an AI-powered codebase intelligence tool that allows developers to understand, navigate, and analyze any GitHub repository in minutes. By providing a GitHub URL or uploading a ZIP file, AskRepo autonomously parses the codebase, maps its dependencies, and allows you to chat with an AI assistant that has deep, contextual knowledge of the code.

## Features

* **Autonomous Code Parsing:** Extracts abstract syntax trees (ASTs) using Tree-sitter to index functions, classes, and file dependencies.
* **Intelligent Chat Assistant:** Ask questions about the codebase architecture, logic, or specific functions. The AI automatically retrieves the relevant context using RAG (Retrieval-Augmented Generation).
* **Architecture Visualization:** Automatically generates a dependency graph highlighting the architecture and relationships between files in the repository.
* **Git History Analysis:** Analyzes the repository's commit history to identify hotspots and frequently modified files.
* **Scalable Architecture:** Designed with FastAPI, PostgreSQL, and a modern React frontend.

## Tech Stack

### Backend
* **Python & FastAPI:** High-performance async API server.
* **PostgreSQL & SQLAlchemy:** Relational database for storing repository metadata and analysis results.
* **FAISS:** Vector database for semantic search and RAG capabilities.
* **Google Gemini AI:** Powers the conversational agent and text embeddings.
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
