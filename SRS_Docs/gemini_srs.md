# Intelligent Customer Resolution Engine

## Project Overview
This document outlines the Software Requirements Specification (SRS) for the **Intelligent Customer Resolution Engine**, a state-of-the-art customer support agent built using LangGraph. The agent will serve as a sophisticated, AI-powered first line of support, capable of unifying interactions from multiple channels (chat, email, ticketing systems) into a single, intelligent workflow. It will autonomously triage inquiries, resolve a wide range of common to complex issues, execute automated tasks, and intelligently escalate to human agents only when necessary. By leveraging advanced Retrieval-Augmented Generation (RAG), tool use, and dynamic routing, this system aims to significantly enhance support efficiency, reduce operational costs, and improve overall customer satisfaction.

---

## Problem Statement

### The Problem
Modern businesses face an ever-increasing volume of customer support inquiries across multiple channels. The traditional, human-centric support model is struggling to keep pace, leading to several critical issues:
*   **High Operational Costs:** Scaling a human support team is expensive and time-consuming.
*   **Slow Response Times:** Customers often face long wait times, especially during peak hours, leading to frustration.
*   **Inconsistent Support Quality:** Service quality can vary between agents, and knowledge is often siloed.
*   **Lost Context:** When a query is escalated or transferred between agents or tiers, the customer is often forced to repeat their issue, creating a poor experience.
*   **Agent Burnout:** Human agents are frequently bogged down by repetitive, low-level queries, preventing them from focusing on high-impact, complex problems.

### How this solution solves the problem
The Intelligent Customer Resolution Engine directly addresses these challenges by introducing an autonomous layer of support.
1.  **Automation at Scale:** The agent can handle a vast number of concurrent conversations 24/7, instantly triaging and resolving a significant percentage of incoming queries without human intervention.
2.  **Intelligent Triage & Routing:** It uses AI to immediately understand a customer's intent, sentiment, and profile, routing the query through the most efficient resolution path.
3.  **Context-Aware Resolution:** By using a vector database (Qdrant) and RAG, the agent accesses a comprehensive knowledge base—including product docs, FAQs, past tickets, and user history—to provide accurate, relevant, and personalized solutions.
4.  **Seamless Escalation:** When human intervention is required, the agent uses checkpointing to bundle the entire conversation history, analysis, and retrieved context, providing the human agent with a complete picture and eliminating the need for repetition.

### Why someone should consider using the project
This project represents a significant leap forward from simple chatbots. It demonstrates a production-grade, agentic system that delivers tangible business value. Adopting this solution will lead to dramatically reduced support costs, faster resolution times, a more consistent customer experience, and empowered human agents who can focus on strategic, value-adding interactions. It showcases mastery of sophisticated AI concepts like conditional agentic routing, multi-source RAG, and persistent state management for robust, real-world applications.

---

## Tech stacks/ Tools to be used

*   **Core Framework:** **LangGraph** will be used to construct the stateful, multi-agent graph.
*   **Programming Language:** **Python 3.10+**.
*   **Vector Database:** **Qdrant**. It will store vectorized versions of all knowledge sources for fast and scalable similarity search.
*   **Large Language Models (LLMs):**
    *   **Triage LLM:** A smaller, faster model (e.g., from Groq, or a fine-tuned open-source model like Llama 3 8B) for initial classification of intent, sentiment, and PII detection.
    *   **Synthesis & Reasoning LLM:** A more powerful model (e.g., GPT-4o, Claude 3 Opus) for synthesizing information, generating high-quality responses, and complex reasoning.
*   **Data Sources / Integrations:**
    *   **Channels:** APIs to connect with web chat widgets, email servers (IMAP/SMTP), and existing ticketing systems (e.g., Zendesk, Jira via APIs).
    *   **Knowledge Bases:** Connectors to ingest product documentation, FAQs, runbooks, annotated past tickets, and product catalogs into Qdrant.
    *   **Internal Systems:** Secure API wrappers for internal tools (e.g., refund processing, order lookup, password reset).
*   **Recommendation:**
    *   **Re-ranking:** A **Cross-Encoder model** (e.g., from the `sentence-transformers` library) should be used after the initial vector search to re-rank the top K retrieved documents for maximum relevance.

---

## Core Workflow

The project will be developed through a structured, phased approach. Each step is described in detail to guide implementation.

### Phase 1: Requirements & Design

This phase focuses on architecting the agent's logic and data structures.

