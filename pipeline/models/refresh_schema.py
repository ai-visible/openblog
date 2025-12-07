"""
Refresh Response Schema - Structured output for content refresh operations

Defines Pydantic models for Gemini's structured JSON output when refreshing content.
This prevents hallucinations and ensures consistent, type-safe responses.

Similar to output_schema.py for blog generation, but tailored for surgical content updates.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class RefreshedSection(BaseModel):
    """
    A single refreshed content section.
    
    Includes the original heading (unchanged), updated content, and a summary of changes.
    """
    
    heading: str = Field(
        ...,
        description="Section heading (preserved from original, plain text only, NO HTML)"
    )
    
    content: str = Field(
        ...,
        description="Updated section content (may include HTML formatting like <p>, <ul>, <strong>)"
    )
    
    change_summary: Optional[str] = Field(
        default="",
        description="Brief description of what changed in this section (e.g., 'Updated statistics to 2025', 'Made tone more professional')"
    )
    
    @field_validator('heading')
    @classmethod
    def validate_heading(cls, v):
        """Ensure heading is non-empty and reasonable length."""
        if not v or not v.strip():
            raise ValueError("Heading cannot be empty")
        if len(v) > 200:
            raise ValueError("Heading too long (max 200 chars)")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Ensure content is non-empty."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class RefreshResponse(BaseModel):
    """
    Complete response from content refresh operation.
    
    Contains all refreshed sections, updated meta description, and overall change summary.
    """
    
    sections: List[RefreshedSection] = Field(
        ...,
        description="List of refreshed sections (at least 1 section required)"
    )
    
    meta_description: Optional[str] = Field(
        default="",
        description="Updated meta description (120-160 characters, plain text only)"
    )
    
    changes_made: str = Field(
        ...,
        description="Overall summary of all changes made across all sections"
    )
    
    @field_validator('sections')
    @classmethod
    def validate_sections(cls, v):
        """Ensure at least one section is present."""
        if not v or len(v) == 0:
            raise ValueError("At least one section is required")
        if len(v) > 50:
            raise ValueError("Too many sections (max 50)")
        return v
    
    @field_validator('meta_description')
    @classmethod
    def validate_meta_description(cls, v):
        """Validate meta description length if provided."""
        if v and len(v) > 160:
            raise ValueError("Meta description too long (max 160 chars)")
        return v.strip() if v else ""
    
    @field_validator('changes_made')
    @classmethod
    def validate_changes_made(cls, v):
        """Ensure changes summary is provided."""
        if not v or not v.strip():
            raise ValueError("Changes summary cannot be empty")
        if len(v) > 500:
            raise ValueError("Changes summary too long (max 500 chars)")
        return v.strip()

