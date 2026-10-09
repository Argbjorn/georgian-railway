import os
import sys

# Make scripts/ modules (gtfs, make_gtfs, config) importable. Appended, not prepended, so that
# `import utils` in tests keeps resolving to tests/utils.py rather than the scripts/utils package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
