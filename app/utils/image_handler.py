import os
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask import current_app

def save_image_from_url(image_url, book_isbn):
    """
    Downloads an image from a URL and saves it to the local storage.
    Returns the relative path to the saved image.
    """
    if not image_url:
        return None

    try:
        # Create the images directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'book_covers')
        os.makedirs(upload_folder, exist_ok=True)

        # Get the file extension from the URL
        parsed_url = urlparse(image_url)
        extension = os.path.splitext(parsed_url.path)[1]
        if not extension:
            extension = '.jpg'  # Default to jpg if no extension found

        # Create a secure filename using the ISBN
        filename = secure_filename(f"{book_isbn}{extension}")
        file_path = os.path.join(upload_folder, filename)

        # Download and save the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Return the relative path using forward slashes
        return f"book_covers/{filename}"

    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None

def delete_book_image(image_path):
    """
    Deletes a book's image file from storage.
    """
    if not image_path:
        return

    try:
        full_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting image: {str(e)}")
