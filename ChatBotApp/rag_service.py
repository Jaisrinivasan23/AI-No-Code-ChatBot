"""
RAG (Retrieval Augmented Generation) Service
Production-level document processing and retrieval system for AI chatbots
"""

import os
import re
import pickle
import hashlib
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np

# Document processing
import PyPDF2
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

# Django imports
from django.conf import settings
from django.core.cache import cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Handles document parsing and text extraction from various file formats
    """
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text content from PDF files"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT files with encoding detection"""
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode file with supported encodings")
        except Exception as e:
            logger.error(f"Error reading TXT file: {str(e)}")
            raise
    
    @staticmethod
    def extract_text_from_csv(file_path: str) -> str:
        """Extract text from CSV files"""
        try:
            df = pd.read_csv(file_path)
            # Convert all columns to string and concatenate
            text = df.to_string(index=False)
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Main method to extract text from any supported file format
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return cls.extract_text_from_pdf(file_path)
        elif file_ext == '.txt':
            return cls.extract_text_from_txt(file_path)
        elif file_ext == '.csv':
            return cls.extract_text_from_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")


class TextChunker:
    """
    Splits documents into semantic chunks with overlap for better context retrieval
    """
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Args:
            chunk_size: Maximum number of characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', '', text)
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_chunks(self, text: str) -> List[Dict[str, any]]:
        """
        Create overlapping chunks from text with metadata
        """
        text = self.clean_text(text)
        sentences = self.split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size, save current chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append({
                    'id': chunk_id,
                    'text': current_chunk.strip(),
                    'char_count': len(current_chunk),
                    'word_count': len(current_chunk.split())
                })
                
                # Create overlap by keeping last part of current chunk
                words = current_chunk.split()
                overlap_words = words[-int(self.overlap/5):] if len(words) > 10 else []
                current_chunk = ' '.join(overlap_words) + ' ' + sentence
                chunk_id += 1
            else:
                current_chunk += ' ' + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'id': chunk_id,
                'text': current_chunk.strip(),
                'char_count': len(current_chunk),
                'word_count': len(current_chunk.split())
            })
        
        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks


