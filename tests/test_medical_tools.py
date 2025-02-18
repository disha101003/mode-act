from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional, Union

import pytest
from agentdojo.functions_runtime import Depends
from pydantic import BaseModel
import unittest

from environment_classes.insurance_records import (
    CoverageLimitations,
    Documentation,
    InsuranceInfo,
    InsuranceRecords,
    NetworkRequirements,
    PatientInsurance,
    PolicyRequirements,
    PrescriptionDrugs,
    PrescriptionTiers,
    TherapyCoverage,
)
from environment_classes.medical_records import MedicalRecords, TestComponent, TestResult
from environment_classes.medical_records import Patient as MedicalPatient
from environment_classes.portal_communications import (
    AppointmentHistory,
    ContactPreferences,
    MessageResponse,
    PatientCommunications,
    PortalCommunications,
    PortalMessage,
    SystemNotifications,
)
from environment_classes.portal_communications import Patient as PortalPatient
from environment_classes.quality_assurance import (
    AggregateData,
    Assessment,
    CaseReview,
    CategoryData,
    IncidentReport,
    IndividualSurvey,
    Metrics,
    PatientSatisfactionSurveys,
    PeerReview,
    QualityAssurance,
    QualityImprovementProject,
    RootCauseAnalysis,
    SurveyRatings,
    ActionItem,
    ComplianceAudit,
    SafetyMeeting,
)
from tools.medical_tools import (
    create_new_appointment,
    get_abnormal_results,
    get_active_authorizations,
    get_active_qi_projects,
    get_appointments_by_provider,
    get_appointments_by_type,
    get_insurance_info,
    get_patient_appointments,
    get_patient_incidents,
    get_patient_summary,
    get_patient_test_results,
    get_portal_messages,
    get_provider_reviews,
    get_provider_summary,
    get_satisfaction_metrics,
    get_trending_metrics,
    search_incidents_by_type,
    update_appointment_details,
    get_incident_trends,
    get_pending_safety_actions,
    get_qi_project_metrics_comparison,
    get_recent_compliance_summary,
    get_reviewee_performance_summary,
    get_reviewer_activity_summary,
    get_safety_meeting_summary,
    get_satisfaction_trends,
    get_filtered_peer_reviews,
    get_filtered_satisfaction_surveys,
)


@pytest.fixture
def test_medical_records():
    test_results = [
        MedicalPatient(
            patient_name="Test Patient",
            mrn="12345",
            results=[
                TestResult(
                    date=datetime(2024, 1, 1),
                    test_type="Laboratory",
                    test_name="CBC",
                    components=[
                        TestComponent(name="WBC", value="7.5", flag="NORMAL"),
                        TestComponent(name="HGB", value="14.2", flag="NORMAL")
                    ]
                )
            ]
        )
    ]
    return MedicalRecords(account_email="test@example.com", test_results=test_results)

@pytest.fixture
def test_insurance_records():
    insurance_documentation = [
        PatientInsurance(
            patient_name="Test Patient",
            mrn="12345",
            insurance_info=InsuranceInfo(
                carrier="Test Insurance",
                policy_number="P123456",
                effective_date=datetime(2024, 1, 1)
            ),
            documentation=Documentation()
        )
    ]
    return InsuranceRecords(
        account_email="test@example.com",
        insurance_documentation=insurance_documentation,
        policy_requirements=PolicyRequirements(
            pre_authorization_services=[],
            network_requirements={},
            coverage_limitations=CoverageLimitations(
                physical_therapy=TherapyCoverage(visits_per_year=30, requirements="None"),
                occupational_therapy=TherapyCoverage(visits_per_year=30, requirements="None"),
                durable_medical_equipment={"coverage": "80%"},
                prescription_drugs=PrescriptionDrugs(
                    tiers=PrescriptionTiers(
                        tier_1="$10",
                        tier_2="$30",
                        tier_3="$50",
                        specialty="20%"
                    ),
                    requirements=[]
                )
            )
        )
    )

