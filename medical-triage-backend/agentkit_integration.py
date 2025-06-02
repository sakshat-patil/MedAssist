from typing import Dict, Any, List, Optional
import os
import json
from anthropic import Anthropic
from pydantic import BaseModel, Field
from twilio.rest import Client
from dotenv import load_dotenv
import traceback
from datetime import datetime, timedelta

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

class FollowUpAgent:
    def __init__(self, anthropic_api_key: str):
        self.anthropic_api_key = anthropic_api_key
        self.conversation_history = {}
        self.learning_history = {}  # Track successful interventions
        self.pattern_recognition = {}  # Track symptom patterns
        
    async def monitor_case(self, case_id: str, initial_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor a medical case and provide autonomous follow-up."""
        # Analyze historical patterns
        similar_cases = self._find_similar_cases(initial_assessment)
        
        # Generate context-aware prompt
        prompt = f"""
        You are an autonomous medical follow-up agent. Your task is to:
        1. Analyze the initial assessment: {json.dumps(initial_assessment)}
        2. Consider similar historical cases: {json.dumps(similar_cases)}
        3. Determine if follow-up is needed based on risk level and symptoms
        4. Generate appropriate follow-up questions
        5. Suggest next steps based on the case progression
        6. Identify potential complications based on patterns
        
        Current case ID: {case_id}
        Current time: {datetime.now().isoformat()}
        
        Provide a structured response with:
        - Follow-up needed (boolean)
        - Risk level change (if any)
        - Recommended questions
        - Suggested next steps
        - Escalation needed (boolean)
        - Potential complications
        - Recommended preventive measures
        """
        
        # Here you would make the actual API call to Claude
        # For now, returning a mock response
        response = {
            "follow_up_needed": True,
            "risk_level_change": "increased",
            "recommended_questions": [
                "Has the pain intensity changed?",
                "Are you experiencing any new symptoms?",
                "Have you taken any medication since the last assessment?"
            ],
            "next_steps": [
                "Schedule follow-up appointment",
                "Monitor vital signs",
                "Update medication if needed"
            ],
            "escalation_needed": False,
            "potential_complications": [
                "Risk of infection",
                "Possible medication interaction"
            ],
            "preventive_measures": [
                "Increase fluid intake",
                "Monitor temperature regularly"
            ]
        }
        
        # Learn from this interaction
        self._update_learning_history(case_id, initial_assessment, response)
        
        return response
    
    def _find_similar_cases(self, current_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar historical cases for pattern recognition."""
        similar_cases = []
        for case_id, history in self.conversation_history.items():
            if self._is_similar_case(history, current_case):
                similar_cases.append({
                    "case_id": case_id,
                    "outcome": history.get("outcome", "unknown"),
                    "successful_interventions": history.get("successful_interventions", [])
                })
        return similar_cases
    
    def _is_similar_case(self, history: Dict[str, Any], current_case: Dict[str, Any]) -> bool:
        """Determine if a historical case is similar to the current case."""
        # Compare symptoms
        current_symptoms = set(s["description"] for s in current_case.get("symptoms", []))
        historical_symptoms = set(s["description"] for s in history.get("symptoms", []))
        
        # Compare vital signs
        current_vitals = current_case.get("vital_signs", {})
        historical_vitals = history.get("vital_signs", {})
        
        # Calculate similarity score
        symptom_similarity = len(current_symptoms.intersection(historical_symptoms)) / len(current_symptoms.union(historical_symptoms))
        vital_similarity = self._compare_vital_signs(current_vitals, historical_vitals)
        
        return (symptom_similarity > 0.5) and (vital_similarity > 0.7)
    
    def _compare_vital_signs(self, current: Dict[str, Any], historical: Dict[str, Any]) -> float:
        """Compare vital signs and return similarity score."""
        if not current or not historical:
            return 0.0
            
        differences = []
        for key in current:
            if key in historical:
                current_val = current[key]
                historical_val = historical[key]
                if isinstance(current_val, (int, float)) and isinstance(historical_val, (int, float)):
                    diff = abs(current_val - historical_val) / max(current_val, historical_val)
                    differences.append(1 - diff)
        
        return sum(differences) / len(differences) if differences else 0.0
    
    def _update_learning_history(self, case_id: str, assessment: Dict[str, Any], response: Dict[str, Any]):
        """Update learning history with successful interventions."""
        if case_id not in self.learning_history:
            self.learning_history[case_id] = []
            
        self.learning_history[case_id].append({
            "timestamp": datetime.now().isoformat(),
            "assessment": assessment,
            "response": response,
            "outcome": "pending"  # Will be updated when case is resolved
        })
        
        # Update pattern recognition
        self._update_pattern_recognition(assessment, response)
    
    def _update_pattern_recognition(self, assessment: Dict[str, Any], response: Dict[str, Any]):
        """Update pattern recognition with new case data."""
        symptoms = [s["description"] for s in assessment.get("symptoms", [])]
        for symptom in symptoms:
            if symptom not in self.pattern_recognition:
                self.pattern_recognition[symptom] = {
                    "count": 0,
                    "successful_interventions": [],
                    "complications": []
                }
            
            self.pattern_recognition[symptom]["count"] += 1
            
            # Track successful interventions
            if response.get("successful_interventions"):
                self.pattern_recognition[symptom]["successful_interventions"].extend(
                    response["successful_interventions"]
                )
            
            # Track complications
            if response.get("potential_complications"):
                self.pattern_recognition[symptom]["complications"].extend(
                    response["potential_complications"]
                )
    
    async def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """Generate a comprehensive case summary."""
        if case_id not in self.conversation_history:
            return {"error": "Case not found"}
            
        history = self.conversation_history[case_id]
        learning_data = self.learning_history.get(case_id, [])
        
        return {
            "case_id": case_id,
            "total_interactions": len(history),
            "first_interaction": history[0]["timestamp"],
            "last_interaction": history[-1]["timestamp"],
            "interaction_summary": [
                {
                    "timestamp": h["timestamp"],
                    "type": h["interaction"].get("type", "unknown"),
                    "summary": h["interaction"].get("summary", "")
                }
                for h in history
            ],
            "learning_insights": [
                {
                    "timestamp": l["timestamp"],
                    "assessment": l["assessment"],
                    "outcome": l["outcome"],
                    "successful_interventions": l.get("successful_interventions", [])
                }
                for l in learning_data
            ],
            "pattern_analysis": self._analyze_patterns(case_id)
        }
    
    def _analyze_patterns(self, case_id: str) -> Dict[str, Any]:
        """Analyze patterns in the case history."""
        if case_id not in self.conversation_history:
            return {}
            
        history = self.conversation_history[case_id]
        symptoms = []
        interventions = []
        
        for entry in history:
            if "symptoms" in entry:
                symptoms.extend(entry["symptoms"])
            if "interventions" in entry:
                interventions.extend(entry["interventions"])
        
        return {
            "common_symptoms": self._get_common_items(symptoms),
            "successful_interventions": self._get_common_items(interventions),
            "risk_patterns": self._analyze_risk_patterns(history)
        }
    
    def _get_common_items(self, items: List[str]) -> List[Dict[str, Any]]:
        """Get most common items from a list."""
        from collections import Counter
        counter = Counter(items)
        return [{"item": item, "count": count} for item, count in counter.most_common(5)]
    
    def _analyze_risk_patterns(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze risk patterns in case history."""
        risk_patterns = []
        for entry in history:
            if "risk_level" in entry:
                risk_patterns.append({
                    "timestamp": entry["timestamp"],
                    "risk_level": entry["risk_level"],
                    "triggering_factors": entry.get("triggering_factors", [])
                })
        return risk_patterns

class CaseMonitor:
    def __init__(self, anthropic_api_key: str):
        self.anthropic_api_key = anthropic_api_key
        self.active_cases = {}
        self.monitoring_rules = {
            "HIGH": {
                "check_interval": 30,  # minutes
                "escalation_threshold": 2,  # number of risk increases
                "required_follow_ups": 3  # per day
            },
            "MODERATE": {
                "check_interval": 60,  # minutes
                "escalation_threshold": 3,
                "required_follow_ups": 2  # per day
            },
            "LOW": {
                "check_interval": 120,  # minutes
                "escalation_threshold": 4,
                "required_follow_ups": 1  # per day
            }
        }

    async def start_monitoring(self, case_id: str, initial_data: Dict[str, Any]):
        """Start monitoring a new case."""
        self.active_cases[case_id] = {
            "data": initial_data,
            "risk_level": initial_data.get("risk_level", "LOW"),
            "last_check": datetime.now(),
            "risk_increases": 0,
            "follow_ups_today": 0,
            "last_follow_up": None,
            "alerts": []
        }
        return await self._schedule_next_check(case_id)

    async def _schedule_next_check(self, case_id: str):
        """Schedule the next check based on risk level."""
        case = self.active_cases[case_id]
        interval = self.monitoring_rules[case["risk_level"]]["check_interval"]
        next_check = datetime.now() + timedelta(minutes=interval)
        case["next_check"] = next_check
        return next_check

    async def check_case(self, case_id: str) -> Dict[str, Any]:
        """Perform a scheduled check on a case."""
        if case_id not in self.active_cases:
            return {"error": "Case not found"}

        case = self.active_cases[case_id]
        current_time = datetime.now()

        # Check if it's time for a follow-up
        if self._needs_follow_up(case):
            follow_up_result = await self._perform_follow_up(case_id)
            case["last_follow_up"] = current_time
            case["follow_ups_today"] += 1

        # Check for risk level changes
        risk_assessment = await self._assess_current_risk(case_id)
        if risk_assessment["risk_level"] > case["risk_level"]:
            case["risk_increases"] += 1
            case["alerts"].append({
                "timestamp": current_time.isoformat(),
                "type": "risk_increase",
                "details": f"Risk level increased to {risk_assessment['risk_level']}"
            })

        # Check if escalation is needed
        if self._needs_escalation(case):
            await self._escalate_case(case_id)

        # Update case data
        case["last_check"] = current_time
        await self._schedule_next_check(case_id)

        return {
            "case_id": case_id,
            "current_status": {
                "risk_level": case["risk_level"],
                "follow_ups_today": case["follow_ups_today"],
                "risk_increases": case["risk_increases"],
                "last_check": case["last_check"].isoformat(),
                "next_check": case["next_check"].isoformat()
            },
            "alerts": case["alerts"]
        }

    def _needs_follow_up(self, case: Dict[str, Any]) -> bool:
        """Determine if a follow-up is needed based on monitoring rules."""
        rules = self.monitoring_rules[case["risk_level"]]
        if case["follow_ups_today"] >= rules["required_follow_ups"]:
            return False
        if not case["last_follow_up"]:
            return True
        time_since_last = datetime.now() - case["last_follow_up"]
        return time_since_last.total_seconds() >= 3600  # 1 hour minimum between follow-ups

    async def _perform_follow_up(self, case_id: str) -> Dict[str, Any]:
        """Perform a follow-up check on the case."""
        case = self.active_cases[case_id]
        # Here you would implement the actual follow-up logic
        # For now, returning a mock response
        return {
            "status": "follow_up_completed",
            "timestamp": datetime.now().isoformat(),
            "findings": "No significant changes in condition"
        }

    async def _assess_current_risk(self, case_id: str) -> Dict[str, Any]:
        """Assess the current risk level of the case."""
        case = self.active_cases[case_id]
        # Here you would implement the actual risk assessment logic
        # For now, returning a mock response
        return {
            "risk_level": case["risk_level"],
            "assessment_time": datetime.now().isoformat()
        }

    def _needs_escalation(self, case: Dict[str, Any]) -> bool:
        """Determine if the case needs escalation."""
        rules = self.monitoring_rules[case["risk_level"]]
        return case["risk_increases"] >= rules["escalation_threshold"]

    async def _escalate_case(self, case_id: str):
        """Escalate the case to a higher level of care."""
        case = self.active_cases[case_id]
        case["alerts"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "escalation",
            "details": "Case escalated due to multiple risk increases"
        })
        # Here you would implement the actual escalation logic
        # For example, notify a doctor or transfer to emergency care

    async def stop_monitoring(self, case_id: str):
        """Stop monitoring a case."""
        if case_id in self.active_cases:
            del self.active_cases[case_id]
            return {"status": "monitoring_stopped", "case_id": case_id}
        return {"error": "Case not found"}
