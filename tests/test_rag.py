"""
Test cases for RAG pipeline functionality
"""
import pytest
import asyncio
import tempfile
import os
import shutil
import json
from datetime import datetime
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rag_pipeline import RAGPipeline
from utils import create_embedding_id

class TestRAGPipeline:
    """Test RAG pipeline functionality"""
    
    def setup_method(self):
        """Setup test fixtures with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGPipeline(
            collection_name="test_collection",
            persist_directory=os.path.join(self.temp_dir, "embeddings")
        )
        
        # Sample email data
        self.sample_emails = [
            {
                'content': 'Thank you for your application to the Software Engineer position at TechCorp. We have received your resume.',
                'metadata': {
                    'email_id': 1,
                    'account': 'test@gmail.com',
                    'category': 'Application Sent',
                    'date': '2024-10-15T10:30:00Z',
                    'subject': 'Application Received - Software Engineer',
                    'sender': 'hr@techcorp.com'
                }
            },
            {
                'content': 'We would like to schedule an interview for the Senior Developer position. Are you available next week?',
                'metadata': {
                    'email_id': 2,
                    'account': 'test@gmail.com',
                    'category': 'Interview',
                    'date': '2024-10-16T14:20:00Z',
                    'subject': 'Interview Invitation - Senior Developer',
                    'sender': 'recruiter@startup.com'
                }
            },
            {
                'content': 'Unfortunately, we have decided to move forward with other candidates for the Data Scientist role.',
                'metadata': {
                    'email_id': 3,
                    'account': 'test@gmail.com',
                    'category': 'Rejection',
                    'date': '2024-10-17T09:15:00Z',
                    'subject': 'Update on Data Scientist Application',
                    'sender': 'hiring@bigtech.com'
                }
            }
        ]
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_embedding_generation(self):
        """Test embedding generation"""
        text = "This is a test email about job application"
        embedding = self.rag.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_empty_text_embedding(self):
        """Test embedding generation for empty text"""
        embedding = self.rag.generate_embedding("")
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        # Should return zero vector for empty text
        assert all(x == 0.0 for x in embedding)
    
    @pytest.mark.asyncio
    async def test_add_email(self):
        """Test adding email to vector store"""
        email = self.sample_emails[0]
        
        embedding_id = await self.rag.add_email(
            content=email['content'],
            metadata=email['metadata']
        )
        
        assert embedding_id is not None
        assert isinstance(embedding_id, str)
        assert email['metadata']['account'] in embedding_id
    
    @pytest.mark.asyncio 
    async def test_search_similar(self):
        """Test similarity search"""
        # Add sample emails
        for email in self.sample_emails:
            await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
        
        # Search for job applications
        results = await self.rag.search_similar("software engineer application", k=2)
        
        assert isinstance(results, list)
        assert len(results) <= 2
        
        if results:
            result = results[0]
            assert 'content' in result
            assert 'metadata' in result
            assert 'similarity_score' in result
            assert isinstance(result['similarity_score'], float)
            assert 0 <= result['similarity_score'] <= 1

    @pytest.mark.asyncio
    async def test_search_by_category(self):
        """Test search by category"""
        # Add sample emails
        for email in self.sample_emails:
            await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
        
        # Search for interview emails
        results = await self.rag.search_by_category("Interview", k=5)
        
        assert isinstance(results, list)
        # Should find at least one interview email
        if results:
            assert any(
                result['metadata'].get('category') == 'Interview' 
                for result in results
            )

    @pytest.mark.asyncio
    async def test_search_by_timeframe(self):
        """Test search by date range"""
        # Add sample emails
        for email in self.sample_emails:
            await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
        
        # Search within a date range
        results = await self.rag.search_by_timeframe(
            start_date="2024-10-15",
            end_date="2024-10-16",
            k=5
        )
        
        assert isinstance(results, list)
        # Should find emails within the date range
        for result in results:
            date_str = result['metadata'].get('date', '')
            if date_str:
                assert '2024-10-15' <= date_str[:10] <= '2024-10-16'

    @pytest.mark.asyncio
    async def test_update_embedding(self):
        """Test updating an existing embedding"""
        email = self.sample_emails[0]
        
        # Add initial email
        embedding_id = await self.rag.add_email(
            content=email['content'],
            metadata=email['metadata']
        )
        
        # Update with new content
        new_content = "Updated: Thank you for your application. We will review it soon."
        new_metadata = email['metadata'].copy()
        new_metadata['category'] = 'Recruiter Response'
        
        success = await self.rag.update_embedding(
            embedding_id=embedding_id,
            content=new_content,
            metadata=new_metadata
        )
        
        assert success == True
        
        # Verify update by searching
        results = await self.rag.search_similar("will review", k=1)
        assert len(results) > 0
        assert "review" in results[0]['content'].lower()

    @pytest.mark.asyncio
    async def test_delete_embedding(self):
        """Test deleting an embedding"""
        email = self.sample_emails[0]
        
        # Add email
        embedding_id = await self.rag.add_email(
            content=email['content'],
            metadata=email['metadata']
        )
        
        # Delete embedding
        success = await self.rag.delete_embedding(embedding_id)
        assert success == True
        
        # Verify deletion - search should not find the deleted content
        results = await self.rag.search_similar(email['content'][:50], k=5)
        # Results should be empty or not contain the deleted content
        assert all(
            email['content'][:20] not in result['content'] 
            for result in results
        )

    def test_collection_stats(self):
        """Test getting collection statistics"""
        stats = self.rag.get_collection_stats()
        
        assert isinstance(stats, dict)
        assert 'total_embeddings' in stats
        assert 'categories' in stats
        assert 'unique_accounts' in stats
        assert 'collection_name' in stats
        assert 'embedding_model' in stats
        
        assert isinstance(stats['total_embeddings'], int)
        assert isinstance(stats['categories'], dict)
        assert isinstance(stats['unique_accounts'], int)

    @pytest.mark.asyncio
    async def test_semantic_search_with_reranking(self):
        """Test semantic search with reranking"""
        # Add sample emails
        for email in self.sample_emails:
            await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
        
        # Test reranking
        results = await self.rag.semantic_search_with_reranking(
            query="software engineer job application",
            k=10,
            rerank_top_k=2
        )
        
        assert isinstance(results, list)
        assert len(results) <= 2
        
        if results:
            # Results should have rerank scores
            for result in results:
                assert 'rerank_score' in result
                assert isinstance(result['rerank_score'], float)

    @pytest.mark.asyncio
    async def test_get_similar_to_email(self):
        """Test finding emails similar to a specific email"""
        # Add sample emails
        embedding_ids = []
        for email in self.sample_emails:
            embedding_id = await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
            embedding_ids.append(embedding_id)
        
        # Find similar emails to the first one
        similar = await self.rag.get_similar_to_email(
            email_id=embedding_ids[0],
            k=2
        )
        
        assert isinstance(similar, list)
        assert len(similar) <= 2
        
        # Should not include the original email
        if similar:
            for result in similar:
                assert result['metadata'].get('email_id') != self.sample_emails[0]['metadata']['email_id']

    @pytest.mark.asyncio
    async def test_export_import_embeddings(self):
        """Test exporting and importing embeddings"""
        # Add sample emails
        for email in self.sample_emails:
            await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
        
        # Export embeddings
        export_path = os.path.join(self.temp_dir, "export.json")
        success = await self.rag.export_embeddings(export_path)
        assert success == True
        assert os.path.exists(export_path)
        
        # Verify export file structure
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        assert 'collection_name' in export_data
        assert 'total_count' in export_data
        assert 'data' in export_data
        assert export_data['total_count'] == len(self.sample_emails)
        
        # Reset collection
        self.rag.reset_collection()
        
        # Import embeddings
        success = await self.rag.import_embeddings(export_path)
        assert success == True
        
        # Verify import worked by searching
        results = await self.rag.search_similar("software engineer", k=5)
        assert len(results) > 0

class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGPipeline(
            collection_name="integration_test",
            persist_directory=os.path.join(self.temp_dir, "embeddings")
        )
    
    def teardown_method(self):
        """Clean up"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete RAG workflow"""
        # Sample job search emails
        job_emails = [
            {
                'content': 'Thank you for applying to Google for the Software Engineer role. We are reviewing your application.',
                'metadata': {
                    'email_id': 1,
                    'account': 'jobseeker@gmail.com',
                    'category': 'Application Sent',
                    'date': datetime.now().isoformat(),
                    'company': 'Google'
                }
            },
            {
                'content': 'We would like to schedule a technical interview for the backend developer position at Facebook.',
                'metadata': {
                    'email_id': 2,
                    'account': 'jobseeker@gmail.com',
                    'category': 'Interview',
                    'date': datetime.now().isoformat(),
                    'company': 'Facebook' 
                }
            },
            {
                'content': 'Congratulations! We are pleased to offer you the position of Senior Developer at Netflix.',
                'metadata': {
                    'email_id': 3,
                    'account': 'jobseeker@gmail.com',
                    'category': 'Offer',
                    'date': datetime.now().isoformat(),
                    'company': 'Netflix'
                }
            }
        ]
        
        # 1. Add emails to vector store
        embedding_ids = []
        for email in job_emails:
            embedding_id = await self.rag.add_email(
                content=email['content'],
                metadata=email['metadata']
            )
            embedding_ids.append(embedding_id)
        
        assert len(embedding_ids) == 3
        
        # 2. Test various search scenarios
        
        # Search for Google-related emails
        google_results = await self.rag.search_similar("Google software engineer application", k=5)
        assert len(google_results) > 0
        assert any("google" in result['content'].lower() for result in google_results)
        
        # Search for interview emails
        interview_results = await self.rag.search_by_category("Interview", k=5)
        assert len(interview_results) > 0
        assert any("interview" in result['content'].lower() for result in interview_results)
        
        # Search for offers
        offer_results = await self.rag.search_similar("job offer congratulations", k=5)
        assert len(offer_results) > 0
        assert any(result['metadata'].get('category') == 'Offer' for result in offer_results)
        
        # 3. Test semantic search capabilities
        semantic_results = await self.rag.search_similar(
            "What companies gave me positive responses?", 
            k=5
        )
        assert len(semantic_results) > 0
        
        # 4. Test collection statistics
        stats = self.rag.get_collection_stats()
        assert stats['total_embeddings'] == 3
        assert 'Interview' in stats['categories']
        assert 'Offer' in stats['categories']
        assert stats['unique_accounts'] == 1
        
        # 5. Test similar email finding
        similar_to_first = await self.rag.get_similar_to_email(embedding_ids[0], k=2)
        assert len(similar_to_first) <= 2
        # Should not include the original email
        original_id = job_emails[0]['metadata']['email_id']
        assert all(
            result['metadata'].get('email_id') != original_id 
            for result in similar_to_first
        )

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in RAG pipeline"""
        # Test search with empty collection
        results = await self.rag.search_similar("test query", k=5)
        assert isinstance(results, list)
        assert len(results) == 0
        
        # Test adding email with malformed metadata
        try:
            await self.rag.add_email(
                content="test content",
                metadata={"invalid": datetime.now()}  # datetime not serializable
            )
            # Should not raise exception, should handle gracefully
        except Exception as e:
            pytest.fail(f"Should handle malformed metadata gracefully: {e}")
        
        # Test deleting non-existent embedding
        success = await self.rag.delete_embedding("non_existent_id")
        assert success == False

class TestUtilityFunctions:
    """Test RAG utility functions"""
    
    def test_create_embedding_id(self):
        """Test embedding ID creation"""
        email_id = "msg123"
        account = "user@gmail.com"
        
        embedding_id = create_embedding_id(email_id, account)
        
        assert isinstance(embedding_id, str)
        assert email_id in embedding_id
        assert account in embedding_id
        assert "_" in embedding_id  # Should be separated by underscore

if __name__ == "__main__":
    pytest.main([__file__])
