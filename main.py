import os
import json
from dotenv import load_dotenv
from typing import TypedDict
from triage_schema import TriageSchema
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore

load_dotenv()

class SampleState(TypedDict):
    user_query: str

graph_builder = StateGraph(
    state_schema=SampleState
)

def testNode(state: SampleState):
    # state["user_query"] = "Hello, it's me, baby.."
    # state["xxxx"] = "Hello, it's me, baby.."
    # return state
    print("Test Node Triggered.")
    return state

def triageNode(state: SampleState):
    print("Triage Node Triggered.")

    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-20b",
        temperature=0.6
    )

    llm = llm.with_structured_output(schema=TriageSchema, method="json_schema")

    messages = [
        SystemMessage(
            content="""
                Analyze the following user query and conversation history. Identify the user's primary intent, sentiment, and whether any PII is present.
            """
        ),
        HumanMessage(content=state['user_query'])
    ]

    # response = llm.invoke(
    #     input=messages
    # )
    # print(f"LLM Response: {response}; type: {type(response)}")
    # print(f"Intent: {response.intent}; Sentiment: {response.sentiment}; PII: {response.pii_detected}")

    response = "This is working...."
    print(f"{response}")

    return state



def retrievalNode(state: SampleState):
    print("Retrieval Node Triggered.")
    query = state["user_query"]

    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}

    hf = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        cache_folder="hf_storage"
    )

    client = QdrantClient(
        url="http://localhost:6333/"
    )
        
    collection_name = "Omni-Channel-CX-RAG-DB"

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=hf
    )

    results = vector_store.similarity_search(
        query=query,
        k=3
    )

    # print(f"Results: {[]}")
    for result in results:
        print(f"{result.page_content}\n\n")


    return state

# Node Registration
graph_builder.add_node(
    node="testNode",
    action=testNode
)
graph_builder.add_node(
    node="triageNode",
    action=triageNode
)
graph_builder.add_node(
    node="retrievalNode",
    action=retrievalNode
)

# Connecting Nodes
graph_builder.add_edge(
    start_key=START,
    end_key="testNode"
)
graph_builder.add_edge(
    start_key="testNode",
    end_key="triageNode"
)
graph_builder.add_edge(
    start_key="triageNode",
    end_key="retrievalNode"
)
graph_builder.add_edge(
    start_key="retrievalNode",
    end_key=END
)

graph = graph_builder.compile()


response = graph.invoke(
    input=SampleState(
        user_query="What are the tools to be used here?"
    )
)

print(response)
