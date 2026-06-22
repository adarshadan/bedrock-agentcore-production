import os
import sys

# Add the repository root (parent of the "tests" directory) to PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)
