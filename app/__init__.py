from flask import Flask

# Initialize the app
app = Flask(__name__)

# Import routes after app initialization to avoid circular imports
from app import app as application
