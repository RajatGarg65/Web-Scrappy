import json
import re

def filter_links(input_file, output_file):
    """
    Filters links from a JSON file based on specific keywords and saves them to a new JSON file.

    Args:
        input_file (str): Path to the input JSON file containing links.
        output_file (str): Path to the output JSON file where filtered links will be saved.

    Returns:
        None
    """

    # Read the input JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
    # Define the regex pattern for matching relevant keywords in links
    
    pattern = re.compile(r'press|news|newsPage|news-releases|newsroom|press-release|information|update|updates|news-research|press-room|results|media|releases|insights|statements|publications|reports|announcements|headlines|bulletin|communique|briefing|digest|gazette|journal|dispatch|news-feed|live-feed|breaking|newsletter', re.IGNORECASE)

    filtered_links = set()
    
    def filter_and_add(link):
        """
        Checks if a link matches the pattern and adds it to the set if it does.

        Args:
            link (str): The link to be checked and potentially added.

        Returns:
            None
        """
        if pattern.search(link):
            filtered_links.add(link)

    # If the data is a dictionary (as in your pagination_links.json)
    if isinstance(data, dict):
        for key, value in data.items():
            filter_and_add(key)  # Filter and add the key (URL)
            if isinstance(value, dict):
                for link in value.get('pagination_links', []):
                    filter_and_add(link)  # Filter and add pagination links
    
    # If the data is already a list (as in your current filtered_pagination_links.json)
    elif isinstance(data, list):
        for link in data:
            filter_and_add(link)
    
    # Convert the set to a sorted list
    filtered_links = sorted(filtered_links)
    
    # Write the filtered links to a new JSON file
    with open(output_file, 'w') as f:
        json.dump(filtered_links, f, indent=2)

    print(f"Filtered links saved to {output_file}")