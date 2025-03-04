#!/bin/bash
#
# SRRConvert_Fastq.sh
#
# SLURM submission script for converting existing .sra files into FASTQ
# via the convert_sra_to_fastq_standalone.py script.
#
# - Finds a CSV ending in *_SRA_RunInfo.csv in the GSE folder (e.g. 200106973_SRA_RunInfo.csv),
#   and passes it to the Python script for dynamic single- or paired-end detection.
#
# - No changes needed in convert_sra_to_fastq_standalone.py.
#
# Usage:
#   sbatch SRRConvert_Fastq.sh
#

#SBATCH --job-name=srr_convert_fastq        # Job name
#SBATCH --output=srr_convert_fastq_%j.out   # Standard output file
#SBATCH --error=srr_convert_fastq_%j.err    # Standard error file
#SBATCH --time=01:00:00                     # Time limit (HH:MM:SS)
#SBATCH --partition=standard                # Partition name
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8                   # Number of CPU cores
#SBATCH --mem=64G                           # Memory allocation
#SBATCH --ntasks=1
#SBATCH --account=sihogan0                  # Account name (if required)

# -----------------------------------------------------------------------------
# 1) Load required modules: sratoolkit, python, etc.
# -----------------------------------------------------------------------------
module load Bioinformatics
module load sratoolkit
module load python/3.12.1

# -----------------------------------------------------------------------------
# 2) Variables for your environment
# -----------------------------------------------------------------------------
BASE_DIR="/nfs/turbo/umms-sihogan/crizza/FetchOmics"
GEO_ACCESSIONS_FILE="$BASE_DIR/geo_accessions.txt"

# The existing Python script you want to run as-is:
CONVERSION_SCRIPT="$BASE_DIR/convert_sra_to_fastq_standalone.py"

echo "[INFO] Starting SRA-to-FASTQ conversion with $CONVERSION_SCRIPT"
echo "[INFO] Base Directory:       $BASE_DIR"
echo "[INFO] GEO Accessions File:  $GEO_ACCESSIONS_FILE"

# -----------------------------------------------------------------------------
# 3) Loop over each GSE in geo_accessions.txt
# -----------------------------------------------------------------------------
while IFS= read -r GSE_ID; do
    # Skip empty lines or comment lines
    if [[ -z "$GSE_ID" ]] || [[ "$GSE_ID" =~ ^# ]]; then
        continue
    fi

    echo "---------------------------------------------------------"
    echo "[INFO] Processing GSE: $GSE_ID"

    # The GSE directory:
    GSE_DIR="$BASE_DIR/$GSE_ID"

    # 3a) Confirm the GSE folder exists
    if [ ! -d "$GSE_DIR" ]; then
        echo "[ERROR] GSE directory not found: $GSE_DIR"
        continue
    fi

    # 3b) Find SRR IDs from a text file, e.g. run_ids_GSE12345.txt
    RUN_ID_FILE="$BASE_DIR/run_ids_${GSE_ID}.txt"
    if [ ! -f "$RUN_ID_FILE" ]; then
        echo "[ERROR] Missing SRR ID file: $RUN_ID_FILE"
        continue
    fi

    # Read all SRR IDs from the file
    RUN_IDS=$(cat "$RUN_ID_FILE")
    echo "[INFO] SRR IDs for $GSE_ID: $RUN_IDS"

    # 3c) Attempt to find a file ending in *_SRA_RunInfo.csv in the GSE folder
    # Using "find" with -maxdepth 1 ensures we only look in the immediate folder
    RUNINFO_CSV=$(find "$GSE_DIR" -maxdepth 1 -type f -name "*_SRA_RunInfo.csv" | head -n 1)

    if [ -z "$RUNINFO_CSV" ]; then
        echo "[WARNING] No *_SRA_RunInfo.csv file found in $GSE_DIR"
        echo "[WARNING] The script will default runs to SINGLE (unless you force --paired)."
    else
        echo "[INFO] Found CSV: $RUNINFO_CSV"
    fi

    # -----------------------------------------------------------------------------
    # 4) Run the Python script with or without --runinfo_csv
    #    (No changes needed in the .py script)
    # -----------------------------------------------------------------------------
    if [ -n "$RUNINFO_CSV" ]; then
        python "$CONVERSION_SCRIPT" \
            --base_dir "$BASE_DIR" \
            --gse_id "$GSE_ID" \
            --run_ids $RUN_IDS \
            --runinfo_csv "$RUNINFO_CSV"
            # --paired  # If you wanted to force everything as paired in addition
                       # to the CSV detection, uncomment this line. Usually not needed.
    else
        python "$CONVERSION_SCRIPT" \
            --base_dir "$BASE_DIR" \
            --gse_id "$GSE_ID" \
            --run_ids $RUN_IDS
            # --paired  # If you want to force everything as paired-end
    fi

    # Check status
    if [ $? -eq 0 ]; then
        echo "[INFO] Successfully processed $GSE_ID"
    else
        echo "[ERROR] Failed to process $GSE_ID"
    fi

done < "$GEO_ACCESSIONS_FILE"

echo "---------------------------------------------------------"
echo "[INFO] SRR-to-FASTQ conversion process completed."
