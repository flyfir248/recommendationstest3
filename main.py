from flask import Flask, render_template, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

# Load the CSV data
data = pd.read_csv('amz_fpkt_data.csv')

# Home route
@app.route('/')
def home():
    # Randomly select a few products for the featured section
    featured_products = data.sample(n=5).to_dict(orient='records')
    return render_template('index.html', featured_products=featured_products)

# Search route
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        results = data[data['deal_title'].str.contains(query, case=False, na=False)]
    else:
        results = pd.DataFrame()
    return render_template('search.html', query=query, results=results)

# Autocomplete route
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
