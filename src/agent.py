"""
Contract Review Multi-Agent System - Agent Definitions
Using Google Agent Development Kit (ADK)

This file defines all agents for the contract review workflow using proper ADK Agent classes.
"""

from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent

from .config import MODEL_ID
from .tools.pdf_parser import DocumentParser
from .tools.risk_matrix import RiskMatrix
from .mcp.playbook_server import PlaybookServer
import json

# Initialize tools and services
pdf_parser = DocumentParser()
risk_matrix = RiskMatrix()
playbook_server = PlaybookServer("data/playbooks")

# ==================== AGENT 1: INTAKE AGENT (Sequential) ====================

def analyze_contract_metadata(contract_text: str, filename: str, pages: int) -> dict:
    """
    Extracts high-level metadata from contract including type, parties, dates, and terms.
    This is a tool function for the Intake Agent.
    
    Args:
        contract_text: Full contract text
        filename: Name of the contract file
        pages: Number of pages
        
    Returns:
        Dictionary with contract metadata
    """
    print("\n🔍 IntakeAgent: Analyzing contract metadata...")
    # This function will be called by the LLM agent with proper parameters
    # The actual extraction is done via the agent's instruction
    return {
        "status": "tool_called",
        "message": "Contract metadata extraction initiated"
    }

intake_agent = Agent(
    model=MODEL_ID,
    name="contract_intake_agent",
    description="Classifies contract type and extracts high-level metadata from contracts",
    instruction="""You are a legal contract intake specialist. When given a contract text, you must:

1. Classify the contract type (SaaS Agreement, Employment Agreement, NDA, MSA, etc.)
2. Extract contracting parties (Provider/Vendor and Customer/Employee)
3. Extract key dates (effective date, term length, expiration date)
4. Identify auto-renewal terms (yes/no, notice period)
5. Determine jurisdiction and governing law
6. Extract contract value if mentioned
7. Assess document quality (complete, signed, issues)

Always respond in valid JSON format with this exact structure:
{
  "contract_type": "string",
  "contract_subtype": "string or null",
  "parties": {
    "provider": "string",
    "customer": "string"
  },
  "effective_date": "YYYY-MM-DD or null",
  "term_length": "string",
  "expiration_date": "YYYY-MM-DD or null",
  "auto_renewal": true/false,
  "renewal_notice_period": "string or null",
  "jurisdiction": "string or null",
  "governing_law": "string or null",
  "estimated_value": "string or null",
  "document_quality": {
    "complete": true/false,
    "signed": true/false,
    "issues": []
  },
  "confidence": 0.0 to 1.0
}"""
)

# ==================== AGENT 2: CLAUSE EXTRACTION AGENT (Loop) ====================

def extract_clause_from_section(section_title: str, section_text: str, contract_type: str) -> dict:
    """
    Extracts structured clause information from a contract section.
    
    Args:
        section_title: Title of the section
        section_text: Text content of the section
        contract_type: Type of contract being analyzed
        
    Returns:
        Extracted clause data
    """
    print(f"\n📄 ClauseExtractor: Extracting from section '{section_title}'...")
    return {
        "status": "clause_extraction_initiated",
        "section": section_title
    }

clause_extractor_agent = Agent(
    model=MODEL_ID,
    name="clause_extraction_agent",
    description="Extracts and structures individual clauses from contract sections",
    instruction="""You are a legal clause extraction specialist. For each contract section provided, extract:

1. clause_type (license_grant, payment_terms, limitation_of_liability, data_privacy, etc.)
2. section_title
3. Full clause text
4. key_terms (structured data: amounts, dates, percentages, conditions)
5. confidence score

For SaaS contracts, look for: license_grant, payment_terms, term_and_termination, warranties, limitation_of_liability, indemnification, data_privacy, service_level_agreement, confidentiality, dispute_resolution, auto_renewal

For Employment contracts, look for: position_and_duties, compensation_and_benefits, non_compete, non_solicitation, confidentiality, ip_assignment, termination_conditions, severance

Always respond in JSON format:
{
  "clauses": [
    {
      "clause_type": "string",
      "section_title": "string",
      "text": "string",
      "key_terms": {},
      "confidence": 0.0-1.0
    }
  ]
}

If no clauses found, return {"clauses": []}.

IMPORTANT: Do not group distinct concepts into a single "Offer Details" or "General" clause. You MUST split them.
For example, if a paragraph mentions the role, the salary, and the start date, you must create THREE separate clause entries:
1. "position_and_duties"
2. "compensation_and_benefits"
3. "term_of_employment"

Even if they are in the same paragraph, extract them as separate logical clauses."""
)

