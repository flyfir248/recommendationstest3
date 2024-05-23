import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('C:/Users/anoop/PycharmProjects/recommendertest3/amz_fpkt_data.csv')

# Extract the 'category_all' column
categories_all = df['category_all']

# Convert all entries to strings and then split them by ','
categories_lists = [str(categories).split(', ') for categories in categories_all]

# Flatten the list of lists
categories_flat = [category for sublist in categories_lists for category in sublist]

# Get unique categories
unique_categories = set(categories_flat)

# Convert unique categories to a list
unique_categories_list = list(unique_categories)

# Print the unique categories
print("Categories:")
for cat in unique_categories_list:
    print(cat)
