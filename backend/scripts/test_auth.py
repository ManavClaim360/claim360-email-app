import sys
import os
sys.path.append(os.getcwd())

from core.auth import get_password_hash, verify_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test():
    print("--- AUTH TEST ---")
    password = "a" * 100  # 100 characters
    print(f"Testing with password length: {len(password)}")
    
    try:
        hashed = get_password_hash(password)
        print(f"Hash success. Hash length: {len(hashed)}")
        
        match = verify_password(password, hashed)
        print(f"Verify success. Match: {match}")
        
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
