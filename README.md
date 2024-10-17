# video web scrape app

A web application built using Flask that allows users to search, watch, and manage video content across multiple streaming platforms. The app features modular scraping, where the modules can be added dynamically from JSON files, user accounts with authentication, and a "My List" feature for storing favorite shows.

---

## Features
Modular Web Scraping: Dynamically load different modules using JSON files to scrape data from video streaming websites.
Search Functionality: Users can search for shows across various platforms using different modules.
Watch Videos: After searching, users can play video content directly from the web app without being redirected to external websites.
User Accounts: Users can register, log in, and manage their own video list ("My List").
My List: Users can add and remove shows and movies from their personal list. Video data is saved in the database for each user.
Responsive Design: The app is built using Bootstrap to provide a clean, professional, and responsive user interface.

---

## Technologies Used
Languages
Python
HTML, CSS
JavaScript (for front-end interactivity and AJAX requests)
SQL (SQLite)

---

## Frameworks & Libraries
Flask: Python web framework for backend functionality.
Bootstrap: CSS framework for responsive and professional design.
Jinja2: Template engine for rendering HTML with dynamic data.
SQLAlchemy: ORM for managing the SQLite database.
Flask-Login: For user authentication and session management.
Flask-Bcrypt: For password hashing and security.
BeautifulSoup: For web scraping static websites.
Selenium: For scraping dynamic websites that require JavaScript rendering.

---

## Setup and Installation
### Clone the repository
```
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
### Create a virtual environment
```
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate  # For Windows
```
### Install dependencies
```
pip install -r requirements.txt
```
### Configure the Database
```
flask shell
from app import db
db.create_all()
exit()
```
### Run the Application
```
python3 app.py
```
Visit the app at http://127.0.0.1:5000/ in your browser.

---

## Usage
Login/Register: Users need to register or log in to access their personalized "My List".
Select a Module: From the home page, select a module from the dropdown menu to search for show.
Search Show: Type an show name in the search box and click "Search" to fetch results.
Watch Show: Click "Watch Now" to view episodes directly in the app.
Add to My List: Add a show to your personal list using the "Add to My List" button, and manage it from the sidebar.

