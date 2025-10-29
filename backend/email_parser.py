"""
Email parsing utilities for Gmail exports and API data
"""
import json
import email
import base64
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
import logging

from .utils import (
    extract_sender_info, 
    extract_company_from_email, 
    parse_gmail_date,
    clean_email_content,
    extract_email_metadata,
    logger
)

class EmailParser:
    """Parse emails from various sources (Gmail API, exports, EML files)"""
    
    def __init__(self):
        self.supported_formats = ['json', 'eml', 'mbox']
    
    def parse_gmail_json(self, data: Union[Dict, List], account_email: str) -> List[Dict[str, Any]]:
        """
        Parse Gmail export JSON data
        Supports both Gmail API format and Google Takeout format
        """
        emails = []
        
        try:
            # Handle different JSON structures
            if isinstance(data, dict):
                # Gmail API format
                if 'messages' in data:
                    messages = data['messages']
                elif 'payload' in data:
                    # Single message
                    messages = [data]
                else:
                    # Google Takeout format
                    messages = [data]
            elif isinstance(data, list):
                messages = data
            else:
                logger.error("Unsupported JSON format")
                return emails
            
            for message in messages:
                try:
                    parsed_email = self._parse_gmail_message(message, account_email)
                    if parsed_email:
                        emails.append(parsed_email)
                except Exception as e:
                    logger.warning(f"Failed to parse message {message.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(emails)} emails from JSON")
            return emails
            
        except Exception as e:
            logger.error(f"Failed to parse Gmail JSON: {e}")
            return emails
    
    def _parse_gmail_message(self, message: Dict[str, Any], account_email: str) -> Optional[Dict[str, Any]]:
        """Parse individual Gmail message"""
        try:
            # Extract basic metadata
            metadata = extract_email_metadata(message)
            
            # Parse date
            date_received = parse_gmail_date(metadata.get('date', ''))
            if not date_received:
                date_received = datetime.now()
            
            # Extract body content
            body_content = self._extract_message_body(message.get('payload', {}))
            
            # Clean and process content
            snippet = clean_email_content(metadata.get('snippet', ''))
            body = clean_email_content(body_content)
            
            # Extract sender information
            sender_info = extract_sender_info(metadata.get('sender', ''))
            
            return {
                'gmail_id': metadata.get('id', ''),
                'account_email': account_email,
                'subject': metadata.get('subject', 'No Subject'),
                'sender': metadata.get('sender', ''),
                'recipient': metadata.get('recipient', account_email),
                'snippet': snippet,
                'body': body,
                'date_received': date_received,
                'thread_id': metadata.get('thread_id', ''),
                'labels': metadata.get('labels', []),
                'sender_name': sender_info['name'],
                'sender_email': sender_info['email'],
                'company': extract_company_from_email(sender_info['email'])
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gmail message: {e}")
            return None
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from Gmail payload"""
        body_parts = []
        
        try:
            # Handle different payload structures
            if 'body' in payload and payload['body'].get('data'):
                # Simple message
                body_data = payload['body']['data']
                decoded = base64.urlsafe_b64decode(body_data + '===').decode('utf-8', errors='ignore')
                body_parts.append(decoded)
            
            elif 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    body_parts.extend(self._extract_part_content(part))
            
            return '\n'.join(body_parts)
            
        except Exception as e:
            logger.warning(f"Failed to extract message body: {e}")
            return ""
    
    def _extract_part_content(self, part: Dict[str, Any]) -> List[str]:
        """Recursively extract content from message parts"""
        content = []
        
        try:
            mime_type = part.get('mimeType', '')
            
            # Text content
            if mime_type.startswith('text/'):
                if 'body' in part and part['body'].get('data'):
                    body_data = part['body']['data']
                    decoded = base64.urlsafe_b64decode(body_data + '===').decode('utf-8', errors='ignore')
                    content.append(decoded)
            
            # Nested parts
            elif 'parts' in part:
                for subpart in part['parts']:
                    content.extend(self._extract_part_content(subpart))
            
        except Exception as e:
            logger.warning(f"Failed to extract part content: {e}")
        
        return content
    
    def parse_eml_content(self, eml_content: str, account_email: str) -> List[Dict[str, Any]]:
        """Parse EML (email) file content"""
        emails = []
        
        try:
            # Parse email message
            msg = email.message_from_string(eml_content)
            
            # Extract headers
            subject = self._decode_header(msg.get('Subject', 'No Subject'))
            sender = self._decode_header(msg.get('From', ''))
            recipient = self._decode_header(msg.get('To', account_email))
            date_str = msg.get('Date', '')
            message_id = msg.get('Message-ID', '')
            
            # Parse date
            date_received = parse_gmail_date(date_str)
            if not date_received:
                date_received = datetime.now()
            
            # Extract body
            body = self._extract_eml_body(msg)
            snippet = body[:200] if body else ""
            
            # Create email data
            email_data = {
                'gmail_id': message_id or f"eml_{hash(eml_content)}",
                'account_email': account_email,
                'subject': subject,
                'sender': sender,
                'recipient': recipient,
                'snippet': clean_email_content(snippet),
                'body': clean_email_content(body),
                'date_received': date_received,
                'thread_id': '',
                'labels': [],
                'sender_name': extract_sender_info(sender)['name'],
                'sender_email': extract_sender_info(sender)['email'],
                'company': extract_company_from_email(extract_sender_info(sender)['email'])
            }
            
            emails.append(email_data)
            logger.info("Successfully parsed EML content")
            
        except Exception as e:
            logger.error(f"Failed to parse EML content: {e}")
        
        return emails
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_header = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_header += part.decode(encoding, errors='ignore')
                    else:
                        decoded_header += part.decode('utf-8', errors='ignore')
                else:
                    decoded_header += part
            
            return decoded_header.strip()
            
        except Exception as e:
            logger.warning(f"Failed to decode header '{header}': {e}")
            return header
    
    def _extract_eml_body(self, msg: email.message.Message) -> str:
        """Extract body from EML message"""
        body_parts = []
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == 'text/plain':
                        charset = part.get_content_charset() or 'utf-8'
                        content = part.get_payload(decode=True)
                        if content:
                            body_parts.append(content.decode(charset, errors='ignore'))
                    
                    elif content_type == 'text/html' and not body_parts:
                        # Use HTML if no plain text found
                        charset = part.get_content_charset() or 'utf-8'
                        content = part.get_payload(decode=True)
                        if content:
                            html_content = content.decode(charset, errors='ignore')
                            # Basic HTML to text conversion
                            text_content = re.sub(r'<[^>]+>', '', html_content)
                            body_parts.append(text_content)
            else:
                # Simple message
                charset = msg.get_content_charset() or 'utf-8'
                content = msg.get_payload(decode=True)
                if content:
                    body_parts.append(content.decode(charset, errors='ignore'))
            
        except Exception as e:
            logger.warning(f"Failed to extract EML body: {e}")
        
        return '\n'.join(body_parts)
    
    def parse_mbox_file(self, mbox_path: str, account_email: str) -> List[Dict[str, Any]]:
        """Parse MBOX file (not implemented - placeholder for future)"""
        logger.warning("MBOX parsing not yet implemented")
        return []
    
    def validate_email_data(self, email_data: Dict[str, Any]) -> bool:
        """Validate parsed email data"""
        required_fields = ['gmail_id', 'account_email', 'subject', 'sender', 'date_received']
        
        for field in required_fields:
            if field not in email_data or not email_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def deduplicate_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate emails based on gmail_id"""
        seen_ids = set()
        unique_emails = []
        
        for email_data in emails:
            gmail_id = email_data.get('gmail_id')
            if gmail_id and gmail_id not in seen_ids:
                seen_ids.add(gmail_id)
                unique_emails.append(email_data)
        
        logger.info(f"Deduplicated {len(emails)} -> {len(unique_emails)} emails")
        return unique_emails
    
    def filter_job_related(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Pre-filter potentially job-related emails"""
        from .utils import is_job_related_email
        
        job_emails = []
        for email_data in emails:
            if is_job_related_email(
                email_data.get('subject', ''),
                email_data.get('sender', ''),
                email_data.get('snippet', '')
            ):
                job_emails.append(email_data)
        
        logger.info(f"Filtered {len(emails)} -> {len(job_emails)} job-related emails")
        return job_emails
    
    def batch_parse_files(self, file_paths: List[str], account_email: str) -> List[Dict[str, Any]]:
        """Parse multiple files"""
        all_emails = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if file_path.endswith('.json'):
                    data = json.loads(content)
                    emails = self.parse_gmail_json(data, account_email)
                elif file_path.endswith('.eml'):
                    emails = self.parse_eml_content(content, account_email)
                else:
                    logger.warning(f"Unsupported file format: {file_path}")
                    continue
                
                all_emails.extend(emails)
                logger.info(f"Parsed {len(emails)} emails from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to parse file {file_path}: {e}")
        
        # Deduplicate across all files
        return self.deduplicate_emails(all_emails)

