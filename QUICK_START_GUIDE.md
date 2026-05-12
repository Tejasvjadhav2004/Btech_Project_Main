# Quick Fix and Run Guide

## Issues Fixed:
1. ✅ Removed invalid WorkflowStatus.REJECTED from state machine
2. ✅ Fixed execution engine service loading
3. ✅ Added forward annotations to orchestrator service

## REQUIRED STEP - Install Missing Package:

Before running the server, you MUST install pydantic-settings:

```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Install the package
pip install pydantic-settings
```

## Then Run the Server:

```bash
# Option 1: Using uvicorn
uvicorn api.main:app --reload

# Option 2: Using Python
python -m api.main
```

## Expected Successful Output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Application startup complete.
INFO:     Database connection established
INFO:     Intelligence layer collections initialized
INFO:     Orchestration layer initialized and started
INFO:     Background scheduler started
```

## If You Get Database Connection Errors:

Make sure MongoDB is running or update `.env` with your MongoDB Atlas credentials:

```env
# For MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/

# For local MongoDB
MONGODB_URI=mongodb://localhost:27017
```

## Next Steps After Server Starts:

1. Open http://localhost:8000/docs in browser
2. Test orchestration endpoints
3. Start frontend: `cd ../frontend && npm run dev`
4. Open http://localhost:5173