#### 1.1. Graph State Definition
The core state object, managed by LangGraph's `StateGraph`, will be a Python `TypedDict`. This ensures type safety and clarity. Checkpointing will be configured to automatically persist this state.

```python
from typing import List, TypedDict, Optional

class AgentState(TypedDict):
    conversation_id: str
    user_id: str
    user_query: str
    conversation_history: List[dict] # e.g., [{"role": "user", "content": "..."}]
    
    # Fields populated by Triage Node
    intent: Optional[str]
    sentiment: Optional[str]
    pii_detected: bool
    user_profile: Optional[dict] # { "account_tier": "premium", "past_resolutions": [...] }

    # Fields populated by RAG / Tool Nodes
    retrieved_context: Optional[List[dict]] # { "source": "doc.pdf", "content": "..." }
    tool_call_result: Optional[str]
    
    # Control flow fields
    confidence_score: float
    escalation_counter: int
    response: Optional[str] # The final response to send to the user
```

#### 1.2. Node Implementation Logic
Each node is a Python function that accepts the `AgentState` dictionary, performs its logic, and returns a dictionary with the fields it has modified.

*   **Ingestion Node (`ingest_query`)**
    *   **Purpose:** The entry point for all new user requests.
    *   **Implementation:** This function receives raw input (e.g., from a FastAPI request body containing `user_id` and `query`). It initializes the `AgentState` with a unique `conversation_id`, the `user_id`, the `user_query`, and sets default values for other fields (e.g., `escalation_counter = 0`, `pii_detected = False`). It also appends the current user query to the `conversation_history`.

*   **Triage Node (`triage_request`)**
    *   **Purpose:** To understand the user's query and enrich the state with metadata.
    *   **Implementation:**
        1.  **Construct a prompt** for the Triage LLM. The prompt must instruct the model to return a structured JSON object.
            *   *Example Prompt Snippet:* `"Analyze the following user query and conversation history. Identify the user's primary intent, sentiment, and whether any PII is present. Respond with a JSON object with keys: 'intent', 'sentiment', 'pii_detected'. Allowed intents are: ['billing_inquiry', 'technical_issue', 'refund_request', 'product_recommendation', 'general_question']."`
        2.  **Call the Triage LLM** with the prompt and parse the JSON response. Handle potential parsing errors.
        3.  **Update the state** with the `intent`, `sentiment`, and `pii_detected` values.
        4.  **Fetch User Profile:** Use the `user_id` from the state to query a long-term memory database (e.g., a simple key-value store or SQL DB) to retrieve the `user_profile` and add it to the state.

*   **Retrieval Node (`retrieve_knowledge`)**
    *   **Purpose:** To find relevant information from the knowledge base to answer the query.
    *   **Implementation:**
        1.  **Vectorize Query:** Convert the `user_query` into a vector embedding using the same model used for data ingestion.
        2.  **Build Qdrant Filter:** Create a filter object based on the current state. For example: `Filter(must=[FieldCondition(key="metadata.doc_type", match=Value(value=state['intent']))])`. This narrows the search to relevant document types.
        3.  **Execute Vector Search:** Call the Qdrant client's `search()` method with the query vector and filter. Retrieve the top K results (e.g., K=10). Use MMR (`search_params=SearchParams(hnsw_ef=128, exact=False, top_k=10, mmr=True)`) to ensure diversity.
        4.  **Re-rank Results:** Pass the original `user_query` and the text content of the K retrieved documents to a Cross-Encoder model. The model will return a list of relevance scores.
        5.  **Select Top N:** Sort the documents by their new cross-encoder scores and select the top N (e.g., N=3) most relevant ones.
        6.  **Update State:** Format the top N documents, including their metadata (e.g., source citations), and update the `retrieved_context` field in the state.

*   **Tool Node (`execute_tool`)**
    *   **Purpose:** To execute predefined, safe internal actions.
    *   **Implementation:** This node acts as a dispatcher.
        1.  Use a dictionary to map intents to tool functions: `tool_map = {'refund_request': process_refund_tool, 'order_status': check_order_status_tool}`.
        2.  Look up the appropriate tool function based on `state['intent']`.
        3.  Call the selected function, passing necessary parameters from the state (e.g., `user_id`).
        4.  The tool function itself will contain the logic to call the internal API, handle authentication, and parse the response. It should include robust error handling (e.g., `try...except` blocks).
        5.  **Update State:** The string output from the tool (e.g., "Refund for order #123 processed successfully." or "Error: User not eligible for refund.") is saved to the `tool_call_result` field in the state.

