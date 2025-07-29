"""
Main scraper and uploader script for OptiSigns support articles
Combined scraper + OpenAI assistant uploader with delta detection
"""

import os
import requests
import json
import hashlib
from markdownify import markdownify as md
from dotenv import load_dotenv
import time
import re
from pathlib import Path
from openai import OpenAI
from datetime import datetime

# Load environment variables
load_dotenv()

# Zendesk configuration
ZS_SUBDOMAIN = os.getenv('ZS_SUBDOMAIN', 'optisignshelp')
ZS_EMAIL = os.getenv('ZS_EMAIL')
ZS_TOKEN = os.getenv('ZS_TOKEN')

class OptiSignsScraper:
    def __init__(self):
        self.base_url = f"https://{ZS_SUBDOMAIN}.zendesk.com/api/v2"
        self.auth = (f"{ZS_EMAIL}/token", ZS_TOKEN) if ZS_EMAIL and ZS_TOKEN else None
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
        """Fetch all articles from Zendesk Help Center"""
        print("Fetching articles from OptiSigns support...")
        
        articles = []
        url = f"{self.base_url}/help_center/articles.json"
        
        while url:
            try:
                if self.auth:
                    response = self.session.get(url, auth=self.auth)
                else:
                    response = self.session.get(url)
                    
                response.raise_for_status()
                data = response.json()
                
                articles.extend(data.get('articles', []))
                url = data.get('next_page')
                
                print(f"Fetched {len(data.get('articles', []))} articles... (Total: {len(articles)})")
                
                # Rate limiting
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching articles: {e}")
                break
                
        print(f"Found {len(articles)} total articles")
        return articles
    
    def clean_html_to_markdown(self, html_content):
        """Convert HTML to clean Markdown"""
        if not html_content:
            return ""
            
        # Convert to markdown
        markdown = md(html_content, 
                     heading_style="ATX",  # Use # style headers
                     bullets="-",          # Use - for bullets
                     strong_em_style="ASTERISK",  # Use ** for bold
                     strip=['script', 'style']  # Remove script/style tags
                     )
        
        # Clean up extra whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = markdown.strip()
        
        return markdown
    
    def generate_slug(self, title):
        """Generate URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def save_article(self, article):
        """Save article as Markdown file"""
        title = article.get('title', 'untitled')
        body = article.get('body', '')
        
        # Generate filename
        slug = self.generate_slug(title)
        filename = f"{slug}.md"
        
        # Convert to markdown
        markdown_content = self.clean_html_to_markdown(body)
        
        # Create full content with metadata
        full_content = f"""# {title}

{markdown_content}

---
*Article URL: {article.get('html_url', 'N/A')}*
*Article ID: {article.get('id', 'N/A')}*
*Last Updated: {article.get('updated_at', 'N/A')}*
"""
        
        # Save to file
        file_path = self.articles_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        return filename, full_content
    
    def detect_changes(self, articles, limit=None):
        """Detect new, updated, and unchanged articles"""
        print("Analyzing article changes...")
        
        # Load previous metadata
        previous_metadata = self.load_metadata()
        
        # Limit articles if specified
        if limit:
            articles = articles[:limit]
            print(f"Processing first {limit} articles...")
        
        new_articles = []
        updated_articles = []
        unchanged_articles = []
        current_metadata = {}
        
        for article in articles:
            article_id = str(article.get('id'))
            title = article.get('title', 'untitled')
            body = article.get('body', '')
            updated_at = article.get('updated_at', '')
            slug = self.generate_slug(title)
            
            # Calculate content hash
            markdown_content = self.clean_html_to_markdown(body)
            content_hash = self.calculate_content_hash(markdown_content)
            
            # Create current metadata entry
            current_metadata[article_id] = {
                'slug': slug,
                'title': title,
                'hash': content_hash,
                'updated_at': updated_at,
                'last_checked': datetime.now().isoformat()
            }
            
            # Compare with previous run
            if article_id not in previous_metadata:
                # New article
                new_articles.append(article)
                print(f"NEW: {title}")
            elif previous_metadata[article_id]['hash'] != content_hash:
                # Updated article
                updated_articles.append(article)
                print(f"UPDATED: {title}")
            else:
                # Unchanged article
                unchanged_articles.append(article)
                print(f"UNCHANGED: {title}")
        
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

class OpenAIUploader:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.config_file = Path("optibot_config.json")
        
    def load_config(self):
        """Load assistant configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        return {}
    
    def save_config(self, config):
        """Save assistant configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def create_assistant(self):
        """Create OptiBot assistant with exact system prompt"""
        system_prompt = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""
        
        print("Creating OptiBot assistant...")
        
        assistant = self.client.beta.assistants.create(
            name="OptiBot",
            instructions=system_prompt,
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
        )
        
        print(f"Assistant created: {assistant.id}")
        return assistant
    
    def upload_files(self, files_data):
        """Upload only changed files to OpenAI"""
        if not files_data:
            print("No files to upload")
            return []
            
        print(f"Uploading {len(files_data)} changed files to OpenAI...")
        
        uploaded_files = []
        
        for file_data in files_data:
            try:
                filename = file_data['filename']
                content = file_data['content']
                
                print(f"Uploading: {filename}")
                
                # Create temporary file for upload
                temp_file = Path(f"temp_{filename}")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Upload to OpenAI
                with open(temp_file, 'rb') as f:
                    uploaded_file = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                    uploaded_files.append(uploaded_file)
                
                # Clean up temp file
                temp_file.unlink()
                    
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error uploading {filename}: {e}")
                continue
        
        print(f"Successfully uploaded {len(uploaded_files)} files to OpenAI")
        return uploaded_files
    
    def setup_assistant(self, files_data):
        """Create/update assistant and upload only changed files"""
        print("Setting up OpenAI Assistant...")
        
        # Load existing config
        config = self.load_config()
        assistant_id = config.get('assistant_id')
        
        # Create assistant if doesn't exist
        if not assistant_id:
            assistant = self.create_assistant()
            assistant_id = assistant.id
        else:
            print(f"Using existing assistant: {assistant_id}")
        
        # Upload only changed files
        uploaded_files = self.upload_files(files_data)
        
        if not uploaded_files:
            print("No new files uploaded")
        
        # Update config
        config.update({
            'assistant_id': assistant_id,
            'last_upload': datetime.now().isoformat(),
            'files_uploaded': len(uploaded_files)
        })
        self.save_config(config)
        
        print(f"Setup complete!")
        print(f"Assistant ID: {assistant_id}")
        print(f"Files uploaded this run: {len(uploaded_files)}")
        
        return assistant_id

def main():
    """Main function: scrape articles with delta detection and upload changes"""
    print("OptiSigns Scraper + Uploader with Delta Detection")
    print("=" * 50)
    
    # Step 1: Scrape with delta detection
    scraper = OptiSignsScraper()
    result = scraper.scrape_articles(limit=35)  # Get 35+ articles
    
    if result['added'] == 0 and result['updated'] == 0:
        print("No changes detected, exiting...")
        return
    
    # Step 2: Upload only changed files to OpenAI
    try:
        uploader = OpenAIUploader()
        assistant_id = uploader.setup_assistant(result['files'])
        
        print(f"\nSuccess! OptiBot ready at: {assistant_id}")
        print(f"Final counts - Added: {result['added']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
            
    except Exception as e:
        print(f"Upload failed: {e}")
        print("Note: Scraping completed successfully, upload can be retried")

if __name__ == "__main__":
    main() 