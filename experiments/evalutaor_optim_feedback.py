from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os
from typing_extensions import TypedDict
from IPython.display import Image, display
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal
from langgraph.types import Command, interrupt


load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key= openai_key)


class Feedback(BaseModel):
    grade: Literal["funny","not funny"] = Field(
        description="The grade of the joke, either funny or not funny"
    )
    feedback: str = Field(
        description="The feedback for the joke, either funny or not funny"
    )

evaluator = llm.with_structured_output(Feedback)

#graph state
class State(TypedDict):
    topic: str
    joke: str
    feedback: str
    funny_or_not_funny: str

#nodes
def llm_call_generation(state: State):
    """ Generate a joke based on the topic provided in the state.
    """
    print("state",state)
    if state.get("grade") == "not_funny":

        msg= llm.invoke(f"generate a funny joke {state['topic']} but take into consideration the feedback: {state['feedback']}")

    else:
        msg= llm.invoke(f"generate a joke on the topic {state['topic']} ")

    return {"joke":msg.content}


def llm_call_evaluator(state: State):
    """ Evaluate the joke generated in the previous step."""
    print("joke",state["joke"])
    feedback = input("how is the joke?")
    # structured_result = evaluator.invoke(f"grade this joke: {state['joke']}")
    grade= input("write funny or not_funny")
    state["funny_or_not_funny"] = grade
    state["feedback"] = feedback
    return {
        "funny_or_not_funny": grade,
        "feedback": feedback,
    }



#conditional edge
def route_joke(state: State):
    if state["funny_or_not_funny"] == "funny":
        return "Accepted"
    else:
        return "Rejected"


#adding nodes

workflow = StateGraph(State)
workflow.add_node("llm_call_generation",llm_call_generation)
workflow.add_node("llm_call_evaluator",llm_call_evaluator)
workflow.add_node("route_joke",route_joke)

#adding edges
workflow.add_edge(START,"llm_call_generation")
workflow.add_edge("llm_call_generation","llm_call_evaluator")
workflow.add_conditional_edges("llm_call_evaluator", route_joke,{"Accepted": END, "Rejected": "llm_call_generation"})

#compile
chain= workflow.compile()

state= chain.invoke({"topic":"cats"})
print(state)
print(state["joke"])
print(state["feedback"])

