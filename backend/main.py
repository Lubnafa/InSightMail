"""
FastAPI main application for InSightMail
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import datetime, timedelta

from .db import DatabaseManager, db_manager, EmailCategory, Email
from .email_parser import EmailParser
from .rag_pipeline import RAGPipeline
from .llm_adapter import LLMAdapter
from .summarizer_chain import SummarizerChain
from .utils import logger

# Initialize FastAPI app
app = FastAPI(
    title="InSightMail API",
    description="LLM-powered email copilot for job hunting progress tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
email_parser = EmailParser()
rag_pipeline = RAGPipeline()
llm_adapter = LLMAdapter()
summarizer_chain = SummarizerChain(llm_adapter)

# Pydantic models for API
class EmailData(BaseModel):
    gmail_id: str
    account_email: str
    subject: str
    sender: str
    recipient: str
    snippet: str
    body: Optional[str] = ""
    date_received: datetime

class ClassifyRequest(BaseModel):
    email_content: str

class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class SummaryResponse(BaseModel):
    summary: str
    stats: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "InSightMail API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        stats = db_manager.get_job_pipeline_stats()
        
        # Check LLM connection (if available)
        llm_status = await llm_adapter.health_check()
        
        return {
            "status": "healthy",
            "database": "connected",
            "llm": llm_status,
            "email_count": sum(stats.values())
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/emails/upload")
async def upload_gmail_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    account_email: str = "default@gmail.com"
):
    """Upload and process Gmail export file"""
    try:
        # Read uploaded file
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
            emails = email_parser.parse_gmail_json(data, account_email)
        else:
            # Assume EML format
            emails = email_parser.parse_eml_content(content.decode('utf-8'), account_email)
        
        # Add background task to process emails
        background_tasks.add_task(process_emails_batch, emails)
        
        return {
            "message": f"Upload successful. Processing {len(emails)} emails.",
            "email_count": len(emails),
            "account": account_email
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

@app.post("/emails/process")
async def process_emails_endpoint(background_tasks: BackgroundTasks):
    """Process unprocessed emails"""
    try:
        # Get unprocessed emails
        with db_manager.SessionLocal() as db:
            unprocessed = db.query(Email).filter(Email.is_processed == False).all()
        
        if not unprocessed:
            return {"message": "No unprocessed emails found"}
        
        # Add background task
        background_tasks.add_task(
            process_emails_batch, 
            [email_to_dict(email) for email in unprocessed]
        )
        
        return {
            "message": f"Processing {len(unprocessed)} emails in background",
            "count": len(unprocessed)
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/emails/classify")
async def classify_email(request: ClassifyRequest):
    """Classify a single email"""
    try:
        result = await summarizer_chain.classify_email(request.email_content)
        return result
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.get("/emails")
async def get_emails(
    account: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get emails with optional filtering"""
    try:
        with db_manager.SessionLocal() as db:
            query = db.query(Email)
            
            if account:
                query = query.filter(Email.account_email == account)
            
            if category:
                query = query.filter(Email.category == category)
            
            emails = query.order_by(Email.date_received.desc()).offset(offset).limit(limit).all()
            
            return {
                "emails": [email_to_dict(email) for email in emails],
                "count": len(emails),
                "total": query.count()
            }
            
    except Exception as e:
        logger.error(f"Get emails failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get emails failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get job pipeline statistics"""
    try:
        stats = db_manager.get_job_pipeline_stats()
        recent_emails = db_manager.get_recent_emails(7)  # Last 7 days
        
        return {
            "pipeline_stats": stats,
            "recent_count": len(recent_emails),
            "categories": [category.value for category in EmailCategory]
        }
        
    except Exception as e:
        logger.error(f"Get stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get stats failed: {str(e)}")

@app.post("/query")
async def query_emails(request: QueryRequest):
    """Query emails using RAG"""
    try:
        # Search similar emails
        results = await rag_pipeline.search_similar(request.query, k=request.limit)
        
        # Generate answer using LLM
        context = "\n\n".join([result['content'] for result in results])
        answer = await llm_adapter.generate_response(
            f"Based on the following emails, answer this question: {request.query}\n\nEmails:\n{context}"
        )
        
        return {
            "answer": answer,
            "sources": results,
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/summary")
async def get_summary(days: int = 7) -> SummaryResponse:
    """Get job search summary"""
    try:
        # Get recent emails
        recent_emails = db_manager.get_recent_emails(days)
        
        # Generate summary
        summary = await summarizer_chain.generate_inbox_summary(recent_emails)
        
        # Get stats
        stats = db_manager.get_job_pipeline_stats()
        
        # Prepare recent activity
        recent_activity = []
        for email in recent_emails[:10]:  # Latest 10
            recent_activity.append({
                "date": email.date_received.isoformat(),
                "subject": email.subject,
                "sender": email.sender,
                "category": email.category,
                "summary": email.summary
            })
        
        return SummaryResponse(
            summary=summary,
            stats=stats,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Get summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get summary failed: {str(e)}")

@app.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    """Delete an email"""
    try:
        with db_manager.SessionLocal() as db:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                raise HTTPException(status_code=404, detail="Email not found")
            
            # Remove from vector store
            if email.embedding_id:
                await rag_pipeline.delete_embedding(email.embedding_id)
            
            db.delete(email)
            db.commit()
            
        return {"message": "Email deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete email failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete email failed: {str(e)}")

# Background task functions
async def process_emails_batch(emails: List[Dict[str, Any]]):
    """Background task to process emails"""
    logger.info(f"Processing batch of {len(emails)} emails")
    
    for email_data in emails:
        try:
            # Check if already processed
            existing = db_manager.get_email_by_gmail_id(email_data.get('gmail_id'))
            if existing and existing.is_processed:
                continue
            
            # Classify email
            email_content = f"{email_data.get('subject', '')} {email_data.get('snippet', '')}"
            classification = await summarizer_chain.classify_email(email_content)
            
            # Store or update email
            if existing:
                db_manager.update_email_classification(
                    existing.id,
                    classification['category'],
                    classification['summary'],
                    classification['confidence']
                )
                email_id = existing.id
            else:
                email_data.update({
                    'category': classification['category'],
                    'summary': classification['summary'],
                    'confidence_score': str(classification['confidence']),
                    'is_processed': True
                })
                new_email = db_manager.add_email(email_data)
                email_id = new_email.id
            
            # Add to vector store
            embedding_id = f"{email_data.get('account_email')}_{email_data.get('gmail_id')}"
            await rag_pipeline.add_email(
                content=email_content,
                metadata={
                    'email_id': email_id,
                    'account': email_data.get('account_email'),
                    'category': classification['category'],
                    'date': email_data.get('date_received')
                },
                embedding_id=embedding_id
            )
            
            logger.info(f"Processed email {email_data.get('gmail_id')}: {classification['category']}")
            
        except Exception as e:
            logger.error(f"Error processing email {email_data.get('gmail_id')}: {e}")
            continue

def email_to_dict(email: Email) -> Dict[str, Any]:
    """Convert Email model to dictionary"""
    return {
        "id": email.id,
        "gmail_id": email.gmail_id,
        "account_email": email.account_email,
        "subject": email.subject,
        "sender": email.sender,
        "recipient": email.recipient,
        "snippet": email.snippet,
        "date_received": email.date_received.isoformat() if email.date_received else None,
        "category": email.category,
        "summary": email.summary,
        "confidence_score": email.confidence_score,
        "is_processed": email.is_processed,
        "created_at": email.created_at.isoformat() if email.created_at else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

