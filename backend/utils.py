"""
Utility functions for InSightMail
"""
import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from email.utils import parseaddr, parsedate_to_datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_email_content(content: str) -> str:
    """Clean and normalize email content"""
    if not content:
        return ""
    
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove email signatures (common patterns)
    signature_patterns = [
        r'--\s*\n.*',  # Standard email signature
        r'Sent from my.*',  # Mobile signatures
        r'Best regards.*',  # Common sign-offs
        r'Thanks.*\n.*\n.*@.*',  # Email with signature
    ]
    
    for pattern in signature_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    return content.strip()

def extract_sender_info(sender: str) -> Dict[str, str]:
    """Extract name and email from sender string"""
    name, email = parseaddr(sender)
    return {
        "name": name.strip() if name else "",
        "email": email.strip().lower() if email else ""
    }

def extract_company_from_email(email_address: str) -> str:
    """Extract company name from email domain"""
    if not email_address or '@' not in email_address:
        return ""
    
    domain = email_address.split('@')[1].lower()
    
    # Remove common domain suffixes
    domain = re.sub(r'\.(com|org|net|edu|gov)$', '', domain)
    
    # Handle common patterns
    if domain.startswith('mail.'):
        domain = domain[5:]
    
    return domain.replace('.', ' ').title()

def is_job_related_email(subject: str, sender: str, content: str) -> bool:
    """Quick heuristic to identify potentially job-related emails"""
    job_keywords = [
        'application', 'interview', 'position', 'job', 'career', 'opportunity',
        'recruiter', 'hiring', 'candidate', 'resume', 'cv', 'offer',
        'rejection', 'thank you for applying', 'next steps', 'screening'
    ]
    
    text_content = f"{subject} {sender} {content}".lower()
    
    return any(keyword in text_content for keyword in job_keywords)

def generate_content_hash(content: str) -> str:
    """Generate a hash for content deduplication"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def parse_gmail_date(date_str: str) -> Optional[datetime]:
    """Parse Gmail date string to datetime object"""
    try:
        if isinstance(date_str, str):
            # Try to parse RFC 2822 format first
            try:
                return parsedate_to_datetime(date_str)
            except:
                # Try ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_str
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    return filename[:255]  # Limit length

def extract_email_metadata(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and normalize metadata from email data"""
    metadata = {
        'id': email_data.get('id', ''),
        'thread_id': email_data.get('threadId', ''),
        'labels': email_data.get('labelIds', []),
        'snippet': email_data.get('snippet', ''),
        'size_estimate': email_data.get('sizeEstimate', 0),
    }
    
    # Extract headers
    headers = {}
    payload = email_data.get('payload', {})
    for header in payload.get('headers', []):
        headers[header['name'].lower()] = header['value']
    
    metadata.update({
        'subject': headers.get('subject', ''),
        'sender': headers.get('from', ''),
        'recipient': headers.get('to', ''),
        'date': headers.get('date', ''),
        'message_id': headers.get('message-id', ''),
    })
    
    return metadata

def format_email_for_llm(email: Dict[str, Any]) -> str:
    """Format email data for LLM processing"""
    template = """
Subject: {subject}
From: {sender}
To: {recipient}
Date: {date}

Content:
{content}
"""
    
    return template.format(
        subject=email.get('subject', 'No Subject'),
        sender=email.get('sender', 'Unknown'),
        recipient=email.get('recipient', 'Unknown'),
        date=email.get('date', 'Unknown'),
        content=email.get('snippet', '')[:500]  # Limit content length
    ).strip()

def create_embedding_id(email_id: str, account: str) -> str:
    """Create unique embedding ID for vector store"""
    return f"{account}_{email_id}"

def validate_email_address(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_urls_from_content(content: str) -> List[str]:
    """Extract URLs from email content"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, content)

def anonymize_email_content(content: str) -> str:
    """Anonymize sensitive information in email content"""
    # Replace email addresses
    content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
    
    # Replace phone numbers
    content = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', content)
    content = re.sub(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', '[PHONE]', content)
    
    # Replace potential SSNs
    content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', content)
    
    return content

def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate simple similarity score between two texts"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def get_email_priority_score(email_data: Dict[str, Any]) -> int:
    """Calculate priority score for email processing (higher = more important)"""
    score = 0
    
    subject = email_data.get('subject', '').lower()
    sender = email_data.get('sender', '').lower()
    
    # High priority keywords
    high_priority = ['offer', 'interview', 'urgent', 'immediate']
    medium_priority = ['application', 'position', 'opportunity', 'recruiter']
    
    for keyword in high_priority:
        if keyword in subject:
            score += 10
    
    for keyword in medium_priority:
        if keyword in subject:
            score += 5
    
    # Sender-based scoring
    if 'noreply' in sender or 'no-reply' in sender:
        score -= 3
    
    if any(word in sender for word in ['hr', 'recruiter', 'talent']):
        score += 7
    
    return max(0, score)

class EmailProcessor:
    """Utility class for email processing operations"""
    
    def __init__(self):
        self.processed_emails = set()
    
    def is_duplicate(self, email_id: str) -> bool:
        """Check if email has already been processed"""
        return email_id in self.processed_emails
    
    def mark_processed(self, email_id: str):
        """Mark email as processed"""
        self.processed_emails.add(email_id)
    
    def batch_process_emails(self, emails: List[Dict[str, Any]], batch_size: int = 10) -> List[List[Dict[str, Any]]]:
        """Split emails into batches for processing"""
        return [emails[i:i + batch_size] for i in range(0, len(emails), batch_size)]

# Global email processor instance
email_processor = EmailProcessor()

