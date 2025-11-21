import pytest
import sys
import os
import shutil

# Add the project root to the python path so we can import smartgallery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define test data paths
TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
TEST_OUTPUT_PATH = os.path.join(TEST_DATA_DIR, 'output')
TEST_INPUT_PATH = os.path.join(TEST_DATA_DIR, 'input')
TEST_SMARTGALLERY_PATH = os.path.join(TEST_DATA_DIR, 'smartgallery')

# Set environment variables BEFORE importing smartgallery
os.environ['BASE_OUTPUT_PATH'] = TEST_OUTPUT_PATH
os.environ['BASE_INPUT_PATH'] = TEST_INPUT_PATH
os.environ['BASE_SMARTGALLERY_PATH'] = TEST_SMARTGALLERY_PATH
os.environ['SERVER_PORT'] = '8190' # Use a different port for testing
os.environ['DATABASE_FILENAME'] = 'test_gallery.sqlite'

# Ensure directories exist
for path in [TEST_OUTPUT_PATH, TEST_INPUT_PATH, TEST_SMARTGALLERY_PATH]:
    os.makedirs(path, exist_ok=True)

# Create the cache directory that smartgallery expects
os.makedirs(os.path.join(TEST_SMARTGALLERY_PATH, '.sqlite_cache'), exist_ok=True)

from smartgallery import app, init_db, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Initialize a fresh DB for testing
    # We might want to clean up before/after, but for now let's just ensure it exists
    # The app uses the global DATABASE_FILE which is derived from env vars we set above.
    with app.app_context():
        init_db()
    
    with app.test_client() as client:
        yield client

@pytest.fixture
def runner(client):
    return app.test_cli_runner()
