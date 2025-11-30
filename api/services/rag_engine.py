"""
RAG Engine for question answering using LangChain with Google Gemini.
Uses LangChain's vector store integration and LCEL chains.
"""

import logging
from django.conf import settings
from typing import List, Dict, Iterator

from langchain_chroma import Chroma
from langchain_chroma import Chroma
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
# LangChain imports
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from api.models import DocumentChunk

logger = logging.getLogger('api')


class RAGEngine:
    """RAG engine using LangChain LCEL with Google Gemini and vector store."""
    
    def __init__(self):
        """Initialize RAG engine with LangChain components."""
        # Initialize Gemini LLM
        self.llm = GoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )
        logger.info(f"Initialized Gemini LLM with model: {settings.GEMINI_MODEL}")
        logger.info(f"Google API key: {settings.GOOGLE_API_KEY}")
        logger.info(f"Temperature: {settings.GEMINI_TEMPERATURE}")
        logger.info(f"Max output tokens: {settings.GEMINI_MAX_TOKENS}")
        logger.info(f"Gemini LLM: {self.llm}")
        
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        logger.info(f"Initialized embeddings with model: {settings.GEMINI_EMBEDDING_MODEL}")
        logger.info(f"Google API key: {settings.GOOGLE_API_KEY}")
        logger.info(f"Embeddings: {self.embeddings}")
        
        # LangChain Chroma vector store
        self.vector_store = Chroma(
            persist_directory=settings.CHROMA_DB_DIR,
            embedding_function=self.embeddings,
        )
        logger.info(f"Initialized LangChain Chroma vector store with persist directory: {settings.CHROMA_DB_DIR}")
        logger.info(f"Embeddings: {self.embeddings}")
        logger.info(f"Vector store: {self.vector_store}")
        
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
        
        logger.info("RAGEngine initialized with LangChain Chroma vector store and Gemini")
    
    def retrieve(self, question: str, document_ids: List[int] = None, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant document chunks using LangChain vector store.
        
        Args:
            question: User's question
            document_ids: Optional list of document IDs to filter
            top_k: Number of chunks to retrieve
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Build filter for specific documents if provided
            search_kwargs = {"k": top_k}
            
            if document_ids:
                # Chroma filter format: {"document_id": {"$in": [id1, id2]}}
                # Or if just one: {"document_id": id}
                if len(document_ids) == 1:
                    search_kwargs["filter"] = {"document_id": document_ids[0]}
                else:
                    search_kwargs["filter"] = {"document_id": {"$in": document_ids}}
            
            # Use LangChain vector store similarity search
            logger.debug(f"Similarity search kwargs: {search_kwargs} for question: {question}")
            docs = self.vector_store.similarity_search(
                question,
                **search_kwargs
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
            logger.info(f"Retrieved {len(chunks)} chunks using LangChain vector store")
            if len(chunks) > 0:
                # Log a sample of metadata for debugging
                try:
                    sample_meta = docs[0].metadata
                    logger.debug(f"Sample doc metadata: {sample_meta}")
                except Exception:
                    pass
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
            yield f"\n__CITATIONS__:{json.dumps(citations)}"
            
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
