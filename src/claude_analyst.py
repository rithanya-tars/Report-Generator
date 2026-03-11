"""
claude_analyst.py
Sends structured client data to Claude via Claude Code CLI.
No API key needed — uses your Claude Code subscription (Max plan).
Returns a complete slide plan as JSON.
"""

import json
import os
import subprocess
import shutil


SYSTEM_PROMPT = """You are an expert business analyst at Tars, a conversational AI platform. 
You create monthly Business Review reports for clients showing chatbot performance.

Your job: Analyze the data provided and return a COMPLETE slide plan as JSON.

RULES:
1. Be data-driven - every insight must reference specific numbers
2. Be dynamic - decide how many slides based on what data exists
3. Be honest - if data shows decline, say so with possible reasons
4. Write in clear business English - clients are non-technical
5. ALWAYS verify numbers match exactly what's in the data - accuracy is critical
6. Return ONLY valid JSON, no markdown, no explanation outside the JSON

SLIDE TYPES you can use (choose what makes sense for the data):
- "cover": Title slide with client name and period
- "overview_stats": Key metrics in big number cards  
- "monthly_trend": Table + bar chart of visits/conversations across months
- "user_journey": How users navigate through the chatbot (gambit flow)
- "conversion_funnel": Specific conversion analysis (e.g. upgrade offer -> apply)
- "device_breakdown": Mobile vs desktop split
- "gambit_analysis": Detailed breakdown of specific gambit options chosen
- "insights_summary": Key takeaways in bullet form
- "next_steps": Recommendations for improvements
- "contact": Get in touch slide

OUTPUT FORMAT (strict JSON):
{
  "report_title": "Business Review - [Client] - [Period]",
  "period_label": "November 2025 to February 2026",
  "slides": [
    {
      "type": "cover",
      "title": "Business Review",
      "subtitle": "November 2025 to February 2026"
    },
    {
      "type": "overview_stats",
      "title": "Performance Overview",
      "period": "January 2026",
      "stats": [
        {"label": "All Bot Visits", "value": "572", "note": null},
        {"label": "Bot Conversations", "value": "398", "note": null},
        {"label": "Goal Completions", "value": "123", "note": "31% rate"},
        {"label": "Interaction Rate", "value": "36.3%", "note": null}
      ],
      "insights": ["Key insight 1", "Key insight 2"]
    },
    {
      "type": "monthly_trend",
      "title": "Visits & Conversations - Over the Months",
      "headers": ["Month", "Bot Visits", "Conversations", "Goals", "Goals %", "Unique Visits", "Unique Convos", "Unique Goals", "Unique Goals %"],
      "rows": [
        ["Nov'25", "282", "174", "42", "24%", "77", "58", "31", "53%"]
      ],
      "chart_data": {
        "labels": ["Nov'25", "Dec'25"],
        "bot_visits": [282, 203],
        "conversations": [174, 124]
      },
      "insights": ["Key trend insight"]
    },
    {
      "type": "insights_summary",
      "title": "Key Insights",
      "insights": ["Insight 1", "Insight 2", "Insight 3"]
    },
    {
      "type": "next_steps",
      "title": "Next Steps for Improvements",
      "items": ["Recommendation 1", "Recommendation 2"]
    },
    {
      "type": "contact",
      "email": "team@hellotars.com",
      "website": "www.hellotars.com",
      "social": "@hellotars.ai"
    }
  ]
}
"""


def build_prompt(client_data: dict) -> str:
    """Build the user prompt with all client data."""
    return f"""Analyze this Tars chatbot performance data and create a complete Business Review slide plan.

CLIENT: {client_data['client_name']}
TARGET MONTH: {client_data['target_month']}

=== CURRENT MONTH DATA ===
{json.dumps(client_data['current_month'], indent=2)}

=== HISTORICAL MONTHS (for trend analysis) ===
{json.dumps(client_data['historical_months'], indent=2)}

=== ALL MONTHS SUMMARY TABLE ===
{json.dumps(client_data['all_months_summary'], indent=2)}

Based on this data:
1. Decide which slides make sense (don't add slides if data doesn't support them)
2. Write specific, accurate insights with exact numbers
3. Structure tables with only the columns that have meaningful data
4. If there are gambit distributions in csv_analysis, create a user journey slide
5. If there are multiple months, create a trend slide
6. Always include: cover, overview_stats (for current month), insights_summary, next_steps, contact
7. The period_label in cover should reflect ALL months in the report, not just current month

Return ONLY the JSON slide plan. No other text."""


def get_slide_plan(client_data: dict, debug: bool = False) -> dict:
    """Call Claude via Claude Code CLI — uses Max subscription, no API key needed."""

    if not shutil.which("claude"):
        raise EnvironmentError(
            "Claude Code CLI not found!\n"
            "Install it with: npm install -g @anthropic-ai/claude-code\n"
            "Then login with: claude"
        )

    print("  🤖 Sending data to Claude for analysis...")

    full_prompt = f"{SYSTEM_PROMPT}\n\n{build_prompt(client_data)}"

    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError("Claude took too long to respond. Please try again.")
    except FileNotFoundError:
        raise EnvironmentError(
            "Claude Code CLI not found!\n"
            "Install it with: npm install -g @anthropic-ai/claude-code\n"
            "Then login with: claude"
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude Code CLI error:\n{result.stderr.strip()}\n"
            "Make sure you are logged in by running: claude"
        )

    response_text = result.stdout.strip()

    if debug:
        with open("debug_claude_raw.txt", "w") as f:
            f.write(response_text)
        print("  🐛 Raw Claude response saved to: debug_claude_raw.txt")

    # Strip markdown code blocks if present
    if "```" in response_text:
        lines = response_text.split("\n")
        cleaned, inside = [], False
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            cleaned.append(line)
        response_text = "\n".join(cleaned).strip()

    # Extract JSON object from response
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start != -1 and end > start:
        response_text = response_text[start:end]

    try:
        slide_plan = json.loads(response_text)
    except json.JSONDecodeError as e:
        if debug:
            with open("debug_parse_error.txt", "w") as f:
                f.write(response_text)
        raise ValueError(
            f"Claude returned invalid JSON: {e}\n"
            f"Response preview:\n{response_text[:500]}\n"
            "Run with --debug flag to save the full response."
        )

    if debug:
        with open("debug_slide_plan.json", "w") as f:
            json.dump(slide_plan, f, indent=2)
        print("  🐛 Parsed slide plan saved to: debug_slide_plan.json")

    print(f"  ✅ Claude generated {len(slide_plan.get('slides', []))} slides")
    return slide_plan
