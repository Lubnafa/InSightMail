"""
Database models and operations for InSightMail
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

Base = declarative_base()

class EmailCategory(Enum):
    APPLICATION_SENT = "Application Sent"
    RECRUITER_RESPONSE = "Recruiter Response"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTION = "Rejection"
    OTHER = "Other"

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, index=True)  # Gmail message ID
    account_email = Column(String, index=True)  # Which Gmail account this is from
    subject = Column(String, index=True)
    sender = Column(String, index=True)
    recipient = Column(String)
    snippet = Column(Text)
    body = Column(Text)
    date_received = Column(DateTime, index=True)
    category = Column(String, default=EmailCategory.OTHER.value)  # Job-related classification
    confidence_score = Column(String)  # LLM confidence in classification
    summary = Column(Text)  # One-line LLM summary
    is_processed = Column(Boolean, default=False)
    embedding_id = Column(String)  # Reference to Chroma vector store
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    position_title = Column(String, index=True)
    application_date = Column(DateTime)
    status = Column(String, default="Applied")  # Applied, Replied, Interview, Offer, Rejection
    source = Column(String)  # LinkedIn, Indeed, Company Website, etc.
    notes = Column(Text)
    last_contact_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    def __init__(self, db_path: str = "data/insightmail.db"):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def add_email(self, email_data: Dict[str, Any]) -> Email:
        """Add a new email to the database"""
        with self.SessionLocal() as db:
            email = Email(**email_data)
            db.add(email)
            db.commit()
            db.refresh(email)
            return email
    
    def get_email_by_gmail_id(self, gmail_id: str) -> Optional[Email]:
        """Get email by Gmail ID"""
        with self.SessionLocal() as db:
            return db.query(Email).filter(Email.gmail_id == gmail_id).first()
    
    def get_emails_by_account(self, account_email: str) -> List[Email]:
        """Get all emails for a specific Gmail account"""
        with self.SessionLocal() as db:
            return db.query(Email).filter(Email.account_email == account_email).all()
    
    def get_emails_by_category(self, category: EmailCategory) -> List[Email]:
        """Get emails by job category"""
        with self.SessionLocal() as db:
            return db.query(Email).filter(Email.category == category.value).all()
    
    def get_recent_emails(self, days: int = 30) -> List[Email]:
        """Get emails from the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with self.SessionLocal() as db:
            return db.query(Email).filter(
                Email.date_received >= cutoff_date
            ).order_by(Email.date_received.desc()).all()
    
    def update_email_classification(self, email_id: int, category: str, summary: str, confidence: float):
        """Update email classification results"""
        with self.SessionLocal() as db:
            email = db.query(Email).filter(Email.id == email_id).first()
            if email:
                email.category = category
                email.summary = summary
                email.confidence_score = str(confidence)
                email.is_processed = True
                email.updated_at = datetime.utcnow()
                db.commit()
    
    def get_job_pipeline_stats(self) -> Dict[str, int]:
        """Get statistics for job application pipeline"""
        with self.SessionLocal() as db:
            stats = {}
            for category in EmailCategory:
                count = db.query(Email).filter(Email.category == category.value).count()
                stats[category.value] = count
            return stats
    
    def add_job_application(self, app_data: Dict[str, Any]) -> JobApplication:
        """Add a new job application"""
        with self.SessionLocal() as db:
            application = JobApplication(**app_data)
            db.add(application)
            db.commit()
            db.refresh(application)
            return application
    
    def get_all_applications(self) -> List[JobApplication]:
        """Get all job applications"""
        with self.SessionLocal() as db:
            return db.query(JobApplication).order_by(JobApplication.application_date.desc()).all()
    
    def search_emails(self, query: str, limit: int = 50) -> List[Email]:
        """Search emails by content"""
        with self.SessionLocal() as db:
            return db.query(Email).filter(
                (Email.subject.contains(query)) |
                (Email.snippet.contains(query)) |
                (Email.sender.contains(query))
            ).order_by(Email.date_received.desc()).limit(limit).all()

# Global database instance
db_manager = DatabaseManager()

