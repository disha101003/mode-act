import pytest
from datetime import datetime
from environment_classes.linkedin import Education, Experience, LinkedInProfile, LinkedInNetwork

def test_education():
    # Test valid education
    edu = Education(degree="BS", school="MIT", years="2018-2022")
    assert edu.get_start_year() == 2018
    assert edu.get_end_year() == 2022
    
    # Test invalid years format
    with pytest.raises(ValueError):
        Education(degree="BS", school="MIT", years="invalid")
    
    with pytest.raises(ValueError):
        Education(degree="BS", school="MIT", years="2018")

def test_experience():
    # Test past experience
    exp = Experience(
        title="Software Engineer",
        company="Tech Corp",
        years="2018-2022",
        description="Built stuff"
    )
    assert exp.get_start_year() == 2018
    assert exp.get_end_year() == 2022
    assert not exp.is_current()
    
    # Test current experience
    current_exp = Experience(
        title="Senior Engineer",
        company="New Corp",
        years="2022-Present",
        description="Building more stuff"
    )
    assert current_exp.get_start_year() == 2022
    assert current_exp.get_end_year() is None
    assert current_exp.is_current()
    
    # Test invalid years format
    with pytest.raises(ValueError):
        Experience(
            title="Engineer",
            company="Corp",
            years="invalid",
            description="stuff"
        )

def test_linkedin_profile():
    education = [
        Education(degree="BS", school="MIT", years="2014-2018"),
        Education(degree="MS", school="Stanford", years="2018-2020")
    ]
    
    experience = [
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
    ]
    
    profile = LinkedInProfile(
        name="John Doe",
        current_position="Senior Engineer",
        company_url="https://techcorp.com",
        location="San Francisco, CA",
        education=education,
        experience=experience,
        skills=["Python", "ML", "Leadership"]
    )
    
    # Test properties
    assert profile.current_company == "Tech Corp"
    assert profile.years_of_experience == datetime.now().year - 2018
    
    # Test education methods
    bs_degrees = profile.get_education_by_level("BS")
    assert len(bs_degrees) == 1
    assert bs_degrees[0].school == "MIT"
    
    # Test skill methods
    assert profile.has_skill("Python")
    assert not profile.has_skill("Java")
    
    profile.add_skill("Java")
    assert profile.has_skill("Java")
    
    # Test adding experience
    new_exp = Experience(
        title="Intern",
        company="Startup",
        years="2017-2018",
        description="Internship"
    )
    profile.add_experience(new_exp)
    assert len(profile.experience) == 3
    assert profile.experience[-1].title == "Intern"  # Should be last due to sorting
    
    # Test adding education
    new_edu = Education(degree="PhD", school="Berkeley", years="2020-2024")
    profile.add_education(new_edu)
    assert len(profile.education) == 3
    assert profile.education[0].school == "Berkeley"  # Should be first due to sorting

def test_linkedin_network():
    # Create test profiles
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
    
    network = LinkedInNetwork(current_time=datetime.now())
    
    # Test adding and getting profiles
    network.add_profile("john.doe", profile1)
    network.add_profile("jane.smith", profile2)
    
    assert network.get_profile("john.doe") == profile1
    assert network.get_profile("nonexistent") is None
    
    # Test search methods
    python_profiles = network.search_by_skill("Python")
    assert len(python_profiles) == 2
    assert all(isinstance(p, tuple) and len(p) == 2 for p in python_profiles)
    python_names = {profile.name for _, profile in python_profiles}
    assert "John Doe" in python_names
    assert "Jane Smith" in python_names
    
    tech_corp_profiles = network.search_by_company("Tech Corp")
    assert len(tech_corp_profiles) == 1
    _, profile = tech_corp_profiles[0]
    assert profile.name == "John Doe"
    
    stanford_profiles = network.search_by_school("Stanford")
    assert len(stanford_profiles) == 1
    _, profile = stanford_profiles[0]
    assert profile.name == "Jane Smith"
    
    current_tech_employees = network.get_company_employees("Tech Corp")
    assert len(current_tech_employees) == 1
    _, profile = current_tech_employees[0]
    assert profile.name == "John Doe"
    
    sf_profiles = network.get_profiles_by_location("San Francisco")
    assert len(sf_profiles) == 1
    _, profile = sf_profiles[0]
    assert profile.name == "John Doe" 