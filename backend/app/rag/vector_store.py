from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
try:
    # Try new import first
    from langchain_core.documents import Document
except ImportError:
    # Fall back to old import
    from langchain.schema import Document

import os
from pathlib import Path
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={'device': settings.embedding_device}
            )
        except Exception as e:
            logger.warning(f"Failed to load embeddings: {e}. Using CPU.")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={'device': 'cpu'}
            )
            
        self.vector_store = None
        self.vector_store_path = settings.vector_store_path
        
        # Create directory if it doesn't exist
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing index
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize or load the FAISS vector store"""
        index_path = self.vector_store_path / "index.faiss"
        config_path = self.vector_store_path / "index.pkl"
        
        if index_path.exists() and config_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"✅ Loaded existing vector store from {self.vector_store_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load vector store: {e}. Creating new one.")
                self._create_new_vector_store()
        else:
            self._create_new_vector_store()
    
    def _create_new_vector_store(self):
        """Create a new empty vector store"""
        try:
            self.vector_store = FAISS.from_texts(
                ["Initialize vector store"],
                self.embeddings,
                metadatas=[{"type": "system", "source": "system"}]
            )
            logger.info("✅ Created new vector store")
        except Exception as e:
            logger.error(f"❌ Failed to create vector store: {e}")
            raise
    
    def upsert_documents(self, documents):
        """Add documents to the vector store"""
        try:
            # Convert to LangChain documents
            langchain_docs = [
                Document(
                    page_content=doc["text"],
                    metadata=doc["metadata"]
                ) for doc in documents
            ]
            
            # If this is the first document (initialization), replace the store
            if len(langchain_docs) == 1 and langchain_docs[0].page_content == "Initialize vector store":
                return
            
            # Add documents to the store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(langchain_docs, self.embeddings)
            else:
                self.vector_store.add_documents(langchain_docs)
            
            # Save the updated store
            self.vector_store.save_local(str(self.vector_store_path))
            
            logger.info(f"✅ Added {len(documents)} documents to vector store")
            return len(documents)
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def search(self, query, limit=5):
        """Search for relevant documents"""
        try:
            if self.vector_store is None:
                self._init_vector_store()
                
            results = self.vector_store.similarity_search_with_score(query, k=limit)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                # Skip internal initialization documents
                if doc.metadata.get("type") == "system":
                    continue

                formatted_results.append({
                    "id": hash(doc.page_content),
                    "text": doc.page_content,
                    "score": 1.0 - score,  # Convert distance to similarity
                    "metadata": doc.metadata
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def delete_collection(self):
        """Delete the collection (for reindexing)"""
        try:
            # Delete FAISS files
            for file in self.vector_store_path.glob("*"):
                file.unlink()
                
            # Recreate the vector store
            self._create_new_vector_store()
            
            logger.info(f"✅ Deleted and recreated vector store at {self.vector_store_path}")
        except Exception as e:
            logger.error(f"❌ Collection deletion error: {e}")
    
    def get_collection_info(self):
        """Get collection information"""
        try:
            # Count documents by trying a search
            test_results = self.search("test", limit=1000)
            return {
                "vectors_count": len(test_results),
                "status": "ready",
                "vector_size": getattr(self.embeddings, 'dimension', 384)
            }
        except Exception as e:
            logger.error(f"❌ Collection info error: {e}")
            return {"error": str(e)}

vector_store = VectorStore()