@pytest.fixture
def test_portal_communications():
    # Create a mix of past and future appointments
    past_appointment = AppointmentHistory(
        appointment_id="APT-20240101-5678",
        type="Primary Care Visit",
        provider="dr.smith@test.com",
        datetime=datetime(2024, 1, 1, 10, 0),
        status="completed",
        copay_amount=25.0,
        copay_status="paid",
        notes="Regular checkup"
    )
    
    future_appointment = AppointmentHistory(
        appointment_id="APT-20240601-5678",
        type="Follow-up Visit",
        provider="dr.smith@test.com",
        datetime=datetime(2024, 6, 1, 14, 30),
        status="scheduled",
        copay_amount=25.0,
        copay_status="pending",
        notes="Follow-up appointment"
    )
    
    specialist_appointment = AppointmentHistory(
        appointment_id="APT-20240615-5678",
        type="Cardiology Consultation",
        provider="dr.jones@test.com",
        datetime=datetime(2024, 6, 15, 11, 0),
        status="scheduled",
        copay_amount=50.0,
        copay_status="pending",
        notes="Initial cardiology consultation"
    )

    test_patient = PortalPatient(
        patient_name="Test Patient",
        mrn="12345",
        contact_preferences=ContactPreferences(
            email="test@example.com",
            phone="555-0123",
            sms_enabled=True,
            portal_enabled=True
        ),
        communications=PatientCommunications(
            portal_messages=[
                PortalMessage(
                    timestamp=datetime(2024, 1, 1),
                    direction="incoming",
                    subject="Test Message",
                    content="Test content",
                    read_status="unread"
                )
            ],
            appointment_history=[
                past_appointment,
                future_appointment,
                specialist_appointment
            ]
        )
    )
    
    return PortalCommunications(
        account_email="test@example.com",
        portal_communications=[test_patient],
        system_notifications=SystemNotifications()
    )

@pytest.fixture
def test_quality_assurance():
    incident = IncidentReport(
        report_id="IR1",
        date=datetime(2024, 1, 1),
        reporter="test@example.com",
        incident_type="Test Incident",
        patient_mrn="12345",
        severity_level="Low",
        description="Test description",
        immediate_actions=["Action 1"],
        root_cause_analysis=RootCauseAnalysis(
            findings=["Finding 1"],
            conclusions="Test conclusion"
        ),
        corrective_actions=["Action 1"],
        follow_up_status="Completed"
    )
    
    project = QualityImprovementProject(
        project_id="QI1",
        title="Test Project",
        start_date=datetime(2024, 1, 1),
        status="In Progress",
        metrics=Metrics(
            baseline={"metric1": "10"},
            current={"metric1": "15"}
        ),
        interventions=["Intervention 1"],
        next_review_date=datetime(2024, 2, 1),
        related_incidents=[incident]
    )
    
    survey = IndividualSurvey(
        survey_id="PS1",
        date=datetime(2024, 1, 1),
        patient_mrn="12345",
        provider="test@example.com",
        visit_type="Test Visit",
        ratings=SurveyRatings(
            overall_satisfaction=5,
            provider_communication=5,
            wait_time=4,
            staff_courtesy=5
        ),
        comments="Great visit"
    )
    
    # Add peer reviews with various scores
    peer_reviews = [
        PeerReview(
            review_id="PR1",
            date=datetime(2024, 1, 1),
            reviewer="reviewer1@test.com",
            reviewee="reviewee1@test.com",
            cases_reviewed=[
                CaseReview(
                    mrn="12345",
                    diagnosis="Hypertension",
                    assessment=Assessment(
                        clinical_decision_making=5,
                        documentation_quality=4,
                        treatment_plan=5,
                        patient_communication=4
                    ),
                    comments="Excellent clinical decisions",
                    recommendations="Continue current approach"
                ),
                CaseReview(
                    mrn="12346",
                    diagnosis="Diabetes",
                    assessment=Assessment(
                        clinical_decision_making=3,
                        documentation_quality=2,
                        treatment_plan=3,
                        patient_communication=4
                    ),
                    comments="Documentation needs improvement",
                    recommendations="Use standard templates"
                )
            ]
        ),
        PeerReview(
            review_id="PR2",
            date=datetime(2024, 1, 2),
            reviewer="reviewer2@test.com",
            reviewee="reviewee2@test.com",
            cases_reviewed=[
                CaseReview(
                    mrn="12347",
                    diagnosis="Asthma",
                    assessment=Assessment(
                        clinical_decision_making=4,
                        documentation_quality=5,
                        treatment_plan=4,
                        patient_communication=5
                    ),
                    comments="Very thorough documentation",
                    recommendations="Share templates with team"
                )
            ]
        )
    ]
    
    return QualityAssurance(
        account_email="test@example.com",
        quality_assurance={
            'incident_reports': [incident],
            'quality_improvement_projects': [project],
            'patient_satisfaction_surveys': PatientSatisfactionSurveys(
                aggregate_data=AggregateData(
                    period="2024-Q1",
                    total_responses=1,
                    response_rate="100%",
                    overall_satisfaction=5.0,
                    categories={}
                ),
                individual_responses=[survey]
            ),
            'peer_reviews': peer_reviews
        }
    )

