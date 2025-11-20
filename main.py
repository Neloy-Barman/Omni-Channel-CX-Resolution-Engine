import os
import json
from dotenv import load_dotenv
from typing import TypedDict
from triage_schema import TriageSchema
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage

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

    response = llm.invoke(
        input=messages
    )
    print(f"LLM Response: {response}; type: {type(response)}")
    print(f"Intent: {response.intent}; Sentiment: {response.sentiment}; PII: {response.pii_detected}")

    # print(f"{response}")

    return state

graph_builder.add_node(
    node="testNode",
    action=testNode
)
graph_builder.add_node(
    node="triageNode",
    action=triageNode
)

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
    end_key=END
)

graph = graph_builder.compile()


response = graph.invoke(
    input=SampleState(
        user_query="Hello, how are you?"
    )
)

print(response)