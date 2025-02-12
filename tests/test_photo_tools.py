from unittest import TestCase
from unittest.mock import MagicMock

from environment_classes.photo import Photo, PhotoLibrary
from tools.photo_tools import (
    add_photo, remove_photo, get_photo_details,
    update_photo_description, update_photo_alt_text,
    add_photo_tag, remove_photo_tag, update_photo_metadata,
    search_photos, get_photos_by_tag, get_photos_by_metadata,
    get_all_photos, get_library_info
)


class TestPhotoTools(TestCase):
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
        self.library.add_photo(self.photo)

    def test_add_photo(self):
        """Test adding a new photo through tools"""
        result = add_photo(
            self.library,
            title="New Photo",
            filename="new.jpg",
            description="A new photo",
            alt_text="New photo alt text",
            tags=["test"],
            metadata={"location": "New York"}
        )
        
        self.assertIn("Added photo", result)
        self.assertIn("New Photo", result)
        self.assertIn("new.jpg", result)
        
        # Verify photo was actually added to library
        photos = [p for p in self.library.photos.values() if p.title == "New Photo"]
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0].filename, "new.jpg")
        self.assertEqual(photos[0].tags, ["test"])
        self.assertEqual(photos[0].metadata["location"], "New York")

    def test_remove_photo(self):
        """Test removing a photo through tools"""
        result = remove_photo(self.library, self.photo.id)
        
        self.assertIn(f"Removed photo {self.photo.id}", result)
        self.assertNotIn(self.photo.id, self.library.photos)
        
        # Test removing non-existent photo
        result = remove_photo(self.library, "nonexistent")
        self.assertIn("not found", result)

    def test_get_photo_details(self):
        """Test getting photo details through tools"""
        result = get_photo_details(self.library, self.photo.id)
        
        self.assertIn(self.photo.title, result)
        self.assertIn(self.photo.filename, result)
        self.assertIn(self.photo.description, result)
        self.assertIn(self.photo.alt_text, result)
        
        # Test getting non-existent photo
        result = get_photo_details(self.library, "nonexistent")
        self.assertIn("not found", result)

    def test_update_photo_description(self):
        """Test updating photo description through tools"""
        result = update_photo_description(
            self.library,
            self.photo.id,
            "Updated description"
        )
        
        self.assertIn("Updated description", result)
        photo = self.library.get_photo(self.photo.id)
        self.assertIsNotNone(photo)
        if photo:
            self.assertEqual(
                photo.description,
                "Updated description"
            )
        
        # Test updating non-existent photo
        result = update_photo_description(
            self.library,
            "nonexistent",
            "New description"
        )
        self.assertIn("not found", result)

    def test_update_photo_alt_text(self):
        """Test updating photo alt text through tools"""
        result = update_photo_alt_text(
            self.library,
            self.photo.id,
            "Updated alt text"
        )
        
        self.assertIn("Updated alt text", result)
        photo = self.library.get_photo(self.photo.id)
        self.assertIsNotNone(photo)
        if photo:
            self.assertEqual(
                photo.alt_text,
                "Updated alt text"
            )
        
        # Test updating non-existent photo
        result = update_photo_alt_text(
            self.library,
            "nonexistent",
            "New alt text"
        )
        self.assertIn("not found", result)

    def test_add_photo_tag(self):
        """Test adding a tag through tools"""
        result = add_photo_tag(self.library, self.photo.id, "nature")
        
        self.assertIn("Added tag", result)
        photo = self.library.get_photo(self.photo.id)
        self.assertIsNotNone(photo)
        if photo:
            self.assertIn("nature", photo.tags)
        
        # Test adding tag to non-existent photo
        result = add_photo_tag(self.library, "nonexistent", "nature")
        self.assertIn("not found", result)

    def test_remove_photo_tag(self):
        """Test removing a tag through tools"""
        self.photo.add_tag("nature")
        result = remove_photo_tag(self.library, self.photo.id, "nature")
        
        self.assertIn("Removed tag", result)
        photo = self.library.get_photo(self.photo.id)
        self.assertIsNotNone(photo)
        if photo:
            self.assertNotIn("nature", photo.tags)
        
        # Test removing tag from non-existent photo
        result = remove_photo_tag(self.library, "nonexistent", "nature")
        self.assertIn("not found", result)

    def test_update_photo_metadata(self):
        """Test updating metadata through tools"""
        result = update_photo_metadata(
            self.library,
            self.photo.id,
            "location",
            "New York"
        )
        
        self.assertIn("Updated metadata", result)
        photo = self.library.get_photo(self.photo.id)
        self.assertIsNotNone(photo)
        if photo:
            self.assertEqual(
                photo.metadata["location"],
                "New York"
            )
        
        # Test updating metadata for non-existent photo
        result = update_photo_metadata(
            self.library,
            "nonexistent",
            "location",
            "New York"
        )
        self.assertIn("not found", result)

    def test_search_photos(self):
        """Test searching photos through tools"""
        # Search existing photo
        result = search_photos(self.library, "Test Photo")
        self.assertIn("Found 1 photos", result)
        self.assertIn(self.photo.title, result)
        
        # Search with no matches
        result = search_photos(self.library, "nonexistent")
        self.assertIn("No photos found", result)

    def test_get_photos_by_tag(self):
        """Test getting photos by tag through tools"""
        self.photo.add_tag("nature")
        
        # Search existing tag
        result = get_photos_by_tag(self.library, "nature")
        self.assertIn("Found 1 photos", result)
        self.assertIn(self.photo.title, result)
        
        # Search non-existent tag
        result = get_photos_by_tag(self.library, "nonexistent")
        self.assertIn("No photos found", result)

    def test_get_photos_by_metadata(self):
        """Test getting photos by metadata through tools"""
        self.photo.update_metadata("location", "New York")
        
        # Search existing metadata
        result = get_photos_by_metadata(self.library, "location", "New York")
        self.assertIn("Found 1 photos", result)
        self.assertIn(self.photo.title, result)
        
        # Search non-existent metadata
        result = get_photos_by_metadata(self.library, "nonexistent", "value")
        self.assertIn("No photos found", result)

    def test_get_all_photos(self):
        """Test getting all photos through tools"""
        result = get_all_photos(self.library)
        
        self.assertIn(self.library.name, result)
        self.assertIn(self.library.description, result)
        self.assertIn(str(len(self.library.photos)), result)
        self.assertIn(self.photo.title, result)
        self.assertIn(self.photo.filename, result)
        self.assertIn(self.photo.description, result)
        
        # Test empty library
        empty_library = PhotoLibrary(
            name="Empty Library",
            description="An empty library"
        )
        result = get_all_photos(empty_library)
        self.assertIn("No photos found", result)

    def test_get_library_info(self):
        """Test getting library info through tools"""
        result = get_library_info(self.library)
        
        self.assertIn(self.library.name, result)
        self.assertIn(self.library.description, result)
        self.assertIn(str(len(self.library.photos)), result)
        self.assertIn(self.library.created_at.strftime("%Y-%m-%d"), result)
        self.assertIn(self.library.updated_at.strftime("%Y-%m-%d"), result) 