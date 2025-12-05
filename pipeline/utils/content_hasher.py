"""
Content Hasher - SimHash implementation for blog content similarity detection.

⚠️ DEPRECATED: This module is deprecated as of 2024-12-03.
Semantic content deduplication is now handled by Gemini embeddings in the Edge Functions.

See:
- supabase/functions/_shared/embedding-client.ts - Embedding client
- supabase/functions/s5-generate-blogs/index.ts - Deduplication integration
- services/content-embedder/ - Modal service for embeddings

The SimHash approach has been replaced because:
1. SimHash only catches near-identical text (lexical similarity)
2. Gemini embeddings catch semantic duplicates (meaning-based similarity)
3. Embeddings are stored in DB for cross-batch comparison

This file is kept for backwards compatibility but should not be used for new code.

Original description:
Uses SimHash algorithm to generate fingerprints for text content that can be
compared to detect similar/duplicate content across blogs.

SimHash properties:
- Similar texts produce similar hashes (small Hamming distance)
- Different texts produce very different hashes (large Hamming distance)
- Fast to compute O(n) where n is number of tokens
"""

import warnings

warnings.warn(
    "content_hasher module is deprecated. Use Gemini embeddings via embedding-client.ts instead.",
    DeprecationWarning,
    stacklevel=2
)

import re
import hashlib
import logging
from typing import Optional, List, Tuple, Set

logger = logging.getLogger(__name__)


