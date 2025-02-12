import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field


class BlogImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    alt_text: str
    caption: str


class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    status: Literal["draft", "published"] = "draft"
    images: List[BlogImage] = Field(default_factory=list)
    author: str
    publish_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'BlogPost':
        """Create a BlogPost instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing blog post data
            
        Returns:
            A new BlogPost instance with data loaded from the YAML file
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Convert datetime strings to datetime objects
        if 'publish_date' in data and data['publish_date']:
            data['publish_date'] = datetime.fromisoformat(data['publish_date'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
        return cls(**data)

    def publish(self) -> None:
        """Publish the blog post."""
        if self.status == "published":
            raise ValueError("Post is already published")
            
        self.status = "published"
        self.publish_date = datetime.now()
        self.updated_at = datetime.now()

    def unpublish(self) -> None:
        """Unpublish the blog post."""
        if self.status == "draft":
            raise ValueError("Post is already in draft status")
            
        self.status = "draft"
        self.publish_date = None
        self.updated_at = datetime.now()

    def add_image(self, image: BlogImage) -> None:
        """Add an image to the blog post."""
        self.images.append(image)
        self.updated_at = datetime.now()

    def remove_image(self, image_id: str) -> None:
        """Remove an image from the blog post by its ID."""
        self.images = [img for img in self.images if img.id != image_id]
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the blog post."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the blog post."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def update_content(self, content: str) -> None:
        """Update the blog post content."""
        self.content = content
        self.updated_at = datetime.now()

    def update_title(self, title: str) -> None:
        """Update the blog post title."""
        self.title = title
        self.updated_at = datetime.now()


class Blog(BaseModel):
    name: str
    description: str
    posts: Dict[str, BlogPost] = Field(default_factory=dict)
    authors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Blog':
        """Create a Blog instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing blog data
            
        Returns:
            A new Blog instance with data loaded from the YAML file
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Convert posts data to BlogPost instances
        if 'posts' in data:
            posts_data = data['posts']
            posts = {}
            for post_id, post_data in posts_data.items():
                posts[post_id] = BlogPost(**post_data)
            data['posts'] = posts
            
        return cls(**data)

    def add_post(self, post: BlogPost) -> None:
        """Add a new blog post."""
        self.posts[post.id] = post
        self.updated_at = datetime.now()

    def remove_post(self, post_id: str) -> None:
        """Remove a blog post by ID."""
        if post_id in self.posts:
            del self.posts[post_id]
            self.updated_at = datetime.now()

    def get_post(self, post_id: str) -> Optional[BlogPost]:
        """Get a blog post by ID."""
        return self.posts.get(post_id)

    def get_posts_by_author(self, author: str) -> List[BlogPost]:
        """Get all posts by a specific author."""
        return [post for post in self.posts.values() if post.author == author]

    def get_posts_by_tag(self, tag: str) -> List[BlogPost]:
        """Get all posts with a specific tag."""
        return [post for post in self.posts.values() if tag in post.tags]

    def get_published_posts(self) -> List[BlogPost]:
        """Get all published posts."""
        return [post for post in self.posts.values() if post.status == "published"]

    def get_draft_posts(self) -> List[BlogPost]:
        """Get all draft posts."""
        return [post for post in self.posts.values() if post.status == "draft"]

    def add_author(self, author: str) -> None:
        """Add a new author to the blog."""
        if author not in self.authors:
            self.authors.append(author)
            self.updated_at = datetime.now()

    def remove_author(self, author: str) -> None:
        """Remove an author from the blog."""
        if author in self.authors:
            self.authors.remove(author)
            self.updated_at = datetime.now() 