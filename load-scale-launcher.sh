#!/usr/bin/env bash

set -exo pipefail

BASE_DIR="$PWD"
INPUT_DIR="$BASE_DIR/massblaster_plutof_pub/indata"

# Debug :
echo "DEBUG: BASE_DIR = $BASE_DIR"
echo "DEBUG: INPUT_DIR = $INPUT_DIR"
echo "DEBUG: pwd = $(pwd)"
echo "DEBUG: contenu de INPUT_DIR :"
ls -l "$INPUT_DIR" || echo "⚠ INPUT_DIR not reachable ⚠"

# Parsing FASTA file
shopt -s nullglob
FILES=("$INPUT_DIR"/source_*.fas)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "⚠ No file source_*.fas found ⚠"
    exit 1
fi


for FILE in "${FILES[@]}"; do
    # Check bases paires number and put it in FILES
    #TOTAL_BP=$(awk '!/^>/ {sum += length($0)} END {print sum}' "$FILES")
    #TOTAL_BP=$(awk '!/^>/ {sum += length($0)} END {print sum}' "${FILES[@]}")
    TOTAL_BP=$(awk '!/^>/ {sum += length($0)} END {print sum+0}' "$FILE")

    if [ "$TOTAL_BP" -eq 0 ]; then
        echo "⚠ Skipping empty file: $FILE"
        continue
    fi
    # Load scaling steps
    if [ "$TOTAL_BP" -lt 50000 ]; then
        CORE=4; MEM=8; TIME=00:15:00
    elif [ "$TOTAL_BP" -lt 500000 ]; then
        CORE=8; MEM=16; TIME=00:30:00
    elif [ "$TOTAL_BP" -lt 1000000 ]; then
        CORE=8; MEM=16; TIME=01:00:00
    elif [ "$TOTAL_BP" -lt 10000000 ]; then
        CORE=16; MEM=32; TIME=02:00:00
    elif [ "$TOTAL_BP" -lt 500000000 ]; then
        CORE=32; MEM=64; TIME=03:00:00
    else
        CORE=64; MEM=128; TIME=05:00:00
    fi

    # to avoid over-threading
    MIN_BP_PER_CORE=500
    MAX_CORES_BY_SIZE=$(( TOTAL_BP / MIN_BP_PER_CORE ))
    MAX_CORES_BY_SIZE=$(( MAX_CORES_BY_SIZE < 1 ? 1 : MAX_CORES_BY_SIZE ))

    CORE=$(( CORE < MAX_CORES_BY_SIZE ? CORE : MAX_CORES_BY_SIZE ))

    # Set cluster limits
    CORE=$(( CORE > 64 ? 64 : CORE ))
    MEM=$(( MEM > 128 ? 128 : MEM ))

    # Infos debug
    echo "[INFO] File: $FILES"
    echo "[INFO] Total BP: $TOTAL_BP"
    echo "[INFO] Resources -> CPU Core(s): $CORE | RAM: ${MEM}G | TIME: $TIME"

    # Launch run-massblaster.slurm.sh with previously defined ressources
    sbatch \
        --job-name=MassBLASTer \
        --output=slurm-logs/%x_%j.out \
        --error=slurm-logs/%x_%j.err \
        --cpus-per-task="$CORE" \
        --mem="${MEM}G" \
        --time="$TIME" \
        run-massblaster.sh "$FILE"

    echo "[INFO] $FILE is now processed in run-massblaster.sh..."

done

# Récupérer le job ID du dernier job MassBLASTer soumis par l'utilisateur
JOBID=$(squeue -u $USER -o "%i %j" -h | grep MassBLASTer | tail -n 1 | awk '{print $1}')
echo "Job ID detected: $JOBID"

# Check for "R" running state, sleep 5 sec, repeat... 
until [ "$(squeue -j $JOBID -h -o %T)" = "RUNNING" ]; do
    echo "Job $JOBID is pending, waiting 5s..."
    sleep 5
done

# OPTIONAL: To check SLURM log output 
tail -n 50 -f $(ls -t slurm-logs/MassBLASTer_*.out | head -n 1)

