import ollama
import logging
from typing import Dict, Optional

class ModelManager:
    def __init__(self, model_names: list = ["phi3", "qwen3-embedding", "gemma3"]):
        self.model_names = model_names
        self.loaded_models: Dict[str, bool] = {}
        self.models: Dict[str, object] = {}  # Placeholder for model objects if needed

    def ensure_model_loaded(self, model_name: str) -> bool:
        """Lazily load a model if not already loaded."""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]

        try:
            ollama.show(model_name)
            logging.info(f"Model {model_name} is available.")
            self.loaded_models[model_name] = True
            return True
        except Exception:
            logging.info(f"Model {model_name} not found, attempting to pull...")
            try:
                ollama.pull(model_name)
                logging.info(f"Model {model_name} pulled successfully.")
                self.loaded_models[model_name] = True
                return True
            except Exception as e:
                logging.error(f"Failed to load model {model_name}: {e}")
                self.loaded_models[model_name] = False
                return False

    def get_available_models(self) -> list:
        """Return list of successfully loaded models."""
        available = []
        for model in self.model_names:
            if self.ensure_model_loaded(model):
                available.append(model)
        return available

    def generate_response(self, model_name: str, prompt: str, stream: bool = True):
        """Generate response using specified model."""
        if not self.ensure_model_loaded(model_name):
            raise ValueError(f"Model {model_name} is not available.")
        try:
            return ollama.generate(model=model_name, prompt=prompt, stream=stream)
        except Exception as e:
            logging.error(f"Error generating with {model_name}: {e}")
            return None