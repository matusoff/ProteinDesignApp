APP_TITLE = "Protein Developability Review Assistant"
APP_VERSION = "1.1"
APP_SUBTITLE = (
    "Sequence-based developability review for protein constructs "
    f"(v{APP_VERSION}: exports + optional ESMFold structure)"
)

MIN_SEQUENCE_LENGTH = 20

HYDRO_WINDOW = 9
AROMATIC_WINDOW = 7
CHARGE_WINDOW = 9

TOP_N_SUGGESTIONS = 5

# ESMFold (optional deps): long sequences need large GPU RAM; CPU is very slow
ESMFOLD_MAX_LENGTH = 400
