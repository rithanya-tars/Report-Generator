#!/usr/bin/env python3
"""
generate.py — Tars Report Generator
====================================
Usage:
  python generate.py --client Amex --month 2026-02 --data /path/to/TarsReports

Options:
  --client    Client folder name (e.g. Amex, AmenClinics)
  --month     Target month in YYYY-MM format (e.g. 2026-02)
  --data      Path to your TarsReports folder (or set TARS_DATA_PATH in .env)
  --dry-run   Process data and show what Claude would receive, without calling API
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional, env vars can be set manually

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_processor import load_client_data
from claude_analyst import get_slide_plan
from pptx_generator import generate_pptx
from pdf_converter import convert_pptx_to_pdf


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tars Report Generator — Create monthly business review decks automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py --client Amex --month 2026-02
  python generate.py --client AmenClinics --month 2026-03 --data /Users/john/TarsReports
  python generate.py --client Amex --month 2026-02 --dry-run
        """
    )
    parser.add_argument("--client", required=True,
                        help="Client folder name (must match folder name exactly)")
    parser.add_argument("--month", required=True,
                        help="Month to generate report for (YYYY-MM format)")
    parser.add_argument("--data", default=None,
                        help="Path to TarsReports folder (overrides TARS_DATA_PATH in .env)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show processed data without calling Claude API or generating files")
    return parser.parse_args()


def validate_month(month: str):
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        print(f"❌ Invalid month format: '{month}'. Use YYYY-MM (e.g. 2026-02)")
        sys.exit(1)


def get_data_path(args_data: str | None) -> str:
    data_path = args_data or os.environ.get("TARS_DATA_PATH")
    if not data_path:
        print("❌ No data path provided!")
        print("   Either:")
        print("   1. Pass --data /path/to/TarsReports")
        print("   2. Set TARS_DATA_PATH=/path/to/TarsReports in your .env file")
        sys.exit(1)
    if not Path(data_path).exists():
        print(f"❌ TarsReports folder not found: {data_path}")
        sys.exit(1)
    return data_path


def main():
    args = parse_args()

    print("\n" + "="*60)
    print("  🚀 Tars Report Generator")
    print("="*60)
    print(f"  Client : {args.client}")
    print(f"  Month  : {args.month}")
    print(f"  Mode   : {'DRY RUN (no API call)' if args.dry_run else 'FULL GENERATION'}")
    print("="*60 + "\n")

    # Validate inputs
    validate_month(args.month)
    data_path = get_data_path(args.data)

    # ── Step 1: Load and process data ──────────────────────────────────────────
    print("📂 Step 1: Loading client data...")
    try:
        client_data = load_client_data(data_path, args.client, args.month)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        sys.exit(1)

    months_found = len(client_data["historical_months"]) + 1
    print(f"  ✅ Found {months_found} month(s) of data for {args.client}")
    print(f"  ✅ Current month: {client_data['target_month']}")
    has_raw = client_data["current_month"]["has_raw_data"]
    print(f"  ✅ Raw CSV data: {'Yes' if has_raw else 'No (analyze.json only)'}")

    if args.dry_run:
        print("\n📋 DRY RUN — Showing processed data structure:\n")
        print(json.dumps(client_data, indent=2, default=str))
        print("\n✅ Dry run complete. No files were generated.")
        return

    # ── Step 2: Get slide plan from Claude ─────────────────────────────────────
    print("\n🤖 Step 2: Sending data to Claude for analysis...")
    try:
        slide_plan = get_slide_plan(client_data)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error calling Claude API: {e}")
        sys.exit(1)

    # ── Step 3: Generate PPTX ──────────────────────────────────────────────────
    print("\n🎨 Step 3: Generating PowerPoint deck...")

    output_dir = Path(data_path) / args.client / args.month
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    pptx_filename = f"{args.client}_{args.month}_report_{timestamp}.pptx"
    pptx_path = output_dir / pptx_filename

    assets = client_data["assets"]
    assets["client_name"] = args.client

    try:
        generate_pptx(slide_plan, assets, str(pptx_path))
    except Exception as e:
        print(f"❌ Error generating PPTX: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ── Step 4: Convert to PDF ─────────────────────────────────────────────────
    print("\n📄 Step 4: Converting to PDF...")
    pdf_path = convert_pptx_to_pdf(str(pptx_path), str(output_dir))

    # ── Done ───────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  ✅ Report Generated Successfully!")
    print("="*60)
    print(f"  📊 PPTX : {pptx_path}")
    if pdf_path:
        print(f"  📄 PDF  : {pdf_path}")
    print(f"  📁 Folder: {output_dir}")
    print("="*60 + "\n")

    # Save the slide plan JSON for reference/debugging
    plan_path = output_dir / f"slide_plan_{timestamp}.json"
    with open(plan_path, "w") as f:
        json.dump(slide_plan, f, indent=2)
    print(f"  💡 Slide plan saved to: {plan_path}")
    print("     (You can inspect this to see what Claude decided to include)\n")


if __name__ == "__main__":
    main()
