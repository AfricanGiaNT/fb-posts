"""
Performance Optimization Handler for Multi-File Upload System
Manages system resources and optimizes operations for multi-file processing.
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceOptimizer:
    """Handles performance optimization for multi-file processing."""
    
    def __init__(self, max_memory_percent: float = 80.0,
                 max_concurrent_files: int = 3):
        self.logger = logging.getLogger(__name__)
        self.max_memory_percent = max_memory_percent
        self.max_concurrent_files = max_concurrent_files
        self._processing_semaphore = asyncio.Semaphore(max_concurrent_files)
        
    async def optimize_batch_processing(self, files: List[Dict]) -> List[Dict]:
        """
        Optimize the processing of multiple files.
        
        Args:
            files: List of file data dictionaries
            
        Returns:
            Processed files with optimized ordering
        """
        try:
            # Check system resources
            if not self._check_system_resources():
                raise ResourceWarning("System resources too constrained")
                
            # Optimize processing order
            optimized_files = self._optimize_processing_order(files)
            
            # Process files with resource management
            processed_files = []
            tasks = []
            
            # Create tasks for each file
            for file_data in optimized_files:
                task = asyncio.create_task(
                    self._process_file_with_resources(file_data.copy())
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            processed_files = await asyncio.gather(*tasks)
            
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Batch processing optimization error: {str(e)}")
            raise
            
    async def optimize_strategy_generation(self, session: Dict) -> Dict:
        """
        Optimize strategy generation process.
        
        Args:
            session: Current session dictionary
            
        Returns:
            Optimized session dictionary
        """
        try:
            # Check memory usage
            if not self._check_memory_usage():
                self._cleanup_session_memory(session)
                
            # Optimize strategy generation
            session = await self._generate_strategy_optimized(session)
            
            return session
            
        except Exception as e:
            self.logger.error(f"Strategy generation optimization error: {str(e)}")
            raise
            
    async def optimize_content_generation(self, session: Dict, file_id: str) -> Dict:
        """
        Optimize content generation for a specific file.
        
        Args:
            session: Current session dictionary
            file_id: ID of the file to generate content for
            
        Returns:
            Updated session dictionary
        """
        try:
            # Find target file
            target_file = None
            for file_data in session['source_files']:
                if file_data['file_id'] == file_id:
                    target_file = file_data
                    break
                    
            if not target_file:
                raise ValueError(f"File {file_id} not found in session")
                
            # Initialize content strategy if not present
            if 'content_strategy' not in session:
                session['content_strategy'] = {
                    'recommended_sequence': [],
                    'cross_references': [],
                    'tone_suggestions': {}
                }
                
            # Optimize context building
            context = await self._build_optimized_context(
                target_file,
                session['source_files'],
                session['content_strategy']
            )
            
            # Generate content with optimized resources
            new_content = await self._generate_content_optimized(
                target_file,
                context
            )
            
            # Update file content
            target_file['content'] = new_content
            
            return session
            
        except Exception as e:
            self.logger.error(f"Content generation optimization error: {str(e)}")
            raise
            
    def _check_system_resources(self) -> bool:
        """Check if system resources are available."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            return (cpu_percent < 90.0 and 
                    memory_percent < self.max_memory_percent)
        except Exception:
            # Default to True if resource check fails
            return True
                
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        return psutil.virtual_memory().percent < self.max_memory_percent
        
    def _cleanup_session_memory(self, session: Dict) -> None:
        """Clean up session memory usage."""
        # Clear any cached data
        if 'cached_analysis' in session:
            del session['cached_analysis']
            
        # Clear any temporary data
        if 'temp_data' in session:
            del session['temp_data']
            
    def _optimize_processing_order(self, files: List[Dict]) -> List[Dict]:
        """Optimize the order of file processing."""
        # Sort files by size (process smaller files first)
        return sorted(files, key=lambda x: len(x.get('content', '')))
        
    async def _process_file_with_resources(self, file_data: Dict) -> Dict:
        """Process a file with resource management."""
        async with self._processing_semaphore:
            try:
                # Check resources before processing
                if not self._check_system_resources():
                    await asyncio.sleep(1)  # Wait for resources
                    
                # Process file
                file_data['processing_status'] = 'processing'
                
                # Perform optimized processing
                file_data = await self._process_optimized(file_data)
                
                file_data['processing_status'] = 'complete'
                return file_data
                
            except Exception as e:
                file_data['processing_status'] = 'error'
                file_data['error'] = str(e)
                raise
                
    async def _process_optimized(self, file_data: Dict) -> Dict:
        """Perform optimized file processing."""
        # Simulate processing with basic analysis
        file_data['word_count'] = len(file_data.get('content', '').split())
        file_data['processed_timestamp'] = datetime.now()
        return file_data
        
    async def _generate_strategy_optimized(self, session: Dict) -> Dict:
        """Generate strategy with optimization."""
        # Implementation would go here
        return session
        
    async def _build_optimized_context(self, target_file: Dict,
                                     all_files: List[Dict],
                                     strategy: Dict) -> Dict:
        """Build optimized context for content generation."""
        # Basic context building
        context = {
            'file_id': target_file['file_id'],
            'related_files': [f for f in all_files if f['file_id'] != target_file['file_id']],
            'strategy': strategy
        }
        return context
        
    async def _generate_content_optimized(self, file_data: Dict,
                                        context: Dict) -> str:
        """Generate content with optimization."""
        # Simple content generation for testing
        return f"Generated content for {file_data['file_id']}" 