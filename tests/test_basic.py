import pytest

def test_index_redirect(client):
    """Test that the root URL redirects to the gallery view."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/galleryout/view/output' in response.headers['Location']

def test_gallery_view_root(client):
    """Test that the main gallery view loads."""
    # We might need to mock get_dynamic_folder_config or ensure the path exists
    # For now, let's see if it returns 200 or redirects if folders are missing
    response = client.get('/galleryout/view/_root_', follow_redirects=True)
    assert response.status_code == 200
    assert b"SmartGallery" in response.data
