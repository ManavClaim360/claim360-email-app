import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

try:
    print("Importing main...")
    from main import app
    print("✅ Main imported successfully.")
    
    print("Importing database...")
    from core.database import engine
    print("✅ Database engine created.")
    
    print("Importing auth...")
    from api.auth import router as auth_router
    print("✅ Auth router imported.")
    
except Exception as e:
    print(f"❌ Import FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
