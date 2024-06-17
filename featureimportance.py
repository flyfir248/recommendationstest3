# Import necessary libraries
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Load the dataset from the CSV file
df = pd.read_csv('amz_fpkt_data.csv')

# Function to recommend products based on product description
def recommend_products(product_id, num_recommendations=3):
    # Combine all attributes into a single string for vectorization
    df['combined_features'] = df['product_description'].fillna('') + ' ' + df['top_customer_reviews'].fillna('')

    # Vectorize the combined features
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_features'])

    # Compute the cosine similarity matrix
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # Get the index of the product that matches the product_id
    idx = df.index[df['deal_id'] == product_id][0]

    # Get the pairwise similarity scores of all products with the selected product
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the products based on similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the top-n most similar products
    sim_scores = sim_scores[1:num_recommendations + 1]

    # Get the product indices
    product_indices = [i[0] for i in sim_scores]

    # Return the top-n most similar products
    return df.iloc[product_indices][['deal_id', 'deal_title', 'deal_url', 'deal_act_price', 'deal_rating', 'deal_rating_count']]

# Example usage: Recommend products similar to the first product
product_id = 5  # Change this to the deal_id of the product you're interested in
num_recommendations = 7
recommendations = recommend_products(product_id, num_recommendations)

# Export recommendations to CSV
output_file_path = 'FeatureRec/featurerecommendations.csv'
recommendations.to_csv(output_file_path, index=False)

print("Recommendations exported to:", output_file_path)
