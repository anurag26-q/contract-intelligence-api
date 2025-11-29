"""
PDF processing service using LangChain's vector database integration.
"""

import logging
from typing import List, Dict
from django.conf import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain.schema import Document as LangChainDocument
from qdrant_client import QdrantClient

logger = logging.getLogger('api')


class PDFProcessor:
    """Service for processing PDF files with LangChain vector database."""
    
    def __init__(self):
        """Initialize PDF processor with LangChain components."""
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        
        # Initialize LangChain embeddings for Gemini
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 4,  # Convert tokens to chars (approx)
            chunk_overlap=self.chunk_overlap * 4,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        # Initialize Qdrant client for collection management
        self.qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        
        # Initialize LangChain Qdrant vector store
        self.vector_store = None
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize LangChain Qdrant vector store."""
        try:
            # Create LangChain Qdrant instance
            self.vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                embeddings=self.embeddings,
            )
            logger.info(f"Initialized LangChain Qdrant vector store: {settings.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
    
    def extract_pages_with_langchain(self, pdf_path: str) -> List[Dict]:
        """Extract text page by page using LangChain PyPDFLoader."""
        try:
            # Use LangChain's PDF loader
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            pages_data = []
            for page_num, page in enumerate(pages, start=1):
                page_data = {
                    'page_number': page_num,
                    'text': page.page_content,
                    'char_count': len(page.page_content),
                    'metadata': page.metadata
                }
                pages_data.append(page_data)
            
            logger.info(f"Extracted {len(pages_data)} pages using LangChain PyPDFLoader")
            return pages_data
        except Exception as e:
            logger.error(f"LangChain PDF extraction failed: {e}")
            raise
    
    def chunk_text_with_langchain(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Chunk text using LangChain RecursiveCharacterTextSplitter."""
        try:
            # Use LangChain's text splitter
            chunks = self.text_splitter.split_text(text)
            
            chunks_data = []
            char_position = 0
            
            for chunk_index, chunk_text in enumerate(chunks):
                chunk_data = {
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'char_start': char_position,
                    'char_end': char_position + len(chunk_text),
                    'metadata': metadata or {},
                }
                chunks_data.append(chunk_data)
                char_position += len(chunk_text)
            
            logger.info(f"Created {len(chunks_data)} chunks using LangChain RecursiveCharacterTextSplitter")
            return chunks_data
        except Exception as e:
            logger.error(f"LangChain text chunking failed: {e}")
            raise
    
    def store_vectors(self, chunks: List[Dict], document_id: int) -> List[str]:
        """Store chunk embeddings using LangChain Qdrant."""
        try:
            # Convert chunks to LangChain Document objects
            documents = []
            for chunk in chunks:
                # Create metadata for each chunk
                chunk_metadata = {
                    'document_id': document_id,
                    'chunk_index': chunk['chunk_index'],
                    'char_start': chunk['char_start'],
                    'char_end': chunk['char_end'],
                }
                
                # Add any additional metadata from chunk
                chunk_metadata.update(chunk.get('metadata', {}))
                
                doc = LangChainDocument(
                    page_content=chunk['text'],
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            # Use LangChain's add_documents method
            # This handles embedding generation and storage automatically
            vector_ids = self.vector_store.add_documents(documents)
            
            logger.info(f"Stored {len(documents)} vectors using LangChain Qdrant for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Vector storage failed: {e}")
            raise
    
    def delete_document_vectors(self, document_id: int):
        """Delete all vectors for a document using LangChain Qdrant."""
        try:
            # Use LangChain's delete method with filter
            # Note: LangChain Qdrant uses the underlying client for deletion
            from qdrant_client.http import models as qdrant_models
            
            self.qdrant_client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key='metadata.document_id',  # Note: LangChain stores metadata differently
                                match=qdrant_models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted vectors for document {document_id} using LangChain Qdrant")
        except Exception as e:
            logger.error(f"Vector deletion failed: {e}")
