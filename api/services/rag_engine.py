"""
RAG Engine for question answering using LangChain with Google Gemini.
Uses LangChain Expression Language (LCEL) for building the RAG pipeline.
"""

import logging
from typing import List, Dict, Iterator
from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

# LangChain imports
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores import Qdrant

from api.models import DocumentChunk

logger = logging.getLogger('api')


class RAGEngine:
    """RAG engine using LangChain LCEL with Google Gemini."""
    
    def __init__(self):
        """Initialize RAG engine with LangChain components."""
        # Initialize Gemini LLM
        self.llm = GoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        # Initialize Qdrant client
        self.qdrant_client = Qdrant Client(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        
        # LangChain Qdrant vector store
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings,
        )
        
        # Create RAG prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are answering questions about legal contracts. Use ONLY the provided context."),
            ("human", """Context:
{context}

Instructions:
1. Answer based solely on the context provided
2. If the answer is not in the context, say "I cannot answer this based on the provided documents"
3. Include specific references to document sections when possible
4. Be concise and accurate

Question: {question}

Answer:""")
        ])
        
        logger.info("RAGEngine initialized with LangChain and Google Gemini")
    
    def retrieve(self, question: str, document_ids: List[int] = None, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant document chunks using vector search.
        
        Args:
            question: User's question
            document_ids: Optional list of document IDs to filter
            top_k: Number of chunks to retrieve
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Build filter for specific documents if provided
            search_filter = None
            if document_ids:
                search_filter = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchAny(any=document_ids)
                        )
                    ]
                )
            
            # Use LangChain vector store for similarity search
            if search_filter:
                docs = self.vector_store.similarity_search(
                    question,
                    k=top_k,
                    filter=search_filter
                )
            else:
                docs = self.vector_store.similarity_search(
                    question,
                    k=top_k
                )
            
            # Convert to our format
            chunks = []
            for doc in docs:
                chunk_data = {
                    'text': doc.page_content,
                    'document_id': doc.metadata.get('document_id'),
                    'chunk_index': doc.metadata.get('chunk_index'),
                    'char_start': doc.metadata.get('char_start'),
                    'char_end': doc.metadata.get('char_end'),
                    'score': doc.metadata.get('score', 0.0),
                }
                chunks.append(chunk_data)
            
            logger.info(f"Retrieved {len(chunks)} chunks for question")
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}", exc_info=True)
            return []
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_id = chunk.get('document_id', 'unknown')
            text = chunk.get('text', '')
            context_parts.append(f"[Document {doc_id}, Chunk {i}]\n{text}\n")
        
        return '\n'.join(context_parts)
    
    def generate_answer(self, question: str, chunks: List[Dict]) -> tuple[str, List[Dict]]:
        """
        Generate answer using LangChain LCEL chain.
        
        Args:
            question: User's question
            chunks: Retrieved document chunks
            
        Returns:
            Tuple of (answer text, citations list)
        """
        try:
            # Build LCEL chain: format context -> prompt -> LLM -> parse output
            rag_chain = (
                {
                    "context": lambda x: self._format_context(chunks),
                    "question": RunnablePassthrough()
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            # Invoke the chain
            answer = rag_chain.invoke(question)
            
            # Extract citations from chunks
            citations = self._extract_citations(chunks)
            
            logger.info(f"Generated answer with {len(citations)} citations")
            return answer, citations
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return "I encountered an error processing your question.", []
    
    def generate_answer_stream(self, question: str, chunks: List[Dict]) -> Iterator[str]:
        """
        Generate streaming answer using LangChain LCEL chain.
        
        Args:
            question: User's question
            chunks: Retrieved document chunks
            
        Yields:
            Answer tokens as they're generated
        """
        try:
            # Build LCEL chain for streaming
            rag_chain = (
                {
                    "context": lambda x: self._format_context(chunks),
                    "question": RunnablePassthrough()
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            # Stream the response
            for chunk in rag_chain.stream(question):
                yield chunk
            
            # After streaming answer, send citations
            citations = self._extract_citations(chunks)
            import json
            yield f"__CITATIONS__:{json.dumps(citations)}"
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield "I encountered an error processing your question."
    
    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        """Extract citation information from retrieved chunks."""
        citations = []
        for chunk in chunks:
            citation = {
                'document_id': chunk.get('document_id'),
                'chunk_index': chunk.get('chunk_index'),
                'char_start': chunk.get('char_start'),
                'char_end': chunk.get('char_end'),
            }
            
            # Try to get page number from database
            try:
                db_chunk = DocumentChunk.objects.get(
                    document_id=chunk.get('document_id'),
                    chunk_index=chunk.get('chunk_index')
                )
                if db_chunk.page:
                    citation['page_number'] = db_chunk.page.page_number
            except:
                pass
            
            citations.append(citation)
        
        return citations
