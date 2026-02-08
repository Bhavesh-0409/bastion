import json
import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class RuleEngine:
    """Executes rule-based security checks on prompts"""
    
    def __init__(self, rules_file: str = "rules/default_rules.json"):
        self.rules = self._load_rules(rules_file)
        self.violations = []
    
    def _load_rules(self, rules_file: str) -> List[Dict]:
        """Load rules from JSON file"""
        try:
            with open(rules_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Rules file not found: {rules_file}. Using empty rules.")
            return []
    
    def check_prompt(self, prompt: str) -> Tuple[bool, List[Dict]]:
        """
        Check prompt against all rules.
        Returns (is_safe, violations_list)
        """
        violations = []
        
        for rule in self.rules:
            if self._evaluate_rule(prompt, rule):
                violations.append({
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "severity": rule.get("severity", "medium")
                })
        
        is_safe = len(violations) == 0
        return is_safe, violations
    
    def _evaluate_rule(self, prompt: str, rule: Dict) -> bool:
        """Evaluate a single rule against prompt"""
        rule_type = rule.get("type")
        
        if rule_type == "regex":
            pattern = rule.get("pattern")
            return bool(re.search(pattern, prompt, re.IGNORECASE))
        
        elif rule_type == "keyword":
            keywords = rule.get("keywords", [])
            return any(kw.lower() in prompt.lower() for kw in keywords)
        
        # TODO: Add more rule types (token_limit, context_window, etc.)
        return False

# Factory function
def create_rule_engine(rules_file: str = "rules/default_rules.json") -> RuleEngine:
    return RuleEngine(rules_file)
