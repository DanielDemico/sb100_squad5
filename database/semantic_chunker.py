import argparse
import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm

from core.config import settings
from core.embeddings import embed_text

logger = logging.getLogger(__name__)

MetadataValue = str | int | float | bool | None

# ─────────────────────────────────────────────
# Global settings
# ─────────────────────────────────────────────

OLLAMA_MODEL = settings.embed_model  # embeddings model via Ollama
EMBED_DIM = 768  # nomic-embed-text dimension
QDRANT_URL = settings.qdrant_url
QDRANT_API_KEY = settings.qdrant_api_key  # for authenticated Qdrant servers
COLLECTION_NAME = settings.collection_name

# Semantic chunking thresholds
SIMILARITY_THRESHOLD = 0.75  # below this → new chunk
MIN_CHUNK_SENTENCES = 3  # minimum sentences per chunk
MAX_CHUNK_SENTENCES = 20  # maximum sentences per chunk


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────


@dataclass
class Sentence:
    """Sentence extracted from a source PDF with its embedding vector.

    The chunking pipeline uses this structure as the smallest semantic unit
    before grouping adjacent sentences into larger Qdrant chunks.
    """

    text: str
    embedding: np.ndarray = field(repr=False)


@dataclass
class Chunk:
    """Indexable text chunk produced from one or more adjacent sentences.

    Holds the merged text, original sentence texts, representative embedding
    and source metadata that will be stored as the Qdrant payload.
    """

    text: str
    sentences: list[str]
    embedding: np.ndarray = field(repr=False)
    metadata: dict[str, MetadataValue] = field(default_factory=dict)


# ─────────────────────────────────────────────
# PDF text extraction
# ─────────────────────────────────────────────


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from every page in a PDF file.

    Args:
        pdf_path: Path to the PDF file to read.

    Returns:
        Concatenated page text separated by newlines.

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
        RuntimeError: If PyMuPDF cannot open or read the document.
    """
    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        text = page.get_text("text")
        pages_text.append(text)
    doc.close()
    return "\n".join(pages_text)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like units using a simple regex.

    The regex avoids an NLP dependency and is tuned for Portuguese/English
    uppercase sentence starts commonly found in the source PDFs.

    Args:
        text: Raw text extracted from one or more PDF pages.

    Returns:
        Normalized sentences longer than 30 characters, with likely PDF noise
        removed.
    """
    # Normalize spaces and line breaks
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Split on end-of-sentence punctuation
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÀÂÊÔÃÕ])", text)

    # Drop very short sentences (PDF noise)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    return sentences


# ─────────────────────────────────────────────
# Embeddings via Ollama (Llama)
# ─────────────────────────────────────────────


def get_embedding(text: str) -> np.ndarray:
    """Generate an embedding vector for text using the configured Ollama model.

    Args:
        text: Text to embed.

    Returns:
        NumPy float32 vector produced by Ollama.

    Raises:
        Exception: Propagates the final Ollama embedding failure from
            ``core.embeddings.embed_text`` after retries.
    """
    vec = embed_text(OLLAMA_MODEL, text)
    return np.array(vec, dtype=np.float32)


def get_embeddings_batch(texts: list[str], batch_size: int = 16) -> list[np.ndarray]:
    """Generate embeddings for many texts in fixed-size batches.

    Args:
        texts: Text fragments to embed in order.
        batch_size: Number of texts grouped per progress-bar step.

    Returns:
        Embedding vectors in the same order as ``texts``.

    Raises:
        Exception: Propagates embedding failures from ``get_embedding``.
    """
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="  Generating embeddings", leave=False):
        batch = texts[i : i + batch_size]
        for text in batch:
            emb = get_embedding(text)
            embeddings.append(emb)
    return embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two embedding vectors.

    Args:
        a: First embedding vector.
        b: Second embedding vector.

    Returns:
        Similarity in the ``[-1.0, 1.0]`` range, or ``0.0`` if either vector
        has zero norm.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ─────────────────────────────────────────────
# Semantic chunking
# ─────────────────────────────────────────────


