---
description: How to install Python packages and run the backend server
---

## Important Rules

1. **Always install Python packages inside the local virtual environment**, NOT the global Python:
   ```bash
   # CORRECT — install in .venv
   .venv\Scripts\pip install <package-name>

   # WRONG — installs globally
   pip install <package-name>
   ```

2. **Backend working directory**: `c:\Users\mahdi\OneDrive\Desktop\Campus-Assistant\backend`

3. **Start the backend server** (uses .venv automatically):
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Start the frontend dev server**:
   ```bash
   cd ..\frontend
   npm run dev
   ```

5. **Environment variables** are in `backend/.env` — never commit this file.

6. **LLM model** can be changed on **line 53 of `backend/main.py`** in the `ChatGoogleGenerativeAI` constructor.
