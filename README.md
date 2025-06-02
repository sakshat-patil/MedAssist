# MedAssist AI - Intelligent Medical Triage Platform

A modern AI-powered medical triage system that provides real-time risk assessment and automated emergency notifications. The platform analyzes medical case descriptions and clinical documents to deliver instant risk evaluations and comprehensive PDF reports.

## Features

- AI-powered medical case analysis
- Clinical document processing (PDF, DOCX, TXT)
- Real-time risk assessment with severity levels
- Automated PDF report generation
- Emergency notification system via Twilio
- Modern, responsive UI with Google Material Design

## Tech Stack

### Frontend
- React
- TypeScript
- Material-UI
- Google Material Design

### Backend
- FastAPI
- Python
- Anthropic Claude
- Twilio
- ReportLab (PDF generation)

## Setup Instructions

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8 or higher
- Twilio account (for emergency notifications)
- Anthropic API key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd medical-triage-backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your credentials:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_phone
   DOCTOR_PHONE_NUMBER=your_doctor_phone
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 3001
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd medical-triage-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:3001

## Usage

1. Enter a medical case description in the text area or upload a medical document
2. Click "Analyze" to process the case
3. View the risk assessment and download the PDF report
4. For high-risk cases, the system will automatically notify the doctor via Twilio

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 