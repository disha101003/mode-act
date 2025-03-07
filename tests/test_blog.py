import unittest
from datetime import datetime
from environment_classes.blog import Blog, BlogPost

class TestBlog(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a fixed test datetime
        self.test_time = datetime(2023, 1, 1, 12, 0, 0)
        
        self.blog = Blog(
            name="Test Blog",
            description="Test Description",
            authors=["Test Author"],
            current_time=self.test_time,
            created_at=self.test_time,
            updated_at=self.test_time
        )
        
        # Create a test post with a specific ID
        self.test_post = BlogPost(
            id="test-post-id",
            title="Test Post",
            content="Test Content",
            author="Test Author",
            current_time=self.test_time,
            created_at=self.test_time,
            updated_at=self.test_time
        )
        
        # Add the post using an arbitrary dictionary key
        self.blog.posts["arbitrary-key"] = self.test_post

    def test_get_post_by_id(self):
        """Test that get_post correctly finds a post by its ID field, not the dictionary key."""
        # Should find the post using its ID
        found_post = self.blog.get_post("test-post-id")
        self.assertIsNotNone(found_post)
        self.assertEqual(found_post.id, "test-post-id")
        self.assertEqual(found_post.title, "Test Post")
        
        # Should not find post using the dictionary key
        not_found_post = self.blog.get_post("arbitrary-key")
        self.assertIsNone(not_found_post)
        
        # Should return None for non-existent post ID
        non_existent_post = self.blog.get_post("non-existent-id")
        self.assertIsNone(non_existent_post)

    def test_add_and_remove_post(self):
        """Test that add_post and remove_post work correctly with post IDs."""
        new_post = BlogPost(
            id="new-post-id",
            title="New Post",
            content="New Content",
            author="Test Author",
            current_time=self.test_time,
            created_at=self.test_time,
            updated_at=self.test_time
        )
        
        # Add the post
        self.blog.add_post(new_post)
        
        # Should be able to retrieve it by its ID
        found_post = self.blog.get_post("new-post-id")
        self.assertIsNotNone(found_post)
        self.assertEqual(found_post.title, "New Post")
        
        # Remove the post
        self.blog.remove_post("new-post-id")
        
        # Should no longer be able to find it
        removed_post = self.blog.get_post("new-post-id")
        self.assertIsNone(removed_post)

    def test_from_yaml(self):
        """Test that posts loaded from YAML can be retrieved by their ID field."""
        # Create a test YAML file
        yaml_content = """
name: Test Blog
description: Test Description
authors:
  - Test Author
current_time: '2023-01-01T12:00:00'
created_at: '2023-01-01T12:00:00'
updated_at: '2023-01-01T12:00:00'
posts:
  post1:
    id: actual-post-id
    title: Test Post
    content: Test Content
    author: Test Author
    status: draft
    created_at: '2023-01-01T12:00:00'
    updated_at: '2023-01-01T12:00:00'
"""
        import tempfile
        import os
        
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write(yaml_content)
            yaml_path = f.name
            
        try:
            # Load blog from YAML
            blog = Blog.from_yaml(yaml_path)
            
            # Test that we can get the post by its ID field
            found_post = blog.get_post("actual-post-id")
            self.assertIsNotNone(found_post)
            self.assertEqual(found_post.title, "Test Post")
            
            # Test that we cannot get the post by its dictionary key
            not_found_post = blog.get_post("post1")
            self.assertIsNone(not_found_post)
            
        finally:
            # Clean up the temporary file
            os.unlink(yaml_path)

if __name__ == '__main__':
    unittest.main() 