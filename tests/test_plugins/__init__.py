import os
import sys

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'plugins')
PLUGIN_DIR = os.path.abspath(PLUGIN_DIR)
assert os.path.exists(PLUGIN_DIR)

sys.path.insert(0, PLUGIN_DIR)
