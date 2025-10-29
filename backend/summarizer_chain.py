"""
Summarizer chain for email classification and inbox summarization
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from .llm_adapter import LLMAdapter
from .db import Email, EmailCategory
from .utils import format_email_for_llm, logger

class SummarizerChain:
    """Chain pipeline for email classification and summarization"""
    
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm = llm_adapter
        self.classification_categories = [
            "Application Sent",
            "Recruiter Response", 
            "Interview",
            "Offer",
            "Rejection",
            "Other"
        ]
    
    def get_classify_email_prompt(self) -> str:
        """Get the email classification prompt template"""
        return """
You are an expert at analyzing job-related emails. Your task is to classify emails and provide concise summaries.

Classify this email into one of these categories:
- Application Sent: Emails sent by the user applying for jobs
- Recruiter Response: Responses from recruiters or HR representatives
- Interview: Interview invitations, scheduling, or follow-ups
- Offer: Job offers or offer-related communications
- Rejection: Rejection letters or negative responses
- Other: Non-job-related or unclear emails

Email to classify:
{email_content}

Provide your response as a JSON object with:
- "category": one of the exact categories above
- "confidence": confidence score from 0.0 to 1.0
- "summary": one-line summary of the email's main point
- "key_info": any important details (company name, position, date, etc.)
"""
    
    def get_summarize_inbox_prompt(self) -> str:
        """Get the inbox summarization prompt template"""
        return """
You are a career advisor analyzing a user's job search email activity. 
Create a comprehensive but concise weekly progress report.

Email Activity Summary:
{email_summaries}

Pipeline Statistics:
{pipeline_stats}

Please provide a structured summary covering:
1. Overall Progress: High-level assessment of job search activity
2. Key Highlights: Important developments (interviews, offers, etc.)
3. Action Items: What the user should focus on next
4. Pipeline Health: Assessment of application-to-response ratio

