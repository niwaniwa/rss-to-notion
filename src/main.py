#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any

from config import Config
from rss_parser import RSSParser
from notion_sync import NotionClient


def main():
    try:
        print(f"RSS to Notion Sync started at {datetime.now(ZoneInfo("Asia/Tokyo"))}")
        
        config = Config()
        if not config.validate():
            sys.exit(1)
        
        print(f"Loaded {len(config.feeds)} feeds")
        
        rss_parser = RSSParser()
        notion_client = NotionClient(config.notion_token, config.notion_database_id)
        
        if not notion_client.test_connection():
            print("Error: Failed to connect to Notion")
            sys.exit(1)
        
        print("Notion connection successful")
        
        total_results = {
            'feeds_processed': 0,
            'feeds_failed': 0,
            'entries_created': 0,
            'entries_updated': 0,
            'entries_failed': 0
        }
        
        for feed_config in config.feeds:
            try:
                print(f"Processing feed: {feed_config.name}")
                
                entries = rss_parser.fetch_and_parse_feed(
                    feed_config.url,
                    feed_config.name,
                    feed_config.tags
                )
                
                if not entries:
                    print(f"No entries found for {feed_config.name}")
                    continue
                
                print(f"Found {len(entries)} entries")
                
                feed_results = sync_entries_to_notion(notion_client, entries)
                
                total_results['feeds_processed'] += 1
                total_results['entries_created'] += feed_results['created']
                total_results['entries_updated'] += feed_results['updated']
                total_results['entries_failed'] += feed_results['errors']
                
                print(f"Feed {feed_config.name}: {feed_results['created']} created, "
                      f"{feed_results['updated']} updated, {feed_results['errors']} errors")
            
            except Exception as e:
                print(f"Error processing feed {feed_config.name}: {e}")
                total_results['feeds_failed'] += 1
        
        # 最終結果出力
        print_final_results(total_results)
        
        # GitHub Actions Job Summary用の出力
        output_github_summary(total_results)
        
        print(f"RSS to Notion Sync completed at {datetime.now(ZoneInfo("Asia/Tokyo"))}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


def sync_entries_to_notion(notion_client: NotionClient, entries: list) -> Dict[str, int]:
    results = {
        'created': 0,
        'updated': 0,
        'errors': 0
    }
    
    for entry in entries:
        try:
            existing = notion_client._find_existing_entry(entry['guid'])
            
            if existing:
                notion_client._update_entry(existing['id'], entry)
                results['updated'] += 1
            else:
                notion_client._create_entry(entry)
                results['created'] += 1
                
        except Exception as e:
            print(f"Error syncing entry '{entry.get('title', 'unknown')}': {e}")
            results['errors'] += 1
    
    return results


def print_final_results(results: Dict[str, int]):
    print("\\n" + "="*50)
    print("SYNC RESULTS")
    print("="*50)
    print(f"Feeds processed: {results['feeds_processed']}")
    print(f"Feeds failed: {results['feeds_failed']}")
    print(f"Entries created: {results['entries_created']}")
    print(f"Entries updated: {results['entries_updated']}")
    print(f"Entries failed: {results['entries_failed']}")
    print(f"Total entries: {results['entries_created'] + results['entries_updated']}")
    print("="*50)


def output_github_summary(results: Dict[str, int]):
    if 'GITHUB_STEP_SUMMARY' in os.environ:
        summary = f"""## RSS to Notion Sync Results

| Metric | Count |
|--------|-------|
| Feeds Processed | {results['feeds_processed']} |
| Feeds Failed | {results['feeds_failed']} |
| Entries Created | {results['entries_created']} |
| Entries Updated | {results['entries_updated']} |
| Entries Failed | {results['entries_failed']} |
| **Total Entries** | **{results['entries_created'] + results['entries_updated']}** |

Sync completed at {datetime.now(ZoneInfo("Asia/Tokyo"))}
"""
        
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'w') as f:
            f.write(summary)


if __name__ == "__main__":
    main()