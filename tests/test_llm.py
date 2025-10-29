"""
Test cases for LLM adapter functionality
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from llm_adapter import LLMAdapter

class TestLLMAdapter:
    """Test LLM adapter functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.llm = LLMAdapter(
            base_url="http://localhost:11434",
            model_name="mistral:7b",
            backup_model="phi3:mini"
        )
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_get):
        """Test successful health check"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "mistral:7b"},
                {"name": "phi3:mini"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = await self.llm.health_check()
        
        assert "healthy" in result
        assert "mistral:7b" in result
        mock_get.assert_called_once()
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_backup_model(self, mock_get):
        """Test health check with backup model"""
        # Mock response with only backup model available
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "phi3:mini"},
                {"name": "other:model"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = await self.llm.health_check()
        
        assert "healthy" in result
        assert "backup" in result
        assert "phi3:mini" in result
        assert self.llm.current_model == "phi3:mini"
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_no_models(self, mock_get):
        """Test health check with no suitable models"""
        # Mock response with no suitable models
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "unsupported:model"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = await self.llm.health_check()
        
        assert "no suitable models" in result
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_list_models(self, mock_get):
        """Test listing available models"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "mistral:7b"},
                {"name": "phi3:mini"},
                {"name": "llama3.2:3b"}
            ]
        }
        mock_get.return_value = mock_response
        
        models = await self.llm.list_models()
        
        assert isinstance(models, list)
        assert "mistral:7b" in models
        assert "phi3:mini" in models
        assert "llama3.2:3b" in models
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_post):
        """Test successful response generation"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from the LLM."
        }
        mock_post.return_value = mock_response
        
        prompt = "Classify this email as job-related or not."
        result = await self.llm.generate_response(prompt)
        
        assert isinstance(result, str)
        assert "test response" in result.lower()
        mock_post.assert_called_once()
        
        # Verify request structure
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == "mistral:7b"
        assert call_args[1]['json']['prompt'] == prompt
        assert call_args[1]['json']['stream'] == False
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, mock_post):
        """Test response generation with system prompt"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Classified as job-related."
        }
        mock_post.return_value = mock_response
        
        prompt = "Please classify this email."
        system_prompt = "You are an expert email classifier."
        
        result = await self.llm.generate_response(prompt, system_prompt=system_prompt)
        
        assert isinstance(result, str)
        
        # Verify system prompt was included
        call_args = mock_post.call_args
        assert call_args[1]['json']['system'] == system_prompt
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_generate_response_api_error(self, mock_post):
        """Test response generation with API error"""
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = await self.llm.generate_response("Test prompt")
        
        assert "Error" in result
        assert "LLM request failed" in result
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_generate_structured_response(self, mock_post):
        """Test structured JSON response generation"""
        # Mock successful structured response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"category": "Application Sent", "confidence": 0.9, "summary": "Job application confirmation"}'
        }
        mock_post.return_value = mock_response
        
        prompt = "Classify this email"
        schema = {
            "category": "string",
            "confidence": "number",
            "summary": "string"
        }
        
        result = await self.llm.generate_structured_response(prompt, schema)
        
        assert isinstance(result, dict)
        assert "category" in result
        assert "confidence" in result
        assert "summary" in result
        assert result["category"] == "Application Sent"
        assert result["confidence"] == 0.9
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_generate_structured_response_invalid_json(self, mock_post):
        """Test structured response with invalid JSON"""
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is not valid JSON response"
        }
        mock_post.return_value = mock_response
        
        prompt = "Classify this email"
        schema = {"category": "string"}
        
        result = await self.llm.generate_structured_response(prompt, schema)
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["parsed"] == False
    
    @pytest.mark.asyncio
    async def test_classify_text(self):
        """Test text classification"""
        categories = ["Application Sent", "Interview", "Rejection", "Other"]
        text = "Thank you for your application to our Software Engineer position."
        
        with patch.object(self.llm, 'generate_structured_response') as mock_generate:
            mock_generate.return_value = {
                "category": "Application Sent",
                "confidence": 0.85,
                "reasoning": "Email confirms receipt of job application"
            }
            
            result = await self.llm.classify_text(text, categories)
            
            assert isinstance(result, dict)
            assert result["category"] == "Application Sent"
            assert result["confidence"] == 0.85
            assert "reasoning" in result
            
            # Verify the method was called with correct parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[0]
            assert text in call_args[0]  # prompt should contain the text
            assert all(cat in call_args[0] for cat in categories)  # prompt should contain categories
    
    @pytest.mark.asyncio
    async def test_classify_text_error_handling(self):
        """Test classification with error handling"""
        categories = ["Category1", "Category2"]
        text = "Test text"
        
        with patch.object(self.llm, 'generate_structured_response') as mock_generate:
            # Simulate an exception
            mock_generate.side_effect = Exception("API error")
            
            result = await self.llm.classify_text(text, categories)
            
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == True
            assert result["category"] == categories[0]  # Should default to first category
            assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_summarize_text(self):
        """Test text summarization"""
        long_text = """
        This is a very long email about a job application process. 
        The candidate applied for a software engineer position at TechCorp.
        The company has reviewed the application and wants to schedule an interview.
        They are impressed with the candidate's background in Python and machine learning.
        """
        
        with patch.object(self.llm, 'generate_response') as mock_generate:
            mock_generate.return_value = "Interview scheduled for software engineer position at TechCorp."
            
            result = await self.llm.summarize_text(long_text, max_length=50)
            
            assert isinstance(result, str)
            assert len(result) > 0
            mock_generate.assert_called_once()
            
            # Verify summarization parameters were passed
            call_args = mock_generate.call_args[0]
            assert "50" in call_args[0]  # max_length should be in prompt
            assert long_text in call_args[0]  # original text should be in prompt
    
    @pytest.mark.asyncio
    async def test_extract_information(self):
        """Test information extraction"""
        text = """
        Dear John,
        
        We would like to invite you for an interview for the Senior Python Developer 
        position at Google. The salary range is $120,000 - $150,000. 
        Please let us know your availability for next week.
        
        Best regards,
        Jane Smith, HR Manager
        """
        
        fields = ["company_name", "position", "salary_range", "contact_person"]
        
        with patch.object(self.llm, 'generate_structured_response') as mock_generate:
            mock_generate.return_value = {
                "company_name": "Google",
                "position": "Senior Python Developer",
                "salary_range": "$120,000 - $150,000",
                "contact_person": "Jane Smith"
            }
            
            result = await self.llm.extract_information(text, fields)
            
            assert isinstance(result, dict)
            assert result["company_name"] == "Google"
            assert result["position"] == "Senior Python Developer"
            assert result["salary_range"] == "$120,000 - $150,000"
            assert result["contact_person"] == "Jane Smith"
    
    @pytest.mark.asyncio
    async def test_batch_process(self):
        """Test batch processing of prompts"""
        prompts = [
            "Classify this as job-related: Application received",
            "Classify this as job-related: Weather update",
            "Classify this as job-related: Interview invitation"
        ]
        
        with patch.object(self.llm, 'generate_response') as mock_generate:
            mock_generate.side_effect = [
                "Job-related: Application",
                "Not job-related: Weather",
                "Job-related: Interview"
            ]
            
            results = await self.llm.batch_process(prompts, max_concurrent=2)
            
            assert isinstance(results, list)
            assert len(results) == len(prompts)
            assert all(isinstance(result, str) for result in results)
            assert "Application" in results[0]
            assert "Weather" in results[1]
            assert "Interview" in results[2]
    
    @pytest.mark.asyncio
    async def test_batch_process_with_exceptions(self):
        """Test batch processing with some failures"""
        prompts = ["prompt1", "prompt2", "prompt3"]
        
        with patch.object(self.llm, 'generate_response') as mock_generate:
            # First call succeeds, second fails, third succeeds
            mock_generate.side_effect = [
                "Success 1",
                Exception("API timeout"),
                "Success 3"
            ]
            
            results = await self.llm.batch_process(prompts)
            
            assert len(results) == 3
            assert results[0] == "Success 1"
            assert "Error" in results[1]  # Exception should be handled
            assert results[2] == "Success 3"
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_get_model_info(self, mock_post):
        """Test getting model information"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "mistral:7b",
            "details": {
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
            }
        }
        mock_post.return_value = mock_response
        
        info = await self.llm.get_model_info()
        
        assert isinstance(info, dict)
        assert "model" in info
        assert info["model"] == "mistral:7b"
    
    @pytest.mark.asyncio
    async def test_chat_completion(self):
        """Test chat-style completion"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Classify this email as job-related or not."},
            {"role": "assistant", "content": "I'll help you classify the email."},
            {"role": "user", "content": "The email says: Thank you for your application."}
        ]
        
        with patch.object(self.llm, 'generate_response') as mock_generate:
            mock_generate.return_value = "This email is job-related as it acknowledges a job application."
            
            result = await self.llm.chat_completion(messages)
            
            assert isinstance(result, str)
            assert "job-related" in result.lower()
            
            # Verify the conversation was formatted correctly
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[0]
            prompt = call_args[0]
            
            assert "System:" in prompt
            assert "Human:" in prompt
            assert "Assistant:" in prompt
            assert all(msg["content"] in prompt for msg in messages)

