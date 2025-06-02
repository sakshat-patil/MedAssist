from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from document_processor import DocumentProcessor
from agentkit_integration import AgentKitIntegration, StructuredData
from triage_pipeline import TriagePipeline
from pdf_generator import PDFGenerator
import os
import traceback  # ⬅️ added for detailed error logging
from twilio.rest import Client

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

# Initialize Twilio client
print("Initializing Twilio client...")
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
doctor_phone_number = os.getenv("DOCTOR_PHONE_NUMBER")


if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number, doctor_phone_number]):
    print("WARNING: Missing Twilio credentials. Calls will not be made.")
    print("Required environment variables:")
    print("- TWILIO_ACCOUNT_SID")
    print("- TWILIO_AUTH_TOKEN")
    print("- TWILIO_PHONE_NUMBER")
    print("- DOCTOR_PHONE_NUMBER")
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
        print("Processed document content:", content)

        structured_data = agent_kit.extract_structured_data(content)
        print("Extracted structured data:", structured_data)

        # Analyze risk
        risk_assessment = agent_kit.analyze_risk(structured_data)
        print("Risk assessment:", risk_assessment)
        
        # If risk level is HIGH, trigger a Twilio call
        if risk_assessment.get("risk_level") == "HIGH":
            print("Risk level is HIGH. Attempting to trigger Twilio call...")
            print(f"Twilio credentials check:")
            print(f"Account SID: {twilio_account_sid[:5]}...")
            print(f"Auth Token: {twilio_auth_token[:5]}...")
            print(f"From Number: {twilio_phone_number}")
            print(f"To Number: {doctor_phone_number}")
            
            if twilio_client is None:
                print("ERROR: Twilio client not initialized. Cannot make call.")
            else:
                try:
                    print("Creating Twilio call...")
                    call = twilio_client.calls.create(
                        to=doctor_phone_number,
                        from_=twilio_phone_number,
                        url="http://demo.twilio.com/docs/voice.xml"
                    )
                    print(f"Call initiated successfully. Call SID: {call.sid}")
                except Exception as e:
                    print(f"Error triggering Twilio call: {str(e)}")
                    traceback.print_exc()

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
        # Extract structured data
        structured_data = agent_kit.extract_structured_data(request.text)
        
        # Analyze risk
        risk_assessment = agent_kit.analyze_risk(structured_data)
        
        # If risk level is HIGH, trigger a Twilio call
        if risk_assessment.get("risk_level") == "HIGH":
            print("Risk level is HIGH. Attempting to trigger Twilio call...")
            if twilio_client is None:
                print("ERROR: Twilio client not initialized. Cannot make call.")
            else:
                try:
                    print("Creating Twilio call...")
                    call = twilio_client.calls.create(
                        to=doctor_phone_number,
                        from_=twilio_phone_number,
                        url="http://demo.twilio.com/docs/voice.xml"
                    )
                    print(f"Call initiated successfully. Call SID: {call.sid}")
                except Exception as e:
                    print(f"Error triggering Twilio call: {str(e)}")
                    traceback.print_exc()
        
        # Generate PDF report
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
