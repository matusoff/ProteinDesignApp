import os

APP_TITLE = "Protein Developability Review Assistant"
APP_VERSION = "1.3.0"
RESULT_SCHEMA_VERSION = "0.3.2"
APP_SUBTITLE = "Sequence developability review — risks, liabilities, and mutation options in one pass."

# Single review mode for now (goal-specific tuning can branch on this later).
REVIEW_GOAL_DEFAULT = "General review"

MIN_SEQUENCE_LENGTH = 20

HYDRO_WINDOW = 9
AROMATIC_WINDOW = 7
CHARGE_WINDOW = 9

TOP_N_SUGGESTIONS = 5

# ESMFold (optional deps): long sequences need large GPU RAM; CPU is very slow
ESMFOLD_MAX_LENGTH = 400

# If PyMOL is installed but the app says "not on PATH", set ONE of:
#   • Environment variable PYMOL_EXECUTABLE (full path to pymol / pymol.bat), or
#   • PYMOL_FALLBACK_PATH below (same idea — common when launching from Cursor/VS Code).
PYMOL_FALLBACK_PATH = ""  # e.g. r"C:\Users\you\miniconda3\Scripts\pymol.bat"

PYMOL_EXECUTABLE = os.environ.get("PYMOL_EXECUTABLE", "").strip() or PYMOL_FALLBACK_PATH.strip()
