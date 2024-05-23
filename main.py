from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load the CSV data
data = pd.read_csv('amz_fpkt_data.csv')

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Search route
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        results = data[data['deal_title'].str.contains(query, case=False, na=False)]
    else:
        results = pd.DataFrame()
    return render_template('search.html', query=query, results=results)

if __name__ == '__main__':
    app.run(debug=False)

