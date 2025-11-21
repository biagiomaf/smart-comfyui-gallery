import pytest
import os
import hashlib
import sqlite3
from smartgallery import get_db_connection, init_db

@pytest.fixture
def sample_file(client):
    """Create a sample file and add it to the DB."""
    base_path = os.environ.get('BASE_OUTPUT_PATH')
    filename = "test_file_ops.txt"
    filepath = os.path.join(base_path, filename)
    
    with open(filepath, 'w') as f:
        f.write("test content")
        
    file_id = hashlib.md5(filepath.encode()).hexdigest()
    mtime = os.path.getmtime(filepath)
    
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO files (id, path, mtime, name, type, has_workflow) VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, filepath, mtime, filename, 'unknown', 0)
        )
        conn.commit()
        
    yield {'id': file_id, 'path': filepath, 'name': filename}
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()

def test_toggle_favorite(client, sample_file):
    """Test toggling favorite status."""
    file_id = sample_file['id']
    
    # Toggle ON
    response = client.post(f'/galleryout/toggle_favorite/{file_id}')
    assert response.status_code == 200
    assert response.json['is_favorite'] is True
    
    with get_db_connection() as conn:
        row = conn.execute("SELECT is_favorite FROM files WHERE id = ?", (file_id,)).fetchone()
        assert row['is_favorite'] == 1
        
    # Toggle OFF
    response = client.post(f'/galleryout/toggle_favorite/{file_id}')
    assert response.status_code == 200
    assert response.json['is_favorite'] is False

def test_rename_file(client, sample_file):
    """Test renaming a file."""
    file_id = sample_file['id']
    old_path = sample_file['path']
    new_name = "renamed_file.txt"
    
    response = client.post(f'/galleryout/rename_file/{file_id}', json={
        'new_name': new_name
    })
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert response.json['new_name'] == new_name
    
    new_id = response.json['new_id']
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    
    assert os.path.exists(new_path)
    assert not os.path.exists(old_path)
    
    # Cleanup the renamed file
    if os.path.exists(new_path):
        os.remove(new_path)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM files WHERE id = ?", (new_id,))
        conn.commit()

def test_delete_file(client, sample_file):
    """Test deleting a file."""
    file_id = sample_file['id']
    filepath = sample_file['path']
    
    response = client.post(f'/galleryout/delete/{file_id}')
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert not os.path.exists(filepath)
    
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        assert row is None
