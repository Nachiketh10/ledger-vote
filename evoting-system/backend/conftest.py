"""
Ensures `backend/` itself is on sys.path so `from app.blockchain.block
import ...` etc. resolve correctly no matter where pytest is invoked
from. Without this, pytest's default import mode only adds the test
file's own directory (tests/) to sys.path, not its parent — so `app`
(which lives at backend/app/) isn't importable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
