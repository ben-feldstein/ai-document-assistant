#!/usr/bin/env python3
"""
Corpus ingestion script for the AI Voice Policy Assistant.

This script ingests sample policy documents into the system
for testing and demonstration purposes.
"""

import os
import sys
import json
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models.entities import Doc
from api.models.db import get_db_session
from api.services.vectorizer import vectorizer_service


class CorpusIngester:
    """Handles ingestion of policy documents into the corpus."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000", api_token: str = None):
        self.api_base_url = api_base_url
        self.api_token = api_token
        self.client = httpx.AsyncClient(timeout=30.0)
        
        if api_token:
            self.client.headers.update({"Authorization": f"Bearer {api_token}"})
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.acquire()
    
    async def ingest_directory(self, directory_path: str, org_id: int = 1) -> List[Dict[str, Any]]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            org_id: Organization ID to associate documents with
            
        Returns:
            List of ingestion results
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        results = []
        
        # Process different file types
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    result = await self._ingest_file(file_path, org_id)
                    results.append(result)
                    print(f"✓ Ingested: {file_path.name}")
                except Exception as e:
                    error_result = {
                        "file": str(file_path),
                        "success": False,
                        "error": str(e)
                    }
                    results.append(error_result)
                    print(f"✗ Failed: {file_path.name} - {e}")
        
        return results
    
    async def _ingest_file(self, file_path: Path, org_id: int) -> Dict[str, Any]:
        """Ingest a single file."""
        file_extension = file_path.suffix.lower()
        
        if file_extension == ".json":
            return await self._ingest_json_file(file_path, org_id)
        elif file_extension in [".txt", ".md"]:
            return await self._ingest_text_file(file_path, org_id)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    async def _ingest_json_file(self, file_path: Path, org_id: int) -> Dict[str, Any]:
        """Ingest a JSON file containing document data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ["title", "text"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare document data
        document_data = {
            "source": str(file_path),
            "uri": data.get("uri"),
            "title": data["title"],
            "text": data["text"],
            "metadata": data.get("metadata", {}),
            "org_id": org_id
        }
        
        # Ingest via API
        response = await self.client.post(
            f"{self.api_base_url}/corpus/doc",
            json=document_data
        )
        
        if response.status_code == 200:
            return {
                "file": str(file_path),
                "success": True,
                "document_id": response.json()["data"]["id"]
            }
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    async def _ingest_text_file(self, file_path: Path, org_id: int) -> Dict[str, Any]:
        """Ingest a plain text or markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from filename or first line
        title = file_path.stem.replace('_', ' ').title()
        
        # Prepare document data
        document_data = {
            "source": str(file_path),
            "title": title,
            "text": content,
            "metadata": {
                "file_type": file_path.suffix,
                "file_size": len(content),
                "ingested_by": "corpus_ingester"
            },
            "org_id": org_id
        }
        
        # Ingest via API
        response = await self.client.post(
            f"{self.api_base_url}/corpus/doc",
            json=document_data
        )
        
        if response.status_code == 200:
            return {
                "file": str(file_path),
                "success": True,
                "document_id": response.json()["data"]["id"]
            }
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    async def ingest_direct_to_db(self, directory_path: str, org_id: int = 1) -> List[Dict[str, Any]]:
        """
        Ingest documents directly to database (bypassing API).
        
        This is useful for bulk ingestion or when the API is not available.
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        results = []
        db = get_db_session()
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        result = await self._ingest_file_to_db(file_path, org_id, db)
                        results.append(result)
                        print(f"✓ Ingested to DB: {file_path.name}")
                    except Exception as e:
                        error_result = {
                            "file": str(file_path),
                            "success": False,
                            "error": str(e)
                        }
                        results.append(error_result)
                        print(f"✗ Failed: {file_path.name} - {e}")
        finally:
            db.close()
        
        return results
    
    async def _ingest_file_to_db(self, file_path: Path, org_id: int, db: Any) -> Dict[str, Any]:
        """Ingest a file directly to the database."""
        file_extension = file_path.suffix.lower()
        
        if file_extension == ".json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            title = data["title"]
            text = data["text"]
            metadata = data.get("metadata", {})
        elif file_extension in [".txt", ".md"]:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            title = file_path.stem.replace('_', ' ').title()
            metadata = {
                "file_type": file_path.suffix,
                "file_size": len(text),
                "ingested_by": "corpus_ingester"
            }
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Create document
        document = Doc(
            org_id=org_id,
            source=str(file_path),
            title=title,
            text=text,
            metadata=metadata
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "file": str(file_path),
            "success": True,
            "document_id": document.id
        }


async def main():
    """Main entry point for the corpus ingestion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest policy documents into the corpus")
    parser.add_argument("directory", help="Directory containing documents to ingest")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--token", help="API authentication token")
    parser.add_argument("--org-id", type=int, default=1, help="Organization ID")
    parser.add_argument("--direct-db", action="store_true", help="Ingest directly to database")
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    # Create ingester
    ingester = CorpusIngester(args.api_url, args.token)
    
    try:
        if args.direct_db:
            print("Ingesting documents directly to database...")
            results = await ingester.ingest_direct_to_db(args.directory, args.org_id)
        else:
            print("Ingesting documents via API...")
            results = await ingester.ingest_directory(args.directory, args.org_id)
        
        # Print summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        print(f"\nIngestion complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed files:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['file']}: {result['error']}")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        sys.exit(1)
    finally:
        await ingester.close()


if __name__ == "__main__":
    asyncio.run(main())
