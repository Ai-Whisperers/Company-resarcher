from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
from ..core.logger import setup_logger

logger = setup_logger("vault")


class VaultManager:
    """
    Manages persistent memory for the system.
    Handles both Vector Storage (Pinecone/Chroma) and Graph Storage (Neo4j).
    Falls back to local JSON storage if keys are missing.
    """

    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.neo4j_uri = os.getenv("NEO4J_URI")

        self.use_pinecone = bool(self.pinecone_api_key)
        self.use_neo4j = bool(self.neo4j_uri)

        self.local_storage_path = "data/vault"
        os.makedirs(self.local_storage_path, exist_ok=True)

        if not self.use_pinecone:
            logger.warning(
                "Pinecone API Key not found. Using local JSON fallback for Vector Vault."
            )

        if not self.use_neo4j:
            logger.warning(
                "Neo4j URI not found. Using local JSON fallback for Graph Vault."
            )

    async def store_report(
        self, company_name: str, report_content: str, metadata: Dict[str, Any]
    ):
        """
        Stores a completed report into the Vault.
        """
        # 1. Store in Vector DB (Chunking would happen here)
        await self._store_vector(company_name, report_content, metadata)

        # 2. Store in Graph DB (Entity extraction would happen here)
        await self._store_graph(company_name, metadata)

    async def search_similar_companies(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for similar companies or past reports.
        """
        if self.use_pinecone:
            return await self._search_pinecone(query)
        else:
            return await self._search_local(query)

    async def _store_vector(
        self, company_name: str, content: str, metadata: Dict[str, Any]
    ):
        if self.use_pinecone:
            # Placeholder for Pinecone implementation
            pass
        else:
            # Local Fallback: Save as JSON
            filename = f"{self.local_storage_path}/vectors.json"
            entry = {
                "company": company_name,
                "content_snippet": content[:200],  # Store snippet
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
            }

            data = []
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    try:
                        data = json.load(f)
                    except:
                        pass

            data.append(entry)
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

    async def _store_graph(self, company_name: str, metadata: Dict[str, Any]):
        if self.use_neo4j:
            # Placeholder for Neo4j implementation
            pass
        else:
            # Local Fallback: Save as JSON
            filename = f"{self.local_storage_path}/graph.json"
            entry = {"node": company_name, "type": "Company", "properties": metadata}

            data = []
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    try:
                        data = json.load(f)
                    except:
                        pass

            data.append(entry)
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

    async def _search_pinecone(self, query: str):
        return []

    async def _search_local(self, query: str):
        # Simple keyword match for fallback
        filename = f"{self.local_storage_path}/vectors.json"
        if not os.path.exists(filename):
            return []

        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except:
                return []

        query = query.lower()
        results = []
        for d in data:
            # Check company name
            if query in d.get("company", "").lower():
                results.append(d)
                continue

            # Check metadata (e.g. industry)
            metadata = d.get("metadata", {})
            if any(query in str(v).lower() for v in metadata.values()):
                results.append(d)
                continue

        return results
