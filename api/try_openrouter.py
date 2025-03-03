"""Script to test OpenRouter service with Gemini."""
import os
import asyncio
from dotenv import load_dotenv
from app.services.openrouter import OpenRouterService
from app.schemas.file import FileResponse
from uuid import uuid4

# Load environment variables from .env file
load_dotenv("api/.env")

async def main():
    """Test the OpenRouter service with a real request."""
    # Use the new API key directly
    api_key = "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"
    
    print(f"Using API key: {api_key[:10]}...")
    
    # Set API key directly
    os.environ["OPENROUTER_API_KEY"] = api_key
    
    # Print full API key for debugging
    print(f"Full API key: {api_key}")
    
    # Create service instance
    service = OpenRouterService()
    
    # Initialize the client
    await service._ensure_client()
    
    # Test data
    project_context = """
    This is a React TypeScript project. We need to create a new Button component
    that follows modern React best practices and supports primary/secondary variants.
    """
    
    change_request = """
    Create a new Button component in src/components/Button.tsx with the following requirements:
    - Use TypeScript and styled-components
    - Support primary and secondary variants through a variant prop
    - Include hover and active states
    - Follow accessibility best practices
    - Export as the default component
    """
    
    current_files = [
        FileResponse(
            id=str(uuid4()),
            path="src/components/HelloWorld.tsx",
            content="""
import React from 'react';

const HelloWorld: React.FC = () => {
    return <h1>Hello, World!</h1>;
};

export default HelloWorld;
"""
        )
    ]
    
    try:
        print("Requesting changes from OpenRouter (Gemini)...")
        
        # Get raw completion first
        completion = await service.client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
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
        
        # Print raw response
        print("\nRaw Response from Gemini:")
        print(completion.choices[0].message.content)
        
        # Process changes through service
        changes = await service.get_file_changes(project_context, change_request, current_files)
        
        print("\nParsed Changes:")
        for change in changes:
            print(f"\nOperation: {change.operation}")
            print(f"Path: {change.path}")
            print("Content:")
            print(change.content)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
