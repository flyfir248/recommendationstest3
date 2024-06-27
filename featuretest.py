import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
data = pd.read_csv("C:/Users/anoop/PycharmProjects/recommendertest3/amz_fpkt_data.csv")

# Fill NaN values with empty strings
data = data.fillna('')

# Combine product description and customer reviews into a single text column
data['combined_text'] = data['product_description'] + ' ' + data['top_customer_reviews']

# Ensure deal_rating is numeric
data['deal_rating'] = pd.to_numeric(data['deal_rating'], errors='coerce')

# Drop rows with NaN deal_rating values
data = data.dropna(subset=['deal_rating'])

# Extract features from text using TF-IDF Vectorizer
tfidf = TfidfVectorizer(max_features=1000)
text_features = tfidf.fit_transform(data['combined_text'])

# Encode categorical features
le = LabelEncoder()
categorical_features = data[['category_1', 'category_2', 'category_3', 'category_4', 'category_5', 'category_6', 'category_7']].apply(le.fit_transform)

# Combine all features
all_features = np.hstack((text_features.toarray(), categorical_features))

# Target variable (for demonstration, we'll use deal_rating as the target)
target = data['deal_rating']

# Train a RandomForestRegressor to determine feature importance
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(all_features, target)

# Get feature importances
importances = model.feature_importances_
top_indices = np.argsort(importances)[-20:]

# Map the top indices to their corresponding feature names
num_tfidf_features = text_features.shape[1]
feature_names = list(tfidf.get_feature_names_out()) + list(categorical_features.columns)
top_features = [feature_names[i] for i in top_indices]

# Streamlit app
st.title("E-commerce Product Browser")

# Sidebar for user input
st.sidebar.header("Search Filters")
search_category = st.sidebar.selectbox("Category", options=data['category_1'].unique())
search_keyword = st.sidebar.text_input("Keyword")

# Filter products based on user input
filtered_data = data[data['category_1'] == search_category]
if search_keyword:
    filtered_data = filtered_data[filtered_data['deal_title'].str.contains(search_keyword, case=False)]

st.header("Product Listings")

for _, row in filtered_data.iterrows():
    st.subheader(row['deal_title'])
    st.write(f"Rating: {row['deal_rating']} ({row['deal_rating_count']} reviews)")
    st.write(f"Price: {row['deal_act_price']} (MRP: {row['deal_mrp_price']})")
    st.write(f"Discount: {row['deal_offer_percent']}%")
    st.write(f"Description: {row['product_description']}")
    st.write(f"Customer Reviews: {row['top_customer_reviews']}")
    st.markdown(f"[Product Link]({row['deal_url']})")

st.header("Important Features")
st.write("These are the features that are most important in predicting deal ratings:")
for feature in top_features:
    st.write(feature)

# Visualize feature importances
st.header("Feature Importance Visualization")
plt.figure(figsize=(10, 6))
sns.barplot(x=importances[top_indices], y=top_features)
plt.title("Top 20 Important Features")
plt.xlabel("Importance")
plt.ylabel("Feature")
st.pyplot(plt)

# Show shared features across products
st.header("Shared Features in Products")
shared_features = []
if search_keyword:
    filtered_data['combined_text'] = filtered_data['product_description'] + ' ' + filtered_data['top_customer_reviews']
    search_tfidf = tfidf.transform(filtered_data['combined_text'])
    for i in range(search_tfidf.shape[1]):
        if search_tfidf[:, i].sum() > 1:
            shared_features.append(tfidf.get_feature_names_out()[i])
    st.write(", ".join(shared_features))
else:
    st.write("No keyword entered to find shared features.")
