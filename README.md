# SEAPP Backend API

This is the backend service for the SEAPP application, built with **FastAPI** and **MongoDB**. It provides a robust API for user authentication, role-based access control, and scan history management.

## 🚀 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: MongoDB (via `pymongo` and `motor` for async operations)
- **Authentication**: JWT (JSON Web Tokens) with `python-jose` and `passlib` for password hashing
- **Server**: Uvicorn

## ✨ Features

- **User Authentication**: Secure Sign Up and Sign In using JWT.
- **Role-based Access Control**: Distinguishes between different user roles (e.g., Student, Teacher).
- **Data Management**: CRUD operations for scan history linked to authenticated users.
- **Automatic API Documentation**: Interactive Swagger UI and ReDoc out of the box.

## 📂 Project Structure

```text
backend/
├── main.py                 # FastAPI application instance & CORS setup
├── models/                 # Pydantic models & Database schemas
├── routers/                # API route definitions (auth_router, scan_router, etc.)
├── utils/                  # Helper functions (security, JWT processing, password hashing)
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (Ignored by Git)
```

## 🛠️ Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites
- Python 3.8+ installed on your machine.
- A MongoDB cluster (e.g., MongoDB Atlas) or a local MongoDB instance.

### 2. Clone the repository
```bash
git clone https://github.com/dinhlong06/DB_SE.git
cd backend
```

### 3. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root of the `backend` directory and add the following variables:

```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
> **Note:** Never commit your `.env` file to version control.

### 6. Run the Server
Start the development server with Uvicorn:
```bash
uvicorn main:app --reload
```
The server will start running at `http://127.0.0.1:8000`.

## 📚 API Documentation

Once the server is running, you can interact with the API using the automatic documentation provided by FastAPI:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## ☁️ Deployment

This project is configured to be easily deployable on **Render**. 
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`

Make sure to add your Environment Variables directly in the Render dashboard and whitelist `0.0.0.0/0` in your MongoDB Network Access settings.