# Tars Report Generator — Changelog

All changes to this project are documented here.
Format: Date | What changed | Why

---

## v1.0 — Initial Build
**Date:** March 10, 2026
**Who:** Rithanya G (Implementation Engineer, Tars)

### What was built
- Full Python tool to auto-generate monthly Business Review PPTX + PDF for Tars clients
- Built with: Python, python-pptx, Anthropic Claude API
- 4 core files:
  - `generate.py` — main entry point (CLI)
  - `src/data_processor.py` — reads CSV + analyze.json, detects gambit columns
  - `src/claude_analyst.py` — sends data to Claude, gets JSON slide plan back
  - `src/pptx_generator.py` — builds branded PPTX from slide plan
  - `src/pdf_converter.py` — converts PPTX to PDF via LibreOffice

### Folder structure decided
```
TarsReports/                        ← lives locally on each laptop, NOT in GitHub
  /ClientName/
    /assets/
      client_logo.png               ← must contain "client" in filename
      tars_logo.png                 ← must contain "tars" in filename
    /YYYY-MM/
      raw_data.csv                  ← exported from Tars admin
      analyze.json                  ← manually filled from Tars Analyze section
      report.pptx                   ← generated output
      report.pdf                    ← generated output
```

### How to run
```powershell
python generate.py --client Amex --month 2026-01
python generate.py --client Amex --month 2026-01 --dry-run
```

### GitHub repo created
- URL: https://github.com/rithanya-tars/Report-Generator
- Private repo
- `.env`, `*.pptx`, `*.pdf`, `*.csv` all blocked by `.gitignore` — client data never touches GitHub

---

## v1.1 — PPTX Design Overhaul
**Date:** March 11, 2026

### What changed
- Extracted exact design values from real `AMEX_Platinum_Nov_2025_to_Feb_2026.pptx`
- Rebuilt `pptx_generator.py` to match exactly:
  - Slide size: `10.0" x 5.625"` (was wrong before)
  - Title box fill: `#B28FD5` (light purple)
  - Table header: `#CCCCCC` (light grey)
  - Title text: `#434343` (dark charcoal)
  - Cover purple: `#6C4098`
  - Logo positions extracted to exact inch values
- Fixed wide tables using smaller font automatically (no more text wrapping)
- Fixed insights never overlapping tables
- Two-table slides working cleanly

---

## v1.2 — Switched to Claude Code CLI (then reverted)
**Date:** March 11, 2026

### What changed
- Rewrote `claude_analyst.py` to use `claude -p` CLI command
- Reason: Manager suggested using org Claude Code subscription instead of paid API key
- Used `subprocess.run(["claude", "-p", prompt])` approach
- **Reverted back to API version** after getting org API key from Vinit Agrawal
- Reason for revert: API approach is more reliable and predictable for programmatic use

### What was learned
- Claude Code is installed in WSL on Rithanya's machine
- Claude Code Max plan is available via `claude@hellotars.com` org account
- For teammates: API key approach is simpler (no Claude Code setup needed)

---

## v1.3 — Moved to WSL then back to Windows PowerShell
**Date:** March 11, 2026

### What happened
- Attempted to run tool in WSL (Ubuntu) since Claude Code was installed there
- Set up virtual environment in WSL: `python3 -m venv venv`
- Realized Windows PowerShell is simpler for the team
- Moved back to PowerShell with API key approach
- Key learning: WSL paths use `/mnt/c/` instead of `C:\`

---

## v1.4 — First Successful Real Report Generated ✅
**Date:** March 11, 2026

### What happened
- Got org API key from Vinit Agrawal
- Added to `.env` file (confirmed `.env` is in `.gitignore` ✅)
- Ran against real Amex January 2026 data
- Claude generated 10 slides from real data:
  - Cover, Performance Overview, Device Distribution
  - Main Menu Engagement, Application Journey Analysis
  - Travel Benefits Deep Dive, Other Benefits Exploration
  - Key Insights, Recommendations, Contact
- PDF skipped (LibreOffice not installed yet)
- Report saved to: `Tars_Reports/Amex/2026-01/`

### Security note from Vinit
- Always keep API key in `.env` only
- `.env` must stay in `.gitignore` (already done ✅)
- Avoid infinite loops that could drain API credits (no loops in current code ✅)

---

## v1.5 — Number Locking Feature ✅
**Date:** March 11, 2026

### What changed
- Problem: Claude was deciding numbers AND writing insights — risk of inaccurate numbers
- Solution: Python calculates all numbers directly from CSV, Claude only writes insights
- Numbers never go through Claude → 100% accurate data in reports
- Dynamic: works for any client, any number of rows, any gambit column names

### New file added
- `src/number_calculator.py` — calculates ALL numbers directly from CSV + analyze.json

### What changed
- `src/claude_analyst.py` — Claude now only writes insights, never numbers
- `src/pptx_generator.py` — accepts locked_numbers dict, uses them directly in slides
- `generate.py` — wires number_calculator between data_processor and claude_analyst

### Flow after this change
```
CSV + analyze.json
    → number_calculator.py  (Python math, 100% accurate)
        → locked numbers go straight to PPTX
        → summary goes to Claude
            → Claude writes insights only
                → insights + locked numbers → PPTX
```

---

## v1.6 — Accurate Gambit Counting + Client Config System
**Date:** March 15, 2026

### Problems fixed
- Gambit counts were wrong — "Upgrade Offer || Upgrade Offer" was counting as 2 instead of 1
- Navigation values like "Previous Menu" and "Main Menu" were being counted as real selections
- Claude was making up gambit numbers even when given locked numbers

### What changed
- `src/data_processor.py` — split `||` values, deduplicate within same row, filter navigation values
- Numbers now verified against Google Sheets COUNTIF — 100% match
- `client_config.json` now includes full gambit repository with level, parent, description for each gambit

### New files
- `Tars_Reports/Amex/client_config.json` — complete Amex bot flow map built from actual bot JSON
- `sample_data/Amex/client_config.json` — updated sample for new clients

### Verification method
Use `=COUNTIF(column,"*Option Name*")` in Google Sheets to verify any gambit count

---

## Pending / Next Steps
- [ ] Install LibreOffice for PDF export
- [ ] Get CSM feedback on slide design
- [ ] Get golden template PPTX from team for pixel-perfect design rebuild
- [ ] Share tool + README with team
- [ ] Complete number locking feature
