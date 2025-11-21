import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure smartgallery can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartgallery import analyze_file_metadata

def test_analyze_file_metadata_image():
    """Test metadata analysis for a standard image."""
    with patch('smartgallery.Image.open') as mock_open:
        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600
        mock_open.return_value.__enter__.return_value = mock_img
        
        # Mock extract_workflow to return None (no workflow)
        with patch('smartgallery.extract_workflow', return_value=None):
            metadata = analyze_file_metadata("test.jpg")
            
            assert metadata['type'] == 'image'
            assert metadata['dimensions'] == '800x600'
            assert metadata['has_workflow'] == 0

def test_analyze_file_metadata_video():
    """Test metadata analysis for a video file."""
    with patch('smartgallery.cv2.VideoCapture') as mock_video_capture:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            5: 30.0,  # cv2.CAP_PROP_FPS
            7: 300.0, # cv2.CAP_PROP_FRAME_COUNT
            3: 1920.0, # cv2.CAP_PROP_FRAME_WIDTH
            4: 1080.0  # cv2.CAP_PROP_FRAME_HEIGHT
        }.get(prop, 0)
        
        mock_video_capture.return_value = mock_cap
        
        with patch('smartgallery.extract_workflow', return_value=None):
            metadata = analyze_file_metadata("test.mp4")
            
            assert metadata['type'] == 'video'
            assert metadata['dimensions'] == '1920x1080'
            assert metadata['duration'] == '00:10' # 300 frames / 30 fps = 10 seconds

def test_analyze_file_metadata_animated_webp():
    """Test metadata analysis for an animated webp."""
    with patch('smartgallery.Image.open') as mock_open:
        mock_img = MagicMock()
        mock_img.is_animated = True
        mock_img.n_frames = 48
        mock_img.width = 512
        mock_img.height = 512
        mock_open.return_value.__enter__.return_value = mock_img
        
        # Mock is_webp_animated helper
        with patch('smartgallery.is_webp_animated', return_value=True):
             with patch('smartgallery.extract_workflow', return_value=None):
                # Assuming WEBP_ANIMATED_FPS is 16.0 (default)
                metadata = analyze_file_metadata("test.webp")
                
                assert metadata['type'] == 'animated_image'
                assert metadata['dimensions'] == '512x512'
                # 48 frames / 16 fps = 3 seconds
                assert metadata['duration'] == '00:03'

def test_analyze_file_metadata_unknown_type():
    """Test metadata analysis for an unknown file type."""
    metadata = analyze_file_metadata("test.xyz")
    assert metadata['type'] == 'unknown'
