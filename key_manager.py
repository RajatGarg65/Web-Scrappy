import os
import json
from dotenv import load_dotenv
from logging_config import logger

load_dotenv()

class KeyManager:
    def __init__(self):
        """
        Initialize the KeyManager class.
        Loads API keys and used keys from environment variables, handling potential JSON decoding errors.
        """
        try:
            # Load API keys from environment variable, default to an empty list if not found

            self.api_keys = json.loads(os.getenv("GROQ_API_KEYS", "[]"))
            logger.info(f"Loaded {len(self.api_keys)} API keys")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing GROQ_API_KEYS: {e}")
            logger.error(f"GROQ_API_KEYS value: {os.getenv('GROQ_API_KEYS')}")
            logger.error("Please ensure GROQ_API_KEYS is a valid JSON array of strings in your .env file.")
            self.api_keys = []

        try:
            # Load used API keys from environment variable, default to an empty list if not found

            self.used_keys = json.loads(os.getenv("USED_GROQ_API_KEYS", "[]"))
            logger.info(f"Loaded {len(self.used_keys)} used keys")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing USED_GROQ_API_KEYS: {e}")
            logger.error(f"USED_GROQ_API_KEYS value: {os.getenv('USED_GROQ_API_KEYS')}")
            logger.error("Please ensure USED_GROQ_API_KEYS is a valid JSON array of strings in your .env file.")
            self.used_keys = []

        self.current_key_index = 0

    def get_next_key(self):
        """
        Retrieve the next available API key.
        If no keys are available, it resets used keys. Cycles through keys and increments the current index.
        :return: The next API key as a string.
        """
        if not self.api_keys:
            logger.info("No available keys, resetting used keys")
            self.reset_used_keys()
        # Reset index if it exceeds the number of available keys

        if self.current_key_index >= len(self.api_keys):
            self.current_key_index = 0
        # Get the key and increment the index for the next call

        key = self.api_keys[self.current_key_index]
        self.current_key_index += 1
        logger.info(f"Using API key: {key[:5]}...{key[-5:]} (index: {self.current_key_index - 1})")

        return key

    def mark_key_as_used(self, key):
        """
        Mark a specific API key as used and update the lists of active and used keys.
        If the number of used keys reaches 30, it resets the used keys.
        :param key: The API key to mark as used.
        """
        if key in self.api_keys:
            # Move the key from active to used keys list

            self.api_keys.remove(key)
            self.used_keys.append(key)
            logger.info(f"Marked key {key[:5]}...{key[-5:]} as used")
            logger.info(f"Total keys in used_keys: {len(self.used_keys)}")
            self.update_env_file()
        # Reset used keys if there are 30 or more

        if len(self.used_keys) >= 30:
            logger.info("Used keys reached 30, resetting")

            self.reset_used_keys()

    def reset_used_keys(self):
        """
        Reset the used keys list by merging it back with the active keys list.
        This function is called when there are no more active keys or the used keys list reaches a threshold.
        """
        logger.info("Resetting used keys")
        # Move all used keys back to active keys

        self.api_keys.extend(self.used_keys)
        self.used_keys.clear()
        logger.info(f"After reset: {len(self.api_keys)} active keys, {len(self.used_keys)} used keys")

        self.update_env_file()

    def update_env_file(self):
        """
        Update the .env file with the current state of active and used keys.
        This function ensures that the changes to the keys are persistent.
        """
        with open('.env', 'r') as f:
            lines = f.readlines()

        with open('.env', 'w') as f:
            for line in lines:
                if line.startswith('GROQ_API_KEYS='):
                    f.write(f'GROQ_API_KEYS={json.dumps(self.api_keys)}\n')
                elif line.startswith('USED_GROQ_API_KEYS='):
                    f.write(f'USED_GROQ_API_KEYS={json.dumps(self.used_keys)}\n')
                else:
                    f.write(line)
        logger.info("Updated .env file with current key status")

# Instantiate KeyManager and potentially perform operations

key_manager = KeyManager()