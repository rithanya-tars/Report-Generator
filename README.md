# 📊 Tars Report Generator

Automatically generates monthly Business Review decks for Tars clients using AI.  
Give it your raw CSV exports + a few numbers from the Analyze section → get a polished PPTX + PDF.

---

## ⚡ Quick Start (5 minutes)

### 1. Clone the repo
```bash
git clone https://github.com/rithanya-tars/Report-Generator.git
cd Report-Generator
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
│   ├── client_config.json        ← Bot flow map (create once per client)
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
│   ├── client_config.json
│   └── 2026-02/
│       ├── raw_data.csv
│       └── analyze.json
│
└── NewClientName/                ← Adding a new client? Just create this folder!
    ├── assets/
    │   └── client_logo.png
    ├── client_config.json
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
| Client config | Always `client_config.json` | `client_config.json` |
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
6. Add any context in the `notes` field (campaigns, events, welcome offer changes etc.)
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
3. Create `client_config.json` — see section below
4. Create your first month folder: `TarsReports/NewClientName/2026-03/`
5. Add `raw_data.csv` and `analyze.json`
6. Run: `python generate.py --client NewClientName --month 2026-03`

No code changes needed.

---

## ⚙️ client_config.json — What It Is and Who Fills It

Every client needs a `client_config.json` file in their folder. This is a **one-time setup** done by the CSM or Implementation Engineer before the first report.

It tells the tool:
- What type of bot this client has (`gambit`, `ai_agent`, or `hybrid`)
- What counts as a goal for this client
- What each gambit column means
- Which columns to ignore (system columns, navigation values)

**Why it matters:** Without this file the tool still works, but with it the numbers are 100% accurate and Claude writes much better, client-specific insights.

### Example `client_config.json` for a gambit bot (like Amex):
```json
{
  "bot_name": "Amex_Upgrade_offer",
  "bot_type": "gambit",
  "goal_definition": "User reached apply_journey gambit — redirected to application link",
  "goal_gambits": ["apply_journey"],
  "ignore_columns": ["sn", "id", "user_ip", "visit_url", "referrer_url"],
  "navigation_values": ["Previous Menu", "Main Menu", "Previous menu", "Main menu"],
  "context": "Amex Platinum Card upgrade chatbot. Monthly welcome offer may change — check notes.",
  "gambits": {
    "main_menu_options": {
      "display_name": "Main Menu",
      "description": "First choice screen users see after welcome message",
      "level": 1,
      "type": "navigation",
      "is_goal": false,
      "options": {
        "Upgrade Offer": "Existing cardholders exploring the upgrade offer",
        "Explore Platinum": "New users exploring card benefits"
      }
    },
    "apply_journey": {
      "display_name": "Apply Journey — GOAL",
      "description": "User reached the application stage. This is the primary goal.",
      "type": "goal",
      "is_goal": true
    }
  }
}
```

### Example `client_config.json` for an AI agent bot (like Amen Clinics):
```json
{
  "bot_name": "AmenClinics_Appointment",
  "bot_type": "ai_agent",
  "goal_definition": "Lead captured — user provided name, email and phone to AI agent",
  "goal_gambits": [],
  "goal_detection": {
    "method": "keyword",
    "column": "Prime_Response",
    "keywords": ["has been received", "team will reach out", "calendly"]
  },
  "ignore_columns": ["sn", "id", "user_ip", "visit_url", "referrer_url"],
  "context": "Amen Clinics appointment booking bot. Goal = lead created when confirmation message is sent."
}
```

> 💡 See `sample_data/Amex/client_config.json` and `sample_data/AmenClinics/client_config.json` in the repo for full examples.

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not found` | Check your `.env` file has the key |
| `Client folder not found` | Check spelling matches folder name exactly |
| `Month not found` | Ensure folder is named `YYYY-MM` format |
| `Missing analyze.json` | Create it using `analyze_template.json` |
| PDF not generated | Install LibreOffice (see Quick Start step 4) |
| Wrong numbers in report | Run `--dry-run` and check gambit_distributions — column names in `client_config.json` must match CSV exactly |
| Gambit counts seem low | Check `navigation_values` in `client_config.json` — make sure all back/menu navigation values are listed |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |

---

## 🧠 How It Works

```
Your raw CSV + analyze.json + client_config.json
        ↓
  data_processor.py
  (reads all months, splits || values, filters navigation,
   detects gambit columns, calculates device splits)
        ↓
  number_calculator.py
  (calculates ALL numbers directly from CSV — 
   Python math, 100% accurate, Claude never touches numbers)
        ↓
  claude_analyst.py
  (sends data summary to Claude API →
   Claude writes insights and slide titles ONLY,
   never calculates or modifies numbers)
        ↓
  pptx_generator.py
  (builds the actual PPTX with tables, charts, branded design,
   injects locked numbers directly — no AI involvement)
        ↓
  pdf_converter.py
  (converts to PDF via LibreOffice)
        ↓
  Your report.pptx + report.pdf ✅
```

**Key principle:** Claude is a copywriter, not a data analyst. All numbers come from Python. Claude only writes the insight text.

---

## 💰 API Cost

Each report costs approximately **$0.05 – $0.20** in Anthropic API credits.  
For 20 reports/month, expect **~$2–4/month** total.

---

## 🔐 Security

- Never commit `.env` to GitHub (it's in `.gitignore`)
- Never put client data in the GitHub repo (keep it in your local `TarsReports` folder)
- Share the API key via secure internal channel (Slack DM, 1Password, etc.)
- `client_config.json` lives in `TarsReports` folder — NOT in GitHub

---

## 📞 Questions?

Ask in your team Slack channel or raise a GitHub issue.