Keep the summary professional, encouraging, and actionable. Limit to 200-300 words.
"""
    
    async def classify_email(self, email_content: str) -> Dict[str, Any]:
        """Classify a single email using LLM"""
        try:
            prompt = self.get_classify_email_prompt().format(
                email_content=email_content[:2000]  # Limit content length
            )
            
            # Get structured response
            result = await self.llm.generate_structured_response(
                prompt=prompt,
                schema={
                    "category": "string",
                    "confidence": "number", 
                    "summary": "string",
                    "key_info": "object"
                },
                temperature=0.3
            )
            
            # Validate and clean result
            category = result.get('category', 'Other')
            if category not in self.classification_categories:
                logger.warning(f"Invalid category '{category}', defaulting to 'Other'")
                category = 'Other'
            
            confidence = float(result.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            
            summary = result.get('summary', 'No summary available')[:200]  # Limit length
            
            return {
                'category': category,
                'confidence': confidence,
                'summary': summary,
                'key_info': result.get('key_info', {}),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email classification failed: {e}")
            return {
                'category': 'Other',
                'confidence': 0.0,
                'summary': f'Classification error: {str(e)[:100]}',
                'key_info': {},
                'error': True
            }
    
    async def batch_classify_emails(self, emails: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple emails in batch"""
        try:
            # Prepare prompts
            prompts = []
            for email_content in emails:
                prompt = self.get_classify_email_prompt().format(
                    email_content=email_content[:2000]
                )
                prompts.append(prompt)
            
            # Process in batch
            results = await self.llm.batch_process(prompts, max_concurrent=3)
            
            # Parse results
            classifications = []
            for i, result in enumerate(results):
                try:
                    # Try to parse as JSON
                    if result.startswith('{'):
                        parsed = json.loads(result)
                        classifications.append(self._validate_classification(parsed))
                    else:
                        # Fallback parsing
                        classifications.append(self._parse_fallback_result(result))
                except Exception as e:
                    logger.warning(f"Failed to parse batch result {i}: {e}")
                    classifications.append({
                        'category': 'Other',
                        'confidence': 0.0,
                        'summary': 'Parsing error',
                        'key_info': {},
                        'error': True
                    })
            
            return classifications
            
        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            return [{'category': 'Other', 'confidence': 0.0, 'summary': 'Batch error', 'key_info': {}, 'error': True}] * len(emails)
    
    def _validate_classification(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean classification result"""
        category = result.get('category', 'Other')
        if category not in self.classification_categories:
            category = 'Other'
        
        confidence = float(result.get('confidence', 0.5))
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            'category': category,
            'confidence': confidence,
            'summary': result.get('summary', 'No summary')[:200],
            'key_info': result.get('key_info', {}),
            'processed_at': datetime.now().isoformat()
        }
    
    def _parse_fallback_result(self, result: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON results"""
        # Simple keyword-based classification
        result_lower = result.lower()
        
        category = 'Other'
        confidence = 0.3
        
        if any(word in result_lower for word in ['application', 'applied', 'applying']):
            category = 'Application Sent'
        elif any(word in result_lower for word in ['recruiter', 'hr', 'hiring']):
            category = 'Recruiter Response'
        elif any(word in result_lower for word in ['interview', 'meeting', 'call']):
            category = 'Interview'
        elif any(word in result_lower for word in ['offer', 'congratulations', 'pleased to offer']):
            category = 'Offer'
        elif any(word in result_lower for word in ['reject', 'unfortunately', 'not selected']):
            category = 'Rejection'
        
        return {
            'category': category,
            'confidence': confidence,
            'summary': result[:100],
            'key_info': {},
            'fallback_parsed': True
        }
    
    async def generate_inbox_summary(self, emails: List[Email]) -> str:
        """Generate comprehensive inbox summary"""
        try:
            # Prepare email summaries
            email_summaries = []
            for email in emails:
                email_summary = f"""
Date: {email.date_received.strftime('%Y-%m-%d') if email.date_received else 'Unknown'}
Category: {email.category}
From: {email.sender}
Subject: {email.subject}
Summary: {email.summary or 'No summary'}
"""
                email_summaries.append(email_summary.strip())
            
            # Calculate pipeline stats
            pipeline_stats = {}
            for category in self.classification_categories:
                count = sum(1 for email in emails if email.category == category)
                pipeline_stats[category] = count
            
            # Format the data for the prompt
            email_summaries_text = "\n\n".join(email_summaries[:20])  # Limit to 20 most recent
            pipeline_stats_text = "\n".join([f"- {category}: {count}" for category, count in pipeline_stats.items()])
            
            prompt = self.get_summarize_inbox_prompt().format(
                email_summaries=email_summaries_text,
                pipeline_stats=pipeline_stats_text
            )
            
            summary = await self.llm.generate_response(
                prompt,
                temperature=0.4,
                max_tokens=500
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Inbox summarization failed: {e}")
            return f"Unable to generate summary: {str(e)}"
    
    async def analyze_job_progress(self, emails: List[Email], days: int = 30) -> Dict[str, Any]:
        """Analyze job search progress over time"""
        try:
            # Filter emails by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_emails = [email for email in emails if email.date_received and email.date_received >= cutoff_date]
            
            # Calculate metrics
            total_emails = len(recent_emails)
            categories_count = {}
            companies = set()
            
            for email in recent_emails:
                category = email.category
                categories_count[category] = categories_count.get(category, 0) + 1
                
                # Extract company info
                if hasattr(email, 'company') and email.company:
                    companies.add(email.company)
            
            # Calculate conversion rates
            applications = categories_count.get('Application Sent', 0)
            responses = categories_count.get('Recruiter Response', 0)
            interviews = categories_count.get('Interview', 0)
            offers = categories_count.get('Offer', 0)
            rejections = categories_count.get('Rejection', 0)
            
            response_rate = (responses / applications * 100) if applications > 0 else 0
            interview_rate = (interviews / applications * 100) if applications > 0 else 0
            offer_rate = (offers / applications * 100) if applications > 0 else 0
            
            return {
                'period_days': days,
                'total_emails': total_emails,
                'categories': categories_count,
                'unique_companies': len(companies),
                'metrics': {
                    'applications_sent': applications,
                    'responses_received': responses,
                    'interviews_scheduled': interviews,
                    'offers_received': offers,
                    'rejections_received': rejections,
                    'response_rate_percent': round(response_rate, 1),
                    'interview_rate_percent': round(interview_rate, 1),
                    'offer_rate_percent': round(offer_rate, 1)
                },
                'companies_contacted': list(companies)[:10]  # Top 10 companies
            }
            
        except Exception as e:
            logger.error(f"Progress analysis failed: {e}")
            return {
                'error': str(e),
                'period_days': days,
                'total_emails': 0,
                'categories': {},
                'metrics': {}
            }
    
    async def suggest_follow_ups(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """Suggest follow-up actions based on email analysis"""
        try:
            suggestions = []
            now = datetime.now()
            
            for email in emails:
                if not email.date_received:
                    continue
                
                days_ago = (now - email.date_received).days
                
                # Follow-up suggestions based on category and timing
                if email.category == 'Application Sent' and days_ago >= 7:
                    if not any(e.sender == email.recipient and e.date_received > email.date_received for e in emails):
                        suggestions.append({
                            'type': 'follow_up',
                            'priority': 'medium',
                            'action': f'Follow up on application to {email.sender}',
                            'email_subject': email.subject,
                            'days_since': days_ago,
                            'reasoning': 'No response received after 1 week'
                        })
                
                elif email.category == 'Interview' and days_ago >= 3:
                    suggestions.append({
                        'type': 'thank_you',
                        'priority': 'high',
                        'action': f'Send thank you note for interview with {email.sender}',
                        'email_subject': email.subject,
                        'days_since': days_ago,
                        'reasoning': 'Interview follow-up is overdue'
                    })
                
                elif email.category == 'Recruiter Response' and days_ago >= 2:
                    suggestions.append({
                        'type': 'response',
                        'priority': 'high',
                        'action': f'Respond to recruiter {email.sender}',
                        'email_subject': email.subject,
                        'days_since': days_ago,
                        'reasoning': 'Recruiter response requires timely reply'
                    })
            
            # Sort by priority and limit results
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            suggestions.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['days_since']))
            
            return suggestions[:10]  # Top 10 suggestions
            
        except Exception as e:
            logger.error(f"Follow-up suggestions failed: {e}")
            return []
    
    async def extract_contact_info(self, email_content: str) -> Dict[str, Any]:
        """Extract contact information from email"""
        try:
            prompt = f"""
Extract contact information from this email:

{email_content[:1000]}

Please extract and return as JSON:
- company_name: company name if mentioned
- contact_person: name of person sending/mentioned
- job_title: job position if mentioned
- location: job location if mentioned  
- salary_range: salary information if mentioned
- next_steps: any mentioned next steps or deadlines
"""
            
            schema = {
                "company_name": "string or null",
                "contact_person": "string or null", 
                "job_title": "string or null",
                "location": "string or null",
                "salary_range": "string or null",
                "next_steps": "string or null"
            }
            
            return await self.llm.generate_structured_response(prompt, schema)
            
        except Exception as e:
            logger.error(f"Contact info extraction failed: {e}")
            return {
                "company_name": None,
                "contact_person": None,
                "job_title": None,
                "location": None,
                "salary_range": None,
                "next_steps": None,
                "error": str(e)
            }

