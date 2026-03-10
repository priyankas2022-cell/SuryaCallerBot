"""ARQ background task for processing knowledge base documents."""

import os
import tempfile

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from loguru import logger
from transformers import AutoTokenizer

from api.db import db_client
from api.db.models import KnowledgeBaseChunkModel
from api.services.gen_ai import OpenAIEmbeddingService
from api.services.gen_ai.embedding.local_embedding_service import LocalEmbeddingService
from api.services.storage import storage_fs

# For tokenization/chunking
TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# File extensions natively supported by docling for rich structural parsing
DOCLING_SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".md", ".asciidoc", ".adoc",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp",
}


def _read_as_plain_text(file_path: str) -> str:
    """Read any file as plain text, trying common encodings."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, ValueError):
            continue
    # Last resort: read as binary and decode with replacement
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8", errors="replace")


def _chunk_plain_text(text: str, max_tokens: int, tokenizer) -> list[str]:
    """Split plain text into chunks by token count."""
    words = text.split()
    chunks = []
    current_words = []
    current_tokens = 0

    for word in words:
        word_tokens = len(tokenizer.encode(word, add_special_tokens=False))
        if current_tokens + word_tokens > max_tokens and current_words:
            chunks.append(" ".join(current_words))
            current_words = [word]
            current_tokens = word_tokens
        else:
            current_words.append(word)
            current_tokens += word_tokens

    if current_words:
        chunks.append(" ".join(current_words))

    return [c for c in chunks if c.strip()]


async def process_knowledge_base_document(
    ctx,
    document_id: int,
    s3_key: str,
    organization_id: int,
    max_tokens: int = 128,
):
    """Process a knowledge base document: download, chunk, embed, and store.

    Args:
        ctx: ARQ context
        document_id: Database ID of the document
        s3_key: S3 key where the file is stored
        organization_id: Organization ID
        max_tokens: Maximum number of tokens per chunk (default: 128)
    """
    logger.info(
        f"Starting knowledge base document processing for document_id={document_id}, "
        f"s3_key={s3_key}, organization_id={organization_id}"
    )

    temp_file_path = None

    try:
        # Update status to processing
        await db_client.update_document_status(document_id, "processing")

        # Extract file extension from S3 key
        filename = s3_key.split("/")[-1]
        file_extension = (
            os.path.splitext(filename)[1] or ".bin"
        )  # Default to .bin if no extension

        # Create temp file for download with correct extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file_path = temp_file.name
        temp_file.close()

        # Download file from S3
        logger.info(f"Downloading file from S3: {s3_key}")
        download_success = await storage_fs.adownload_file(s3_key, temp_file_path)

        if not download_success:
            raise Exception(f"Failed to download file from S3: {s3_key}")

        if not os.path.exists(temp_file_path):
            raise FileNotFoundError(f"Downloaded file not found: {temp_file_path}")

        file_size = os.path.getsize(temp_file_path)
        logger.info(f"Downloaded file size: {file_size} bytes")

        # Compute file hash and get mime type
        file_hash = db_client.compute_file_hash(temp_file_path)
        mime_type = db_client.get_mime_type(temp_file_path)
        filename = s3_key.split("/")[-1]

        # Get document record
        document = await db_client.get_document_by_id(document_id)
        if not document:
            raise Exception(f"Document {document_id} not found")

        # Check if a document with this hash already exists (reject duplicates)
        existing_doc = await db_client.get_document_by_hash(file_hash, organization_id)
        if existing_doc and existing_doc.id != document_id:
            error_message = (
                f"This file is a duplicate of '{existing_doc.filename}'. "
                f"Please delete the duplicate files and consolidate them into a single unique file before uploading."
            )
            logger.warning(
                f"Duplicate document detected: {document_id} is duplicate of {existing_doc.id} "
                f"({existing_doc.filename})"
            )
            # Update file metadata
            await db_client.update_document_metadata(
                document_id,
                file_size_bytes=file_size,
                file_hash=file_hash,
                mime_type=mime_type,
            )
            # Mark as failed with duplicate error message
            await db_client.update_document_status(
                document_id,
                "failed",
                error_message=error_message,
                docling_metadata={
                    "duplicate_of": existing_doc.document_uuid,
                    "duplicate_filename": existing_doc.filename,
                },
            )
            return

        # Update document with file metadata
        await db_client.update_document_metadata(
            document_id,
            file_size_bytes=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
        )

        # Initialize the embedding service
        logger.info(
            f"Initializing embedding service with max_tokens={max_tokens}"
        )
        
        # Try to get user's embeddings configurations
        embeddings_api_key = None
        embeddings_model = None
        embeddings_base_url = None
        use_local_embeddings = False
        
        if document.created_by:
            user_config = await db_client.get_user_configurations(document.created_by)
            if user_config.embeddings:
                embeddings_api_key = user_config.embeddings.api_key
                embeddings_model = user_config.embeddings.model
                embeddings_base_url = getattr(user_config.embeddings, "base_url", None)
                
                # Check if user wants to use local embeddings
                if embeddings_model and embeddings_model.lower() in ["local", "sentence-transformers", "all-minilm-l6-v2"]:
                    use_local_embeddings = True
                    logger.info("Using LOCAL embeddings (sentence-transformers) - FREE!")
                # Check if embeddings provider is NOT OpenRouter (OpenRouter doesn't support embeddings)
                elif hasattr(user_config.embeddings, 'provider') and user_config.embeddings.provider and user_config.embeddings.provider.lower() == 'openrouter':
                    logger.warning(f"OpenRouter does not support embeddings! Falling back to LOCAL embeddings (FREE)")
                    use_local_embeddings = True
                else:
                    logger.info(f"Using configured embeddings model: {embeddings_model}")

        # Decide which embedding service to use
        if use_local_embeddings or not embeddings_api_key:
            # Use FREE local embeddings
            logger.info("Using LocalEmbeddingService (FREE, no API key required)")
            service = LocalEmbeddingService(
                db_client=db_client,
                model_id="sentence-transformers/all-MiniLM-L6-v2",
                max_tokens=max_tokens,
            )
        else:
            # Use OpenAI-compatible embeddings
            logger.info(f"Using OpenAIEmbeddingService with model: {embeddings_model}")
            service = OpenAIEmbeddingService(
                db_client=db_client,
                max_tokens=max_tokens,
                api_key=embeddings_api_key,
                model_id=embeddings_model or "text-embedding-3-small",
                base_url=embeddings_base_url,
            )

        # Determine processing mode based on file extension
        use_docling = file_extension.lower() in DOCLING_SUPPORTED_EXTENSIONS
        logger.info(
            f"File extension '{file_extension}' -> "
            f"{'docling structural parsing' if use_docling else 'plain text extraction'}"
        )

        # Step 2: Initialize tokenizer for chunking (always needed)
        logger.info(
            f"Loading tokenizer: {TOKENIZER_MODEL} with max_tokens={max_tokens}"
        )
        raw_tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
        tokenizer = HuggingFaceTokenizer(
            tokenizer=raw_tokenizer,
            max_tokens=max_tokens,
        )

        chunk_texts = []
        chunk_records = []
        token_counts = []
        docling_metadata = {}

        if use_docling:
            # Step 1: Convert document with docling (rich structural parsing)
            logger.info("Converting document with docling")
            converter = DocumentConverter()
            conversion_result = converter.convert(temp_file_path)
            doc = conversion_result.document

            docling_metadata = {
                "num_pages": len(doc.pages) if hasattr(doc, "pages") else None,
                "document_type": type(doc).__name__,
                "parser": "docling",
            }

            # Step 3: Initialize chunker
            logger.info(f"Initializing HybridChunker with max_tokens={max_tokens}")
            chunker = HybridChunker(tokenizer=tokenizer)

            # Step 4: Chunk the document
            logger.info(f"Chunking document with max_tokens={max_tokens}")
            dl_chunks = list(chunker.chunk(dl_doc=doc))
            total_raw_chunks = len(dl_chunks)
            logger.info(f"Generated {total_raw_chunks} docling chunks")

            for i, chunk in enumerate(dl_chunks):
                chunk_text = chunk.text
                contextualized_text = chunker.contextualize(chunk=chunk)
                text_to_tokenize = contextualized_text if contextualized_text else chunk_text
                token_count = len(
                    raw_tokenizer.encode(text_to_tokenize, add_special_tokens=False)
                )
                token_counts.append(token_count)

                chunk_metadata = {}
                if hasattr(chunk, "meta") and chunk.meta:
                    chunk_metadata = {
                        "doc_items": (
                            [str(item) for item in chunk.meta.doc_items]
                            if hasattr(chunk.meta, "doc_items")
                            else []
                        ),
                        "headings": (
                            chunk.meta.headings if hasattr(chunk.meta, "headings") else []
                        ),
                    }

                chunk_record = KnowledgeBaseChunkModel(
                    document_id=document_id,
                    organization_id=organization_id,
                    chunk_text=chunk_text,
                    contextualized_text=contextualized_text,
                    chunk_index=i,
                    chunk_metadata=chunk_metadata,
                    embedding_model=service.get_model_id(),
                    embedding_dimension=service.get_embedding_dimension(),
                    token_count=token_count,
                )
                chunk_records.append(chunk_record)
                chunk_texts.append(text_to_tokenize)

        else:
            # Plain text extraction for all other file types (.php, .py, .js, .csv, .json, etc.)
            logger.info(f"Reading file as plain text (extension: {file_extension})")
            plain_text = _read_as_plain_text(temp_file_path)
            if not plain_text.strip():
                raise ValueError(f"File appears to be empty or unreadable: {filename}")

            docling_metadata = {
                "document_type": "plain_text",
                "parser": "plain_text",
                "file_extension": file_extension,
                "char_count": len(plain_text),
            }

            plain_chunks = _chunk_plain_text(plain_text, max_tokens, raw_tokenizer)
            logger.info(f"Generated {len(plain_chunks)} plain text chunks")

            for i, chunk_text in enumerate(plain_chunks):
                token_count = len(
                    raw_tokenizer.encode(chunk_text, add_special_tokens=False)
                )
                token_counts.append(token_count)

                chunk_record = KnowledgeBaseChunkModel(
                    document_id=document_id,
                    organization_id=organization_id,
                    chunk_text=chunk_text,
                    contextualized_text=chunk_text,
                    chunk_index=i,
                    chunk_metadata={"parser": "plain_text", "file_extension": file_extension},
                    embedding_model=service.get_model_id(),
                    embedding_dimension=service.get_embedding_dimension(),
                    token_count=token_count,
                )
                chunk_records.append(chunk_record)
                chunk_texts.append(chunk_text)

        total_chunks = len(chunk_records)

        # Log chunk statistics
        if token_counts:
            avg_tokens = sum(token_counts) / len(token_counts)
            min_tokens = min(token_counts)
            max_tokens_actual = max(token_counts)
            logger.info("Chunk token statistics:")
            logger.info(f"  - Average: {avg_tokens:.1f} tokens")
            logger.info(f"  - Min: {min_tokens} tokens")
            logger.info(f"  - Max: {max_tokens_actual} tokens")

        # Step 6: Generate embeddings using OpenAI
        logger.info(f"Generating embeddings using {service.get_model_id()}")
        embeddings = await service.embed_texts(chunk_texts)

        # Step 7: Attach embeddings to chunk records
        for chunk_record, embedding in zip(chunk_records, embeddings):
            chunk_record.embedding = embedding

        # Step 8: Save chunks in database
        logger.info("Storing chunks in database")
        await db_client.create_chunks_batch(chunk_records)

        # Step 9: Update document status to completed
        await db_client.update_document_status(
            document_id,
            "completed",
            total_chunks=total_chunks,
            docling_metadata=docling_metadata,
        )

        logger.info(
            f"Successfully processed knowledge base document {document_id}. "
            f"Total chunks: {total_chunks}"
        )

    except Exception as e:
        logger.error(
            f"Error processing knowledge base document {document_id}: {e}",
            exc_info=True,
        )
        # Update document status to failed
        await db_client.update_document_status(
            document_id, "failed", error_message=str(e)
        )
        raise

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
