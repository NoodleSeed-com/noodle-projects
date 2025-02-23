"""Script to test OpenRouter service with Gemini."""
import os
from app.services.openrouter import OpenRouterService
from app.models.project import FileResponse
from uuid import uuid4

def main():
    """Test the OpenRouter service with a real request."""
    # Set API key
    os.environ["OPENROUTER_API_KEY"] = "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"
    
    # Create service instance
    service = OpenRouterService()
    
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
        completion = service.client.chat.completions.create(
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
        changes = service.get_file_changes(project_context, change_request, current_files)
        
        print("\nParsed Changes:")
        for change in changes:
            print(f"\nOperation: {change.operation}")
            print(f"Path: {change.path}")
            print("Content:")
            print(change.content)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
