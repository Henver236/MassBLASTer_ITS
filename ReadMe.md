# MassBLATer pipeline #

## Disclaimer 
This software is a custom adaptation of the TU‑NHM/massblaster_plutof_pub pipeline. By using it, you agree to comply with the original project's licensing terms as set forth by its creator, Kessy Abarenkov for the Biodiversity Informatics research group of Tartu Univeristy. 
Here is the adresse of the original project : https://github.com/TU-NHM/massblaster_plutof_pub
The author of this customized version provides the code “as‑is” and makes no warranties regarding its performance, accuracy, or suitability for any particular purpose. Consequently, the author cannot be held responsible for the quality, correctness, or any consequences arising from the results generated with this pipeline. Users assume all risk associated with its deployment and should verify outputs independently before relying on them.

## Introduction

This pipeline is designed to run a blastn on a large number of sequences gathered in a FASTA file (.fas), using ITS databases such as UNITE or INSD.

The output consists of a dynamic HTML page that allows you to view the results, as well as a CSV file (.csv).

The pipeline keeps the three best “hits”.

---

## Expected Inputs

Ideally, the pipeline expects a FASTA file (.fas) with a header line that starts with `>`, containing the sequence name and some additional information, followed by a line with the trimmed sequence (without primers).

The expected sequence‑name format is:
```text
<SAMPLE_ID>_<YYMMDD>-<SAMPLE_CODE>[_<OPTIONAL_INFO>...]
````

În other words :
Sequence ID; `_`; sequencing date; `-`; sample code; `_`; the primer used (optionnal).

Exemple :
```fasta
>TJU-6_251027-L7_ITS1F
```
This is the naming convention used by the Fasteris laboratory. However, it's possible to name samples freely as long as the `_` character is avoided.

---

## Usage

1. Upload the data into a `data` folder.
2. Transfer the file to be processed to 
   `~/unite-massblaster/massblaster_plutof_pub/indata`
3. Prefix the file name with `source_` 
   (e.g.: `source_MonFichierFasta.fas`)
4. Launch the pipeline with the command:
```bash
sbatch ~/unite-massblaster/launch-massblaster.slurm.sh
```

---

## SLURM

By default, the pipeline runs under SLURM.
SLURM is used to optimise and schedule ressources usage on HPC cluster.

It is possible to modify the SLURM behavior or run the command locally by editing or removing the SLURM snippet at the beginning of the wrapper:
```text
~/unite-massblaster/launch-massblaster-v3.slurm.sh
```

---

## Line by line description of the MassBLASTer launch script

```bash
./massblaster.sif /run_massblaster.sh "$CLEAN_NAME" \
    -num_threads 4 \
    -dust no \
    -db "/massblaster_plutof_rel/data/plutof_fungi_its" \
    -outfmt 15 \
    -reward 1 \
    -gapextend 2 \
    -max_target_seqs 1 \
    -penalty -2 \
    -word_size 28 \
    -gapopen 0
```
---

### `./massblaster.sif /run_massblaster.sh "$CLEAN_NAME"`

The container massblaster.sif launches the blast script on the file name passed via `"$CLEAN_NAME"`

---

### `-num_threads 4`

Number of CPU cores to use (here 4).

---

### `-dust no`
Disables the low‑complexity filter. Normally, DUST removes highly repetitive motifs; it's turn off because ITS regions can contain important repeats that we don’t want to lose.

---

### `-db "/massblaster_plutof_rel/data/plutof_fungi_its"`

Database against which the sequences are compare. 
In this example it's  `plutof_fungi_its`

Other database options are:
```bash
Option               "Description"

plutof_fungi_its:    "UNITE (only fungi); rDNA ITS"
plutof_nf_its:       "UNITE (non-fungi) / Other_euk_1; rDNA ITS"
insd_its:            "INSD (only fungi); rDNA ITS"
insd_nf_its:         "INSD (non-fungi); rDNA ITS / Other_euk_2"
envir_plutof_its:    "UNITE environmental (all eukaryotes) / Envir; rDNA ITS"
plutof_tri12:        "ToxGen; Tri12"
plutof1:             "UNITE+INSD"
plutof2:             "UNITE+Envir"
plutof3:             "UNITE+Other_euk"
plutof4:             "INSD+Envir"
plutof5:             "INSD+Other_euk"
plutof6:             "Envir+Other_euk"
plutof7:             "UNITE+INSD+Envir"
plutof8:             "UNITE+INSD+Other_euk"
plutof9:             "INSD+Envir+Other_euk"
plutof10:            "UNITE+Envir+Other_euk"
plutof11:            "UNITE+INSD+Envir+Other_euk"
```
Replace the last part of the path with the desired option.

---

### `-outfmt 15`
Output format → JSON (standard BLAST format 15). That’s why the .txt files actually contain JSON.

---

### `-reward 1`
Reward score for a matching base (+1 per correct match).

---

### `-gapextend 2`
Cost to extend a gap = 2. 
A long gap therefore costs more, but the opening penalty is zero (useful for ITS, which often has structural indels).
---

### `-max_target_seqs 1`
Keep only the best hit. 
MassBLASTER returns the single best assignment by default.
I adjust this parameter to retrieve the top 3 hits, but you can keep more hits.

---

### `-penalty -2`
Penalty for a mismatch. 
One different base = –2 points.
Thus, the alignment score is calculated as +1 for a match, –2 for a mismatch. 
This ratio favors precise alignments, which is suited with ITS data.

---

### `-word_size 28`
Seed word length = 28 bases. 
This is unusually long for classic BLASTN but it's align with MassBLASTER’s strategy: stricter matches, less noise, and only serious hits retained.

---

### `-gapopen 0`
Gap opening cost = 0. 
apparently it's atypical, but this makes sense for ITS sequences where insertions/deletions are very frequent.


