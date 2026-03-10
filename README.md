# 📊 Tars Report Generator

Automatically generates monthly Business Review decks for Tars clients using AI.  
Give it your raw CSV exports + a few numbers from the Analyze section → get a polished PPTX + PDF.

---

## ⚡ Quick Start (5 minutes)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_ORG/tars-report-gen.git
cd tars-report-gen
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your config
```bash
cp .env.example .env
```
Open `.env` and fill in:
- `ANTHROPIC_API_KEY` — get this from your team lead (shared org key)
- `TARS_DATA_PATH` — path to your `TarsReports` folder on your machine

### 4. Install LibreOffice (for PDF export)
- **Mac**: Download from https://www.libreoffice.org/download/
- **Windows**: Same link above, run the installer
- **Linux**: `sudo apt install libreoffice`

> 💡 LibreOffice is only needed for PDF. PPTX always works without it.

### 5. Set up your TarsReports folder
See folder structure below. Put your data in the right place.

### 6. Generate a report!
```bash
python generate.py --client Amex --month 2026-02
```

---

## 📁 TarsReports Folder Structure

This folder lives on **your laptop** (NOT inside the GitHub repo).  
Every teammate has their own copy. Put it wherever you like — just set `TARS_DATA_PATH` in `.env`.

```
TarsReports/
│
├── Amex/
│   ├── assets/
│   │   ├── client_logo.png       ← Amex logo image
│   │   └── tars_logo.png         ← Tars logo image
│   ├── 2025-11/
│   │   ├── raw_data.csv          ← Exported from Tars (View & Export Data)
│   │   └── analyze.json          ← Numbers from Tars Analyze section (fill manually)
│   ├── 2025-12/
│   │   ├── raw_data.csv
│   │   └── analyze.json
│   └── 2026-01/
│       ├── raw_data.csv
│       └── analyze.json
│
├── AmenClinics/
│   ├── assets/
│   │   └── client_logo.png
│   ├── 2026-02/
│   │   ├── raw_data.csv
│   │   └── analyze.json
│
└── NewClientName/                ← Adding a new client? Just create this folder!
    ├── assets/
    │   └── client_logo.png
    └── 2026-03/
        ├── raw_data.csv
        └── analyze.json
```

### ⚠️ Naming Rules (everyone must follow these)

| Thing | Rule | Example |
|-------|------|---------|
| Client folder | Exact name, no spaces | `Amex`, `AmenClinics`, `HDFC_Bank` |
| Month folder | Always `YYYY-MM` | `2026-02`, `2025-11` |
| CSV file | Always `raw_data.csv` | `raw_data.csv` |
| Analyze file | Always `analyze.json` | `analyze.json` |
| Client logo | Must contain word `client` | `client_logo.png`, `amex_client.png` |
| Tars logo | Must contain word `tars` | `tars_logo.png` |

---

## 📋 Monthly Workflow (Every Month)

### Step 1: Export raw data from Tars
1. Go to **hellotars.com → your client bot → Check Data → View & Export Data**
2. Set the date range for the month
3. Click **Export Data** → select all gambits → download CSV
4. Rename the file to `raw_data.csv`
5. Put it in `TarsReports/ClientName/YYYY-MM/raw_data.csv`

### Step 2: Fill in analyze.json
1. Copy `analyze_template.json` from this repo
2. Go to **hellotars.com → your client bot → Check Data → Analyze**
3. Set the same date range
4. Note down these numbers from the Analyze page:
   - All Bot Visits
   - Bot Conversations  
   - Bot Goal Completions (and %)
   - Click "Unique Users Data" toggle and note unique versions of above
5. Fill them into your `analyze.json`
6. Add any context in the `notes` field (campaigns, events, etc.)
7. Save as `TarsReports/ClientName/YYYY-MM/analyze.json`

### Step 3: Run the generator
```bash
python generate.py --client ClientName --month YYYY-MM
```

### Step 4: Check the output
Your `TarsReports/ClientName/YYYY-MM/` folder will have:
- `ClientName_YYYY-MM_report_TIMESTAMP.pptx` — edit if needed
- `ClientName_YYYY-MM_report_TIMESTAMP.pdf` — send to client
- `slide_plan_TIMESTAMP.json` — Claude's decisions (for debugging)

---

## 🛠️ Commands Reference

```bash
# Basic usage
python generate.py --client Amex --month 2026-02

# Specify a different data folder
python generate.py --client Amex --month 2026-02 --data /path/to/TarsReports

# Dry run — see what data Claude will get, without calling API
python generate.py --client Amex --month 2026-02 --dry-run

# Help
python generate.py --help
```

---

## ➕ Adding a New Client

1. Create `TarsReports/NewClientName/` folder
2. Add `assets/client_logo.png` inside it
3. Create your first month folder: `TarsReports/NewClientName/2026-03/`
4. Add `raw_data.csv` and `analyze.json`
5. Run: `python generate.py --client NewClientName --month 2026-03`

That's it. No code changes needed.

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not found` | Check your `.env` file has the key |
| `Client folder not found` | Check spelling matches folder name exactly |
| `Month not found` | Ensure folder is named `YYYY-MM` format |
| `Missing analyze.json` | Create it using `analyze_template.json` |
| PDF not generated | Install LibreOffice (see Quick Start step 4) |
| Wrong numbers in report | Double-check your `analyze.json` values |

---

## 🧠 How It Works

```
Your raw CSV + analyze.json
        ↓
  data_processor.py
  (reads all months, detects gambit columns, calculates device splits etc.)
        ↓
  claude_analyst.py  
  (sends structured data to Claude API → Claude decides slides, writes insights)
        ↓
  pptx_generator.py
  (builds the actual PPTX with tables, charts, branded design)
        ↓
  pdf_converter.py
  (converts to PDF via LibreOffice)
        ↓
  Your report.pptx + report.pdf ✅
```

---

## 💰 API Cost

Each report costs approximately **$0.05 – $0.20** in Anthropic API credits.  
For 20 reports/month, expect **~$2–4/month** total.

---

## 🔐 Security

- Never commit `.env` to GitHub (it's in `.gitignore`)
- Never put client data in the GitHub repo (keep it in your local `TarsReports` folder)
- Share the API key via secure internal channel (Slack DM, 1Password, etc.)

---

## 📞 Questions?

Ask in your team Slack channel or raise a GitHub issue.
