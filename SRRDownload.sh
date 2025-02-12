#!/bin/bash

#SBATCH --job-name=srr_download
#SBATCH --output=srr_download_%A_%a.log
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

# Read GEO directories from the file
GEO_DIRS=$(cat "$GEO_ACCESSIONS_FILE")

# Run SRRDownload with the base directory and GEO directories
python /nfs/turbo/umms-sihogan/crizza/FetchOmics/SRRDownload.py "$BASE_DIR" $GEO_DIRS >> "$BASE_DIR/FetchOmics/srr_download.log" 2>&1
