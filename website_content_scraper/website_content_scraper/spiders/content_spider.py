import scrapy
import re
import json
from urllib.parse import urlparse, urljoin
from datetime import datetime
import logging
import os

class ContentSpider(scrapy.Spider):
    name = 'content_spider'
    custom_settings = {
        'USER_AGENT': 'YourBot/0.1 (+http://www.yourdomain.com)',
        'LOG_LEVEL': logging.INFO,
        'CLOSESPIDER_TIMEOUT': 3600,  # Close the spider after 1 hour
    }
    def __init__(self, input_file=None, *args, **kwargs):
        """
        Initialize the ContentSpider class.
        :param input_file: Path to the file containing the URLs to scrape.
        """
        super(ContentSpider, self).__init__(*args, **kwargs)
        self.input_file = input_file
        self.allowed_domains = []
        self.visited_urls = set()
        self.keywords = [
            'press release', 'new', 'newsroom', 'newsPage', 'press-release', 'press', 'press room', 
            'news', 'news-release', 'announcement', 'update', 'updates', 'news-research', 
            'press-room', 'results', 'media', 'releases', 'insights', 'statements', 'publications', 
            'reports', 'announcements', 'headlines', 'bulletin', 'communique', 'briefing', 
            'digest', 'gazette', 'journal', 'dispatch', 'news-feed', 'live-feed', 'breaking', 
            'newsletter'
        ]
        self.url_pattern = re.compile(r'(press|news|newsPage|news-releases|newsroom|press-release|announcement|update|updates|news-research|press-room|results|media|releases|insights|statements|publications|reports|announcements|headlines|bulletin|communique|briefing|digest|gazette|journal|dispatch|news-feed|live-feed|breaking|newsletter)[a-zA-Z0-9-\/]+\/?$', re.IGNORECASE)

        self.exclude_pattern = re.compile(r'contact', re.IGNORECASE)
        self.pagination_handler_calls = 0
        self.parent_url = None
        self.pagination_info = {}
        self.pagination_links = set()  # Add this line


    def start_requests(self):
        """
        Read the input file containing URLs and initiate requests to those URLs.
        """
        # Read the filtered URLs from the input_file
        if not self.input_file:
            self.logger.error('No input file provided')
            return

        try:
            with open(self.input_file, 'r') as f:
                urls = json.load(f)
        except Exception as e:
            self.logger.error(f'Error reading input file: {e}')
            return

        for url in urls:
            # Extract the domain from each URL and add it to allowed_domains
            domain = urlparse(url).netloc
            if domain not in self.allowed_domains:
                self.allowed_domains.append(domain)
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                self.parent_url = url  # Store the parent URL
                yield scrapy.Request(url=url, callback=self.parse, meta={'parent_url': url})

    def parse(self, response):
        """
        Handle the response for each request, extract content, and handle pagination.
        :param response: The response object containing the page content.
        """
        
        content_data = {}

        for heading in response.xpath('//h1|//h2|//h3|//h4|//h5|//h6'):
            heading_text = heading.xpath('normalize-space(.)').get()
            link = heading.xpath('.//a/@href').extract_first()
            # Resolve the link to a full URL
            if link:
                link = response.urljoin(link) 
            
            # Append heading and link if exists
            content_data[heading_text] = link if link else "No link provided"

        # XPath Selection: Selects all text nodes within the body, excluding text within script and style tags.
        # Extract Text Nodes: Extracts the text content of the selected nodes.
        # Clean Text: Cleans the extracted text by:
        # Stripping extra whitespace.
        # Joining the text nodes into a single string with spaces normalized.

        # Extract general body content without headings
        text_nodes = response.xpath('//body//*[not(self::script or self::style)]//text()').extract()
        cleaned_text = ' '.join([re.sub('\s+', ' ', t.strip()) for t in text_nodes if t.strip()])

        #Filter Content: Calls the filter_content method to further clean the text by removing content that looks like script or style data.

        # Filter out content that looks like script/style data
        cleaned_text = self.filter_content(cleaned_text)

        #Yield Data: Creates a dictionary containing the URL of the page, the extracted headings and their links, and the cleaned body content. This dictionary is then yielded, making it available for further processing or storage.

        yield {
            'url': response.url,
            'headings': content_data,
            'content': cleaned_text
        }

        # CSS Selection: Selects all links (href attributes) on the page.
        # Join Links: Converts relative links to absolute URLs.
        # Filter Links: Checks if the link matches the criteria defined in the should_visit_url method and if it has not been visited before.
        # Add to Visited: Adds the link to the set of visited URLs.
        # Yield Request: Yields a new scrapy.Request for the link, with self.parse as the callback method to process the response.

        # Follow links that match the press release criteria and are within the allowed domains
        for href in response.css('a::attr(href)').extract():
            url = response.urljoin(href)
            if self.should_visit_url(url) and url not in self.visited_urls:
                self.visited_urls.add(url)
                yield scrapy.Request(url, callback=self.parse)
        # Regex Selection: Uses a regular expression to find all URLs in the cleaned body content.
        # Filter Links: Checks if the link matches the criteria and has not been visited.
        # Add to Visited: Adds the link to the set of visited URLs.
        # Yield Request: Yields a new scrapy.Request for the link, with self.parse as the callback method.


        # Extract and follow links from the content itself
        for link in re.findall(r'https?://\S+', cleaned_text):
            if self.should_visit_url(link) and link not in self.visited_urls:
                self.visited_urls.add(link)
                yield scrapy.Request(link, callback=self.parse)
        self.logger.info("About to call handle_pagination")

        pagination_request = self.handle_pagination(response)
        if pagination_request:
            yield pagination_request
        self.logger.info("Finished handle_pagination")



        # Extract links from card elements
        self.extract_links_from_cards(response)
        
    def should_visit_url(self, url):
        """
        Determine if a URL should be visited based on allowed domains and criteria.
        :param url: The URL to check.
        :return: True if the URL should be visited, False otherwise.
        """
        # Check if URL is in allowed domains
        if urlparse(url).netloc not in self.allowed_domains:
            return False
        # Check if URL contains any of the keywords or matches the specific pattern
        if any(keyword in url.lower() for keyword in self.keywords):
            return True
        if self.url_pattern.search(url) and not self.exclude_pattern.search(url):
            return True
        
        return False

    def filter_content(self, content):
        """
        Remove common script/style content and unwanted tags from the content.
        :param content: The content to clean.
        :return: The cleaned content.
        """
        # Remove common script/style content
        patterns_to_remove = [
            r'//<!\[CDATA\[.*?\]\]>',
            r'var .*?;',
            r'function .*?\}',
            r'\(function.*?\);',
            r'formalyze.*?;',
            r'<!--.*?-->',
            r'<.*?>'
        ]
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        return content.strip()

    def handle_pagination(self, response):
        """
        Handle pagination links on the page and yield requests for next/previous pages.
        :param response: The response object containing the page content.
        :return: A Scrapy Request for the next page if available, otherwise None.
        """

        self.pagination_handler_calls += 1
        self.logger.info(f'Handling pagination for {response.url}')
        
        parent_url = response.meta.get('parent_url', self.parent_url)
        if parent_url not in self.pagination_info:
            self.pagination_info[parent_url] = {
                'pagination_links': set(),
                'page_count': 0
            }
        
        self.pagination_info[parent_url]['pagination_links'].add(response.url)
        self.pagination_info[parent_url]['page_count'] += 1
        # Write pagination info to file immediately
        self.write_pagination_info()
        next_page = response.css('a.next::attr(href), a[rel="next"]::attr(href), a[aria-label="Next"]::attr(href)').extract_first()
        prev_page = response.css('a.prev::attr(href), a[rel="prev"]::attr(href), a[aria-label="Previous"]::attr(href)').extract_first()
        self.logger.info(f'Next page: {next_page}')
        self.logger.info(f'Previous page: {prev_page}')

        if next_page:
            next_page = response.urljoin(next_page)
            self.pagination_info[parent_url]['pagination_links'].add(next_page)
            if next_page not in self.visited_urls:
                self.visited_urls.add(next_page)
                self.logger.info(f'Queueing next page: {next_page}')
                return scrapy.Request(next_page, callback=self.parse, meta={'parent_url': parent_url})

        if prev_page:
            prev_page = response.urljoin(prev_page)
            self.pagination_info[parent_url]['pagination_links'].add(prev_page)
            if prev_page not in self.visited_urls:
                self.visited_urls.add(prev_page)
                self.logger.info(f'Queueing previous page: {prev_page}')
                return scrapy.Request(prev_page, callback=self.parse, meta={'parent_url': parent_url})

        page_numbers = response.css('a.page-numbers::attr(href), a.page-link::attr(href), li.pagination a::attr(href)').extract()
        for page in page_numbers:
            page = response.urljoin(page)
            self.pagination_info[parent_url]['pagination_links'].add(page)
            if page not in self.visited_urls:
                self.visited_urls.add(page)
                self.logger.info(f'Queueing page number: {page}')
                return scrapy.Request(page, callback=self.parse, meta={'parent_url': parent_url})

        year_dropdowns = response.xpath('//select[contains(@id, "year")]/option/@value').extract()
        for year in year_dropdowns:
            year_page = response.urljoin(year)
            self.pagination_info[parent_url]['pagination_links'].add(year_page)
            if year_page not in self.visited_urls:
                self.visited_urls.add(year_page)
                return scrapy.Request(year_page, callback=self.parse, meta={'parent_url': parent_url})

    def write_pagination_info(self):
        """
        Write the pagination information to a JSON file.
        """
        formatted_pagination_info = {
            parent_url: {
                'pagination_links': list(info['pagination_links']),
                'page_count': info['page_count']
            }
            for parent_url, info in self.pagination_info.items()
        }
        # Use the output_dir passed as a parameter to the spider
        file_path = os.path.join(self.settings.get('OUTPUT_DIR', ''), 'pagination_info.json')
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(formatted_pagination_info, f, indent=2)
            self.logger.info(f'Pagination info updated in {file_path}')
        except Exception as e:
            self.logger.error(f'Error saving pagination info: {e}')


    def closed(self, reason):
        """
        Called when the spider is closed. Save the pagination information to a file.
        :param reason: The reason the spider is closed.
        """
        self.logger.info(f'Spider closed with reason: {reason}. Saving pagination info.')
        
        formatted_pagination_info = {
            parent_url: {
                'pagination_links': list(info['pagination_links']),
                'page_count': info['page_count']
            }
            for parent_url, info in self.pagination_info.items()
        }
        # Save the file in the same directory as the spider
        file_path = os.path.join(os.path.dirname(__file__), 'pagination_info.json')
        
        try:
            with open(file_path, 'w') as f:
                json.dump(formatted_pagination_info, f, indent=2)
            self.logger.info(f'Pagination info saved successfully to {file_path}')
            self.logger.info(f'Pagination info: {formatted_pagination_info}')
        except Exception as e:
            self.logger.error(f'Error saving pagination info: {e}')
        

                
        self.logger.info(f'Pagination info before formatting: {self.pagination_info}')
        self.logger.info(f'Formatted pagination info: {formatted_pagination_info}')
        
        self.logger.info(f'Total pagination parent URLs: {len(self.pagination_info)}')
        self.logger.info(f'Total pagination links: {sum(len(info["pagination_links"]) for info in self.pagination_info.values())}')
        self.logger.info(f'Total pages crawled: {sum(info["page_count"] for info in self.pagination_info.values())}')
        self.logger.info(f'handle_pagination was called {self.pagination_handler_calls} times')



    def extract_links_from_cards(self, response):
        """
        Extract links from card elements on the page and yield requests for those links.
        :param response: The response object containing the page content.
        """
        # Extract links from card elements
        card_links = response.css('div.card a::attr(href), div.news-card a::attr(href), div.press-card a::attr(href)').extract()
        for link in card_links:
            url = response.urljoin(link)
            if self.should_visit_url(url) and url not in self.visited_urls:
                self.visited_urls.add(url)
                yield scrapy.Request(url, callback=self.parse)
