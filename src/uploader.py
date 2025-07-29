"""
OpenAI Assistant and file upload module
Handles creating assistants and uploading files to existing vector stores
"""

import os
import json
import time
from pathlib import Path
from openai import OpenAI
from datetime import datetime


class OpenAIUploader:
    def __init__(self, vector_store_id=None):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.config_file = Path("optibot_config.json")
        # Use provided vector store ID or try to load from config
        self.vector_store_id = vector_store_id
        
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
                    print(f"  File ID: {uploaded_file.id}")
                
                # Clean up temp file
                temp_file.unlink()
                    
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error uploading {filename}: {e}")
                continue
        
        print(f"Successfully uploaded {len(uploaded_files)} files to OpenAI")
        return uploaded_files
    
    def attach_to_vector_store(self, uploaded_files):
        """Try to attach files to the existing vector store"""
        if not uploaded_files or not self.vector_store_id:
            return False
            
        try:
            print(f"Adding {len(uploaded_files)} files to vector store {self.vector_store_id}...")
            file_ids = [f.id for f in uploaded_files]
            
            # Use file_batches API to add files to vector store
            file_batch = self.client.beta.vector_stores.file_batches.create(
                vector_store_id=self.vector_store_id,
                file_ids=file_ids
            )
            print(f"File batch created: {file_batch.id}")
            
            # Wait for completion
            max_wait = 60  # Maximum 60 seconds
            waited = 0
            
            while file_batch.status in ['in_progress', 'queued'] and waited < max_wait:
                time.sleep(3)
                waited += 3
                try:
                    file_batch = self.client.beta.vector_stores.file_batches.retrieve(
                        batch_id=file_batch.id,
                        vector_store_id=self.vector_store_id
                    )
                    print(f"Batch status: {file_batch.status} (waited {waited}s)")
                except Exception as e:
                    print(f"Error checking batch status: {e}")
                    break
            
            if file_batch.status == 'completed':
                print(f"Successfully added files to vector store!")
                return True
            else:
                print(f"Batch status: {file_batch.status} after {waited}s")
                return False
                
        except Exception as e:
            print(f"Error adding files to vector store: {e}")
            return False
    
    def attach_vector_store_to_assistant(self, assistant_id):
        """Attach the vector store to the assistant"""
        if not self.vector_store_id:
            return False
            
        try:
            print(f"Attaching vector store {self.vector_store_id} to assistant {assistant_id}...")
            self.client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            print(f"Vector store attached to assistant!")
            return True
            
        except Exception as e:
            print(f"Error attaching vector store to assistant: {e}")
            return False
    
    def setup_assistant(self, files_data):
        """Create/update assistant and upload only changed files"""
        print("Setting up OpenAI Assistant...")
        
        # Load existing config
        config = self.load_config()
        assistant_id = config.get('assistant_id')
        
        # Set vector store ID from config if not provided
        if not self.vector_store_id:
            self.vector_store_id = config.get('vector_store_id')
        
        # Create assistant if doesn't exist
        if not assistant_id:
            assistant = self.create_assistant()
            assistant_id = assistant.id
        else:
            print(f"Using existing assistant: {assistant_id}")
        
        # Upload only changed files
        uploaded_files = self.upload_files(files_data)
        
        success_vector_store = False
        success_attachment = False
        
        if uploaded_files and self.vector_store_id:
            # Try to add files to vector store
            success_vector_store = self.attach_to_vector_store(uploaded_files)
            
            # Try to attach vector store to assistant
            success_attachment = self.attach_vector_store_to_assistant(assistant_id)
        elif not self.vector_store_id:
            print("No vector store ID provided - files uploaded but need manual attachment")
        
        # Update config
        config.update({
            'assistant_id': assistant_id,
            'vector_store_id': self.vector_store_id,
            'last_upload': datetime.now().isoformat(),
            'files_uploaded': len(uploaded_files) if uploaded_files else 0,
            'vector_store_attachment_success': success_vector_store and success_attachment
        })
        self.save_config(config)
        
        # Summary
        print(f"\nSetup complete!")
        print(f"Assistant ID: {assistant_id}")
        print(f"Vector Store ID: {self.vector_store_id}")
        print(f"Files uploaded this run: {len(uploaded_files) if uploaded_files else 0}")
        
        if success_vector_store and success_attachment:
            print("Files successfully attached to vector store and assistant!")
        elif uploaded_files:
            print("Files uploaded but may need manual attachment in Playground")
            print("File IDs for manual attachment:")
            for i, f in enumerate(uploaded_files, 1):
                print(f"  {i}. {f.id}")
        
        return assistant_id
    
    def get_file_ids_for_manual_attachment(self):
        """Get recently uploaded file IDs for manual attachment"""
        # This could be enhanced to track recent uploads
        # For now, just indicate that manual steps are needed
        return [] 