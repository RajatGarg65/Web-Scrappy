from logging_config import logger
from groq_test import run_groq_api as original_run_groq_api
def run_groq_api(content, url):
    """
    Wrapper function for calling the original Groq API implementation.

    Args:
        content (str): The text content to be processed.
        url (str): The URL associated with the content.

    Returns:
        str: The processed content returned by the original Groq API function.

    Raises:
        Exception: If an error occurs during the API call, it logs the error and raises the exception.
    """
    try:
        # Call the original Groq API function

        result = original_run_groq_api(content,url)
        return result
    except Exception as e:
        # Log the error if an exception occurs

        logger.error(f"Error in Groq API call: {str(e)}")
        # Re-raise the exception to propagate it further

        raise