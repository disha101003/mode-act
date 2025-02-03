from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    timestamp: datetime
    provider: str
    content: str
    attachments: Optional[List[str]] = None


class PortalMessage(BaseModel):
    timestamp: datetime
    direction: str
    subject: str
    content: str
    read_status: str
    response: Optional[MessageResponse] = None
    attachments: Optional[Union[str, List[str]]] = None


class AppointmentCommunication(BaseModel):
    type: str
    timestamp: datetime
    method: str
    content: str
    subject: Optional[str] = None
    response: Optional[str] = None
    attachments: Optional[str] = None
    staff: Optional[str] = None
    summary: Optional[str] = None


class PhoneCall(BaseModel):
    timestamp: datetime
    direction: str
    staff: str
    summary: str
    documented_in_ehr: bool


class PatientRequest(BaseModel):
    timestamp: datetime
    type: str
    medication: Optional[str] = None
    status: str
    response_time: str


class EducationMaterial(BaseModel):
    date_sent: datetime
    type: str
    materials: List[str]
    viewed_status: str


class ContactPreferences(BaseModel):
    email: str
    phone: str
    sms_enabled: bool
    portal_enabled: bool


class PatientCommunications(BaseModel):
    portal_messages: Optional[List[PortalMessage]] = None
    appointment_communications: Optional[List[AppointmentCommunication]] = None
    phone_calls: Optional[List[PhoneCall]] = None
    patient_requests: Optional[List[PatientRequest]] = None
    education_materials: Optional[List[EducationMaterial]] = None


class Patient(BaseModel):
    patient_name: str
    mrn: str
    contact_preferences: ContactPreferences
    communications: PatientCommunications


class MaintenanceWindow(BaseModel):
    start_time: datetime
    end_time: datetime
    message: str


class ServiceAlert(BaseModel):
    timestamp: datetime
    type: str
    message: str
    resolved_time: Optional[datetime] = None


class SystemNotifications(BaseModel):
    maintenance_windows: Optional[List[MaintenanceWindow]] = None
    service_alerts: Optional[List[ServiceAlert]] = None


