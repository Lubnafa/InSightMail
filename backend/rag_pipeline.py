"""
RAG (Retrieval-Augmented Generation) pipeline using Chroma and SentenceTransformers
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd

from .utils import create_embedding_id, logger

class RAGPipeline:
    """RAG pipeline for email search and retrieval"""
    
    def __init__(self, 
                 collection_name: str = "insightmail_emails",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "data/embeddings"):
        
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.persist_directory = persist_directory
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {embedding_model}: {e}")
            # Fallback to a smaller model
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Using fallback embedding model: all-MiniLM-L6-v2")
            except Exception as fallback_error:
                logger.error(f"Failed to load fallback model: {fallback_error}")
                raise Exception("Could not initialize any embedding model")
        
        # Initialize Chroma client
        self._init_chroma_client()
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
    
    def _init_chroma_client(self):
        """Initialize ChromaDB client"""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"Initialized Chroma client at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chroma client: {e}")
            # Fallback to in-memory client
            self.client = chromadb.Client()
            logger.warning("Using in-memory Chroma client (data will not persist)")
    
    def _get_or_create_collection(self):
        """Get or create the email collection"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Found existing collection: {self.collection_name}")
            return collection
            
        except Exception:
            # Create new collection
            try:
                collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "InSightMail email embeddings"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                return collection
                
            except Exception as e:
                logger.error(f"Failed to create collection: {e}")
                raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if not text or not text.strip():
                # Return zero vector for empty text
                return [0.0] * self.embedding_model.get_sentence_embedding_dimension()
            
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on error
            dim = getattr(self.embedding_model, 'get_sentence_embedding_dimension', lambda: 384)()
            return [0.0] * dim
    
    async def add_email(self, 
                       content: str,
                       metadata: Dict[str, Any],
                       embedding_id: Optional[str] = None) -> str:
        """Add email to vector store"""
        try:
            # Generate embedding ID if not provided
            if not embedding_id:
                embedding_id = create_embedding_id(
                    str(metadata.get('email_id', 'unknown')),
                    metadata.get('account', 'default')
                )
            
            # Generate embedding
            embedding = self.generate_embedding(content)
            
            # Prepare metadata (Chroma requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                if value is not None:
                    if isinstance(value, (datetime, pd.Timestamp)):
                        chroma_metadata[key] = value.isoformat()
                    else:
                        chroma_metadata[key] = str(value)
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[chroma_metadata],
                ids=[embedding_id]
            )
            
            logger.info(f"Added email embedding: {embedding_id}")
            return embedding_id
            
        except Exception as e:
            logger.error(f"Failed to add email embedding: {e}")
            raise
    
    async def search_similar(self, 
                           query: str, 
                           k: int = 10,
                           filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar emails"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Prepare where filter
            where_filter = None
            if filter_metadata:
                where_filter = {}
                for key, value in filter_metadata.items():
                    if value is not None:
                        where_filter[key] = str(value)
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'similarity_score': 1 - results['distances'][0][i] if results['distances'] else 0.0,
                        'distance': results['distances'][0][i] if results['distances'] else 1.0
                    })
            
            logger.info(f"Found {len(formatted_results)} similar emails for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def search_by_category(self, 
                               category: str, 
                               k: int = 10) -> List[Dict[str, Any]]:
        """Search emails by category"""
        return await self.search_similar(
            query=f"emails about {category}",
            k=k,
            filter_metadata={'category': category}
        )
    
    async def search_by_timeframe(self, 
                                start_date: str,
                                end_date: Optional[str] = None,
                                k: int = 10) -> List[Dict[str, Any]]:
        """Search emails by date range"""
        try:
            # For simple date filtering, we'll use the query with date context
            date_query = f"emails from {start_date}"
            if end_date:
                date_query += f" to {end_date}"
            
            # Get all results first (Chroma doesn't support complex date filtering easily)
            all_results = self.collection.get(
                include=["documents", "metadatas"]
            )
            
            # Filter by date manually
            filtered_results = []
            if all_results['documents']:
                for i, doc in enumerate(all_results['documents']):
                    metadata = all_results['metadatas'][i] if all_results['metadatas'] else {}
                    email_date = metadata.get('date', '')
                    
                    if email_date:
                        try:
                            # Simple date comparison (YYYY-MM-DD format)
                            if start_date <= email_date[:10]:
                                if not end_date or email_date[:10] <= end_date:
                                    filtered_results.append({
                                        'content': doc,
                                        'metadata': metadata,
                                        'similarity_score': 1.0,
                                        'distance': 0.0
                                    })
                        except Exception:
                            continue
            
            # Sort by date (newest first) and limit
            filtered_results.sort(
                key=lambda x: x['metadata'].get('date', ''), 
                reverse=True
            )
            
            return filtered_results[:k]
            
        except Exception as e:
            logger.error(f"Date search failed: {e}")
            return []
    
    async def get_similar_to_email(self, 
                                 email_id: str,
                                 k: int = 5) -> List[Dict[str, Any]]:
        """Find emails similar to a specific email"""
        try:
            # Get the email content first
            results = self.collection.get(
                ids=[email_id],
                include=["documents"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.warning(f"Email {email_id} not found in vector store")
                return []
            
            email_content = results['documents'][0]
            
            # Search for similar emails (excluding the original)
            similar = await self.search_similar(email_content, k=k+1)
            
            # Filter out the original email
            filtered_similar = [
                result for result in similar 
                if result['metadata'].get('email_id') != email_id
            ]
            
            return filtered_similar[:k]
            
        except Exception as e:
            logger.error(f"Similar email search failed: {e}")
            return []
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding from the vector store"""
        try:
            self.collection.delete(ids=[embedding_id])
            logger.info(f"Deleted embedding: {embedding_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding {embedding_id}: {e}")
            return False
    
    async def update_embedding(self, 
                             embedding_id: str,
                             content: str,
                             metadata: Dict[str, Any]) -> bool:
        """Update an existing embedding"""
        try:
            # Generate new embedding
            embedding = self.generate_embedding(content)
            
            # Prepare metadata
            chroma_metadata = {}
            for key, value in metadata.items():
                if value is not None:
                    if isinstance(value, (datetime, pd.Timestamp)):
                        chroma_metadata[key] = value.isoformat()
                    else:
                        chroma_metadata[key] = str(value)
            
            # Update in collection
            self.collection.update(
                ids=[embedding_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[chroma_metadata]
            )
            
            logger.info(f"Updated embedding: {embedding_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update embedding {embedding_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            # Get collection info
            collection_count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(
                limit=min(100, collection_count),
                include=["metadatas"]
            )
            
            # Analyze categories
            categories = {}
            accounts = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    category = metadata.get('category', 'Unknown')
                    categories[category] = categories.get(category, 0) + 1
                    
                    account = metadata.get('account')
                    if account:
                        accounts.add(account)
            
            return {
                'total_embeddings': collection_count,
                'categories': categories,
                'unique_accounts': len(accounts),
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                'total_embeddings': 0,
                'categories': {},
                'unique_accounts': 0,
                'error': str(e)
            }
    
    async def semantic_search_with_reranking(self, 
                                           query: str,
                                           k: int = 20,
                                           rerank_top_k: int = 5) -> List[Dict[str, Any]]:
        """Search with additional reranking for better results"""
        try:
            # Initial search with higher k
            initial_results = await self.search_similar(query, k=k)
            
            if len(initial_results) <= rerank_top_k:
                return initial_results
            
            # Re-rank using cross-encoder or more sophisticated scoring
            # For now, we'll use a simple relevance scoring based on keyword overlap
            reranked = self._rerank_results(query, initial_results)
            
            return reranked[:rerank_top_k]
            
        except Exception as e:
            logger.error(f"Semantic search with reranking failed: {e}")
            return []
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple reranking based on keyword overlap"""
        try:
            query_words = set(query.lower().split())
            
            for result in results:
                content = result['content'].lower()
                content_words = set(content.split())
                
                # Calculate keyword overlap
                overlap = len(query_words.intersection(content_words))
                overlap_score = overlap / len(query_words) if query_words else 0
                
                # Combine with original similarity
                original_similarity = result.get('similarity_score', 0)
                combined_score = 0.7 * original_similarity + 0.3 * overlap_score
                
                result['rerank_score'] = combined_score
            
            # Sort by rerank score
            return sorted(results, key=lambda x: x.get('rerank_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results
    
    async def export_embeddings(self, output_path: str) -> bool:
        """Export embeddings to JSON file for backup"""
        try:
            all_data = self.collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            export_data = {
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name,
                'export_date': datetime.now().isoformat(),
                'total_count': len(all_data['ids']) if all_data['ids'] else 0,
                'data': {
                    'ids': all_data['ids'],
                    'documents': all_data['documents'],
                    'metadatas': all_data['metadatas'],
                    'embeddings': all_data['embeddings']
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported {export_data['total_count']} embeddings to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    async def import_embeddings(self, input_path: str) -> bool:
        """Import embeddings from JSON file"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            data = import_data['data']
            
            if data['ids'] and data['documents']:
                self.collection.add(
                    ids=data['ids'],
                    documents=data['documents'],
                    metadatas=data['metadatas'] if data['metadatas'] else [{}] * len(data['ids']),
                    embeddings=data['embeddings'] if data['embeddings'] else None
                )
                
                logger.info(f"Imported {len(data['ids'])} embeddings from {input_path}")
                return True
            else:
                logger.warning("No data to import")
                return False
                
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False
    
    def reset_collection(self):
        """Reset the entire collection (use with caution!)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.warning(f"Reset collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")

# Global RAG pipeline instance
rag_pipeline = RAGPipeline()