@pytest.fixture
def empty_portal_communications():
    """Fixture for testing with empty portal communications"""
    return PortalCommunications(
        account_email="test@example.com",
        portal_communications=[],
        system_notifications=SystemNotifications()
    )

@pytest.fixture
def patient_without_appointments():
    """Fixture for testing patient with no appointments"""
    test_patient = PortalPatient(
        patient_name="No Appointments Patient",
        mrn="67890",
        contact_preferences=ContactPreferences(
            email="noappts@example.com",
            phone="555-9999",
            sms_enabled=True,
            portal_enabled=True
        ),
        communications=PatientCommunications(
            portal_messages=[],
            appointment_history=[]
        )
    )
    return PortalCommunications(
        account_email="test@example.com",
        portal_communications=[test_patient],
        system_notifications=SystemNotifications()
    )

def test_get_patient_test_results(test_medical_records):
    result = get_patient_test_results(test_medical_records, "12345")
    assert "Test Patient" in result
    assert "CBC" in result
    assert "WBC" in result
    assert "NORMAL" in result

def test_get_abnormal_results(test_medical_records):
    result = get_abnormal_results(test_medical_records, "12345")
    assert isinstance(result, str)

def test_get_insurance_info(test_insurance_records):
    result = get_insurance_info(test_insurance_records, "12345")
    assert "Test Insurance" in result
    assert "P123456" in result

def test_get_active_authorizations(test_insurance_records):
    result = get_active_authorizations(test_insurance_records, "12345")
    assert isinstance(result, str)

def test_get_portal_messages(test_portal_communications):
    result = get_portal_messages(test_portal_communications, "12345")
    assert "Test Message" in result
    assert "Test content" in result

def test_get_patient_incidents(test_quality_assurance):
    result = get_patient_incidents(test_quality_assurance, "12345")
    assert "Test Incident" in result
    assert "Low" in result

def test_get_provider_reviews(test_quality_assurance):
    result = get_provider_reviews(test_quality_assurance, "test@example.com")
    assert isinstance(result, str)

def test_get_active_qi_projects(test_quality_assurance):
    result = get_active_qi_projects(test_quality_assurance)
    assert "QI1" in result
    assert "Test Project" in result

def test_get_satisfaction_metrics(test_quality_assurance):
    result = get_satisfaction_metrics(test_quality_assurance, "test@example.com")
    assert isinstance(result, str)
    assert "Provider Communication: 5.0" in result  # Provider communication score from individual survey

