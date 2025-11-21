import os
import pytest
from smartgallery import extract_workflow

def test_extract_workflow_all_images(client):
    """Test extraction of workflow from all supported images in the output directory."""
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    assert base_path is not None, "BASE_OUTPUT_PATH environment variable not set"
    
    if not os.path.exists(base_path):
        # If the directory doesn't exist, it's effectively empty, so success.
        return

    supported_extensions = {'.webp', '.jpeg', '.jpg', '.png'}
    files_processed = 0
    
    for filename in os.listdir(base_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_extensions:
            filepath = os.path.join(base_path, filename)
            print(f"Testing workflow extraction for: {filename}")
            
            workflow = extract_workflow(filepath)
            assert workflow is not None, f"Failed to extract workflow from {filename}"
            files_processed += 1
            
    print(f"Processed {files_processed} images.")
