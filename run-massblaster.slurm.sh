#!/usr/bin/env bash

#SBATCH --job-name=MassBLASTer
#SBATCH --output=slurm-logs/%x_%j.out
#SBATCH --error=slurm-logs/%x_%j.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00


#set -euxo pipefail
set -exo pipefail

BASE_DIR="$PWD"
INPUT_DIR="$BASE_DIR/massblaster_plutof_pub/indata"

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
    -num_threads 8 \
    -dust no \
    -db "/massblaster_plutof_rel/data/ITS_RefSeq_Fungi" \
    -outfmt 15 \
    -reward 1 \
    -gapextend 2 \
    -max_target_seqs 3 \
    -penalty -2 \
    -word_size 28 \
    -gapopen 0

python "$BASE_DIR/format-output.py"

# Cleaning folders...
#rm -rf outdata/* userdir/*

echo "\e[32m ✔ MassBLASTer pipeline completed ! \e[0m"
