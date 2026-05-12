"""
Platform fix for pymongo Windows compatibility issue
This module patches the platform module to avoid subprocess calls during import
"""
import sys
import platform

# Check if we're on Windows
if sys.platform == "win32":
    # Monkey-patch the platform module to avoid the subprocess call
    # that causes KeyboardInterrupt issues with pymongo
    def patched_win32_ver():
        """Patched version that doesn't call subprocess"""
        # Return a fake version that won't cause issues
        return ("10", "0", "0")
    
    # Replace the win32_ver function
    platform.win32_ver = patched_win32_ver
    
    # Also patch uname to avoid subprocess calls
    def patched_uname():
        """Patched uname that doesn't call subprocess"""
        class FakeUname:
            system = "Windows"
            node = ""
            release = "10"
            version = "10.0.0"
            machine = "AMD64"
        return FakeUname()
    
    platform.uname = patched_uname
    
    print("Platform module patched for Windows compatibility")

# Now we can safely import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

print("pymongo imported successfully")