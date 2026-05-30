# LeaseLens — Complete Windows Setup Guide
### Written in plain English. No experience needed. Follow every step in order.

---

## WHAT YOU WILL HAVE AT THE END

A fully working LeaseLens running on your Windows computer:
- Backend API at: http://localhost:8000
- Frontend app at: http://localhost:5173
- You can upload leases and get real AI analysis

Total time: about 45 minutes the first time.

---

## PART 1 — INSTALL 4 FREE TOOLS (one time only)

### Tool 1: VS Code (your code editor)

1. Go to **https://code.visualstudio.com**
2. Click the big blue **"Download for Windows"** button
3. Run the downloaded `.exe` file
4. During install, check these two boxes:
   - ✅ **Add "Open with Code" action to Windows Explorer file context menu**
   - ✅ **Add to PATH**
5. Click Install → Finish
6. Open VS Code — it should open without errors ✅

---

### Tool 2: Python 3.12

1. Go to **https://www.python.org/downloads/**
2. Click **"Download Python 3.12.x"** (the yellow button)
3. Run the downloaded `.exe`
4. ⚠️ **CRITICAL — On the VERY FIRST screen:**
   - Check ✅ **"Add Python 3.12 to PATH"**
   - Then click **"Install Now"**
5. If you see **"Disable path length limit"** — click it
6. Click Close

**Verify it worked:**
- Press `Win + R`, type `cmd`, press Enter
- Type: `python --version`
- You should see: `Python 3.12.x` ✅
- If you see **"Python was not found"** → uninstall Python, reinstall, and CHECK that PATH box

---

### Tool 3: Node.js

1. Go to **https://nodejs.org**
2. Click the **"LTS"** button (left side — stable version)
3. Run the downloaded `.msi` installer
4. Click Next → Next → Next → Install (all defaults are fine)
5. If it asks to install additional tools → click **Yes** and let it finish
6. Click Finish

**Verify it worked:**
- Open a NEW Command Prompt (close old one, open new)
- Type: `node --version` → should show `v20.x.x` ✅
- Type: `npm --version` → should show `10.x.x` ✅

---

### Tool 4: Git

1. Go to **https://git-scm.com/download/win**
2. Click the **"64-bit Git for Windows Setup"** link
3. Run the installer
4. On the screen **"Choosing the default editor"** → select **"Use Visual Studio Code as Git's default editor"**
5. On **"Adjusting the name of the initial branch"** → select **"Override: main"**
6. Everything else → click Next all the way through → Install

**Verify:**
- Open NEW Command Prompt → type: `git --version`
- Should show: `git version 2.x.x` ✅

---

## PART 2 — GET YOUR FREE API KEYS

### Key 1: Anthropic API Key (the AI brain — REQUIRED)

1. Go to **https://console.anthropic.com**
2. Click **"Sign Up"** — create a free account with your email
3. Verify your email (check spam folder if not received)
4. Go to **https://console.anthropic.com/settings/keys**
5. Click **"Create Key"**
6. Name it anything, e.g. `leaselens`
7. ⚠️ **COPY THE KEY NOW** — it starts with `sk-ant-api03-...`
8. Paste it into Notepad and save — you only see it once!

> Free tier gives $5 credit = about 100 analyses. More than enough to test.

---

### Key 2: Supabase Database (free PostgreSQL — no install needed)

1. Go to **https://supabase.com**
2. Click **"Start your project"** → Sign up (GitHub login is easiest)
3. Click **"New project"**
4. Fill in:
   - **Name:** `leaselens`
   - **Database Password:** make something strong, e.g. `MyLeaseLens2024!`
   - **Region:** Southeast Asia (Singapore) — closest to India
5. Click **"Create new project"** → wait 2–3 minutes for setup
6. When the dashboard loads:
   - Click **"Settings"** (gear icon in left sidebar)
   - Click **"Database"**
   - Scroll down to **"Connection string"**
   - Click the **"URI"** tab
   - Copy the full string — looks like:
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.abcxyz.supabase.co:5432/postgres
     ```
   - **Replace `[YOUR-PASSWORD]`** with the password you set in step 4
   - Paste this in Notepad and save

7. **Enable pgvector extension (one time only):**
   - Click **"SQL Editor"** in the left sidebar
   - Click **"New query"**
   - Paste this and click **"Run"**:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - You should see: **"Success. No rows returned"** ✅

---

## PART 3 — SET UP THE PROJECT

### Step 1: Extract the zip file

1. Find `leaselens-production.zip` in your Downloads folder
2. Right-click it → **"Extract All..."**
3. Change the destination to: `C:\Projects\leaselens`
   - (Create the `Projects` folder first if it doesn't exist)
4. Click **"Extract"**

You should now have: `C:\Projects\leaselens\` with folders inside: `backend\`, `frontend\`, `docs\`, etc.

---

### Step 2: Open the project in VS Code

1. Open VS Code
2. Go to **File → Open Folder**
3. Navigate to `C:\Projects\leaselens` and click **"Select Folder"**
4. If it asks "Do you trust the authors?" → click **"Yes, I trust the authors"**

---

### Step 3: Open the terminal inside VS Code

Press **`Ctrl + `` `** (that's Ctrl + backtick — the key above Tab, below Escape)

A terminal panel opens at the bottom. This is where you type all commands.

> If the terminal opens as PowerShell and commands don't work, click the dropdown arrow next to the `+` button and select **"Command Prompt"**

---

## PART 4 — SET UP THE BACKEND (Python)

Type these commands one at a time in the VS Code terminal. Press Enter after each. Wait for each to finish before typing the next.

### Step 1: Go to the backend folder
```
cd backend
```

### Step 2: Create Python virtual environment
```
python -m venv venv
```
Wait 10 seconds. A `venv` folder appears. ✅

### Step 3: Activate the virtual environment
```
venv\Scripts\activate
```
Your prompt now shows `(venv)` at the start. ✅

> **If you get an error about "execution policy"**, run this first:
> ```
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Answer `Y` then try the activate command again.