class VectorStore:
    """
    Manages vector embeddings and similarity search using FAISS
    """
    
    def __init__(self, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize vector store with embedding model
        
        Args:
            embedding_model_name: Name of sentence-transformer model
                - 'all-MiniLM-L6-v2': Fast, good quality (384 dimensions)
                - 'all-mpnet-base-v2': Higher quality (768 dimensions)
        """
        self.model = SentenceTransformer(embedding_model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.chunks = []
        logger.info(f"Initialized embedding model: {embedding_model_name} ({self.dimension}D)")
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Create vector embeddings for text chunks
        """
        texts = [chunk['text'] for chunk in chunks]
        logger.info(f"Creating embeddings for {len(texts)} chunks...")
        
        # Generate embeddings in batches for efficiency
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings.astype('float32')
    
    def build_index(self, chunks: List[Dict]) -> None:
        """
        Build FAISS index from document chunks
        """
        self.chunks = chunks
        embeddings = self.create_embeddings(chunks)
        
        # Use IndexFlatL2 for exact search (good for small to medium datasets)
        # For larger datasets, consider IndexIVFFlat or IndexHNSW
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        
        logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for most relevant chunks using semantic similarity
        
        Args:
            query: User query
            top_k: Number of top results to return
            
        Returns:
            List of relevant chunks with scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk['score'] = float(distance)
                chunk['similarity'] = 1 / (1 + distance)  # Convert distance to similarity
                results.append(chunk)
        
        return results
    
    def save(self, file_path: str) -> None:
        """Save vector store to disk"""
        data = {
            'chunks': self.chunks,
            'dimension': self.dimension
        }
        
        # Save FAISS index
        faiss.write_index(self.index, f"{file_path}.faiss")
        
        # Save chunks and metadata
        with open(f"{file_path}.pkl", 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved vector store to {file_path}")
    
    def load(self, file_path: str) -> None:
        """Load vector store from disk"""
        # Load FAISS index
        self.index = faiss.read_index(f"{file_path}.faiss")
        
        # Load chunks and metadata
        with open(f"{file_path}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.dimension = data['dimension']
        
        logger.info(f"Loaded vector store from {file_path}")


class RAGService:
    """
    Main RAG service that orchestrates document processing, indexing, and retrieval
    """
    
    def __init__(self, chatbot_id: int, cache_enabled: bool = True):
        """
        Initialize RAG service for a specific chatbot
        
        Args:
            chatbot_id: ID of the chatbot
            cache_enabled: Whether to use caching
        """
        self.chatbot_id = chatbot_id
        self.cache_enabled = cache_enabled
        self.vector_store = VectorStore()
        self.chunker = TextChunker(chunk_size=500, overlap=100)
        self.doc_processor = DocumentProcessor()
        
        # Define storage paths
        self.storage_dir = os.path.join(settings.MEDIA_ROOT, 'rag_indices')
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_path = os.path.join(self.storage_dir, f'chatbot_{chatbot_id}')
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key for chatbot"""
        return f"rag_{self.chatbot_id}_{key}"
    
    def process_document(self, file_path: str) -> Dict:
        """
        Process a document: extract text, chunk, and create embeddings
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Processing statistics
        """
        logger.info(f"Processing document: {file_path}")
        
        # Extract text
        text = self.doc_processor.extract_text(file_path)
        
        # Create chunks
        chunks = self.chunker.create_chunks(text)
        
        # Build vector index
        self.vector_store.build_index(chunks)
        
        # Save index to disk
        self.vector_store.save(self.index_path)
        
        # Cache the vector store if enabled
        if self.cache_enabled:
            cache.set(
                self._get_cache_key('vector_store'),
                self.vector_store,
                timeout=3600  # 1 hour
            )
        
        stats = {
            'total_chars': len(text),
            'total_chunks': len(chunks),
            'avg_chunk_size': np.mean([c['char_count'] for c in chunks]),
            'index_size': self.vector_store.index.ntotal
        }
        
        logger.info(f"Document processed successfully: {stats}")
        return stats
    
    def load_index(self) -> bool:
        """
        Load existing index from cache or disk
        
        Returns:
            True if index loaded successfully, False otherwise
        """
        # Try cache first
        if self.cache_enabled:
            cached_store = cache.get(self._get_cache_key('vector_store'))
            if cached_store:
                self.vector_store = cached_store
                logger.info("Loaded vector store from cache")
                return True
        
        # Try loading from disk
        if os.path.exists(f"{self.index_path}.faiss"):
            try:
                self.vector_store.load(self.index_path)
                
                # Update cache
                if self.cache_enabled:
                    cache.set(
                        self._get_cache_key('vector_store'),
                        self.vector_store,
                        timeout=3600
                    )
                
                return True
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}")
                return False
        
        return False
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant context for a query
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            Combined context from top chunks
        """
        # Load index if not already loaded
        if self.vector_store.index is None:
            if not self.load_index():
                raise ValueError("No index available. Process a document first.")
        
        # Search for relevant chunks
        results = self.vector_store.search(query, top_k=top_k)
        
        # Combine chunks into context
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Context {i}]\n{result['text']}")
        
        context = "\n\n".join(context_parts)
        
        logger.info(f"Retrieved {len(results)} chunks for query: {query[:50]}...")
        return context
    
    def generate_prompt(self, query: str, context: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a prompt for the AI model with retrieved context
        
        Args:
            query: User query
            context: Retrieved context
            system_prompt: Optional custom system prompt
            
        Returns:
            Complete prompt for AI model
        """
        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant. Answer the user's question based on the provided context.
If the answer cannot be found in the context, clearly state that you don't have enough information.
Be concise, accurate, and cite specific parts of the context when relevant."""
        
        prompt = f"""{system_prompt}

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
        
        return prompt
    
    def query(self, user_question: str, top_k: int = 3, system_prompt: Optional[str] = None) -> Dict:
        """
        Main query method that retrieves context and generates prompt
        
        Args:
            user_question: User's question
            top_k: Number of context chunks to retrieve
            system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary with context and prompt
        """
        # Retrieve relevant context
        context = self.retrieve_context(user_question, top_k=top_k)
        
        # Generate prompt
        prompt = self.generate_prompt(user_question, context, system_prompt)
        
        return {
            'context': context,
            'prompt': prompt,
            'chunks_retrieved': top_k
        }
    
    def clear_cache(self) -> None:
        """Clear cached data for this chatbot"""
        if self.cache_enabled:
            cache.delete(self._get_cache_key('vector_store'))
            logger.info(f"Cleared cache for chatbot {self.chatbot_id}")
    
    def delete_index(self) -> None:
        """Delete stored index files"""
        try:
            if os.path.exists(f"{self.index_path}.faiss"):
                os.remove(f"{self.index_path}.faiss")
            if os.path.exists(f"{self.index_path}.pkl"):
                os.remove(f"{self.index_path}.pkl")
            self.clear_cache()
            logger.info(f"Deleted index for chatbot {self.chatbot_id}")
        except Exception as e:
            logger.error(f"Error deleting index: {str(e)}")


# Utility function for quick RAG setup
def setup_rag_for_chatbot(chatbot_id: int, document_path: str) -> RAGService:
    """
    Quick setup function for RAG with a chatbot
    
    Args:
        chatbot_id: ID of the chatbot
        document_path: Path to the document file
        
    Returns:
        Configured RAGService instance
    """
    rag_service = RAGService(chatbot_id)
    rag_service.process_document(document_path)
    return rag_service
