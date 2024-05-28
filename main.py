from flask import Flask, render_template, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

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
    return data


data = calculate_scores(data)


@app.route('/')
def home():
    # Randomly select a few products for the featured section
    featured_products = data.sample(n=5).to_dict(orient='records')

    # Select the top product based on score
    top_product = data.loc[data['score'].idxmax()].to_dict()

    return render_template('index.html', featured_products=featured_products, top_product=top_product)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
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