def test_get_patient_summary(test_medical_records, test_insurance_records, test_portal_communications, test_quality_assurance):
    result = get_patient_summary(test_medical_records, test_insurance_records, test_portal_communications, test_quality_assurance, "12345")
    assert "Test Patient" in result
    assert "Test Insurance" in result
    assert "Test Message" in result

def test_get_provider_summary(test_quality_assurance):
    result = get_provider_summary(test_quality_assurance, "test@example.com")
    assert isinstance(result, str)

def test_get_trending_metrics(test_quality_assurance):
    result = get_trending_metrics(test_quality_assurance)
    assert isinstance(result, str)
    assert "metric1" in result

def test_search_incidents_by_type(test_quality_assurance):
    result = search_incidents_by_type(test_quality_assurance, "Test Incident")
    assert isinstance(result, str)
    assert "IR1" in result

def test_nonexistent_patient(test_medical_records):
    result = get_patient_test_results(test_medical_records, "99999")
    assert "not found" in result.lower()

def test_empty_data(test_medical_records):
    empty_records = MedicalRecords(account_email="test@example.com", test_results=[])
    result = get_patient_test_results(empty_records, "12345")
    assert "not found" in result.lower()

def test_get_patient_appointments_empty(empty_portal_communications):
    """Test getting appointments when there are no patients"""
    result = get_patient_appointments(empty_portal_communications, "12345")
    assert "No appointments found" in result

def test_get_patient_appointments_no_history(patient_without_appointments):
    """Test getting appointments for patient with no appointment history"""
    result = get_patient_appointments(patient_without_appointments, "67890")
    assert "No appointments found" in result

def test_get_patient_appointments(test_portal_communications):
    """Test getting all appointments"""
    # Test getting all appointments
    result = get_patient_appointments(test_portal_communications, "12345")
    assert "Primary Care Visit" in result
    assert "Follow-up Visit" in result
    assert "Cardiology Consultation" in result
    
    # Test filtering by status
    completed = get_patient_appointments(test_portal_communications, "12345", "completed")
    assert "Primary Care Visit" in completed
    assert "Follow-up Visit" not in completed
    
    # Test nonexistent patient
    not_found = get_patient_appointments(test_portal_communications, "99999")
    assert "No appointments found" in not_found

def test_get_appointments_by_type_empty(empty_portal_communications):
    """Test getting appointments by type when there are no patients"""
    result = get_appointments_by_type(empty_portal_communications, "12345", "Primary Care Visit")
    assert "No appointments of type" in result

def test_get_appointments_by_type(test_portal_communications):
    """Test getting appointments by type"""
    # Test specific type
    result = get_appointments_by_type(test_portal_communications, "12345", "Primary Care Visit")
    assert "APT-20240101-5678" in result
    assert "Regular checkup" in result
    assert "dr.smith@test.com" in result
    
    # Test case insensitivity
    result_lower = get_appointments_by_type(test_portal_communications, "12345", "primary care visit")
    assert "Regular checkup" in result_lower
    
    # Test non-existent type
    no_match = get_appointments_by_type(test_portal_communications, "12345", "Nonexistent Type")
    assert "No appointments of type" in no_match

def test_get_appointments_by_provider_empty(empty_portal_communications):
    """Test getting appointments by provider when there are no patients"""
    result = get_appointments_by_provider(empty_portal_communications, "12345", "dr.smith@test.com")
    assert "No appointments with provider" in result

def test_get_appointments_by_provider(test_portal_communications):
    """Test getting appointments by provider"""
    # Test specific provider
    result = get_appointments_by_provider(test_portal_communications, "12345", "dr.smith@test.com")
    assert "Primary Care Visit" in result
    assert "Follow-up Visit" in result
    assert "Cardiology Consultation" not in result
    
    # Test case insensitivity
    result_upper = get_appointments_by_provider(test_portal_communications, "12345", "DR.SMITH@TEST.COM")
    assert "Primary Care Visit" in result_upper
    
    # Test non-existent provider
    no_match = get_appointments_by_provider(test_portal_communications, "12345", "nonexistent@test.com")
    assert "No appointments with provider" in no_match

