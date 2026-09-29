"""
Agent Memory System: Short-Term Scratchpad Memory & Long-Term Session Memory.
"""

from typing import List, Dict, Any, Optional


class ShortTermMemory:
    """
    Short-Term Scratchpad Memory for the ReAct Agent loop.
    Stores the sequence of Thought -> Action -> Action Input -> Observation for the current task.
    """
    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

    def add_step(self, step_num: int, thought: str, action: str, action_input: str, observation: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.steps.append({
            "step": step_num,
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation
        })
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    def get_scratchpad_str(self) -> str:
        if not self.steps:
            return "No previous steps taken."

        lines = []
        for s in self.steps:
            lines.append(f"Step {s['step']}:")
            lines.append(f"Thought: {s['thought']}")
            lines.append(f"Action: {s['action']}")
            lines.append(f"Action Input: {s['action_input']}")
            lines.append(f"Observation: {s['observation']}\n")
        return "\n".join(lines)

    def is_looping(self, current_action: str, current_input: str) -> bool:
        """
        Detects if the agent is stuck in an infinite loop calling the exact same tool with exact same input repeatedly.
        """
        count = 0
        for s in reversed(self.steps):
            if s["action"] == current_action and s["action_input"].strip() == current_input.strip():
                count += 1
                if count >= 2:
                    return True
            else:
                break
        return False


class LongTermMemory:
    """
    Long-Term Memory store for keeping track of customer interactions, ticket history, and policy clarifications across sessions.
    """
    def __init__(self):
        self.history: Dict[str, Dict[str, Any]] = {}

    def store_ticket_resolution(self, ticket_id: str, summary: str, status: str):
        self.history[ticket_id] = {
            "summary": summary,
            "status": status
        }

    def get_ticket_history(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        return self.history.get(ticket_id)

    def get_all_summaries(self) -> str:
        if not self.history:
            return "No historical ticket resolutions stored."
        items = [f"- Ticket {tid}: Status={data['status']}, Resolution={data['summary']}" for tid, data in self.history.items()]
        return "\n".join(items)
