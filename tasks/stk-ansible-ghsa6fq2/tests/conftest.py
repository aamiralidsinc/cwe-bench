"""Make the staged support package importable from both hidden groups."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
