# SPICE Platform

**SPICE Platform** is an AI-powered web platform for designing, simulating, and analyzing electronic circuits. It features an interactive schematic editor, automatic SPICE netlist generation, waveform visualization, automated circuit measurements, AI-assisted debugging, and intelligent simulation analysis, providing an end-to-end environment for circuit design, validation, and optimization.



## Tech Stack

- **Frontend (`/frontend`)**: Next.js (React 19), TypeScript, Tailwind CSS
- **Backend (`/backend`)**: FastAPI, PostgreSQL.


## Prerequisites

Ensure you have the following installed on your machine:

- **Node.js** (v18 or higher) & `npm`
- **Python** (v3.10 or higher)
- **PostgreSQL** database server
- **ngspice** (must be installed and available in your system path)

---

## Project Setup & Running

### 1. Database Setup

Make sure PostgreSQL is running, then create a database and user:

```sql
CREATE DATABASE spice_db;
CREATE USER spice_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE spice_db TO spice_user;
```

---

### 2. Backend Setup (`/backend`)

1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables by copying `sample.env` to `.env`:
   ```bash
   cp sample.env .env
   ```
   Edit `.env` to match your database settings and optional API keys:
   ```env
   DB_URL="postgresql://spice_user:your_password@localhost:5432/spice_db"
   OPENCODE_API_KEY=your_actual_key_here
   OPENCODE_API_BASE=https://opencode.ai/zen/v1
   OPENCODE_MODEL=minimax-m2.5-free
   ```

5. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the FastAPI backend server:
   ```bash
   python manage.py runserver
   ```
   The backend API will run at `http://localhost:8000`.

---

### 3. Frontend Setup (`/frontend`)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node package dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   The application UI will be running at `http://localhost:3000`.

---

## Useful Management Commands

### Backend
- `python manage.py runserver` — Starts PostgreSQL (if managed locally) and launches the FastAPI server.
- `python manage.py makemigrations` — Autogenerates new Alembic migration scripts based on model changes.
- `python manage.py migrate` — Applies pending migrations to PostgreSQL.

### Frontend
- `npm run dev` — Starts the Next.js development server.
- `npm run build` — Builds the application for production.
- `npm run format` — Formats code using Prettier.
