from sklearn.metrics.pairwise import cosine_similarity

from transformers import AutoModel, AutoTokenizer
import torch
from sklearn.metrics.pairwise import cosine_similarity

# Load BERT model & tokenizer (Small, efficient model)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def _get_embedding(text: str):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].numpy()  # Use [CLS] token representation


def get_cosine_similarity(doc1: str, doc2: str) -> float:
    embedding_old = _get_embedding(doc1)
    embedding_new = _get_embedding(doc2)
    return cosine_similarity(embedding_old, embedding_new)[0][0]
