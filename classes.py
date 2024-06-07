import pandas as pd
import os
import ast

# Load the CSV file
file_path = 'amz_fpkt_data.csv'
data = pd.read_csv(file_path)

# Define the base directory to save the categorized files
base_dir = 'classes'

# Create the directory if it doesn't exist
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Define category hierarchy
category_hierarchy = {
    "Electronics": ["TVs", "laptops", "smartphones", "accessories"],
    "Books": ["genres", "audiobooks", "eBooks"],
    "Clothing, Shoes, and Jewelry": ["men", "women", "children", "accessories"],
    "Home & Kitchen": ["kitchen appliances", "furniture", "home decor", "bedding"],
    "Beauty & Personal Care": ["skincare", "makeup", "haircare", "grooming products"],
    "Toys & Games": ["board games", "educational toys", "for children of all ages"],
    "Sports & Outdoors": ["sporting equipment", "outdoor gear", "fitness products"],
    "Automotive": ["car accessories", "tools", "vehicle parts"],
    "Grocery & Gourmet Food": ["food items", "beverages", "pantry staples"],
    "Health & Household": ["health care products", "cleaning supplies", "household essentials"]
}


# Helper function to classify subcategories
def classify_into_subcategory(cat_list, hierarchy):
    if isinstance(cat_list, str):
        try:
            cats = ast.literal_eval(cat_list)
            if isinstance(cats, list):
                for category, subcategories in hierarchy.items():
                    for subcategory in subcategories:
                        if subcategory in cats:
                            return category, subcategory
        except (ValueError, SyntaxError):
            pass
    return None, None


# Process and save data into hierarchical folders
for category, subcategories in category_hierarchy.items():
    for subcategory in subcategories:
        # Filter data for each subcategory
        def is_in_subcategory(cat_list):
            cat, subcat = classify_into_subcategory(cat_list, category_hierarchy)
            return cat == category and subcat == subcategory


        subcategory_data = data[data['category_all'].apply(is_in_subcategory)]

        # Create directory for each category and subcategory
        subcategory_dir = os.path.join(base_dir, category.replace(' ', '_'), subcategory.replace(' ', '_'))
        if not os.path.exists(subcategory_dir):
            os.makedirs(subcategory_dir)

        # Save subcategory data
        subcategory_filename = f"{subcategory.replace(' ', '_')}.csv"
        subcategory_data.to_csv(os.path.join(subcategory_dir, subcategory_filename), index=False)

print(f"Categorized files have been saved in the '{base_dir}' folder.")
