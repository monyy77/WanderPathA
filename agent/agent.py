import asyncio
from pyexpat.errors import messages
from unittest import result

from matplotlib.pyplot import step
from memory import router
from memory.fact_extractor_llm import FactExtractorLLM
from memory.memory_item_factory import MemoryItemFactory
from pydantic import ValidationError
from dataclasses import dataclass
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from .schema import (
    ACTION_INPUT_SCHEMAS,
    AgentStep,
    build_agent_step_model,
    TERMINAL_ACTIONS,
    MAX_STEPS,
)
from memory.scratchpad import ShortTermMemory, process_customer_message
from Context_eval.context_strategies import zone_based_pruning
from memory.metadata_builder import MetadataBuilder

from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.consolidation import ConsolidationLayer

load_dotenv()


@dataclass
class AgentContext:
    user_id: str


@dataclass
class ToolRuntimeShim:
    context: AgentContext


def build_system_prompt(tool_names):

    tool_list = "\n".join(tool_names)

    return f"""
You are a constrained travel support agent.

Use ONLY these tools:
{tool_list}
Additional Instructions:
1. Do NOT retry calling a tool if you already received an Observation from it.
2. Once you have gathered enough information to answer the user's question, set your action to 'final_answer' and provide the final response in 'action_input.answer'.
3. Do NOT invent or call tools that are not listed above.

Think step by step and return only the structured response.
"""

# def build_structured_model():
#     return init_chat_model(
#         model="google_genai:gemini-3.5-flash-lite",
#         max_tokens=1024,
#         max_retries=3,
#     ).with_structured_output(AgentStep)

#groq
def build_structured_model(action_names):
    """Rebuilds the structured-output schema from whatever tools are
    live right now, so a runtime tool-list change (e.g. VIP unlock)
    immediately changes what the LLM is allowed to output."""
    step_model = build_agent_step_model(action_names)
    return init_chat_model(
        model="llama-3.3-70b-versatile",
        model_provider="groq",
        max_tokens=1024,
        max_retries=3,
    ).with_structured_output(step_model)

#  # Issue 6
async def discover_tools(client):
    """Dynamically fetches and registers available tools from the MCP Client."""
    tools_list = await client.get_tools()
    # turns from list to dict
    tools_dict = {tool.name: tool for tool in tools_list}

    return tools_dict  # Dict: {tool_name: tool_instance}

#   # Issue  10    
def validate_step(step, tools) -> bool:
    return step.action in TERMINAL_ACTIONS or step.action in tools

#  # Issue 7 
#  Issue #7: Tool Execution Engine
async def tool_call(step: AgentStep, tools: dict, context: AgentContext = None):
    """Validates payload schema, injects runtime context, and executes tool."""
    tool = tools[step.action]

    payload = step.action_input

    # 1. Pydantic validation if schema exists
    schema_cls = ACTION_INPUT_SCHEMAS.get(step.action)
    if schema_cls:
        validated_input = schema_cls(**step.action_input)
        payload = validated_input.model_dump()

    # 2. Inject context (user_id) if missing
    if context and isinstance(payload, dict):
        if step.action in {
            "get_booking_history",
            "get_customer_profile",
        }:
            payload.setdefault("user_id", context.user_id)
    # 3. Asynchronous execution
    result = await tool.ainvoke(payload)
    return result

def handle_final_action(step):

    if step.action == "final_answer":
        print(step.action_input["answer"])
        return True

    if step.action == "end_conversation":
        if step.action_input:
            print(step.action_input.get("answer", "Goodbye!"))
        else:
            print("Goodbye!")
        return True

    if step.action == "escalate":
        print("Escalating to human support...")
        return True

    return False

#observation
def handle_tool_result(messages, step, result):
    print(f"Observation from {step.action}: {result}")
    messages.append(
        HumanMessage(
            content=f"Observation from {step.action}: {result}"
        )
    )

conversation_history = {}
known_tools_by_user = {}
short_term_memories = {}

episodic_memories = {}
semantic_memories = {}
consolidation_layers = {}

routers = {}

