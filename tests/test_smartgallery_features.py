import unittest
import os
import shutil
import time
import tempfile
from unittest.mock import patch, MagicMock
import sys
import importlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSmartGalleryFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create mocks
        cls.mock_cv2 = MagicMock()
        cls.mock_pil = MagicMock()
        cls.mock_tqdm = MagicMock()
        cls.mock_flask = MagicMock()
        cls.mock_werkzeug = MagicMock()
        
        # Setup Flask mock
        def route_decorator(*args, **kwargs):
            def wrapper(f):
                return f
            return wrapper
        cls.mock_flask.Flask.return_value.route.side_effect = route_decorator
        
        # Patch sys.modules
        cls.modules_patcher = patch.dict(sys.modules, {
            'cv2': cls.mock_cv2,
            'PIL': cls.mock_pil,
            'PIL.Image': cls.mock_pil.Image,
            'PIL.ImageSequence': cls.mock_pil.ImageSequence,
            'tqdm': cls.mock_tqdm,
            'flask': cls.mock_flask,
            'werkzeug': cls.mock_werkzeug,
            'werkzeug.utils': cls.mock_werkzeug.utils
        })
        cls.modules_patcher.start()
        
        # Force reload/import of smartgallery with mocks
        if 'smartgallery' in sys.modules:
            del sys.modules['smartgallery']
        import smartgallery
        cls.smartgallery = smartgallery
        
    @classmethod
    def tearDownClass(cls):
        cls.modules_patcher.stop()
        # Clean up smartgallery from sys.modules so subsequent tests re-import the real one (or their own mocks)
        if 'smartgallery' in sys.modules:
            del sys.modules['smartgallery']

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.delete_cache_dir = os.path.join(self.test_dir, 'Deleted')
        self.zip_cache_dir = os.path.join(self.test_dir, 'zip_downloads')
        os.makedirs(self.delete_cache_dir)
        os.makedirs(self.zip_cache_dir)
        
        # Patch globals on the imported module
        self.orig_delete_cache_dir = self.smartgallery.DELETE_CACHE_DIR
        self.orig_zip_cache_dir = self.smartgallery.ZIP_CACHE_DIR
        self.orig_clear_temp_days = self.smartgallery.CLEAR_TEMP_DAYS
        self.orig_delete_moves = self.smartgallery.DELETE_MOVES
        
        self.smartgallery.DELETE_CACHE_DIR = self.delete_cache_dir
        self.smartgallery.ZIP_CACHE_DIR = self.zip_cache_dir
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.smartgallery.DELETE_CACHE_DIR = self.orig_delete_cache_dir
        self.smartgallery.ZIP_CACHE_DIR = self.orig_zip_cache_dir
        self.smartgallery.CLEAR_TEMP_DAYS = self.orig_clear_temp_days
        self.smartgallery.DELETE_MOVES = self.orig_delete_moves

    def test_cleanup_temp_files(self):
        # Set retention to 1 day
        self.smartgallery.CLEAR_TEMP_DAYS = 1
        
        # Create old file (2 days old)
        old_file = os.path.join(self.delete_cache_dir, 'old.txt')
        with open(old_file, 'w') as f: f.write('old')
        old_time = time.time() - (2 * 86400)
        os.utime(old_file, (old_time, old_time))
        
        # Create new file (1 hour old)
        new_file = os.path.join(self.delete_cache_dir, 'new.txt')
        with open(new_file, 'w') as f: f.write('new')
        
        # Create old folder
        old_folder = os.path.join(self.delete_cache_dir, 'old_folder')
        os.makedirs(old_folder)
        os.utime(old_folder, (old_time, old_time))
        
        # Run cleanup
        count, errors = self.smartgallery.cleanup_temp_files()
        
        # Verify
        self.assertFalse(os.path.exists(old_file), "Old file should be deleted")
        self.assertTrue(os.path.exists(new_file), "New file should remain")
        self.assertFalse(os.path.exists(old_folder), "Old folder should be deleted")
        self.assertEqual(count, 2)
        self.assertEqual(len(errors), 0)

    def test_delete_folder_moves_if_enabled(self):
        # Setup
        self.smartgallery.DELETE_MOVES = True
        folder_to_delete = os.path.join(self.test_dir, 'folder_to_delete')
        os.makedirs(folder_to_delete)
        
        # Mock dependencies using patch on the module object we imported
        with patch.object(self.smartgallery, 'get_dynamic_folder_config') as mock_get_config, \
             patch.object(self.smartgallery, 'get_db_connection') as mock_get_db, \
             patch.object(self.smartgallery, 'request', MagicMock()) as mock_request, \
             patch.object(self.smartgallery, 'jsonify', MagicMock()) as mock_jsonify:
             
            mock_get_config.return_value = {
                'key1': {'path': folder_to_delete}
            }
            
            # Mock DB
            mock_conn = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_conn
            
            # Call delete_folder
            self.smartgallery.delete_folder('key1')
                
            # Verify
            self.assertFalse(os.path.exists(folder_to_delete), "Original folder should be gone")
            
            moved_folder = os.path.join(self.delete_cache_dir, 'folder_to_delete')
            self.assertTrue(os.path.exists(moved_folder), "Folder should be moved to Deleted")
            
            # Verify success response
            mock_jsonify.assert_called_with({'status': 'success', 'message': 'Folder deleted.'})

if __name__ == '__main__':
    unittest.main()
