"""
one_pager_generator.py
Entry point for single-page HTML/PDF report output.

Pipeline:
  client_data + locked_numbers -> Claude-drafted report_plan -> HTML -> (optional) PDF

This file is the skeleton. Real Claude + HTML template implementations will replace
the placeholders below.
"""

from pathlib import Path
from datetime import datetime


def get_report_plan(client_data: dict, locked_numbers: dict, api_key: str, knowledge_dir: str) -> dict:
    """
    Ask Claude for a one-pager report plan (KPI cards, sections, insights, action item).
    Placeholder: returns a hardcoded sample plan.
    """
    print("  [one-pager] get_report_plan() — placeholder (no Claude call yet)")

    return {
        "client_name": client_data.get("client_name", "Client"),
        "period": locked_numbers.get("overview", {}).get("period_label", ""),
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


def render_html(report_plan: dict, locked_numbers: dict, assets: dict) -> str:
    """
    Render the one-pager HTML from the report plan + locked numbers.
    Placeholder: returns a stub document.
    """
    print("  [one-pager] render_html() — placeholder stub")
    return "<html><body><h1>One-pager coming soon</h1></body></html>"


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
