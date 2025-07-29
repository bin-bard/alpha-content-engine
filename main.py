"""
Main entry point for OptiSigns scraper and uploader
Orchestrates scraping articles and uploading to OpenAI Assistant
"""

import os
from dotenv import load_dotenv
from src.scraper import OptiSignsScraper
from src.uploader import OpenAIUploader

# Load environment variables
load_dotenv()

# Your existing vector store ID from OpenAI UI
VECTOR_STORE_ID = "vs_688930b3082c8191a882a9d8471bb562"

def main():
    """Main function: scrape articles with delta detection and upload changes"""
    print("OptiSigns Scraper + Uploader with Delta Detection")
    print("=" * 50)
    
    try:
        # Step 1: Scrape with delta detection
        print("Step 1: Scraping articles...")
        scraper = OptiSignsScraper()
        result = scraper.scrape_articles(limit=35)  # Get 35+ articles
        
        if result['added'] == 0 and result['updated'] == 0:
            print("No changes detected, exiting...")
            return 0
        
        # Step 2: Upload only changed files to OpenAI
        print("\nStep 2: Uploading to OpenAI...")
        uploader = OpenAIUploader(vector_store_id=VECTOR_STORE_ID)
        assistant_id = uploader.setup_assistant(result['files'])
        
        print(f"\nSuccess! OptiBot ready at: {assistant_id}")
        print(f"Final counts - Added: {result['added']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
        
        # Instructions for testing
        print(f"\nNext steps:")
        print(f"1. Go to: https://platform.openai.com/playground/assistants?assistant={assistant_id}")
        print(f"2. Ask: 'How do I add a YouTube video?'")
        print(f"3. Take a screenshot of the response with citations")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Scraping may have completed successfully, upload can be retried")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 