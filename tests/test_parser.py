"""
Test cases for email parser functionality
"""
import pytest
import json
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from email_parser import EmailParser
from utils import extract_sender_info, is_job_related_email, parse_gmail_date

class TestEmailParser:
    """Test email parser functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = EmailParser()
        self.sample_gmail_json = {
            "id": "test123",
            "threadId": "thread123", 
            "snippet": "Thank you for your application to Software Engineer position...",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Application Received - Software Engineer"},
                    {"name": "From", "value": "HR Team <hr@techcorp.com>"},
                    {"name": "To", "value": "john@example.com"},
                    {"name": "Date", "value": "Mon, 15 Oct 2024 10:30:00 -0700"}
                ],
                "body": {
                    "data": "VGhhbmsgeW91IGZvciB5b3VyIGFwcGxpY2F0aW9u"  # Base64 encoded
                }
            }
        }
        
        self.sample_eml_content = """From: recruiter@company.com
To: candidate@email.com  
Subject: Interview Invitation - Senior Developer
Date: Tue, 16 Oct 2024 14:20:00 +0000

Hi John,

We would like to invite you for an interview for the Senior Developer position.

Best regards,
Jane Smith
"""

    def test_parse_gmail_message(self):
        """Test parsing individual Gmail message"""
        result = self.parser._parse_gmail_message(self.sample_gmail_json, "test@gmail.com")
        
        assert result is not None
        assert result['gmail_id'] == "test123"
        assert result['account_email'] == "test@gmail.com"
        assert result['subject'] == "Application Received - Software Engineer"
        assert result['sender'] == "HR Team <hr@techcorp.com>"
        assert "application" in result['snippet'].lower()
        assert isinstance(result['date_received'], datetime)

    def test_parse_gmail_json_single_message(self):
        """Test parsing single Gmail JSON message"""
        emails = self.parser.parse_gmail_json(self.sample_gmail_json, "test@gmail.com")
        
        assert len(emails) == 1
        assert emails[0]['subject'] == "Application Received - Software Engineer"

    def test_parse_gmail_json_multiple_messages(self):
        """Test parsing multiple Gmail JSON messages"""
        messages_data = {
            "messages": [self.sample_gmail_json, self.sample_gmail_json]
        }
        
        emails = self.parser.parse_gmail_json(messages_data, "test@gmail.com")
        
        assert len(emails) == 2

    def test_parse_eml_content(self):
        """Test parsing EML content"""
        emails = self.parser.parse_eml_content(self.sample_eml_content, "test@gmail.com")
        
        assert len(emails) == 1
        assert emails[0]['subject'] == "Interview Invitation - Senior Developer"
        assert emails[0]['sender'] == "recruiter@company.com"
        assert "interview" in emails[0]['snippet'].lower()

    def test_validate_email_data(self):
        """Test email data validation"""
        valid_data = {
            'gmail_id': 'test123',
            'account_email': 'test@gmail.com',
            'subject': 'Test Subject',
            'sender': 'sender@company.com',
            'date_received': datetime.now()
        }
        
        invalid_data = {
            'gmail_id': '',  # Missing required field
            'account_email': 'test@gmail.com',
        }
        
        assert self.parser.validate_email_data(valid_data) == True
        assert self.parser.validate_email_data(invalid_data) == False

    def test_deduplicate_emails(self):
        """Test email deduplication"""
        emails = [
            {'gmail_id': 'test1', 'subject': 'Email 1'},
            {'gmail_id': 'test2', 'subject': 'Email 2'},
            {'gmail_id': 'test1', 'subject': 'Duplicate Email 1'},  # Duplicate
        ]
        
        deduplicated = self.parser.deduplicate_emails(emails)
        
        assert len(deduplicated) == 2
        gmail_ids = [email['gmail_id'] for email in deduplicated]
        assert 'test1' in gmail_ids
        assert 'test2' in gmail_ids

    def test_filter_job_related(self):
        """Test job-related email filtering"""
        emails = [
            {
                'subject': 'Application for Software Engineer Position',
                'sender': 'hr@company.com',
                'snippet': 'Thank you for applying'
            },
            {
                'subject': 'Newsletter - Weekly Updates',
                'sender': 'news@website.com',
                'snippet': 'This week in tech'
            },
            {
                'subject': 'Interview Invitation',
                'sender': 'recruiter@firm.com',
                'snippet': 'We would like to schedule an interview'
            }
        ]
        
        job_emails = self.parser.filter_job_related(emails)
        
        assert len(job_emails) == 2  # Should filter out newsletter
        subjects = [email['subject'] for email in job_emails]
        assert 'Newsletter - Weekly Updates' not in subjects

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_extract_sender_info(self):
        """Test sender information extraction"""
        # Test with name and email
        sender1 = "John Doe <john@company.com>"
        info1 = extract_sender_info(sender1)
        assert info1['name'] == "John Doe"
        assert info1['email'] == "john@company.com"
        
        # Test with email only
        sender2 = "jane@company.com"
        info2 = extract_sender_info(sender2)
        assert info2['name'] == ""
        assert info2['email'] == "jane@company.com"

    def test_is_job_related_email(self):
        """Test job-related email detection"""
        # Positive cases
        assert is_job_related_email(
            "Application for Software Engineer", 
            "hr@company.com", 
            "Thank you for applying"
        ) == True
        
        assert is_job_related_email(
            "Interview Invitation",
            "recruiter@firm.com",
            "We would like to schedule"
        ) == True
        
        # Negative case
        assert is_job_related_email(
            "Newsletter Update",
            "news@website.com", 
            "This week's updates"
        ) == False

    def test_parse_gmail_date(self):
        """Test Gmail date parsing"""
        # RFC 2822 format
        date1 = "Mon, 15 Oct 2024 10:30:00 -0700"
        parsed1 = parse_gmail_date(date1)
        assert isinstance(parsed1, datetime)
        
        # ISO format
        date2 = "2024-10-15T10:30:00Z"
        parsed2 = parse_gmail_date(date2)
        assert isinstance(parsed2, datetime)
        
        # Invalid date
        date3 = "invalid date"
        parsed3 = parse_gmail_date(date3)
        assert parsed3 is None

class TestEmailParserIntegration:
    """Integration tests for email parser"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.parser = EmailParser()
    
    @pytest.fixture
    def sample_gmail_export(self):
        """Sample Gmail export data"""
        return {
            "messages": [
                {
                    "id": "msg001",
                    "threadId": "thread001",
                    "snippet": "Thank you for your interest in the Software Engineer position at TechCorp.",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Application Received - Software Engineer"},
                            {"name": "From", "value": "HR Team <hr@techcorp.com>"},
                            {"name": "To", "value": "candidate@email.com"},
                            {"name": "Date", "value": "Mon, 15 Oct 2024 10:30:00 -0700"}
                        ]
                    }
                },
                {
                    "id": "msg002", 
                    "threadId": "thread002",
                    "snippet": "We would like to invite you for an interview.",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Interview Invitation - Senior Developer"},
                            {"name": "From", "value": "Jane Smith <jane@startup.com>"},
                            {"name": "To", "value": "candidate@email.com"},
                            {"name": "Date", "value": "Wed, 17 Oct 2024 14:15:00 -0700"}
                        ]
                    }
                }
            ]
        }
    
    def test_full_parsing_workflow(self, sample_gmail_export):
        """Test complete parsing workflow"""
        # Parse Gmail export
        emails = self.parser.parse_gmail_json(sample_gmail_export, "candidate@email.com")
        
        # Validate results
        assert len(emails) == 2
        
        # Check first email
        email1 = emails[0]
        assert email1['gmail_id'] == "msg001"
        assert email1['account_email'] == "candidate@email.com"
        assert "software engineer" in email1['subject'].lower()
        assert email1['sender_email'] == "hr@techcorp.com"
        assert email1['company'] == "techcorp"
        
        # Check second email
        email2 = emails[1]
        assert email2['gmail_id'] == "msg002"
        assert "interview" in email2['subject'].lower()
        assert email2['sender_name'] == "Jane Smith"
        
        # Test validation
        for email in emails:
            assert self.parser.validate_email_data(email) == True
        
        # Test deduplication (should remain 2 unique emails)
        deduplicated = self.parser.deduplicate_emails(emails)
        assert len(deduplicated) == 2
        
        # Test job filtering (both should be job-related)
        job_emails = self.parser.filter_job_related(emails)
        assert len(job_emails) == 2

    def test_error_handling(self):
        """Test error handling for malformed data"""
        # Test with empty data
        emails1 = self.parser.parse_gmail_json({}, "test@email.com")
        assert emails1 == []
        
        # Test with malformed JSON structure
        malformed_data = {"invalid": "structure"}
        emails2 = self.parser.parse_gmail_json(malformed_data, "test@email.com")
        assert isinstance(emails2, list)
        
        # Test with empty EML content
        emails3 = self.parser.parse_eml_content("", "test@email.com")
        assert isinstance(emails3, list)

if __name__ == "__main__":
    pytest.main([__file__])
