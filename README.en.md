# Photoshop AI Assistant

<span>**English** | [中文](README.md)</span>

Control Adobe Photoshop with natural language — an intelligent PS operation assistant powered by Gemini AI.

Have AI manipulate Photoshop directly through conversation, handling common operations like layer management and canvas editing.

## System Requirements

- **Operating System**: Windows (requires COM interface to control Photoshop)
- **Python**: 3.10+
- **Adobe Photoshop**: Installed and runnable
- **API Key**: At least one supported AI model API Key required (supports Gemini, DeepSeek, Qwen, or OpenAI-compatible custom endpoints).
  - *Note: The selected model must support both **Function Calling** and **multimodal image input** (for canvas snapshot analysis, e.g. `gemini-3.1-flash-lite`, `mimo-v2.5`, etc.).*

## Installation

```bash
# Clone the project
git clone <repo-url>
cd ps-ai-assistant

# Install Python dependencies
pip install -r backend/requirements.txt

# (Optional) Install launcher tray dependencies — enable system tray icon
pip install -r requirements-launcher.txt
```

## Usage

### One-Click Launch (Recommended)

Two launch options available:

**① `start.bat` — with console window**: Double-click to open a cmd window showing real-time logs, with a tray icon displayed. Useful for observing startup logs or troubleshooting.

**② `start_silent.vbs` — fully silent (recommended for daily use)**: Double-click and **no window appears** — only the tray icon runs in background. Cleaner desktop for everyday use.

For first use, it's recommended to install the tray dependency (optional; if missing, it automatically falls back to pure background process, but you won't be able to exit through the tray and need to use Task Manager):

```bash
pip install -r requirements-launcher.txt
```

Startup arguments (for `start.bat`, or directly calling `python launcher.py`):

| Argument | Description |
|----------|-------------|
| (none) | Production mode: only starts backend, uses pre-built `frontend/dist` |
| `--dev` | Development mode: starts both backend + Vite dev server (hot reload) |
| `--no-tray` | No tray icon, runs in CLI only |
| `--no-browser` | Does not auto-open browser after startup |
| `--port <port>` | Specify backend port (default 18919; not recommended to change in production due to frontend hardcoding) |

Examples:
```bash
start.bat --dev          REM Development mode
start.bat --no-browser   REM Don't auto-open browser
python launcher.py --dev --no-tray
```

The launcher includes these automation capabilities:
- **Environment pre-check**: Python / Node versions; auto-installs missing key dependencies
- **Port detection**: Automatically finds an available port if 18919 is occupied (dev mode)
- **Log persistence**: All output written to `logs/launcher.log` for troubleshooting

#### System Tray Menu

After startup, a PS icon appears in the bottom-right tray. Hover shows running status (`Running :18919` or `Stopped`). Right-click menu:

| Menu Item | Description |
|-----------|-------------|
| **Open Browser** (double-click icon also works) | Opens the app page in default browser |
| **Stop Service / Start Service** | Dynamic toggle: "Stop Service" when running, "Start Service" when stopped — useful for temporarily releasing ports or pausing |
| **Restart Service** | Stop and relaunch, applies config changes |
| **View Logs** | Opens `logs/launcher.log` in Notepad |
| **Exit** | Stops all sub-processes and exits the launcher |

> Note: In production mode, port is fixed to 18919 (hardcoded in `socket.ts` on the frontend). Changing ports will cause frontend to fail connecting to backend.

---

### Command Line Launch (Manual)

If you don't want to use the launcher, run directly:

```bash
python -m backend.server
```

Server runs by default at `http://localhost:18919`.

### Configuring API Key

This project supports multiple LLM providers (Gemini, DeepSeek, Qwen, etc.). Two ways to configure API Keys:

1. **Frontend config panel** (recommended): After starting the server, click the settings button in the top-right corner of the frontend UI. In the settings panel, select your desired LLM provider, enter the corresponding API Key and save. For custom models, you can also configure Base URL and model name.

2. **Environment variables**:
   For different models, set the corresponding environment variable before startup:
   - Gemini: `GEMINI_API_KEY`
   - DeepSeek: `DEEPSEEK_API_KEY`
   - Qwen: `DASHSCOPE_API_KEY`

   Example:
   ```bash
   set DEEPSEEK_API_KEY=your-api-key-here
   python -m backend.server
   ```

### Using the AI Assistant

After starting the server and configuring your API Key, send natural language instructions through the frontend chat interface. The AI will automatically invoke the powerful Photoshop interface capabilities below based on your intent.

## Supported Operations & Example Prompts

We've integrated dozens of native Photoshop control interfaces into the AI, covering layers, selections, color correction, filters, and AI generation.

