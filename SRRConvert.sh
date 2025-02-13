#!/bin/bash

#SBATCH --job-name=srr_convert
#SBATCH --output=srr_convert_%A_%a.log
#SBATCH --time=4:00:00
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --account=sihogan0

# Load required modules
module load Bioinformatics
module load sratoolkit
module load python/3.12.1

# Set base directory for GEO accession directories
BASE_DIR="/nfs/turbo/umms-sihogan/crizza"
GEO_ACCESSIONS_FILE="$BASE_DIR/FetchOmics/geo_accessions.txt"

# Run SRRConvert for each GSE ID listed in the GEO_ACCESSIONS_FILE
while IFS= read -r GSE_ID; do
    echo "Processing GSE ID: $GSE_ID"
    python /nfs/turbo/umms-sihogan/crizza/FetchOmics/SRRConvert.py \
        --base_dir "$BASE_DIR/FetchOmics" \
        --gse_list "$GSE_ID" >> "$BASE_DIR/FetchOmics/srr_convert.log" 2>&1

    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Successfully processed $GSE_ID."
    else
        echo "Failed to process $GSE_ID."
    fi
done < "$GEO_ACCESSIONS_FILE"

echo "SRR conversion process completed."
