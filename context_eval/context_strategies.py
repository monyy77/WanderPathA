import re
from langchain.messages import AIMessage, HumanMessage, SystemMessage

_TOOL_OBSERVATION_RE = re.compile(r"observation from", re.I)
_TOOL_ACTION_RE = re.compile(r"observation from (?:tool ')?([\w_]+)", re.I)


def _is_tool_observation(message) -> bool:
    return bool(_TOOL_OBSERVATION_RE.search(str(message.content)))


def _tool_label(message) -> str:
    match = _TOOL_ACTION_RE.search(str(message.content))
    return match.group(1) if match else "tool"


def sliding_window(messages, max_messages):
    """Keep only the last `max_messages`. Simplest strategy, and the
    weakest one for this use case: it has no idea a message it's about to
    drop contains a fact the agent still needs — it just counts backward
    from the end.
    """
    return messages[-max_messages:]

def observation_masking(messages, keep_recent_observations=2):
    """Collapse *older* tool outputs into a one-line placeholder, but keep
    the most recent `keep_recent_observations` tool results intact — those
    are the ones the agent hasn't necessarily acted on yet.

    The previous version of this function masked every observation the
    instant it was appended, including the one from the step that just
    ran — so the agent could never actually see a tool result it had just
    asked for. That's fixed here: only observations older than the most
    recent `keep_recent_observations` get collapsed.
    """
    tool_indices = [i for i, m in enumerate(messages) if _is_tool_observation(m)]
    keep_indices = set(tool_indices[-keep_recent_observations:]) if tool_indices else set()

    masked = []
    for i, message in enumerate(messages):
        if _is_tool_observation(message) and i not in keep_indices:
            masked.append(
                type(message)(content=f"[Tool output masked: {_tool_label(message)}]")
            )
        else:
            masked.append(message)

    return masked

def _summarize_chunk(previous_summary: str, chunk_text: str) -> str:
    """Fold `chunk_text` into `previous_summary`. Tries a real LLM call
    (that's what makes this "recursive" rather than a one-shot truncation:
    each chunk's summary is built on top of the last one); falls back to a
    cheap deterministic compression if no model/API is available, so the
    test suite can still run offline without burning API budget on every
    invocation, per the cost note in the project brief.
    """
    try:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(
            model="llama-3.3-70b-versatile",
            model_provider="groq",
            max_tokens=200,
            max_retries=1,
        )
        prompt = (
            "You are compressing an ongoing support conversation into a "
            "running summary. Keep every concrete fact, number, and "
            "customer constraint (accessibility needs, budget figures, "
            "dates, preferences). Drop routine tool-call chatter. Merge "
            "the new content into the existing summary in 3-5 sentences.\n\n"
            f"Existing summary:\n{previous_summary or '(none yet)'}\n\n"
            f"New content to fold in:\n{chunk_text}"
        )
        response = model.invoke(prompt)
        return str(response.content).strip()
    except Exception:
        return _fallback_summarize_chunk(previous_summary, chunk_text)


def _fallback_summarize_chunk(previous_summary: str, chunk_text: str) -> str:
    """Deterministic, offline fallback (no model call). Tool-observation
    lines are pure repetitive noise, so they get collapsed to a count.
    Everything else — customer and agent turns — is where actual
    decisions and constraints live, so it's kept in full rather than
    truncated to a "first sentence": an earlier version of this did that
    and silently dropped facts that came after the first period in a
    message (e.g. "...to Hurghada. One traveler uses a wheelchair..."
    would lose the wheelchair clause). This fallback is intentionally
    conservative about what counts as safe-to-compress.
    """
    kept_lines = []
    tool_observation_count = 0

    for line in chunk_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if _TOOL_OBSERVATION_RE.search(line):
            tool_observation_count += 1
        else:
            kept_lines.append(line)

    if tool_observation_count:
        kept_lines.append(f"[{tool_observation_count} tool observations checked]")

    condensed = " | ".join(kept_lines)
    if previous_summary:
        return f"{previous_summary} | {condensed}"
    return condensed


def recursive_summarization(messages, max_recent=8, chunk_size=6):
    """Fold everything older than the last `max_recent` messages into a
    running summary, built up `chunk_size` messages at a time (hence
    "recursive": each chunk's summary absorbs the previous one).
    """
    if len(messages) <= max_recent:
        return messages

    old_messages = messages[:-max_recent]
    recent_messages = messages[-max_recent:]

    running_summary = ""
    for start in range(0, len(old_messages), chunk_size):
        chunk = old_messages[start : start + chunk_size]
        chunk_text = "\n".join(str(m.content) for m in chunk)
        running_summary = _summarize_chunk(running_summary, chunk_text)

    summary_message = SystemMessage(
        content=f"Summary of earlier conversation: {running_summary}"
    )
    return [summary_message] + recent_messages

def _classify_zone(message) -> str:
    """Four zones, not three. The earlier version lumped the agent's own
    Thought/Action messages (AIMessage) in with real customer dialogue —
    since those outnumber actual customer turns many times over in a
    tool-heavy conversation, they crowded the customer's original
    statement straight out of the "keep the last N conversation
    messages" window. Agent reasoning steps are noise for this purpose,
    same as tool output, so they get their own zone.
    """
    if isinstance(message, SystemMessage) or getattr(message, "type", None) == "system":
        return "system"
    if _is_tool_observation(message):
        return "tool_history"
    if isinstance(message, AIMessage) or getattr(message, "type", None) == "ai":
        return "agent_reasoning"
    return "conversation"


def zone_based_pruning(
    messages,
    keep_recent_conversation=6,
    keep_recent_tool=2,
    keep_recent_reasoning=2,
):
   
    zones = [_classify_zone(m) for m in messages]

    def keep_set(zone_name, keep_recent):
        indices = [i for i, z in enumerate(zones) if z == zone_name]
        return set(indices[-keep_recent:]) if indices else set()

    keep_tool = keep_set("tool_history", keep_recent_tool)
    keep_reasoning = keep_set("agent_reasoning", keep_recent_reasoning)
    keep_conversation = keep_set("conversation", keep_recent_conversation)

    result = []
    for i, message in enumerate(messages):
        zone = zones[i]

        if zone == "system":
            result.append(message)

        elif zone == "tool_history":
            if i in keep_tool:
                result.append(message)
            else:
                result.append(
                    type(message)(content=f"[Tool output masked: {_tool_label(message)}]")
                )

        elif zone == "agent_reasoning":
            if i in keep_reasoning:
                result.append(message)
            else:
                result.append(type(message)(content="[Earlier reasoning step omitted]"))

        elif zone == "conversation" and i in keep_conversation:
            result.append(message)
        # conversation messages outside the window are dropped entirely

    return result
