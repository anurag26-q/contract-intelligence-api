"""
PDF processing service using LangChain Gemini embeddings.
"""

import logging
import hashlib
from typing import List, Dict
import PyPDF2
import pdfplumber
from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import uuid

logger = logging.getLogger('api')


class PDFProcessor:
    """Service for processing PDF files with LangChain Gemini embeddings."""
    
    def __init__(self):
        """Initialize PDF processor with LangChain Gemini embeddings."""
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.qdrant_client = None
        
        # Initialize LangChain embeddings for Gemini
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        self._init_qdrant()
    
    def _init_qdrant(self):
        """Initialize Qdrant client."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
            # Create collection if it doesn't exist (Gemini embeddings are 768-dimensional)
            try:
                self.qdrant_client.get_collection(settings.QDRANT_COLLECTION_NAME)
            except Exception:
                self.qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=768,  # Gemini embedding-001 dimension
                        distance=qdrant_models.Distance.COSINE
                    ),
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
    
    def extract_pages_with_pdfplumber(self, pdf_path: str) -> List[Dict]:
        """Extract text page by page with metadata using pdfplumber."""
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    
                    page_data = {
                        'page_number': page_num,
                        'text': text,
                        'char_count': len(text),
                        'metadata': {
                            'width': page.width,
                            'height': page.height,
                        }
                    }
                    pages_data.append(page_data)
            
            return pages_data
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            raise
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Chunk text using recursive character splitting."""
        chunks = []
        text_length = len(text)
        
        # Convert token-based size to character-based (rough estimate: 1 token ≈ 4 chars)
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4
        
        start = 0
        chunk_index = 0
        
        while start < text_length:
            end = min(start + char_chunk_size, text_length)
            chunk_text = text[start:end]
            
            chunk_data = {
                'chunk_index': chunk_index,
                'text': chunk_text,
                'char_start': start,
                'char_end': end,
                'metadata': metadata or {},
            }
            chunks.append(chunk_data)
            
            chunk_index += 1
            start = end - char_overlap if end < text_length else text_length
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using LangChain Gemini."""
        try:
            # Use LangChain's embed_documents method
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Generated {len(embeddings)} embeddings using Gemini")
            return embeddings
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {e}")
            raise
    
    def store_vectors(self, chunks: List[Dict], document_id: int) -> List[str]:
        """Store chunk embeddings in Qdrant."""
        try:
            # Extract texts for embedding
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings using LangChain Gemini
            embeddings = self.generate_embeddings(texts)
            
            # Create points for Qdrant
            points = []
            vector_ids = []
            
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)
                
                point = qdrant_models.PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload={
                        'document_id': document_id,
                        'chunk_index': chunk['chunk_index'],
                        'char_start': chunk['char_start'],
                        'char_end': chunk['char_end'],
                        'text': chunk['text'][:500],  # Store preview
                        'metadata': chunk.get('metadata', {}),
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points
            )
            
            logger.info(f"Stored {len(points)} vectors in Qdrant for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Vector storage failed: {e}")
            raise
    
    def delete_document_vectors(self, document_id: int):
        """Delete all vectors for a document from Qdrant."""
        try:
            self.qdrant_client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key='document_id',
                                match=qdrant_models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted vectors for document {document_id}")
        except Exception as e:
            logger.error(f"Vector deletion failed: {e}")
