"""Local embedding service using sentence-transformers.

This module provides FREE document processing capabilities using:
- sentence-transformers/all-MiniLM-L6-v2 for embeddings (384 dimensions)
- Docling for document conversion and chunking
- pgvector for vector similarity search

Benefits:
- Completely FREE - no API keys required
- Works offline - no internet dependency
- Privacy - data never leaves your machine
- Unlimited usage - no quota limits
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from loguru import logger
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from api.db.db_client import DBClient
from api.db.models import KnowledgeBaseChunkModel

from .base import BaseEmbeddingService

# Global cache for heavy models
_MODEL_CACHE = {}

# Model configuration
DEFAULT_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# For chunking
TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class LocalEmbeddingService(BaseEmbeddingService):
    """FREE local embedding service using sentence-transformers."""

    def __init__(
        self,
        db_client: DBClient,
        model_id: str = DEFAULT_MODEL_ID,
        max_tokens: int = 128,
        device: Optional[str] = None,
    ):
        """Initialize the local embedding service.

        Args:
            db_client: Database client for storing documents and chunks
            model_id: Sentence transformer model ID 
                     (default: all-MiniLM-L6-v2 - best speed/quality balance)
            max_tokens: Maximum number of tokens per chunk (default: 128)
            device: Device to run model on ('cuda', 'cpu', etc.)
                   If None, will auto-detect (prefer GPU if available)
        """
        self.db = db_client
        self.model_id = model_id
        self.max_tokens = max_tokens
        
        # Auto-detect device: prefer GPU if available
        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Local embedding service initializing with model: {model_id}")
        logger.info(f"Using device: {self.device}")
        
    async def _get_model(self):
        """Get or load the sentence transformer model from global cache."""
        global _MODEL_CACHE
        if self.model_id not in _MODEL_CACHE:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_id} (one-time setup)...")
                # Load model in a separate thread to avoid blocking the event loop
                model = await asyncio.to_thread(
                    SentenceTransformer, 
                    self.model_id, 
                    device=self.device,
                    trust_remote_code=True
                )
                model.eval()
                _MODEL_CACHE[self.model_id] = model
                logger.info(f"✅ Model {self.model_id} loaded successfully on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer model: {e}")
                raise
        return _MODEL_CACHE[self.model_id]

    async def _get_tokenizer(self):
        """Get or load the tokenizer."""
        # Using a simple local cache for tokenizer if needed, but here we just re-init 
        # or use the one from the model. HuggingFaceTokenizers are lightweight.
        try:
            raw_tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, TOKENIZER_MODEL)
            return HuggingFaceTokenizer(
                tokenizer=raw_tokenizer,
                max_tokens=self.max_tokens,
            )
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using local model.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not texts:
            return []
        
        logger.info(f"Generating {len(texts)} embeddings locally...")
        
        try:
            model = await self._get_model()
            
            # Generate embeddings using sentence-transformers
            # Move blocking encode call to a thread
            def _encode():
                with torch.no_grad():
                    return model.encode(
                        texts,
                        batch_size=32,
                        show_progress_bar=len(texts) > 10,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                    )

            embeddings = await asyncio.to_thread(_encode)
            
            # Convert numpy arrays to lists and PAD to 1536 dimensions
            # The database column is fixed at 1536 dimensions for OpenAI compatibility
            embedding_list = []
            for emb in embeddings:
                emb_list = emb.tolist()
                if len(emb_list) < 1536:
                    # Pad with zeros to reach 1536 dimensions
                    emb_list.extend([0.0] * (1536 - len(emb_list)))
                embedding_list.append(emb_list)
            
            logger.info(f"✅ Successfully generated {len(embedding_list)} embeddings (padded to 1536 dimensions)")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}", exc_info=True)
            raise

    def get_model_id(self) -> str:
        """Get the current model ID."""
        return self.model_id

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return EMBEDDING_DIMENSION

    async def process_document_and_store(
        self,
        document_id: int,
        file_path: str,
        organization_id: int,
        max_tokens: int = 128,
    ) -> int:
        """Process a document and store embeddings in database."""
        logger.info(f"Processing document {document_id} with local embeddings")
        
        # Step 1: Convert document with docling
        # Run in thread as it's CPU-bound
        converter = DocumentConverter()
        conversion_result = await asyncio.to_thread(converter.convert, file_path)
        doc = conversion_result.document
        
        # Step 2: Initialize chunker
        tokenizer = await self._get_tokenizer()
        chunker = HybridChunker(tokenizer=tokenizer)
        
        # Step 3: Chunk the document
        def _chunk():
            return list(chunker.chunk(dl_doc=doc))
        dl_chunks = await asyncio.to_thread(_chunk)
        chunk_texts = [chunk.text for chunk in dl_chunks]
        
        logger.info(f"Generated {len(chunk_texts)} chunks")
        
        # Step 4: Generate embeddings
        embeddings = await self.embed_texts(chunk_texts)
        
        # Step 5: Create chunk records and store in database
        chunk_records = []
        for i, (text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            token_count = len(tokenizer.tokenizer.encode(text, add_special_tokens=False))
            chunk_record = KnowledgeBaseChunkModel(
                document_id=document_id,
                organization_id=organization_id,
                chunk_text=text,
                contextualized_text=text,
                chunk_index=i,
                chunk_metadata={"parser": "docling"},
                embedding_model=self.model_id,
                embedding_dimension=EMBEDDING_DIMENSION,
                token_count=token_count,
                embedding=embedding,
            )
            chunk_records.append(chunk_record)
        
        # Store in database
        await self.db.create_chunks_batch(chunk_records)
        
        logger.info(f"✅ Stored {len(chunk_records)} chunks with embeddings")
        
        return len(chunk_records)