class ContentHasher:
    """
    SimHash-based content fingerprinting for duplicate detection.
    
    Uses 64-bit SimHash for efficient similarity comparison.
    Hamming distance < 3 indicates very similar content.
    """
    
    # Number of bits in the hash
    HASH_BITS = 64
    
    # Hamming distance threshold for "similar" content
    SIMILARITY_THRESHOLD = 3
    
    # Stop words to filter out (common words that don't affect meaning)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
        'that', 'these', 'those', 'it', 'its', 'as', 'if', 'when', 'where',
        'how', 'what', 'which', 'who', 'whom', 'whose', 'why', 'not', 'no',
        'yes', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'than', 'too', 'very', 'just', 'also', 'now', 'then',
    }
    
    def __init__(self, similarity_threshold: int = None):
        """
        Initialize the content hasher.
        
        Args:
            similarity_threshold: Hamming distance threshold for similarity (default: 3)
        """
        self.similarity_threshold = similarity_threshold or self.SIMILARITY_THRESHOLD
    
    @classmethod
    def compute_simhash(cls, text: str) -> int:
        """
        Compute SimHash fingerprint for text.
        
        Args:
            text: Input text to hash
            
        Returns:
            64-bit SimHash fingerprint as integer
        """
        if not text:
            return 0
        
        # Tokenize and clean text
        tokens = cls._tokenize(text)
        
        if not tokens:
            return 0
        
        # Initialize bit counts
        bit_counts = [0] * cls.HASH_BITS
        
        # Process each token
        for token in tokens:
            # Get hash for token
            token_hash = cls._get_token_hash(token)
            
            # Update bit counts
            for i in range(cls.HASH_BITS):
                if token_hash & (1 << i):
                    bit_counts[i] += 1
                else:
                    bit_counts[i] -= 1
        
        # Build final hash
        simhash = 0
        for i in range(cls.HASH_BITS):
            if bit_counts[i] > 0:
                simhash |= (1 << i)
        
        return simhash
    
    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """
        Tokenize text into meaningful tokens.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens (words and n-grams)
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)  # Words with 3+ chars
        
        # Filter stop words
        words = [w for w in words if w not in cls.STOP_WORDS]
        
        # Create tokens: individual words + bigrams for better accuracy
        tokens = words.copy()
        
        # Add bigrams (pairs of consecutive words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")
        
        return tokens
    
    @classmethod
    def _get_token_hash(cls, token: str) -> int:
        """
        Get hash for a single token.
        
        Args:
            token: Token string
            
        Returns:
            64-bit hash value
        """
        # Use MD5 and take first 8 bytes (64 bits)
        hash_bytes = hashlib.md5(token.encode('utf-8')).digest()[:8]
        return int.from_bytes(hash_bytes, byteorder='big')
    
    @classmethod
    def hamming_distance(cls, hash1: int, hash2: int) -> int:
        """
        Calculate Hamming distance between two hashes.
        
        Args:
            hash1: First hash
            hash2: Second hash
            
        Returns:
            Number of differing bits
        """
        xor = hash1 ^ hash2
        return bin(xor).count('1')
    
    def is_similar(self, hash1: int, hash2: int) -> bool:
        """
        Check if two hashes represent similar content.
        
        Args:
            hash1: First SimHash
            hash2: Second SimHash
            
        Returns:
            True if content is similar (Hamming distance <= threshold)
        """
        distance = self.hamming_distance(hash1, hash2)
        return distance <= self.similarity_threshold
    
    def compute_hash_for_article(self, article: dict) -> int:
        """
        Compute SimHash for an article dictionary.
        
        Uses headline, intro, and section content for fingerprinting.
        
        Args:
            article: Article dictionary with content fields
            
        Returns:
            64-bit SimHash fingerprint
        """
        # Build content string from article
        content_parts = []
        
        # Include headline (weighted higher by repetition)
        headline = article.get('headline') or article.get('Headline', '')
        if headline:
            content_parts.extend([headline] * 3)  # Weight headline 3x
        
        # Include intro
        intro = article.get('intro') or article.get('Intro', '')
        if intro:
            content_parts.append(intro)
        
        # Include section content
        for i in range(1, 10):
            section_content = article.get(f'section_{i:02d}_content', '')
            if section_content:
                content_parts.append(section_content)
        
        # Include key takeaways
        for i in range(1, 4):
            takeaway = article.get(f'key_takeaway_{i:02d}', '')
            if takeaway:
                content_parts.append(takeaway)
        
        full_content = ' '.join(content_parts)
        return self.compute_simhash(full_content)
    
    def find_similar(
        self,
        target_hash: int,
        existing_hashes: List[Tuple[str, int]]
    ) -> Optional[Tuple[str, int]]:
        """
        Find similar content from a list of existing hashes.
        
        Args:
            target_hash: Hash to compare
            existing_hashes: List of (identifier, hash) tuples
            
        Returns:
            (identifier, hamming_distance) if similar content found, None otherwise
        """
        for identifier, existing_hash in existing_hashes:
            distance = self.hamming_distance(target_hash, existing_hash)
            if distance <= self.similarity_threshold:
                return (identifier, distance)
        
        return None
    
    @staticmethod
    def hash_to_hex(simhash: int) -> str:
        """
        Convert SimHash to hexadecimal string for storage.
        
        Args:
            simhash: 64-bit SimHash integer
            
        Returns:
            16-character hex string
        """
        return format(simhash, '016x')
    
    @staticmethod
    def hex_to_hash(hex_string: str) -> int:
        """
        Convert hexadecimal string back to SimHash.
        
        Args:
            hex_string: 16-character hex string
            
        Returns:
            64-bit SimHash integer
        """
        return int(hex_string, 16)


def compute_content_hash(article: dict) -> str:
    """
    Convenience function to compute SimHash for an article.
    
    Args:
        article: Article dictionary
        
    Returns:
        16-character hex string hash
    """
    hasher = ContentHasher()
    simhash = hasher.compute_hash_for_article(article)
    return hasher.hash_to_hex(simhash)


def check_content_similarity(
    article: dict,
    existing_hashes: List[Tuple[str, str]],
    threshold: int = 3
) -> Optional[Tuple[str, int]]:
    """
    Check if article content is similar to any existing content.
    
    Args:
        article: Article dictionary to check
        existing_hashes: List of (slug/id, hex_hash) tuples
        threshold: Hamming distance threshold
        
    Returns:
        (matching_slug/id, hamming_distance) if similar, None otherwise
    """
    hasher = ContentHasher(similarity_threshold=threshold)
    target_hash = hasher.compute_hash_for_article(article)
    
    # Convert hex strings to integers
    int_hashes = [
        (identifier, hasher.hex_to_hash(hex_hash))
        for identifier, hex_hash in existing_hashes
    ]
    
    return hasher.find_similar(target_hash, int_hashes)