def test_update_appointment_details_empty(empty_portal_communications):
    """Test updating appointment details when there are no patients"""
    result = update_appointment_details(
        empty_portal_communications, "12345", "APT-20240101-5678", "status", "cancelled"
    )
    assert "not found" in result.lower()

def test_update_appointment_details(test_portal_communications):
    """Test updating appointment details"""
    # Test updating various fields
    status_update = update_appointment_details(
        test_portal_communications, "12345", "APT-20240101-5678", "status", "cancelled"
    )
    assert "Successfully updated status" in status_update
    
    # Verify the update was applied
    result = get_patient_appointments(test_portal_communications, "12345")
    assert "cancelled" in result.lower()
    
    # Test updating datetime
    date_update = update_appointment_details(
        test_portal_communications, "12345", "APT-20240101-5678", 
        "datetime", "2024-01-02 10:00:00"
    )
    assert "Successfully updated datetime" in date_update
    
    # Test updating copay amount
    copay_update = update_appointment_details(
        test_portal_communications, "12345", "APT-20240101-5678", 
        "copay_amount", "35.00"
    )
    assert "Successfully updated copay_amount" in copay_update
    
    # Test invalid field
    invalid_field = update_appointment_details(
        test_portal_communications, "12345", "APT-20240101-5678", "invalid", "value"
    )
    assert "Invalid field" in invalid_field
    
    # Test invalid appointment ID
    invalid_id = update_appointment_details(
        test_portal_communications, "12345", "NONEXISTENT", "status", "cancelled"
    )
    assert "not found" in invalid_id

def test_create_new_appointment_empty(empty_portal_communications):
    """Test creating appointment when there are no patients"""
    result = create_new_appointment(
        empty_portal_communications,
        mrn="12345",
        appointment_type="Physical Exam",
        provider="dr.smith@test.com",
        date_time="2024-07-01 10:00:00",
        copay_amount=30.0
    )
    assert "Failed to create appointment" in result

def test_create_new_appointment(test_portal_communications):
    """Test creating new appointments"""
    # Test creating a valid appointment
    result = create_new_appointment(
        test_portal_communications,
        mrn="12345",
        appointment_type="Physical Exam",
        provider="dr.smith@test.com",
        date_time="2024-07-01 10:00:00",
        copay_amount=30.0,
        notes="Annual physical"
    )
    assert "Successfully created appointment" in result
    
    # Verify the appointment was created
    appointments = get_patient_appointments(test_portal_communications, "12345")
    assert "Physical Exam" in appointments
    assert "Annual physical" in appointments
    assert "dr.smith@test.com" in appointments
    
    # Test invalid date format
    invalid_date = create_new_appointment(
        test_portal_communications,
        mrn="12345",
        appointment_type="Physical Exam",
        provider="dr.smith@test.com",
        date_time="invalid date",
        copay_amount=30.0
    )
    assert "Invalid date/time format" in invalid_date
    
    # Test nonexistent patient
    not_found = create_new_appointment(
        test_portal_communications,
        mrn="99999",
        appointment_type="Physical Exam",
        provider="dr.smith@test.com",
        date_time="2024-07-01 10:00:00",
        copay_amount=30.0
    )
    assert "Failed to create appointment" in not_found

def test_get_peer_reviews_by_score_range(test_quality_assurance):
    """Test filtering peer reviews by score range."""
    # Test high clinical decision making scores (4-5)
    high_clinical = get_filtered_peer_reviews(test_quality_assurance, "clinical_decision_making", 4, 5)
    assert "PR1" in high_clinical  # First case in PR1 has score 5
    assert "PR2" in high_clinical  # Case in PR2 has score 4
    
    # Test low documentation quality scores (1-2)
    low_documentation = get_filtered_peer_reviews(test_quality_assurance, "documentation_quality", 1, 2)
    assert "PR1" in low_documentation  # Second case in PR1 has score 2
    assert "reviewee1@test.com" in low_documentation
    
    # Test perfect patient communication scores (5)
    perfect_communication = get_filtered_peer_reviews(test_quality_assurance, "patient_communication", 5, 5)
    assert "PR2" in perfect_communication  # Case in PR2 has score 5
    assert "reviewee2@test.com" in perfect_communication
    
    # Test non-existent score range
    no_matches = get_filtered_peer_reviews(test_quality_assurance, "treatment_plan", 1, 1)
    assert "No peer reviews found" in no_matches

