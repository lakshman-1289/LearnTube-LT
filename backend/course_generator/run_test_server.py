import sys
import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Add the backend root to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

env_path = backend_root / ".env"
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    # Verify environment variables
    if not os.getenv("GROQ_API_KEY"):
        print("GROQ_API_KEY not found in environment variables")
        exit(1)
    
    print("Starting Course Generator Test API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "course_generator.src.test_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
