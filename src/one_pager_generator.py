"""
one_pager_generator.py
Entry point for single-page HTML/PDF report output.

Pipeline:
  client_data + locked_numbers -> Claude-drafted report_plan -> HTML -> (optional) PDF

This file is the skeleton. Real Claude + HTML template implementations will replace
the placeholders below.
"""

import html as _html
import json as _json
import urllib.request as _urlreq
import urllib.error as _urlerr
from pathlib import Path
from datetime import datetime


def _esc(s) -> str:
    return _html.escape(str(s) if s is not None else "")


def _fmt_num(n) -> str:
    try:
        return f"{int(n):,}"
    except (ValueError, TypeError):
        return str(n)


REPORT_PLAN_INSTRUCTIONS = """You are generating a report plan for a monthly one-pager. Return ONLY valid JSON, no markdown, no explanation.

Return this exact JSON structure:
{
  "insights": [
    {"category": "CONVERSION", "text": "1-2 sentence insight about conversion"},
    {"category": "ENGAGEMENT", "text": "1-2 sentence insight about engagement"},
    {"category": "OPPORTUNITY", "text": "1-2 sentence insight about an opportunity or alert"}
  ],
  "action_item": "1-2 sentence recommendation for the client"
}

Rules:
- Return exactly 3 insights. Exactly 1 sentence, maximum 20 words. Be ruthlessly concise. Every word must earn its place.
- Categories must be one of: CONVERSION, ENGAGEMENT, OPPORTUNITY, CAMPAIGN, ALERT
- Use ONLY the exact numbers provided. Never calculate or derive new numbers.
- If account context is provided, use it to make insights specific to this client.
- Connect every number to a business meaning.
- The action_item should be specific and actionable, not generic."""


def _fallback_plan(client_name: str, period: str) -> dict:
    return {
        "client_name": client_name,
        "period": period,
        "kpi_cards": [
            {"metric": "bot_visits", "highlight": False},
            {"metric": "conversations", "highlight": False},
            {"metric": "goal_completions", "highlight": True},
            {"metric": "interaction_rate", "highlight": False},
        ],
        "sections": ["funnel", "top_selections", "explore_breakdown", "device_split"],
        "insights": [
            {"category": "CONVERSION", "text": "Placeholder insight 1"},
            {"category": "ENGAGEMENT", "text": "Placeholder insight 2"},
            {"category": "OPPORTUNITY", "text": "Placeholder insight 3"},
        ],
        "action_item": "Placeholder action item",
    }


def _strip_json_fences(text: str) -> str:
    if "```" in text:
        lines = text.split("\n")
        cleaned, inside = [], False
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            cleaned.append(line)
        text = "\n".join(cleaned).strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return text