### Step 4: Install Python packages
```
pip install -r requirements.txt
```
This downloads ~30 packages. Takes 3–5 minutes. ✅ when you see `Successfully installed...`

> **If you see errors about "Microsoft Visual C++":**
> 1. Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
> 2. Download and run "Build Tools for Visual Studio"
> 3. Check ✅ "Desktop development with C++"
> 4. Install, restart your computer, then retry `pip install -r requirements.txt`

### Step 5: Create your `.env` secrets file

In VS Code's left panel (the file explorer), inside the `backend` folder:
1. Right-click the file called `.env.example`
2. Click **"Copy"**
3. Right-click on the `backend` folder → **"Paste"**
4. Right-click the new file → **"Rename"** → rename it to `.env` (just `.env`, delete `.example`)
5. Click `.env` to open it

Now fill in these values:

**Line: `APP_SECRET_KEY=`**
Generate a random key by running this in the terminal:
```
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output (a long string of letters and numbers) and paste it after `APP_SECRET_KEY=`

**Lines: `DATABASE_URL=` and `DATABASE_URL_SYNC=`**

Take your Supabase connection string from Notepad. It looks like:
```
postgresql://postgres:MyPassword@db.abcxyz.supabase.co:5432/postgres
```

For `DATABASE_URL=` — change `postgresql://` to `postgresql+asyncpg://`:
```
DATABASE_URL=postgresql+asyncpg://postgres:MyPassword@db.abcxyz.supabase.co:5432/postgres
```

For `DATABASE_URL_SYNC=` — keep `postgresql://` as-is:
```
DATABASE_URL_SYNC=postgresql://postgres:MyPassword@db.abcxyz.supabase.co:5432/postgres
```

**Line: `ANTHROPIC_API_KEY=`**
Paste your `sk-ant-api03-...` key here:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

**Line: `FRONTEND_URL=`**
Leave as-is for local development:
```
FRONTEND_URL=http://localhost:5173
```

Press **Ctrl+S** to save the `.env` file.

---

### Step 6: Create the database tables

```
alembic upgrade head
```

You should see output ending with:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema with pgvector
```
✅ Your database tables are created.

**If you see "connection refused"** → check your `DATABASE_URL` in `.env`. Make sure you replaced `[YOUR-PASSWORD]` with the actual Supabase password.

**If you see "password authentication failed"** → wrong password in the URL. Re-copy from Supabase dashboard.

---

### Step 7: Start the backend server

```
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Test it:** Open your browser and go to: **http://localhost:8000/health**

You should see:
```json
{"status":"healthy","service":"LeaseLens API","version":"1.0.0"}
```
✅ Backend is running!

Also visit **http://localhost:8000/api/docs** — you'll see the interactive API documentation.

> ⚠️ **Keep this terminal open.** The backend must keep running.

---

## PART 5 — SET UP THE FRONTEND (React)

### Step 1: Open a second terminal

In VS Code, click the **`+`** button in the top-right corner of the terminal panel.

This opens a new terminal tab while the backend keeps running in the first tab.

### Step 2: Go to the frontend folder

```
cd frontend
```

