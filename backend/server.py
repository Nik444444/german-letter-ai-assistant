import os
import io
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import pytesseract
import PyPDF2
import fitz  # PyMuPDF
import json
from dotenv import load_dotenv
from llm_manager import llm_manager
from models import (
    UserRegistration, UserLogin, UserProfile, UserInDB, 
    ApiKeyUpdate, users_collection, UserApiKeys
)
from auth import (
    hash_password, verify_password, create_access_token, 
    encrypt_api_key, decrypt_api_key, get_current_user_token,
    generate_user_id
)
import os

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Reinitialize LLM manager after loading environment variables
llm_manager.load_providers()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="German Letter AI Assistant with Multi-LLM Support")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LetterAnalysisRequest(BaseModel):
    text: str
    language: str = "en"

class LetterAnalysisResponse(BaseModel):
    analysis: dict
    summary: str
    actions_needed: List[str]
    deadlines: List[str]
    response_template: Optional[str] = None
    llm_provider: Optional[str] = None

def extract_text_from_image(image_file) -> str:
    """Extract text from image using OCR"""
    try:
        image = Image.open(image_file)
        # Configure Tesseract for German language
        custom_config = r'--oem 3 --psm 6 -l deu+eng'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to extract text from image: {str(e)}")

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF"""
    try:
        text = ""
        # Try with PyMuPDF first (better for complex PDFs)
        try:
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
        except:
            # Fallback to PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")

def create_analysis_prompt(text: str, language: str) -> str:
    """Create a comprehensive prompt for LLM to analyze German letters"""
    
    language_instructions = {
        "en": {
            "analyze_in": "English",
            "template": """You are an expert assistant helping migrants and refugees understand German official letters. Analyze this German letter and provide a comprehensive response in English.

LETTER TEXT:
{text}

Please provide a detailed analysis in the following JSON format:
{{
    "summary": "Brief summary of what this letter is about",
    "sender": "Who sent this letter (agency/organization)",
    "letter_type": "Type of letter (e.g., Jobcenter notification, BAMF decision, etc.)",
    "main_content": "Main content explanation in simple English",
    "actions_needed": ["List of specific actions the recipient needs to take"],
    "deadlines": ["Any important deadlines mentioned with dates"],
    "documents_required": ["Any documents that need to be submitted"],
    "consequences": "What happens if no action is taken",
    "urgency_level": "LOW/MEDIUM/HIGH",
    "response_template": "A template response letter in German if a response is needed (or null if no response needed)"
}}

Make sure to:
1. Explain everything in simple, clear English
2. Highlight any urgent deadlines
3. Explain the consequences of not responding
4. Provide practical next steps
5. If a response is needed, include a polite German template"""
        },
        "ru": {
            "analyze_in": "Russian",
            "template": """Вы эксперт-помощник, помогающий мигрантам и беженцам понимать немецкие официальные письма. Проанализируйте это немецкое письмо и предоставьте подробный ответ на русском языке.

ТЕКСТ ПИСЬМА:
{text}

Предоставьте детальный анализ в следующем JSON формате:
{{
    "summary": "Краткое резюме о чем это письмо",
    "sender": "Кто отправил это письмо (агентство/организация)",
    "letter_type": "Тип письма (например, уведомление Jobcenter, решение BAMF и т.д.)",
    "main_content": "Объяснение основного содержания простыми словами на русском",
    "actions_needed": ["Список конкретных действий, которые нужно предпринять получателю"],
    "deadlines": ["Любые важные сроки с датами"],
    "documents_required": ["Любые документы, которые нужно предоставить"],
    "consequences": "Что произойдет, если не предпринять никаких действий",
    "urgency_level": "LOW/MEDIUM/HIGH",
    "response_template": "Шаблон ответного письма на немецком языке, если требуется ответ (или null, если ответ не нужен)"
}}

