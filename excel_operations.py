import pandas as pd
from openpyxl import Workbook, load_workbook
import os
import json

def read_input_file(filename):
    """
    Reads an input file (Excel or CSV) and returns a DataFrame containing the 'parent_url' column.

    Args:
        filename (str): The path to the input file.

    Returns:
        pd.DataFrame: A DataFrame with the 'parent_url' column if successful; otherwise, None.
    """
    # Get file extension

    _, file_extension = os.path.splitext(filename)
    # Check if the file is Excel

    if file_extension.lower() in ['.xlsx', '.xls']:
        try:
            # Read Excel file
            return pd.read_excel(filename, usecols=['parent_url'])
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            print("Trying to read as CSV...")
    # Attempt to read CSV file if Excel reading failed

    try:
        return pd.read_csv(filename, usecols=['parent_url'])
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None