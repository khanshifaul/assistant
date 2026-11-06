import ollama
import logging
import numpy as np
import chromadb
from typing import List, Tuple
from sklearn.cluster import KMeans

class EmbeddingEngine:
    def __init__(self, embedding_model: str = "qwen3-embedding"):
        self.embedding_model = embedding_model
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="conversation_segments")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for given text using Ollama."""
        try:
            response = ollama.embeddings(model=self.embedding_model, prompt=text)
            return np.array(response['embedding'])
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return None

    def add_segment(self, segment_id: str, text: str, metadata: dict = None):
        """Add a conversation segment to the vector database."""
        embedding = self.generate_embedding(text)
        if embedding is not None:
            self.collection.add(
                ids=[segment_id],
                embeddings=[embedding.tolist()],
                documents=[text],
                metadatas=[metadata] if metadata else None
            )
            logging.info(f"Added segment {segment_id}")
        else:
            logging.error(f"Failed to add segment {segment_id}")

    def compute_similarity(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Compute similarity and return top-k similar segments."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            similarities = []
            for id_, distance in zip(results['ids'][0], results['distances'][0]):
                similarity = 1 / (1 + distance)  # Convert distance to similarity
                similarities.append((id_, similarity))
            return similarities
        except Exception as e:
            logging.error(f"Error computing similarity: {e}")
            return []

    def cluster_segments(self, n_clusters: int = 3) -> dict:
        """Cluster segments using KMeans."""
        try:
            embeddings = self.collection.get(include=['embeddings'])['embeddings']
            if not embeddings:
                return {}
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)  # Index of segment
            return clusters
        except Exception as e:
            logging.error(f"Error clustering segments: {e}")
            return {}