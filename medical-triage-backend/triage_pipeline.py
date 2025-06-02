from typing import Dict, Any
from agentkit_integration import AgentKitIntegration

class TriagePipeline:
    def __init__(self):
        self.agent_kit = AgentKitIntegration()

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Analyze risk using the structured data
            risk_assessment = self.agent_kit.analyze_risk(data)
            
            # Return the complete result
            return {
                "structured_data": data,
                "risk_assessment": risk_assessment
            }
        except Exception as e:
            raise Exception(f"Error in triage pipeline: {str(e)}")

    def _validate_data(self, data: Dict[str, Any]) -> None:
        """Validate the input data structure."""
        required_fields = ["symptoms", "vital_signs", "medical_history"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            
            if not isinstance(data[field], (list, dict)):
                raise ValueError(f"Invalid type for field {field}")
            
            if field == "symptoms" and not isinstance(data[field], list):
                raise ValueError("Symptoms must be a list")
            
            if field == "vital_signs" and not isinstance(data[field], dict):
                raise ValueError("Vital signs must be a dictionary")
            
            if field == "medical_history" and not isinstance(data[field], list):
                raise ValueError("Medical history must be a list") 