import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Mock cv2 and flask before importing smartgallery
sys.modules['cv2'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Add parent directory to path to import smartgallery
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smartgallery

class TestConfigStructure(unittest.TestCase):
    def setUp(self):
        # Reset the global cache before each test
        smartgallery.folder_config_cache = None

    @patch('smartgallery.BASE_OUTPUT_PATH', '/mock/output')
    @patch('smartgallery.BASE_INPUT_PATH', '/mock/input')
    @patch('os.walk')
    @patch('os.path.getmtime')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_get_dynamic_folder_config_structure(self, mock_exists, mock_isdir, mock_getmtime, mock_walk):
        # Setup mocks
        mock_getmtime.return_value = 1234567890.0
        mock_isdir.return_value = True
        mock_exists.return_value = True
        
        # Mock os.walk to return some dummy folders
        def walk_side_effect(path):
            if path == '/mock/output':
                yield ('/mock/output', ['sub1', 'sub2'], [])
                yield ('/mock/output/sub1', [], [])
                yield ('/mock/output/sub2', [], [])
            elif path == '/mock/input':
                yield ('/mock/input', ['workflow_json'], [])
                yield ('/mock/input/workflow_json', [], [])
            else:
                yield (path, [], [])
        mock_walk.side_effect = walk_side_effect

        # Call the function
        config = smartgallery.get_dynamic_folder_config(force_refresh=True)

        # Verify Root
        self.assertIn('_root_', config)
        root = config['_root_']
        self.assertEqual(root['display_name'], 'Main')
        self.assertIn('output', root['children']) # Check key names, might need adjustment based on implementation
        self.assertIn('input', root['children'])

        # Verify Output Root
        output_key = 'output' # Assumed key
        self.assertIn(output_key, config)
        self.assertEqual(config[output_key]['path'].replace('\\', '/'), '/mock/output')
        self.assertEqual(config[output_key]['parent'], '_root_')

        # Verify Input Root
        input_key = 'input' # Assumed key
        self.assertIn(input_key, config)
        self.assertEqual(config[input_key]['path'].replace('\\', '/'), '/mock/input')
        self.assertEqual(config[input_key]['parent'], '_root_')

        # Verify Subfolders
        # We need to check if subfolders are correctly keyed and parented
        # Since keys are base64 encoded relative paths, we need to check logic
        
        found_sub1 = False
        for key, value in config.items():
            if value['display_name'] == 'sub1' and value['parent'] == output_key:
                found_sub1 = True
                break
        self.assertTrue(found_sub1, "Output subfolder 'sub1' not found or parent incorrect")

        found_workflow = False
        for key, value in config.items():
            if value['display_name'] == 'workflow_json' and value['parent'] == input_key:
                found_workflow = True
                break
        self.assertTrue(found_workflow, "Input subfolder 'workflow_json' not found or parent incorrect")

if __name__ == '__main__':
    unittest.main()
