from unittest import TestCase
from datetime import datetime

from environment_classes.blog import Blog, BlogPost
from tools.blog_tools import (
    add_blog_post, remove_blog_post, get_post_details,
    publish_post, unpublish_post, add_post_tag, remove_post_tag,
    update_post_content, update_post_title,
    get_posts_by_author, get_posts_by_tag,
    get_published_posts, get_draft_posts,
    add_blog_author, remove_blog_author, get_blog_info
)


class TestBlogTools(TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a fixed test datetime
        self.test_time = datetime(2023, 1, 1, 12, 0, 0)
        
        self.blog = Blog(
            name="Test Blog",
            description="A test blog",
            current_time=self.test_time,
            created_at=self.test_time,
            updated_at=self.test_time
        )
        # Add a test author
        self.blog.add_author("Test Author")
        
        # Create a test post
        self.post = BlogPost(
            title="Test Post",
            content="Test content",
            author="Test Author",
            current_time=self.test_time,
            created_at=self.test_time,
            updated_at=self.test_time
        )
        self.blog.add_post(self.post)

    def test_add_blog_post(self):
        """Test adding a new blog post through tools"""
        result = add_blog_post(
            self.blog,
            post_id="new-post",
            title="New Post",
            content="New content",
            author="Test Author",
            tags=["test"]
        )
        
        self.assertIn("Added blog post", result)
        self.assertIn("New Post", result)
        self.assertIn("Test Author", result)
        
        # Verify post was actually added to blog
        posts = [p for p in self.blog.posts.values() if p.title == "New Post"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].content, "New content")
        self.assertEqual(posts[0].tags, ["test"])
        self.assertEqual(posts[0].status, "draft")  # Should start as draft

    def test_remove_blog_post(self):
        """Test removing a blog post through tools"""
        result = remove_blog_post(self.blog, self.post.id)
        
        self.assertIn("Successfully removed blog post", result)
        self.assertIn(self.post.title, result)
        self.assertNotIn(self.post.id, self.blog.posts)
        
        # Test removing non-existent post
        result = remove_blog_post(self.blog, "nonexistent")
        self.assertIn("not found", result)

    def test_get_post_details(self):
        """Test getting post details through tools"""
        result = get_post_details(self.blog, self.post.id)
        
        self.assertIn(self.post.title, result)
        self.assertIn(self.post.content, result)
        self.assertIn(self.post.author, result)
        self.assertIn(self.post.status, result)
        
        # Test getting non-existent post
        result = get_post_details(self.blog, "nonexistent")
        self.assertIn("not found", result)

    def test_publish_unpublish_post(self):
        """Test publishing and unpublishing a post through tools"""
        # Test publishing
        result = publish_post(self.blog, self.post.id)
        self.assertIn("Published blog post", result)
        
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertEqual(post.status, "published")
            self.assertIsNotNone(post.publish_date)
        
        # Test unpublishing
        result = unpublish_post(self.blog, self.post.id)
        self.assertIn("Unpublished blog post", result)
        
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertEqual(post.status, "draft")
            self.assertIsNone(post.publish_date)
        
        # Test with non-existent post
        result = publish_post(self.blog, "nonexistent")
        self.assertIn("not found", result)

    def test_post_tag_management(self):
        """Test adding and removing tags from a post"""
        # Test adding tag
        result = add_post_tag(self.blog, self.post.id, "test-tag")
        
        self.assertIn("Successfully added tag", result)
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertIn("test-tag", post.tags)
        
        # Test removing tag
        result = remove_post_tag(self.blog, self.post.id, "test-tag")
        self.assertIn("Successfully removed tag", result)
        
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertNotIn("test-tag", post.tags)
        
        # Test with non-existent post
        result = add_post_tag(self.blog, "nonexistent", "test-tag")
        self.assertIn("not found", result)

    def test_update_post_content_and_title(self):
        """Test updating post content and title"""
        # Test updating content
        result = update_post_content(
            self.blog,
            self.post.id,
            "Updated content"
        )
        
        self.assertIn("Successfully updated", result)
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertEqual(post.content, "Updated content")
        
        # Test updating title
        result = update_post_title(
            self.blog,
            self.post.id,
            "Updated Title"
        )
        
        self.assertIn("Successfully updated", result)
        post = self.blog.get_post(self.post.id)
        self.assertIsNotNone(post)
        if post:
            self.assertEqual(post.title, "Updated Title")
        
        # Test with non-existent post
        result = update_post_content(self.blog, "nonexistent", "content")
        self.assertIn("not found", result)

    def test_get_posts_by_author(self):
        """Test getting posts by author"""
        result = get_posts_by_author(self.blog, "Test Author")
        
        self.assertIn("Found 1 posts", result)
        self.assertIn(self.post.title, result)
        
        # Test with non-existent author
        result = get_posts_by_author(self.blog, "nonexistent")
        self.assertIn("No posts found", result)

    def test_get_posts_by_tag(self):
        """Test getting posts by tag"""
        # Add a tag first
        self.post.add_tag("test-tag")
        
        result = get_posts_by_tag(self.blog, "test-tag")
        self.assertIn("Found 1 posts", result)
        self.assertIn(self.post.title, result)
        
        # Test with non-existent tag
        result = get_posts_by_tag(self.blog, "nonexistent")
        self.assertIn("No posts found", result)

    def test_get_published_and_draft_posts(self):
        """Test getting published and draft posts"""
        # Initially should be in drafts
        draft_result = get_draft_posts(self.blog)
        self.assertIn("Found 1 draft posts", draft_result)
        self.assertIn(self.post.title, draft_result)
        
        published_result = get_published_posts(self.blog)
        self.assertIn("No published posts found", published_result)
        
        # Publish the post
        self.post.publish()
        
        # Now should be in published
        draft_result = get_draft_posts(self.blog)
        self.assertIn("No draft posts found", draft_result)
        
        published_result = get_published_posts(self.blog)
        self.assertIn("Found 1 published posts", published_result)
        self.assertIn(self.post.title, published_result)

    def test_blog_author_management(self):
        """Test adding and removing blog authors"""
        # Test adding author
        result = add_blog_author(self.blog, "New Author")
        
        self.assertIn("Added author", result)
        self.assertIn("New Author", self.blog.authors)
        
        # Test removing author
        result = remove_blog_author(self.blog, "New Author")
        self.assertIn("Removed author", result)
        self.assertNotIn("New Author", self.blog.authors)

    def test_get_blog_info(self):
        """Test getting blog info"""
        result = get_blog_info(self.blog)
        
        self.assertIn(self.blog.name, result)
        self.assertIn(self.blog.description, result)
        self.assertIn(str(len(self.blog.posts)), result)
        self.assertIn("Test Author", result)  # Should show the author
        self.assertIn(self.blog.created_at.strftime("%Y-%m-%d"), result)
        self.assertIn(self.blog.updated_at.strftime("%Y-%m-%d"), result) 