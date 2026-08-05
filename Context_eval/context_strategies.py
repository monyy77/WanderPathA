def sliding_window(messages, max_messages):
    return messages[-max_messages:]


def observation_masking(messages):
    masked = []

    for message in messages:
        content = str(message.content)

        if "Observation from tool" in content:
            masked.append(type(message)(content="[Tool output masked]"))
        else:
            masked.append(message)

    return masked


def recursive_summarization(messages, max_messages):
    if len(messages) <= max_messages:
        return messages

    old_messages = messages[:-max_messages]
    recent_messages = messages[-max_messages:]

    summary = "Summary of previous conversation:\n"
    summary += "\n".join(
        str(message.content) for message in old_messages
    )

    summary_message = type(messages[0])(content=summary)

    return [summary_message] + recent_messages


def zone_based_pruning(messages, keep_recent=10):
    system_messages = []
    recent_messages = []

    for message in messages:
        if message.type == "system":
            system_messages.append(message)

    recent_messages = messages[-keep_recent:]

    return system_messages + recent_messages
