import os
import pandas as pd
import re

# Load the CSV file into a DataFrame
df = pd.read_csv('C:/Users/anoop/PycharmProjects/recommendertest3/amz_fpkt_data.csv')

# Drop rows with missing values in the 'category_all' column
df = df.dropna(subset=['category_all'])

# Extract the 'category_all' column
categories_all = df['category_all']

# Convert all entries to strings and then split them by ','
categories_lists = [str(categories).split(', ') for categories in categories_all]

# Flatten the list of lists
categories_flat = [category for sublist in categories_lists for category in sublist]

# Get unique categories
unique_categories = set(categories_flat)

# Create a folder to save the category DataFrames if it doesn't exist
folder_path = 'dataframecategories'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Create and save separate CSV files for each unique category
for category in unique_categories:
    # Escape special characters in the category name
    escaped_category = re.escape(category)
    # Filter rows that belong to the current category
    category_df = df[df['category_all'].str.contains(escaped_category)]
    # Save the DataFrame as a CSV file in the folder
    file_path = os.path.join(folder_path, f"{category}.csv")
    category_df.to_csv(file_path, index=False)
    print(f"Saved {category}.csv in dataframecategories folder.")
