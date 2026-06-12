# Architecture

*Last updated: 2026-06-12*

## System Design
The system follows a client-server architecture using WebSocket for real-time interaction.

## Components
1. **Frontend (React + Vite)**: Provides a chat-like interface. Communicates with the backend via Socket.IO.
2. **Backend Server (`backend/server.py`)**: Uses FastAPI and python-socketio to handle WebSocket connections and serve static frontend files.
3. **AI Agent (`backend/agent.py`)**: Wraps the Gemini API. Exposes Photoshop operations as function-calling tools to the AI.
4. **Photoshop Application**: The local instance of Photoshop being controlled via COM interface.

## Data Flow
1. User sends a natural language message from the frontend.
2. `server.py` receives the message via `ai_chat` event and passes it to `PhotoshopAgent`.
3. `PhotoshopAgent` appends the message to the conversation history and sends it to the Gemini model.
4. Gemini decides to call tools (e.g., `create_layer`, `get_canvas_snapshot`).
5. `PhotoshopAgent` executes the Python functions which invoke Photoshop COM methods.
6. Execution results are returned to Gemini.
7. Gemini generates the final response, which is sent back to the frontend via Socket.IO.