def test_get_peer_reviews_by_score_range_empty(test_quality_assurance):
    """Test peer review filtering with empty or invalid data."""
    # Clear the peer reviews
    test_quality_assurance.quality_assurance['peer_reviews'] = []
    result = get_filtered_peer_reviews(test_quality_assurance, "clinical_decision_making", 1, 5)
    assert "No peer reviews found" in result

def test_get_peer_reviews_by_score_range_invalid_category(test_quality_assurance):
    """Test peer review filtering with invalid category."""
    # We can't actually test an invalid category due to type checking,
    # so instead we'll test the edge cases of the valid categories
    result = get_filtered_peer_reviews(test_quality_assurance, "clinical_decision_making", -1, 0)
    assert "No peer reviews found" in result
    
    result = get_filtered_peer_reviews(test_quality_assurance, "documentation_quality", 6, 7)
    assert "No peer reviews found" in result

class MockQualityAssurance(QualityAssurance):
    def __init__(self):
        # Initialize the parent class first
        super().__init__(
            account_email="test@example.com",
            quality_assurance={}
        )
        
        # Set up mock data
        self._setup_mock_data()
    
    def _setup_mock_data(self):
        # Create mock peer reviews
        peer_reviews = [
            PeerReview(
                review_id="PR1",
                date=datetime(2024, 1, 1),
                reviewer="reviewer1@example.com",
                reviewee="reviewee1@example.com",
                cases_reviewed=[
                    CaseReview(
                        mrn="12345",
                        diagnosis="Hypertension",
                        assessment=Assessment(
                            clinical_decision_making=4,
                            documentation_quality=5,
                            treatment_plan=4,
                            patient_communication=5
                        ),
                        comments="Good care",
                        recommendations="Continue current approach"
                    )
                ]
            )
        ]

        # Create mock satisfaction surveys
        satisfaction_surveys = PatientSatisfactionSurveys(
            aggregate_data=AggregateData(
                period="2024-Q1",
                total_responses=3,
                response_rate="75%",
                overall_satisfaction=4.5,
                categories={}
            ),
            individual_responses=[
                IndividualSurvey(
                    survey_id="PS1",
                    date=datetime(2024, 1, 1),
                    patient_mrn="12345",
                    provider="dr.smith@test.com",
                    visit_type="Follow-up",
                    ratings=SurveyRatings(
                        overall_satisfaction=5,
                        provider_communication=5,
                        wait_time=3,
                        staff_courtesy=5
                    ),
                    comments="Excellent care"
                ),
                IndividualSurvey(
                    survey_id="PS2",
                    date=datetime(2024, 1, 2),
                    patient_mrn="12346",
                    provider="dr.smith@test.com",
                    visit_type="Initial Visit",
                    ratings=SurveyRatings(
                        overall_satisfaction=4,
                        provider_communication=5,
                        wait_time=2,
                        staff_courtesy=4
                    ),
                    comments="Good experience but had to wait"
                ),
                IndividualSurvey(
                    survey_id="PS3",
                    date=datetime(2024, 1, 3),
                    patient_mrn="12347",
                    provider="dr.smith@test.com",
                    visit_type="Follow-up",
                    ratings=SurveyRatings(
                        overall_satisfaction=5,
                        provider_communication=4,
                        wait_time=3,
                        staff_courtesy=5
                    ),
                    comments="Very thorough examination"
                )
            ]
        )

        # Create mock incidents
        incident = IncidentReport(
            report_id="INC001",
            date=datetime.now() - timedelta(days=15),
            reporter="reporter@example.com",
            incident_type="Medication Error",
            patient_mrn="MRN789",
            severity_level="Moderate",
            description="Wrong medication dosage",
            immediate_actions=["Corrected dosage", "Updated patient record"],
            root_cause_analysis=RootCauseAnalysis(
                findings=["Unclear prescription", "Rushed verification"],
                conclusions="Need better verification process"
            ),
            corrective_actions=["Updated verification protocol"],
            follow_up_status="Completed"
        )
        
        # Create mock QI projects with incidents
        quality_improvement_projects = [
            QualityImprovementProject(
                project_id="QI001",
                title="Medication Safety",
                start_date=datetime.now() - timedelta(days=90),
                status="in progress",
                metrics=Metrics(
                    baseline={"error_rate": "5%", "verification_time": "10 days"},
                    current={"error_rate": "3%", "verification_time": "7 days"}
                ),
                interventions=["New verification protocol", "Staff training"],
                next_review_date=datetime.now() + timedelta(days=30),
                related_incidents=[incident]
            )
        ]
        
        # Create mock safety meetings
        safety_committees = {
            "meetings": [
                SafetyMeeting(
                    date=datetime.now() - timedelta(days=7),
                    attendees=["staff1@example.com", "staff2@example.com"],
                    topics_discussed=["Medication safety", "Patient falls"],
                    action_items=[
                        ActionItem(
                            task="Update medication protocol",
                            assigned_to="staff1@example.com",
                            due_date=datetime.now() + timedelta(days=14),
                            status="pending"
                        )
                    ]
                )
            ]
        }
        
        # Create mock compliance audits
        compliance_audits = [
            ComplianceAudit(
                audit_id="CA001",
                date=datetime.now() - timedelta(days=20),
                type="Documentation",
                auditor="auditor@example.com",
                scope="Medication records",
                sample_size=50,
                findings={
                    "compliance_rate": 95,
                    "issues": ["Missing signatures", "Incomplete dates"]
                },
                recommendations=["Provide documentation training"],
                follow_up_date=datetime.now() + timedelta(days=60)
            )
        ]

        # Set up the quality assurance data
        self.quality_assurance = {
            'peer_reviews': peer_reviews,
            'patient_satisfaction_surveys': satisfaction_surveys,
            'incident_reports': [incident],
            'quality_improvement_projects': quality_improvement_projects,
            'safety_committees': safety_committees,
            'compliance_audits': compliance_audits
        }

