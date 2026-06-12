# Directory Structure

*Last updated: 2026-06-12*

## Layout

- `backend/` - Python backend code
  - `server.py` - FastAPI application and Socket.IO server setup.
  - `agent.py` - Core AI logic, tool definitions, and Photoshop COM integration.
  - `config.py` - Configuration and API key management.
  - `requirements.txt` - Python dependencies.
  - `store/` - Runtime configuration storage.
- `frontend/` - React frontend code
  - `src/` - React components, socket client setup, and styling.
  - `package.json` - NPM dependencies and scripts.
  - `vite.config.ts` - Vite configuration.
- `README.md` - Project overview and setup instructions.
