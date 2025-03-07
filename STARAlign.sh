#!/bin/bash
#SBATCH --job-name=star_align
#SBATCH --output=star_align_%j.out
#SBATCH --error=star_align_%j.err
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --partition=standard
#SBATCH --account=sihogan0

###############################################################################
# STARAlign.sh (Updated)
# ----------------------
# Runs STARAlign.py for single-end FASTQ files located in Data directory.
# Ensures paths are explicitly set between script directory and data location.
###############################################################################

# Load modules
module load Bioinformatics
module load star
module load python/3.12.1    # Ensure Python module has necessary packages

# Define directories explicitly
SCRIPT_DIR="/nfs/turbo/umms-sihogan/crizza/FetchOmics"  # Location of STARAlign.py
BASE_DIR="/nfs/turbo/umms-sihogan/crizza/Data"          # Location of your datasets (FASTQ files)

# List of datasets to process (update this if you add more datasets)
GSE_LIST="GSE128003 GSE128074"

# Number of threads (cpus) to use for STAR
THREADS=$SLURM_CPUS_PER_TASK

echo "=========================================================="
echo "[INFO] STAR Alignment job starting..."
echo "  Python script location : $SCRIPT_DIR/STARAlign.py"
echo "  Data location         : $BASE_DIR"
echo "  Datasets              : $GSE_LIST"
echo "  Threads               : $THREADS"
echo "=========================================================="

# Change directory to where the Python script is located
cd "$SCRIPT_DIR" || { echo "[ERROR] Cannot access $SCRIPT_DIR. Exiting."; exit 1; }

# Call the Python script, explicitly passing the correct data directory
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
