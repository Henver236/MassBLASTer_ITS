from Bio import SeqIO
import re

# Paramètres
START_PATTERN = "CAT"
WINDOW_SIZE = 50
THRESHOLD = 0.05  # 5 %

# Bases dégénérées IUPAC (hors ACGTU)
AMBIGUOUS_RE = re.compile(r"[NRYWSKMBDHV]", re.IGNORECASE)

def trim_sequence(seq):
    seq = str(seq)

    # 1) Trim du début sur CAT
    start = seq.find(START_PATTERN)
    if start == -1:
        return None  # ou return seq si tu veux les garder

    seq = seq[start:]

    # 2) Trim de fin par fenêtre glissante
    for i in range(0, len(seq) - WINDOW_SIZE + 1):
        window = seq[i:i + WINDOW_SIZE]
        amb = len(AMBIGUOUS_RE.findall(window))
        if amb / WINDOW_SIZE > THRESHOLD:
            return seq[:i]

    return seq


with open("ITS_trimmed.fasta", "w") as out:
    for record in SeqIO.parse("input.fasta", "fasta"):
        trimmed = trim_sequence(record.seq)
        if trimmed and len(trimmed) > 0:
            record.seq = trimmed
            SeqIO.write(record, out, "fasta")
