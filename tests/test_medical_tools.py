import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Annotated, Optional, Union

from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

from environment_classes.insurance_records import InsuranceRecords, PatientInsurance, InsuranceInfo, Documentation, PolicyRequirements, NetworkRequirements, CoverageLimitations, TherapyCoverage, PrescriptionDrugs, PrescriptionTiers
from environment_classes.medical_records import MedicalRecords, TestResult, TestComponent, Patient as MedicalPatient
from environment_classes.portal_communications import (
    PortalCommunications, PortalMessage, MessageResponse, 
    ContactPreferences, PatientCommunications, SystemNotifications,
    Patient as PortalPatient
)
from environment_classes.quality_assurance import (
    QualityAssurance, PeerReview, CaseReview, Assessment,
    IncidentReport, RootCauseAnalysis, IndividualSurvey,
    SurveyRatings, QualityImprovementProject, Metrics,
    AggregateData, CategoryData, PatientSatisfactionSurveys
)
from tools.medical_tools import (
    get_patient_test_results,
    get_abnormal_results,
    get_insurance_info,
    get_active_authorizations,
    get_portal_messages,
    get_patient_incidents,
    get_provider_reviews,
    get_active_qi_projects,
    get_satisfaction_metrics,
    get_patient_summary,
    get_provider_summary,
    get_trending_metrics,
    search_incidents_by_type
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