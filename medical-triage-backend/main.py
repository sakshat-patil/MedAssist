from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from document_processor import DocumentProcessor
from agentkit_integration import AgentKitIntegration, StructuredData, FollowUpAgent
from triage_pipeline import TriagePipeline
from pdf_generator import PDFGenerator
import os
import traceback
from twilio.rest import Client
from datetime import datetime

app = FastAPI(
    title="MedAssist AI",
    description="Intelligent Medical Triage Platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
agent_kit = AgentKitIntegration()
triage_pipeline = TriagePipeline()
pdf_generator = PDFGenerator()
case_monitor = FollowUpAgent(os.getenv("ANTHROPIC_API_KEY"))

# Initialize Twilio client
print("Initializing Twilio client...")
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
doctor_phone_number = os.getenv("DOCTOR_PHONE_NUMBER")

if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number, doctor_phone_number]):
    print("WARNING: Missing Twilio credentials. Calls will not be made.")
    twilio_client = None
else:
    twilio_client = Client(twilio_account_sid, twilio_auth_token)
    print("Twilio client initialized successfully.")

# Create reports directory
os.makedirs("reports", exist_ok=True)

class StructuredData(BaseModel):
    symptoms: List[Dict[str, Any]]
    vital_signs: Dict[str, Any]
    medical_history: List[str]

class TriageRequest(BaseModel):
    text: str

@app.post("/api/analyze-triage")
async def analyze_triage(data: StructuredData):
    try:
        result = triage_pipeline.process(data.dict())
        pdf_path = pdf_generator.save_report(result)
        result["pdf_url"] = f"/api/reports/{os.path.basename(pdf_path)}"
        return result
    except Exception as e:
        print("Error in /api/analyze-triage:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    try:
        content = await document_processor.process_file(file)
        structured_data = agent_kit.extract_structured_data(content)
        risk_assessment = agent_kit.analyze_risk(structured_data)
        
        if risk_assessment.get("risk_level") == "HIGH" and twilio_client:
            try:
                call = twilio_client.calls.create(
                    to=doctor_phone_number,
                    from_=twilio_phone_number,
                    url="http://demo.twilio.com/docs/voice.xml"
                )
            except Exception as e:
                print(f"Error triggering Twilio call: {str(e)}")

        result = triage_pipeline.process(structured_data)
        pdf_path = pdf_generator.save_report(result)
        result["pdf_url"] = f"/api/reports/{os.path.basename(pdf_path)}"
        return result
    except Exception as e:
        print("Error in /api/analyze-document:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    try:
        file_path = os.path.join("reports", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(file_path, media_type="application/pdf")
    except Exception as e:
        print("Error in /api/reports/{filename}:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze")
async def analyze_triage(request: TriageRequest) -> Dict[str, Any]:
    try:
        structured_data = agent_kit.extract_structured_data(request.text)
        risk_assessment = agent_kit.analyze_risk(structured_data)
        
        if risk_assessment.get("risk_level") == "HIGH" and twilio_client:
            try:
                call = twilio_client.calls.create(
                    to=doctor_phone_number,
                    from_=twilio_phone_number,
                    url="http://demo.twilio.com/docs/voice.xml"
                )
            except Exception as e:
                print(f"Error triggering Twilio call: {str(e)}")
        
        result = {
            "structured_data": structured_data,
            "risk_assessment": risk_assessment
        }
        pdf_path = pdf_generator.save_report(result)
        result["pdf_url"] = f"/api/reports/{os.path.basename(pdf_path)}"
        
        return result
    except Exception as e:
        print(f"Error in analyze_triage: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/follow-up/{case_id}")
async def follow_up_case(case_id: str, assessment: Dict[str, Any]):
    """Initiate autonomous follow-up for a medical case."""
    try:
        result = await case_monitor.monitor_case(case_id, assessment)
        return result
    except Exception as e:
        print(f"Error in follow-up: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/case-history/{case_id}")
async def get_case_history(case_id: str):
    """Get the conversation history for a case."""
    try:
        history = await case_monitor.get_case_summary(case_id)
        return history
    except Exception as e:
        print(f"Error getting case history: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-case/{case_id}")
async def update_case(case_id: str, interaction: Dict[str, Any]):
    """Update the case with new interaction data."""
    try:
        await case_monitor.update_conversation_history(case_id, interaction)
        return {"status": "success", "message": "Case updated successfully"}
    except Exception as e:
        print(f"Error updating case: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
