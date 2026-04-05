# CHIGURU Website — Deployment Guide

---

## Phase 1 · Testing (GitHub Pages)

This phase gets the site live on a temporary URL so the team can review it before we go public. One team member hosts it on their personal GitHub account. Takes about 10 minutes.

**You will need:** your GitHub account login and the file `index.html`

> The website file has already been renamed `index.html` for you. Do not rename it.

---

### Step 1 — Create a new repository

1. Log in to [github.com](https://github.com)
2. Click **+** (top right) → **New repository**
3. Set the following:
   - **Repository name:** `chiguru-cohort`
   - **Visibility:** Public
   - Everything else: leave as default
4. Click **Create repository**

---

### Step 2 — Upload the file

1. On the repository page, click **uploading an existing file**
2. Drag and drop `index.html` into the upload box
3. Scroll down and click **Commit changes**

---

### Step 3 — Enable GitHub Pages

1. Click the **Settings** tab in your repository
2. In the left sidebar, click **Pages**
3. Under **Source**, select **Deploy from a branch**
4. Under **Branch**, select **main** — leave folder as `/ (root)`
5. Click **Save**

Wait 2 minutes, then refresh. You will see:

> *Your site is live at `https://your-username.github.io/chiguru-cohort/`*

Send this link to the team for feedback.

---

### Updating the site

When you receive a revised `index.html`:

1. Go to your repository → click `index.html`
2. Click the **pencil icon** → then the **upload icon** → upload the new file
3. Click **Commit changes**

The site updates within 2 minutes.

---

### If something looks wrong

| Problem | Fix |
|---|---|
| 404 error | Wait 5 min and refresh. Check the file is named exactly `index.html` |
| Old version still showing | Hard-refresh: **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows) |
| Site looks broken | Open `index.html` locally first — if it looks fine locally, re-upload |

---

## Phase 2 · Public launch (custom domain)

Once internal feedback is incorporated, we will move to a proper domain — something like `chigurastudy.org`. This involves registering a domain (~₹1,000/year) and pointing it to the same GitHub repository. A separate guide will cover this step.

---

Last updated: 2026-03-08 19:17