def get_report_plan(client_data: dict, locked_numbers: dict, api_key: str, knowledge_dir: str) -> dict:
    """
    Ask Claude for the one-pager report plan (3 insights + action item).
    Falls back to a placeholder plan on any error.
    """
    client_name = client_data.get("client_name", "Client")
    period = (locked_numbers.get("overview") or {}).get("period_label", "")
    fallback = _fallback_plan(client_name, period)

    # 1. Load tars_brain.md
    brain_content = ""
    if knowledge_dir:
        brain_path = Path(knowledge_dir) / "_platform" / "tars_brain.md"
        if brain_path.exists():
            try:
                brain_content = brain_path.read_text(encoding="utf-8")
                print(f"  [one-pager] Loaded tars_brain.md ({len(brain_content)} chars)")
            except Exception as e:
                print(f"  [one-pager] Failed to read tars_brain.md: {e}")
        else:
            print(f"  [one-pager] tars_brain.md not found at {brain_path}")
    else:
        print("  [one-pager] knowledge_dir not provided — skipping tars_brain")

    # 2. Dossier
    dossier = client_data.get("dossier", "") or ""
    print(f"  [one-pager] Dossier: {'found' if dossier else 'not found'}")

    if not api_key:
        print("  [one-pager] ANTHROPIC_API_KEY not set — returning fallback plan")
        return fallback

    # 3. System prompt
    system_prompt = (
        brain_content + "\n\n" + REPORT_PLAN_INSTRUCTIONS
        if brain_content else REPORT_PLAN_INSTRUCTIONS
    )

    # 4. User message
    overview = locked_numbers.get("overview") or {}
    gambit_stats = locked_numbers.get("gambit_stats") or {}
    device = (locked_numbers.get("device_breakdown") or {}).get("breakdown") or {}
    funnel = locked_numbers.get("funnel") or {}

    top_gambits = sorted(
        gambit_stats.items(),
        key=lambda kv: kv[1].get("total_interactions", 0),
        reverse=True,
    )[:3]
    top_gambits_summary = {
        col: {
            "total_interactions": stats.get("total_interactions", 0),
            "options": {
                opt: {"count": d.get("count"), "percent": d.get("percent")}
                for opt, d in list((stats.get("options") or {}).items())[:6]
            },
        }
        for col, stats in top_gambits
    }

    parts = [f"CLIENT: {client_name}", f"PERIOD: {period}"]
    if dossier:
        parts.append("=== ACCOUNT CONTEXT ===\n" + dossier + "\n=== END ACCOUNT CONTEXT ===")
    parts.append("=== OVERVIEW NUMBERS ===\n" + _json.dumps(overview, indent=2))
    parts.append("=== TOP GAMBITS ===\n" + _json.dumps(top_gambits_summary, indent=2))
    parts.append("=== DEVICE BREAKDOWN ===\n" + _json.dumps(device, indent=2))
    if funnel:
        parts.append("=== FUNNEL ===\n" + _json.dumps(funnel, indent=2))
    parts.append("Generate the report plan JSON now.")
    user_message = "\n\n".join(parts)

    # 5. Call Claude API via urllib (no SDK)
    print("  [one-pager] Calling Claude API...")
    request_body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    req = _urlreq.Request(
        "https://api.anthropic.com/v1/messages",
        data=_json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with _urlreq.urlopen(req, timeout=60) as resp:
            response_data = _json.loads(resp.read().decode("utf-8"))
    except _urlerr.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"  [one-pager] Claude API error {e.code}: {err_body[:200]}")
        return fallback
    except Exception as e:
        print(f"  [one-pager] Claude API request failed: {e}")
        return fallback

    # 6. Parse response
    try:
        raw_text = response_data["content"][0]["text"].strip()
        parsed = _json.loads(_strip_json_fences(raw_text))
    except (KeyError, IndexError, _json.JSONDecodeError) as e:
        print(f"  [one-pager] Failed to parse Claude response: {e}")
        return fallback

    print("  [one-pager] Report plan received")
    return {
        "client_name": client_name,
        "period": period,
        "kpi_cards": fallback["kpi_cards"],
        "sections": fallback["sections"],
        "insights": parsed.get("insights", fallback["insights"]),
        "action_item": parsed.get("action_item", fallback["action_item"]),
    }


