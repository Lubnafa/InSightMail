# Sample Gmail Export Data

This directory contains sample email data for testing InSightMail functionality. These files demonstrate different Gmail export formats and contain realistic (but fictional) job-related emails.

## 📁 Files

### `sample_gmail.json`
- **Format**: Gmail API JSON export format
- **Contains**: 8 sample emails covering all job search categories:
  - Application confirmations
  - Recruiter outreach
  - Interview invitations  
  - Job offers
  - Rejections
  - Follow-up emails
- **Use**: Primary test dataset for bulk email processing

### `sample_email.eml`
- **Format**: Standard EML (Email Message) format
- **Contains**: Single technical interview scheduling email
- **Use**: Test EML parsing functionality

### `job_rejection.eml`
- **Format**: EML with HTML content
- **Contains**: Professional rejection email from a large company
- **Use**: Test HTML email parsing and rejection classification

## 🚀 Usage

### Quick Test

1. **Start InSightMail**:
   ```bash
   # Terminal 1: Backend
   cd backend && python -m uvicorn main:app --reload
   
   # Terminal 2: Frontend  
   cd frontend && streamlit run app.py
   ```

2. **Upload Sample Data**:
   - Navigate to "Email Upload" in the dashboard
   - Enter account email: `demo@gmail.com`
   - Upload `sample_gmail.json`
   - Wait for processing to complete

3. **Explore Results**:
   - Check "Dashboard" for overview metrics
   - Visit "Job Pipeline" to see categorized emails
   - Use "Ask My Inbox" to search: *"Show me all interview emails"*

### Programmatic Loading

```python
# From project root
import sys
sys.path.append('backend')

from email_parser import EmailParser

# Load sample data
parser = EmailParser()
emails = parser.batch_parse_files([
    'data/samples/sample_gmail.json',
    'data/samples/sample_email.eml', 
    'data/samples/job_rejection.eml'
], 'demo@gmail.com')

print(f"Loaded {len(emails)} sample emails")

# Show categories
from collections import Counter
categories = Counter(email.get('category', 'Unknown') for email in emails)
print("Categories:", dict(categories))
```

## 📊 Expected Results

After processing the sample data, you should see:

- **Total Emails**: ~10 emails
- **Categories**:
  - Application Sent: 1-2 emails
  - Recruiter Response: 2-3 emails  
  - Interview: 2-3 emails
  - Offer: 1 email
  - Rejection: 1-2 emails
  - Other: 0-1 emails

- **Companies**: TechCorp, InnovateAI, StartupXYZ, BigTech Corp, etc.
- **Response Rate**: ~60-80% (since these are curated examples)
- **Date Range**: October 2024

## 🔍 Testing Scenarios

### Classification Testing

- **Application Confirmations**: Test detection of "application received" emails
- **Recruiter Outreach**: Test identification of unsolicited recruiter emails  
- **Interview Scheduling**: Test parsing of interview invitations with specific details
- **Offers**: Test recognition of job offer emails with positive language
- **Rejections**: Test detection of rejection emails with polite but negative content

### Search Testing

Try these queries in "Ask My Inbox":

- *"Which companies sent me interview invitations?"*
- *"Show me all emails from Google"*
- *"What job offers did I receive?"*
- *"Find emails about software engineer positions"*
- *"Which emails need follow-up?"*

### Analytics Testing

Check the Analytics dashboard for:

- **Pipeline Conversion**: Application → Response → Interview → Offer flow
- **Company Analysis**: Most active companies and engagement scores  
- **Timing Patterns**: When emails were received
- **Performance Metrics**: Response rates and success indicators

## 🛠️ Customization

### Adding Your Own Samples

1. **Export from Gmail**:
   - Use Google Takeout or Gmail API
   - Save as JSON or EML format

2. **Anonymize Data**:
   ```python
   # Remove personal information
   from utils import anonymize_email_content
   cleaned_content = anonymize_email_content(email_content)
   ```

3. **Add to Samples**:
   - Place files in this directory
   - Update this README with descriptions
   - Test with InSightMail

### Modifying Existing Samples

- **Edit JSON**: Modify `sample_gmail.json` to add/remove emails
- **Update Headers**: Change dates, senders, subjects as needed
- **Content**: Modify base64-encoded body content (use online encoder/decoder)

## 📝 Notes

- **Privacy**: All sample data is fictional - no real email addresses or companies
- **Base64 Encoding**: Email bodies in JSON format are base64 encoded
- **HTML Content**: Some emails contain HTML for testing parsing robustness  
- **Realistic Content**: Emails mirror real job search communications for accurate testing

## 🐛 Troubleshooting

**No emails processed?**
- Check file format (JSON/EML supported)
- Verify account email is entered correctly
- Look for parsing errors in backend logs

**Wrong classifications?**
- Adjust LLM prompts in `summarizer_chain.py`
- Check confidence scores in email details
- Try different Ollama models (mistral:7b vs phi3:mini)

**Search not working?**
- Wait for embedding generation to complete
- Check ChromaDB status in backend logs
- Verify vector database is initialized
