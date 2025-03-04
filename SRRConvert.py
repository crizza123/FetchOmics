#!/usr/bin/env python
# coding: utf-8

import os
import sys
import glob
import argparse
import subprocess
import pandas as pd
from utils import log_message, create_directory

class SRRConvert:
    def __init__(self, base_dir: str):
        """
        Initialize SRRConvert with base directory.
        
        Args:
            base_dir (str): Base directory where GSE subdirectories are located.
        """
        self.base_dir = base_dir

    def convert_srr_to_fastq(self, srr_ids: list, accession: str) -> None:
        """
        Convert SRA files to FASTQ format for a list of SRR IDs.
        
        Args:
            srr_ids (list): List of SRR IDs to convert.
            accession (str): GEO accession ID.
        """
        geo_dir = os.path.join(self.base_dir, accession)
        
        # Get library layout information if available
        runinfo_file = os.path.join(geo_dir, f"{accession}_SRA_RunInfo.csv")
        layout_map = {}
        
        if os.path.exists(runinfo_file):
            try:
                runinfo_df = pd.read_csv(runinfo_file)
                if "Run" in runinfo_df.columns and "LibraryLayout" in runinfo_df.columns:
                    layout_map = {row["Run"]: row["LibraryLayout"] for _, row in runinfo_df.iterrows()}
            except Exception as e:
                log_message(f"Error reading RunInfo file: {e}", level="WARNING")
        
        for srr_id in srr_ids:
            # The SRR directory should be in the GEO directory
            srr_dir = os.path.join(geo_dir, srr_id)
            
            # Use glob to find the SRA file regardless of its nested location
            sra_file_pattern = os.path.join(srr_dir, "**", f"{srr_id}.sra")
            sra_files = glob.glob(sra_file_pattern, recursive=True)
            
            if not sra_files:
                log_message(f"SRA file not found for {srr_id}. Checking for alternative locations...", level="WARNING")
                
                # Check additional common locations
                alt_patterns = [
                    os.path.join(srr_dir, "SRA", f"{srr_id}.sra"),
                    os.path.join(srr_dir, f"{srr_id}.sra"),
                    os.path.join(geo_dir, f"{srr_id}", f"{srr_id}.sra")
                ]
                
                for pattern in alt_patterns:
                    if os.path.exists(pattern):
                        sra_files = [pattern]
                        log_message(f"Found SRA file at: {pattern}")
                        break
                
                if not sra_files:
                    log_message(f"SRA file not found for {srr_id}. Skipping conversion.", level="ERROR")
                    continue
            
            sra_file = sra_files[0]  # Use the first found SRA file
            
            # Determine library layout
            layout = layout_map.get(srr_id, "SINGLE").upper()
            
            # Output to the same directory as the SRA file
            output_dir = os.path.dirname(sra_file)
            
            log_message(f"Converting {srr_id} to FASTQ in {output_dir}...")
            
            try:
                # Use fasterq-dump with --split-files option
                fasterq_command = [
                    "fasterq-dump",
                    "--split-files",
                    sra_file,
                    "-O", output_dir
                ]
                
                subprocess.run(fasterq_command, check=True, text=True)
                
                # Handle file naming based on layout
                if layout == "SINGLE":
                    # For single-end reads, rename _1.fastq to .fastq if needed
                    single_fastq = os.path.join(output_dir, f"{srr_id}_1.fastq")
                    if os.path.exists(single_fastq):
                        target_fastq = os.path.join(output_dir, f"{srr_id}.fastq")
                        os.rename(single_fastq, target_fastq)
                        log_message(f"Renamed {single_fastq} to {target_fastq}")
                
                log_message(f"Successfully converted {srr_id} to FASTQ format in {output_dir}")
                
            except subprocess.CalledProcessError as e:
                log_message(f"Error converting {srr_id} to FASTQ: {e}", level="ERROR")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Convert SRA files to FASTQ format.")
    parser.add_argument("--base_dir", required=True, help="Base directory where GSE subdirectories are located.")
    parser.add_argument("--gse_list", nargs="+", required=True, help="List of GSE IDs to process.")
    return parser.parse_args()

def main():
    """Main function to run SRRConvert."""
    args = parse_arguments()
    
    converter = SRRConvert(args.base_dir)
    
    for gse_id in args.gse_list:
        log_message(f"Processing GSE ID: {gse_id}")
        
        # Get SRR IDs for this GSE
        srr_csv_path = os.path.join(args.base_dir, gse_id, f"{gse_id}_SRR.csv")
        
        if not os.path.exists(srr_csv_path):
            log_message(f"SRR CSV file not found for {gse_id}. Skipping.", level="WARNING")
            continue
        
        try:
            srr_df = pd.read_csv(srr_csv_path)
            if "Run" not in srr_df.columns:
                log_message(f"'Run' column not found in {srr_csv_path}. Skipping {gse_id}.", level="ERROR")
                continue
                
            srr_ids = srr_df["Run"].tolist()
            converter.convert_srr_to_fastq(srr_ids, gse_id)
            
        except Exception as e:
            log_message(f"Error processing {gse_id}: {e}", level="ERROR")

if __name__ == "__main__":
    main()
