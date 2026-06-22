import unittest
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


class AgentUiControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    def test_agent_controls_are_hidden_in_base_markup(self):
        for control_id in (
            "agent-load-default-btn",
            "agent-load-candidate-btn",
            "agent-accumulate-btn",
        ):
            control = self.soup.find(id=control_id)
            self.assertIsNotNone(control)
            self.assertIn("hidden", control.get("class", []))

    def test_agent_controls_are_revealed_only_by_agent_query_mode(self):
        self.assertIn(
            "new URLSearchParams(window.location.search).get('agent') === '1'",
            self.html,
        )
        self.assertIn("if (agentMode) {", self.html)
        self.assertIn("agentLoadDefaultBtn.classList.remove('hidden');", self.html)
        self.assertIn("agentLoadCandidateBtn.classList.remove('hidden');", self.html)
        self.assertIn("agentAccumulateBtn.classList.remove('hidden');", self.html)

    def test_accumulation_control_is_explicitly_agent_only(self):
        control = self.soup.find(id="agent-accumulate-btn")
        self.assertEqual(control.find("span").get_text(strip=True), "AGENT")
        self.assertIn("Accumulate approved unique", control.get_text(" ", strip=True))


if __name__ == "__main__":
    unittest.main()
