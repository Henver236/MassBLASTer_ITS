#!/usr/bin/env bash

INPUT=$1
OUT_FASTA="ITS_trimmed.fasta"
LOG="ITS_trim.log"

WINDOW=50
THRESHOLD=0.05
PATTERN="CAT"

# En-tête du log
echo -e "id\torig_len\tstart_cut\tend_cut\tfinal_len\thas_CAT" > "$LOG"

awk -v W=$WINDOW -v T=$THRESHOLD -v PAT=$PATTERN -v LOG="$LOG" '
BEGIN {
    RS=">"
    FS="\n"
}
NR > 1 {
    id = $1
    seq = ""
    for (i = 2; i <= NF; i++) seq = seq $i
    orig_len = length(seq)

    # 1) Trim début sur CAT
    pos = index(seq, PAT)
    if (pos > 0) {
        start_cut = pos
        seq = substr(seq, pos)
        has_cat = "yes"
    } else {
        start_cut = 0
        has_cat = "no"
    }

    # 2) Trim fin par fenêtre glissante
    end_cut = length(seq)
    for (i = 1; i <= length(seq) - W + 1; i++) {
        window = substr(seq, i, W)
        amb = gsub(/[NRYWSKMBDHV]/, "", window)
        if (amb / W > T) {
            end_cut = i - 1
            break
        }
    }

    if (end_cut < 1) end_cut = 1
    trimmed = substr(seq, 1, end_cut)
    final_len = length(trimmed)

    # FASTA output
    print ">" id
    print trimmed

    # LOG
    printf "%s\t%d\t%d\t%d\t%d\t%s\n", \
        id, orig_len, start_cut, end_cut, final_len, has_cat >> LOG
}
' "$INPUT" > "$OUT_FASTA"
