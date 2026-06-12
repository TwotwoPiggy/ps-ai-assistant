# Coding Conventions

*Last updated: 2026-06-12*

## General
- **Language**: Python for backend, TypeScript for frontend.
- **Naming**: `snake_case` for Python functions and variables, `PascalCase` for React components.

## Error Handling
- Backend tool functions (in `agent.py`) catch exceptions and return dictionaries formatted as `{"success": False, "error": str(e)}`. This allows Gemini to know if a tool call failed.

## Gemini Integration
- Tools are defined as standard Python methods in `PhotoshopAgent`.
- Gemini responses are parsed for function calls. Tool results are appended to the conversation history as user role content containing function response parts.
- Large base64 images are cleaned from the history to save tokens.
