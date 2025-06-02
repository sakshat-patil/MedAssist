from typing import Dict, Any, List
import os
import json
from anthropic import Anthropic
from pydantic import BaseModel, Field
from twilio.rest import Client
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# -------------------- Pydantic Schemas --------------------

class Symptom(BaseModel):
    description: str = Field(description="Description of the symptom")
    severity: str = Field(description="Severity level of the symptom (mild, moderate, severe)")

class VitalSigns(BaseModel):
    blood_pressure: Dict[str, int] = Field(description="Blood pressure readings (systolic and diastolic)")
    heart_rate: int = Field(description="Heart rate in beats per minute")
    temperature: Dict[str, Any] = Field(description="Body temperature with value and unit")
    oxygen_saturation: int = Field(description="Oxygen saturation percentage")

class StructuredData(BaseModel):
    symptoms: List[Symptom] = Field(description="List of symptoms with their severity")
    vital_signs: VitalSigns = Field(description="Vital signs measurements")
    medical_history: List[str] = Field(description="List of relevant medical history items")

class RiskAssessment(BaseModel):
    risk_level: str = Field(description="Risk level (LOW, MODERATE, HIGH)")
    explanation: str = Field(description="Detailed explanation of the risk assessment")

# -------------------- Core Integration Class --------------------

class AgentKitIntegration:
    def __init__(self):
        # Check for required environment variables
        required_vars = [
            "ANTHROPIC_API_KEY",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "DOCTOR_PHONE_NUMBER",
            "TWILIO_PHONE_NUMBER"
        ]
        for var in required_vars:
            if not os.getenv(var):
                raise EnvironmentError(f"Missing environment variable: {var}")

        # Initialize Anthropic client
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Initialize Twilio client
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.doctor_phone = os.getenv("DOCTOR_PHONE_NUMBER")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured medical data from text input."""
        try:
            # Create the prompt
            system_prompt = """You are a medical triage assistant. Extract structured medical information from the input text.
            Focus on identifying symptoms, their severity, vital signs, and relevant medical history.
            Format the output as a JSON object with the following structure:
            {
                "symptoms": [
                    {
                        "description": "string",
                        "severity": "mild|moderate|severe"
                    }
                ],
                "vital_signs": {
                    "blood_pressure": {
                        "systolic": number,
                        "diastolic": number
                    },
                    "heart_rate": number,
                    "temperature": {
                        "value": number,
                        "unit": "C|F"
                    },
                    "oxygen_saturation": number
                },
                "medical_history": ["string"]
            }"""

            # Get response from Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            
            # Safely extract and parse the response
            raw = response.content[0].text if response.content else "{}"
            structured_data = StructuredData.parse_raw(raw).model_dump()
            return structured_data
        except Exception as e:
            raise Exception(f"Error extracting structured data: {str(e)}")

    def analyze_risk(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk level based on structured data."""
        try:
            system_prompt = """You are a medical risk assessment expert. Analyze the provided medical data and determine the risk level.
            Consider symptoms, vital signs, and medical history.
            Provide a risk level (LOW, MODERATE, HIGH) and a detailed explanation.
            Format your response as a JSON object with 'risk_level' and 'explanation' fields.
            For neurological symptoms (headache, weakness, speech problems) with high blood pressure, always return HIGH risk.
            For chest pain with shortness of breath, always return HIGH risk."""

            # Get response from Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Analyze this medical data: {json.dumps(structured_data, indent=2)}"}
                ]
            )
            
            # Safely extract and parse the response
            raw = response.content[0].text if response.content else "{}"
            print("Raw risk assessment response:", raw)  # Debug log
            risk_assessment = RiskAssessment.parse_raw(raw).model_dump()
            print("Parsed risk assessment:", risk_assessment)  # Debug log
            
            # If risk is HIGH, notify doctor via SMS
            if risk_assessment["risk_level"] == "HIGH":
                self._notify_doctor(structured_data, risk_assessment)
            
            return risk_assessment
        except Exception as e:
            print(f"Error in analyze_risk: {str(e)}")  # Debug log
            traceback.print_exc()  # Print full traceback
            raise Exception(f"Error analyzing risk: {str(e)}")

    def _notify_doctor(self, structured_data: Dict[str, Any], risk_assessment: Dict[str, Any]) -> None:
        """Send SMS notification to doctor for high-risk cases."""
        try:
            # Format the message
            message = (
                "🚨 HIGH RISK MEDICAL CASE 🚨\n\n"
                f"Risk Level: {risk_assessment['risk_level']}\n"
                f"Explanation: {risk_assessment['explanation']}\n\n"
                "Patient Data:\n"
                f"Symptoms: {json.dumps([s['description'] for s in structured_data['symptoms']], indent=2)}\n"
                f"Vital Signs: {json.dumps(structured_data['vital_signs'], indent=2)}\n"
                f"Medical History: {json.dumps(structured_data['medical_history'], indent=2)}"
            )
            
            # Truncate message if it exceeds Twilio's limit (1600 chars)
            if len(message) > 1500:
                message = message[:1500] + "\n... (truncated)"
            
            # Send SMS
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.doctor_phone
            )
        except Exception as e:
            print(f"Failed to send SMS notification: {str(e)}")
            # Don't raise the exception - we don't want SMS failure to break the main flow
