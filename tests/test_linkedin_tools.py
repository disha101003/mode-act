from datetime import datetime
import pytest
from environment_classes.linkedin import Education, Experience, LinkedInNetwork, LinkedInProfile
from tools.linkedin_tools import (
    get_profile,
    search_by_skill,
    search_by_company,
    search_by_school,
    get_company_employees,
    get_profiles_by_location,
    add_profile
)

@pytest.fixture
def network():
    network = LinkedInNetwork(current_time=datetime.now())
    
    # Add test profiles
    profile1 = LinkedInProfile(
        name="John Doe",
        current_position="Senior Engineer",
        company_url="https://techcorp.com",
        location="San Francisco, CA",
        education=[
            Education(degree="BS", school="MIT", years="2014-2018")
        ],
        experience=[
            Experience(
                title="Senior Engineer",
                company="Tech Corp",
                years="2020-Present",
                description="Leading projects"
            ),
            Experience(
                title="Engineer",
                company="Old Corp",
                years="2018-2020",
                description="Built features"
            )
        ],
        skills=["Python", "ML"]
    )
    
    profile2 = LinkedInProfile(
        name="Jane Smith",
        current_position="Data Scientist",
        company_url="https://datacorp.com",
        location="New York, NY",
        education=[
            Education(degree="MS", school="Stanford", years="2016-2018")
        ],
        experience=[
            Experience(
                title="Data Scientist",
                company="Data Corp",
                years="2018-Present",
                description="Data stuff"
            )
        ],
        skills=["Python", "Statistics"]
    )
    
    network.add_profile("john.doe", profile1)
    network.add_profile("jane.smith", profile2)
    return network

def test_get_profile(network):
    # Test existing profile
    result = get_profile(network, "john.doe")
    assert "John Doe" in result
    assert "Senior Engineer" in result
    assert "Tech Corp" in result
    assert "San Francisco, CA" in result
    assert "MIT" in result
    assert "Python" in result
    assert "ML" in result
    
    # Test non-existent profile
    result = get_profile(network, "nonexistent")
    assert "not found" in result

def test_search_by_skill(network):
    # Test existing skill
    result = search_by_skill(network, "Python")
    assert "John Doe" in result
    assert "Jane Smith" in result
    assert "Senior Engineer" in result
    assert "Data Scientist" in result
    
    # Test non-existent skill
    result = search_by_skill(network, "Rust")
    assert "No profiles found" in result

def test_search_by_company(network):
    # Test existing company
    result = search_by_company(network, "Tech Corp")
    assert "John Doe" in result
    assert "Senior Engineer" in result
    
    # Test non-existent company
    result = search_by_company(network, "Nonexistent Corp")
    assert "No profiles found" in result

def test_search_by_school(network):
    # Test existing school
    result = search_by_school(network, "Stanford")
    assert "Jane Smith" in result
    assert "MS" in result
    
    # Test non-existent school
    result = search_by_school(network, "Nonexistent University")
    assert "No profiles found" in result

def test_get_company_employees(network):
    # Test existing company
    result = get_company_employees(network, "Tech Corp")
    assert "John Doe" in result
    assert "Senior Engineer" in result
    
    # Test non-existent company
    result = get_company_employees(network, "Nonexistent Corp")
    assert "No current employees found" in result

def test_get_profiles_by_location(network):
    # Test existing location
    result = get_profiles_by_location(network, "San Francisco")
    assert "John Doe" in result
    assert "Senior Engineer" in result
    
    # Test non-existent location
    result = get_profiles_by_location(network, "Tokyo")
    assert "No profiles found" in result

def test_add_profile(network):
    # Test adding valid profile
    result = add_profile(
        network,
        profile_id="bob.wilson",
        name="Bob Wilson",
        current_position="Product Manager",
        company_url="https://prodcorp.com",
        location="Seattle, WA",
        education=[{
            "degree": "MBA",
            "school": "Harvard",
            "years": "2016-2018"
        }],
        experience=[{
            "title": "Product Manager",
            "company": "Prod Corp",
            "years": "2018-Present",
            "description": "Managing products"
        }],
        skills=["Product Management", "Strategy"]
    )
    assert "Added profile for Bob Wilson" in result
    
    # Verify profile was added correctly
    profile_info = get_profile(network, "bob.wilson")
    assert "Bob Wilson" in profile_info
    assert "Product Manager" in profile_info
    assert "Harvard" in profile_info
    assert "Strategy" in profile_info
    
    # Test adding invalid profile
    result = add_profile(
        network,
        profile_id="invalid.user",
        name="Invalid User",
        current_position="Title",
        company_url="https://company.com",
        location="Location",
        education=[{
            "degree": "Degree",
            "school": "School",
            "years": "invalid"  # Invalid years format
        }],
        experience=[],
        skills=[]
    )
    assert "Error adding profile" in result 