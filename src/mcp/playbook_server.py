import json
import os
from typing import Dict, Any, Optional

class PlaybookServer:
    """
    Simulates an MCP server for accessing contract playbooks.
    In a full ADK implementation, this would be a standalone process communicating via stdio/SSE.
    Here, we implement it as a class for direct integration in the standalone app.
    """
    
    def __init__(self, playbook_dir: str):
        self.playbook_dir = playbook_dir
        self.playbooks: Dict[str, Any] = {}
        self._load_playbooks()

    def _load_playbooks(self):
        """Loads all JSON playbooks from the directory."""
        if not os.path.exists(self.playbook_dir):
            return

        for filename in os.listdir(self.playbook_dir):
            if filename.endswith(".json"):
                contract_type = filename.replace(".json", "")
                with open(os.path.join(self.playbook_dir, filename), 'r') as f:
                    self.playbooks[contract_type] = json.load(f)

    def get_playbook(self, contract_type: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full playbook for a contract type."""
        return self.playbooks.get(contract_type)

    def compare_term(self, contract_type: str, clause_type: str, actual_value: str) -> Dict[str, Any]:
        """
        Compares an actual term against the playbook standards.
        """
        playbook = self.get_playbook(contract_type)
        if not playbook:
            return {"error": "Playbook not found"}
            
        preferred_terms = playbook.get("preferred_terms", {})
        term_standards = preferred_terms.get(clause_type)
        
        if not term_standards:
            return {"status": "unknown_clause", "message": "No standard defined for this clause."}

        # In a real MCP server, this might use an LLM or fuzzy matching to compare
        # For this simulation, we return the standards for the agent to compare
        return {
            "standards": term_standards,
            "actual_value": actual_value,
            "instruction": "Compare 'actual_value' against 'standards' to determine deviation."
        }

    def get_suggested_language(self, contract_type: str, clause_type: str) -> Optional[str]:
        """Retrieves suggested language for a clause."""
        # Placeholder: In a real app, this would fetch from a template library
        return f"[Standard {clause_type} language for {contract_type}]"
