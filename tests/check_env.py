import sys
import os

print(f"Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    import client
    print("Import client: SUCCESS")
except ImportError as e:
    print(f"Import client: FAILED ({e})")

try:
    import pytest
    print("Import pytest: SUCCESS")
except ImportError as e:
    print(f"Import pytest: FAILED ({e})")
