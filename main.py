"""
Main scraper and uploader script for OptiSigns support articles
Combined scraper + OpenAI assistant uploader
"""

import os
import requests
import json
from markdownify import markdownify as md
from dotenv import load_dotenv
import time
import re
from pathlib import Path
from openai import OpenAI

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
            
        print(f"Saved: {filename}")
        return filename
    
    def scrape_articles(self, limit=None):
        """Main scraping function"""
        print("Starting OptiSigns article scraping...")
        
        # Get all articles
        articles = self.get_all_articles()
        
        if not articles:
            print("No articles found!")
            return 0
            
        # Limit articles if specified
        if limit:
            articles = articles[:limit]
            print(f"Processing first {limit} articles...")
        
        # Process each article
        saved_count = 0
        for i, article in enumerate(articles, 1):
            try:
                filename = self.save_article(article)
                saved_count += 1
                print(f"[{i}/{len(articles)}] Processed: {article.get('title', 'N/A')}")
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Error processing article {i}: {e}")
                continue
        
        print(f"\nScraping complete!")
        print(f"Successfully saved {saved_count}/{len(articles)} articles")
        return saved_count

class OpenAIUploader:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.articles_dir = Path("articles")
        
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
    
    def upload_files(self):
        """Upload all markdown files to OpenAI"""
        if not self.articles_dir.exists():
            print(f"Articles directory not found: {self.articles_dir}")
            return []
            
        # Get all markdown files
        md_files = list(self.articles_dir.glob("*.md"))
        if not md_files:
            print("No markdown files found!")
            return []
            
        print(f"Found {len(md_files)} markdown files to upload...")
        
        uploaded_files = []
        
        for md_file in md_files:
            try:
                print(f"Uploading: {md_file.name}")
                
                with open(md_file, 'rb') as file:
                    uploaded_file = self.client.files.create(
                        file=file,
                        purpose='assistants'
                    )
                    uploaded_files.append(uploaded_file)
                    
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error uploading {md_file.name}: {e}")
                continue
        
        print(f"Successfully uploaded {len(uploaded_files)} files to OpenAI")
        return uploaded_files
    
    def setup_assistant(self):
        """Create assistant and upload files"""
        print("Setting up OpenAI Assistant...")
        
        # Create assistant
        assistant = self.create_assistant()
        
        # Upload files
        uploaded_files = self.upload_files()
        
        if not uploaded_files:
            print("No files uploaded")
            return None
        
        print(f"Setup complete!")
        print(f"Assistant ID: {assistant.id}")
        print(f"Files uploaded: {len(uploaded_files)}")
        
        # Save configuration
        with open("optibot_config.txt", "w") as f:
            f.write(f"assistant_id={assistant.id}\n")
            f.write(f"files_count={len(uploaded_files)}\n")
        
        print("Configuration saved to optibot_config.txt")
        return assistant

def main():
    """Main function: scrape articles and upload to OpenAI"""
    print("OptiSigns Scraper + Uploader")
    print("=" * 40)
    
    # Step 1: Scrape articles
    scraper = OptiSignsScraper()
    article_count = scraper.scrape_articles(limit=35)  # Get 35+ articles
    
    if article_count == 0:
        print("No articles scraped, exiting...")
        return
    
    # Step 2: Upload to OpenAI
    try:
        uploader = OpenAIUploader()
        assistant = uploader.setup_assistant()
        
        if assistant:
            print(f"\nSuccess! OptiBot ready at: {assistant.id}")
        else:
            print("Failed to create assistant")
            
    except Exception as e:
        print(f"Upload failed: {e}")
        print("Note: Scraping completed successfully, upload can be retried")

if __name__ == "__main__":
    main() 