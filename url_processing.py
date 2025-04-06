from logging_config import logger
import time
from tqdm import tqdm
import json
import os
from api_operations import run_groq_api
from excel_operations import update_excel, remove_row_from_excel
from file_operations import scrape_pagination, save_to_json, filter_links, read_pagination_info, run_scrapy_command

updated_rows_count = 0 
def process_url(row):
    """
    Process a single URL by scraping and updating results in Excel.
    
    Args:
        row (dict): Dictionary containing the URL to process.
        
    Returns:
        tuple: (start_url, website_time, success), where success is a boolean indicating if processing was successful.
    """
    start_url = row['parent_url']
    try:
        # Process the URL and measure the time taken

        website_time = main(start_url)
        if website_time is not None:
            logger.info(f"Processed {start_url} in {website_time:.2f} seconds")
            return start_url, website_time, True
        else:
            logger.info(f"Skipped {start_url} - already processed")
            return start_url, 0, False
    except Exception as e:
        logger.error(f"Error processing {start_url}: {e}")
        return start_url, 0, False


    
def process_groq_result(item, groq_result, start_url, all_urls, results, pagination_info):
    """
    Process the result from the Groq API and update the Excel file.
    
    Args:
        item (dict): Dictionary containing URL and content.
        groq_result (str): Result from Groq API.
        start_url (str): The initial URL being processed.
        all_urls (list): List of all URLs scraped.
        results (list): List to store the results.
        pagination_info (dict): Pagination information dictionary.
        
    Returns:
        bool: True if processing was successful, False otherwise.
    """

    if groq_result and "NO PRESS RELEASE".upper() not in groq_result.upper():
        # Append result to results list

        results.append({'url': item['url'], 'groq_result': groq_result})
        pagination_parent_url = next(iter(pagination_info.keys()), '')
        page_info = pagination_info.get(pagination_parent_url, {})
        # Prepare the row data for Excel

        excel_row = [
            len(results),
            start_url,
            json.dumps(all_urls),
            item['url'],
            json.dumps(groq_result),
            pagination_parent_url,
            json.dumps(page_info.get('pagination_links', [])),
            page_info.get('page_count', '')
        ]
        
        try:
            update_excel(start_url, excel_row, pagination_info)

        except Exception as e:
            logger.error(f"Error updating Excel for URL {item['url']}: {e}")

        return True
    else:
        logger.info(f"No press release content found for {item['url']}. Removing from Excel if exists.")
        try:
            remove_row_from_excel(start_url, item['url'])
        except Exception as e:
            logger.error(f"Error removing row from Excel for URL {item['url']}: {e}")
        return False

def main(start_url):
    """
    Main function to handle the URL processing workflow.
    
    Args:
        start_url (str): The initial URL to process.
        
    Returns:
        float: The total time taken for processing the URL.
    """
    # Clear the cache for read_pagination_info
    read_pagination_info.cache_clear()
    start_time = time.time()
    # Setup directories for output

    base_dir = os.getcwd()
    output_dir_name = start_url.split('/')[-1] or "default_directory"
    output_dir = os.path.join(base_dir, "outputs", output_dir_name)
    # Skip processing if the output directory already exists

    if os.path.exists(output_dir):
        logger.info(f"Skipping {start_url} - output directory already exists")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    # Scrape pagination and save extracted URLs

    all_urls = scrape_pagination(start_url)
    extracted_urls_file = os.path.join(output_dir, 'extracted_urls.json')
    save_to_json(all_urls, extracted_urls_file)
    # Filter links and run Scrapy command


    filtered_links_file = os.path.join(output_dir, 'filtered_links.json')
    filter_links(extracted_urls_file, filtered_links_file)

    scrapy_project_dir = os.path.join(base_dir, 'website_content_scraper')
    output_json_path = os.path.join(base_dir, output_dir, 'scraped_content.json')
    
    run_scrapy_command(base_dir, scrapy_project_dir, filtered_links_file, output_json_path, output_dir)
    # Read and update pagination info

    pagination_info_path = os.path.join(output_dir, 'pagination_info.json')
    pagination_info = read_pagination_info(pagination_info_path)
    existing_pagination_info = read_pagination_info(pagination_info_path)

    if pagination_info != existing_pagination_info:
        with open(pagination_info_path, 'w') as f:
            json.dump(pagination_info, f)
        logger.info(f"Updated pagination info written to {pagination_info_path}")
    else:
        logger.info(f"Pagination info unchanged, skipping write operation")

    filtered_pagination_links = os.path.join(output_dir, 'filtered_pagination_links.json')
    filter_links(pagination_info_path, filtered_pagination_links)
    # Load and process scraped data

    try:
        with open(output_json_path, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"No data file found at {output_json_path}")
        return

    results = []

    total_items = len(scraped_data)
    for index, item in enumerate(tqdm(scraped_data, desc="Processing with Groq API"), 1):
        try:
            logger.info(f"Processing item {index} of {total_items}: Sending URL to Groq API: {item['url']}")
            
            try:
                groq_result = run_groq_api(item['content'], item['url'])
                process_groq_result(item, groq_result, start_url, all_urls, results, pagination_info)
                # The retry decorator will handle retries
            except Exception as e:
                logger.error(f"Error processing content from {item['url']}: {e}")
                print("Exception just after Groq API call:", e)
                tqdm.write(f"Error processing content from {item['url']}: {e}")
            
            logger.info(f"Processed {index} out of {total_items} items")
            
        except Exception as e:
            logger.error(f"Unexpected error processing {item['url']}: {e}")
            tqdm.write(f"Unexpected error processing {item['url']}: {e}")
    # Save final results

    final_results_path = os.path.join(output_dir, 'final_results.json')
    with open(final_results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    total_time = end_time - start_time
    return total_time