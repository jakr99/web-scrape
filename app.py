from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class MyList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    link = db.Column(db.String(150), nullable=False)
    image = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    my_list = db.relationship('MyList', backref='owner', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hash the password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create the new user
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Fetch the user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if the password is correct
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your credentials.', 'danger')
    
    return render_template('login.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

my_list = []

# Load all available modules from the 'modules/' directory
def load_all_modules():
    modules = {}
    module_files = os.listdir('modules/')
    
    for filename in module_files:
        with open(os.path.join('modules', filename), 'r') as file:
            module_data = json.load(file)
            modules[module_data['moduleInfo']['moduleName']] = module_data
            
    return modules

# Load all the modules at startup
modules = load_all_modules()

@app.route('/')
def index():
    # Pass the available modules to the template for the dropdown
    module_names = list(modules.keys())
    return render_template('index.html', module_names=module_names)

@app.route('/add_to_list', methods=['POST'])
@login_required
def add_to_list():
    anime_data = request.get_json()
    print(f"data recieved: {anime_data}")
    title = anime_data.get('title')
    link = anime_data.get('link')
    image = anime_data.get('image')

    # Ensure data is valid
    if not title or not link or not image:
        return jsonify({"error": "Missing data"}), 400

    # Check if the anime is already in the user's list
    existing_anime = MyList.query.filter_by(title=title, user_id=current_user.id).first()
    if not existing_anime:
        new_anime = MyList(title=title, link=link, image=image, user_id=current_user.id)
        db.session.add(new_anime)
        db.session.commit()

    return jsonify({"success": True})


@app.route('/remove_from_list', methods=['POST'])
@login_required
def remove_from_list():
    data = request.get_json()
    anime_id = data.get('id')  # Get the ID of the anime to be removed

    if anime_id:
        # Query the database for the anime by its ID and the current user's ID
        anime_to_remove = MyList.query.filter_by(id=anime_id, user_id=current_user.id).first()

        if anime_to_remove:
            db.session.delete(anime_to_remove)
            db.session.commit()
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Anime not found"}), 404
    else:
        return jsonify({"error": "Invalid ID"}), 400


@app.route('/my_list')
@login_required
def view_my_list():
    # Get all anime in the user's "My List"
    user_list = MyList.query.filter_by(user_id=current_user.id).all()

    # Convert the list to a dictionary to send as JSON
    my_list_data = [
        {
            'id': anime.id,  # Include the ID to remove items from the list later
            'title': anime.title,
            'link': anime.link,
            'image': anime.image
        }
        for anime in user_list
    ]

    return jsonify({"my_list": my_list_data})


@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    selected_module_name = request.form['module']
    
    selected_module = modules[selected_module_name]
    
    # Get dynamic selectors from the module's JSON file
    item_selector = selected_module['selectors']['itemSelector']
    title_selector = selected_module['selectors']['titleSelector']
    link_selector = selected_module['selectors']['linkSelector']
    image_selector = selected_module['selectors']['imageSelector']

    search_url = selected_module['search'][0]['request']['url'].replace('<searched>', query)
    
    response = requests.get(search_url)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from the website"}), 500
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    items = soup.select(item_selector)
    dataArray = []
    
    for item in items:
        # Handle dynamic title selection (via attribute or text content)
        title = (
            item.select_one(title_selector).get('title') or
            item.select_one(title_selector).get('data-jname') or
            item.select_one(title_selector).text.strip()
        )

        # Handle dynamic link selection (from the 'href' attribute)
        link = selected_module['moduleInfo']['baseURL'] + item.select_one(link_selector)['href']

        # Handle dynamic image selection (from the 'data-src' attribute or 'src')
        image = (
            item.select_one(image_selector).get('data-src') or
            item.select_one(image_selector)['src']
        )
        
        dataArray.append({
            'title': title,
            'link': link,
            'image': image
        })

    
    return jsonify({"data": dataArray})

@app.route('/watch')
def watch_anime():
    title = request.args.get('title')
    link = request.args.get('link')

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set up Selenium WebDriver (make sure to adjust the path to where your ChromeDriver is located)
    chrome_service = Service('/users/jakelee/chromedriver-mac-arm64/chromedriver')  # Update this path to where your chromedriver is installed
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # Load the page with Selenium
    driver.get(link)
    time.sleep(5)  # Wait for the JavaScript to load the page content

    # Get the fully rendered HTML
    page_source = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, 'lxml')

    # Extract episodes (same as before, based on the Anitaku structure)
    episodes = []
    episode_items = soup.select('a:has(.name)')

    for ep in episode_items:
        if ep.select_one('.name'):
            ep_link = ep['href'].strip()
            full_ep_link = 'https://anitaku.to' + ep_link or 'https://hianime.to' + ep_link
            ep_number = ep.select_one('.name').text.strip().replace('EP', '').strip()

            episodes.append({'number': ep_number, 'link': full_ep_link})

    # Close the Selenium WebDriver
    driver.quit()

    return render_template('watch.html', title=title, episodes=episodes)

@app.route('/play')
def play_video():
    # Get the episode link from the query parameter
    episode_link = request.args.get('episode_link')

    # Fetch the episode page to extract the video source URL
    response = requests.get(episode_link)

    if response.status_code != 200:
        return "Failed to load video", 500

    soup = BeautifulSoup(response.text, 'lxml')

    # Find the <iframe> tag and extract the src attribute
    iframe_tag = soup.find('iframe')
    
    if iframe_tag:
        video_url = iframe_tag['src']
    else:
        return "Video not found", 404

    # Pass the video URL to the template for rendering
    return render_template('play.html', video_url=video_url)

@app.route('/episodes', methods=['GET'])
def episodes():
    anime_link = request.args.get('anime_link')
    
    # Fetch the anime's episode list page
    response = requests.get(anime_link)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from the website"}), 500

    soup = BeautifulSoup(response.text, 'lxml')

    # Capture episode range links
    episode_range_links = []
    range_elements = soup.select('a[ep_start]')  # Select <a> tags with ep_start and ep_end attributes
    for element in range_elements:
        ep_start = element['ep_start']
        ep_end = element['ep_end']
        range_text = f"{ep_start}-{ep_end}"
        # Assuming clicking the range updates the same page or leads to a different URL
        episode_range_links.append({
            'range': range_text,
            'link': anime_link + f"?ep_start={ep_start}&ep_end={ep_end}"
        })

    # Capture individual episode links (if available)
    episodes = []
    episode_elements = soup.select('a.episode-link')  # Adjust the selector to match actual episode links
    for episode in episode_elements:
        episode_name = episode.text.strip()
        episode_link = episode['href']
        episodes.append({
            'name': episode_name,
            'link': episode_link
        })

    return render_template('watch.html', episodes=episodes, episode_ranges=episode_range_links)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
