#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess

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
        srr_dir = os.path.join(gse_dir, run_id)  # GSExxx/SRRxxx
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

        # Extra debug check
        if not os.path.isfile(sra_path):
            log_message(f"{sra_path} not found after prefetch.", level="WARNING")

def convert_sra_to_fastq(run_ids, base_dir, gse_id, runinfo_dict=None):
    """
    Converts .sra files to FASTQ, detecting SINGLE vs. PAIRED from runinfo_dict if provided.
    Directory structure assumed to be base_dir/GSE_ID/SRR_ID/SRR_ID.sra.

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
        
        # Determine layout
        layout = runinfo_dict.get(run_id, "SINGLE").upper() if runinfo_dict else "SINGLE"
        log_message(f"Detected layout for {run_id}: {layout}", "DEBUG")

        if layout == "PAIRED":
            log_message(f"{run_id}: Paired-end data – FASTQ files split into _1 and _2.")
        else:
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
    parser.add_argument("--base_dir", required=True, help="Base output directory")
    parser.add_argument("--gse_list", nargs="+", help="List of GSE IDs to process (optional)")
    parser.add_argument("--paired", action='store_true', help="If provided, assume runs are paired-end unless stated otherwise")
    args = parser.parse_args()

    # Debug logging for arguments
    log_message(f"Arguments received: base_dir={args.base_dir}, gse_list={args.gse_list}, paired={args.paired}", "DEBUG")

    # If a GSE list was not provided, we might read from a geo_accessions.txt or something else
    # This snippet is an example. Adjust as needed in your environment.
    if not args.gse_list:
        default_gse_file = os.path.join(args.base_dir, "geo_accessions.txt")
        log_message(f"No GSE list provided; reading from {default_gse_file}", "DEBUG")
        if not os.path.isfile(default_gse_file):
            log_message(f"Could not find default GSE list file: {default_gse_file}", "ERROR")
            sys.exit(1)
        with open(default_gse_file, "r") as f:
            args.gse_list = [line.strip() for line in f if line.strip()]

    # Example: for each GSE, read the SRR IDs from a text file
    for gse_id in args.gse_list:
        if not gse_id:
            continue
        log_message(f"Processing GSE: {gse_id}", "INFO")

        # The user might have a file like run_ids_<GSE_ID>.txt
        run_id_file = os.path.join(args.base_dir, f"run_ids_{gse_id}.txt")
        if not os.path.isfile(run_id_file):
            log_message(f"Missing run ID file for {gse_id}: {run_id_file}", level="ERROR")
            continue

        with open(run_id_file, "r") as rf:
            run_ids = [line.strip() for line in rf if line.strip()]

        # For demonstration, create a runinfo_dict to track single/paired
        # If `--paired` is set, we treat all runs as PAIRED.
        # Otherwise, default to SINGLE. Alternatively, you can load an SRA_RunInfo CSV here if needed.
        runinfo_dict = {}
        if args.paired:
            for rid in run_ids:
                runinfo_dict[rid] = "PAIRED"
        else:
            for rid in run_ids:
                runinfo_dict[rid] = "SINGLE"

        # Download the SRA files
        log_message(f"Downloading SRA files for GSE: {gse_id}", "INFO")
        download_sra_files(run_ids, args.base_dir, gse_id)

        # Convert them to FASTQ
        log_message(f"Converting SRA to FASTQ for GSE: {gse_id}", "INFO")
        convert_sra_to_fastq(run_ids, args.base_dir, gse_id, runinfo_dict)

        log_message(f"Finished processing GSE: {gse_id}\n", "INFO")

if __name__ == "__main__":
    main()
