"""OpenRouter service for AI interactions."""
import os
import re
from typing import List
from openai import OpenAI
from ..models.project import FileChange, AIResponse, FileResponse

class OpenRouterService:
    """Service for interacting with OpenRouter API."""
    
    def __init__(self):
        """Initialize the OpenRouter service."""
        if os.getenv("TESTING"):
            self.client = None
        else:
            self.client = self._get_client()
    
    def _get_client(self) -> OpenAI:
        """Get OpenAI client configured for OpenRouter."""
        if os.getenv("TESTING"):
            return None
            
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
            
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://noodleseed.com",
                "X-Title": "Noodle Seed"
            }
        )
    
    def get_file_changes(
        self,
        project_context: str,
        change_request: str,
        current_files: List[FileResponse]
    ) -> List[FileChange]:
        """Get file changes from AI based on context and request.
        
        Args:
            project_context: Context about the project
            change_request: Requested changes to make
            current_files: List of current files with their paths and content
            
        Returns:
            List of file changes to apply
            
        Raises:
            ValueError: If AI response is invalid
        """
        if self.client is None:
            # During testing, we don't make actual API calls
            return []
            
        completion = self.client.chat.completions.create(
            model="google/gemini-2.0-flash-001",  # Using Gemini 2.0 Flash for testing
            messages=[
                {
                    "role": "system",
                    "content": "You are a code modification assistant. Based on the project context and change request, provide a list of file changes in the following format:\n<noodle_response>\n{\"changes\": [{\"operation\": \"create|update|delete\", \"path\": \"file/path\", \"content\": \"file content\"}]}\n</noodle_response>"
                },
                {
                    "role": "user",
                    "content": "\n".join([
                        "Project Context:",
                        project_context,
                        "",
                        "Current Files:",
                        *[f"- {f.path}:\n{f.content}" for f in current_files],
                        "",
                        "Change Request:",
                        change_request
                    ])
                }
            ]
        )
        
        # Extract response between tags
        response_text = completion.choices[0].message.content
        match = re.search(r"<noodle_response>\s*(.*?)\s*</noodle_response>", response_text, re.DOTALL)
        if not match:
            raise ValueError("AI response missing noodle_response tags")
        
        # Parse changes
        ai_response = AIResponse.model_validate_json(match.group(1))
        return ai_response.changes

def get_openrouter():
    """Dependency to get OpenRouter service."""
    return OpenRouterService()
