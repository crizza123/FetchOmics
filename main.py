import os

import pandas as pd

from GeoDataset import GeoDataset

from SRRDownload import SRRDownload

from SRRConvert import SRRConvert

from utils import log_message



def main(geo_accessions_file, base_dir="output", summary_csv="metadata_summary.csv"):

    """

    Main function to process GEO accessions, download SRRs, and convert them to FASTQ.

    """

    log_message("Starting GEO dataset processing pipeline.")



    # Read GEO accessions from file

    with open(geo_accessions_file, "r") as f:

        geo_accessions = [line.strip() for line in f if line.strip()]

    

    # Initialize GeoDataset

    geo_dataset = GeoDataset(geo_accessions)

    geo_results = geo_dataset.process_all(base_dir, summary_csv)

    

    # Initialize SRRDownload

    srr_downloader = SRRDownload()

    

    for result in geo_results:

        accession = result["accession"]

        geo_dir = result["geo_directory"]

        gds_id = result["gds_id"]

        

        if not gds_id:

            log_message(f"Skipping {accession} due to missing GDS ID.", level="WARNING")

            continue

        

        srr_csv_path = os.path.join(geo_dir, "SRR.csv")

        runinfo_path = os.path.join(geo_dir, f"{gds_id}_SRA_RunInfo.csv")

        

        if not os.path.exists(srr_csv_path) or not os.path.exists(runinfo_path):

            log_message(f"Skipping {accession}, missing required files.", level="WARNING")

            continue

        

        # Read SRR IDs and library layout

        try:

            srr_df = pd.read_csv(srr_csv_path)

            srr_ids = srr_df["Run"].tolist()

            runinfo_df = pd.read_csv(runinfo_path)

            layout_map = {row["Run"]: row.get("LibraryLayout", "SINGLE") for _, row in runinfo_df.iterrows() if "Run" in row}

        except Exception as e:

            log_message(f"Error reading metadata for {accession}: {e}", level="ERROR")

            continue

        

        # Download SRRs

        srr_downloader.download_srrs(srr_ids, geo_dir)

    

    # Convert SRRs to FASTQ

    srr_converter = SRRConvert()

    for result in geo_results:

        accession = result["accession"]

        geo_dir = result["geo_directory"]

        gds_id = result["gds_id"]

        

        if not gds_id:

            continue

        

        runinfo_path = os.path.join(geo_dir, f"{gds_id}_SRA_RunInfo.csv")

        if not os.path.exists(runinfo_path):

            continue

        

        try:

            runinfo_df = pd.read_csv(runinfo_path)

            layout_map = {row["Run"]: row.get("LibraryLayout", "SINGLE") for _, row in runinfo_df.iterrows() if "Run" in row}

        except Exception as e:

            log_message(f"Error reading runinfo for {accession}: {e}", level="ERROR")

            continue

        

        srr_converter.convert_srr_to_fastq(srr_ids, geo_dir, layout_map)

    

    log_message("Finished GEO dataset processing pipeline.")



if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print("Usage: python main.py <geo_accessions_file>")

        sys.exit(1)

    

    geo_accessions_file = sys.argv[1]

    main(geo_accessions_file)


