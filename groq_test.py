import os
import re
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logging_config import logger
from key_manager import key_manager

# Custom exception for rate limit issues
class RateLimitException(Exception):
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=30, min=60, max=120),
    retry=retry_if_exception_type(RateLimitException)
)
def run_groq_api(content,url, max_length=6000):
    """
    Sends content to the Groq API to extract and present press release and related content.

    Args:
        content (str): The text content to be processed.
        url (str): The URL associated with the content (used for logging).
        max_length (int): The maximum length of content chunks to be processed by the API.

    Returns:
        str: The processed content after extraction and formatting.

    Raises:
        RateLimitException: If the API rate limit is exceeded.
    """
    try:
        retry_state = run_groq_api.retry.statistics
        attempt_number = retry_state['attempt_number'] if retry_state else 1

        # Get the next available API key

        api_key = key_manager.get_next_key()
        client = Groq(api_key=api_key)
        # Split content into manageable chunks

        parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
        results = []
        for part in parts:
            logger.info(f"Processing part for url:{url}")  # Log first 50 characters of part for reference
            try:
                # Request completion from Groq API

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": f"""
                                Extract and present the press release, news, newsPage, press media, reports related content as follows:
                                1. Provide the official reports, press release, newsPage, newsroom, news, press, press room, news feed, breaking news, newsletter, publication or similar content text exactly as it appears.
                                2. List all links to separate reports, press releases, newsPage, newsroom, news, press, press room, news feed, breaking news, newsletters, or content.
                                3. If only titles are available, present them in a comma-separated list.
                                4. Include the content that is part of the official newsPage, reports, press release, newsroom, news, press, press room, news feed, breaking news, newsletter, or content.
                                5. Omit any text that is not part of the press release itself, such as:
                                - Introductory or concluding remarks
                                - Explanatory notes
                                - Commentary
                                - Disclaimers (unless they are part of the official reports, press release, newsPage, newsroom, news, press, press room, news feed, breaking news, newsletter, or content)
                                6. If the content contains non-English text, extract and present it in its original language without translation.
                                7. Preserve the original formatting, including headers, subheaders, and bullet points.
                                8. Do not add any additional text, headers, or explanations of your own.
                                9. Start directly with the press release content without any introductory text.
                                10. If no press release content is found, respond with "NO PRESS RELEASE CONTENT".
                                11. Do not include any introductory phrases. Start directly with the reports, press release, newsroom, news, press, press room, news feed, breaking news, newsletter, or content.

                                Content to analyze:
                                {part}
                            """
                        }
                    ],
                    model="llama3-8b-8192",
                )
                # Extract and clean up the result

                result = chat_completion.choices[0].message.content
                
                # Remove introductory phrases
                result = re.sub(r'^.*?(Here is|Here are).*?:\s*\n*', '', result, flags=re.IGNORECASE | re.DOTALL)
                
                results.append(result.strip())
                logger.info(f"Successfully processed part url{url}")
            except Exception as e:
                logger.info(f"Retrying due to error:{url}")
                key_manager.mark_key_as_used(api_key)

                raise RateLimitException(str(e))
        
        # Combine results and remove any remaining introductory phrases
        combined_result = ' '.join(results)
        final_result = re.sub(r'^.*?(Here is|Here are).*?:\s*\n*', '', combined_result, flags=re.IGNORECASE | re.DOTALL)
    except Exception as e:
        logger.error(f"Error on attempt {attempt_number} for URL {url}: {str(e)}")
        key_manager.mark_key_as_used(api_key)
        raise RateLimitException(str(e))    
    return final_result.strip()