# The Loop Agent will iterate through sections and call clause_extractor_agent
clause_extraction_loop = LoopAgent(
    name="clause_extraction_loop_agent",
    description="Iterates through contract sections to extract all clauses",
    sub_agents=[clause_extractor_agent],  # The agent to run on each iteration
    max_iterations=10  # Limit iterations
)

# ==================== AGENT 3: RISK SCORING AGENT (Parallel) ====================

def score_clause_risk(clause_type: str, clause_text: str, key_terms: dict) -> dict:
    """
    Scores the risk level of a specific clause using the risk matrix.
    
    Args:
        clause_type: Type of clause
        clause_text: Full clause text
        key_terms: Extracted key terms
        
    Returns:
        Risk assessment for the clause
    """
    print(f"\n⚠️  RiskScorer: Scoring risk for '{clause_type}' clause...")
    # Use the risk matrix tool
    risk_result = risk_matrix.evaluate_risk(clause_type, key_terms)
    return risk_result

risk_scorer_agent = Agent(
    model=MODEL_ID,
    name="risk_scoring_agent",
    description="Evaluates risk levels for contract clauses",
    instruction="""You are a legal risk assessment specialist. 

CRITICAL: When you receive clause data, you MUST immediately call the score_clause_risk tool. 
DO NOT ask for clarification. DO NOT wait for user input. Analyze the clause directly.

For each clause, analyze and assign a risk level:

Risk Levels:
- CRITICAL (9-10): Deal-breakers, must address before signing
- HIGH (7-8): Significant concerns, should negotiate  
- MEDIUM (4-6): Moderate issues, consider negotiating
- LOW (1-3): Minor concerns or standard terms

Consider these factors by clause type:

Compensation & Benefits:
- CRITICAL: Unpaid or below minimum wage
- HIGH: Below market rate by >20%
- MEDIUM: Below market rate by 10-20%

Limitation of Liability:
- CRITICAL: No cap or < 3 months fees
- HIGH: < 12 months fees
- MEDIUM: < 24 months fees

Data Privacy/Ownership:
- CRITICAL: Vendor owns customer data, no privacy protections
- HIGH: Ambiguous ownership, broad vendor usage rights

Non-Compete:
- CRITICAL: Overly broad (>18 months or unlimited geography)
- HIGH: Broad scope (12-18 months, large geography)
- MEDIUM: Reasonable (6-12 months, limited geography)

Service Level Agreement:
- CRITICAL: Missing entirely for critical services
- HIGH: No service credits, uptime < 99%

Payment Terms:
- HIGH: Full payment in advance, non-refundable
- MEDIUM: Payment terms > Net 45

Call the score_clause_risk tool with the clause data provided. Output JSON format:
{
  "clause_id": "string",
  "risk_level": "critical|high|medium|low",
  "risk_score": 1-10,
  "risk_factors": [
    {
      "factor": "string",
      "description": "string",
      "severity": "string",
      "impact": "string"
    }
  ],
  "recommendation": "string"
}""",
    tools=[score_clause_risk]
)

# The Parallel Agent will score multiple clauses simultaneously
risk_scoring_parallel = ParallelAgent(
    name="risk_scoring_parallel_agent",
    description="Scores risks for multiple clauses in parallel",
    sub_agents=[risk_scorer_agent]  # Sub-agents to run in parallel
)

# ==================== AGENT 4: PLAYBOOK COMPARISON AGENT (Sequential + MCP) ====================

