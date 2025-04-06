
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from excel_operations import read_input_file
from url_processing import process_url
from logging_config import logger
import concurrent.futures


if __name__ == "__main__":
    # Define the input file containing URLs

    input_filename = 'input_urls.xlsx'
    # Read the input file into a DataFrame

    url_df = read_input_file(input_filename)
    # Slice the DataFrame to process a specific range of URLs

    url_df = url_df[1:2].copy() #it means need to read 1st 2 rows
    # Initialize counters

    successful_websites = 0
    processed_websites = 0
    # Check if the DataFrame was successfully read

    if url_df is None:
        logger.error("Failed to read input file. Please check the file format and try again.")
        print("Failed to read input file. Please check the file format and try again.")
    else:
        # Get the total number of websites to process
        total_websites = len(url_df)
        total_time = 0
        successful_websites = 0
        # Use ThreadPoolExecutor to process URLs concurrently
        #you can increase the worker value according to your system
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit tasks to the thread pool

            futures = [executor.submit(process_url, row) for _, row in url_df.iterrows()]
            # Iterate over the completed futures

            for future in tqdm(concurrent.futures.as_completed(futures), total=total_websites, desc="Processing websites"):
                start_url, website_time, success = future.result()
                processed_websites += 1
                remaining_websites = total_websites - processed_websites
                # Update counters and log results

                if success:
                    total_time += website_time
                    successful_websites += 1
                    tqdm.write(f"Processed {start_url} in {website_time:.2f} seconds")
                    logger.info(f"Successfully processed parent URL: {start_url} in {website_time:.2f} seconds")

                else:
                    tqdm.write(f"Skipped or error processing {start_url}")
                # Log progress

                logger.info(f"Progress: {processed_websites}/{total_websites} parent URLs processed. {remaining_websites} remaining.")
                tqdm.write(f"Progress: {processed_websites}/{total_websites} parent URLs processed. {remaining_websites} remaining.")
        # Calculate and log performance metrics

        avg_time = total_time / successful_websites if successful_websites > 0 else 0
        logger.info(f"Total websites processed: {successful_websites}/{total_websites}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Average time per website: {avg_time:.2f} seconds")
        # Print performance metrics

        print(f"\nTotal websites processed: {successful_websites}/{total_websites}")
        print(f"Total processing time: {total_time:.2f} seconds")
        print(f"Average time per website: {avg_time:.2f} seconds")