(If you're still in the backend folder: `cd ..\frontend`)

### Step 3: Create the frontend `.env` file

In the VS Code file explorer, inside the `frontend` folder:
1. Right-click `.env.example` → Copy → Paste → Rename to `.env`
2. Open it — it contains:
   ```
   VITE_API_URL=http://localhost:8000
   ```
3. That's already correct. Save it (Ctrl+S).

### Step 4: Install frontend packages

```
npm install
```

Takes 2–3 minutes. You'll see a progress bar. ✅ when you see `added XXX packages`.

### Step 5: Start the frontend

```
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

Open your browser and go to: **http://localhost:5173**

You should see the LeaseLens homepage with the dark navy blue header. 🎉

---

## PART 6 — TEST THE FULL APP

1. Go to **http://localhost:5173**
2. Click **"Get Started Free"**
3. Click **"Sign up →"** and register with:
   - Any email address (fake is fine for testing, e.g. `test@test.com`)
   - Password: must have 8+ chars, 1 uppercase, 1 number — e.g. `TestLease1`
4. You'll be taken to the **Analyze** page
5. Click the **"✏️ Paste Text"** tab
6. Click **"Load demo lease →"** (bottom-right of the text box)
7. A Bengaluru rental agreement will appear — full of illegal clauses
8. Keep jurisdiction as **"Bengaluru, Karnataka, India"**
9. Click **"🔍 Analyze My Lease"**
10. Watch the loading animation (15–30 seconds — this is real AI analysis)
11. You should see results with:
    - A fairness score around **15–25/100 (Predatory)**
    - Multiple CRITICAL and HIGH issues flagged
    - Illegal clauses highlighted
    - A ready-to-send counter-proposal letter

**If this works — your LeaseLens is fully operational.** ✅

---

## PART 7 — HOW TO RESTART AFTER CLOSING VS CODE

Every time you close VS Code and want to run LeaseLens again:

**Terminal 1 (Backend):**
```
cd C:\Projects\leaselens\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```
cd C:\Projects\leaselens\frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## PART 8 — COMMON ERRORS AND FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `python was not found` | PATH not set | Reinstall Python, check "Add to PATH" |
| `venv\Scripts\activate` fails | Execution policy | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `pip install` C++ errors | Missing build tools | Install "Build Tools for Visual Studio" with C++ workload |
| `alembic upgrade head` fails with "connection refused" | Wrong DATABASE_URL | Check URL in `.env` — ensure Supabase URL is correct |
| `alembic` not found | venv not activated | You should see `(venv)` in prompt. Run activate again. |
| Port 8000 already in use | Old Python process | Open Task Manager → Details → find `python.exe` → End Task |
| `npm install` takes forever | Slow network | Wait. It downloads ~100MB of packages. Normal. |
| White screen at localhost:5173 | Build error | Press F12 → Console tab → read the error |
| 401 Unauthorized | Not logged in | Register/login first, then analyze |
| 429 Too Many Requests | Free plan limit (1/month) | In Supabase, delete your user row from the `users` table and re-register |
| "AI service not configured" | Missing API key | Check `ANTHROPIC_API_KEY` in `backend\.env` |
| "Cannot open PDF" | Bad PDF file | Try a different PDF, or use the "Paste Text" mode |

---

## PART 9 — RUN THE TESTS

To verify everything works correctly:

```
cd C:\Projects\leaselens\backend
venv\Scripts\activate
python -m pytest tests/test_core.py -v
```

You should see **23 passed** with no failures. ✅

---

## PART 10 — DEPLOY ONLINE (share with the world)

When you're ready to put LeaseLens on the internet for others to use:

### Step 1: Push to GitHub (5 minutes)

1. Go to **https://github.com** → sign up if you don't have an account
2. Click **"New repository"** → name it `leaselens` → click **"Create repository"**
3. In VS Code terminal (from `C:\Projects\leaselens`):
   ```
   git init
   git add .
   git commit -m "feat: initial production build of LeaseLens"
   git branch -M main
   git remote add origin https://github.com/YOURUSERNAME/leaselens.git
   git push -u origin main
   ```

### Step 2: Deploy backend to Railway (free tier, 5 minutes)

1. Go to **https://railway.app** → click **"Login"** → use GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `leaselens` repository
4. Click **"Add variables"** and add ALL variables from your `backend\.env` file
   - Also add: `APP_ENV=production`
   - Also add: `FRONTEND_URL=https://YOUR-APP.vercel.app` (you'll get this in Step 3)
5. Set **Root Directory** to `/backend`
6. Railway auto-detects Python and deploys. Wait 2–3 minutes.
7. Click **"Settings"** → copy your Railway URL, e.g.: `https://leaselens-api.up.railway.app`

### Step 3: Deploy frontend to Vercel (free, 3 minutes)

1. Go to **https://vercel.com** → sign up with GitHub
2. Click **"Add New Project"** → import your `leaselens` repo
3. Set **Root Directory** to `frontend`
4. Under **Environment Variables**, add:
   ```
   VITE_API_URL = https://leaselens-api.up.railway.app
   ```
   (use your actual Railway URL from Step 2)
5. Click **"Deploy"**
6. Vercel gives you a URL like: `https://leaselens.vercel.app`

### Step 4: Update Railway FRONTEND_URL

Go back to Railway → your project → Variables → update `FRONTEND_URL` to your Vercel URL.

**Your app is now live on the internet.** ✅

Share your Vercel URL with anyone to try it!

---

## QUICK REFERENCE

| What | Command | Where |
|------|---------|-------|
| Start backend | `uvicorn app.main:app --reload --port 8000` | `backend/` folder with venv active |
| Start frontend | `npm run dev` | `frontend/` folder |
| Run tests | `python -m pytest tests/test_core.py -v` | `backend/` folder with venv active |
| Build frontend | `npm run build` | `frontend/` folder |
| Update DB | `alembic upgrade head` | `backend/` folder with venv active |

| URL | What's there |
|-----|-------------|
| http://localhost:5173 | Your app (frontend) |
| http://localhost:8000 | Backend API |
| http://localhost:8000/api/docs | Interactive API documentation |
| http://localhost:8000/health | Health check |

