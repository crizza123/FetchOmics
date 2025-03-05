#!/bin/bash
#
# SRRConvert_Fastq.sh
#
# SLURM submission script for converting existing .sra files into FASTQ
# via the convert_sra_to_fastq_standalone.py script, relying on the Python code
# to read <GSE_ID>_SRR.csv.
#
# This script:
#   - Reads a list of GSE IDs from geo_accessions.txt
#   - For each GSE, it calls the Python script with --gse_list GSE_ID
#   - The Python script itself handles reading run IDs from <GSE_ID>_SRR.csv
#   - No references to run_ids_<GSE_ID>.txt in this script.
#
# Usage:
#   sbatch SRRConvert_Fastq.sh
#

#SBATCH --job-name=srr_convert_fastq
#SBATCH --output=srr_convert_fastq_%j.out
#SBATCH --error=srr_convert_fastq_%j.err
#SBATCH --time=01:00:00
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --account=sihogan0

echo "[DEBUG] Slurm job name: ${SLURM_JOB_NAME}"
echo "[DEBUG] Slurm job ID: ${SLURM_JOB_ID}"
echo "[DEBUG] Node list: ${SLURM_NODELIST}"
echo "[DEBUG] Number of CPUs: ${SLURM_CPUS_PER_TASK}"
echo "[DEBUG] Memory: ${SLURM_MEM_PER_NODE}"

# -----------------------------------------------------------------------------
# 1) Load required modules for SRAToolkit and Python
# -----------------------------------------------------------------------------
module load Bioinformatics
module load sratoolkit
module load python/3.12.1

# -----------------------------------------------------------------------------
# 2) Define your environment variables
# -----------------------------------------------------------------------------
BASE_DIR="/nfs/turbo/umms-sihogan/crizza/FetchOmics"
GEO_ACCESSIONS_FILE="$BASE_DIR/geo_accessions.txt"

# Path to the Python script that converts .sra -> FASTQ.
# This .py script is assumed to handle reading <GSE_ID>_SRR.csv internally.
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

    # Check if the GSE directory exists
    GSE_DIR="$BASE_DIR/$GSE_ID"
    if [ ! -d "$GSE_DIR" ]; then
        echo "[ERROR] GSE directory not found: $GSE_DIR"
        continue
    fi

    # We simply call the Python script, passing the GSE ID via --gse_list
    # The Python script itself should look for <GSE_ID>_SRR.csv in BASE_DIR
    # or handle it however you've coded it (e.g., GSE113046_SRR.csv).
    echo "[DEBUG] Invoking Python script with --gse_list $GSE_ID"
    python "$CONVERSION_SCRIPT" \
        --base_dir "$BASE_DIR" \
        --gse_list "$GSE_ID"
        # --paired  # Uncomment if you want to force all runs in each GSE to be paired

    STATUS=$?
    echo "[DEBUG] Python script exit code: $STATUS"
    if [ $STATUS -eq 0 ]; then
        echo "[INFO] Successfully processed $GSE_ID"
    else
        echo "[ERROR] Failed to process $GSE_ID (exit code: $STATUS)"
    fi

done < "$GEO_ACCESSIONS_FILE"

echo "---------------------------------------------------------"
echo "[INFO] SRR-to-FASTQ conversion process completed."
