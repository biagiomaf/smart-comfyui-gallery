import pytest
import os
import json
import shutil
from smartgallery import get_dynamic_folder_config

def test_create_folder(client):
    """Test creating a new folder."""
    # Ensure we have a clean state
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    new_folder_name = "test_create_folder"
    new_folder_path = os.path.join(base_path, new_folder_name)
    
    if os.path.exists(new_folder_path):
        shutil.rmtree(new_folder_path)
        
    response = client.post('/galleryout/create_folder', json={
        'parent_key': '_root_',
        'folder_name': new_folder_name
    })
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert os.path.exists(new_folder_path)
    
    # Clean up
    if os.path.exists(new_folder_path):
        os.rmdir(new_folder_path)

def test_create_duplicate_folder(client):
    """Test creating a folder that already exists."""
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    folder_name = "test_duplicate"
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    response = client.post('/galleryout/create_folder', json={
        'parent_key': '_root_',
        'folder_name': folder_name
    })
    
    assert response.status_code == 400
    assert response.json['status'] == 'error'
    
    os.rmdir(folder_path)

def test_rename_folder(client):
    """Test renaming a folder."""
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    old_name = "test_rename_old"
    new_name = "test_rename_new"
    old_path = os.path.join(base_path, old_name)
    new_path = os.path.join(base_path, new_name)
    
    os.makedirs(old_path, exist_ok=True)
    if os.path.exists(new_path):
        os.rmdir(new_path)
        
    # Need to refresh config so the app knows about the new folder
    get_dynamic_folder_config(force_refresh=True)
    
    # Find the key for the old folder
    folders = get_dynamic_folder_config()
    folder_key = None
    for key, info in folders.items():
        if info['path'] == old_path:
            folder_key = key
            break
            
    assert folder_key is not None
    
    response = client.post(f'/galleryout/rename_folder/{folder_key}', json={
        'new_name': new_name
    })
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)
    
    os.rmdir(new_path)

def test_delete_folder(client):
    """Test deleting a folder."""
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    folder_name = "test_delete"
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    get_dynamic_folder_config(force_refresh=True)
    
    folders = get_dynamic_folder_config()
    folder_key = None
    for key, info in folders.items():
        if info['path'] == folder_path:
            folder_key = key
            break
            
    assert folder_key is not None
    
    response = client.post(f'/galleryout/delete_folder/{folder_key}')
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert not os.path.exists(folder_path)
