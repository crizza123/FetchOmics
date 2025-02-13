#!/usr/bin/env python3
"""
SRRConvert.py

This script processes compressed .sra files for each specified GSE id.
For each GSE directory under <base_dir>/<GSE_ID>/, it finds all files ending with .sra 
and converts them into fastq files using the SRA Toolkit's fasterq-dump utility.

Key Notes:
    - The fasterq-dump utility can convert compressed .sra files directly into fastq format.
      For paired-end reads, the '--split-files' option is used to generate separate FASTQ files.
    - If the .sra file contains paired-end data, this will produce two files (e.g., sample_1.fastq and sample_2.fastq).
    
Usage:
    python SRRConvert.py --base_dir /path/to/FetchOmics --gse_list GSE113046 GSE106973
"""

import os
import glob
import logging
import argparse
import subprocess

def setup_logging() -> None:
    """Configure logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert compressed .sra files to fastq format using fasterq-dump with split-files option."
    )
    parser.add_argument(
        "--base_dir",
        required=True,
        help="Base directory containing GSE subdirectories (e.g., /nfs/turbo/umms-sihogan/crizza/FetchOmics)."
    )
    parser.add_argument(
        "--gse_list",
        required=True,
        nargs="+",
        help="List of GSE IDs to process (e.g., GSE113046 GSE106973)."
    )
    return parser.parse_args()

def convert_sra_to_fastq(sra_file: str) -> None:
    """Convert a single .sra file into fastq format using fasterq-dump with the --split-files option."""
    # Extract the SRR id from the filename (assumes file is named like SRRxxxxxxx.sra)
    srr_id = os.path.basename(sra_file).rsplit('.', 1)[0]
    logging.info(f"Processing SRR id '{srr_id}' from file: {sra_file}")

    # Build the fasterq-dump command with --split-files.
    command = ['fasterq-dump', sra_file, '--split-files']

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"Conversion output for {srr_id}:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"Conversion warnings for {srr_id}:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {srr_id}:\n{e.stderr}")

def process_gse_directory(gse_id: str, base_dir: str) -> None:
    """Process a single GSE directory by converting all .sra files found within it."""
    gse_dir = os.path.join(base_dir, gse_id)
    if not os.path.isdir(gse_dir):
        logging.warning(f"GSE directory not found: {gse_dir}")
        return

    # Find all .sra files in the GSE directory.
    sra_files = glob.glob(os.path.join(gse_dir, "*.sra"))
    if not sra_files:
        logging.warning(f"No .sra files found in directory: {gse_dir}")
        return

    logging.info(f"Found {len(sra_files)} .sra file(s) in {gse_dir}. Beginning conversion.")
    for sra_file in sra_files:
        convert_sra_to_fastq(sra_file)

def main() -> None:
    """Main function to parse arguments and process each GSE directory."""
    setup_logging()
    args = parse_arguments()

    # Process each specified GSE.
    for gse_id in args.gse_list:
        logging.info(f"Starting processing for {gse_id}")
        process_gse_directory(gse_id, args.base_dir)

if __name__ == '__main__':
    main()
