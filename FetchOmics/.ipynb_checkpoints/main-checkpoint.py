#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import os
from GeoDataset import GeoDataset
from SRRProcessor import SRRProcessor
from utils import log_message

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <geo_accession_or_file> <base_output_dir> [email] [tool]")
        print("Example: python main.py GSE113046 /path/to/output/directory your_email@example.com FetchOmics")
        print("Example: python main.py geo_accessions.txt /path/to/output/directory your_email@example.com FetchOmics")
        print("\nThis script processes GEO accessions to fetch metadata and convert SRR files into FASTQ files.")
        sys.exit(1)

    geo_input = sys.argv[1]
    base_output_dir = sys.argv[2]

    # Optional arguments
    email = sys.argv[3] if len(sys.argv) > 3 else "your_email@example.com"
    tool = sys.argv[4] if len(sys.argv) > 4 else "FetchOmics"

    # Determine if input is a file or a single accession
    if os.path.exists(geo_input):
        # Input is a file
        try:
            with open(geo_input, "r") as f:
                geo_accessions = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading '{geo_input}': {e}")
            sys.exit(1)

        if not geo_accessions:
            print("Error: No GEO accessions found in the input file. Please provide at least one GEO accession.")
            sys.exit(1)

    else:
        # Input is a single GEO accession
        geo_accessions = [geo_input]

    print(f"Processing the following GEO accessions: {geo_accessions}")
    print(f"Using email: {email}, tool: {tool}")

    geo = GeoDataset(geo_accessions, email=email, tool=tool)

    try:
        geo_results = geo.process_all(base_dir=base_output_dir, summary_csv=os.path.join(base_output_dir, "metadata_summary.csv"))
    except Exception as e:
        log_message(f"An error occurred during GEO accession processing: {e}", level="ERROR")
        sys.exit(1)

    srr_processor = SRRProcessor()

    try:
        log_message("Starting SRR processing...")
        srr_processor.process_srrs_in_geo_dirs(geo_results)
        log_message("SRR processing completed successfully.")
    except Exception as e:
        log_message(f"An error occurred during SRR processing: {e}", level="ERROR")
        sys.exit(1)

    print("FetchOmics processing completed successfully.")

if __name__ == "__main__":
    main()