def render_html(report_plan: dict, locked_numbers: dict, assets: dict) -> str:
    """
    Render the 1440x810 single-page HTML report.
    Reads numbers defensively — skips any section whose data is missing.
    """
    # ── Extract data ──────────────────────────────────────────────────────────
    client_name = report_plan.get("client_name", "Client")
    period = report_plan.get("period", "")
    insights = report_plan.get("insights") or []
    action_item = report_plan.get("action_item") or ""

    overview = locked_numbers.get("overview") or {}
    device_breakdown = (locked_numbers.get("device_breakdown") or {}).get("breakdown") or {}
    gambit_stats = locked_numbers.get("gambit_stats") or {}
    trend_months = (locked_numbers.get("trend") or {}).get("months") or []
    funnel_data = locked_numbers.get("funnel") or {}

    bot_visits = overview.get("bot_visits", 0) or 0
    conversations = overview.get("conversations", 0) or 0
    goal_completions = overview.get("goal_completions", 0) or 0
    unique_visits = overview.get("unique_visits", 0) or 0
    unique_goals = overview.get("unique_goal_completions", 0) or 0
    goals_pct = overview.get("goals_achieved_percent", 0) or 0
    unique_goals_pct = overview.get("unique_goals_achieved_percent", 0) or 0

    interaction_rate = round((conversations / bot_visits) * 100) if bot_visits else 0

    # ── KPI cards ─────────────────────────────────────────────────────────────
    kpi_specs = [
        {"label": "Bot Visits", "value": bot_visits,
         "sub": f"{_fmt_num(unique_visits)} unique" if unique_visits else "",
         "accent": "#6B3FA0"},
        {"label": "Conversations", "value": conversations,
         "sub": f"{interaction_rate}% interaction" if interaction_rate else "",
         "accent": "#6B3FA0"},
        {"label": "Goal Completions", "value": goal_completions,
         "sub": f"{goals_pct}% conversion" if goals_pct else "",
         "accent": "#0D9668"},
        {"label": "Unique Goals", "value": unique_goals,
         "sub": f"{unique_goals_pct}% unique conv" if unique_goals_pct else "",
         "accent": "#0D9668"},
    ]
    kpi_cards_html = "".join(
        f'<div class="kpi-card" style="border-top-color:{s["accent"]};">'
        f'<div class="kpi-label">{_esc(s["label"])}</div>'
        f'<div class="kpi-value">{_fmt_num(s["value"])}</div>'
        f'<div class="kpi-sub">{_esc(s["sub"])}</div>'
        f'</div>'
        for s in kpi_specs if s["value"]
    )

    # ── Funnel section ────────────────────────────────────────────────────────
    funnel_steps = []
    if isinstance(funnel_data, dict) and funnel_data:
        for key, label in [
            ("visited", "Visited"),
            ("engaged", "Engaged"),
            ("explored", "Explored"),
            ("converted", "Converted"),
            ("reached_destination", "Reached Destination"),
        ]:
            v = funnel_data.get(key)
            if v is not None:
                funnel_steps.append({"label": label, "count": int(v)})

    if not funnel_steps:
        if bot_visits:
            funnel_steps.append({"label": "Bot Visits", "count": bot_visits})
        if conversations:
            funnel_steps.append({"label": "Conversations", "count": conversations})
        if goal_completions:
            funnel_steps.append({"label": "Goal Completions", "count": goal_completions})

    funnel_html = ""
    if funnel_steps:
        max_count = max((s["count"] for s in funnel_steps), default=1) or 1
        first_count = funnel_steps[0]["count"] or 1
        total_steps = len(funnel_steps)
        rows = []
        for i, step in enumerate(funnel_steps):
            width_pct = (step["count"] / max_count) * 100
            if total_steps >= 3 and i >= total_steps - 2:
                color = "#0D9668"
            else:
                color = "#6B3FA0"
            pct_first = round((step["count"] / first_count) * 100)
            rows.append(
                f'<div class="funnel-row">'
                f'<div class="funnel-label">{_esc(step["label"])}</div>'
                f'<div class="funnel-bar-wrap">'
                f'<div class="funnel-bar" style="width:{width_pct:.1f}%;background:{color};"></div>'
                f'<span class="funnel-count">{_fmt_num(step["count"])}</span>'
                f'<span class="funnel-pct">{pct_first}%</span>'
                f'</div></div>'
            )
        funnel_html = (
            '<div class="section">'
            '<div class="section-label">Conversion Funnel</div>'
            f'{"".join(rows)}'
            '</div>'
        )

    # ── What Users Explored ───────────────────────────────────────────────────
    # Left column uses the SECOND-ranked gambit by total_interactions so it never
    # duplicates the right column's "Top User Selections". If only one gambit
    # exists, this section is skipped entirely.
    explored_html = ""
    explore_key = None
    if gambit_stats:
        ranked_keys = sorted(
            gambit_stats.keys(),
            key=lambda kk: gambit_stats[kk].get("total_interactions", 0),
            reverse=True,
        )
        if len(ranked_keys) >= 2:
            explore_key = ranked_keys[1]

    if explore_key:
        opts = list((gambit_stats[explore_key].get("options") or {}).items())[:4]
        if opts:
            max_count = max((d["count"] for _, d in opts), default=1) or 1
            rows = []
            for opt, d in opts:
                width_pct = (d["count"] / max_count) * 100
                rows.append(
                    f'<div class="mini-row">'
                    f'<div class="mini-label">{_esc(opt)}</div>'
                    f'<div class="mini-bar-wrap">'
                    f'<div class="mini-bar" style="width:{width_pct:.1f}%;background:#B298D4;"></div>'
                    f'<span class="mini-count">{_fmt_num(d["count"])}</span>'
                    f'</div></div>'
                )
            explored_html = (
                '<div class="section">'
                '<div class="section-label">What Users Explored</div>'
                f'{"".join(rows)}'
                '</div>'
            )

    # ── Device Split ──────────────────────────────────────────────────────────
    device_html = ""
    if device_breakdown:
        total_devices = sum(d.get("count", 0) for d in device_breakdown.values())
        if total_devices:
            mobile_count = device_breakdown.get("Mobile", {}).get("count", 0)
            desktop_count = 0
            for k, v in device_breakdown.items():
                if k == "Mobile":
                    continue
                if "desktop" in k.lower():
                    desktop_count += v.get("count", 0)
            mobile_pct = round((mobile_count / total_devices) * 100) if mobile_count else 0
            desktop_pct = round((desktop_count / total_devices) * 100) if desktop_count else 0

            segs = []
            if mobile_pct:
                segs.append(
                    f'<div class="stacked-seg" style="width:{mobile_pct}%;background:#6B3FA0;">'
                    f'<span>Mobile {mobile_pct}%</span></div>'
                )
            if desktop_pct:
                segs.append(
                    f'<div class="stacked-seg" style="width:{desktop_pct}%;background:#B298D4;">'
                    f'<span>Desktop {desktop_pct}%</span></div>'
                )
            if mobile_pct >= desktop_pct and mobile_pct:
                ctx = f"Mobile-first audience — {mobile_pct}% on phones."
            elif desktop_pct:
                ctx = f"Desktop-heavy audience — {desktop_pct}% on laptops/desktops."
            else:
                ctx = ""
            device_html = (
                '<div class="section">'
                '<div class="section-label">Device Split</div>'
                f'<div class="stacked-bar">{"".join(segs)}</div>'
                f'<div class="device-context">{_esc(ctx)}</div>'
                '</div>'
            )

    # ── Key Insights ──────────────────────────────────────────────────────────
    category_colors = {
        "CONVERSION": ("#0D9668", "#ECFDF5"),
        "ENGAGEMENT": ("#6B3FA0", "#F3F0F8"),
        "OPPORTUNITY": ("#D4500A", "#FFF5F0"),
        "CAMPAIGN": ("#8C8FA3", "#F5F6FA"),
        "ALERT": ("#DC2626", "#FEF2F2"),
    }
    insights_html = ""
    if insights:
        rows = []
        for ins in insights[:4]:
            cat = (ins.get("category") or "ENGAGEMENT").upper()
            color, bg = category_colors.get(cat, ("#6B3FA0", "#F3F0F8"))
            rows.append(
                f'<div class="insight" style="background:{bg};border-left-color:{color};">'
                f'<div class="insight-cat" style="color:{color};">{_esc(cat)}</div>'
                f'<div class="insight-text">{_esc(ins.get("text", ""))}</div>'
                f'</div>'
            )
        insights_html = (
            '<div class="section">'
            '<div class="section-label">Key Insights</div>'
            f'{"".join(rows)}'
            '</div>'
        )

    # ── Action Item ───────────────────────────────────────────────────────────
    action_html = ""
    if action_item:
        action_html = (
            '<div class="action-box">'
            '<div class="action-label">Action Item</div>'
            f'<div class="action-text">{_esc(action_item)}</div>'
            '</div>'
        )

    # ── Top User Selections ───────────────────────────────────────────────────
    selections_html = ""
    if gambit_stats:
        top_key = max(
            gambit_stats.keys(),
            key=lambda kk: gambit_stats[kk].get("total_interactions", 0),
            default=None,
        )
        if top_key:
            all_opts = list((gambit_stats[top_key].get("options") or {}).items())
            is_apply = lambda name: ("apply" in name.lower()) or ("interested" in name.lower())

            # Top 6 by count (already sorted), then ensure any Apply/Interested
            # options from the full data make it into the list.
            opts = all_opts[:6]
            present = {o for o, _ in opts}
            missing_apply = [(o, d) for o, d in all_opts if is_apply(o) and o not in present]
            for ao in missing_apply:
                replaceable = [i for i, (o, _) in enumerate(opts) if not is_apply(o)]
                if not replaceable:
                    break
                opts[replaceable[-1]] = ao
            opts.sort(key=lambda x: x[1].get("count", 0), reverse=True)

            if opts:
                max_count = max((d["count"] for _, d in opts), default=1) or 1
                rows = []
                for opt, d in opts:
                    ol = opt.lower()
                    if "apply" in ol or "interested" in ol:
                        bar_color = "#0D9668"
                    elif "fee" in ol or "cost" in ol:
                        bar_color = "#D4500A"
                    else:
                        bar_color = "#6B3FA0"
                    width_pct = (d["count"] / max_count) * 100
                    rows.append(
                        f'<div class="sel-row">'
                        f'<div class="sel-label">{_esc(opt)}</div>'
                        f'<div class="sel-bar-wrap">'
                        f'<div class="sel-bar" style="width:{width_pct:.1f}%;background:{bar_color};"></div>'
                        f'<span class="sel-count">{_fmt_num(d["count"])}</span>'
                        f'</div></div>'
                    )
                selections_html = (
                    '<div class="section">'
                    '<div class="section-label">Top User Selections</div>'
                    f'{"".join(rows)}'
                    '</div>'
                )

    # ── Monthly Trend table ───────────────────────────────────────────────────
    trend_html = ""
    if len(trend_months) >= 2:
        last_i = len(trend_months) - 1
        rows = []
        for i, m in enumerate(trend_months):
            cls = "trend-highlight" if i == last_i else ""
            rows.append(
                f'<tr class="{cls}">'
                f'<td>{_esc(m.get("month_label", ""))}</td>'
                f'<td>{_fmt_num(m.get("bot_visits", 0))}</td>'
                f'<td>{_fmt_num(m.get("conversations", 0))}</td>'
                f'<td>{_fmt_num(m.get("goal_completions", 0))}</td>'
                f'<td>{_esc(m.get("goals_achieved_percent", 0))}%</td>'
                f'</tr>'
            )
        trend_html = (
            '<div class="section">'
            '<div class="section-label">Monthly Trend</div>'
            '<table class="trend-table">'
            '<thead><tr><th>Month</th><th>Visits</th><th>Convos</th><th>Goals</th><th>Conv%</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody>'
            '</table>'
            '</div>'
        )

    # ── CSS (plain string, no interpolation) ──────────────────────────────────
    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 1440px; height: 810px; overflow: hidden;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  background: #ffffff; color: #1B1D2A;
}
.page { width: 1440px; height: 810px; display: flex; flex-direction: column; }

