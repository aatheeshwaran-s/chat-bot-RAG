"""
Week 9: Trajectory Evaluation - Spot when agent takes the wrong path.

Core Concept:
  RIGHT ANSWER ≠ RIGHT PATH
  
  Example: Agent answers "20 days leave" correctly
  But path: lookup_policy → check_ticket_db → calculate_amount → lookup_policy → final_answer
  Should be: lookup_policy → final_answer
  
  Gap = Answer correct BUT path is wrong (got lucky, will break next time)
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AgentStep:
    """One step in agent's trajectory."""
    step_num: int
    action: str            # Tool name
    action_input: str      # Input to tool
    observation: str       # Result from tool


class TrajectoryEvaluator:
    """Checks if agent took the right path, not just right answer."""
    
    def evaluate(
        self,
        trajectory: List[AgentStep],
        expected_tools: List[str],
        answer_is_correct: bool
    ) -> Dict[str, Any]:
        """
        Evaluate a trajectory.
        
        Args:
            trajectory: Agent's steps taken
            expected_tools: What tools should have been used
            answer_is_correct: Is final answer factually correct?
        
        Returns:
            Report with gap detection
        """
        actual_tools = [step.action for step in trajectory]
        
        # Calculate metrics
        tool_accuracy = self._accuracy(actual_tools, expected_tools)
        efficiency = len(expected_tools) / len(trajectory) if trajectory else 0
        has_loop = self._detect_loop(trajectory)
        
        # Trajectory is correct if: good accuracy + no loops + reasonable efficiency
        trajectory_ok = tool_accuracy >= 0.7 and not has_loop and efficiency >= 0.5
        
        # GAP = answer correct but path wrong
        gap_exists = answer_is_correct and not trajectory_ok
        
        return {
            "answer_correct": answer_is_correct,
            "trajectory_correct": trajectory_ok,
            "gap_exists": gap_exists,
            "tool_accuracy": round(tool_accuracy, 2),
            "efficiency": round(efficiency, 2),
            "has_loop": has_loop,
            "actual_tools": actual_tools,
            "expected_tools": expected_tools,
            "failures": self._classify_failures(trajectory, expected_tools)
        }
    
    def _accuracy(self, actual: List[str], expected: List[str]) -> float:
        """% of correct tools used."""
        if not expected:
            return 1.0
        correct = sum(1 for i, tool in enumerate(actual) 
                     if i < len(expected) and tool == expected[i])
        return correct / len(expected)
    
    def _detect_loop(self, trajectory: List[AgentStep]) -> bool:
        """Is agent repeating the same action?"""
        for i in range(len(trajectory) - 1):
            if (trajectory[i].action == trajectory[i+1].action and 
                trajectory[i].action_input == trajectory[i+1].action_input):
                return True
        return False
    
    def _classify_failures(self, trajectory: List[AgentStep], expected: List[str]) -> List[str]:
        """Identify what went wrong."""
        failures = []
        
        # Check for loops
        if self._detect_loop(trajectory):
            failures.append("LOOP: repeated same tool call")
        
        # Check for wrong tools
        actual = [s.action for s in trajectory]
        for i, tool in enumerate(actual):
            if i < len(expected) and tool != expected[i]:
                failures.append(f"WRONG_TOOL at step {i+1}: used {tool}, expected {expected[i]}")
        
        # Check for too many steps
        if len(trajectory) > len(expected) * 1.5:
            failures.append(f"INEFFICIENT: {len(trajectory)} steps vs {len(expected)} optimal")
        
        return failures


if __name__ == "__main__":
    # Example: Good trajectory (no gap)
    steps_good = [
        AgentStep(1, "lookup_policy", "leave policy", "20 days"),
        AgentStep(2, "final_answer", "20 days", "answered")
    ]
    
    evaluator = TrajectoryEvaluator()
    result = evaluator.evaluate(
        trajectory=steps_good,
        expected_tools=["lookup_policy", "final_answer"],
        answer_is_correct=True
    )
    
    print("✓ GOOD TRAJECTORY (no gap):")
    print(f"  Answer correct: {result['answer_correct']}")
    print(f"  Trajectory correct: {result['trajectory_correct']}")
    print(f"  Gap exists: {result['gap_exists']}")
    print()
    
    # Example: Bad trajectory (GAP EXISTS)
    steps_bad = [
        AgentStep(1, "lookup_policy", "leave", "policy found"),
        AgentStep(2, "check_ticket_db", "TICK-1", "ticket data"),
        AgentStep(3, "calculate_amount", "5", "calc done"),
        AgentStep(4, "lookup_policy", "leave", "policy found again"),  # LOOP!
        AgentStep(5, "final_answer", "20 days", "answered")
    ]
    
    result = evaluator.evaluate(
        trajectory=steps_bad,
        expected_tools=["lookup_policy", "final_answer"],
        answer_is_correct=True
    )
    
    print("⚠️  GAP EXISTS (outcome OK, trajectory bad):")
    print(f"  Answer correct: {result['answer_correct']}")
    print(f"  Trajectory correct: {result['trajectory_correct']}")
    print(f"  Gap exists: {result['gap_exists']}")
    print(f"  Tool accuracy: {result['tool_accuracy']}")
    print(f"  Failures: {result['failures']}")
