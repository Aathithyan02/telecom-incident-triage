import os
import glob
import numpy as np
import faiss
from google import genai
from typing import List, Dict, Optional

class LocalRunbookStore:
    def __init__(self, runbooks_dir: str = "data/runbooks"):
        self.runbooks_dir = runbooks_dir
        self.chunks: List[Dict[str, str]] = []
        self.index = None
        self.dimension = 768
        self.client = None
        self._load_chunks()

    def _get_client(self):
        if not self.client:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is missing!")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def _load_chunks(self):
        files = glob.glob(os.path.join(self.runbooks_dir, "*.md"))
        for path in files:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            runbook_id = os.path.basename(path).split("_")[0]
            sections = content.split("## ")
            for sec in sections:
                if sec.strip():
                    self.chunks.append({
                        "runbook_id": runbook_id,
                        "text": sec.strip(),
                        "source": os.path.basename(path)
                    })

    def _extract_embedding_values(self, res) -> List[float]:
        """Extracts vector values safely across SDK versions."""
        if hasattr(res, "embeddings") and res.embeddings:
            return list(res.embeddings[0].values)
        elif hasattr(res, "embedding") and res.embedding:
            return list(res.embedding.values)
        raise ValueError("Could not extract embedding values from response")

    def _embed(self, text: str) -> List[float]:
        client = self._get_client()
        # Hackathon instruction: Use gemini-embedding-001 (or text-embedding-004)
        for model_name in ["gemini-embedding-001", "text-embedding-004"]:
            try:
                res = client.models.embed_content(
                    model=model_name,
                    contents=text
                )
                return self._extract_embedding_values(res)
            except Exception:
                continue
        raise RuntimeError("Failed to compute embedding with available models")

    def build_index(self):
        embeddings = []
        for chunk in self.chunks:
            emb = self._embed(chunk["text"])
            embeddings.append(emb)

        arr = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(arr)
        self.dimension = arr.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(arr)

    def search(self, query: str, threshold: float = 0.68) -> Optional[Dict]:
        if not self.index:
            self.build_index()

        emb = self._embed(query)
        q_vec = np.array([emb], dtype="float32")
        faiss.normalize_L2(q_vec)

        scores, indices = self.index.search(q_vec, 1)
        best_score = float(scores[0][0])
        best_idx = int(indices[0][0])

        if best_score >= threshold:
            match = self.chunks[best_idx].copy()
            match["score"] = best_score
            return match
        return None