import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AgentUiContractTests(unittest.TestCase):
    def test_agent_controls_are_hidden_in_base_markup(self):
        for control_id in (
            "agent-load-default-btn",
            "agent-load-candidate-btn",
            "agent-accumulate-btn",
        ):
            match = re.search(
                rf'<button id="{re.escape(control_id)}" class="([^"]+)"',
                INDEX,
            )
            self.assertIsNotNone(match, control_id)
            self.assertIn("hidden", match.group(1).split(), control_id)

    def test_agent_controls_are_revealed_only_by_agent_query_mode(self):
        self.assertIn(
            "const agentMode = new URLSearchParams(window.location.search).get('agent') === '1';",
            INDEX,
        )
        agent_block = re.search(
            r"if \(agentMode\) \{(?P<body>.*?)\n\s*\}",
            INDEX,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(agent_block)
        body = agent_block.group("body")
        self.assertIn("agentLoadDefaultBtn.classList.remove('hidden')", body)
        self.assertIn("agentLoadCandidateBtn.classList.remove('hidden')", body)
        self.assertIn("agentAccumulateBtn.classList.remove('hidden')", body)

    def test_accumulation_control_is_agent_only_and_unique(self):
        self.assertEqual(INDEX.count('id="agent-accumulate-btn"'), 1)
        self.assertNotIn('id="accumulate-btn"', INDEX)
        self.assertIn("X-Agent-Automation", INDEX)
        self.assertIn("acceptance: 'unique'", INDEX)


if __name__ == "__main__":
    unittest.main()
