"""Split downloaded Ministry PDFs into a clinical corpus and an archive.

The operation is deterministic and reversible: the complete original manifest
is kept in ``data/raw/archive/manifest.full.json`` while ``data/raw/manifest.json``
contains only documents selected for patient-facing clinical retrieval.
"""

import json
from pathlib import Path
import shutil


CLINICAL_FILENAMES = {
    "RVF_ CNOUSP 2025.pdf",
    "GUIDE DE LA CIRCONCISION DE L’ENFANT.pdf",
    "Circulaire_diffusion_manuel_rougeole.pdf",
    "Guide AFFECTIONS RESPIRATOIRES DE L ENFANT.pdf",
    "Guide DPM.pdf",
    "Guide national de p.e.c de la co-infection TB -VIH VF.pdf",
    "GUIDE NATIONAL DE PRISE EN CHARGE LA TB CHEZ L'ENFANT ET L'ADOSCENT VF.pdf",
    "Version Finale Lignes Directrices TEP PNLAT Version finale  Août 2023.pdf",
    "DMM.pdf",
    "GUIDE NATIONAL PTME.pdf",
    "Guide AES.pdf",
    "Référentiel de dépistage, de diagnostic et de prise en charge du Trouble du Spectre de l’Autisme.pdf",
    "Guide des évictions scolaires.pdf",
    "Critères recevabilté PF 2019.pdf",
    "Guide Infertilité .pdf",
    "Guide lutte ANTI-LEPREUSE 2014.pdf",
    "Guide de prise en charge HVC.pdf",
    "fiche A4 calculateur logigramme de PEC.pdf",
    "Guide risque cardiovasculaire VF  AZ 08 juillet 2019.pdf",
    "HTA et modes de vie sains VF janv 2020.pdf",
    "HTA et prévention des complications VF janv 2020.pdf",
    "guide Filières DE SOINS UNCV VF.pdf",
    "Reěfeěrnetiel deěpistage néonatal de la surdité chez l'enfant publié.pdf",
    "calendrier national de vaccination- (1).pdf",
    "Guide National  de prise en charge VF M.pdf",
    "Guide DAD (1).pdf",
    "Prise-en-charge-de-la-TB.pdf",
    "Guide des prélévements.pdf",
    "PAQUET MINIMUM DE SERVICES EN  ADDICTOLOGIE.pdf",
    "Protocole National et Kit de _Prévention et de gestion des Overdoses Chez les PUD_.pdf",
    "Guide des Urgences Pédiatriques.pdf",
    "Cadre référentiel équipements dialyse.pdf",
    "Guid_Couv_PCIE_Enf_Sain_FINAL_OK_27 dec17.pdf",
    "Guid_PEC_NNE_Hopital_11Nov17.pdf",
    "Guide tabac complet.pdf",
    "Guide_Pratique_v3.pdf",
    "stratégie de com et couseling DPCSC MAROC.pdf",
}


def curate(raw_dir: Path = Path("data/raw")) -> tuple[int, int]:
    manifest_path = raw_dir / "manifest.json"
    archive_dir = raw_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    full_manifest = archive_dir / "manifest.full.json"
    if not full_manifest.exists():
        full_manifest.write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    selected = []
    archived = []
    for record in records:
        filename = record["filename"]
        source = raw_dir / filename
        destination = archive_dir / filename
        if filename in CLINICAL_FILENAMES:
            if not source.exists() and destination.exists():
                shutil.move(destination, source)
            selected.append(record)
        else:
            if source.exists():
                shutil.move(source, destination)
            archived.append(record)

    temporary = manifest_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(manifest_path)
    (archive_dir / "manifest.archived.json").write_text(
        json.dumps(archived, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return len(selected), len(archived)


if __name__ == "__main__":
    kept, moved = curate()
    print(f"Clinical PDFs kept: {kept}; PDFs archived: {moved}")
