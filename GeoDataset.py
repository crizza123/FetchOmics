# GeoDataset.py



import os

import pandas as pd

from utils import fetch_numeric_id, fetch_runinfo, log_message, create_directory



class GeoDataset:

    def __init__(self, geo_accessions, email="your_email@example.com",

                 tool="FetchOmics", api_key=None):

        if isinstance(geo_accessions, str):

            self.geo_accessions = [geo_accessions]

        elif isinstance(geo_accessions, list):

            self.geo_accessions = geo_accessions

        else:

            raise ValueError("geo_accessions must be a string or a list of strings.")



        self.email = email

        self.tool = tool

        self.api_key = api_key  # store the key

        self.results = []

        self.metadata_summary = []

        self.srr_list = []



    def parse_runinfo(self, runinfo_file, geo_dir):

        try:

            df = pd.read_csv(runinfo_file)

            if df.empty:

                log_message(f"RunInfo file {runinfo_file} is empty.", level="WARNING")

                return None



            species = df["ScientificName"].unique().tolist() if "ScientificName" in df.columns else []

            library_strategy = df["LibraryStrategy"].unique().tolist() if "LibraryStrategy" in df.columns else []

            library_layout = df["LibraryLayout"].unique().tolist() if "LibraryLayout" in df.columns else []

            platform = df["Platform"].unique().tolist() if "Platform" in df.columns else []

            model = df["Model"].unique().tolist() if "Model" in df.columns else []

            runs = df["Run"].tolist() if "Run" in df.columns else []



            srr_file = os.path.join(geo_dir, "SRR.csv")

            srr_df = pd.DataFrame({"Run": runs})

            srr_df.to_csv(srr_file, index=False, header=True)

            log_message(f"SRR list saved to {srr_file}")



            self.srr_list.extend(runs)



            return {

                "species": species,

                "library_strategy": library_strategy,

                "library_layout": library_layout,

                "platform": platform,

                "model": model,

                "runs": runs,

            }

        except Exception as e:

            log_message(f"Error parsing RunInfo file {runinfo_file}: {e}", level="ERROR")

            return None



    def process_single_accession(self, accession, base_dir="output"):

        log_message(f"Processing GEO accession: {accession}")



        geo_dir = create_directory(os.path.join(base_dir, accession))



        # Pass self.api_key into fetch_numeric_id

        gds_id = fetch_numeric_id(accession, email=self.email, tool=self.tool, api_key=self.api_key)

        if not gds_id:

            log_message(f"No GDS ID found for GEO accession: {accession}", level="WARNING")

            return {

                "accession": accession,

                "gds_id": None,

                "geo_directory": geo_dir,

                "metadata": None,

            }



        runinfo_file = fetch_runinfo(gds_id, output_dir=geo_dir)

        if not runinfo_file:

            log_message(f"RunInfo file not found for GEO accession: {accession}", level="ERROR")

            return {

                "accession": accession,

                "gds_id": gds_id,

                "geo_directory": geo_dir,

                "metadata": None,

            }



        metadata = self.parse_runinfo(runinfo_file, geo_dir)

        if metadata:

            for run in metadata["runs"]:

                self.metadata_summary.append({

                    "accession": accession,

                    "gds_id": gds_id,

                    "species": ", ".join(metadata["species"]),

                    "library_strategy": ", ".join(metadata["library_strategy"]),

                    "library_layout": ", ".join(metadata["library_layout"]),

                    "platform": ", ".join(metadata["platform"]),

                    "model": ", ".join(metadata["model"]),

                    "run": run,

                })



        result = {

            "accession": accession,

            "gds_id": gds_id,

            "geo_directory": geo_dir,

            "metadata": metadata,

        }

        log_message(f"Finished processing GEO accession: {accession}")

        return result



    def process_all(self, base_dir="output", summary_csv="metadata_summary.csv"):

        log_message(f"Starting batch processing of {len(self.geo_accessions)} GEO accessions.")

        for accession in self.geo_accessions:

            result = self.process_single_accession(accession, base_dir)

            self.results.append(result)



        if self.metadata_summary:

            summary_df = pd.DataFrame(self.metadata_summary)

            summary_df.to_csv(summary_csv, index=False)

            log_message(f"Metadata summary saved to {summary_csv}")



        log_message("Finished batch processing.")

        return self.results


