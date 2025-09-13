import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class FeedConfig:
    url: str
    name: str
    tags: List[str]


class Config:
    def __init__(self, config_file: str = "feeds.json"):
        self.config_file = config_file
        self.notion_token = self._get_env_var("NOTION_TOKEN")
        self.notion_database_id = self._get_env_var("NOTION_DATABASE_ID")
        self.feeds = self._load_feeds_config()
    
    def _get_env_var(self, var_name: str) -> str:
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required")
        return value
    
    def _load_feeds_config(self) -> List[FeedConfig]:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            feeds = []
            for feed_data in data.get('feeds', []):
                feeds.append(FeedConfig(
                    url=feed_data['url'],
                    name=feed_data['name'],
                    tags=feed_data.get('tags', [])
                ))
            
            if not feeds:
                raise ValueError("No feeds configured in feeds.json")
            
            return feeds
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_file}: {e}")
    
    def validate(self) -> bool:
        if not self.notion_token:
            print("Error: NOTION_TOKEN environment variable is required")
            return False
        
        if not self.notion_database_id:
            print("Error: NOTION_DATABASE_ID environment variable is required")
            return False
        
        if not self.feeds:
            print("Error: No feeds configured")
            return False
        
        return True