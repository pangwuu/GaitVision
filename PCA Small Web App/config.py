
import os

# Get the absolute path of the project root
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Flask application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 
    
    # Use a local, predictable temp directory
    UPLOAD_FOLDER = os.path.join(basedir, 'tmp', 'uploads')
    RESULTS_FOLDER = os.path.join(basedir, 'tmp', 'results')
    
    # Ensure folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

