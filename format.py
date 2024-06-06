import pandas as pd

# Load the CSV data into a DataFrame
file_path = 'amz_fpkt_data.csv'  # Path to the uploaded CSV file
data = pd.read_csv(file_path)


# Define the function to process 'top_offers' and 'top_customer_reviews'
def process_json_columns(row):
    # Convert string representation of list to actual list
    try:
        row['top_offers'] = eval(row['top_offers'])
    except:
        row['top_offers'] = []

    try:
        row['top_customer_reviews'] = eval(row['top_customer_reviews'])
    except:
        row['top_customer_reviews'] = []

    return row


# Apply the function to the DataFrame
data = data.apply(process_json_columns, axis=1)

# Display the processed DataFrame
print(data.head())

# Save the processed DataFrame to a new CSV file if needed
output_file_path = 'processedfile/processed_amz_fpkt_data.csv'
data.to_csv(output_file_path, index=False)