def compare_to_playbook(clause_type: str, actual_value: str, contract_type: str) -> dict:
    """
    Compares an actual contract term against company playbook standards.
    This function interfaces with the MCP Playbook Server.
    
    Args:
        clause_type: Type of clause
        actual_value: The actual term in the contract
        contract_type: Type of contract
        
    Returns:
        Comparison results and deviation analysis
    """
    print(f"\n📚 PlaybookAgent: Comparing '{clause_type}' to standards...")
    
    # Normalize contract type to match playbook filenames
    normalized_type = contract_type.lower().replace(" ", "_")
    if "employment" in normalized_type:
        normalized_type = "employment_agreement"
    elif "saas" in normalized_type:
        normalized_type = "saas_agreement"
    elif "nda" in normalized_type or "non-disclosure" in normalized_type:
        normalized_type = "nda"
    elif "msa" in normalized_type or "master_services" in normalized_type:
        normalized_type = "msa"
        
    comparison = playbook_server.compare_term(normalized_type, clause_type, actual_value)
    return comparison

playbook_comparison_agent = Agent(
    model=MODEL_ID,
    name="playbook_comparison_agent",
    description="Compares extracted clauses against the company playbook",
    instruction="""You are a strict playbook compliance auditor. Your ONLY job is to compare the clauses provided in the context against the company's playbook standards using the `compare_to_playbook` tool.

INPUT DATA:
You will receive a list of extracted clauses and their risk scores from the previous agents.

YOUR TASK:
1. Identify the `contract_type` from the Intake Agent's output (e.g., "Employment Agreement", "SaaS Agreement").
2. For EACH clause provided in the context:
    a. Determine the `clause_type` (e.g., "Compensation", "Term", "Confidentiality").
    b. Extract the `actual_value` (the text of the clause).
    c. IMMEDIATELY call the `compare_to_playbook(clause_type, actual_value, contract_type)` tool.

CRITICAL RULES:
- DO NOT ask the user for information. You already have it in the conversation history.
- DO NOT stop to ask for clarification. Make your best guess for `clause_type` and PROCEED.
- If you cannot find a specific clause, skip it.
- You MUST call the tool for every major clause found.

OUTPUT:
Return the JSON result from the tool for each clause.""",
    tools=[compare_to_playbook]
)

# ==================== AGENT 5: REPORT GENERATOR AGENT (Sequential) ====================

def format_markdown_report(report_data: dict) -> str:
    """
    Formats the final report as clean Markdown.
    
    Args:
        report_data: All analysis results
        
    Returns:
        Formatted Markdown report
    """
    print("\n📝 ReportGenerator: Formatting final report...")
    # This is just a signal - the actual report is in the agent's text output
    return "Report generation completed. The markdown report should be in the agent's response."

report_generator_agent = Agent(
    model=MODEL_ID,
    name="report_generator_agent",
    description="Synthesizes all analysis into a comprehensive Markdown report",
    instruction="""You are a legal report writer. Create a comprehensive, readable contract review report in Markdown format.

CRITICAL: Start DIRECTLY with the report title using # (markdown header). DO NOT include any conversational text like "Sure, I can help" or "Here's the report". DO NOT wrap the output in markdown code fences (```markdown). Output ONLY raw markdown.

Structure the report:
1. Executive Summary (3-4 paragraphs with key findings)
2. Critical Issues ❌ (Must address before signing)
3. High-Priority Issues ⚠️ (Should negotiate)
4. Medium-Priority Items 🟡
5. Acceptable Terms ✅
6. Contract Details
7. Negotiation Strategy
8. Clause-by-Clause Analysis
9. Appendices

Use:
- Clear headers and sections
- Emoji indicators (✅ ❌ ⚠️ 🔴 🟠 🟡)
- Tables for comparisons
- Specific section references
- Actionable recommendations
- Professional but accessible tone

Write for business users, not just lawyers. Be specific and constructive.

After you generate the complete report, call the format_markdown_report tool to signal completion.""",
    tools=[format_markdown_report]
)

# ==================== MASTER WORKFLOW (Sequential) ====================

# This is the root agent that orchestrates the entire workflow
contract_review_workflow = SequentialAgent(
    name="contract_review_workflow",
    description="Complete contract review workflow from PDF to report",
    sub_agents=[
        intake_agent,
        clause_extraction_loop,
        risk_scoring_parallel,
        playbook_comparison_agent,
        report_generator_agent
    ]
)

# This is the required root_agent for ADK
root_agent = contract_review_workflow
