# MassBLATer pipeline #

## Introduction

Ce pipeline a été prévu pour lancer un blastn sur un grand nombre de séquences,  
rassemblée dans un fichier FASTA (.fas),  
en utilisant des bases de données ITS, comme UNITE ou INSD.  

En sortie, on obtient une page HTML dynamique qui permet de visualiser les réultats,  
ainsi qu'un fichier CSV (.csv).  

Le pipeline retient les trois meilleurs "hits"

---

## Entrées attendues

Idéalement, le pipeline attend un fichier FASTA (.fas) avec une ligne commencent par `>`,  
contenant le nom de la séquence et certaines infos,  
et une ligne avec la séquence trimmée (sans les primers).

Le format de nom de séquence attendu est le suivant :

```text
<SAMPLE_ID>_<YYMMDD>-<SAMPLE_CODE>[_<OPTIONAL_INFO>...]
````

C'est à dire :
Un identifiant de séquence; `_`; la date du séquençage; `-`; le code de l'échantillon; `_`; le primer uilisé (optionnel).

Exemple :

```fasta
>TJU-6_251027-L7_ITS1F
```

Il s'agit du format de séquence utilisé par le laboratoire Fasteris.
Il est toute fois possible de nommer ses échantillons de façon libre,
simplement en évitant le caractère `_`.

---

## Usage

1. uploader les données dans un fichiers `data`
2. transférer le fichier à traiter dans
   `~/unite-massblaster/massblaster_plutof_pub/indata`
3. ajouter `source_` au début du nom du fichier
   (ex: `source_MonFichierFasta.fas`)
4. lancer le pipeline avec la commande :

```bash
sbatch ~/unite-massblaster/launch-massblaster.slurm.sh
```

---

## SLURM

Par défaut, le pipeline utilise SLURM.

Il est possible de modifier le comportement de SLURM ou de lancer la commande localement
suprimant le snipet slurm au début du wrapper :

```text
~/unite-massblaster/launch-massblaster-v3.slurm.sh
```

---

## Description ligne par ligne du script de lancement de MassBLASTer

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

Lancement du container massblaster (apptainer ou singularity)
lancement du script de blast sur le nom de fichier trasnmis pas `"$CLEAN_NAME"`

---

### `-num_threads 4`

Le nombre de coeur CPU utiliser pour l'éxécution (ici 4)

---

### `-dust no`

Désactive le filtre de basses complexités sur les séquences.
Normalement dust supprime des motifs très répétitifs — ici on le coupe, car les ITS peuvent contenir des répétitions importantes et on ne veut pas les perdre.

---

### `-db "/massblaster_plutof_rel/data/plutof_fungi_its"`

Base de données contre laquelle on aligne les séquences :
Ici → `plutof_fungi_its`

Mais il y a d'autre option :

plutof_fungi_its:     "UNITE (only fungi); rDNA ITS"
plutof_nf_its:        "UNITE (non-fungi) / Other_euk_1; rDNA ITS"
insd_its:             "INSD (only fungi); rDNA ITS"
insd_nf_its:          "INSD (non-fungi); rDNA ITS / Other_euk_2"
envir_plutof_its:     "UNITE environmental (all eukaryotes) / Envir; rDNA ITS"
plutof_tri12:         "ToxGen; Tri12"
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

Remlacer la dernière partie du chemin par l'option choisie.

---

### `-outfmt 15`

Format de sortie → JSON (standard BLAST 15)
C’est pour cela que les fichiers .txt contiennent en réalité du JSON.

---

### `-reward 1`

Score de récompense pour une base identique (= +1 point par match correct)

---

### `-gapextend 2`

Coût d’extension d’un gap = 2
Donc un gap long coûte cher (bien), mais on ne pénalise pas l'ouverture initiale (utile pour l’ITS qui a souvent des indels structuraux).

---

### `-max_target_seqs 1`

On garde seulement le meilleur hit.
MassBlaster cherche juste la meilleure assignation possible.
Voir si il est possible de jouer avec cette option pour sortir les 3 meilleures hits par exemple.

---

### `-penalty -2`

Pénalité pour un mismatch (une base différente)(= -2 points)

Donc le score d’alignement est basé sur :
+1 pour un match
-2 pour une erreur

Apparement, ce ratio favorise des alignements précis, adaptés à l’ITS.

---

### `-word_size 28`

Longueur de mot (« seed word ») = 28 bases

Très long pour du BLASTN classique, mais cohérent avec la stratégie MassBlaster :
On veut des alignements plus stricts, éviter le bruit, et ne retenir que les hits sérieux.

---

### `-gapopen 0`

Coût d’ouverture d’un gap = 0

Il semblerait que cela soit inhabituel mais cohérent pour des séquences ITS, où les insertions / délétions sont très fréquentes.