def semantic_chunking(sentences: list[Sentence]) -> list[list[Sentence]]:
    """Group adjacent sentences into semantically coherent chunks.

    Algorithm:
      1. Start a chunk with the first sentence.
      2. For each next sentence, compare against the current chunk's mean embedding.
      3. If similarity < threshold (or the chunk got too large), start a new chunk.
      4. Respect minimum and maximum sizes.

    Args:
        sentences: Ordered PDF sentences with precomputed embeddings.

    Returns:
        Ordered groups of sentences ready to become indexable chunks.
    """
    if not sentences:
        return []

    chunks: list[list[Sentence]] = []
    current_chunk: list[Sentence] = [sentences[0]]

    for i in range(1, len(sentences)):
        sentence = sentences[i]

        # Compare the next sentence against the chunk centroid, not only the
        # previous sentence, so the split decision reflects the whole local topic.
        chunk_embeddings = np.stack([s.embedding for s in current_chunk])
        chunk_mean = chunk_embeddings.mean(axis=0)

        similarity = cosine_similarity(chunk_mean, sentence.embedding)
        too_large = len(current_chunk) >= MAX_CHUNK_SENTENCES
        too_small = len(current_chunk) < MIN_CHUNK_SENTENCES

        if (similarity < SIMILARITY_THRESHOLD and not too_small) or too_large:
            # A low similarity marks a topic shift, but only after the minimum
            # chunk size avoids tiny fragments; the max size caps overly broad chunks.
            chunks.append(current_chunk)
            current_chunk = [sentence]
        else:
            current_chunk.append(sentence)

    # The final open group is not closed by a following topic shift, so it must
    # be appended explicitly to avoid dropping the tail of the document.
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def build_chunks(
    sentence_groups: list[list[Sentence]],
    metadata: dict[str, MetadataValue],
) -> list[Chunk]:
    """Convert grouped sentences into Qdrant-ready ``Chunk`` objects.

    Args:
        sentence_groups: Semantic sentence groups from ``semantic_chunking``.
        metadata: Source metadata to copy into every chunk payload.

    Returns:
        Chunks with merged text, sentence text list, mean embedding and metadata.
    """
    chunks = []
    for group in sentence_groups:
        text = " ".join(s.text for s in group)

        # Averaging sentence embeddings gives Qdrant one representative vector
        # for the whole chunk while preserving sentence text in metadata.
        embeddings = np.stack([s.embedding for s in group])
        chunk_embedding = embeddings.mean(axis=0)

        chunk = Chunk(
            text=text,
            sentences=[s.text for s in group],
            embedding=chunk_embedding,
            metadata={**metadata, "num_sentences": len(group)},
        )
        chunks.append(chunk)
    return chunks


# ─────────────────────────────────────────────
# Qdrant
# ─────────────────────────────────────────────


def init_qdrant(client: QdrantClient, embed_dim: int) -> None:
    """Create the configured Qdrant collection when missing.

    Args:
        client: Qdrant client connected to the target instance.
        embed_dim: Embedding dimensionality used by the collection vector.

    Returns:
        None.

    Raises:
        Exception: Propagates Qdrant client failures while listing or creating
            collections.
    """
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=embed_dim, distance=Distance.COSINE),
        )
        logger.info(
            "semantic_chunker.collection_created",
            extra={"collection": COLLECTION_NAME, "dim": embed_dim},
        )
    else:
        logger.info("semantic_chunker.collection_exists", extra={"collection": COLLECTION_NAME})


def upsert_chunks(client: QdrantClient, chunks: list[Chunk]) -> int:
    """Insert generated chunks into the configured Qdrant collection.

    Args:
        client: Qdrant client connected to the target instance.
        chunks: Prepared chunks with text, vectors and source metadata.

    Returns:
        Number of points submitted to Qdrant.

    Raises:
        Exception: Propagates Qdrant upsert failures.
    """
    points = []
    for chunk in chunks:
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk.embedding.tolist(),
            payload={
                "text": chunk.text,
                "num_sentences": chunk.metadata.get("num_sentences", 0),
                "source_file": chunk.metadata.get("source_file", ""),
                "source_path": chunk.metadata.get("source_path", ""),
            },
        )
        points.append(point)

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────


def process_pdf(pdf_path: str, client: QdrantClient) -> int:
    """Process one PDF and index its semantic chunks in Qdrant.

    Args:
        pdf_path: Path to the source PDF.
        client: Qdrant client used for collection setup and point upsert.

    Returns:
        Number of chunks indexed; ``0`` when the PDF has no extractable text or
        no valid sentences.

    QUALITY: long-function-justification - extraction, batch embedding, semantic chunking,
    collection setup, and upsert are the atomic ingestion unit for one source document.
    """
    filename = Path(pdf_path).name
    logger.info("semantic_chunker.pdf_start", extra={"file": filename})

    # 1. Text extraction
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        logger.warning("semantic_chunker.empty_pdf", extra={"file": filename})
        return 0

    # 2. Sentence splitting
    raw_sentences = split_into_sentences(raw_text)
    logger.info(
        "semantic_chunker.sentences_extracted",
        extra={"file": filename, "count": len(raw_sentences)},
    )

    if len(raw_sentences) == 0:
        return 0

    # 3. Sentence embeddings
    logger.info("semantic_chunker.embeddings_start", extra={"model": OLLAMA_MODEL})
    texts = list(raw_sentences)
    embeddings = get_embeddings_batch(texts)

    sentences = [
        Sentence(text=t, embedding=e) for t, e in zip(raw_sentences, embeddings, strict=True)
    ]

    # 4. Semantic chunking
    sentence_groups = semantic_chunking(sentences)
    logger.info(
        "semantic_chunker.chunks_built", extra={"file": filename, "count": len(sentence_groups)}
    )

    # 5. Build chunks with metadata
    metadata: dict[str, MetadataValue] = {
        "source_file": filename,
        "source_path": str(Path(pdf_path).resolve()),
    }
    chunks = build_chunks(sentence_groups, metadata)

    # 6. Indexing in Qdrant
    count = upsert_chunks(client, chunks)
    logger.info("semantic_chunker.chunks_indexed", extra={"file": filename, "count": count})
    return count