Убедитесь, что вы:
1. Объясняете все простыми, понятными словами на русском
2. Выделяете срочные сроки
3. Объясняете последствия неответа
4. Предоставляете практические следующие шаги
5. Если нужен ответ, включите вежливый немецкий шаблон"""
        }
    }
    
    lang_config = language_instructions.get(language, language_instructions["en"])
    return lang_config["template"].format(text=text)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "German Letter AI Assistant with Multi-LLM Support"}

@app.get("/api/llm-status")
async def get_llm_status():
    """Get status of all LLM providers"""
    try:
        status = llm_manager.get_provider_status()
        return {
            "status": "success",
            "providers": status,
            "total_providers": len(status),
            "active_providers": sum(1 for p in status.values() if p["status"] == "active")
        }
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/test-llm")
async def test_llm_providers():
    """Test all LLM providers with a simple prompt"""
    try:
        test_prompt = "Say 'Hello, I am working!' in JSON format: {\"message\": \"Hello, I am working!\"}"
        
        results = {}
        for provider in llm_manager.providers:
            try:
                if provider.can_make_request() and provider.config.status.value == "active":
                    provider.record_request()
                    content = await provider.generate_content(test_prompt)
                    provider.record_success()
                    results[provider.name] = {
                        "status": "success",
                        "response": content[:100] + "..." if len(content) > 100 else content
                    }
                else:
                    results[provider.name] = {
                        "status": "skipped",
                        "reason": "Rate limited or not active"
                    }
            except Exception as e:
                provider.record_error(str(e))
                results[provider.name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "test_results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing LLM providers: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/analyze-file", response_model=LetterAnalysisResponse)
async def analyze_file(
    file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """Analyze uploaded file (image or PDF) and extract letter information"""
    
    try:
        # Validate file type
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type not specified")
        
        # Extract text based on file type
        if file.content_type.startswith('image/'):
            text = extract_text_from_image(file.file)
        elif file.content_type == 'application/pdf':
            text = extract_text_from_pdf(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an image or PDF file.")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file")
        
        # Analyze with Multi-LLM system
        prompt = create_analysis_prompt(text, language)
        
        try:
            response_text, used_provider = await llm_manager.generate_content(prompt)
            logger.info(f"Successfully analyzed using provider: {used_provider}")
        except Exception as e:
            logger.error(f"All LLM providers failed: {e}")
            return LetterAnalysisResponse(
                analysis={"error": "All LLM providers failed", "details": str(e)},
                summary="All AI services are currently unavailable. Please try again later.",
                actions_needed=["Please try again later when AI services are available"],
                deadlines=[],
                response_template=None,
                llm_provider="none"
            )
        
        # Parse the JSON response
        try:
            # Check if response is empty
            if not response_text or response_text.strip() == "":
                logger.error("Empty response from LLM")
                return LetterAnalysisResponse(
                    analysis={"error": "Empty response from AI"},
                    summary="AI service returned empty response. Please try again.",
                    actions_needed=["Please try uploading the file again"],
                    deadlines=[],
                    response_template=None,
                    llm_provider=used_provider
                )
            
            # Extract JSON from response
            logger.info(f"LLM response: {response_text[:200]}...")
            
            # Try to find JSON in the response
            json_text = response_text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    json_text = response_text[json_start:json_end].strip()
            elif response_text.startswith("{"):
                # Already looks like JSON
                json_text = response_text
            else:
                # Try to extract JSON from the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx+1]
                else:
                    raise json.JSONDecodeError("No JSON found in response", response_text, 0)
            
            logger.info(f"Attempting to parse JSON: {json_text[:200]}...")
            analysis_data = json.loads(json_text)
            
            # Validate required fields
            if not isinstance(analysis_data, dict):
                raise ValueError("Response is not a valid JSON object")
            
            return LetterAnalysisResponse(
                analysis=analysis_data,
                summary=analysis_data.get("summary", "Analysis completed"),
                actions_needed=analysis_data.get("actions_needed", []),
                deadlines=analysis_data.get("deadlines", []),
                response_template=analysis_data.get("response_template"),
                llm_provider=used_provider
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Full response text: {response_text}")
            
            # Fallback: return structured response with raw text
            return LetterAnalysisResponse(
                analysis={
                    "raw_response": response_text,
                    "error": "Failed to parse AI response",
                    "summary": "AI provided analysis but in unexpected format"
                },
                summary="AI analysis completed but response format was unexpected. Please try again.",
                actions_needed=["Please try uploading the file again", "Check if the document contains clear German text"],
                deadlines=[],
                response_template=None,
                llm_provider=used_provider
            )
        
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

@app.post("/api/analyze-text", response_model=LetterAnalysisResponse)
async def analyze_text(request: LetterAnalysisRequest):
    """Analyze text directly without file upload"""
    
    try:
        prompt = create_analysis_prompt(request.text, request.language)
        
        try:
            response_text, used_provider = await llm_manager.generate_content(prompt)
            logger.info(f"Successfully analyzed using provider: {used_provider}")
        except Exception as e:
            logger.error(f"All LLM providers failed: {e}")
            return LetterAnalysisResponse(
                analysis={"error": "All LLM providers failed", "details": str(e)},
                summary="All AI services are currently unavailable. Please try again later.",
                actions_needed=["Please try again later when AI services are available"],
                deadlines=[],
                response_template=None,
                llm_provider="none"
            )
        
        # Parse the JSON response
        try:
            # Check if response is empty
            if not response_text or response_text.strip() == "":
                logger.error("Empty response from LLM")
                return LetterAnalysisResponse(
                    analysis={"error": "Empty response from AI"},
                    summary="AI service returned empty response. Please try again.",
                    actions_needed=["Please try with different text"],
                    deadlines=[],
                    response_template=None,
                    llm_provider=used_provider
                )
            
            # Extract JSON from response
            logger.info(f"LLM response: {response_text[:200]}...")
            
            # Try to find JSON in the response
            json_text = response_text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    json_text = response_text[json_start:json_end].strip()
            elif response_text.startswith("{"):
                # Already looks like JSON
                json_text = response_text
            else:
                # Try to extract JSON from the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx+1]
                else:
                    raise json.JSONDecodeError("No JSON found in response", response_text, 0)
            
            logger.info(f"Attempting to parse JSON: {json_text[:200]}...")
            analysis_data = json.loads(json_text)
            
            # Validate required fields
            if not isinstance(analysis_data, dict):
                raise ValueError("Response is not a valid JSON object")
            
            return LetterAnalysisResponse(
                analysis=analysis_data,
                summary=analysis_data.get("summary", "Analysis completed"),
                actions_needed=analysis_data.get("actions_needed", []),
                deadlines=analysis_data.get("deadlines", []),
                response_template=analysis_data.get("response_template"),
                llm_provider=used_provider
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Full response text: {response_text}")
            
            # Fallback: return structured response with raw text
            return LetterAnalysisResponse(
                analysis={
                    "raw_response": response_text,
                    "error": "Failed to parse AI response",
                    "summary": "AI provided analysis but in unexpected format"
                },
                summary="AI analysis completed but response format was unexpected. Please try again.",
                actions_needed=["Please try with different text", "Check if the text contains clear German content"],
                deadlines=[],
                response_template=None,
                llm_provider=used_provider
            )
        
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)