STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")

HYDROPHOBIC_AA = set("AILMFWVY")
AROMATIC_AA = set("FWY")
POLAR_AA = set("STNQCG")
CHARGED_AA = set("DEHKR")

# Kyte-Doolittle
KD_SCALE = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}

POSITIVE_AA = set("KRH")
NEGATIVE_AA = set("DE")

PATCH_BREAKING_MAP = {
    "F": ["S", "Y", "T"],
    "W": ["Y", "F", "S"],
    "Y": ["S", "T", "N"],
    "L": ["E", "Q", "N"],
    "I": ["E", "Q", "N"],
    "V": ["E", "Q", "N"],
    "M": ["Q", "L", "N"],
    "A": ["S", "T", "N"],
}
