import json
import os
from logging_config import logger
import subprocess
from extract_links import scrape_pagination, save_to_json
from filter_links import filter_links
from functools import lru_cache

@lru_cache(maxsize=32)
def read_pagination_info(file_path):
    """
    Reads pagination information from a JSON file and caches the result.

    Args:
        file_path (str): Path to the JSON file containing pagination info.

    Returns:
        dict: Parsed pagination information or an empty dictionary if an error occurs.
    """
    try:
        with open(file_path, 'r') as f:
            info = json.load(f)
        logger.info(f"Successfully read pagination info from {file_path}")
        return info
    except FileNotFoundError:
        logger.warning(f"Pagination info file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error reading pagination info: {e}")
        return {}

def run_scrapy_command(base_dir, scrapy_project_dir, filtered_links_file, output_json_path, output_dir):
    """
    Runs a Scrapy command to crawl content using the Scrapy framework.

    Args:
        base_dir (str): The base directory to return to after running the command.
        scrapy_project_dir (str): Directory of the Scrapy project.
        filtered_links_file (str): Path to the input file containing filtered links for scraping.
        output_json_path (str): Path where the output JSON data will be saved.
        output_dir (str): Directory for Scrapy to store output files.

    Returns:
        None
    """
    # Change the current working directory to the Scrapy project directory
    os.chdir(scrapy_project_dir)
    # Define the Scrapy command to be executed

    scrapy_command = [
        'scrapy', 'crawl', 'content_spider',
        '-a', f'input_file={filtered_links_file}',
        '-o', output_json_path,
        '-s', f'OUTPUT_DIR={output_dir}'
    ]
    # Run the Scrapy command and suppress output

    subprocess.run(scrapy_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Return to the base directory

    os.chdir(base_dir)