"""
RAG (Retrieval-Augmented Generation) engine for question answering.
"""

import logging
import openai
from django.conf import settings
from qdrant_client import QdrantClient
from typing import List, Dict, Tuple
import uuid

logger = logging.getLogger('api')

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY


class RAGEngine:
    """Service for RAG-based question answering over contracts."""
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.qdrant_client = None
        self._init_qdrant()
    
    def _init_qdrant(self):
        """Initialize Qdrant client."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
    
    def retrieve(self, question: str, document_ids: List[int] = None, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant chunks for a question."""
        try:
            # Generate query embedding
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=[question]
            )
            query_embedding = response.data[0].embedding
            
            # Build filter for specific documents if provided
            search_filter = None
            if document_ids:
                search_filter = {
                    'must': [
                        {
                            'key': 'document_id',
                            'match': {'any': document_ids}
                        }
                    ]
                }
            
            # Search Qdrant
            search_results = self.qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
            )
            
            # Format results
            chunks = []
            for result in search_results:
                chunks.append({
                    'text': result.payload.get('text', ''),
                    'document_id': result.payload.get('document_id'),
                    'chunk_index': result.payload.get('chunk_index'),
                    'char_start': result.payload.get('char_start'),
                    'char_end': result.payload.get('char_end'),
                    'score': result.score,
                })
            
            logger.info(f"Retrieved {len(chunks)} chunks for question")
            return chunks
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def generate_answer(self, question: str, chunks: List[Dict]) -> Tuple[str, List[Dict]]:
        """Generate answer using retrieved chunks."""
        try:
            # Build context from chunks
            context_parts = []
            for i, chunk in enumerate(chunks):
                context_parts.append(f"[Document {chunk['document_id']}, Chunk {i+1}]\n{chunk['text']}")
            
            context = "\n\n".join(context_parts)
            
            # System prompt
            system_prompt = """You are answering questions about legal contracts. Use ONLY the provided context.

Context:
{context}

Instructions:
1. Answer based solely on the context provided
2. If the answer is not in the context, say "I cannot answer this based on the provided documents"
3. Include specific references to document sections when possible
4. Be concise and accurate

Answer:"""
            
            # Generate answer
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context)},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
            )
            
            answer = response.choices[0].message.content
            
            # Extract citations
            citations = self._extract_citations(chunks)
            
            logger.info("Generated answer successfully")
            return answer, citations
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return "An error occurred while generating the answer.", []
    
    def generate_answer_stream(self, question: str, chunks: List[Dict]):
        """Generate answer with streaming (generator function)."""
        try:
            # Build context
            context_parts = []
            for i, chunk in enumerate(chunks):
                context_parts.append(f"[Document {chunk['document_id']}, Chunk {i+1}]\n{chunk['text']}")
            
            context = "\n\n".join(context_parts)
            
            system_prompt = """You are answering questions about legal contracts. Use ONLY the provided context.

Context:
{context}

Instructions:
1. Answer based solely on the context provided
2. If the answer is not in the context, say "I cannot answer this based on the provided documents"
3. Be concise and accurate

Answer:"""
            
            # Stream response
            stream = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context)},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            # Yield citations at the end
            citations = self._extract_citations(chunks)
            yield f"\n\n__CITATIONS__:{citations}"
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield "An error occurred while generating the answer."
    
    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        """Extract citation information from chunks."""
        citations = []
        for chunk in chunks:
            citations.append({
                'document_id': chunk['document_id'],
                'char_start': chunk['char_start'],
                'char_end': chunk['char_end'],
                'page_number': self._estimate_page(chunk['char_start']),  # Rough estimate
            })
        return citations
    
    def _estimate_page(self, char_position: int) -> int:
        """Estimate page number from character position (rough estimate)."""
        # Assume ~3000 characters per page
        return (char_position // 3000) + 1
