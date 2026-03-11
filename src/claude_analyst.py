"""
claude_analyst.py
Claude's ONLY job is to write insights and text — never numbers.
All numbers are pre-calculated by number_calculator.py and passed in directly.
This ensures 100% data accuracy in reports.
"""

import json
import os


SYSTEM_PROMPT = """You are an expert business analyst at Tars, a conversational AI platform.
You create monthly Business Review reports for clients showing chatbot performance.

IMPORTANT: You will be given pre-calculated numbers. Do NOT change, recalculate, or 
second-guess these numbers. They are verified directly from raw data.

Your ONLY job is to:
1. Decide which slide types make sense given the data available
2. Write clear, specific insights that reference the numbers given to you
3. Write recommendations for next steps
4. Return a JSON slide plan with the structure shown below

RULES:
- Reference exact numbers in insights (use what you are given)
- Be honest — if data shows decline, say so with possible reasons  
- Write in clear business English — clients are non-technical
- Only include slides where data exists to support them
- Return ONLY valid JSON, no markdown, no explanation outside the JSON
- Do NOT invent or estimate any numbers

SLIDE TYPES:
- "cover": Title slide
- "overview_stats": Big number stat cards (numbers will be injected — just write insights)
- "monthly_trend": Month by month table (data will be injected — just write insights)
- "device_breakdown": Mobile vs Desktop (data will be injected — just write insights)
- "gambit_analysis": Button/option choices breakdown (data will be injected — just write insights)
- "insights_summary": Key takeaways in bullet points
- "next_steps": Recommendations for improvement
- "contact": Get in touch slide

OUTPUT FORMAT — return exactly this structure:
{
  "report_title": "Business Review - ClientName - Period",
  "slides": [
    {
      "type": "cover",
      "title": "Business Review",
      "subtitle": "January 2026"
    },
    {
      "type": "overview_stats",
      "insights": [
        "Write 2-3 key insights about the overview numbers here"
      ]
    },
    {
      "type": "monthly_trend",
      "insights": [
        "Write 2-3 insights about the monthly trend here"
      ]
    },
    {
      "type": "device_breakdown",
      "insights": [
        "Write 1-2 insights about device usage here"
      ]
    },
    {
      "type": "gambit_analysis",
      "gambit_column": "main_menu",
      "insights": [
        "Write 2-3 insights about what users selected here"
      ]
    },
    {
      "type": "insights_summary",
      "insights": [
        "Top 4-5 overall takeaways from the data"
      ]
    },
    {
      "type": "next_steps",
      "items": [
        "Specific recommendation 1",
        "Specific recommendation 2"
      ]
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


def build_prompt(client_data: dict, locked_numbers: dict) -> str:
    """
    Build prompt for Claude — numbers already calculated, Claude just writes insights.
    """
    overview = locked_numbers.get("overview", {})
    device = locked_numbers.get("device_breakdown", {})
    gambits = locked_numbers.get("gambit_stats", {})
    trend = locked_numbers.get("trend", {})
    duration = locked_numbers.get("duration", {})
    gambit_cols = locked_numbers.get("gambit_columns", [])

    # Summarize gambit data for Claude
    gambit_summary = {}
    for col, stats in gambits.items():
        gambit_summary[col] = {
            opt: f"{d['count']} selections ({d['percent']})"
            for opt, d in stats.get("options", {}).items()
        }

    return f"""Write insights for a Business Review report for {client_data['client_name']}.

PERIOD: {overview.get('period_label', client_data['target_month'])}

=== VERIFIED NUMBERS (do not change these) ===

OVERVIEW STATS:
- Bot Visits: {overview.get('bot_visits', 0):,}
- Conversations: {overview.get('conversations', 0):,}
- Goal Completions: {overview.get('goal_completions', 0):,}
- Goals Achieved %: {overview.get('goals_achieved_percent', 0)}%
- Unique Visits: {overview.get('unique_visits', 0):,}
- Unique Conversations: {overview.get('unique_conversations', 0):,}
- Unique Goal Completions: {overview.get('unique_goal_completions', 0):,}
- Unique Goals Achieved %: {overview.get('unique_goals_achieved_percent', 0)}%

MONTHLY TREND:
{json.dumps([m for m in trend.get('months', [])], indent=2)}

DEVICE BREAKDOWN:
{json.dumps(device.get('breakdown', {}), indent=2)}

GAMBIT / BUTTON SELECTIONS:
{json.dumps(gambit_summary, indent=2)}

CONVERSATION DURATION:
{json.dumps(duration, indent=2)}

=== YOUR TASK ===
Based on the above numbers:
1. Decide which slides make sense (skip device_breakdown if no device data, etc.)
2. Write specific insights referencing the exact numbers above
3. Include gambit_analysis slides for the most interesting gambit columns: {gambit_cols[:3]}
4. Always include: cover, overview_stats, insights_summary, next_steps, contact

Return ONLY the JSON slide plan. No other text."""


def get_slide_plan(client_data: dict, locked_numbers: dict, debug: bool = False) -> dict:
    """
    Call Claude API — only for writing insights, never for numbers.
    Numbers are already locked in locked_numbers dict.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found!\n"
            "Please set it in your .env file:\n"
            "  ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx"
        )

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    print("  🤖 Sending data to Claude for insights...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_prompt(client_data, locked_numbers)}
        ]
    )

    response_text = message.content[0].text.strip()

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

    # Extract JSON
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
        print("  🐛 Slide plan saved to: debug_slide_plan.json")

    print(f"  ✅ Claude wrote insights for {len(slide_plan.get('slides', []))} slides")
    return slide_plan