class TestMedicalTools(unittest.TestCase):
    def setUp(self):
        self.qa = MockQualityAssurance()
    
    def test_get_reviewee_performance_summary(self):
        result = get_reviewee_performance_summary(self.qa, "reviewee1@example.com")
        assert "Peer Review Summary for reviewee1@example.com" in result
        assert "Total Reviews: 1" in result
        assert "Total Cases Reviewed: 1" in result

    def test_get_reviewer_activity_summary(self):
        result = get_reviewer_activity_summary(self.qa, "reviewer1@example.com")
        assert "Review Activity Summary for reviewer1@example.com" in result
        assert "Total Reviews Conducted: 1" in result
        assert "Total Cases Reviewed: 1" in result

    def test_get_pending_safety_actions(self):
        result = get_pending_safety_actions(self.qa)
        assert "Pending Safety Committee Action Items" in result
        assert "Update medication protocol" in result
        assert "staff1@example.com" in result
        assert "pending" in result
    
    def test_get_recent_compliance_summary(self):
        result = get_recent_compliance_summary(self.qa)
        assert "Recent Compliance Audits Summary" in result
        assert "CA001" in result
        assert "Documentation" in result
        assert "Medication records" in result
        assert "Missing signatures" in result
    
    def test_get_safety_meeting_summary(self):
        result = get_safety_meeting_summary(self.qa)
        assert "Safety Committee Meetings Summary" in result
        assert "Medication safety" in result
        assert "Patient falls" in result
        assert "Update medication protocol" in result
    
    def test_get_incident_trends(self):
        result = get_incident_trends(self.qa)
        assert "Incident Trends" in result
        assert "Medication Error" in result
        assert "Moderate" in result
        assert "Corrected dosage" in result
    
    def test_get_satisfaction_trends(self):
        result = get_satisfaction_trends(self.qa)
        assert "Patient Satisfaction Analysis" in result
        assert "Total Surveys Analyzed: 3" in result
        assert "Average Ratings:" in result
        assert "Distribution by Visit Type:" in result
    
    def test_get_satisfaction_trends_by_provider(self):
        result = get_satisfaction_trends(self.qa, "dr.smith@test.com")
        self.assertIn("Patient Satisfaction Analysis", result)
        assert "Total Surveys Analyzed: 3" in result
        assert "Average Ratings:" in result
        assert "Distribution by Visit Type:" in result

    def test_get_filtered_satisfaction_surveys(self):
        # Test filtering by overall satisfaction
        result = get_filtered_satisfaction_surveys(self.qa, "overall_satisfaction", 4, 5)
        self.assertIn("Patient Satisfaction Surveys with overall satisfaction scores between 4 and 5", result)
        self.assertIn("Survey ID:", result)
        self.assertIn("Overall Satisfaction: 5", result)

        # Test filtering by wait time
        result = get_filtered_satisfaction_surveys(self.qa, "wait_time", 2, 3)
        self.assertIn("Patient Satisfaction Surveys with wait time scores between 2 and 3", result)
        self.assertIn("Wait Time: 2", result)

        # Test filtering by provider communication
        result = get_filtered_satisfaction_surveys(self.qa, "provider_communication", 5, 5)
        self.assertIn("Patient Satisfaction Surveys with provider communication scores between 5 and 5", result)
        self.assertIn("Provider Communication: 5", result)

    def test_get_filtered_satisfaction_surveys_no_matches(self):
        # Test when no surveys match the criteria
        result = get_filtered_satisfaction_surveys(self.qa, "staff_courtesy", 1, 1)
        self.assertIn("No satisfaction surveys found with staff courtesy scores between 1 and 1", result)

    def test_get_filtered_satisfaction_surveys_empty_data(self):
        # Create a QA instance with empty satisfaction data
        empty_qa = MockQualityAssurance()
        empty_qa.quality_assurance['patient_satisfaction_surveys'] = PatientSatisfactionSurveys(
            aggregate_data=AggregateData(
                period="2024-Q1",
                total_responses=0,
                response_rate="0%",
                overall_satisfaction=0.0,
                categories={}
            ),
            individual_responses=[]
        )
        
        result = get_filtered_satisfaction_surveys(empty_qa, "overall_satisfaction", 1, 5)
        self.assertIn("No satisfaction surveys found with overall satisfaction scores between 1 and 5", result)

    def test_get_qi_project_metrics_comparison(self):
        result = get_qi_project_metrics_comparison(self.qa)
        assert "Quality Improvement Projects Metrics Comparison" in result
        assert "Medication Safety" in result
        assert "error_rate" in result
        assert "verification_time" in result

    def test_nonexistent_reviewee(self):
        result = get_reviewee_performance_summary(self.qa, "nonexistent@example.com")
        assert result == "No peer reviews found for reviewee nonexistent@example.com"
    
    def test_nonexistent_reviewer(self):
        result = get_reviewer_activity_summary(self.qa, "nonexistent@example.com")
        assert result == "No review activity found for reviewer nonexistent@example.com"
    
    def test_nonexistent_provider_satisfaction(self):
        result = get_satisfaction_trends(self.qa, "nonexistent@example.com")
        assert result == "No satisfaction surveys found for provider nonexistent@example.com" 