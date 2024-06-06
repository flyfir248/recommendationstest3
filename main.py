import logging
import csv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Define the SearchQuery model
class SearchQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('search_queries', lazy=True))

    def __repr__(self):
        return f'<SearchQuery {self.query}>'

# Create the database
with app.app_context():
    db.create_all()

# Load the CSV data
data = pd.read_csv('amz_fpkt_data.csv')

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True))


# Create the new tables
with app.app_context():
    db.create_all()
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.json.get('product_id')
    if product_id:
        cart_item = Cart(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400



@app.route('/profile')
@login_required
def profile():
    # Fetch cart items for the current user
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()

    # Calculate total amount
    total_amount = 0
    for item in cart_items:
        product = data[data['id'] == item.product_id].iloc[0]
        total_amount += product['price'] * item.quantity

    return render_template('profile.html', cart_items=cart_items, wishlist_items=wishlist_items,
                           total_amount=total_amount)


@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    products = [{'product_id': item.product_id, 'quantity': item.quantity} for item in cart_items]
    return render_template('cart.html', products=products)

@app.route('/add_to_wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    product_id = request.json.get('product_id')
    if product_id:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400

@app.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    products = [{'product_id': item.product_id} for item in wishlist_items]
    return render_template('wishlist.html', products=products)

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
    return redirect(url_for('wishlist'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        logging.info(f'New user registered: {user.username}')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            logging.info(f'User logged in: {user.username}')
            return redirect(url_for('home'))
        else:
            logging.warning('Failed login attempt')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logging.info(f'User logged out: {current_user.username}')
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
@login_required
def home():
    try:
        sorted_data = data.sort_values(by='score', ascending=False)
        featured_products = sorted_data.sample(n=5).to_dict(orient='records')
        top_products = sorted_data.head(5).to_dict(orient='records')
        recommended_products = get_recommendations()

        logging.info(f"User {current_user.username} accessed home page")
        return render_template('index.html', featured_products=featured_products, top_products=top_products, recommended_products=recommended_products)
    except Exception as e:
        logging.error(f"Error in home route: {e}")
        return "Internal Server Error", 500

@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query')
    if query:
        save_search_to_csv(query)
        results = data[data['deal_title'].str.contains(query, case=False, na=False)]
        logging.info(f"User {current_user.username} searched for '{query}'")
    else:
        results = pd.DataFrame()
    return render_template('search.html', query=query, results=results)

@app.route('/autocomplete', methods=['GET'])
@login_required
def autocomplete():
    query = request.args.get('query', '')
    if query:
        suggestions = data[data['deal_title'].str.contains(query, case=False, na=False)]['deal_title'].unique().tolist()
    else:
        suggestions = []
    return jsonify(suggestions)

@app.route('/category_filters', methods=['GET'])
@login_required
def category_filters():
    category = request.args.get('category')
    csv_path = categories.get(category)
    if csv_path:
        df = pd.read_csv(csv_path)
        filters = df.columns.tolist()  # Assuming the first row contains filter names
        return jsonify({'filters': filters})
    else:
        return jsonify({'filters': []})

# Path to the directory containing categorized CSVs
CATEGORIES_PATH = 'dataframecategories'

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
@login_required
def list_categories():
    return render_template('categories.html', categories=categories.keys())

@app.route('/category/<category_name>')
@login_required
def show_category(category_name):
    csv_path = categories.get(category_name)
    if csv_path:
        df = pd.read_csv(csv_path)
        products = df.to_dict(orient='records')
        return render_template('category.html', category_name=category_name, products=products)
    else:
        return "Category not found", 404

@app.route('/deals')
@login_required
def deals():
    return "Deals page"  # Implement deals logic here

@app.route('/contact')
@login_required
def contact():
    return "Contact page"  # Implement contact logic here

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