*   **Synthesis Node (`generate_response`)**
    *   **Purpose:** To create the final, human-like response for the user.
    *   **Implementation:**
        1.  **Construct a detailed prompt** for the Synthesis LLM. This is the most critical prompt. It must include placeholders for all relevant context.
            *   *Example Prompt Snippet:* `"You are a helpful customer support agent. Given the full conversation history, the following context from our knowledge base, and the result of any tools used, formulate a clear and helpful response to the user's latest query. If you use information from the knowledge base, cite the source (e.g., '[Source: product_manual.pdf, page 4]'). \n\n Conversation History: {conversation_history} \n\n Knowledge Base Context: {retrieved_context} \n\n Tool Result: {tool_call_result} \n\n User Query: {user_query} \n\n Your Response:"`
        2.  **Call the Synthesis LLM** with the fully formatted prompt.
        3.  **Update State:** Store the LLM's generated text in the `response` field. Also, append both the agent's response and the previous user query to the `conversation_history`.

*   **Human Escalation Node (`prepare_for_handoff`)**
    *   **Purpose:** To cleanly transfer the conversation to a human agent.
    *   **Implementation:**
        1.  **Create State Bundle:** Serialize the key fields of the `AgentState` into a human-readable Markdown string. Include a summary, the full chat history, and all retrieved context.
        2.  **Create Ticket:** Make an API call to the target support system (e.g., Zendesk API). Create a new ticket, setting the ticket's description to the generated state bundle and assigning it to the appropriate human agent queue.
        3.  **Inform User:** Update the `response` field in the state with a message like, "I'm connecting you with a human agent who can better assist you. They will have the full context of our conversation."

#### 1.3. Edge Logic Implementation
Conditional edges are Python functions that take the `AgentState` and return a string corresponding to the name of the next node.

*   **Router after Triage (`route_after_triage`)**
    *   **Logic:**
        ```python
        def route_after_triage(state: AgentState) -> str:
            if state["pii_detected"] and state["intent"] in ["refund_request", "billing_inquiry"]:
                return "human_escalation_node"
            if state["intent"] in ["technical_issue", "product_recommendation"]:
                return "retrieve_knowledge_node"
            if state["intent"] in ["refund_request", "order_status"]:
                return "execute_tool_node"
            else:
                return "retrieve_knowledge_node" # Default to RAG for general questions
        ```

*   **Router after Action (`decide_next_step`)**
    *   This function runs after the RAG or Tool nodes.
    *   **Logic:**
        ```python
        def decide_next_step(state: AgentState) -> str:
            state["escalation_counter"] += 1
            if state["escalation_counter"] > 2:
                return "human_escalation_node"

            # A simple confidence check could be the length/quality of retrieved context
            if state["retrieved_context"] and len(state["retrieved_context"]) > 0:
                state["confidence_score"] = 0.9 # High confidence
            elif state["tool_call_result"] and "Error" not in state["tool_call_result"]:
                state["confidence_score"] = 0.95 # High confidence
            else:
                state["confidence_score"] = 0.4 # Low confidence

            if state["confidence_score"] > 0.8:
                return "generate_response_node"
            else:
                # Could route to a 'clarification_node' or escalate
                return "human_escalation_node" 
        ```

### Phase 2: Implementation

*   **Step 1: Environment & Data Setup:**
    *   **Dependencies:** Create a `requirements.txt` file: `langchain`, `langgraph`, `qdrant-client`, `fastapi`, `uvicorn`, `sentence-transformers`, `python-dotenv`, `groq` (or other LLM SDKs).
    *   **Qdrant Ingestion:** Write a `ingest.py` script. This script will:
        1.  Scan a local directory for documentation files (.md, .txt, .pdf).
        2.  Use `RecursiveCharacterTextSplitter` to break documents into chunks.
        3.  Initialize a `SentenceTransformer` model (e.g., `'all-MiniLM-L6-v2'`).
        4.  For each chunk, generate a vector embedding.
        5.  Use `qdrant_client.upsert()` to load a `PointStruct` containing the vector and a `payload` with the text content and metadata (e.g., `{"source": file_path, "chunk_id": i}`).

