# RAG Question Answering Prompt

This prompt is used for answering questions about legal contracts using Retrieval-Augmented Generation (RAG).

## Prompt

```
You are answering questions about legal contracts. Use ONLY the provided context.

Context:
{chunks}

Instructions:
1. Answer based solely on the context provided
2. If the answer is not in the context, say "I cannot answer this based on the provided documents"
3. Include specific references to document sections when possible
4. Be concise and accurate

Answer:
```

## Rationale

**Strict Grounding**: The emphasis on "ONLY the provided context" prevents hallucination. This is critical for legal documents where accuracy is paramount.

**Explicit Refusal Instruction**: We explicitly tell the model to refuse answering if the information isn't in the context. This prevents the LLM from making up answers based on its training data.

**Citation Encouragement**: By asking for "specific references", we encourage the model to ground its answers in specific document sections, which helps with citation generation.

**Conciseness**: Legal documents can be verbose. We ask for concise answers to improve user experience.

**Temperature (0.3)**: We use a low but not zero temperature to allow some natural language variation while maintaining factual accuracy.

## Context Construction

The context is built from the top-K retrieved chunks:

```
[Document {document_id}, Chunk 1]
{chunk_text}

[Document {document_id}, Chunk 2]
{chunk_text}
...
```

Each chunk includes the document ID prefix so the model knows which document it came from, facilitating citation.

## Citation Extraction

After answer generation, we extract citations from the retrieved chunks:
- Document ID
- Character position range (char_start, char_end)
- Estimated page number

## Model: `gpt-4-turbo-preview`

We use GPT-4 Turbo for RAG because:
- Superior reading comprehension for legal text
- Better ability to synthesize information across multiple chunks
- More reliable following of "context-only" instructions
- Lower hallucination rate compared to smaller models
