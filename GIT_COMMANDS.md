# Git Commands Cheatsheet
### For Tars Report Generator project
A simple reference for all git commands used in this project.
No prior git knowledge needed — just follow the steps!

---

## First Time Setup (do this once)

### Clone the repo to your machine
```powershell
git clone https://github.com/rithanya-tars/Report-Generator.git
cd Report-Generator
```
**What it does:** Downloads the project from GitHub to your laptop.

---

## Everyday Commands

### Check what's changed
```powershell
git status
```
**What it does:** Shows which files you've changed, added, or deleted.
Green = staged (ready to commit). Red = not staged yet.

### See commit history
```powershell
git --no-pager log --oneline
```
**What it does:** Shows a list of all changes ever made to the project.
Each line is one commit with a short ID (like `27edb60`) and a message.

### Pull latest changes from GitHub
```powershell
git pull
```
**What it does:** Downloads any new changes your teammates pushed to GitHub.
Always run this before starting work.

---

## Saving Your Changes

### Step 1 — Stage your changes
```powershell
# Stage a specific file
git add src/pptx_generator.py

# Stage all changed files at once
git add .
```
**What it does:** Tells git which changes you want to save.

### Step 2 — Commit (save a snapshot)
```powershell
git commit -m "Your message here describing what you changed"
```
**What it does:** Saves a snapshot of your staged changes with a description.
Write clear messages like `"Fix table alignment on slide 3"` not `"changes"`.

### Step 3 — Push to GitHub
```powershell
git push
```
**What it does:** Uploads your committed changes to GitHub so teammates can see them.

---

## Undoing Things

### Revert a specific file to an older version
```powershell
# First find the commit ID you want to go back to
git --no-pager log --oneline

# Then revert just that file
git checkout COMMIT_ID -- src/filename.py

# Example
git checkout b614273 -- src/claude_analyst.py
```
**What it does:** Replaces the file with its version from that specific commit.
Other files are not affected.

### Undo changes to a file (before committing)
```powershell
git checkout -- src/filename.py
```
**What it does:** Discards changes to that file and goes back to the last committed version.
⚠️ Cannot be undone — use carefully!

---

## Checking Differences

### See what changed in a file
```powershell
git diff src/filename.py
```
**What it does:** Shows line by line what changed. Green = added, Red = removed.

---

## Common Mistakes & Fixes

### Accidentally committed the wrong file?
```powershell
git reset HEAD~1
```
**What it does:** Undoes the last commit but keeps your file changes.
You can then fix things and commit again.

### Git says "pager not found" error?
```powershell
# Add --no-pager before any command
git --no-pager log --oneline
git --no-pager diff
```

### Merge conflict?
Don't panic — just message Rithanya or check the file that has conflict markers (`<<<<<<`).

---

## Our Commit History So Far

| Commit ID | Message | What it was |
|-----------|---------|-------------|
| `b614273` | Initial commit - Tars Report Generator | Original full build |
| `27edb60` | Switch to Claude Code CLI - no API key needed | Claude Code attempt (later reverted) |
| Latest | Revert to Anthropic API version | Back to API approach |

---

## Tips
- **Always `git pull` before starting work** — avoids conflicts
- **Commit often** — small commits are easier to undo than big ones
- **Write clear commit messages** — future you will thank present you
- **Never commit `.env`** — API keys must stay off GitHub (already in `.gitignore` ✅)
