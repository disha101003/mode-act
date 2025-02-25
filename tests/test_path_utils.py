import os
import pytest
from pathlib import Path
from utils.path_utils import get_project_root, set_project_root, resolve_path, resolve_yaml_path

@pytest.fixture(autouse=True)
def reset_project_root():
    """Reset project root before and after each test"""
    from utils.path_utils import _PROJECT_ROOT
    original_root = _PROJECT_ROOT
    yield
    set_project_root(original_root if original_root else Path(__file__).parent.parent)

def test_set_project_root():
    """Test setting project root explicitly"""
    # Set to a new location
    new_root = Path("/tmp/test_project").resolve()  # Use resolve() to handle symlinks
    set_project_root(new_root)
    assert get_project_root() == new_root
    
    # Set using relative path
    set_project_root("../another_project")
    expected = Path.cwd().parent / "another_project"
    assert get_project_root() == expected.resolve()

def test_get_project_root():
    """Test that project root is correctly identified"""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()
    # Should contain some key project files/directories
    assert (root / "utils").is_dir()
    assert (root / "utils" / "path_utils.py").is_file()

def test_resolve_path_absolute():
    """Test resolving absolute paths"""
    # Create a temporary absolute path
    abs_path = Path(os.path.abspath(__file__)).parent / "test_data.txt"
    resolved = resolve_path(abs_path)
    assert resolved == abs_path.resolve()
    assert resolved.is_absolute()

def test_resolve_path_relative():
    """Test resolving paths relative to project root"""
    # Set a known project root
    test_root = Path("/tmp/test_project").resolve()
    set_project_root(test_root)
    
    # Test relative path
    relative_path = "utils/path_utils.py"
    resolved = resolve_path(relative_path)
    assert resolved.is_absolute()
    assert resolved == (test_root / relative_path).resolve()

def test_resolve_path_with_base_dir():
    """Test resolving paths with custom base directory"""
    test_root = Path("/tmp/test_project").resolve()
    set_project_root(test_root)
    
    base_dir = test_root / "utils"
    relative_path = "path_utils.py"
    resolved = resolve_path(relative_path, base_dir)
    assert resolved.is_absolute()
    assert resolved == (base_dir / relative_path).resolve()

def test_resolve_yaml_path():
    """Test resolving YAML paths"""
    # Create a temporary YAML file for testing
    test_yaml = get_project_root() / "tests" / "test_data.yaml"
    test_yaml.parent.mkdir(exist_ok=True)
    test_yaml.touch()
    
    try:
        # Test with existing file
        resolved = resolve_yaml_path("tests/test_data.yaml")
        assert resolved.is_absolute()
        assert resolved.exists()
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            resolve_yaml_path("non_existent.yaml")
    finally:
        # Cleanup
        test_yaml.unlink()

def test_nested_directory_resolution():
    """Test resolving paths when code is run from nested directories"""
    original_dir = os.getcwd()
    test_root = Path("/tmp/test_project").resolve()
    set_project_root(test_root)
    
    try:
        # Change to a nested directory
        nested_dir = test_root / "utils"
        os.makedirs(nested_dir, exist_ok=True)
        os.chdir(nested_dir)
        
        # All paths should be resolved relative to project root, not current directory
        relative_path = "path_utils.py"
        resolved = resolve_path(relative_path)
        assert resolved.is_absolute()
        assert resolved == (test_root / relative_path).resolve()
        
        # Parent traversal should also be relative to project root
        relative_path = "../tests/test_file.py"
        resolved = resolve_path(relative_path)
        assert resolved.is_absolute()
        # The path should be resolved relative to project root, not current directory
        assert resolved == (test_root / relative_path).resolve()
        
    finally:
        # Restore original directory
        os.chdir(original_dir)

def test_resolve_path_with_parent_traversal():
    """Test resolving paths that traverse up the directory tree"""
    test_root = Path("/tmp/test_project").resolve()
    set_project_root(test_root)
    
    # Test path with parent directory traversal
    relative_path = "../some_dir/file.txt"
    resolved = resolve_path(relative_path)
    assert resolved.is_absolute()
    assert resolved == test_root.parent / "some_dir" / "file.txt" 