# DhanSarthi — AUTHENTICATION ARCHITECTURE & INTEGRATION GUIDE

This document details the production-ready authentication system implemented for DhanSarthi, which connects the React frontend, FastAPI backend, and PostgreSQL database.

---

## 1. Authentication Architecture

DhanSarthi uses standard stateless **JWT (JSON Web Tokens)** for securing API endpoints:

```text
React Frontend                    FastAPI Backend                  PostgreSQL DB
      │                                  │                               │
      │ ─── 1. POST /auth/register ────> │ ────────────────────────────> │ (Persist User)
      │                                  │                               │
      │ ─── 2. POST /auth/login ───────> │ (Verify Password Hash)        │
      │ <── 3. Token Response (JWT) ──── │                               │
      │                                  │                               │
      │ ─── 4. Bearer Token Request ───> │ (Decode & Verify Claim)       │
      │                                  │ ─── 5. Fetch User Profile ──> │
      │ <── 6. Authenticated Response ── │                               │
```

---

## 2. API Endpoints

### Registration
*   **Path**: `POST /api/v1/auth/register`
*   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123"
    }
    ```
*   **Process**:
    1. Validates input schema (minimum 8-character password).
    2. Case-insensitively normalizes the email address.
    3. Verifies that the email is not already registered.
    4. Hashes the password securely with `bcrypt`.
    5. Saves the user record in PostgreSQL and auto-provisions a default profile.
*   **Response**: Safe user details (excluding password hash).

### Login
*   **Path**: `POST /api/v1/auth/login`
*   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123"
    }
    ```
*   **Process**:
    1. Validates and normalizes email.
    2. Queries the user from PostgreSQL.
    3. Verifies the password using `bcrypt` check.
    4. Issues a signed JWT access token containing only the user's ID as the `sub` claim.
*   **Response**: `{ "access_token": "...", "token_type": "bearer" }`

### Logout
*   **Path**: `POST /api/v1/auth/logout`
*   **Process**: Returns a success status. Since stateless JWT tokens are used, the frontend client handles logout by clearing the token locally.

### Get Current User
*   **Path**: `GET /api/v1/auth/me`
*   **Process**: Decodes the JWT token from the Authorization header (`Bearer <token>`) and returns the current user profile.

---

## 3. Database User Model & Security

*   **Model**: [User](file:///d:/New%20folder/New%20DhanSarthi/DhanSarthi-Remastered/backend/app/models/user.py) contains `id`, `email`, `password_hash`, `is_active`, `created_at`, and `updated_at`.
*   **Email Uniqueness**: Enforced at the database level using a unique index (`unique=True` on `users.email`).
*   **Password Hashing**: Utilizes the `bcrypt` library with a dynamic salt to hash passwords before storing them. Plaintext passwords are never saved or logged.
*   **User Data Isolation**: Every protected model (Income, Expense, Transaction, Goal, Budget, Document, etc.) is linked to a `user_id` foreign key. The backend enforces isolation server-side by retrieving data scoped to `current_user.id` resolved from the token.

---

## 4. Frontend Integration & Route Protection

### Centralized Auth State
Managed inside [AuthProvider.jsx](file:///d:/New%20folder/New%20DhanSarthi/DhanSarthi-Remastered/frontend/src/providers/AuthProvider.jsx) via React Context:
*   **Status States**: `INITIALIZING` (restoring session), `AUTHENTICATED`, `UNAUTHENTICATED`, and `AUTH_ERROR`.
*   **Session Restoration**: On application mount, the client checks `localStorage` for a JWT. If found, it fetches `/auth/me` to retrieve the current user and restore the session.
*   **Logout**: Removes the token, profile selection keys, and onboarding keys from `localStorage`, then resets state to `UNAUTHENTICATED`.

### Routing Protection
*   **ProtectedRoute**: Validates authentication and onboarding. Shows a loading screen during initialization. If unauthenticated, it redirects to `/login`.
*   **PublicRoute**: Wraps public-facing login and register forms. If an authenticated user attempts to access `/login` or `/register`, they are redirected back to `/dashboard`.
*   **AppRoutes**: lazy-loads `Login.jsx` and `Register.jsx`.

---

## 5. Local Setup & Configuration

### Environment Configuration
Ensure your [backend .env](file:///d:/New%20folder/New%20DhanSarthi/DhanSarthi-Remastered/backend/.env) contains:
```env
DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/dhansarthi
SECRET_KEY=generate-a-strong-secret-key-locally
```

Ensure your frontend `.env` contains:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Local Development Startup

1.  **Start PostgreSQL**:
    Verify that your PostgreSQL service is running on port `5432`.
2.  **Run Migrations**:
    From the backend directory:
    ```powershell
    .venv\Scripts\alembic upgrade head
    ```
3.  **Start FastAPI Backend**:
    From the backend directory:
    ```powershell
    .venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
4.  **Start React Frontend**:
    From the frontend directory:
    ```powershell
    npm run dev
    ```
