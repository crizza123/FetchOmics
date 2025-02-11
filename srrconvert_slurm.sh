#!/bin/bash

#SBATCH --job-name=srr_convert

#SBATCH --output=srr_convert_%A_%a.out

#SBATCH --error=srr_convert_%A_%a.err

#SBATCH --time=4:00:00

#SBATCH --partition=standard

#SBATCH --nodes=1

#SBATCH --ntasks=1

#SBATCH --cpus-per-task=8

#SBATCH --mem=32G

#SBATCH --array=1-64%5  # Run 64 tasks, 5 concurrently

#SBATCH --account=sihogan0



# Load required modules

module load sratoolkit

module load python/3.12.1



# Set base directory for GEO accession directories

BASE_DIR="/nfs/turbo/umms-sihogan/crizza"

GEO_ACCESSIONS_FILE="/nfs/turbo/umms-sihogan/crizza/FetchOmics/geo_accessions.txt"



# Run SRRConvert with correct base directory

python /nfs/turbo/umms-sihogan/crizza/FetchOmics/SRRConvert.py "$GEO_ACCESSIONS_FILE" "$BASE_DIR"


