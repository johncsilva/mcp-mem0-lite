# GEMINI.md

## Project Overview

This project, `mcp-mem0-lite`, is a Python-based server that provides a memory storage and retrieval system for an AI assistant, likely Claude Desktop. It acts as a local, personal memory store, allowing the AI to remember information across conversations.

The server uses the following technologies:

*   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python.
*   **mem0:** A library for building and managing long-term memory for AI applications.
*   **SQLite:** A C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine.
*   **ChromaDB:** An open-source embedding database for building AI applications with semantic search.
*   **Ollama:** A tool for running large language models locally.

The architecture consists of a `Claude Desktop` client communicating with the `FastMCP` server via Server-Sent Events (SSE). The server exposes a set of tools for memory management, and `mem0` handles the core memory operations, using SQLite for metadata storage, ChromaDB for vector storage, and Ollama for generating embeddings and providing language model capabilities.

## Building and Running

### 1. Prerequisites

*   Python 3.7+
*   Ollama installed and running with the required models (e.g., `nomic-embed-text`, `llama3.1:8b`).

### 2. Installation

While there isn't a formal `requirements.txt`, the following libraries are used:

*   `fastapi`
*   `uvicorn`
*   `python-dotenv`
*   `mem0`
*   `mcp-sdk`

You can install them using pip:

```bash
pip install fastapi uvicorn python-dotenv mem0ai mcp-sdk
```

### 3. Configuration

Create a `.env` file in the root of the project with the following content, adjusting the paths and models as needed:

```env
HOST=127.0.0.1
PORT=8050
DATABASE_URL=sqlite:///mem0.db
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMS=768
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
```

### 4. Running the Server

To start the server, run the following command:

```bash
python server.py
```

The server will be available at `http://127.0.0.1:8050`.

## Development Conventions

*   **Configuration:** The server is configured through environment variables, which are loaded from a `.env` file. This is a common practice for separating configuration from code.
*   **API:** The server uses FastAPI to create a REST API and a Server-Sent Events (SSE) endpoint for real-time communication with the client.
*   **Tools:** The server's functionality is exposed as a set of "tools" using the `FastMCP` class. This is a design pattern that allows clients to discover and execute available functions.
*   **Error Handling:** The code includes basic error handling, such as checking if `mem0` is initialized before use.
*   **Modularity:** The code is organized into sections for helper functions, the `mem0` constructor, MCP server and tools, and the application lifecycle.

## Key Files

*   `server.py`: The main FastAPI application that runs the MCP server.
*   `README_MCP_SETUP.md`: Provides detailed setup instructions and an overview of the architecture.
*   `.env`: The configuration file for the server.
*   `claude_desktop_config.json`: An example configuration file for the Claude Desktop client.
*   `mcp_client.py`: A simple Python client that demonstrates how to connect to the server.