async def run_agent(client, user_input: str, user_id: str = "C001"):

    tools = await discover_tools(client)

    current_tool_names = set(tools.keys())

    context = AgentContext(user_id=user_id)

    if user_id not in short_term_memories:
        short_term_memories[user_id] = ShortTermMemory()

    memory = short_term_memories[user_id]

    if user_id not in episodic_memories:
        episodic_memories[user_id] = EpisodicMemory()

    if user_id not in semantic_memories:
        semantic_memories[user_id] = SemanticMemory()

    if user_id not in consolidation_layers:
        consolidation_layers[user_id] = ConsolidationLayer(
            episodic_store=episodic_memories[user_id],
            semantic_store=semantic_memories[user_id],
            llm=FactExtractorLLM(),
        )

    if user_id not in routers:
        router_llm = router.RouterLLM()

        routers[user_id] = router.PromoteOrDropRouter(
            episodic_store=episodic_memories[user_id],
            short_term=memory,
            llm=router_llm,
        )

    system_prompt = build_system_prompt(sorted(current_tool_names))
    model = build_structured_model(list(current_tool_names))

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            SystemMessage(content=system_prompt)
        ]
    else:
        previous_tool_names = known_tools_by_user.get(user_id, current_tool_names)
        newly_available = current_tool_names - previous_tool_names
        if newly_available:
            # Genuine runtime tool-list change mid-conversation (e.g. the
            # customer was just upgraded to VIP). Refresh the system
            # prompt in place and drop a notice into the transcript so
            # the model knows what's new — no reset, no reconnect.
            conversation_history[user_id][0] = SystemMessage(content=system_prompt)
            conversation_history[user_id].append(
                HumanMessage(
                    content=(
                        "SYSTEM NOTICE: New tools just became available: "
                        f"{', '.join(sorted(newly_available))}. "
                        "You may use them starting now if relevant."
                    )
                )
            )
            print(
                f"\n[agent] Tool list changed mid-conversation for {user_id}: "
                f"+{sorted(newly_available)}"
            )

    known_tools_by_user[user_id] = current_tool_names

    messages = conversation_history[user_id]

    memory.messages.clear()
    memory.messages.extend(messages)

    user_message = HumanMessage(content=user_input)

    messages.append(user_message)
    memory.add(user_message)

    memory_item = MemoryItemFactory.from_message(
        user_message,
        metadata=MetadataBuilder.build(
            entity_type="customer",
            entity_id=user_id,
        ),
    )

    memory.add_item(memory_item)

    routers[user_id].route(memory_item)

    routers[user_id].route(memory_item)

    episodic_store = episodic_memories[user_id]
    consolidation = consolidation_layers[user_id]

    if len(episodic_store.get_unconsolidated()) >= 5:
        consolidation.consolidate()


    semantic_store = semantic_memories[user_id]

    relevant_facts = semantic_store.retrieve(user_input)

    if relevant_facts:
        memory_context = "\n".join(
            f"- {fact.predicate}: {fact.value}"
            for fact in relevant_facts
        )

        messages.append(
            SystemMessage(
                content=(
                    "Relevant long-term customer memory:\n"
                    + memory_context
                )
            )
        )

    # Scratchpad: detect and pin any high-stakes fact in this customer
    # message (rules first, LLM fallback only if rules find nothing).
    # This runs once per user turn, not per agent step, since it's about
    # what the *customer* said, not what the agent is doing internally.
    # turn = number of messages already in this user's transcript, so
    # each pinned fact records a stable position in the conversation.
    process_customer_message(memory, user_input, turn=len(messages))

    # Build metadata
    metadata = MetadataBuilder.build(
        entity_type="customer",
        entity_id=user_id,
    )

    # (Agent Loop)
    for step_num in range(MAX_STEPS):
        print(f"\n--- Step {step_num + 1} ---")
        memory.messages = list(messages)
        filtered_messages = zone_based_pruning(
            memory.get_messages())

        # Inject the scratchpad as its own SystemMessage so pruning
        # strategies (which only ever operate on filtered_messages/the
        # rolling buffer) can never destroy the plan, sub-goal, or
        # pinned facts. This block is always the freshest scratchpad
        # state, appended after masking so it can't get masked itself.
        scratchpad_block = SystemMessage(
            content=memory.render_scratchpad_for_prompt()
        )
        final_messages = filtered_messages + [scratchpad_block]

        step: AgentStep = await model.ainvoke(final_messages)
        print(f"Thought: {step.thought}")
        print(f"Action: {step.action}")
        messages.append(
            AIMessage(content=f"Thought: {step.thought}\nAction: {step.action}\nInput: {step.action_input}")
        )
        #(Final Action)
        if handle_final_action(step):
            consolidation_layers[user_id].consolidate()
            return step
        
        #  Step Validation check
        if not validate_step(step, tools):
            messages.append(
                HumanMessage(
                    content=f"Error: '{step.action}' is not a valid tool. Choose from: {list(tools.keys())}"
                )
            )
            continue


        # (MCP Tool Execution)
        try:
            result = await tool_call(step, tools, context=context)
            handle_tool_result(messages, step, result)
            
        except ValidationError as e:
            messages.append(
                HumanMessage(content=f"Invalid arguments for {step.action}: {e.errors()}")
            )
        except Exception as e:
            messages.append(
                HumanMessage(content=f"Error executing tool {step.action}: {str(e)}")
            )
    print("Reached maximum execution steps without final answer.")
    return None


async def main():
    print("Agent module ready. Use run_agent(client, user_input) inside an active client session.")


if __name__ == "__main__":
    asyncio.run(main())
