from flask import Flask, render_template, request, jsonify
import pandas as pd
import random
import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='product_scores.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

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
data = pd.read_csv('amz_fpkt_data.csv')

print(data.columns)

def calculate_scores(data):
    # Ensure 'product_description' has no missing values
    data['product_description'] = data['product_description'].fillna('')

    # Calculate the frequency of each category
    category_counts = data['category_all'].value_counts().to_dict()

    # Calculate the frequency of each attribute
    attribute_counts = {}
    for description in data['product_description']:
        for attribute in description.split(','):
            attribute = attribute.strip()
            if attribute in attribute_counts:
                attribute_counts[attribute] += 1
            else:
                attribute_counts[attribute] = 1

    # Calculate score for each product
    data['score'] = data.apply(lambda row: category_counts.get(row['category_all'], 0) +
                                           sum(attribute_counts.get(attr.strip(), 0) for attr in
                                               row['product_description'].split(',')),
                               axis=1)

    # Log the scores
    logging.info("Calculated scores:")
    for idx, row in data.iterrows():
        logging.info(f"Product ID: {row['deal_id']}, Score: {row['score']}")

    return data

data = calculate_scores(data)

@app.route('/')
def home():
    # Sort products based on score in descending order
    sorted_data = data.sort_values(by='score', ascending=False)

    # Randomly select a few products for the featured section
    featured_products = sorted_data.sample(n=5).to_dict(orient='records')

    # Select the top products based on score
    top_products = sorted_data.head(5).to_dict(orient='records')

    return render_template('index.html', featured_products=featured_products, top_products=top_products)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        # Store the search query in the database
        new_query = SearchQuery(query=query)
        db.session.add(new_query)
        db.session.commit()

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

if __name__ == '__main__':
    app.run(debug=False)
