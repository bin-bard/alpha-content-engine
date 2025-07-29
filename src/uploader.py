"""
OpenAI Assistant and file upload module
Handles creating assistants and uploading files with robust error handling
"""

import os
import json
import time
import logging
from pathlib import Path
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optisigns_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OpenAIUploader:
    def __init__(self, vector_store_id: Optional[str] = None):
        """Initialize OpenAI uploader with optional vector store ID"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.config_file = Path("optibot_config.json")
        self.vector_store_id = vector_store_id
        
        logger.info("OpenAI Uploader initialized")
        
    def load_config(self) -> Dict:
        """Load assistant configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_file}")
                    return config
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return {}
    
    def save_config(self, config: Dict) -> None:
        """Save assistant configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def create_assistant(self) -> str:
        """Create OptiBot assistant with exact system prompt"""
        system_prompt = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""

        try:
            logger.info("Creating new OptiBot assistant...")
            assistant = self.client.beta.assistants.create(
                name="OptiBot",
                instructions=system_prompt,
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
            )
            
            logger.info(f"Assistant created successfully: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            logger.error(f"Failed to create assistant: {e}")
            raise
    
    def create_vector_store(self, name: str = "OptiSigns Support Articles") -> Optional[str]:
        """Create a new vector store"""
        try:
            logger.info(f"Creating new vector store: {name}")
            vector_store = self.client.beta.vector_stores.create(name=name)
            logger.info(f"Vector store created successfully: {vector_store.id}")
            return vector_store.id
            
        except AttributeError as e:
            logger.warning("Vector stores not available via API - manual attachment required")
            return None
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            return None
    
    def verify_vector_store(self, vector_store_id: str) -> bool:
        """Verify if a vector store exists and is accessible"""
        try:
            vector_store = self.client.beta.vector_stores.retrieve(vector_store_id)
            logger.info(f"Vector store verified: {vector_store_id}")
            return True
        except AttributeError:
            logger.warning("Vector stores not available via API")
            return False
        except Exception as e:
            logger.warning(f"Vector store {vector_store_id} not accessible: {e}")
            return False
    
    def upload_files(self, files_data: List[Dict]) -> List:
        """Upload files to OpenAI with error handling"""
        if not files_data:
            logger.info("No files to upload")
            return []
            
        logger.info(f"Starting upload of {len(files_data)} files...")
        uploaded_files = []
        failed_uploads = []
        
        for i, file_data in enumerate(files_data, 1):
            try:
                filename = file_data['filename']
                content = file_data['content']
                
                logger.info(f"[{i}/{len(files_data)}] Uploading: {filename}")
                
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
                    logger.info(f"    File uploaded: {uploaded_file.id}")
                
                # Clean up temp file
                temp_file.unlink()
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
                failed_uploads.append(filename)
                continue
        
        logger.info(f"Upload complete: {len(uploaded_files)} successful, {len(failed_uploads)} failed")
        if failed_uploads:
            logger.warning(f"Failed uploads: {failed_uploads}")
            
        return uploaded_files
    
    def wait_for_batch_completion(self, file_batch, vector_store_id: str, timeout: int = 300) -> bool:
        """Wait for file batch processing to complete"""
        logger.info(f"Waiting for batch {file_batch.id} to complete...")
        start_time = time.time()
        
        while file_batch.status in ['in_progress', 'queued']:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(f"Batch processing timed out after {timeout} seconds")
                return False
            
            time.sleep(3)
            try:
                file_batch = self.client.beta.vector_stores.file_batches.retrieve(
                    batch_id=file_batch.id,
                    vector_store_id=vector_store_id
                )
                logger.info(f"Batch status: {file_batch.status} (elapsed: {elapsed:.1f}s)")
            except Exception as e:
                logger.error(f"Error checking batch status: {e}")
                return False
        
        if file_batch.status == 'completed':
            logger.info("Batch processing completed successfully!")
            return True
        else:
            logger.error(f"Batch processing failed with status: {file_batch.status}")
            return False
    
    def attach_files_to_vector_store(self, uploaded_files: List, vector_store_id: str) -> bool:
        """Add uploaded files to vector store and wait for completion"""
        if not uploaded_files or not vector_store_id:
            logger.warning("No files or vector store to attach")
            return False
            
        try:
            file_ids = [f.id for f in uploaded_files]
            logger.info(f"Adding {len(file_ids)} files to vector store {vector_store_id}")
            
            # Create file batch
            file_batch = self.client.beta.vector_stores.file_batches.create(
                vector_store_id=vector_store_id,
                file_ids=file_ids
            )
            logger.info(f"File batch created: {file_batch.id}")
            
            # Wait for batch completion
            success = self.wait_for_batch_completion(file_batch, vector_store_id)
            
            if success:
                logger.info("Files successfully attached to vector store")
            else:
                logger.error("Failed to attach files to vector store")
                
            return success
            
        except AttributeError:
            logger.warning("Vector store file operations not available via API")
            return False
        except Exception as e:
            logger.error(f"Error attaching files to vector store: {e}")
            return False
    
    def attach_vector_store_to_assistant(self, assistant_id: str, vector_store_id: str) -> bool:
        """Attach vector store to assistant"""
        try:
            logger.info(f"Attaching vector store {vector_store_id} to assistant {assistant_id}")
            
            self.client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            
            logger.info("Vector store successfully attached to assistant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to attach vector store to assistant: {e}")
            return False
    
    def get_or_create_vector_store(self, config: Dict) -> Optional[str]:
        """Get existing vector store or create new one"""
        vector_store_id = self.vector_store_id or config.get('vector_store_id')
        
        # Try to verify existing vector store
        if vector_store_id:
            if self.verify_vector_store(vector_store_id):
                logger.info(f"Using existing vector store: {vector_store_id}")
                return vector_store_id
            else:
                logger.warning(f"Vector store {vector_store_id} not accessible, creating new one")
        
        # Create new vector store
        new_vector_store_id = self.create_vector_store()
        if new_vector_store_id:
            logger.info(f"Created new vector store: {new_vector_store_id}")
            return new_vector_store_id
        else:
            logger.warning("Could not create vector store - manual attachment required")
            return None
    
    def setup_assistant(self, files_data: List[Dict]) -> Tuple[str, bool]:
        """
        Create assistant with vector store following assignment requirements:
        1. Upload files to OpenAI
        2. Attach files to Vector Store 
        3. Create Assistant with vector store attached
        Returns: (assistant_id, success_flag)
        """
        logger.info("Starting OpenAI Assistant setup...")
        
        # Load existing configuration
        config = self.load_config()
        assistant_id = config.get('assistant_id')
        
        # Step 1: Upload files to OpenAI first
        if not files_data:
            logger.info("No files to upload")
            # If no new files but assistant exists, return it
            if assistant_id:
                return assistant_id, True
            # Otherwise create assistant without files
            try:
                assistant_id = self.create_assistant()
                config.update({'assistant_id': assistant_id})
                self.save_config(config)
                return assistant_id, True
            except Exception as e:
                logger.error(f"Failed to create assistant: {e}")
                return None, False
        
        logger.info("Step 1: Uploading files to OpenAI...")
        uploaded_files = self.upload_files(files_data)
        if not uploaded_files:
            logger.error("No files were uploaded successfully")
            return assistant_id, False
        
        # Step 2: Attach files to Vector Store
        logger.info("Step 2: Attaching files to Vector Store...")
        vector_store_id = self.get_or_create_vector_store(config)
        
        vector_store_success = False
        if vector_store_id:
            vector_store_success = self.attach_files_to_vector_store(uploaded_files, vector_store_id)
            logger.info(f"Vector store attachment: {'SUCCESS' if vector_store_success else 'FAILED'}")
        else:
            logger.warning("No vector store available - will create assistant without vector store")
        
        # Step 3: Create Assistant with vector store attached (or update existing)
        logger.info("Step 3: Creating/updating Assistant...")
        
        if not assistant_id:
            # Create new assistant
            try:
                assistant_id = self.create_assistant()
                logger.info(f"New assistant created: {assistant_id}")
            except Exception as e:
                logger.error(f"Failed to create assistant: {e}")
                return None, False
        else:
            logger.info(f"Using existing assistant: {assistant_id}")
        
        # Step 4: Attach vector store to assistant (if we have one)
        attachment_success = False
        if vector_store_id and vector_store_success:
            attachment_success = self.attach_vector_store_to_assistant(assistant_id, vector_store_id)
            logger.info(f"Assistant attachment: {'SUCCESS' if attachment_success else 'FAILED'}")
        
        # Update configuration with all results
        config.update({
            'assistant_id': assistant_id,
            'vector_store_id': vector_store_id,
            'last_upload': datetime.now().isoformat(),
            'files_uploaded': len(uploaded_files),
            'vector_store_success': vector_store_success,
            'attachment_success': attachment_success,
            'manual_attachment_required': not (vector_store_success and attachment_success),
            'chunks_embedded': len(uploaded_files) if vector_store_success else 0
        })
        self.save_config(config)
        
        # Log final results
        logger.info("=" * 50)
        logger.info("SETUP COMPLETE - SUMMARY:")
        logger.info(f"Assistant ID: {assistant_id}")
        logger.info(f"Vector Store ID: {vector_store_id}")
        logger.info(f"Files uploaded: {len(uploaded_files)}")
        logger.info(f"Files embedded in vector store: {len(uploaded_files) if vector_store_success else 0}")
        logger.info(f"Vector store success: {vector_store_success}")
        logger.info(f"Assistant attachment success: {attachment_success}")
        logger.info("=" * 50)
        
        if vector_store_success and attachment_success:
            logger.info("All operations completed successfully!")
            print("Success! Assistant is ready with all files attached!")
            print(f"Files embedded in vector store: {len(uploaded_files)}")
            print(f"Chunks embedded: {len(uploaded_files)} files processed")
        else:
            logger.warning("Manual file attachment may be required")
            print("Files uploaded but manual attachment needed in OpenAI Playground")
            print("File IDs for manual attachment:")
            for i, f in enumerate(uploaded_files, 1):
                print(f"  {i}. {f.id}")
        
        overall_success = len(uploaded_files) > 0 and (vector_store_success or not vector_store_id)
        return assistant_id, overall_success 