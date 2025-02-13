#!/bin/bash
#
# SRRConvert.sh
#
# SLURM submission script for running SRRConvert.py.
#
# This script passes the required arguments --base_dir and --gse_list to the Python script.
#
# Usage:
#   sbatch SRRConvert.sh
#

#SBATCH --job-name=srr_convert             # Job name
#SBATCH --output=srr_convert_%j.out         # Standard output file (with job ID)
#SBATCH --error=srr_convert_%j.err          # Standard error file (with job ID)
#SBATCH --time=01:00:00                    # Time limit (HH:MM:SS)
#SBATCH --partition=standard                # Partition name (update this to your cluster's partition)
#SBATCH --nodes=1                          # Number of nodes
#SBATCH --ntasks=1                         # Number of tasks (processes)

# Load required modules
module load Bioinformatics
module load sratoolkit
module load python/3.12.1

# Define the base directory where your GSE subdirectories are located.
BASE_DIR="/nfs/turbo/umms-sihogan/crizza/FetchOmics"

# Define the list of GSE IDs to process.
# Read GSE IDs from the geo_accessions.txt file.
GEO_ACCESSIONS_FILE="$BASE_DIR/geo_accessions.txt"

# Debug: Echo the variables for logging purposes.
echo "Running SRRConvert.py with BASE_DIR: ${BASE_DIR}"
echo "Processing GSE IDs from file: ${GEO_ACCESSIONS_FILE}"

# Run SRRConvert for each GSE ID listed in the GEO_ACCESSIONS_FILE
while IFS= read -r GSE_ID; do
    echo "Processing GSE ID: $GSE_ID"
    python /nfs/turbo/umms-sihogan/crizza/FetchOmics/SRRConvert.py --base_dir "$BASE_DIR" --gse_list "$GSE_ID"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Successfully processed $GSE_ID."
    else
        echo "Failed to process $GSE_ID."
    fi
done < "$GEO_ACCESSIONS_FILE"

echo "SRR conversion process completed."
