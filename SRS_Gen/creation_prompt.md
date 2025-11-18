## CONTEXT
I want to create a `Customer Support AI Agent using LangGraph`. I have collected different overviews for the same project. There are some common functionalities in between them but some lack requirements or processes mentioned in others. I want each and every feature mentioned in different data and merge them all into a common `Software Requirements Specification` document. The document should contain all the details in depth that a developer should follow from starting till the delivery phase of the project. 

## PROJECT DESCRIPTION DATA
```md
## Dynamic Customer Support Triage & Resolution Agent

**Detailed Description:**
This agent acts as a first-line, AI-powered customer support specialist. It goes beyond simple chatbots by handling multi-step, complex user issues autonomously.

-   **Problem Solved:** Reduces human agent workload by automatically resolving common-to-complex issues, and intelligently escalating only the truly novel or high-stakes problems.
-   **How it Functions:**
    1.  **Ingestion Node:** Receives a customer query from a chat widget or email.
    2.  **Triage Node:** A small LLM call classifies the query's intent (e.g., `billing_inquiry`, `technical_issue`, `refund_request`).
    3.  **Conditional Edge (Routing):** Based on the intent, the graph routes to different specialized flows.
        -   `billing_inquiry` -> **RAG Node:** The agent retrieves the user's past invoices and payment history from a **Qdrant DB** (which stores customer interaction and transaction data) to understand the context.
        -   `technical_issue` -> **RAG Node:** The agent searches a **Qdrant DB** indexed with technical documentation, tutorials, and past resolved tickets for a solution.
    4.  **Tool Node:** If needed (e.g., for a `refund_request`), the agent uses a tool to call an internal API to check eligibility or process the refund.
    5.  **Synthesis Node:** An LLM synthesizes the information from RAG and tools into a helpful, conversational response.
    6.  **Human Escalation Node:** If the agent cannot resolve the issue after a few attempts (tracked in its state), a **Conditional Edge** routes the entire conversation history to a human agent.
-   **Why it Appeals to Recruiters:** This project showcases a practical, high-value business application. It demonstrates sophisticated **Conditional Edges** for smart routing, a non-trivial **RAG** implementation on real-world data (not just docs), and critical use of **Checkpointing** to persist conversation state for seamless human handoff. The **Memory Layer** ensures the agent remembers the context of the current conversation.
```
```md
## Omni-Channel Support Orchestrator
A production-grade customer support agent that unifies chat, email, and ticket systems into one brain. It triages, answers, executes safe automations (password reset, refund eligibility), and escalates with traceable reasoning and citations.

- How it works: a planner node classifies intent and user profile, retrieval nodes pull product docs, runbooks, and past tickets from QDrant, a tool node executes allowed actions, and an escalation node hands off with a state bundle. Conditional edges route to “clarify,” “tool,” or “human” based on confidence, sensitivity, or account tier.
- QDrant RAG: vector search over product manuals, annotated tickets, macros; metadata filters by product/version/tier; MMR + cross-encoder re-rank for precise context; outputs cite chunks.
- Checkpointing & Memory: per-conversation checkpoints to resume after tool calls or human handoffs; long-term memory stores user preferences, previous resolutions, and account context to personalize next steps.
- Why it impresses: shows LangGraph mastery with smart routing (confidence thresholds and PII triggers), multi-hop retrieval, tool-execution subgraphs, auditability via checkpoints, and grounded support at scale.
```
```md
## Intelligent Customer Service Escalation Agent
A customer support system that autonomously handles tier-1 queries while intelligently escalating complex cases. The agent uses RAG with QDrant to search knowledge bases and past resolution histories. Nodes process customer intent, retrieve solutions, and assess escalation criteria. Conditional edges determine when to escalate based on sentiment analysis and solution confidence scores. Checkpointing ensures no customer context is lost during transfers, while memory maintains conversation history. Demonstrates production-ready customer service automation with smart routing between support tiers.
```

```md
## Intelligent Customer Support Agent for E-Commerce
This project addresses the challenge of providing personalized, efficient customer support in e-commerce platforms where queries range from product recommendations to order troubleshooting. The agent integrates an LLM for natural language processing, with nodes for query classification, knowledge retrieval, and response generation. Edges connect these nodes, while conditional edges route based on query type (e.g., routing to a refund node if sentiment analysis detects dissatisfaction). RAG uses QDrant DB to vector-search a product catalog and FAQ database for accurate, context-aware responses. Checkpointing saves session states for multi-turn interactions, and a memory layer retains user history for personalized follow-ups. It appeals to AI recruiters by showcasing LangGraph's conditional routing for dynamic workflows, checkpointing for persistent state management, and RAG integration for scalable knowledge retrieval, demonstrating sophisticated agentic design in customer service automation.
```

## TASK
You need to approach the provided project details step by step internally, understand and analyze the client needs, extract the features from all resources. Finally, generate a `SRS` document and return the content in `.md` file formation.

## RULES
- Add the following sections while generating the `SRS` documentation.
    - Project Title
    - Project Overview
    - Problem Statement
    - Tech stacks/ Tools to be used
    - Core Workflow 
    - Deliverables
- When descriptions conflict or overlap, prioritize the most detailed version and consolidate similar features.
- The `Title` of the project should be `Professional`, `Appealing`, `Eye-catching` and memorable while reflecting the project's core purpose.
- The `Project Overview` should contain a summarized version of the whole project that gives a clear understanding within a short time.
- The `Problem Statement` should have the following characteristics: - 
    - The Problem
    - How this solution solves the problem.
    - Why someone should consider using the project.
