# DataContractIQ Setup Guide

## Project Audit & Error Resolution

### Current Issues Identified

1. **Frontend**: Missing npm dependencies (React, TypeScript, Vite not installed)
2. **Frontend**: Missing CSS files (index.css, TailwindCSS not configured)
3. **Backend**: Missing Python virtual environment
4. **Backend**: Dependencies not installed
5. **Database**: PostgreSQL not set up with Pagila database

---

## Prerequisites

Before starting, ensure you have:
- **Node.js 18+** and **npm** installed
- **Python 3.11+** installed
- **PostgreSQL 14+** installed and running
- **Git** installed

### Check Prerequisites

```powershell
# Check Node.js and npm
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher

# Check Python
python --version  # Should be 3.11.0 or higher

# Check PostgreSQL
psql --version  # Should be 14.0 or higher
```

---

## Step-by-Step Setup Instructions

### Phase 1: Backend Setup

#### 1.1 Create Python Virtual Environment

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 1.2 Install Python Dependencies

```powershell
# Make sure virtual environment is activated (you should see (venv) in prompt)
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi==0.109.0
- uvicorn==0.27.0
- sqlalchemy==2.0.25
- psycopg2-binary==2.9.9
- pydantic==2.5.3
- pydantic-settings==2.1.0
- python-dotenv==1.0.0
- alembic==1.13.1

#### 1.3 Configure Environment Variables

```powershell
# Copy example env file
cp .env.example .env

# Edit .env file with your database credentials
# Update DATABASE_URL if needed
```

#### 1.4 Test Backend Server

```powershell
# Run the FastAPI server
python -m uvicorn app.main:app --reload

# Server should start on http://localhost:8000
# Open browser and visit:
# - http://localhost:8000 (root endpoint)
# - http://localhost:8000/health (health check)
# - http://localhost:8000/docs (API documentation)
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### Phase 2: Frontend Setup

#### 2.1 Install Node Dependencies

```powershell
# Navigate to frontend directory (from project root)
cd frontend

# Install all dependencies
npm install

# This will install:
# - react, react-dom
# - typescript
# - vite
# - tailwindcss
# - All other dependencies from package.json
```

**If npm install fails**, try:
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json if they exist
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue

# Install again
npm install
```

#### 2.2 Configure TailwindCSS

Create TailwindCSS configuration:

```powershell
# Initialize Tailwind (if not already done)
npx tailwindcss init -p
```

This creates `tailwind.config.js` and `postcss.config.js`.

#### 2.3 Create Missing CSS Files

The following files need to be created (see file contents below).

#### 2.4 Test Frontend Server

```powershell
# Start Vite dev server
npm run dev

# Server should start on http://localhost:5173
# Open browser and visit http://localhost:5173
```

**Expected Output:**
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h to show help
```

---

### Phase 3: Database Setup

#### 3.1 Create PostgreSQL Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE pagila;
\q
```

#### 3.2 Load Pagila Schema

```powershell
# Load the Pagila database schema
psql -U postgres -d pagila -f ../GreenCycleBikes/pagila-master/pagila-insert-data.sql
```

#### 3.3 Verify Database

```powershell
# Connect to pagila database
psql -U postgres -d pagila

# List tables
\dt

# Should see 21 tables including:
# - actor, film, customer, rental, payment, etc.

# Exit
\q
```

---

## Required File Modifications

### 1. Create `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  width: 100%;
}
```

### 2. Create `frontend/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 3. Create `frontend/postcss.config.js`

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 4. Update `frontend/.gitignore`

```
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

### 5. Create `backend/.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite3

# Logs
*.log
```

---

## Root Cause Analysis

### Frontend Errors

**Error:** `Cannot find module 'react'`
**Cause:** npm dependencies not installed
**Fix:** Run `npm install` in frontend directory

**Error:** `Cannot find module './App.tsx'`
**Cause:** Missing CSS imports and TailwindCSS configuration
**Fix:** Create `index.css` and configure Tailwind

**Error:** TypeScript errors about JSX
**Cause:** React types not installed or tsconfig misconfigured
**Fix:** Ensure `@types/react` is installed and tsconfig.json is correct

### Backend Errors

**Error:** `Import "fastapi" could not be resolved`
**Cause:** Python dependencies not installed in virtual environment
**Fix:** Create venv and run `pip install -r requirements.txt`

**Error:** `Import "pydantic_settings" could not be resolved`
**Cause:** Package installed but IDE not using correct Python interpreter
**Fix:** Select correct Python interpreter (venv) in VS Code

---

## Verification Checklist

After completing setup, verify:

### Backend
- [ ] Virtual environment activated
- [ ] All pip packages installed (`pip list` shows all dependencies)
- [ ] FastAPI server runs without errors
- [ ] Health endpoint returns 200 OK: http://localhost:8000/health
- [ ] API docs accessible: http://localhost:8000/docs

### Frontend
- [ ] node_modules directory exists
- [ ] npm install completed without errors
- [ ] Vite dev server starts without errors
- [ ] Browser shows landing page at http://localhost:5173
- [ ] No console errors in browser DevTools
- [ ] TailwindCSS classes render correctly

### Database
- [ ] PostgreSQL service running
- [ ] pagila database created
- [ ] All 21 tables loaded
- [ ] Can connect from Python using DATABASE_URL

---

## Common Issues & Solutions

### Issue: "Execution policy error" (PowerShell)
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "Port 8000 already in use"
**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue: "Port 5173 already in use"
**Solution:**
```powershell
# Find and kill process using port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Issue: PostgreSQL connection refused
**Solution:**
1. Verify PostgreSQL service is running
2. Check DATABASE_URL in .env file
3. Verify credentials (username/password)
4. Ensure database 'pagila' exists

### Issue: TailwindCSS classes not working
**Solution:**
1. Verify `tailwind.config.js` exists
2. Verify `postcss.config.js` exists
3. Verify `@tailwind` directives in `index.css`
4. Restart Vite dev server

---

## Next Steps After Setup

Once all errors are resolved and both servers are running:

1. **Test API Connection**: Click "Check API" button on frontend
2. **Verify Database**: Backend should connect to PostgreSQL
3. **Begin Phase 2**: Start implementing schema introspection
4. **Update Phase Status**: Mark Phase 1 as complete

---

## Quick Start Commands

```powershell
# Terminal 1 - Backend
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - Database (if needed)
psql -U postgres -d pagila
```

---

*Last Updated: 2026-05-01*
*Phase 1: Project Foundation & Database Setup*