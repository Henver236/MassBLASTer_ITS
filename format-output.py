#!/usr/bin/env python3

import json
import csv
import re
import os
from html import escape
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
#  PARAMÈTRES
# ──────────────────────────────────────────────

# Obtenir le répertoire où le script Python est situé
BASE_DIR = Path(__file__).parent  # Cela renverra le répertoire du script Python

# Input : où se trouvent le fichier JSON créé par blastn
INPUT_DIR = BASE_DIR / "massblaster_plutof_pub/outdata"
# Output : dossier où sont créer le CSV et HTML
OUTPUT_BASE = BASE_DIR / "output" # Alternative : Path("output") pour relatif au pwd

# Création automatique du dossier final avec le timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
timestamp2 = datetime.now().strftime("%Y%m%d")
FINAL_OUTPUT_DIR = OUTPUT_BASE / f"MassBLASTer_output_{timestamp}"
FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Fichier CSV global
CSV_OUT = FINAL_OUTPUT_DIR / f"massblaster_results_{timestamp}.csv"

# ──────────────────────────────────────────────
#  CSV
# ──────────────────────────────────────────────

csv_rows = []
csv_header = [
    "source_file", "query_id", "query_title", "query_len",
    "sample_name",
    "sci_name",
    "hit_num", "accession", "title", "hit_len",
    "hsp_num", "bit_score", "evalue", "identity",
    "align_len", "identity_percent",
    "query_from", "query_to", "hit_from", "hit_to", "gaps",
    "qseq", "hseq", "midline"
]

# ──────────────────────────────────────────────
#  DÉTECTION DES FICHIERS JSON
# ──────────────────────────────────────────────

json_like_ext = {".json", ".fas", ".fasta", ".txt"}
json_files = []

for f in sorted(INPUT_DIR.iterdir()):
    if f.suffix.lower() in json_like_ext and f.is_file():
        try:
            with f.open() as h:
                if h.read(1).strip() == "{":
                    json_files.append(f)
        except Exception:
            pass

print(f"Trouvé {len(json_files)} fichiers JSON-like dans {INPUT_DIR}")

# ──────────────────────────────────────────────
#  FONCTIONS
# ──────────────────────────────────────────────

def parse_sample_info(query_title):
    """
    Parsing permissif du query_title.
    """

    sample_id = "unknown"
    date_raw = None
    date_iso = "unknown"
    sample_code = "NA"

    if not query_title:
        return sample_id, date_raw, date_iso, sample_code

    parts = query_title.split("_")

    # Sample ID
    sample_id = parts[0]

    if len(parts) < 2:
        return sample_id, date_raw, date_iso, sample_code

    mid = parts[1]

    # Date YYMMDD
    m_date = re.search(r"(\d{6})", mid)
    if m_date:
        date_raw = m_date.group(1)
        try:
            yy = int(date_raw[:2])
            mm = int(date_raw[2:4])
            dd = int(date_raw[4:6])
            year = 2000 + yy if yy < 70 else 1900 + yy
            date_iso = f"{year:04d}-{mm:02d}-{dd:02d}"
        except Exception:
            date_iso = "invalid"

    # Code échantillon
    m_code = re.search(r"-([A-Za-z0-9]+)", mid)
    if m_code:
        sample_code = m_code.group(1)

    return sample_id, date_raw, date_iso, sample_code


def colorize_alignment(q, m, h):
    cq, cm, ch = "", "", ""
    for qc, mc, hc in zip(q, m, h):
        if mc == "|":
            style = 'color:green'
        elif qc == "-" or hc == "-":
            style = 'color:#888'
        else:
            style = 'color:red'

        cq += f'<span style="{style}">{qc}</span>'
        cm += f'<span style="{style}">{mc}</span>'
        ch += f'<span style="{style}">{hc}</span>'
    return cq, cm, ch


def make_blast_style_alignment(hsp):
    qseq = hsp["qseq"]
    mseq = hsp["midline"]
    hseq = hsp["hseq"]

    q_pos = hsp["query_from"]
    h_pos = hsp["hit_from"]

    BLOCK = 60
    html = "<strong>Alignment :</strong><br><code>"

    for i in range(0, len(qseq), BLOCK):
        q_block = qseq[i:i+BLOCK]
        m_block = mseq[i:i+BLOCK]
        h_block = hseq[i:i+BLOCK]

        cq, cm, ch = colorize_alignment(q_block, m_block, h_block)

        html += (
            f"Query {str(q_pos).ljust(4)} {cq}<br>"
            f"{' '*11}{cm}<br>"
            f"Sbjct {str(h_pos).ljust(4)} {ch}<br><br>"
        )

        q_pos += len(q_block.replace("-", ""))
        h_pos += len(h_block.replace("-", ""))

    html += "</code>"
    return html

# ──────────────────────────────────────────────
#  PARSE + HTML
# ──────────────────────────────────────────────

