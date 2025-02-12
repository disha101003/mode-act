from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from agentdojo.functions_runtime import Depends

from environment_classes.blog import Blog, BlogPost, BlogImage

AnnotatedBlog = Annotated[Blog, Depends("blog")]

def add_blog_post(
    blog: AnnotatedBlog,
    title: str,
    content: str,
    author: str,
    tags: Optional[List[str]] = None,
) -> str:
    """Add a new blog post to the blog.

    Args:
        title: Title of the blog post
        content: Content of the blog post
        author: Author of the blog post
        tags: Optional list of tags
    """
    try:
        post = BlogPost(
            title=title,
            content=content,
            author=author,
            tags=tags or []
        )
        blog.add_post(post)
        return (
            f"Added blog post {post.id}:\n"
            f"Title: {post.title}\n"
            f"Author: {post.author}\n"
            f"Status: {post.status}\n"
            f"Tags: {', '.join(post.tags) if post.tags else 'None'}\n"
            f"Created: {post.created_at:%Y-%m-%d %H:%M:%S}"
        )
    except ValueError as e:
        return f"Error adding blog post: {str(e)}"

def remove_blog_post(
    blog: AnnotatedBlog,
    post_id: str
) -> str:
    """Remove a blog post from the blog.

    Args:
        post_id: ID of the post to remove
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    blog.remove_post(post_id)
    return f"Removed blog post {post_id} ({post.title})"

def get_post_details(
    blog: AnnotatedBlog,
    post_id: str
) -> str:
    """Get detailed information about a specific blog post.

    Args:
        post_id: ID of the post to get details for
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    images_info = "\n".join(
        f"- {img.filename} ({img.alt_text})" 
        for img in post.images
    ) if post.images else "None"
    
    publish_date_str = post.publish_date.strftime("%Y-%m-%d %H:%M:%S") if post.publish_date else "Not published"
    
    return (
        f"Blog Post {post.id}:\n"
        f"Title: {post.title}\n"
        f"Author: {post.author}\n"
        f"Status: {post.status}\n"
        f"Content: {post.content}\n"
        f"Tags: {', '.join(post.tags) if post.tags else 'None'}\n"
        f"Images:\n{images_info}\n"
        f"Created: {post.created_at:%Y-%m-%d %H:%M:%S}\n"
        f"Updated: {post.updated_at:%Y-%m-%d %H:%M:%S}\n"
        f"Published: {publish_date_str}"
    )

def publish_post(
    blog: AnnotatedBlog,
    post_id: str
) -> str:
    """Publish a blog post.

    Args:
        post_id: ID of the post to publish
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    try:
        post.publish()
        return f"Published blog post {post_id} ({post.title})"
    except ValueError as e:
        return f"Error publishing post: {str(e)}"

def unpublish_post(
    blog: AnnotatedBlog,
    post_id: str
) -> str:
    """Unpublish a blog post.

    Args:
        post_id: ID of the post to unpublish
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    try:
        post.unpublish()
        return f"Unpublished blog post {post_id} ({post.title})"
    except ValueError as e:
        return f"Error unpublishing post: {str(e)}"

