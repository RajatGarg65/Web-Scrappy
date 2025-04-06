# Web Scraping Project

This project extracts URLs from a website, filters them, and then scrapes the content of the filtered URLs using Scrapy.

## Project Structure
```
SCRAPPING/
│
├── .venv/
│
├── Pipeline/
│   ├── extract_links.py
│   ├── filter_links.py
│   └── groq_test.py
│
└── website_content_scraper/
    ├── website_content_scraper/
    │   ├── __pycache__/
    │   ├── spiders/
    │   │   ├── __pycache__/
    │   │   ├── __init__.py
    │   │   └── content_spider.py
    │   ├── __init__.py
    │   ├── items.py
    │   ├── middlewares.py
    │   ├── pipelines.py
    │   └── settings.py
    ├── scrapy.cfg
    └── chromedriver.exe

```
## Components

1. **extract_links.py**: This script uses Selenium to extract URLs from the target website and saves the extracted URLs in `extracted_urls.json`.
2. **filter_links.py**: This script filters the extracted URLs based on predefined criteria and saves the filtered URLs in `filtered_links.json`.
3. **website_content_scraper**: This directory contains the Scrapy project for extracting the body content from the filtered URLs. The extracted content is saved in `output.json`.
4. **groq_test.py**: This script is used to get articles or links from the extracted content. The extracted content is used as input for the Groq API or prompt.
5. **main.py**: This script combines all the steps into a single workflow for ease of use.

## Setup

1. **Virtual Environment**: Create and activate a virtual environment to manage dependencies.
   ```sh
   python -m venv .venv
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser --->  Optional
   source .venv/bin/activate    or     .\venv\Scripts\Activate.ps1   # On Windows use `.venv\Scripts\activate`

2. **Install Dependencies**: Install the required Python packages.
    ```
    pip install -r requirements.txt
    ```
 
3. **Run the script** : Replace the path to excel file and run the main.py file
    ```
    python main.py