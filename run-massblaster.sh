#!/usr/bin/env bash

# Measuring time
START=$(date +%s)

# Setting verbose output for debugging
set -exo pipefail

BASE_DIR="$PWD"
INPUT_DIR="$BASE_DIR/massblaster_plutof_pub/indata"

THREADS=${SLURM_CPUS_PER_TASK:-1}

# Debug :
echo "DEBUG: BASE_DIR = $BASE_DIR"
echo "DEBUG: INPUT_DIR = $INPUT_DIR"
echo "DEBUG: pwd = $(pwd)"
echo "DEBUG: contenu de INPUT_DIR :"
ls -l "$INPUT_DIR" || echo "⚠ INPUT_DIR not reachable ⚠"

shopt -s nullglob
FILES=("$INPUT_DIR"/source_*.fas)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "⚠ No file source_*.fas found ⚠"
    exit 1
fi

# Récupère le fichier qui commence par "source_"
SOURCE_FILE="${FILES[0]}"
# Extrait uniquement le nom du fichier (sans le chemin)
SOURCE_FILENAME=$(basename "$SOURCE_FILE")
# Retire le préfixe "source_"
CLEAN_NAME=${SOURCE_FILENAME#source_}

# Affiche pour vérification
echo "Source file : $SOURCE_FILE"
echo "Cleaned name : $CLEAN_NAME"

# création du dossier de sortie :
mkdir -p "output"

cd "$BASE_DIR/massblaster_plutof_pub"

apptainer exec massblaster.sif /run_massblaster.sh "$CLEAN_NAME" \
    -num_threads "$THREADS" \
    -dust no \
    -db "/massblaster_plutof_rel/data/plutof13" \
    -outfmt 15 \
    -reward 1 \
    -gapextend 2 \
    -max_target_seqs 1 \
    -penalty -2 \
    -word_size 28 \
    -gapopen 0

python3 "$BASE_DIR/format-output.py"

## Coping & Cleaning folders...
cd ..
# Retrieve the last MassBLASTer_output_* folder and store it in the last_dir variable :
last_dir="$(ls -d output/MassBLASTer_output_* 2>/dev/null | sort -r | head -n 1)"
# (Optionnal) check that the folder is found :
[ -z "$last_dir" ] && echo "⚠ No folder output/MassBLASTer_output_* found ⚠" && exit 1
# Coping file in the folder specified under $last_dir :
cp -rv massblaster_plutof_pub/outdata/* "$last_dir"
# Removing files in outdata/ and userdir/ so these folders are ready for the next run :
rm -rf massblaster_plutof_pub/outdata/* massblaster_plutof_pub/userdir/*

# Measuring time - end
END=$(date +%s)
ELAPSED=$((END - START))

#echo "[OK] ✔✔✔ MassBLASTer pipeline completed in $ELAPSED seconds ! "

printf "[OK]  ✔✔✔ MassBLASTer pipeline completed in %02d:%02d:%02d\n" $((ELAPSED/3600)) $((ELAPSED%3600/60)) $((ELAPSED%60))