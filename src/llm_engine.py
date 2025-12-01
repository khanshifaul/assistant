import ollama
import logging

class InterviewAssistantSLM:
    def __init__(self, model_name="phi3"):
        self.model_name = model_name
        logging.info(f"Initializing SLM with model: {model_name}")
        # We assume the model is pulled. We can try to pull it if not.
        try:
            ollama.show(model_name)
            logging.info(f"Model {model_name} found.")
        except Exception:
            logging.info(f"Model {model_name} not found, pulling...")
            try:
                ollama.pull(model_name)
                logging.info(f"Model {model_name} pulled successfully.")
            except Exception as e:
                logging.error(f"Failed to pull model {model_name}: {e}")
                # We don't raise here, maybe the service isn't up yet, we'll try in generate

    def is_question(self, text):
        """
        Simple heuristic to check if text is a question.
        """
        text = text.strip()
        if not text:
            return False
        
        if text.endswith("?"):
            return True
        
        question_starters = ["what", "when", "where", "why", "how", "who", "can you", "could you", "tell me"]
        lower_text = text.lower()
        if any(lower_text.startswith(s) for s in question_starters):
            return True
            
        return False

    def generate_answer(self, question, context=""):
        """
        Generates an answer for the given question using Ollama (Streaming).
        """
        prompt = f"""You are an expert interview candidate. Answer the following interview question concisely (max 2 sentences) and professionally.

Context: {context}

Question: {question}

Answer:"""
        
        try:
            stream = ollama.generate(model=self.model_name, prompt=prompt, stream=True)
            for chunk in stream:
                yield chunk['response']
        except Exception as e:
            logging.error(f"Ollama generation failed: {e}")
            yield "Error generating answer. Is Ollama running?"
