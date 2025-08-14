# StrategemForge: AI-Powered Counter-Strike 2 Analytics Platform

## 1. Overview

StrategemForge is a comprehensive, self-hostable analytics platform designed to give Counter-Strike 2 teams a competitive edge. It moves beyond simple statistics by leveraging advanced AI, including Graph Neural Networks (GNNs) for tactical analysis and Large Language Models (LLMs) for generating actionable, natural-language insights.

This platform is built to run entirely on a powerful local PC, ensuring data privacy and eliminating subscription costs. It provides a complete ecosystem for demo analysis, opponent scouting, and strategic planning.

### Core Technologies
*   **Backend:** Python
*   **Demo Parsing:** `awpy` [1, 2]
*   **AI/ML:** PyTorch, PyTorch Geometric, PyTorch Geometric Temporal [3, 4]
*   **LLM Orchestration:** LangChain, Ollama [5, 6, 7]
*   **Vector Database:** ChromaDB / FAISS [8, 9]
*   **Frontend Dashboard:** Plotly Dash [10, 11]

---

## 2. Phased Implementation Plan

This project is designed to be built in distinct, sequential phases. Each phase delivers a functional component of the platform, allowing for incremental development and immediate value at every stage.

### Phase 1: The Foundation - Automated Demo Parsing
**Goal:** Establish a reliable pipeline to ingest raw CS2 demo files (`.dem`) and convert them into a structured, machine-readable format.

**Tasks:**
1.  **Environment Setup:** Create a dedicated Python environment (`>=3.11`) and install foundational libraries like `awpy`. [1]
2.  **Develop Parsing Script:** Write a Python script that takes a demo file path as input and uses `awpy` to parse it into a comprehensive JSON object. [12]
3.  **Data Cleaning:** Implement functions to filter out irrelevant data, such as warmup rounds, knife rounds, and restarts. [13, 2]
4.  **Data Storage:** Define a clear and consistent file structure to store the parsed JSON outputs, linking them to the original demo files.

**Outcome:** A command-line tool that can process a directory of demo files and produce clean, structured JSON data for each match.

---

### Phase 2: The Command Center - Interactive Dashboard
**Goal:** Create a web-based user interface to visualize the parsed data, focusing on an interactive 2D replay viewer.

**Tasks:**
1.  **Setup Dash Application:** Initialize a multi-page Plotly Dash application. [14, 11]
2.  **Build Layouts:** Design the UI layout for a match selection page and a round analysis page using Dash HTML and Core Components. [10]
3.  **Implement 2D Replay:**
    *   Use a Plotly scatter plot to render a top-down map.
    *   Create a callback that updates player positions on the map based on a time slider. [15]
    *   Overlay key events (kills, bomb plants, grenade detonations) onto the map.
4.  **Data Integration:** Write callbacks that load the parsed JSON data from Phase 1 based on user selections (e.g., choosing a match from a dropdown). [16]

**Outcome:** A functional web dashboard where a user can select a match, choose a round, and scrub through an interactive 2D replay of that round.

---

### Phase 3: The AI Analyst - "Query-Your-Demos" with RAG
**Goal:** Integrate a local Large Language Model to allow users to ask natural language questions about their gameplay data.

**Tasks:**
1.  **Local LLM Setup:** Install and run a local LLM (e.g., Llama 3 8B, Mistral 7B) using `Ollama`. [17, 6]
2.  **Knowledge Base Creation:**
    *   Write scripts to process the JSON data from Phase 1 into plain text documents (e.g., one document per round summary).
    *   Split these documents into smaller, semantically coherent chunks. [18, 9]
    *   Use an embedding model (e.g., `nomic-embed-text` via Ollama) to convert text chunks into vector embeddings. [6]
3.  **Vector Store Implementation:** Store the embeddings in a local vector database like ChromaDB or FAISS. [8, 9]
4.  **Build RAG Pipeline:** Use LangChain to construct a Retrieval-Augmented Generation (RAG) chain. This chain will:
    *   Take a user's question.
    *   Retrieve relevant text chunks from the vector store.
    *   Pass the question and retrieved context to the local LLM to generate an answer. [19, 20, 7]
5.  **Dashboard Integration:** Add a new page to the Dash app with a chat interface for users to interact with the RAG system.

**Outcome:** A powerful "AI Analyst" feature in the dashboard, enabling users to ask questions like *"How many rounds have we won on Inferno T-side when we get the first kill?"* and receive data-grounded answers.

---

### Phase 4: Advanced Insight - GNN for Tactic Classification
**Goal:** Develop and integrate a Graph Neural Network (GNN) to automatically identify and label team tactics within each round.

**Tasks:**
1.  **Data Labeling:** Manually review a subset of your team's demos (a few hundred rounds is a good start) and assign a tactical label to each round (e.g., 'A Rush', 'B Split', 'Default'). [21, 22]
2.  **Graph Preprocessing:** Create a data pipeline that converts the parsed frame-by-frame data into sequences of graph representations for each round. [21]
3.  **Model Definition:** Define a Spatio-Temporal GNN (ST-GNN) architecture in PyTorch, using layers from PyTorch Geometric and PyTorch Geometric Temporal. A GCN or GAT layer followed by a GRU is a strong starting point. [3]
4.  **Model Training:** Train the ST-GNN on the labeled dataset to classify tactical executions.
5.  **Integration:** Serve the trained model via a simple Flask API and call it from the Dash dashboard. Display the GNN's top predicted tactic (and confidence score) in the 2D replay view.

**Outcome:** The dashboard's 2D replay will be enhanced with an AI-powered label that identifies the executed tactic, providing a deeper level of automated analysis.

---

### Phase 5: Automation & Expansion - Fine-Tuning for Scouting
**Goal (Advanced):** Fine-tune a local LLM to automate the generation of structured opponent scouting reports.

**Tasks:**
1.  **Create Fine-Tuning Dataset:** Generate a dataset of several hundred `(input, output)` pairs.
    *   **Input:** A structured summary of an opponent's demo (e.g., JSON with key stats, player positions, GNN-identified tactics).
    *   **Output:** A human-written, high-quality scouting report based on that input.
2.  **Setup Fine-Tuning Environment:** Use Hugging Face libraries like `TRL` and `PEFT` to prepare for training. [23, 24]
3.  **Instruction Tuning:** Format the dataset using an instruction-following template (e.g., "Based on this data, write a scouting report..."). [25, 26]
4.  **Run Fine-Tuning:** Fine-tune a 7B or