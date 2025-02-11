import os

import logging

import subprocess

import requests

import time

from multiprocessing import BoundedSemaphore



# Semaphore to limit concurrent requests

global_request_semaphore = BoundedSemaphore(3)  # Limit to 3 concurrent requests



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



def fetch_numeric_id(accession, email="your_email@example.com", tool="FetchOmics", max_retries=10, delay=5):

    params = {

        "db": "gds",

        "term": f"{accession}[Accession]",

        "retmode": "json",

        "email": email,

        "tool": tool

    }



    for attempt in range(1, max_retries + 1):

        try:

            with global_request_semaphore:  # Limit concurrent requests

                response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)

            

            # Check for rate-limiting response (HTTP 429)

            if response.status_code == 429:

                retry_after = int(response.headers.get("Retry-After", delay))

                log_message(f"Rate limit exceeded (Attempt {attempt}). Retrying in {retry_after} seconds...")

                time.sleep(retry_after)

                continue



            response.raise_for_status()

            data = response.json()

            id_list = data.get("esearchresult", {}).get("idlist", [])

            if id_list:

                log_message(f"Accession: {accession}, First GDS ID: {id_list[0]}")

                time.sleep(0.34)  # Ensure at most 3 requests per second

                return id_list[0]

            else:

                log_message(f"Accession: {accession}, No GDS ID found.", level="WARNING")

                return None

        except requests.exceptions.RequestException as e:

            log_message(f"Attempt {attempt}: Error fetching numeric ID for {accession}: {e}", level="WARNING")

            if attempt < max_retries:

                backoff_time = delay * (2 ** (attempt - 1))

                log_message(f"Retrying in {backoff_time} seconds...")

                time.sleep(backoff_time)

            else:

                log_message(f"Max retries reached for {accession}.", level="ERROR")

                return None



def fetch_runinfo(gds_id, output_dir, max_retries=10, delay=5):

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{gds_id}_SRA_RunInfo.csv")



    command = (

        f"elink -db gds -id {gds_id} -target sra | "

        f"efetch -format runinfo > {output_file}"

    )



    for attempt in range(1, max_retries + 1):

        try:

            with global_request_semaphore:  # Limit concurrent requests

                result = subprocess.run(command, shell=True, check=True, text=True)



            log_message(f"RunInfo for GDS ID {gds_id} saved to {output_file}")

            time.sleep(0.34)  # Ensure at most 3 requests per second

            return output_file

        except subprocess.CalledProcessError as e:

            log_message(f"Attempt {attempt}: Error fetching RunInfo for GDS ID {gds_id}: {e}", level="WARNING")

            if attempt < max_retries:

                backoff_time = delay * (2 ** (attempt - 1))

                log_message(f"Retrying in {backoff_time} seconds...")

                time.sleep(backoff_time)

            else:

                log_message(f"Max retries reached for GDS ID {gds_id}.", level="ERROR")

                return None


