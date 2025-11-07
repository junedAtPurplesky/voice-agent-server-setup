#!/usr/bin/env python3
"""
Text processing and buffering for streaming TTS
"""

import re
from typing import List, Optional, Iterator
from collections import deque
import logging

from config import TextProcessingConfig, StreamingConfig

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text preprocessing and chunking for TTS"""
    
    def __init__(self, config: TextProcessingConfig):
        self.config = config
        
        # Sentence boundary regex
        self.sentence_pattern = re.compile(
            r'([.!?]+[\s\n]*|[\n]{2,})',
            re.UNICODE
        )
        
        # Number normalization patterns
        self.number_patterns = {
            r'\b(\d+)%\b': r'\1 percent',
            r'\$(\d+)': r'\1 dollars',
            r'\b(\d+)°\b': r'\1 degrees',
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for TTS
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not self.config.normalize_text:
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters if configured
        if self.config.remove_special_chars:
            text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        
        # Normalize numbers
        for pattern, replacement in self.number_patterns.items():
            text = re.sub(pattern, replacement, text)
        
        # Expand common abbreviations
        text = self._expand_abbreviations(text)
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations"""
        abbreviations = {
            r'\bDr\.': 'Doctor',
            r'\bMr\.': 'Mister',
            r'\bMrs\.': 'Missus',
            r'\bMs\.': 'Miss',
            r'\betc\.': 'et cetera',
            r'\be\.g\.': 'for example',
            r'\bi\.e\.': 'that is',
        }
        
        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not self.config.split_sentences:
            return [text]
        
        # Split by sentence boundaries
        parts = self.sentence_pattern.split(text)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            if self.sentence_pattern.match(part):
                # This is a delimiter
                if current_sentence:
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                # This is content
                current_sentence += part
        
        # Add remaining content
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Split long sentences if needed
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > self.config.max_sentence_length:
                # Split by commas or semicolons
                sub_parts = re.split(r'[,;]', sentence)
                for part in sub_parts:
                    if part.strip():
                        final_sentences.append(part.strip())
            else:
                final_sentences.append(sentence)
        
        return [s for s in final_sentences if s]
    
    def process_text(self, text: str) -> List[str]:
        """
        Complete text processing pipeline
        
        Args:
            text: Input text
            
        Returns:
            List of processed sentences ready for TTS
        """
        # Normalize
        text = self.normalize_text(text)
        
        # Split into sentences
        sentences = self.split_sentences(text)
        
        return sentences
    
    def parse_ssml(self, ssml_text: str) -> List[dict]:
        """
        Parse SSML markup (simplified implementation)
        
        Args:
            ssml_text: SSML formatted text
            
        Returns:
            List of text chunks with metadata
        """
        # This is a simplified SSML parser
        # Full implementation would use XML parser
        
        # Remove SSML tags for now and extract text
        text = re.sub(r'<[^>]+>', '', ssml_text)
        
        # Process as regular text
        sentences = self.process_text(text)
        
        return [{"text": s, "metadata": {}} for s in sentences]


class TextBuffer:
    """
    Buffer for streaming text processing
    Implements ElevenLabs-style flush behavior
    """
    
    def __init__(
        self,
        streaming_config: StreamingConfig,
        text_config: TextProcessingConfig
    ):
        self.streaming_config = streaming_config
        self.text_processor = TextProcessor(text_config)
        
        self.buffer = []
        self.sentence_count = 0
        self.total_processed = 0
    
    def add_text(self, text: str) -> List[str]:
        """
        Add text to buffer and return sentences ready for synthesis
        
        Args:
            text: Input text chunk
            
        Returns:
            List of sentences ready to synthesize (if flush threshold reached)
        """
        # Process incoming text
        sentences = self.text_processor.process_text(text)
        
        # Add to buffer
        self.buffer.extend(sentences)
        self.sentence_count += len(sentences)
        
        # Check if we should flush
        if self.sentence_count >= self.streaming_config.flush_threshold:
            return self.flush()
        
        return []
    
    def flush(self) -> List[str]:
        """
        Flush buffer and return all accumulated sentences
        
        Returns:
            All buffered sentences
        """
        if not self.buffer:
            return []
        
        sentences = self.buffer.copy()
        self.buffer.clear()
        self.sentence_count = 0
        self.total_processed += len(sentences)
        
        logger.debug(f"Flushed {len(sentences)} sentences")
        
        return sentences
    
    def has_data(self) -> bool:
        """Check if buffer has data"""
        return len(self.buffer) > 0
    
    def reset(self):
        """Reset buffer"""
        self.buffer.clear()
        self.sentence_count = 0
        logger.debug("Text buffer reset")
    
    def get_stats(self) -> dict:
        """Get buffer statistics"""
        return {
            "buffered_sentences": len(self.buffer),
            "total_processed": self.total_processed,
            "will_flush_in": max(0, self.streaming_config.flush_threshold - self.sentence_count)
        }


class StreamingSentenceIterator:
    """
    Iterator for streaming sentence-by-sentence synthesis
    with proper buffering and flush control
    """
    
    def __init__(
        self,
        text: str,
        text_config: TextProcessingConfig,
        streaming_config: StreamingConfig
    ):
        self.text_processor = TextProcessor(text_config)
        self.streaming_config = streaming_config
        
        # Process all text into sentences
        self.sentences = self.text_processor.process_text(text)
        self.current_index = 0
        
        logger.debug(f"Streaming iterator created with {len(self.sentences)} sentences")
    
    def __iter__(self):
        return self
    
    def __next__(self) -> List[str]:
        """
        Get next batch of sentences according to flush threshold
        
        Returns:
            List of sentences to synthesize together
            
        Raises:
            StopIteration: When no more sentences
        """
        if self.current_index >= len(self.sentences):
            raise StopIteration
        
        # Get batch according to flush threshold
        batch_size = self.streaming_config.flush_threshold
        batch = []
        
        while (self.current_index < len(self.sentences) and 
               len(batch) < batch_size):
            batch.append(self.sentences[self.current_index])
            self.current_index += 1
        
        return batch
    
    def has_more(self) -> bool:
        """Check if there are more sentences"""
        return self.current_index < len(self.sentences)
    
    def get_progress(self) -> dict:
        """Get progress information"""
        return {
            "current": self.current_index,
            "total": len(self.sentences),
            "remaining": len(self.sentences) - self.current_index,
            "percentage": (self.current_index / len(self.sentences) * 100) if self.sentences else 100
        }