- Break down the `Core Workflow` into logical development phases such as Requirements, Design, Implementation, Testing, and Deployment.
- Describe each `Phase` of the workflow thoroughly. 
- Organize the content into logical sections and key concepts.
- Provide comprehensive but focused details covering all functional and non-functional requirements to make the `Development` phase easier for the `Developer`.
- Formatting:
    - Use Markdown headings, bold text, and lists where helpful.
    - In bullet/numbered lists only, make labels before the colon bold (e.g., **Environment:** Production).
- Writing style:
    - Sentences should be short, concise, easy, clean, and in a professional tone.
    - Be comprehensive yet concise; avoid repetition.
- In `Tech Stack / Tools`, prefer technologies mentioned in the provided descriptions. If you propose alternatives, mark them as **Recommendations** and justify briefly.
- Provide a clear understanding of the `Deliverables` to the client.
- Mention the specific list of items/artifacts/files to be `Delivered`. 
- Return me with the whole response as a `Markdown` within **4 Backticks**(````<generated_markdown_content>````).
- Strictly keep the generated content within **4 Backticks**.

## EXAMPLE
Use the example below for structure and level-of-detail only. Do not copy vendor names, tools, or constraints unless they are present in the provided descriptions.
```md
# AI-Powered Customer Feedback Automation

## Project Overview

This project automates Artisan Corner's customer feedback processing by replacing manual sorting with an intelligent AI-driven workflow. The solution uses n8n to connect Tally.so web forms with Hugging Face AI services for sentiment analysis and image recognition, Supabase for data storage, and Discord for team notifications. Key benefits include faster response times to urgent issues, reduced manual workload, consistent classification of all feedback, and valuable insights into customer sentiment trends through centralized data tracking.

---

## Problem Statement
Our current process is as follows:
1.  A customer fills out a web form with their name, email, a message, and an optional image upload (e.g., showing a damaged product).
2.  An email notification is sent to a general `support@artisancorner.example` inbox.
3.  A team member reads the email, manually determines if it's a positive review, a general question, or an urgent issue, and then forwards it to the correct department or adds it to a spreadsheet.

This manual process is slow, prone to error, and we are not effectively tracking sentiment or common issues over time.

---

## Tech Stack (Open to Alternatives if Justified)

To ensure this project is feasible and cost-effective, we want to use services with free tiers.

*   **Automation Platform:** **n8n** (You can use the free n8n Cloud tier or self-host).
*   **Web Form:** **Tally.so**. It's free, user-friendly, and has excellent webhook support. You will need to create the form yourself.
    *   *Fields:* Name (Text), Email (Email), Message (Text Area), Product Image (File Upload).
*   **Database:** **Supabase**. It provides a free PostgreSQL database which is perfect for our needs. You will need to design a simple table schema to store the submissions.
*   **AI Functionality (NLP & Image Recognition):** **Hugging Face Inference API**. It offers a generous free tier for accessing thousands of pre-trained models.
    *   *For NLP:* Use a popular `sentiment-analysis` model.
    *   *For Image Recognition:* Use an `object-detection` or `image-classification` model.
*   **Notifications:** **Discord**. It's free and easy to set up incoming webhooks for sending formatted messages to different channels.

---

## Core Workflow

We need an end-to-end n8n workflow that automates the entire process. Here is the step-by-step logic we envision:

1.  **Trigger: Web Form Submission**
    *   The workflow must start when a customer submits our "Customer Feedback Form". This form will send its data via a webhook.

2.  **AI Analysis (NLP) on the Message**
    *   The text from the customer's message should be sent to an AI service to perform two tasks:
        *   **Sentiment Analysis:** Determine if the message is `Positive`, `Negative`, or `Neutral`.
        *   **Keyword Extraction/Categorization:** Identify key topics like "shipping," "damage," "quality," "praise," or "question."

3.  **AI Analysis (Image Recognition) on the Uploaded Image**
    *   If a customer has uploaded an image, the workflow should send the image URL to an AI service to analyze its content.
    *   The primary goal is to identify if the image contains things like "broken pottery," "cracked wood," or "packaging," which would indicate a damaged product issue.

4.  **Data Consolidation & Storage**
    *   All the data—original form submission, sentiment score, text category, and image analysis tags—must be collected.
    *   This consolidated record should then be inserted as a new row into our database for future reporting and analysis.

5.  **Intelligent Routing (Decision Making)**
    *   Based on the AI analysis, the workflow needs to branch into different paths:
        *   **Path A (Urgent Issue):** If sentiment is `Negative` AND the image analysis detects "damage" or the text mentions "broken"/"damaged," send a high-priority, formatted notification to our internal `#support-urgent` channel.
        *   **Path B (Positive Feedback):** If sentiment is `Positive`, send a notification to our `#happy-customers` channel so the marketing team can see it.
        *   **Path C (General Inquiry):** For all other cases (e.g., `Neutral` sentiment, questions), send a standard notification to the `#general-inquiries` channel.

---

## Expected Deliverables
1.  A fully functional and tested n8n workflow JSON file.
2.  The SQL `CREATE TABLE` statement for the Supabase table schema you designed.
3.  Brief (1-2 page) documentation explaining:
    *   How to set up the credentials (API keys, webhook URLs).
    *   An overview of the workflow logic.
    *   The names of the Hugging Face models you used.
4.  A short screen recording (Loom or similar) demonstrating the workflow in action from form submission to Discord notification.
```

## RESPONSE RETURN FORMAT
````md
    <generated_markdown_content>
````