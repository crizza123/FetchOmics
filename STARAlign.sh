#!/bin/bash
#SBATCH --job-name=star_align
#SBATCH --output=star_align_%j.out
#SBATCH --error=star_align_%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --partition=standard
#SBATCH --account=sihogan0

###############################################################################
# STARAlign.sh
# ------------
# Submits a job to align single-end FASTQ files to GRCm39 in a nested directory
# structure: /nfs/turbo/umms-sihogan/crizza/Data/GSEXXX/SRRXXX/SRXXX/*.fastq
#
# Usage: sbatch STARAlign.sh
#
# Note: Adjust time, memory, partition, etc., as needed for your HPC usage.
###############################################################################

# Load modules
module load Bioinformatics
module load STAR
module load python/3.12.1    # or whichever Python module has necessary packages

# Define the base directory where your GSE datasets reside
BASE_DIR="/nfs/turbo/umms-sihogan/crizza/Data"

# List the GSE datasets you want to process (space-separated)
GSE_LIST="GSE106973 GSE128003 GSE128074"

# Number of threads (cpus) to use for STAR
THREADS=8

echo "=========================================================="
echo "[INFO] STAR Alignment job starting..."
echo "  Base directory : $BASE_DIR"
echo "  Datasets       : $GSE_LIST"
echo "  Threads        : $THREADS"
echo "=========================================================="

# Call the Python script to do the alignment logic
python STARAlign.py \
    --base_dir "$BASE_DIR" \
    --gse_list $GSE_LIST \
    --threads $THREADS

# Check exit status
if [[ $? -ne 0 ]]; then
    echo "[ERROR] STARAlign.py encountered an error. See star_align_${SLURM_JOB_ID}.err for details."
    exit 1
else
    echo "[INFO] STAR alignment job finished successfully."
fi