for json_file in json_files:
    print(f"[INFO] Lecture de : {json_file.name}")

    with json_file.open() as f:
        data = json.load(f)

    reports = data["BlastOutput2"]

    clean_name = json_file.stem.replace("source_", "").replace(".fas", "")
    html_out = FINAL_OUTPUT_DIR / f"{clean_name}_{timestamp}.html"
    html_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    example_title = reports[0]["report"]["results"]["search"]["query_title"]
    sample_id, _, seq_date_iso, _ = parse_sample_info(example_title)

    seq_label = seq_date_iso if seq_date_iso != "unknown" else "unknown date"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>MassBLASTer Results — {escape(clean_name)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h2 {{ margin-top: 40px; text-decoration: underline; }}
table {{ border-collapse: collapse; margin-left: 30px; margin-bottom: 30px; }}
th, td {{ border: 1px solid #aaa; padding: 6px 10px; white-space: nowrap; }}
th {{ background: #002060; color: white; }}
code {{ background: #f5f5f5; padding: 6px; display: block; white-space: pre; }}
h3 {{ margin-left: 30px; }}

/* Bouton flottant "Retour en haut" */
.back-to-top {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #002060;
  color: white;
  padding: 10px 15px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}}
.back-to-top:hover {{
  background: #003399;
}}
.query-separator {{
  border: 0;
  border-top: 3px solid #800000;  /* rouge foncé */
  margin: 40px 0 20px 0;
}}
</style>
</head>
<body>
<a id="top"></a>

<h1>MassBLASTer Results — {escape(clean_name)}</h1>
<p><strong>Sequenced on {seq_label}</strong></p>
<p><em>MassBLASTed on {html_timestamp}</em></p>

<h2>Queries Index</h2>
<table>
<tr>
<th>Query</th><th>Sample ID</th><th>Sample name</th>
<th>Hit 1</th><th>Hit 2</th><th>Hit 3</th>
</tr>
"""

    # INDEX
    for rep in reports:
        search = rep["report"]["results"]["search"]
        sid, _, _, scode = parse_sample_info(search["query_title"])

        hits = search["hits"][:3]
        cells = ""

        for h in hits:
            desc = h["description"][0]
            hsp = h["hsps"][0]
            sci_name = desc["title"].split("|")[-1].replace("_", " ")
            pct = 100 * hsp["identity"] / hsp["align_len"]
            cells += f"<td><i>{escape(sci_name)}</i><br>{pct:.1f}%</td>"

        cells += "<td></td>" * (3 - len(hits))

        html += f"""
<tr>
<td><a href="#{escape(search['query_id'])}">{escape(search['query_id'])}</a></td>
<td>{escape(sid)}</td>
<td>{escape(scode)}</td>
{cells}
</tr>
"""

    html += "</table>"

    # DÉTAILS
    for rep in reports:
        search = rep["report"]["results"]["search"]
        sid, _, _, scode = parse_sample_info(search["query_title"])

        html += f"""
<hr class="query-separator">
<h2 id="{escape(search['query_id'])}">{escape(search['query_id'])}</h2>
<p><strong>Sequence ID :</strong> {escape(search['query_title'])}</p>
<p><strong>Sample name :</strong> {escape(scode)}</p>
"""

        for hit in search["hits"]:
            desc = hit["description"][0]
            html += f"""
<h3>Hit #{hit['num']}</h3>
<table>
<tr><th>Accession</th><td>{escape(desc['accession'])}</td></tr>
<tr><th>Title</th><td><i>{escape(desc['title'])}</i></td></tr>
<tr><th>Hit length</th><td>{hit['len']}</td></tr>
"""

            for hsp in hit["hsps"]:
                pct = hsp["identity"] / hsp["align_len"] * 100
                sci_name = desc["title"].split("|")[-1].replace("_", " ")

                csv_rows.append([
                    json_file.name, search["query_id"], search["query_title"],
                    search["query_len"], scode, sci_name,
                    hit["num"], desc["accession"], desc["title"], hit["len"],
                    hsp["num"], hsp["bit_score"], hsp["evalue"],
                    hsp["identity"], hsp["align_len"], f"{pct:.2f}",
                    hsp["query_from"], hsp["query_to"],
                    hsp["hit_from"], hsp["hit_to"], hsp["gaps"],
                    hsp["qseq"], hsp["hseq"], hsp["midline"]
                ])

                html += f"""
<tr><th>Bit score</th><td>{hsp['bit_score']}</td></tr>
<tr><th>E-value</th><td>{hsp['evalue']}</td></tr>
<tr><th>Identity</th><td>{pct:.1f}%</td></tr>
</table>
{make_blast_style_alignment(hsp)}
<table>
"""

            html += "</table>"

    html += """
    <a href="#top" class="back-to-top">↑ Back to the top</a>
    </body></html>
    """


    with html_out.open("w") as f:
        f.write(html)

    print(f"[OK]  ✔ HTML file generated : {html_out.name}")

# CSV global
with open(CSV_OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(csv_header)
    writer.writerows(csv_rows)

print(f"\n[OK] ✔ CSV file generated : {CSV_OUT}")
print(f"[OK] ✔ All results are in : {FINAL_OUTPUT_DIR}\n")
