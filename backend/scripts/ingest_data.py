import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vector_store import vector_store
from app.core.config import settings

logger = logging.getLogger(__name__)

# PDF source directories scanned relative to settings.data_path
PDF_DIRS = {
    "policy_documents": "policy",
    "claim_guides": "claim",
}


def load_pdf_data(pdf_dir: Path, doc_type: str):
    """Extract text from every PDF in a directory and chunk it.

    Returns documents with metadata {source, page, type} so retrieval can
    cite the originating file and page.
    """
    from pypdf import PdfReader

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )

    documents = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        try:
            reader = PdfReader(str(pdf_path))
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if not text:
                    continue
                for chunk in splitter.split_text(text):
                    chunk = chunk.strip()
                    if chunk:
                        documents.append({
                            "text": chunk,
                            "metadata": {
                                "source": pdf_path.name,
                                "page": page_number,
                                "type": doc_type,
                            },
                        })
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {e}")
    return documents

def load_department_csv(csv_path: Path):
    """Load one department knowledge CSV in the standard QA format.

    Expected columns: department, category, question, answer
    Optional columns: keywords, last_reviewed, owner.
    Rows missing a question or answer are skipped.
    """
    documents = []
    try:
        # utf-8-sig tolerates the BOM Excel adds when saving CSVs
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                question = (row.get("question") or "").strip()
                answer = (row.get("answer") or "").strip()
                if not question or not answer:
                    continue

                text_parts = [f"Question: {question}", f"Answer: {answer}"]
                keywords = (row.get("keywords") or "").strip()
                if keywords:
                    text_parts.append(f"Keywords: {keywords}")

                documents.append({
                    "text": "\n".join(text_parts),
                    "metadata": {
                        "type": (row.get("department") or "general").strip(),
                        "category": (row.get("category") or "insurance").strip(),
                        "source": csv_path.name,
                    },
                })
        return documents
    except Exception as e:
        logger.error(f"Error loading department CSV {csv_path}: {e}")
        return []

def load_csv_data(csv_path: Path):
    """Load and chunk CSV data"""
    documents = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create a text representation
                text_parts = []
                metadata = {
                    "type": row.get("type", "general"),
                    "category": row.get("category", "insurance"),
                    "source": str(csv_path.name)
                }
                
                for key, value in row.items():
                    if value and isinstance(value, str) and value.strip():
                        text_parts.append(f"{key}: {value.strip()}")
                
                if text_parts:
                    documents.append({
                        "text": "\n".join(text_parts),
                        "metadata": metadata
                    })
        
        return documents
    except Exception as e:
        logging.error(f"Error loading CSV {csv_path}: {e}")
        return []

def main():
    print("🔄 Starting data ingestion process...")
    
    # Clear existing collection
    try:
        vector_store.delete_collection()
        print("✅ Cleared existing collection")
    except Exception as e:
        print(f"⚠️ Could not clear collection: {e}")
    
    # Load all data sources
    all_docs = []
    
    # Load knowledge base
    kb_path = settings.data_path / "insurance_knowledge.csv"
    if kb_path.exists():
        docs = load_csv_data(kb_path)
        all_docs.extend(docs)
        print(f"📄 Loaded {len(docs)} documents from knowledge base")
    else:
        print("❌ No knowledge base found!")
        return

    # Load department knowledge CSVs (one file per department/division)
    dept_dir = settings.data_path / "departments"
    if dept_dir.is_dir():
        dept_files = [
            p for p in sorted(dept_dir.glob("*.csv"))
            if "sample" not in p.name.lower() and "template" not in p.name.lower()
        ]
        for csv_path in dept_files:
            docs = load_department_csv(csv_path)
            if docs:
                all_docs.extend(docs)
                print(f"🏢 Loaded {len(docs)} Q&A entries from {csv_path.name}")
            else:
                print(f"⏭️  No usable rows in {csv_path.name}")
        if not dept_files:
            print("⏭️  No department CSV files found in data/departments")
    else:
        print("⏭️  Skipping missing departments directory")

    # Load PDF documents (policy documents, claim guides)
    for dir_name, doc_type in PDF_DIRS.items():
        pdf_dir = settings.data_path / "docs" / dir_name
        if not pdf_dir.is_dir():
            print(f"⏭️  Skipping missing PDF directory: {dir_name}")
            continue
        docs = load_pdf_data(pdf_dir, doc_type)
        if docs:
            all_docs.extend(docs)
            print(f"📚 Loaded {len(docs)} chunks from {dir_name}")
        else:
            print(f"⏭️  No PDF documents found in {dir_name}")

    if not all_docs:
        print("❌ No documents found! Aborting ingestion.")
        return
    
    # Upsert to vector store
    try:
        count = vector_store.upsert_documents(all_docs)
        print(f"✅ Successfully ingested {count} documents into vector store")
        
        # Show collection info
        info = vector_store.get_collection_info()
        print(f"📊 Collection stats: {info}")
    except Exception as e:
        print(f"❌ Failed to ingest documents: {e}")
        raise

if __name__ == "__main__":
    main()