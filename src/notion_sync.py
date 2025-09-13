import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError


class NotionClient:
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id
        self.rate_limit_delay = 0.4  # Notionのレート制限対策（1秒あたり3リクエスト以下）
    
    def upsert_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = self._find_existing_entry(entry_data['guid'])
            
            if existing:
                result = self._update_entry(existing['id'], entry_data)
                print(f"Updated entry: {entry_data['title'][:50]}...")
                return result
            else:
                result = self._create_entry(entry_data)
                print(f"Created entry: {entry_data['title'][:50]}...")
                return result
        
        except Exception as e:
            print(f"Error upserting entry {entry_data.get('guid', 'unknown')}: {e}")
            raise
    
    def _find_existing_entry(self, guid: str) -> Optional[Dict[str, Any]]:
        try:
            self._handle_rate_limit()
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "GUID",
                    "rich_text": {
                        "equals": guid
                    }
                },
                page_size=1
            )
            
            if response['results']:
                return response['results'][0]
            return None
        
        except APIResponseError as e:
            if e.status == 429:
                self._handle_429_error(e)
                return self._find_existing_entry(guid)
            raise
    
    def _create_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._handle_rate_limit()
            
            properties = self._build_notion_properties(entry_data)
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            return response
        
        except APIResponseError as e:
            if e.status == 429:
                self._handle_429_error(e)
                return self._create_entry(entry_data)  # リトライ
            raise
    
    def _update_entry(self, page_id: str, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._handle_rate_limit()
            
            properties = self._build_notion_properties(entry_data)
            
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            return response
        
        except APIResponseError as e:
            if e.status == 429:
                self._handle_429_error(e)
                return self._update_entry(page_id, entry_data)  # リトライ
            raise
    
    def _build_notion_properties(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": entry_data['title'][:2000]  # Notion制限
                        }
                    }
                ]
            },
            "URL": {
                "url": entry_data['url']
            },
            "GUID": {
                "rich_text": [
                    {
                        "text": {
                            "content": entry_data['guid']
                        }
                    }
                ]
            },
            "Source": {
                "select": {
                    "name": entry_data['source']
                }
            },
            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": entry_data['summary'][:2000]  # Notion制限
                        }
                    }
                ]
            }
        }
        
        if entry_data.get('published_at'):
            properties["PublishedAt"] = {
                "date": {
                    "start": entry_data['published_at'].isoformat()
                }
            }
        
        if entry_data.get('tags'):
            properties["Tags"] = {
                "multi_select": [
                    {"name": tag[:100]} for tag in entry_data['tags'][:25]  # Notion制限
                ]
            }
        
        return properties
    
    def _handle_rate_limit(self):
        time.sleep(self.rate_limit_delay)
    
    def _handle_429_error(self, error: APIResponseError):
        retry_after = 1
        
        # Retry-Afterヘッダーがあれば使用
        if hasattr(error, 'response') and error.response:
            retry_after_header = error.response.headers.get('Retry-After')
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    pass
        
        print(f"Rate limit hit, waiting {retry_after} seconds...")
        time.sleep(retry_after)
    
    def batch_upsert(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        results = {
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        for entry in entries:
            try:
                existing = self._find_existing_entry(entry['guid'])
                
                if existing:
                    self._update_entry(existing['id'], entry)
                    results['updated'] += 1
                else:
                    self._create_entry(entry)
                    results['created'] += 1
                    
            except Exception as e:
                print(f"Error processing entry {entry.get('title', 'unknown')}: {e}")
                results['errors'] += 1
        
        return results
    
    def test_connection(self) -> bool:
        try:
            self.client.databases.retrieve(self.database_id)
            return True
        except Exception as e:
            print(f"Notion connection test failed: {e}")
            return False