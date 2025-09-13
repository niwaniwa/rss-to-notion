import feedparser
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser


class RSSParser:
    def __init__(self):
        pass
    
    def fetch_and_parse_feed(self, feed_url: str, feed_name: str, feed_tags: List[str] = None) -> List[Dict[str, Any]]:
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                print(f"Warning: Feed parsing error for {feed_url}: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries:
                entry_data = self.extract_entry_data(entry, feed_name, feed_tags)
                if entry_data:
                    entries.append(entry_data)
            
            return entries
        
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def extract_entry_data(self, entry: Any, feed_name: str, feed_tags: List[str] = None) -> Optional[Dict[str, Any]]:
        try:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            
            if not title or not link:
                return None
            
            published_at = self._parse_published_date(entry)
            
            guid = self._generate_guid(entry, link, published_at)
            
            summary = self._extract_summary(entry)
            
            tags = self._extract_tags(entry, feed_tags or [])
            
            return {
                'title': title,
                'url': link,
                'published_at': published_at,
                'source': feed_name,
                'guid': guid,
                'summary': summary,
                'tags': tags
            }
        
        except Exception as e:
            print(f"Error extracting entry data: {e}")
            return None
    
    def _parse_published_date(self, entry: Any) -> Optional[datetime]:
        date_fields = ['published', 'pubDate', 'updated', 'date']
        
        for field in date_fields:
            date_str = entry.get(field)
            if date_str:
                try:
                    return date_parser.parse(date_str)
                except Exception:
                    continue
        
        return datetime.utcnow()
    
    def _generate_guid(self, entry: Any, link: str, published_at: Optional[datetime]) -> str:
        guid = entry.get('guid') or entry.get('id')
        if guid:
            return str(guid)
        
        hash_input = link
        if published_at:
            hash_input += published_at.isoformat()
        
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def _extract_summary(self, entry: Any) -> str:
        summary_fields = ['summary', 'description', 'content']
        
        for field in summary_fields:
            content = entry.get(field)
            if content:
                if isinstance(content, list) and content:
                    content = content[0]
                if hasattr(content, 'value'):
                    content = content.value
                
                clean_content = self._clean_html(str(content))
                
                if len(clean_content) > 500:
                    clean_content = clean_content[:500] + "..."
                
                return clean_content.strip()
        
        return ""
    
    def _clean_html(self, html_content: str) -> str:
        clean = re.sub(r'<[^>]+>', '', html_content)
        
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&apos;', "'")
        clean = clean.replace('&#39;', "'")
        clean = clean.replace('&nbsp;', ' ')
        
        # 連続する空白を単一スペースに
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean.strip()
    
    def _extract_tags(self, entry: Any, feed_tags: List[str]) -> List[str]:
        tags = list(feed_tags)
        
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, 'term') and tag.term:
                    tags.append(tag.term.strip())
        
        categories = entry.get('categories', [])
        if categories:
            tags.extend([cat.strip() for cat in categories if cat.strip()])
        
        normalized_tags = []
        for tag in tags:
            tag = tag.lower().strip()
            if tag and tag not in normalized_tags:
                normalized_tags.append(tag)
        
        return normalized_tags