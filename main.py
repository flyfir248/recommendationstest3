import logging
import csv
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the SearchQuery model
class SearchQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchQuery {self.query}>'

# Create the database
with app.app_context():
    db.create_all()

# Load the CSV data
data = pd.read_csv('C:/Users/anoop/PycharmProjects/recommendertest3/amz_fpkt_data.csv')

def calculate_scores(data):
    data['product_description'] = data['product_description'].fillna('')
    category_counts = data['category_all'].value_counts().to_dict()
    attribute_counts = {}
    for description in data['product_description']:
        for attribute in description.split(','):
            attribute = attribute.strip()
            if attribute in attribute_counts:
                attribute_counts[attribute] += 1
            else:
                attribute_counts[attribute] = 1

    data['score'] = data.apply(lambda row: category_counts.get(row['category_all'], 0) +
                                           sum(attribute_counts.get(attr.strip(), 0) for attr in
                                               row['product_description'].split(',')),
                               axis=1)
    return data

data = calculate_scores(data)

def save_search_to_csv(query):
    with open('search_queries.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([query, datetime.utcnow()])

def load_search_queries():
    try:
        search_data = pd.read_csv('search_queries.csv', names=['query', 'timestamp'], parse_dates=['timestamp'])
        return search_data
    except FileNotFoundError:
        return pd.DataFrame(columns=['query', 'timestamp'])

def get_recommendations():
    try:
        search_data = load_search_queries()
        if search_data.empty:
            logging.info("No recent search found.")
            return []

        latest_search = search_data.iloc[-1]
        logging.info(f"Latest search query: {latest_search['query']}")

        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(data['product_description'])
        search_vector = tfidf_vectorizer.transform([latest_search['query']])
        cosine_similarities = cosine_similarity(search_vector, tfidf_matrix).flatten()
        similar_indices = cosine_similarities.argsort()[:-6:-1]
        recommended_products = data.iloc[similar_indices].to_dict(orient='records')

        logging.info(f"Recommended products: {recommended_products}")

        return recommended_products
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        return []

@app.route('/')
def home():
    try:
        sorted_data = data.sort_values(by='score', ascending=False)
        featured_products = sorted_data.sample(n=5).to_dict(orient='records')
        top_products = sorted_data.head(5).to_dict(orient='records')
        recommended_products = get_recommendations()

        return render_template('index.html', featured_products=featured_products, top_products=top_products, recommended_products=recommended_products)
    except Exception as e:
        logging.error(f"Error in home route: {e}")
        return "Internal Server Error", 500

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        save_search_to_csv(query)
        results = data[data['deal_title'].str.contains(query, case=False, na=False)]
    else:
        results = pd.DataFrame()
    return render_template('search.html', query=query, results=results)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    if query:
        suggestions = data[data['deal_title'].str.contains(query, case=False, na=False)]['deal_title'].unique().tolist()
    else:
        suggestions = []
    return jsonify(suggestions)

# Path to the directory containing categorized CSVs
CATEGORIES_PATH = 'C:/Users/anoop/PycharmProjects/recommendertest3/dataframecategories'

# Load all categories and their CSVs
def load_categories():
    categories = {}
    for filename in os.listdir(CATEGORIES_PATH):
        if filename.endswith('.csv'):
            category_name = filename[:-4]
            categories[category_name] = os.path.join(CATEGORIES_PATH, filename)
    return categories

categories = load_categories()

@app.route('/categories')
def list_categories():
    return render_template('categories.html', categories=categories.keys())

@app.route('/category/<category_name>')
def show_category(category_name):
    csv_path = categories.get(category_name)
    if csv_path:
        df = pd.read_csv(csv_path)
        products = df.to_dict(orient='records')
        return render_template('category.html', category_name=category_name, products=products)
    else:
        return "Category not found", 404

@app.route('/deals')
def deals():
    return "Deals page"  # Implement deals logic here

@app.route('/contact')
def contact():
    return "Contact page"  # Implement contact logic here

if __name__ == '__main__':
    app.run(debug=False)
