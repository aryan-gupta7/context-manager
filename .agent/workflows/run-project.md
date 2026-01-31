---
description: How to run the Backend, Frontend, and Ollama server
---

Follow these steps to get the environment up and running.

### 1. Ollama Server & Models
Open a terminal and run the following:

// turbo
```powershell
# Start Ollama (usually running in background, but ensure it's on)
ollama serve
```

In a **separate** terminal, create the custom models required for the Fractal Workspace:
```powershell
# Navigate to the project root
cd "c:/coding vs/context-manager"

# Create the Reasoner model
ollama create main-reasoner -f backend/ollama/Modelfile.main-reasoner

# Create the Graph Builder model
ollama create graph-builder -f backend/ollama/Modelfile.graph-builder
```

### 2. Backend (FastAPI)
Open a new terminal and run:

```powershell
cd "c:/coding vs/context-manager/backend"

# Ensure Virtual Environment is active
.\venv\Scripts\activate

# Start the server
uvicorn main:app --reload
```
The backend will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend (Vite)
Open a new terminal and run:

```powershell
cd "c:/coding vs/context-manager/frontend"

# Install dependencies (only once)
npm install

# Start development server
npm run dev
```
The frontend will be available at [http://localhost:5173](http://localhost:5173).

### 4. Database Reminder
Ensure your PostgreSQL server is running and you have created the database:
```sql
CREATE DATABASE fractal_workspace;
```
Check your `backend/.env` file to ensure the credentials match your local Postgres setup.