/* Header */
.header {
  height: 60px; padding: 0 28px;
  background: linear-gradient(90deg, #2D1B69 0%, #8B5FBF 100%);
  color: #ffffff; display: flex; align-items: center; justify-content: space-between;
}
.header-left { display: flex; align-items: center; gap: 14px; }
.brand { font-size: 20px; font-weight: 700; letter-spacing: 1.5px; }
.sep { width: 1px; height: 22px; background: rgba(255,255,255,0.4); }
.client { font-size: 15px; font-weight: 500; opacity: 0.95; }
.period-pill {
  padding: 6px 14px; font-size: 11px; font-weight: 600;
  background: rgba(255,255,255,0.15); border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.3); letter-spacing: 0.5px;
}

/* KPI row */
.kpi-row {
  height: 82px; padding: 10px 28px;
  display: flex; gap: 14px; background: #FAFAFC;
  border-bottom: 1px solid #E8E9F0;
}
.kpi-card {
  flex: 1; background: #ffffff; border: 1px solid #E8E9F0; border-top: 3px solid #6B3FA0;
  border-radius: 6px; padding: 8px 14px; display: flex; flex-direction: column;
  justify-content: center;
}
.kpi-label {
  font-size: 9.5px; font-weight: 700; letter-spacing: 1.2px; color: #6B3FA0;
  text-transform: uppercase;
}
.kpi-value { font-size: 28px; font-weight: 700; color: #1B1D2A; line-height: 1.1; margin-top: 2px; }
.kpi-sub { font-size: 10px; color: #8C8FA3; margin-top: 2px; }

/* Main content */
.main {
  flex: 1; display: grid; grid-template-columns: 330px 1fr 330px;
  gap: 16px; padding: 14px 28px;
}
.col { display: flex; flex-direction: column; gap: 12px; overflow: hidden; }

/* Sections */
.section {
  background: #ffffff; border: 1px solid #E8E9F0; border-radius: 6px; padding: 10px 12px;
}
.section-label {
  font-size: 9.5px; font-weight: 700; letter-spacing: 1.2px; color: #6B3FA0;
  text-transform: uppercase; margin-bottom: 8px;
}

/* Funnel */
.funnel-row { margin-bottom: 6px; }
.funnel-label { font-size: 10px; color: #1B1D2A; margin-bottom: 3px; font-weight: 500; }
.funnel-bar-wrap {
  position: relative; height: 20px; background: #F3F0F8; border-radius: 4px; overflow: hidden;
}
.funnel-bar { height: 100%; border-radius: 4px; }
.funnel-count {
  position: absolute; right: 40px; top: 50%; transform: translateY(-50%);
  font-size: 10px; font-weight: 600; color: #1B1D2A;
}
.funnel-pct {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  font-size: 9.5px; color: #8C8FA3;
}

/* Mini rows (explored / selections) */
.mini-row, .sel-row { margin-bottom: 5px; }
.mini-label, .sel-label {
  font-size: 10px; color: #1B1D2A; margin-bottom: 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mini-bar-wrap, .sel-bar-wrap {
  position: relative; height: 14px; background: #F3F0F8; border-radius: 3px; overflow: hidden;
}
.mini-bar, .sel-bar { height: 100%; border-radius: 3px; }
.mini-count, .sel-count {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  font-size: 9.5px; font-weight: 600; color: #1B1D2A;
}

/* Device split */
.stacked-bar {
  display: flex; height: 26px; border-radius: 4px; overflow: hidden; border: 1px solid #E8E9F0;
}
.stacked-seg {
  display: flex; align-items: center; justify-content: center;
  color: #ffffff; font-size: 10px; font-weight: 600;
}
.device-context { font-size: 10px; color: #8C8FA3; margin-top: 6px; }

/* Insights */
.insight {
  border-left: 3px solid #6B3FA0; padding: 8px 10px; margin-bottom: 7px; border-radius: 3px;
}
.insight-cat {
  font-size: 9px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  margin-bottom: 3px;
}
.insight-text { font-size: 12px; line-height: 1.35; color: #1B1D2A; }

/* Action box */
.action-box {
  background: linear-gradient(135deg, #2D1B69 0%, #6B3FA0 100%);
  color: #ffffff; padding: 10px 14px; border-radius: 6px;
}
.action-label {
  font-size: 9px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase;
  opacity: 0.85; margin-bottom: 3px;
}
.action-text { font-size: 12px; line-height: 1.35; font-weight: 500; }

/* Trend table */
.trend-table { width: 100%; border-collapse: collapse; font-size: 10px; }
.trend-table th {
  background: #FAFAFC; color: #6B3FA0; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; font-size: 9px; padding: 5px 6px;
  border-bottom: 1px solid #E8E9F0; text-align: left;
}
.trend-table td {
  padding: 5px 6px; border-bottom: 1px solid #F3F0F8; color: #1B1D2A;
}
.trend-table tr.trend-highlight td {
  background: #F3F0F8; font-weight: 700; color: #2D1B69;
}

/* Footer */
.footer {
  height: 30px; padding: 0 28px; display: flex; align-items: center;
  justify-content: space-between; font-size: 10px; color: #8C8FA3;
  border-top: 1px solid #E8E9F0; background: #FAFAFC;
}
"""

    # ── Assemble ──────────────────────────────────────────────────────────────
    footer_right = f"Bot: {_esc(client_name)} · {_esc(period)} · team@hellotars.com"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(client_name)} — One-Pager</title>
<style>{css}</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-left">
      <div class="brand">TARS</div>
      <div class="sep"></div>
      <div class="client">{_esc(client_name)}</div>
    </div>
    <div class="period-pill">{_esc(period)}</div>
  </div>
  <div class="kpi-row">{kpi_cards_html}</div>
  <div class="main">
    <div class="col">
      {funnel_html}
      {explored_html}
      {device_html}
    </div>
    <div class="col">
      {insights_html}
      {action_html}
    </div>
    <div class="col">
      {selections_html}
      {trend_html}
    </div>
  </div>
  <div class="footer">
    <div>Generated by TARS AI Platform</div>
    <div>{footer_right}</div>
  </div>
</div>
</body>
</html>"""


def save_report(html: str, output_dir: str, client_name: str, month: str) -> tuple[str, str | None]:
    """
    Save HTML to disk and attempt PDF conversion via pdfkit at 1440x810 with zero margins.
    Returns (html_path, pdf_path_or_none).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base_name = f"{client_name}_{month}_one_pager_{timestamp}"
    html_path = output_dir / f"{base_name}.html"
    pdf_path = output_dir / f"{base_name}.pdf"

    html_path.write_text(html, encoding="utf-8")
    print(f"  💾 Saved HTML: {html_path}")

    pdf_output: str | None = None
    try:
        import pdfkit

        options = {
            "page-width": "1440px",
            "page-height": "810px",
            "margin-top": "0",
            "margin-right": "0",
            "margin-bottom": "0",
            "margin-left": "0",
            "encoding": "UTF-8",
            "print-media-type": None,
            "enable-local-file-access": None,
        }

        pdfkit.from_string(html, str(pdf_path), options=options)
        pdf_output = str(pdf_path)
        print(f"  💾 Saved PDF:  {pdf_path}")
    except ImportError:
        print("  ⚠️  pdfkit not installed — skipping PDF conversion.")
        print("     Install with: pip install pdfkit (and install wkhtmltopdf)")
    except Exception as e:
        print(f"  ⚠️  PDF conversion failed: {e}")

    return str(html_path), pdf_output


def generate_one_pager(
    client_data: dict,
    locked_numbers: dict,
    output_dir: str,
    api_key: str,
    knowledge_dir: str,
) -> str:
    """
    Orchestrate the one-pager pipeline: plan -> render -> save.
    Returns the HTML output path.
    """
    print("\n📄 Generating one-pager...")

    report_plan = get_report_plan(client_data, locked_numbers, api_key, knowledge_dir)
    html = render_html(report_plan, locked_numbers, client_data.get("assets", {}))

    client_name = client_data.get("client_name", "Client")
    month = client_data.get("target_month", "")
    html_path, _pdf_path = save_report(html, output_dir, client_name, month)

    return html_path
