import os
from typing import List, Dict


class SupabaseVectorDB:
    """Minimal adapter for a Supabase-backed vector DB.

    This is a lightweight stub to provide a consistent import and a graceful
    fallback when the `supabase` client or configuration is not available.

    It implements `similarity_search(query, top_k)` and returns a list of
    dict-like results with a `text_content` key to match callers in this repo.
    """

    def __init__(self, table: str = "documents"):
        self.url = os.getenv("SUPABASE_URL") or os.getenv("DATABASE_URL")
        self.key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.table = table
        self.client = None

        try:
            from supabase import create_client

            if self.url and self.key:
                self.client = create_client(self.url, self.key)
        except Exception:
            # supabase package not installed or failed to import; keep client None
            self.client = None

    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Perform a similarity search and return results in the form:

        [{"text_content": "..."}, ...]

        If the Supabase client isn't configured, return an empty list so callers
        can handle the "I don't know" path gracefully.
        """
        if not self.client:
            return []

        try:
            # This is intentionally generic: different schemas or Supabase setups
            # will require custom queries. Implementers can replace this with a
            # project-specific vector search (RPC or vector extension queries).
            # For now, attempt a simple select as a placeholder.
            resp = (
                self.client
                .table(self.table)
                .select("*")
                .limit(top_k)
                .execute()
            )

            data = resp.data if hasattr(resp, "data") else resp
            results = []
            for row in data or []:
                text = None
                if isinstance(row, dict):
                    # Prefer common keys
                    text = row.get("text") or row.get("content") or row.get("body") or row.get("text_content")
                if text is None:
                    # Fallback to stringifying the row
                    text = str(row)
                results.append({"text_content": text})

            return results

        except Exception:
            return []
