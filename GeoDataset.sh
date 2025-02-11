#!/bin/bash

#SBATCH --job-name=geo_dataset
#SBATCH --output=geo_dataset_%A_%a.log
#SBATCH --time=4:00:00
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --account=sihogan0

# Load required modules
module load Bioinformatics
module load python/3.12.1

# Set base directory for GEO accession directories
BASE_DIR="/nfs/turbo/umms-sihogan/crizza"
GEO_ACCESSIONS_FILE="$BASE_DIR/FetchOmics/geo_accessions.txt"

# Run GeoDataset
python /nfs/turbo/umms-sihogan/crizza/FetchOmics/GeoDataset.py "$GEO_ACCESSIONS_FILE" "$BASE_DIR" >> "$BASE_DIR/FetchOmics/geo_dataset.log" 2>&1
