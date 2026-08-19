
"""Planning Agent: IROPS reshuffle (decomposition, dynamic decomposition,
planning-algorithm routing).
 
Only the lightweight DAG primitives are exported here. `run_planning_agent`
is intentionally NOT imported at package init time -- it pulls in the full
MCP/LLM stack (and, transitively, the Memory/RAG agent's own dependencies
via agent.agent.discover_tools), which shouldn't be required just to use
Plan/Task/TaskType or to unit-test dag.py in isolation.
 
To run the agent: `from planning.planning_agent import run_planning_agent`.
"""
 
from planning.dag import Plan, Task, TaskType
 
__all__ = ["Plan", "Task", "TaskType"]
 
