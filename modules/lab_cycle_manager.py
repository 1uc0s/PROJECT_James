# modules/lab_cycle_manager.py - Updated for simplified folder structure
import os
import json
import datetime
import numpy as np

# Vector database for RAG
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available - falling back to simple similarity search")

# For generating embeddings
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Transformers not available - using basic TF-IDF for embeddings")
    from sklearn.feature_extraction.text import TfidfVectorizer

from config import LAB_CYCLES_DIR, get_cycle_paths

class LabCycleManager:
    def __init__(self):
        """Initialize the lab cycle manager for organizing lab sessions"""
        # Ensure lab cycles directory exists
        os.makedirs(LAB_CYCLES_DIR, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = None
        self.tokenizer = None
        self.vector_size = 384  # Default for sentence transformers
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a small but effective sentence transformer model
                self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                self.embedding_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                print("Using sentence-transformers for embeddings")
            except Exception as e:
                print(f"Error loading transformer model: {e}")
                print("Falling back to TF-IDF")
                self.embedding_model = None
        
        if not self.embedding_model and not TRANSFORMERS_AVAILABLE:
            self.tfidf = TfidfVectorizer(max_features=self.vector_size)
            print("Using TF-IDF for embeddings")
    
    def create_lab_cycle(self, cycle_id, title, description=None):
        """Create a new lab cycle"""
        cycle_dir = os.path.join(LAB_CYCLES_DIR, cycle_id)
        
        if os.path.exists(cycle_dir):
            raise ValueError(f"Lab cycle '{cycle_id}' already exists")
        
        # Create directories using the helper function
        paths = get_cycle_paths(cycle_id)
        
        # Create metadata
        metadata = {
            "cycle_id": cycle_id,
            "title": title,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "sessions": [],
            "knowledge_base": {
                "indexed": False,
                "last_updated": None,
                "document_count": 0
            }
        }
        
        # Save metadata
        with open(os.path.join(paths["root"], "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Created lab cycle: {title} (ID: {cycle_id})")
        return cycle_id
    
    def list_lab_cycles(self):
        """List all available lab cycles"""
        cycles = []
        
        for item in os.listdir(LAB_CYCLES_DIR):
            cycle_dir = os.path.join(LAB_CYCLES_DIR, item)
            metadata_file = os.path.join(cycle_dir, "metadata.json")
            
            if os.path.isdir(cycle_dir) and os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    cycles.append(metadata)
                except Exception as e:
                    print(f"Error loading metadata for cycle {item}: {e}")
        
        return cycles
    
    def get_lab_cycle(self, cycle_id):
        """Get a lab cycle by ID"""
        paths = get_cycle_paths(cycle_id)
        metadata_file = os.path.join(paths["root"], "metadata.json")
        
        if not os.path.exists(metadata_file):
            raise ValueError(f"Lab cycle '{cycle_id}' not found")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return metadata
    
    def add_session_to_cycle(self, cycle_id, session_id, session_info=None):
        """Add a session to a lab cycle"""
        paths = get_cycle_paths(cycle_id)
        metadata_file = os.path.join(paths["root"], "metadata.json")
        
        if not os.path.exists(metadata_file):
            raise ValueError(f"Lab cycle '{cycle_id}' not found")
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Add session if not already in the list
        if session_id not in [s["session_id"] for s in metadata["sessions"]]:
            session_data = {
                "session_id": session_id,
                "added_at": datetime.datetime.now().isoformat(),
            }
            
            if session_info:
                session_data.update(session_info)
                
            metadata["sessions"].append(session_data)
            
            # Save updated metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Added session '{session_id}' to lab cycle '{cycle_id}'")
        
        return True
    
    # RAG functionality
    def add_document_to_knowledge_base(self, cycle_id, document, title=None, document_id=None, metadata=None):
        """Add a document to the knowledge base of a lab cycle"""
        paths = get_cycle_paths(cycle_id)
        kb_dir = paths["knowledge_base"]
        
        # Generate ID if not provided
        if not document_id:
            document_id = f"doc_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare document metadata
        doc_metadata = {
            "id": document_id,
            "title": title or f"Document {document_id}",
            "added_at": datetime.datetime.now().isoformat(),
            "user_metadata": metadata or {}
        }
        
        # Save document
        with open(os.path.join(kb_dir, f"{document_id}.txt"), 'w') as f:
            f.write(document)
        
        # Save metadata
        with open(os.path.join(kb_dir, f"{document_id}.json"), 'w') as f:
            json.dump(doc_metadata, f, indent=2)
        
        # Update cycle metadata
        cycle_metadata_file = os.path.join(paths["root"], "metadata.json")
        
        if os.path.exists(cycle_metadata_file):
            with open(cycle_metadata_file, 'r') as f:
                cycle_metadata = json.load(f)
            
            cycle_metadata["knowledge_base"]["document_count"] += 1
            cycle_metadata["knowledge_base"]["last_updated"] = datetime.datetime.now().isoformat()
            cycle_metadata["knowledge_base"]["indexed"] = False
            
            with open(cycle_metadata_file, 'w') as f:
                json.dump(cycle_metadata, f, indent=2)
        
        print(f"Added document '{doc_metadata['title']}' to knowledge base")
        return document_id
    
    def _generate_embeddings(self, texts):
        """Generate embeddings for a list of text chunks"""
        if not texts:
            return np.array([])
        
        if self.embedding_model and TRANSFORMERS_AVAILABLE:
            # Use transformer model
            embeddings = []
            
            for text in texts:
                try:
                    # Encode text in batches if needed
                    inputs = self.tokenizer(text, padding=True, truncation=True, 
                                          return_tensors="pt", max_length=512)
                    
                    # Get model output and mean-pool over tokens
                    with torch.no_grad():
                        outputs = self.embedding_model(**inputs)
                    
                    # Use mean pooling over tokens as the sentence embedding
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Error generating embedding: {e}")
                    # Provide a fallback embedding of zeros
                    embeddings.append(np.zeros(self.vector_size))
            
            return np.array(embeddings)
        else:
            # Fall back to TF-IDF
            try:
                # Fit the vectorizer if this is the first batch
                if not hasattr(self, 'tfidf_fitted') or not self.tfidf_fitted:
                    self.tfidf.fit(texts)
                    self.tfidf_fitted = True
                
                # Transform the texts
                embeddings = self.tfidf.transform(texts).toarray()
                
                # Ensure each embedding has the right dimensions
                if embeddings.shape[1] < self.vector_size:
                    padding = np.zeros((embeddings.shape[0], self.vector_size - embeddings.shape[1]))
                    embeddings = np.hstack((embeddings, padding))
                
                return embeddings
            except Exception as e:
                print(f"Error with TF-IDF embedding: {e}")
                return np.zeros((len(texts), self.vector_size))
    
    def _chunk_text(self, text, chunk_size=512, overlap=64):
        """Split text into overlapping chunks for more effective retrieval"""
        chunks = []
        words = text.split()
        
        # Minimum chunk length
        min_chunk_length = 50
        
        if len(words) <= chunk_size:
            # Text is shorter than chunk size
            if len(words) >= min_chunk_length:
                chunks.append(" ".join(words))
            return chunks
            
        for i in range(0, len(words) - overlap, chunk_size - overlap):
            chunk = words[i:i + chunk_size]
            if len(chunk) >= min_chunk_length:
                chunks.append(" ".join(chunk))
                
        return chunks
    
    def build_knowledge_base_index(self, cycle_id):
        """Build or update the vector index for the knowledge base"""
        paths = get_cycle_paths(cycle_id)
        kb_dir = paths["knowledge_base"]
        index_dir = os.path.join(kb_dir, "index")
        os.makedirs(index_dir, exist_ok=True)
        
        # Get all document files
        document_files = [f for f in os.listdir(kb_dir) if f.endswith('.txt')]
        
        if not document_files:
            print(f"No documents found in knowledge base for cycle '{cycle_id}'")
            return False
        
        # Extract text and metadata
        all_chunks = []
        chunk_metadata = []
        
        for doc_file in document_files:
            doc_id = os.path.splitext(doc_file)[0]
            meta_file = f"{doc_id}.json"
            
            if not os.path.exists(os.path.join(kb_dir, meta_file)):
                continue
                
            # Load document
            with open(os.path.join(kb_dir, doc_file), 'r') as f:
                text = f.read()
            
            # Load metadata
            with open(os.path.join(kb_dir, meta_file), 'r') as f:
                metadata = json.load(f)
            
            # Chunk the document
            chunks = self._chunk_text(text)
            
            # Add chunks and their metadata
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "doc_id": doc_id,
                    "title": metadata.get("title", f"Document {doc_id}"),
                    "chunk_id": i,
                    "metadata": metadata.get("user_metadata", {}),
                    "text": chunk
                })
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self._generate_embeddings(all_chunks)
        
        # Save chunk metadata
        with open(os.path.join(index_dir, "chunks.json"), 'w') as f:
            json.dump(chunk_metadata, f, indent=2)
        
        # Build vector index
        if FAISS_AVAILABLE and len(embeddings) > 0:
            try:
                # Create and train index
                dimension = embeddings.shape[1]
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings.astype('float32'))
                
                # Save index
                faiss.write_index(index, os.path.join(index_dir, "faiss.index"))
                
                # Save embedding dimension
                with open(os.path.join(index_dir, "dimensions.json"), 'w') as f:
                    json.dump({"dimensions": dimension}, f)
                
                print(f"FAISS index built with {len(embeddings)} vectors of dimension {dimension}")
            except Exception as e:
                print(f"Error building FAISS index: {e}")
                # Save embeddings as numpy array as fallback
                np.save(os.path.join(index_dir, "embeddings.npy"), embeddings)
                print(f"Saved embeddings as numpy array instead")
        else:
            # Save embeddings as numpy array
            np.save(os.path.join(index_dir, "embeddings.npy"), embeddings)
            print(f"Saved embeddings as numpy array (FAISS not available)")
        
        # Update cycle metadata
        cycle_metadata_file = os.path.join(paths["root"], "metadata.json")
        with open(cycle_metadata_file, 'r') as f:
            cycle_metadata = json.load(f)
        
        cycle_metadata["knowledge_base"]["indexed"] = True
        cycle_metadata["knowledge_base"]["last_updated"] = datetime.datetime.now().isoformat()
        cycle_metadata["knowledge_base"]["document_count"] = len(document_files)
        
        with open(cycle_metadata_file, 'w') as f:
            json.dump(cycle_metadata, f, indent=2)
        
        return True
    
    def retrieve_relevant_context(self, cycle_id, query, max_results=5):
        """Retrieve relevant context from the knowledge base using vector similarity"""
        paths = get_cycle_paths(cycle_id)
        kb_dir = paths["knowledge_base"]
        index_dir = os.path.join(kb_dir, "index")
        
        # Check if index exists
        if not os.path.exists(index_dir):
            print(f"Knowledge base index not found for cycle '{cycle_id}'")
            return []
        
        # Load chunk metadata
        chunks_file = os.path.join(index_dir, "chunks.json")
        if not os.path.exists(chunks_file):
            print(f"Chunk metadata not found for cycle '{cycle_id}'")
            return []
            
        with open(chunks_file, 'r') as f:
            chunk_metadata = json.load(f)
        
        if not chunk_metadata:
            return []
        
        # Generate query embedding
        query_embedding = self._generate_embeddings([query])[0]
        
        # Perform search
        if FAISS_AVAILABLE and os.path.exists(os.path.join(index_dir, "faiss.index")):
            try:
                # Load FAISS index
                index = faiss.read_index(os.path.join(index_dir, "faiss.index"))
                
                # Search
                distances, indices = index.search(
                    np.array([query_embedding]).astype('float32'), 
                    min(max_results, len(chunk_metadata))
                )
                
                # Get results
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(chunk_metadata):
                        result = chunk_metadata[idx].copy()
                        result["score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                        results.append(result)
                
                return results
            except Exception as e:
                print(f"Error searching FAISS index: {e}")
                print("Falling back to numpy-based search")
        
        # Fallback to numpy-based search
        try:
            embeddings_file = os.path.join(index_dir, "embeddings.npy")
            if not os.path.exists(embeddings_file):
                print(f"Embeddings file not found for cycle '{cycle_id}'")
                return []
                
            embeddings = np.load(embeddings_file)
            
            # Calculate distances
            distances = np.linalg.norm(embeddings - query_embedding, axis=1)
            
            # Get top results
            top_indices = np.argsort(distances)[:max_results]
            
            # Format results
            results = []
            for idx in top_indices:
                if idx < len(chunk_metadata):
                    result = chunk_metadata[idx].copy()
                    result["score"] = float(1.0 / (1.0 + distances[idx]))  # Convert distance to similarity score
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"Error performing numpy-based search: {e}")
            return []
    
    def get_knowledge_context(self, cycle_id, query, max_results=5, format_for_prompt=True):
        """Get relevant context formatted for inclusion in an LLM prompt"""
        results = self.retrieve_relevant_context(cycle_id, query, max_results)
        
        if not results:
            return ""
        
        if format_for_prompt:
            context = "RELEVANT CONTEXT FROM PREVIOUS LAB SESSIONS:\n\n"
            
            for result in results:
                context += f"--- From: {result['title']} ---\n"
                context += result["text"]
                context += "\n\n"
            
            return context
        else:
            return results