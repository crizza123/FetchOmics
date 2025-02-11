#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import pandas as pd
import subprocess
from utils import log_message, create_directory


class SRRProcessor:
    def __init__(self):
        """
        Initialize the SRRProcessor.

        Assumes that `prefetch` and `fasterq-dump` are available in the global PATH.
        """
        pass  # No need for paths if tools are globally accessible

    def process_srrs_in_geo_dirs(self, geo_results):
        """
        Process SRRs dynamically from the `geo_dir` paths created by GeoDataset.

        Args:
            geo_results (list): The results list from GeoDataset's `process_all` method.

        Returns:
            None
        """
        for result in geo_results:
            accession = result["accession"]
            geo_dir = result["geo_directory"]
            srr_csv_path = os.path.join(geo_dir, "SRR.csv")
            runinfo_path = os.path.join(geo_dir, "SRA_RunInfo.csv")

            # Check if SRR.csv exists in the GEO directory
            if not os.path.exists(srr_csv_path):
                log_message(f"SRR.csv not found in {geo_dir}. Skipping {accession}.", level="WARNING")
                continue

            # Check if RunInfo.csv exists
            if not os.path.exists(runinfo_path):
                log_message(f"RunInfo.csv not found in {geo_dir}. Skipping {accession}.", level="WARNING")
                continue

            # Read SRRs from SRR.csv
            try:
                srr_df = pd.read_csv(srr_csv_path)
                srr_ids = srr_df["Run"].tolist()
                if not srr_ids:
                    log_message(f"No SRRs found in {srr_csv_path}. Skipping {accession}.", level="WARNING")
                    continue
            except Exception as e:
                log_message(f"Error reading {srr_csv_path}: {e}", level="ERROR")
                continue

            # Read LibraryLayout from RunInfo.csv
            try:
                runinfo_df = pd.read_csv(runinfo_path)
                layout_map = {
                    row["Run"]: row["LibraryLayout"] if "LibraryLayout" in row else "SINGLE"
                    for _, row in runinfo_df.iterrows()
                }
            except Exception as e:
                log_message(f"Error reading {runinfo_path}: {e}", level="ERROR")
                continue

            # Process SRRs
            self._process_srr_list(srr_ids, geo_dir, layout_map)

    def _process_srr_list(self, srr_ids, geo_dir, layout_map):
        """
        Helper method to process a list of SRR IDs.

        Args:
            srr_ids (list): List of SRR IDs to process.
            geo_dir (str): Base GEO directory where SRR subdirectories will be created.
            layout_map (dict): Mapping of SRR IDs to LibraryLayout (PAIRED or SINGLE).

        Returns:
            None
        """
        for srr_id in srr_ids:
            log_message(f"Processing SRR: {srr_id}")

            # Create a subdirectory for each SRR within the GEO directory
            srr_output_dir = create_directory(os.path.join(geo_dir, f"{srr_id}_Fastq"))

            try:
                # Step 1: Prefetch the SRR file
                log_message(f"Fetching SRR {srr_id}...")
                prefetch_command = ["prefetch", srr_id, "-O", srr_output_dir]
                subprocess.run(prefetch_command, check=True, text=True)
                log_message(f"Successfully fetched {srr_id}.")

                # Step 2: Convert to FASTQ format
                log_message(f"Converting {srr_id} to FASTQ...")
                sra_file = os.path.join(srr_output_dir, f"{srr_id}.sra")
                fasterq_command = ["fasterq-dump", "--split-files", sra_file, "-O", srr_output_dir]
                subprocess.run(fasterq_command, check=True, text=True)

                # Handle paired-end vs single-end naming
                layout = layout_map.get(srr_id, "SINGLE").upper()
                if layout == "PAIRED":
                    log_message(f"Detected PAIRED layout for {srr_id}.")
                    # Files remain `_1.fastq` and `_2.fastq`
                else:
                    log_message(f"Detected SINGLE layout for {srr_id}.")
                    single_fastq = os.path.join(srr_output_dir, f"{srr_id}_1.fastq")
                    if os.path.exists(single_fastq):
                        os.rename(single_fastq, os.path.join(srr_output_dir, f"{srr_id}.fastq"))

                # Step 3: Clean up the SRA file (optional)
                if os.path.exists(sra_file):
                    os.remove(sra_file)
                    log_message(f"Deleted SRA file for {srr_id}.")

            except subprocess.CalledProcessError as e:
                log_message(f"Error processing {srr_id}: {e}", level="ERROR")
                continue

        log_message(f"Finished processing SRRs in {geo_dir}.")

