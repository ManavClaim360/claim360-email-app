import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

modules = [
    "api.auth",
    "api.campaigns",
    "api.data",
    "api.signature",
    "api.templates",
    "api.tracking",
    "core.auth",
    "core.config",
    "core.database",
    "main"
]

print("Starting import check...")
for module_name in modules:
    try:
        print(f"Checking {module_name}...", end=" ")
        __import__(module_name)
        print("OK")
    except Exception as e:
        print(f"FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

print("Import check complete.")
