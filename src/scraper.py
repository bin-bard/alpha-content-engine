"""
OptiSigns article scraper module
Handles fetching, converting, and saving articles from Zendesk API
"""

import os
import requests
import json
import hashlib
import time
import re
from pathlib import Path
from markdownify import markdownify as md
from datetime import datetime


class OptiSignsScraper:
    def __init__(self):
        # Zendesk configuration
        self.subdomain = os.getenv('ZS_SUBDOMAIN', 'optisignshelp')
        self.email = os.getenv('ZS_EMAIL')
        self.token = os.getenv('ZS_TOKEN')
        
        self.base_url = f"https://{self.subdomain}.zendesk.com/api/v2"
        self.auth = (f"{self.email}/token", self.token) if self.email and self.token else None
        self.session = requests.Session()
        self.articles_dir = Path("articles")
        self.articles_dir.mkdir(exist_ok=True)
        self.metadata_file = Path("article_metadata.json")
        
    def load_metadata(self):
        """Load previous run metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load metadata: {e}")
        return {}
    
    def save_metadata(self, metadata):
        """Save current run metadata"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save metadata: {e}")
    
    def calculate_content_hash(self, content):
        """Calculate SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_all_articles(self):
        """Fetch all articles from Zendesk API"""
        print("Fetching articles from Zendesk API...")
        
        articles = []
        page = 1
        
        while True:
            try:
                url = f"{self.base_url}/help_center/articles.json"
                params = {
                    'page': page,
                    'per_page': 100,
                    'sort_by': 'updated_at',
                    'sort_order': 'desc'
                }
                
                response = self.session.get(url, auth=self.auth, params=params)
                response.raise_for_status()
                
                data = response.json()
                page_articles = data.get('articles', [])
                
                if not page_articles:
                    break
                
                articles.extend(page_articles)
                print(f"Fetched page {page}: {len(page_articles)} articles")
                
                if not data.get('next_page'):
                    break
                
                page += 1
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching articles: {e}")
                break
        
        print(f"Total articles fetched: {len(articles)}")
        return articles
    
    def clean_html_to_markdown(self, html_content):
        """Convert HTML content to clean Markdown"""
        if not html_content:
            return ""
        
        # Convert HTML to Markdown
        markdown = md(html_content, heading_style="ATX")
        
        # Clean up the markdown
        lines = markdown.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, navigation elements, and ads
            if (line and 
                not line.startswith('*') and 
                'navigation' not in line.lower() and
                'advertisement' not in line.lower()):
                cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)
    
    def generate_slug(self, title):
        """Generate a URL-friendly slug from title"""
        if not title:
            return "untitled"
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        return slug[:50]  # Limit length
    
    def save_article(self, article):
        """Save article as markdown file"""
        title = article.get('title', 'Untitled')
        body = article.get('body', '')
        url = article.get('html_url', '')
        
        # Generate filename
        slug = self.generate_slug(title)
        filename = f"{slug}.md"
        filepath = self.articles_dir / filename
        
        # Convert HTML to Markdown
        markdown_content = self.clean_html_to_markdown(body)
        
        # Add frontmatter
        full_content = f"""# {title}

{markdown_content}

Article URL: {url}"""
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        return filename, full_content
    
    def detect_changes(self, articles, limit=None):
        """Detect new, updated, and unchanged articles"""
        print("Detecting changes...")
        
        # Load previous metadata
        previous_metadata = self.load_metadata()
        current_metadata = {}
        
        # Apply limit if specified
        if limit:
            articles = articles[:limit]
        
        new_articles = []
        updated_articles = []
        unchanged_articles = []
        
        for article in articles:
            article_id = str(article.get('id'))
            title = article.get('title', 'Untitled')
            updated_at = article.get('updated_at', '')
            body = article.get('body', '')
            
            # Calculate content hash
            content_hash = self.calculate_content_hash(body)
            
            # Store current metadata
            current_metadata[article_id] = {
                'title': title,
                'updated_at': updated_at,
                'content_hash': content_hash,
                'slug': self.generate_slug(title)
            }
            
            # Check if article is new or updated
            if article_id not in previous_metadata:
                new_articles.append(article)
            elif previous_metadata[article_id].get('content_hash') != content_hash:
                updated_articles.append(article)
            else:
                unchanged_articles.append(article)
        
        # Save current metadata
        self.save_metadata(current_metadata)
        
        return new_articles, updated_articles, unchanged_articles
    
    def scrape_articles(self, limit=None):
        """Main scraping function with delta detection"""
        print("Starting OptiSigns article scraping with delta detection...")
        
        # Get all articles
        articles = self.get_all_articles()
        
        if not articles:
            print("No articles found!")
            return {'added': 0, 'updated': 0, 'skipped': 0, 'files': []}
            
        # Detect changes
        new_articles, updated_articles, unchanged_articles = self.detect_changes(articles, limit)
        
        # Process only new and updated articles
        articles_to_process = new_articles + updated_articles
        processed_files = []
        
        print(f"\nProcessing changes:")
        print(f"- NEW: {len(new_articles)} articles")
        print(f"- UPDATED: {len(updated_articles)} articles") 
        print(f"- UNCHANGED: {len(unchanged_articles)} articles")
        
        if not articles_to_process:
            print("No changes detected, nothing to process.")
            return {
                'added': 0,
                'updated': 0, 
                'skipped': len(unchanged_articles),
                'files': []
            }
        
        # Save changed articles
        for i, article in enumerate(articles_to_process, 1):
            try:
                filename, content = self.save_article(article)
                processed_files.append({
                    'filename': filename,
                    'content': content,
                    'article_id': article.get('id'),
                    'title': article.get('title')
                })
                
                status = "NEW" if article in new_articles else "UPDATED"
                print(f"[{i}/{len(articles_to_process)}] {status}: {filename}")
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Error processing article {i}: {e}")
                continue
        
        result = {
            'added': len(new_articles),
            'updated': len(updated_articles),
            'skipped': len(unchanged_articles),
            'files': processed_files
        }
        
        print(f"\nScraping complete!")
        print(f"Added: {result['added']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
        
        return result 