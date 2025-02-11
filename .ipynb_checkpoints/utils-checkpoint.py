#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import logging
import subprocess
import requests
import time

def log_message(message, level="INFO"):
    levels = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.log(levels.get(level, logging.INFO), message)

def create_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception as e:
        log_message(f"Error creating directory {path}: {e}", level="ERROR")
        return None

def fetch_numeric_id(accession, email="your_email@example.com", tool="FetchOmics", max_retries=5, delay=5):
    params = {
        "db": "gds",
        "term": f"{accession}[Accession]",
        "retmode": "json",
        "email": email,
        "tool": tool
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
            response.raise_for_status()
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if id_list:
                log_message(f"Accession: {accession}, First GDS ID: {id_list[0]}")
                return id_list[0]
            else:
                log_message(f"Accession: {accession}, No GDS ID found.", level="WARNING")
                return None
        except requests.exceptions.RequestException as e:
            log_message(f"Attempt {attempt}: Error fetching numeric ID for {accession}: {e}", level="WARNING")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                log_message(f"Max retries reached for {accession}.", level="ERROR")
                return None

def fetch_runinfo(gds_id, output_dir, max_retries=5, delay=5):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{gds_id}_SRA_RunInfo.csv")

    command = (
        f"elink -db gds -id {gds_id} -target sra | "
        f"efetch -format runinfo > {output_file}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            subprocess.run(command, shell=True, check=True, text=True)
            log_message(f"RunInfo for GDS ID {gds_id} saved to {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            log_message(f"Attempt {attempt}: Error fetching RunInfo for GDS ID {gds_id}: {e}", level="WARNING")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                log_message(f"Max retries reached for GDS ID {gds_id}.", level="ERROR")
                return None

