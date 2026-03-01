# backend/compliance_agent.py
"""Compliance review agent using Pydantic AI and Bedrock."""

import os
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel

from models import ComplianceReport, TripSummary, Violation
from email_service import send_email

# Pacific Region fishing regulations
PACIFIC_REGULATIONS = {
    "Albacore Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "Target species for commercial longline fishing. No catch limits in international waters."
    },
    "Bigeye Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "High-value target species. Quota managed by WCPFC."
    },
    "Mahi-Mahi": {
        "status": "legal",
        "fine": 0,
        "summary": "Legal target species. No restrictions."
    },
    "Yellowfin Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "Target species. Subject to annual quotas."
    },
    "Shark": {
        "status": "bycatch",
        "fine": 500,
        "summary": "Bycatch species. Must release alive when possible. Finning prohibited. $500 fine per unreleased shark."
    },
    "Opah": {
        "status": "bycatch",
        "fine": 250,
        "summary": "Non-target species. Should release to minimize ecosystem impact. $250 fine if retained."
    },
    "Pelagic Stingray": {
        "status": "protected",
        "fine": 5000,
        "summary": "Protected under Pacific Marine Conservation Act. Immediate release required. $5,000 fine per incident. Three violations triggers license suspension."
    },
    "Unknown": {
        "status": "unknown",
        "fine": 100,
        "summary": "Unidentified species must be logged and reported. $100 administrative fee if not properly documented."
    },
}

SYSTEM_PROMPT = """You are a fishing compliance officer reviewing audit logs from commercial vessels in the Pacific Region.

Your job:
1. Review the audit log provided
2. Look up regulations for each species using the get_species_regulation tool
3. Identify any violations (unreleased bycatch or protected species)
4. Generate a compliance report
5. If there are unreleased violations, send an alert email using the send_alert_email tool

Be thorough. For each unique species in the log, check its regulation status.
Calculate total fines based on violation counts and fine amounts from the regulations.

Severity levels:
- compliant: No violations
- minor: Only unreleased bycatch, total fines < $1000
- major: Multiple bycatch violations or total fines >= $1000
- critical: Any unreleased protected species

Always call get_species_regulation for each species before making compliance determinations.
"""

# Track if email was sent during agent run
_email_was_sent = False


def _create_agent() -> Agent[None, ComplianceReport]:
    """Create the compliance agent with Bedrock model."""
    model = BedrockConverseModel(
        model_name="us.anthropic.claude-sonnet-4-20250514-v1:0",
    )

    return Agent(
        model=model,
        output_type=ComplianceReport,
        system_prompt=SYSTEM_PROMPT,
    )


# Create agent instance
agent = _create_agent()


@agent.tool_plain
def get_species_regulation(species: str) -> dict:
    """Look up fishing regulations for a species in the Pacific region.

    Args:
        species: The name of the fish species to look up.

    Returns:
        Dictionary with status, fine amount, and regulatory summary.
    """
    reg = PACIFIC_REGULATIONS.get(species)
    if reg:
        return reg
    return {
        "status": "unknown",
        "fine": 0,
        "summary": f"No regulatory data available for '{species}'."
    }


@agent.tool_plain
def send_alert_email(to: str, subject: str, body: str) -> str:
    """Send a compliance alert email via AWS SES.

    Use this tool when violations require immediate notification to compliance officers.

    Args:
        to: Email address of the recipient (compliance officer).
        subject: Email subject line.
        body: Full email body with violation details.

    Returns:
        Success or failure message.
    """
    global _email_was_sent

    success = send_email(to, subject, body)
    _email_was_sent = success

    if success:
        return "Email sent successfully."
    return "Email sending failed (check logs)."


async def run_compliance_review(audit_log: str) -> ComplianceReport:
    """
    Run the compliance agent on an audit log.

    Args:
        audit_log: Formatted string of the vessel's catch audit log.

    Returns:
        ComplianceReport with analysis and recommendations.
    """
    global _email_was_sent
    _email_was_sent = False

    # Get recipient email from env
    to_email = os.getenv("SES_TO_EMAIL", "compliance@example.com")

    # Add recipient info to the prompt
    user_prompt = f"""Review the following audit log and generate a compliance report.

If violations are found, send an alert email to: {to_email}

AUDIT LOG:
{audit_log}
"""

    result = await agent.run(user_prompt)

    # Update email_sent field based on actual tool call
    report = result.output
    report.email_sent = _email_was_sent

    return report