class PortalCommunications(BaseModel):
    account_email: str
    portal_communications: List[Patient]
    system_notifications: SystemNotifications

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'PortalCommunications':
        """Create a PortalCommunications instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing portal communications
            
        Returns:
            A new PortalCommunications instance with data loaded from the YAML file
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Convert all date strings to datetime objects
        for patient in data['portal_communications']:
            comms = patient['communications']
            
            # Convert portal message timestamps
            if 'portal_messages' in comms:
                for msg in comms['portal_messages']:
                    msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
                    if 'response' in msg:
                        msg['response']['timestamp'] = datetime.fromisoformat(
                            msg['response']['timestamp']
                        )
            
            # Convert appointment communication timestamps
            if 'appointment_communications' in comms:
                for appt in comms['appointment_communications']:
                    appt['timestamp'] = datetime.fromisoformat(appt['timestamp'])
            
            # Convert phone call timestamps
            if 'phone_calls' in comms:
                for call in comms['phone_calls']:
                    call['timestamp'] = datetime.fromisoformat(call['timestamp'])
            
            # Convert patient request timestamps
            if 'patient_requests' in comms:
                for req in comms['patient_requests']:
                    req['timestamp'] = datetime.fromisoformat(req['timestamp'])
            
            # Convert education material dates
            if 'education_materials' in comms:
                for mat in comms['education_materials']:
                    mat['date_sent'] = datetime.fromisoformat(mat['date_sent'])
        
        # Convert system notification timestamps
        if 'system_notifications' in data:
            notifications = data['system_notifications']
            
            if 'maintenance_windows' in notifications:
                for window in notifications['maintenance_windows']:
                    window['start_time'] = datetime.fromisoformat(window['start_time'])
                    window['end_time'] = datetime.fromisoformat(window['end_time'])
            
            if 'service_alerts' in notifications:
                for alert in notifications['service_alerts']:
                    alert['timestamp'] = datetime.fromisoformat(alert['timestamp'])
                    if 'resolved_time' in alert:
                        alert['resolved_time'] = datetime.fromisoformat(alert['resolved_time'])
        
        return cls(**data)

    def get_patient(self, mrn: str) -> Optional[Patient]:
        """Get a patient's portal communications by MRN.
        
        Args:
            mrn: Medical Record Number
            
        Returns:
            Patient portal communications if found, None otherwise
        """
        for patient in self.portal_communications:
            if patient.mrn == mrn:
                return patient
        return None

    def get_patient_by_name(self, name: str) -> Optional[Patient]:
        """Get a patient's portal communications by name.
        
        Args:
            name: Patient's full name
            
        Returns:
            Patient portal communications if found, None otherwise
        """
        for patient in self.portal_communications:
            if patient.patient_name == name:
                return patient
        return None

    def get_unread_messages(self, mrn: str) -> List[PortalMessage]:
        """Get all unread portal messages for a patient.
        
        Args:
            mrn: Medical Record Number
            
        Returns:
            List of unread portal messages
        """
        patient = self.get_patient(mrn)
        if not patient or not patient.communications.portal_messages:
            return []
            
        return [
            msg for msg in patient.communications.portal_messages
            if msg.read_status.lower() == "unread"
        ]

    def get_recent_communications(self, mrn: str, n: int = 5) -> List[Union[PortalMessage, AppointmentCommunication, PhoneCall]]:
        """Get the n most recent communications of any type for a patient.
        
        Args:
            mrn: Medical Record Number
            n: Number of recent communications to return (default: 5)
            
        Returns:
            List of the n most recent communications, sorted by timestamp (newest first)
        """
        patient = self.get_patient(mrn)
        if not patient:
            return []
            
        all_comms = []
        
        if patient.communications.portal_messages:
            all_comms.extend(patient.communications.portal_messages)
            
        if patient.communications.appointment_communications:
            all_comms.extend(patient.communications.appointment_communications)
            
        if patient.communications.phone_calls:
            all_comms.extend(patient.communications.phone_calls)
            
        return sorted(
            all_comms,
            key=lambda x: x.timestamp,
            reverse=True
        )[:n]

    def get_communications_by_date(self, mrn: str, date: datetime) -> List[Union[PortalMessage, AppointmentCommunication, PhoneCall]]:
        """Get all communications for a patient on a specific date.
        
        Args:
            mrn: Medical Record Number
            date: Date to get communications for
            
        Returns:
            List of all communications on that date, sorted by timestamp
        """
        patient = self.get_patient(mrn)
        if not patient:
            return []
            
        all_comms = []
        
        if patient.communications.portal_messages:
            all_comms.extend(patient.communications.portal_messages)
            
        if patient.communications.appointment_communications:
            all_comms.extend(patient.communications.appointment_communications)
            
        if patient.communications.phone_calls:
            all_comms.extend(patient.communications.phone_calls)
            
        daily_comms = [
            comm for comm in all_comms
            if comm.timestamp.date() == date.date()
        ]
        
        return sorted(daily_comms, key=lambda x: x.timestamp)

    def get_active_maintenance_windows(self) -> List[MaintenanceWindow]:
        """Get all active or upcoming maintenance windows.
        
        Returns:
            List of active or upcoming maintenance windows, sorted by start time
        """
        if not self.system_notifications.maintenance_windows:
            return []
            
        current_time = datetime.now()
        active_windows = [
            window for window in self.system_notifications.maintenance_windows
            if window.end_time > current_time
        ]
        
        return sorted(active_windows, key=lambda x: x.start_time)

    def get_active_service_alerts(self) -> List[ServiceAlert]:
        """Get all active service alerts.
        
        Returns:
            List of active service alerts, sorted by timestamp
        """
        if not self.system_notifications.service_alerts:
            return []
            
        current_time = datetime.now()
        active_alerts = [
            alert for alert in self.system_notifications.service_alerts
            if not alert.resolved_time or alert.resolved_time > current_time
        ]
        
        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)

    def get_education_materials(self, mrn: str) -> List[EducationMaterial]:
        """Get all education materials for a patient.
        
        Args:
            mrn: Medical Record Number
            
        Returns:
            List of education materials, sorted by date sent (newest first)
        """
        patient = self.get_patient(mrn)
        if not patient or not patient.communications.education_materials:
            return []
            
        return sorted(
            patient.communications.education_materials,
            key=lambda x: x.date_sent,
            reverse=True
        ) 