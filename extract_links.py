from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time

def scrape_pagination(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    urls = set()  # Use a set to avoid duplicates
    page_number = 1
    
    while True:
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # Scroll to load any lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for potential lazy-loaded content
        
        # Extract content
        elements = driver.find_elements(By.XPATH, "//a[@href]")
        new_urls = [element.get_attribute('href') for element in elements if element.get_attribute('href')]
        urls.update(new_urls)  # Add new URLs to the set
        
        try:
            # Try to find the next page button
            next_page = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Next') or contains(@class, 'next')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", next_page)
            next_page.click()
            time.sleep(2)  # Wait for the page to load
            page_number += 1
        except (TimeoutException, NoSuchElementException):
            print("No more pages or reached the end")
            break

    driver.quit()
    return list(urls)  # Convert set back to list

def save_to_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.common.action_chains import ActionChains
# import json
# import time
# import re

# def scrape_pagination(url):
#     """
#     Scrapes a web page for URLs and pagination links.

#     Args:
#         url (str): The URL of the web page to scrape.

#     Returns:
#         list: A list of unique URLs extracted from the page.
#     """
#     # Set up Chrome options for headless mode
#     options = webdriver.ChromeOptions()
#     options.add_argument('--headless')
#     driver = webdriver.Chrome(options=options)
#     driver.get(url)
    
#     urls = set()
    
#     def extract_links():
#         """
#         Extracts all potential URLs from the page, including href, onclick, class attributes, 
#         data attributes, and script content.
#         """
#         try:
#             # Extract visible links
#             elements = driver.find_elements(By.XPATH, "//*[@href or @onclick or contains(@class, 'link') or contains(@class, 'btn')]")
#             for element in elements:
#                 # Check href attribute
#                 href = element.get_attribute('href')
#                 if isinstance(href, str) and href.startswith('http'):
#                     urls.add(href)
                
#                 # Check onclick attribute
#                 onclick = element.get_attribute('onclick')
#                 if onclick:
#                     potential_urls = re.findall(r'https?://[^\s\'"]+', onclick)
#                     urls.update(potential_urls)
                
#                 # Check class attribute for potential links
#                 class_attr = element.get_attribute('class')
#                 if class_attr:
#                     potential_urls = re.findall(r'https?://[^\s\'"]+', class_attr)
#                     urls.update(potential_urls)
                
#                 # Check data attributes for potential links
#                 for attr in element.get_property('attributes'):
#                     if attr['name'].startswith('data-'):
#                         potential_urls = re.findall(r'https?://[^\s\'"]+', attr['value'])
#                         urls.update(potential_urls)

#             # Extract links from script tags
#             script_tags = driver.find_elements(By.TAG_NAME, 'script')
#             for script in script_tags:
#                 script_content = script.get_attribute('innerHTML')
#                 potential_urls = re.findall(r'https?://[^\s\'"]+', script_content)
#                 urls.update(potential_urls)

#         # Perform initial extraction of links

    
#         except Exception as e:
#             print(f"Error in extract_links: {str(e)}")
#         extract_links()

#         # Scroll down to load additional content and extract links

#         last_height = driver.execute_script("return document.body.scrollHeight")
#         while True:
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             time.sleep(2)
#             new_height = driver.execute_script("return document.body.scrollHeight")
#             if new_height == last_height:
#                 break
#             last_height = new_height
#             extract_links()

#         # Click on elements that might reveal more links
#         clickable_elements = driver.find_elements(By.XPATH, "//button | //a[contains(@class, 'button') or contains(@class, 'btn')]")
#         for element in clickable_elements:
#             try:
#                 ActionChains(driver).move_to_element(element).click().perform()
#                 time.sleep(1)
#                 extract_links()
#             except:
#                 pass  # If click fails, just continue

#         driver.quit()
#         return list(urls)
        

# def save_to_json(data, filename):
#     """
#     Saves the given data to a JSON file.

#     Args:
#         data (dict/list): The data to save to the file.
#         filename (str): The path to the output JSON file.

#     Returns:
#         None
#     """
#     with open(filename, 'w') as file:
#         json.dump(data, file, indent=4)

