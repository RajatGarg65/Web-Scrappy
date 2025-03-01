from excel_operations import read_input_file
if __name__ == "__main__":
    # Define the input file containing URLs

    input_filename = 'input_urls.xlsx'
    # Read the input file into a DataFrame

    url_df = read_input_file(input_filename)
    print("read_my_excel",url_df)
    # Slice the DataFrame to process a specific range of URLs