*   **Step 2: Graph & API Implementation:**
    *   **Graph Assembly:** In a `graph.py` file, define the `AgentState`, all node functions, and the conditional edge functions.
    *   Instantiate the `StateGraph`: `workflow = StateGraph(AgentState)`.
    *   Add nodes: `workflow.add_node("triage", triage_request)`.
    *   Set entry point: `workflow.set_entry_point("triage")`.
    *   Add conditional edges: `workflow.add_conditional_edges("triage", route_after_triage, {"retrieve_knowledge_node": "retrieve_knowledge", ...})`.
    *   Compile the graph: `app = workflow.compile(checkpointer=memory_saver)`.
    *   **API Wrapper:** In a `main.py` file, create a FastAPI application. Define a `/chat` endpoint that accepts a JSON body. This endpoint will invoke the compiled LangGraph app (`app.stream(...)` or `app.invoke(...)`) with the user's input and return the final `response` from the state.

### Phase 3: Testing

*   **Unit Testing:** Use `pytest`.
    *   **Example:** For the `triage_node`, create a mock LLM that returns a known JSON string. Call the node with a sample state and `assert` that the state is correctly updated with the intent and sentiment from the mock response.
*   **Integration Testing:**
    *   **Example:** Create a test for the RAG flow. Mock the `qdrant_client.search` to return a predefined list of documents. Invoke the graph from the entry point. `assert` that the `retrieve_knowledge_node` is called and that the `generate_response_node`'s prompt includes content from the mocked documents.
*   **End-to-End Testing & Evaluation:**
    *   Create a `test_e2e.py` script that uses the `requests` library to send queries to the running FastAPI application.
    *   Define a "golden dataset" in a CSV file with columns: `query`, `expected_intent`, `expected_response_keywords`.
    *   The script will iterate through the dataset, send each query to the API, and check if the agent's `intent` classification and final response meet the criteria. Tools like `LangSmith` can be integrated to automatically trace and evaluate these runs for faithfulness and accuracy.

### Phase 4: Deployment & Delivery

*   **Containerization:**
    *   The `Dockerfile` will define the steps to build the application image. It will start from a Python base image, copy the `requirements.txt` and install dependencies, then copy the rest of the application code (`main.py`, `graph.py`, etc.), and finally set the `CMD` to run the Uvicorn server.
*   **CI/CD Pipeline:**
    *   Set up a GitHub Actions workflow (`.github/workflows/deploy.yml`).
    *   **On push to `main`:** The workflow will trigger, run all `pytest` tests, build the Docker image, tag it, push it to a container registry (e.g., AWS ECR), and finally call a deployment script or use a provider-specific action to update the service (e.g., `aws ecs update-service --force-new-deployment`).
*   **Monitoring & Logging:**
    *   Within the Python code, use the standard `logging` library.
    *   In each node, log critical information with the `conversation_id`, such as the entry into the node, the result of the LLM call, the routing decision, and any errors. Configure the logging output to be JSON-formatted for easy parsing by services like Datadog or an ELK stack.

---

## Deliverables

Upon completion, the following artifacts will be delivered:

1.  **Source Code:**
    *   A complete, well-documented Python project repository containing the LangGraph implementation (`graph.py`), API wrapper (`main.py`), and data ingestion scripts (`ingest.py`).

2.  **Deployment Artifacts:**
    *   `Dockerfile` for containerizing the application.
    *   `docker-compose.yml` for easy local deployment and testing of the agent and Qdrant.
    *   `requirements.txt` listing all Python dependencies.
    *   Configuration files (e.g., `.env.example`) for managing environment variables (API keys, DB connections).

3.  **Documentation:**
    *   **This SRS Document:** The finalized version of this specification.
    *   **Setup & Deployment Guide:** A `README.md` file with clear, step-by-step instructions for setting up the environment, running the agent locally via Docker Compose, and deploying it.
    *   **Knowledge Base Management Guide:** Instructions on how to format, process, and ingest new documents into the Qdrant database to keep the agent's knowledge up-to-date.
    *   **API Documentation:** An auto-generated Swagger/OpenAPI UI (from FastAPI) detailing the `/chat` endpoint, expected request body, and response format.

4.  **Demonstration:**
    *   A short screen recording (~5-10 minutes) demonstrating the agent's capabilities across several key scenarios:
        *   A successful technical issue resolution using RAG.
        *   A successful billing inquiry using a tool.
        *   An intelligent escalation to a human agent due to low confidence or negative sentiment.