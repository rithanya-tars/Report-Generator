"""
claude_analyst.py
Claude decides slide structure, titles, layout and writes short bullet-point insights.
All numbers are pre-calculated by number_calculator.py and passed via locked_numbers.
Claude must use ONLY the exact numbers provided — never calculate, derive, or modify them.
"""

import json
import os


SYSTEM_PROMPT = """You are an expert business analyst at Tars, a conversational AI platform.
You create monthly Business Review reports for clients showing chatbot performance.

Your job: Analyze the data provided and return a COMPLETE slide plan as JSON.

=== ABSOLUTE RULES ===
1. Use ONLY the exact numbers provided to you. NEVER calculate, derive, estimate, round,
   average, sum, subtract, or modify any numbers. If a number is "572", write "572" — not
   "~570", not "approximately 600", not "nearly 600". Copy numbers exactly as given.
2. Do NOT invent any numbers that are not in the data provided.
3. Do NOT perform any arithmetic on the numbers (no percentages, no differences, no totals).
   If you need a comparison like "increased by X", that number MUST already be in the data.
   Otherwise just say "increased" or "decreased" without inventing a delta.
4. Every insight must be a short bullet point (1 sentence max), not a paragraph.
5. Be honest — if data shows decline, say so with possible reasons.
6. Write in clear business English — clients are non-technical.
7. Return ONLY valid JSON, no markdown, no explanation outside the JSON.

SLIDE TYPES you can use (choose what makes sense for the data):
- "cover": Title slide with client name and period
- "overview_stats": Key metrics in big number cards
- "monthly_trend": Table + bar chart of visits/conversations across months
- "device_breakdown": Mobile vs desktop split
- "gambit_analysis": Detailed breakdown of specific gambit/button options chosen
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
      "insights": [
        "Short bullet insight referencing exact numbers",
        "Another short bullet insight"
      ]
    },
    {
      "type": "monthly_trend",
      "title": "Visits & Conversations - Over the Months",
      "insights": [
        "Short bullet about the trend using exact numbers from the table"
      ]
    },
    {
      "type": "device_breakdown",
      "title": "Device Breakdown",
      "insights": [
        "Short bullet about device split using exact numbers"
      ]
    },
    {
      "type": "gambit_analysis",
      "title": "User Selections - [Column Name]",
      "gambit_column": "column_name_here",
      "insights": [
        "Short bullet about what users selected"
      ]
    },
    {
      "type": "insights_summary",
      "title": "Key Insights",
      "insights": [
        "Takeaway 1",
        "Takeaway 2",
        "Takeaway 3",
        "Takeaway 4"
      ]
    },
    {
      "type": "next_steps",
      "title": "Next Steps for Improvements",
      "items": [
        "Specific recommendation 1",
        "Specific recommendation 2",
        "Specific recommendation 3"
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
    Build prompt with all verified numbers and multi-month historical data.
    Claude decides structure/titles/layout and writes short bullet insights.
    """
    overview = locked_numbers.get("overview", {})
    device = locked_numbers.get("device_breakdown", {})
    gambits = locked_numbers.get("gambit_stats", {})
    trend = locked_numbers.get("trend", {})
    duration = locked_numbers.get("duration", {})
    gambit_cols = locked_numbers.get("gambit_columns", [])

    # Build explicit gambit counts so Claude cannot recalculate
    gambit_explicit_lines = []
    for col, stats in gambits.items():
        options = stats.get("options", {})
        total = stats.get("total_interactions", 0)
        if not options:
            continue
        gambit_explicit_lines.append(f"\n--- {col} exact counts (total interactions: {total}) ---")
        for i, (opt, d) in enumerate(options.items(), 1):
            gambit_explicit_lines.append(
                f"  {i}. {opt} = {d['count']} total ({d['percent']})"
            )
    gambit_explicit_block = "\n".join(gambit_explicit_lines) if gambit_explicit_lines else "No gambit data available."

    # Include full historical data so Claude can compare months
    historical_months = client_data.get("historical_months", [])
    all_months_summary = client_data.get("all_months_summary", [])

    # Build historical details outside f-string to avoid brace escaping issues
    hist_details = [
        {"month": m.get("month"), "analyze": m.get("analyze", {})}
        for m in historical_months
    ]
    hist_json = json.dumps(hist_details, indent=2)

    # Client config context for Claude
    client_config = client_data.get("client_config", {})
    config_context = ""
    if client_config:
        bot_type = client_config.get("bot_type", "gambit")
        goal_def = client_config.get("goal_definition", "")
        key_columns = client_config.get("key_columns", [])
        context_note = client_config.get("context", "")
        config_lines = [f"BOT TYPE: {bot_type}"]
        if goal_def:
            config_lines.append(f"GOAL DEFINITION: {goal_def}")
        if key_columns:
            config_lines.append(f"KEY COLUMNS TO FOCUS ON: {', '.join(key_columns)}")
        if context_note:
            config_lines.append(f"CLIENT CONTEXT: {context_note}")
        config_context = "\n=== CLIENT CONFIGURATION ===\n" + "\n".join(config_lines) + "\n"

    return f"""Analyze this Tars chatbot performance data and create a complete Business Review slide plan.

CLIENT: {client_data['client_name']}
TARGET MONTH: {client_data['target_month']}
{config_context}

=== CRITICAL RULE ===
You must use ONLY the exact numbers below. NEVER calculate, derive, round, or modify them.
Copy numbers exactly as they appear. Do NOT compute differences, averages, or percentages yourself.
Write each insight as a short bullet point (1 sentence), not a paragraph.

=== VERIFIED NUMBERS (use these exactly — do not change) ===

OVERVIEW STATS (current month):
- Bot Visits: {overview.get('bot_visits', 0):,}
- Conversations: {overview.get('conversations', 0):,}
- Goal Completions: {overview.get('goal_completions', 0):,}
- Goals Achieved %: {overview.get('goals_achieved_percent', 0)}%
- Unique Visits: {overview.get('unique_visits', 0):,}
- Unique Conversations: {overview.get('unique_conversations', 0):,}
- Unique Goal Completions: {overview.get('unique_goal_completions', 0):,}
- Unique Goals Achieved %: {overview.get('unique_goals_achieved_percent', 0)}%
- Period: {overview.get('period_label', client_data['target_month'])}

MONTHLY TREND (all months — use for comparisons):
{json.dumps(trend.get('months', []), indent=2)}

ALL MONTHS SUMMARY:
{json.dumps(all_months_summary, indent=2)}

DEVICE BREAKDOWN:
{json.dumps(device.get('breakdown', {}), indent=2)}

GAMBIT / BUTTON SELECTIONS (EXACT COUNTS — READ CAREFULLY):
{gambit_explicit_block}

*** WARNING: THE ABOVE ARE THE ONLY NUMBERS YOU MAY USE FOR GAMBIT INSIGHTS. ***
*** Do not count rows. Do not calculate. Do not estimate. Do not use any other counts. ***
*** Copy these numbers EXACTLY into your gambit_analysis insights. ***

CONVERSATION DURATION:
{json.dumps(duration, indent=2)}

=== HISTORICAL MONTH DETAILS ===
{hist_json}

=== YOUR TASK ===
Based on the above data:
1. Decide which slides make sense (don't add slides if data doesn't support them)
2. Choose appropriate titles for each slide
3. Write short bullet-point insights (1 sentence each) referencing exact numbers from above
4. If there are gambit distributions, create gambit_analysis slides for the most interesting columns: {gambit_cols[:3]}
5. If there are multiple months, create a monthly_trend slide comparing them
6. Always include: cover, overview_stats, insights_summary, next_steps, contact
7. The period_label in cover should reflect ALL months in the data, not just current month

Return ONLY the JSON slide plan. No other text."""


def get_slide_plan(client_data: dict, locked_numbers: dict, debug: bool = False) -> dict:
    """
    Call Claude API — Claude decides slide structure, titles, and writes insights.
    Numbers are already locked in locked_numbers dict and will be injected by pptx_generator.
    Claude must use ONLY the exact numbers provided.
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

    print("  🤖 Sending data to Claude for analysis...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
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

    print(f"  ✅ Claude generated {len(slide_plan.get('slides', []))} slides")
    return slide_plan