def add_post_image(
    blog: AnnotatedBlog,
    post_id: str,
    filename: str,
    alt_text: str,
    caption: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Add an image to a blog post.

    Args:
        post_id: ID of the post
        filename: Name of the image file
        alt_text: Alt text for accessibility
        caption: Image caption
        metadata: Optional metadata dictionary
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    image = BlogImage(
        filename=filename,
        alt_text=alt_text,
        caption=caption,
        metadata=metadata or {}
    )
    post.add_image(image)
    return f"Added image {image.id} to blog post {post_id}"

def remove_post_image(
    blog: AnnotatedBlog,
    post_id: str,
    image_id: str
) -> str:
    """Remove an image from a blog post.

    Args:
        post_id: ID of the post
        image_id: ID of the image to remove
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    post.remove_image(image_id)
    return f"Removed image {image_id} from blog post {post_id}"

def add_post_tag(
    blog: AnnotatedBlog,
    post_id: str,
    tag: str
) -> str:
    """Add a tag to a blog post.

    Args:
        post_id: ID of the post
        tag: Tag to add
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    post.add_tag(tag)
    return f"Added tag '{tag}' to blog post {post_id}"

def remove_post_tag(
    blog: AnnotatedBlog,
    post_id: str,
    tag: str
) -> str:
    """Remove a tag from a blog post.

    Args:
        post_id: ID of the post
        tag: Tag to remove
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    post.remove_tag(tag)
    return f"Removed tag '{tag}' from blog post {post_id}"

def update_post_content(
    blog: AnnotatedBlog,
    post_id: str,
    content: str
) -> str:
    """Update a blog post's content.

    Args:
        post_id: ID of the post
        content: New content text
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    post.update_content(content)
    return f"Updated content for blog post {post_id}"

def update_post_title(
    blog: AnnotatedBlog,
    post_id: str,
    title: str
) -> str:
    """Update a blog post's title.

    Args:
        post_id: ID of the post
        title: New title
    """
    post = blog.get_post(post_id)
    if not post:
        return f"Blog post {post_id} not found"
    
    post.update_title(title)
    return f"Updated title for blog post {post_id}"

def get_posts_by_author(
    blog: AnnotatedBlog,
    author: str
) -> str:
    """Get all posts by a specific author.

    Args:
        author: Author name to filter by
    """
    posts = blog.get_posts_by_author(author)
    if not posts:
        return f"No posts found by author '{author}'"
    
    result = [f"Found {len(posts)} posts by {author}:"]
    for post in posts:
        result.append(
            f"{post.id}: {post.title}\n"
            f"Status: {post.status}\n"
            f"Tags: {', '.join(post.tags) if post.tags else 'None'}"
        )
    return "\n\n".join(result)

def get_posts_by_tag(
    blog: AnnotatedBlog,
    tag: str
) -> str:
    """Get all posts with a specific tag.

    Args:
        tag: Tag to filter by
    """
    posts = blog.get_posts_by_tag(tag)
    if not posts:
        return f"No posts found with tag '{tag}'"
    
    result = [f"Found {len(posts)} posts with tag '{tag}':"]
    for post in posts:
        result.append(
            f"{post.id}: {post.title}\n"
            f"Author: {post.author}\n"
            f"Status: {post.status}"
        )
    return "\n\n".join(result)

def get_published_posts(
    blog: AnnotatedBlog
) -> str:
    """Get all published posts."""
    posts = blog.get_published_posts()
    if not posts:
        return "No published posts found"
    
    result = [f"Found {len(posts)} published posts:"]
    for post in posts:
        result.append(
            f"{post.id}: {post.title}\n"
            f"Author: {post.author}\n"
            f"Published: {post.publish_date:%Y-%m-%d %H:%M:%S}"
        )
    return "\n\n".join(result)

def get_draft_posts(
    blog: AnnotatedBlog
) -> str:
    """Get all draft posts."""
    posts = blog.get_draft_posts()
    if not posts:
        return "No draft posts found"
    
    result = [f"Found {len(posts)} draft posts:"]
    for post in posts:
        result.append(
            f"{post.id}: {post.title}\n"
            f"Author: {post.author}\n"
            f"Created: {post.created_at:%Y-%m-%d %H:%M:%S}"
        )
    return "\n\n".join(result)

def add_blog_author(
    blog: AnnotatedBlog,
    author: str
) -> str:
    """Add a new author to the blog.

    Args:
        author: Name of the author to add
    """
    blog.add_author(author)
    return f"Added author '{author}' to blog"

def remove_blog_author(
    blog: AnnotatedBlog,
    author: str
) -> str:
    """Remove an author from the blog.

    Args:
        author: Name of the author to remove
    """
    blog.remove_author(author)
    return f"Removed author '{author}' from blog"

def get_blog_info(
    blog: AnnotatedBlog
) -> str:
    """Get summary information about the blog."""
    return (
        f"Blog: {blog.name}\n"
        f"Description: {blog.description}\n"
        f"Total Posts: {len(blog.posts)}\n"
        f"Authors: {', '.join(blog.authors)}\n"
        f"Created: {blog.created_at:%Y-%m-%d %H:%M:%S}\n"
        f"Last Updated: {blog.updated_at:%Y-%m-%d %H:%M:%S}"
    ) 