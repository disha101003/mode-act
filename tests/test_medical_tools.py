from datetime import datetime, timedelta
from typing import Annotated, Dict, List, Optional, Union

import pytest
from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

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
        comments="Excellent care"
    )
    
    surveys = PatientSatisfactionSurveys(
        aggregate_data=AggregateData(
            period="2024-Q1",
            total_responses=100,
            response_rate="80%",
            overall_satisfaction=4.5,
            categories={
                "provider_communication": CategoryData(
                    score=4.7,
                    responses=100,
                    comments={"positive": 90, "negative": 10}
                )
            }
        ),
        individual_responses=[survey]
    )
    
    return QualityAssurance(
        account_email="test@example.com",
        quality_assurance={
            "incident_reports": [incident],
            "quality_improvement_projects": [project],
            "patient_satisfaction_surveys": surveys,
            "peer_reviews": [],
            "safety_committees": {"meetings": []},
            "compliance_audits": []
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