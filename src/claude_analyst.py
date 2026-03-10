"""
claude_analyst.py
Sends structured client data to Claude API.
Claude decides what slides to make, writes all insights, structures all tables.
Returns a complete slide plan as JSON.
"""

import json
import os


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
- "conversion_funnel": Specific conversion analysis (e.g. upgrade offer → apply)
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


def get_slide_plan(client_data: dict) -> dict:
    """Call Claude API and get back a structured slide plan."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found!\n"
            "Please set it in your .env file:\n"
            "  ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx"
        )

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    print("  🤖 Sending data to Claude for analysis...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_prompt(client_data)}
        ]
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code blocks if Claude added them
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        slide_plan = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON: {e}\n"
            f"Response was:\n{response_text[:500]}"
        )

    print(f"  ✅ Claude generated {len(slide_plan.get('slides', []))} slides")
    return slide_plan
