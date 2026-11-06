#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from model_manager import ModelManager
from embedding_engine import EmbeddingEngine
from context_builder import ContextBuilder
import logging

logging.basicConfig(level=logging.INFO)

def test_model_manager():
    print("Testing ModelManager...")
    manager = ModelManager()
    available = manager.get_available_models()
    print(f"Available models: {available}")
    if available:
        response = manager.generate_response(available[0], "Hello, test prompt")
        if response:
            print("Model generation successful.")
        else:
            print("Model generation failed.")
    else:
        print("No models available.")

def test_embedding_engine():
    print("Testing EmbeddingEngine...")
    engine = EmbeddingEngine()
    embedding = engine.generate_embedding("Test text for embedding.")
    if embedding is not None:
        print(f"Embedding generated: {embedding.shape}")
        engine.add_segment("test_seg_1", "Test segment text.")
        similarities = engine.compute_similarity(embedding, top_k=1)
        print(f"Similarities: {similarities}")
    else:
        print("Embedding generation failed.")

def test_context_builder():
    print("Testing ContextBuilder...")
    builder = ContextBuilder()
    # Add some history
    builder.add_to_history("What is your experience?", "I have 5 years in software engineering.")
    builder.add_to_history("Tell me about a project.", "I worked on a web app using React.")
    context = builder.build_context("What projects have you done?")
    print(f"Built context: {context}")

if __name__ == "__main__":
    test_model_manager()
    test_embedding_engine()
    test_context_builder()
    print("Basic tests completed.")