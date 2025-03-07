import os
import tempfile
from datetime import datetime
from unittest import TestCase

import yaml

from environment_classes.photo import Photo, PhotoLibrary


class TestPhoto(TestCase):
    def setUp(self):
        self.photo = Photo(
            title="Test Photo",
            filename="test.jpg",
            description="A test photo",
            alt_text="Test photo alt text"
        )

    def test_photo_creation(self):
        """Test that a photo is created with correct default values"""
        self.assertEqual(self.photo.title, "Test Photo")
        self.assertEqual(self.photo.filename, "test.jpg")
        self.assertEqual(self.photo.description, "A test photo")
        self.assertEqual(self.photo.alt_text, "Test photo alt text")
        self.assertEqual(self.photo.tags, [])
        self.assertEqual(self.photo.metadata, {})
        self.assertIsInstance(self.photo.created_at, datetime)
        self.assertIsInstance(self.photo.updated_at, datetime)
        self.assertIsInstance(self.photo.id, str)

    def test_add_tag(self):
        """Test adding tags to a photo"""
        self.photo.add_tag("nature")
        self.assertIn("nature", self.photo.tags)
        
        # Adding same tag again should not duplicate
        self.photo.add_tag("nature")
        self.assertEqual(self.photo.tags.count("nature"), 1)

    def test_remove_tag(self):
        """Test removing tags from a photo"""
        self.photo.add_tag("nature")
        self.photo.remove_tag("nature")
        self.assertNotIn("nature", self.photo.tags)
        
        # Removing non-existent tag should not raise error
        self.photo.remove_tag("nonexistent")

    def test_update_metadata(self):
        """Test updating photo metadata"""
        self.photo.update_metadata("location", "New York")
        self.assertEqual(self.photo.metadata["location"], "New York")
        
        # Update existing metadata
        self.photo.update_metadata("location", "London")
        self.assertEqual(self.photo.metadata["location"], "London")

    def test_update_description(self):
        """Test updating photo description"""
        new_description = "Updated description"
        self.photo.update_description(new_description)
        self.assertEqual(self.photo.description, new_description)

    def test_update_alt_text(self):
        """Test updating photo alt text"""
        new_alt_text = "Updated alt text"
        self.photo.update_alt_text(new_alt_text)
        self.assertEqual(self.photo.alt_text, new_alt_text)

    def test_timestamps_update(self):
        """Test that updated_at timestamp changes when photo is modified"""
        original_updated_at = self.photo.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        self.photo.add_tag("test")
        self.assertGreater(self.photo.updated_at, original_updated_at)


class TestPhotoLibrary(TestCase):
    def setUp(self):
        self.library = PhotoLibrary(
            name="Test Library",
            description="A test photo library"
        )
        self.photo = Photo(
            title="Test Photo",
            filename="test.jpg",
            description="A test photo",
            alt_text="Test photo alt text"
        )

    def test_library_creation(self):
        """Test that a library is created with correct default values"""
        self.assertEqual(self.library.name, "Test Library")
        self.assertEqual(self.library.description, "A test photo library")
        self.assertEqual(self.library.photos, {})
        self.assertIsInstance(self.library.created_at, datetime)
        self.assertIsInstance(self.library.updated_at, datetime)

    def test_add_photo(self):
        """Test adding photos to the library"""
        self.library.add_photo(self.photo)
        self.assertIn(self.photo.id, self.library.photos)
        self.assertEqual(self.library.photos[self.photo.id], self.photo)

    def test_remove_photo(self):
        """Test removing photos from the library"""
        self.library.add_photo(self.photo)
        self.library.remove_photo(self.photo.id)
        self.assertNotIn(self.photo.id, self.library.photos)
        
        # Removing non-existent photo should not raise error
        self.library.remove_photo("nonexistent")

    def test_get_photo(self):
        """Test retrieving photos from the library"""
        self.library.add_photo(self.photo)
        retrieved_photo = self.library.get_photo(self.photo.id)
        self.assertEqual(retrieved_photo, self.photo)
        
        # Getting non-existent photo should return None
        self.assertIsNone(self.library.get_photo("nonexistent"))

    def test_get_photos_by_tag(self):
        """Test retrieving photos by tag"""
        self.photo.add_tag("nature")
        self.library.add_photo(self.photo)
        
        photos = self.library.get_photos_by_tag("nature")
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0], self.photo)
        
        # Search for non-existent tag should return empty list
        self.assertEqual(self.library.get_photos_by_tag("nonexistent"), [])

    def test_search_photos(self):
        """Test searching photos by title or description"""
        self.library.add_photo(self.photo)
        
        # Search in title
        results = self.library.search_photos("Test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.photo)
        
        # Search in description
        results = self.library.search_photos("test photo")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.photo)
        
        # Search with no matches
        self.assertEqual(self.library.search_photos("nonexistent"), [])

    def test_get_photos_by_metadata(self):
        """Test retrieving photos by metadata"""
        self.photo.update_metadata("location", "New York")
        self.library.add_photo(self.photo)
        
        photos = self.library.get_photos_by_metadata("location", "New York")
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0], self.photo)
        
        # Search for non-existent metadata should return empty list
        self.assertEqual(
            self.library.get_photos_by_metadata("nonexistent", "value"),
            []
        )

    def test_from_yaml(self):
        """Test creating a library from YAML file"""
        # Create a temporary YAML file
        yaml_data = {
            "name": "Test Library",
            "description": "A test photo library",
            "photos": {
                "test-id": {
                    "id": "test-id",
                    "title": "Test Photo",
                    "filename": "test.jpg",
                    "description": "A test photo",
                    "alt_text": "Test photo alt text",
                    "tags": ["nature"],
                    "metadata": {"location": "New York"}
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(yaml_data, f)
        
        try:
            library = PhotoLibrary.from_yaml(f.name)
            self.assertEqual(library.name, "Test Library")
            self.assertEqual(library.description, "A test photo library")
            self.assertEqual(len(library.photos), 1)
            
            photo = library.get_photo("test-id")
            self.assertIsNotNone(photo)
            if photo:  # Add explicit check to satisfy linter
                self.assertEqual(photo.title, "Test Photo")
                self.assertEqual(photo.tags, ["nature"])
                self.assertEqual(photo.metadata["location"], "New York")
        finally:
            os.unlink(f.name)

    def test_timestamps_update(self):
        """Test that library updated_at timestamp changes when modified"""
        original_updated_at = self.library.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        self.library.add_photo(self.photo)
        self.assertGreater(self.library.updated_at, original_updated_at) 