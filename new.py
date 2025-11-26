import time
from dataclasses import dataclass
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

class State(TypedDict):
	boiled: bool
	poured_coffee: bool
	prepared: bool
	served: bool

@dataclass
class Context:
	user_id: str
	user_name: str

def boil_water(state: State):
	print(f"State: {state}")
	print(f"Boiling Water.")
	state['boiled'] = True
	return state

def pour_coffee_soluble(state: State, config: RunnableConfig):
	print(f"State: {state}")
	print("Pouring started.")
	t = config['configurable']['spoon_times']
	print(f"Need to add {t} half-tea spoons of coffee.")
	for i in range(t):
		print("Pouring Instant Coffee")
		time.sleep(1)
        # Simulating 1 second required to pour coffee into the mug
	state['poured_coffee'] = True
	config['configurable']['spoon_times'] = 5
	return state
		
def mix_with_water(state: State):
	print("Mixing Coffee with hot water.")
	print(f"State: {state}")
	state['prepared'] = True
	return state
	
def serve_coffee(state: State, runtime: Runtime[Context]):
	print(f"State: {state}")
	print(f"Coffee is prepared for user: {runtime.context.user_id}")
	state['served'] = True
	print(f"State: {state}")
	print(f"{runtime.context.user_name}, kindly have your coffee.")
	return state

# Graph Initialization
builder = StateGraph(State)

# Node Registration
builder.add_node("BoilWater", boil_water)
builder.add_node("PourSoluble", pour_coffee_soluble)
builder.add_node("Mix", mix_with_water)
builder.add_node("Serve", serve_coffee)

# Node Registration
builder.add_edge(START, "BoilWater")
builder.add_edge("BoilWater", "PourSoluble")
builder.add_edge("PourSoluble", "Mix")
builder.add_edge("Mix", "Serve")
builder.add_edge("Serve", END)

graph = builder.compile()

# User State
state = State(
	boiled=False,
	poured_coffee=False,
	prepared=False,
	served=False
)

# Configurations
config = {
	"configurable": {
		"spoon_times": 3
	}
}

# Context
context = Context(
	user_id="InsCofee123",
	user_name="Neloy"
)

graph.invoke(
	input = state,
	config = config,
	context=context
)