def process_folder(folder_path: str) -> None:
    """Process and index all PDFs found recursively in a folder.

    Args:
        folder_path: Directory containing source PDFs.

    Returns:
        None.

    QUALITY: long-function-justification - folder discovery, empty-folder handling,
    Qdrant setup, per-PDF ingestion loop, and final indexing summary form one
    operator-facing ingestion transaction.
    """
    pdf_files = list(Path(folder_path).glob("**/*.pdf"))
    if not pdf_files:
        logger.warning("semantic_chunker.no_pdfs_found", extra={"folder": folder_path})
        return

    logger.info(
        "semantic_chunker.folder_start",
        extra={"folder": folder_path, "pdf_count": len(pdf_files)},
    )

    # Initialize Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    init_qdrant(client, EMBED_DIM)

    total_chunks = 0
    for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
        total_chunks += process_pdf(str(pdf_path), client)

    logger.info(
        "semantic_chunker.pipeline_complete",
        extra={
            "pdfs_processed": len(pdf_files),
            "chunks_indexed": total_chunks,
            "collection": COLLECTION_NAME,
            "qdrant_url": QDRANT_URL,
        },
    )


# ─────────────────────────────────────────────
# Search (usage example)
# ─────────────────────────────────────────────


def search(query: str, top_k: int = 5) -> None:
    """Run a semantic search against Qdrant and log ranked results.

    Args:
        query: Natural-language query to embed and search.
        top_k: Maximum number of nearest chunks to log.

    Returns:
        None.

    Raises:
        Exception: Propagates embedding or Qdrant query failures.
    """
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    query_embedding = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k,
        with_payload=True,
    ).points

    logger.info("semantic_chunker.search", extra={"query": query, "top_k": top_k})
    for i, r in enumerate(results, 1):
        logger.info(
            "semantic_chunker.search_result",
            extra={
                "rank": i,
                "score": round(r.score, 4),
                "source_file": r.payload.get("source_file") if r.payload else None,
                "snippet": (r.payload.get("text", "")[:300] if r.payload else ""),
            },
        )


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────


def main() -> None:
    """Parse CLI arguments and dispatch indexing or search commands.

    Returns:
        None.

    QUALITY: long-function-justification - argparse setup and command dispatch remain
    together because splitting the parser obscures CLI flags and subcommands.
    """
    global OLLAMA_MODEL, SIMILARITY_THRESHOLD, QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Semantic Chunking Pipeline with Llama + Qdrant")
    subparsers = parser.add_subparsers(dest="command")

    # Command: index
    index_parser = subparsers.add_parser("index", help="Index PDFs from a folder")
    index_parser.add_argument("folder", help="Path to the folder containing the PDFs")
    index_parser.add_argument("--model", default=OLLAMA_MODEL, help="Ollama model for embeddings")
    index_parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Similarity threshold for a new chunk (default: 0.75)",
    )
    index_parser.add_argument("--qdrant-url", default=QDRANT_URL, help="Qdrant URL")
    index_parser.add_argument("--api-key", default=QDRANT_API_KEY, help="Qdrant API key (optional)")
    index_parser.add_argument("--collection", default=COLLECTION_NAME, help="Collection name")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Semantic search over the collection")
    search_parser.add_argument("query", help="Search text")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    search_parser.add_argument("--qdrant-url", default=QDRANT_URL)
    search_parser.add_argument(
        "--api-key", default=QDRANT_API_KEY, help="Qdrant API key (optional)"
    )
    search_parser.add_argument("--collection", default=COLLECTION_NAME)

    args = parser.parse_args()

    if args.command == "index":
        OLLAMA_MODEL = args.model
        SIMILARITY_THRESHOLD = args.threshold
        QDRANT_URL = args.qdrant_url
        QDRANT_API_KEY = args.api_key
        COLLECTION_NAME = args.collection
        process_folder(args.folder)

    elif args.command == "search":
        QDRANT_URL = args.qdrant_url
        QDRANT_API_KEY = args.api_key
        COLLECTION_NAME = args.collection
        search(args.query, top_k=args.top_k)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