### 1. Basic Operations & Canvas Management
| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| **Get Layer Tree** | View complete layer structure of current document | `"What layers are there?"` |
| **Get Canvas Snapshot** | Capture current image for AI visual analysis | `"What do you think of the current composition?"` |
| **Create/Delete Layer** | Create or delete specified layer | `"Create a new layer called 'Effects'"`, `"Delete empty layers"` |
| **Modify Layer Properties** | Adjust name, visibility, ordering, opacity | `"Hide background layer"`, `"Move text layer to top"` |
| **Crop/Resize Canvas** | Crop or change canvas/image size | `"Crop 100 pixels from the right"`, `"Resize canvas to 1920x1080"` |
| **Flip Canvas** | Flip entire document horizontally or vertically | `"Flip canvas horizontally"` |

### 2. Selection & Mask Control
| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| **Basic Selection** | Create rectangular, elliptical selections; select all / deselect | `"Draw a 500x500 rectangular selection in the middle"` |
| **Smart Selection** | Smart subject/sky selection | `"Cut out the person in the image"` |
| **Refine Selection** | Feather, expand, contract, smooth, inverse | `"Feather current selection by 20 pixels"`, `"Inverse selection"` |
| **Layer Mask** | Add, delete, enable or disable masks | `"Add a mask to current layer"`, `"Disable this mask temporarily"` |
| **Channel Conversion** | Save selection to channel or load from channel | `"Save this selection as a channel"` |

### 3. Professional Color Correction & Lighting
| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| **Exposure Adjustment** | Adjust brightness/contrast, Levels | `"Image is too dark, increase brightness"`, `"Adjust levels"` |
| **Color Adjustment** | Hue/Saturation, Color Balance, Black & White | `"Convert this to black and white"`, `"Increase saturation by 10%"` |
| **Non-destructive Adjustment Layer** | Create independent adjustment layer with color properties | `"Create an adjustment layer and slightly lower contrast"` |
| **Color Palette Control** | Set foreground/background color | `"Set foreground color to red"` |
| **Image Fill** | Solid color fill, Content-Aware Fill | `"Use content-aware fill to remove the person in the selection"` |

### 4. Advanced Filters & Portrait Retouching
| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| **Blur & Sharpen** | Gaussian Blur, Surface Blur, Unsharp Mask | `"Gaussian blur the background"`, `"Sharpen this image slightly"` |
| **Smart Liquify** | Automatically convert to Smart Object and invoke non-destructive Liquify | `"I want to slim the face, open the Liquify panel"` |
| **Camera Raw** | Read and inject external XMP film presets | `"Apply this film-style Camera Raw preset"` |
| **Neural Filters** | Invoke official Neural Filters AI panel | `"Open Neural Filters, I want to use Smart Portrait"` |
| **Commercial Skin Retouching Macro** | Auto-execute high-low frequency separation, create skin retouching layer | `"This is a portrait, run the commercial skin retouching flow"` |
| **Generative Fill** | Call Adobe Firefly for AI image generation | `"Generate a hand-drawn style golden lucky cat in this selection"` |

### 5. Automation & Action Integration
| Operation | Description | Example Prompt |
|-----------|-------------|----------------|
| **Action Execution** | Invoke PS recorded actions by action name and action set | `"Run an action called 'Woodcut'"` |
| **External Script Execution** | Load and run local whitelisted extension JSX scripts | `"Run test.jsx from the resources directory"` |
| **Web Slice Export** | Auto-slice current canvas and save to desktop | `"Save current canvas as PNG slices to desktop"` |

## Project Structure

```
ps-ai-assistant/
├── backend/
│   ├── __init__.py          # Package entry
│   ├── agent.py             # Photoshop AI Agent (Gemini + COM tools)
│   ├── config.py            # API Key config management
│   ├── server.py            # FastAPI + Socket.IO server
│   ├── requirements.txt     # Python dependencies
│   └── store/               # Runtime config storage (gitignored)
├── frontend/                # Frontend UI (React + Vite)
├── launcher.py              # Service launcher (env check / tray / dual mode)
├── start.bat                # Windows launch entry (with console)
├── start_silent.vbs         # Windows silent launch entry (no window, tray only)
├── requirements-launcher.txt # Optional launcher dependencies (tray icon)
├── logs/                    # Launcher logs (gitignored)
├── .gitignore
└── README.md
```

## Tech Stack

- **AI Model**: Google Gemini / DeepSeek / Qwen (Function Calling)
- **Backend**: FastAPI + python-socketio + uvicorn
- **PS Control**: pywin32 COM interface
- **Communication Protocol**: Socket.IO (WebSocket)

## License

MIT
