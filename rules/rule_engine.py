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
        logger.info(f"[DEBUG-RULEENGINE] RuleEngine initialized with {len(self.rules)} rules from {rules_file}")
        
        # Debug: Log a sample of loaded rules
        if self.rules:
            for rule in self.rules[:3]:
                logger.info(f"[DEBUG-RULEENGINE] Sample rule - ID: {rule.get('id')}, Type: {rule.get('type')}, Intent: {rule.get('intent')}")
            logger.info(f"[DEBUG-RULEENGINE] Last rule - ID: {self.rules[-1].get('id')}")
    
    def _load_rules(self, rules_file: str) -> List[Dict]:
        """Load rules from JSON file"""
        try:
            with open(rules_file, "r") as f:
                loaded_rules = json.load(f)
                logger.info(f"[DEBUG-RULEENGINE] Loaded {len(loaded_rules)} rules from {rules_file}")
                return loaded_rules
        except FileNotFoundError:
            logger.warning(f"Rules file not found: {rules_file}. Using empty rules.")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"[DEBUG-RULEENGINE] JSON decode error in rules file: {e}")
            return []
    
    def check_prompt(self, prompt: str) -> Tuple[bool, List[Dict]]:
        """
        Check prompt against all rules.
        Returns (is_safe, violations_list)
        """
        violations = []
        logger.info(f"[DEBUG-RULEENGINE] Checking prompt (length {len(prompt)}): {prompt[:100]}...")
        
        for rule in self.rules:
            matched = self._evaluate_rule(prompt, rule)
            if matched:
                violation = {
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "severity": rule.get("severity", "medium"),
                    "intent": rule.get("intent")
                }
                violations.append(violation)
                logger.warning(f"[DEBUG-RULEENGINE] VIOLATION TRIGGERED - Rule ID: {rule.get('id')}, Name: {rule.get('name')}, Intent: {rule.get('intent')}")
        
        is_safe = len(violations) == 0
        logger.info(f"[DEBUG-RULEENGINE] Check complete - {len(violations)} violations found, is_safe={is_safe}")
        return is_safe, violations
    
    def _evaluate_rule(self, prompt: str, rule: Dict) -> bool:
        """Evaluate a single rule against prompt"""
        rule_type = rule.get("type")
        rule_id = rule.get("id")
        
        try:
            if rule_type == "regex":
                pattern = rule.get("pattern")
                if not pattern:
                    logger.warning(f"[DEBUG-RULEENGINE] Rule {rule_id} has no pattern")
                    return False
                
                matched = bool(re.search(pattern, prompt, re.IGNORECASE))
                if matched:
                    logger.debug(f"[DEBUG-RULEENGINE] Rule {rule_id} regex matched: {pattern[:50]}...")
                return matched
            
            elif rule_type == "keyword":
                keywords = rule.get("keywords", [])
                for kw in keywords:
                    if kw.lower() in prompt.lower():
                        logger.debug(f"[DEBUG-RULEENGINE] Rule {rule_id} keyword matched: '{kw}'")
                        return True
                return False
            
            else:
                logger.warning(f"[DEBUG-RULEENGINE] Unknown rule type '{rule_type}' for rule {rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"[DEBUG-RULEENGINE] Error evaluating rule {rule_id}: {e}")
            return False

# Factory function
def create_rule_engine(rules_file: str = "rules/default_rules.json") -> RuleEngine:
    return RuleEngine(rules_file)

