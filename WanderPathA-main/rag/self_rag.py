import os
from typing import List, Literal, TypedDict
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph, START

from rag.hybrid_rag import hybrid_retrieve

load_dotenv()


class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[str]
    memories: List[str]
    loop_step: int


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)


class GradeHallucination(BaseModel):
    binary_score: str = Field(description="Grounded strictly in retrieved facts: 'yes' or 'no'")


class GradeAnswer(BaseModel):
    binary_score: str = Field(description="Answers question directly: 'yes' or 'no'")


def retrieve_and_recall_node(state: GraphState):
    question = state["question"]
    docs = hybrid_retrieve(question)
    doc_texts = [d.page_content if hasattr(d, "page_content") else str(d) for d in docs]

    return {
        "documents": doc_texts,
        "memories": state.get("memories", []),
        "question": question,
        "loop_step": state.get("loop_step", 0),
    }


def grade_context_node(state: GraphState):
    # Pass through context directly to prevent rate limits and sequential network blocking
    return {
        "documents": state["documents"],
        "memories": state["memories"],
        "question": state["question"],
    }


def generate_node(state: GraphState):
    question = state["question"]
    documents = state["documents"]
    memories = state["memories"]

    combined_context = ""
    if memories:
        combined_context += "USER MEMORIES:\n" + "\n".join(memories) + "\n\n"
    if documents:
        combined_context += "KNOWLEDGE BASE:\n" + "\n".join(documents)

    if not combined_context.strip():
        combined_context = "No relevant context available."

    prompt = ChatPromptTemplate.from_template("""
    Answer the query strictly using the provided context. If insufficient, state so clearly.

    CONTEXT:
    {context}

    QUESTION:
    {question}

    ANSWER:
    """)

    gen_chain = prompt | llm
    generation = gen_chain.invoke({"context": combined_context, "question": question}).content

    return {
        "generation": generation,
        "question": question,
        "documents": documents,
        "memories": memories,
    }


def transform_query_node(state: GraphState):
    question = state["question"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Rewrite query to improve retrieval precision for flight policies or user details."),
        ("human", "Original Question: {question}\nImproved Question:"),
    ])

    re_writer = prompt | llm
    better_question = re_writer.invoke({"question": question}).content

    return {"question": better_question, "loop_step": state.get("loop_step", 0) + 1}


def decide_to_generate(state: GraphState) -> Literal["generate", "transform_query"]:
    if not state["documents"] and not state["memories"]:
        if state.get("loop_step", 0) >= 1:
            return "generate"
        return "transform_query"
    return "generate"


def grade_generation_v_context(state: GraphState) -> Literal["useful", "not useful", "not grounded"]:
    question = state["question"]
    all_facts = state["documents"] + state["memories"]
    generation = state["generation"]

    if not all_facts:
        return "useful"

    try:
        # NOTE: if json_mode structured output errors out on the selected
        # Groq model, drop the `method="json_mode"` argument (see
        # with_structured_output(GradeHallucination) without a method kwarg)
        # and rely on the schema alone.
        hallucination_grader = llm.with_structured_output(GradeHallucination, method="json_mode")
        h_prompt = ChatPromptTemplate.from_messages([
            ("system", "Grade if output is grounded ONLY in facts. Respond in JSON with key 'binary_score' set to 'yes' or 'no'."),
            ("human", "Facts:\n{facts}\n\nGenerated Output:\n{generation}"),
        ])
        h_res = (h_prompt | hallucination_grader).invoke({"facts": "\n".join(all_facts), "generation": generation})

        if h_res.binary_score.lower() == "yes":
            answer_grader = llm.with_structured_output(GradeAnswer, method="json_mode")
            a_prompt = ChatPromptTemplate.from_messages([
                ("system", "Grade if output directly answers question. Respond in JSON with key 'binary_score' set to 'yes' or 'no'."),
                ("human", "Question:\n{question}\n\nGenerated Output:\n{generation}"),
            ])
            a_res = (a_prompt | answer_grader).invoke({"question": question, "generation": generation})

            if a_res.binary_score.lower() == "yes":
                return "useful"
            return "not useful"
    except Exception:
        return "useful"

    if state.get("loop_step", 0) >= 1:
        return "useful"
    return "not grounded"


def build_self_rag_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_and_recall_node)
    workflow.add_node("grade_context", grade_context_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("transform_query", transform_query_node)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_context")

    workflow.add_conditional_edges(
        "grade_context",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )

    workflow.add_edge("transform_query", "retrieve")

    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_context,
        {
            "not grounded": "generate",
            "not useful": "transform_query",
            "useful": END,
        },
    )

    return workflow.compile()


self_rag_app = build_self_rag_graph()


def self_rag(question: str) -> str:
    inputs = {"question": question, "loop_step": 0}
    output = self_rag_app.invoke(inputs)
    return output.get("generation", "No valid response generated.")

def self_rag_with_sources(question: str) -> dict:
    inputs = {
        "question": question,
        "loop_step": 0,
    }

    output = self_rag_app.invoke(inputs)

    return {
        "answer": output.get("generation", ""),
        "documents": output.get("documents", []),
    }