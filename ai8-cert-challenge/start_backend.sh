#!/bin/bash

# Start the FastAPI backend server
echo "🚀 Starting Scout Backend..."
echo "Backend will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""

uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

