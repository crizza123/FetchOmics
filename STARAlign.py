#!/usr/bin/env python3

import os
import sys
import glob
import subprocess
import argparse

###############################################################################
# STARAlign.py (Updated)
# ----------------------
# Searches for single-end FASTQ files inside the correct base directory and 
# aligns them with STAR.
###############################################################################

# Define STAR genome index and GTF annotation explicitly
GENOME_INDEX = "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCm39"
ANNOTATION_GTF = "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCm39/GRCm39.gtf"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Recursively find FASTQ files and align them with STAR to GRCm39."
    )
    parser.add_argument("--base_dir", required=True,
                        help="Base directory containing GSEXXX subdirectories.")
    parser.add_argument("--gse_list", nargs="+", required=True,
                        help="One or more GSE dataset IDs to process (e.g., GSE106973).")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of CPU threads for STAR (default=1).")
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = os.path.abspath(args.base_dir)  # Ensure absolute path
    gse_list = args.gse_list
    threads = args.threads

    print("==========================================================")
    print(f"[INFO] Base directory: {base_dir}")
    print(f"[INFO] GSE datasets: {', '.join(gse_list)}")
    print(f"[INFO] Using {threads} threads for STAR alignment.")
    print(f"[INFO] Genome index: {GENOME_INDEX}")
    print("==========================================================")

    overall_fail = 0  # track if any alignment fails

    for gse_id in gse_list:
        gse_path = os.path.join(base_dir, gse_id)
        if not os.path.isdir(gse_path):
            print(f"[ERROR] Cannot find dataset directory for {gse_id}: {gse_path}", file=sys.stderr)
            overall_fail += 1
            continue

        print(f"\n[INFO] Processing dataset: {gse_id}")

        # Locate SRR subdirectories
        srr_folders = [
            d for d in os.listdir(gse_path)
            if d.startswith("SRR") and os.path.isdir(os.path.join(gse_path, d))
        ]

        if not srr_folders:
            print(f"[WARNING] No SRR subdirectories found in {gse_path}. Skipping.")
            continue

        for srr_id in sorted(srr_folders):
            srr_dir = os.path.join(gse_path, srr_id)
            print(f"[INFO] Searching for FASTQ files under: {srr_dir}")

            # Recursively search for FASTQ files
            fastq_paths = glob.glob(os.path.join(srr_dir, "**", "*.fastq"), recursive=True)
            fastq_paths += glob.glob(os.path.join(srr_dir, "**", "*.fastq.gz"), recursive=True)
            fastq_paths.sort()

            if len(fastq_paths) == 0:
                print(f"[WARNING] No FASTQ files found for {srr_id}.")
                continue

            print(f"[INFO] Found {len(fastq_paths)} FASTQ file(s). Assuming SINGLE-END layout.")

            # Construct the STAR command
            out_prefix = os.path.join(srr_dir, f"{srr_id}_")
            star_cmd = [
                "STAR",
                f"--runThreadN {threads}",
                f"--genomeDir {GENOME_INDEX}",
                f"--readFilesIn {' '.join(fastq_paths)}",
                f"--outFileNamePrefix {out_prefix}",
                "--outSAMtype BAM Unsorted",
                "--outFilterMultimapNmax 1"
            ]

            # Handle gzipped FASTQ
            if any(fp.endswith(".gz") for fp in fastq_paths):
                star_cmd.append("--readFilesCommand zcat")

            star_cmd_str = " ".join(star_cmd)
            print(f"[DEBUG] STAR command:\n  {star_cmd_str}")

            try:
                subprocess.run(star_cmd_str, shell=True, check=True)
                print(f"[INFO] Alignment complete for {srr_id}. Output at {out_prefix}Aligned.out.bam")
            except subprocess.CalledProcessError as e:
                overall_fail += 1
                print(f"[ERROR] STAR alignment failed for {srr_id}. Exit code {e.returncode}.", file=sys.stderr)

    if overall_fail > 0:
        print("[ERROR] Some alignments failed. Check logs.")
        sys.exit(1)
    else:
        print("[INFO] All alignments completed successfully.")

if __name__ == "__main__":
    main()
