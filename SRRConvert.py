#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import csv  # used if you have multiple columns or a header in the CSV

def log_message(msg, level="INFO"):
    """Utility function to log a message with a specified level."""
    print(f"[{level}] {msg}")

def download_sra_files(run_ids, base_dir, gse_id):
    """
    Downloads .sra files for each run in `run_ids`, placing them in:
        base_dir/GSE_ID/SRR_ID/SRR_ID.sra

    Debugging messages included to track folder creation and downloading.
    """
    gse_dir = os.path.join(base_dir, gse_id)
    log_message(f"Ensuring GSE directory exists: {gse_dir}", "DEBUG")
    os.makedirs(gse_dir, exist_ok=True)

    for run_id in run_ids:
        srr_dir = os.path.join(gse_dir, run_id)  # e.g. GSExxx/SRRxxx
        log_message(f"Creating/using SRR directory: {srr_dir}", "DEBUG")
        os.makedirs(srr_dir, exist_ok=True)

        sra_filename = f"{run_id}.sra"
        sra_path = os.path.join(srr_dir, sra_filename)
        log_message(f"Expecting SRA file at: {sra_path}", "DEBUG")

        prefetch_cmd = ["prefetch", run_id, "-O", srr_dir]
        log_message(f"Running prefetch for {run_id}: {' '.join(prefetch_cmd)}", "DEBUG")

        try:
            subprocess.run(prefetch_cmd, check=True, text=True)
            log_message(f"Successfully downloaded {run_id} to {srr_dir}")
        except subprocess.CalledProcessError as e:
            log_message(f"Error downloading {run_id}: {e}", level="ERROR")
            continue

        if not os.path.isfile(sra_path):
            log_message(f"{sra_path} not found after prefetch.", level="WARNING")

def convert_sra_to_fastq(run_ids, base_dir, gse_id, runinfo_dict=None):
    """
    Converts .sra files to FASTQ, detecting SINGLE vs. PAIRED from runinfo_dict if provided.
    Directory structure assumed: base_dir/GSE_ID/SRR_ID/SRR_ID.sra.

    Debugging statements help track the conversion process and file renaming.
    """
    gse_dir = os.path.join(base_dir, gse_id)
    log_message(f"Ensuring GSE directory exists: {gse_dir}", "DEBUG")

    for run_id in run_ids:
        srr_dir = os.path.join(gse_dir, run_id)
        sra_path = os.path.join(srr_dir, f"{run_id}.sra")

        if not os.path.exists(sra_path):
            log_message(f"{sra_path} does not exist. Skipping.", level="WARNING")
            continue

        log_message(f"Converting {run_id}.sra to FASTQ...", "DEBUG")
        conv_cmd = ["fasterq-dump", "--split-files", "--threads", "4", sra_path, "-O", srr_dir]
        log_message(f"Running fasterq-dump: {' '.join(conv_cmd)}", "DEBUG")

        try:
            subprocess.run(conv_cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            log_message(f"fasterq-dump failed for {run_id}: {e}", level="ERROR")
            continue
        
        # Determine layout from runinfo_dict or default to SINGLE
        layout = runinfo_dict.get(run_id, "SINGLE").upper() if runinfo_dict else "SINGLE"
        log_message(f"Detected layout for {run_id}: {layout}", "DEBUG")

        if layout == "PAIRED":
            log_message(f"{run_id}: Paired-end data – FASTQ files split into _1 and _2.")
        else:
            # Single-end: rename *_1.fastq -> .fastq
            single_fastq = os.path.join(srr_dir, f"{run_id}_1.fastq")
            target_fastq = os.path.join(srr_dir, f"{run_id}.fastq")
            if os.path.exists(single_fastq):
                log_message(f"Renaming {single_fastq} to {target_fastq}", "DEBUG")
                os.rename(single_fastq, target_fastq)
                log_message(f"{run_id}: Single-end data – renamed '{run_id}_1.fastq' to '{run_id}.fastq'.")

        # Optional: remove the .sra file to save space
        # log_message(f"Removing {sra_path}", "DEBUG")
        # try:
        #     os.remove(sra_path)
        # except OSError:
        #     pass

def main():
    parser = argparse.ArgumentParser(description="SRRConvert: Downloads SRA files and converts to FASTQ.")
    parser.add_argument("--base_dir", required=True, help="Base output directory (where GSE folders exist)")
    parser.add_argument("--gse_list", nargs="+", help="List of GSE IDs to process (optional)")
    parser.add_argument("--paired", action='store_true', help="If provided, treat runs as paired-end by default")
    args = parser.parse_args()

    # Debug logging for arguments
    log_message(f"Arguments received: base_dir={args.base_dir}, gse_list={args.gse_list}, paired={args.paired}", "DEBUG")

    # If a GSE list was not provided, read from a default file (optional)
    if not args.gse_list:
        default_gse_file = os.path.join(args.base_dir, "geo_accessions.txt")
        log_message(f"No GSE list provided; reading from {default_gse_file}", "DEBUG")
        if not os.path.isfile(default_gse_file):
            log_message(f"Could not find default GSE list file: {default_gse_file}", "ERROR")
            sys.exit(1)
        with open(default_gse_file, "r") as f:
            args.gse_list = [line.strip() for line in f if line.strip()]

    for gse_id in args.gse_list:
        if not gse_id:
            continue
        log_message(f"Processing GSE: {gse_id}", "INFO")

        # -- ADJUSTMENT: Instead of run_ids_<GSE_ID>.txt, we read from <GSE_ID>_SRR.csv
        # Example: GSE113046_SRR.csv
        # Adjust if your CSV has more columns or a different format.
        csv_file = os.path.join(args.base_dir, f"{gse_id}_SRR.csv")
        if not os.path.isfile(csv_file):
            log_message(f"Missing run ID CSV for {gse_id}: {csv_file}", level="ERROR")
            continue

        # We'll parse the CSV, assuming a header on the first line and run IDs in subsequent lines
        run_ids = []
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                # If your CSV has columns with a header named "Run", use DictReader:
                # reader = csv.DictReader(f)
                # for row in reader:
                #     if "Run" in row:
                #         run_ids.append(row["Run"])
                
                # If it's a single-column CSV with a header line, skip the header
                # and read each subsequent line as an SRR ID:
                next(f)  # Skip header row
                for line in f:
                    line = line.strip()
                    if line:
                        run_ids.append(line)
        except Exception as e:
            log_message(f"Error reading CSV {csv_file}: {e}", level="ERROR")
            continue

        log_message(f"Found {len(run_ids)} run IDs for {gse_id}: {run_ids}", "DEBUG")

        # Create a runinfo_dict to track single/paired, defaulting to SINGLE if not forced:
        runinfo_dict = {}
        default_layout = "PAIRED" if args.paired else "SINGLE"
        for rid in run_ids:
            runinfo_dict[rid] = default_layout

        # Download SRA
        log_message(f"Downloading SRA files for GSE: {gse_id}", "INFO")
        download_sra_files(run_ids, args.base_dir, gse_id)

        # Convert to FASTQ
        log_message(f"Converting SRA to FASTQ for GSE: {gse_id}", "INFO")
        convert_sra_to_fastq(run_ids, args.base_dir, gse_id, runinfo_dict)

        log_message(f"Finished processing GSE: {gse_id}\n", "INFO")

if __name__ == "__main__":
    main()
