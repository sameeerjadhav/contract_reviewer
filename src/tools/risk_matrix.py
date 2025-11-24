from typing import Dict, List, Any

class RiskMatrix:
    """
    Encodes risk rules for different clause types.
    """
    
    def __init__(self):
        self.rules = {
            "limitation_of_liability": [
                {"condition": "no_cap", "risk_level": "critical", "score": 10, "description": "No liability cap found (unlimited liability)."},
                {"condition": "cap_lt_12_months", "risk_level": "high", "score": 8, "description": "Liability cap is less than 12 months of fees."},
                {"condition": "cap_lt_24_months", "risk_level": "medium", "score": 5, "description": "Liability cap is less than 24 months of fees."}
            ],
            "data_privacy": [
                {"condition": "vendor_owns_data", "risk_level": "critical", "score": 10, "description": "Vendor claims ownership of customer data."},
                {"condition": "no_privacy_clause", "risk_level": "critical", "score": 9, "description": "No data privacy or protection clause found."},
                {"condition": "ambiguous_ownership", "risk_level": "high", "score": 8, "description": "Data ownership is ambiguous."}
            ],
            "service_level_agreement": [
                {"condition": "missing_sla", "risk_level": "critical", "score": 10, "description": "No Service Level Agreement (SLA) found."},
                {"condition": "uptime_lt_99", "risk_level": "high", "score": 8, "description": "Uptime guarantee is less than 99%."},
                {"condition": "weak_remedies", "risk_level": "medium", "score": 6, "description": "Weak remedies for downtime (e.g., no credits)."}
            ],
            "termination": [
                {"condition": "vendor_terminate_no_cause", "risk_level": "critical", "score": 9, "description": "Vendor can terminate without cause, but customer cannot."},
                {"condition": "short_notice", "risk_level": "high", "score": 7, "description": "Termination notice period is very short (< 30 days)."}
            ],
            "payment_terms": [
                {"condition": "payment_upfront", "risk_level": "high", "score": 7, "description": "Full payment required in advance."},
                {"condition": "net_gt_45", "risk_level": "medium", "score": 4, "description": "Payment terms > Net 45."}
            ],
             "non_compete": [
                {"condition": "unlimited_scope", "risk_level": "critical", "score": 10, "description": "Unlimited geography or duration for non-compete."},
                {"condition": "duration_gt_2_years", "risk_level": "high", "score": 8, "description": "Non-compete duration > 2 years."}
            ]
        }

    def evaluate_risk(self, clause_type: str, extracted_terms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates risk for a specific clause based on extracted terms.
        This is a simplified rule engine. In a real scenario, this would involve
        more complex logic or even another LLM call to match conditions.
        """
        if clause_type not in self.rules:
            return {"risk_level": "unknown", "score": 0, "factors": []}
            
        relevant_rules = self.rules[clause_type]
        risk_factors = []
        max_score = 0
        
        # Heuristic matching of terms to rules
        # In a real implementation, the 'extracted_terms' would need to be structured
        # to easily check these conditions (e.g., 'cap_months': 6).
        
        # Example logic for Limitation of Liability
        if clause_type == "limitation_of_liability":
            cap_months = extracted_terms.get("cap_months_fees")
            if cap_months is None and extracted_terms.get("has_cap") is False:
                 self._add_factor(risk_factors, relevant_rules, "no_cap")
            elif cap_months:
                if cap_months < 12:
                    self._add_factor(risk_factors, relevant_rules, "cap_lt_12_months")
                elif cap_months < 24:
                    self._add_factor(risk_factors, relevant_rules, "cap_lt_24_months")

        # Example logic for SLA
        elif clause_type == "service_level_agreement":
            if extracted_terms.get("missing"):
                 self._add_factor(risk_factors, relevant_rules, "missing_sla")
            else:
                uptime = extracted_terms.get("uptime_percentage")
                if uptime and uptime < 99.0:
                     self._add_factor(risk_factors, relevant_rules, "uptime_lt_99")
        
        # Calculate max score from identified factors
        if risk_factors:
            max_score = max(f["score"] for f in risk_factors)
            overall_level = max(risk_factors, key=lambda x: x["score"])["risk_level"]
        else:
            overall_level = "low"
            max_score = 1

        return {
            "risk_level": overall_level,
            "risk_score": max_score,
            "risk_factors": risk_factors
        }

    def _add_factor(self, factors_list, rules, condition_key):
        rule = next((r for r in rules if r["condition"] == condition_key), None)
        if rule:
            factors_list.append(rule)