class TestLLMAdapterIntegration:
    """Integration tests for LLM adapter"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.llm = LLMAdapter()
    
    @pytest.mark.asyncio
    async def test_email_classification_workflow(self):
        """Test complete email classification workflow"""
        # Sample job-related email
        email_content = """
        Subject: Application Received - Software Engineer Position
        From: hr@techcorp.com
        
        Dear Candidate,
        
        Thank you for your interest in the Software Engineer position at TechCorp.
        We have received your application and will review it shortly.
        
        Best regards,
        HR Team
        """
        
        categories = ["Application Sent", "Recruiter Response", "Interview", "Offer", "Rejection", "Other"]
        
        with patch.object(self.llm, 'generate_structured_response') as mock_generate:
            mock_generate.return_value = {
                "category": "Recruiter Response",
                "confidence": 0.92,
                "reasoning": "Email acknowledges receipt of job application from company HR"
            }
            
            # Test classification
            classification_result = await self.llm.classify_text(email_content, categories)
            
            assert classification_result["category"] == "Recruiter Response"
            assert classification_result["confidence"] > 0.9
            assert "reasoning" in classification_result
        
        with patch.object(self.llm, 'generate_response') as mock_generate:
            mock_generate.return_value = "Company acknowledged job application receipt, positive initial response."
            
            # Test summarization
            summary = await self.llm.summarize_text(email_content, max_length=100)
            
            assert isinstance(summary, str)
            assert len(summary) > 0
            assert any(word in summary.lower() for word in ["application", "company", "job"])
        
        with patch.object(self.llm, 'generate_structured_response') as mock_generate:
            mock_generate.return_value = {
                "company_name": "TechCorp",
                "position": "Software Engineer",
                "contact_person": "HR Team",
                "next_steps": "Application review"
            }
            
            # Test information extraction
            fields = ["company_name", "position", "contact_person", "next_steps"]
            extracted_info = await self.llm.extract_information(email_content, fields)
            
            assert extracted_info["company_name"] == "TechCorp"
            assert extracted_info["position"] == "Software Engineer"
            assert extracted_info["contact_person"] == "HR Team"

if __name__ == "__main__":
    pytest.main([__file__])
