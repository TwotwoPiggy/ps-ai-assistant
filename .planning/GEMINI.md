# AI Assistant Global Coding Guidelines (UXP & Python)

This file contains the core "Iron Rules" for the AI when developing or modifying code for the PS AI Assistant project.
Whenever you are writing code for this project, you MUST adhere to these rules strictly.

## UXP Frontend (Photoshop Plugin) Iron Rules

1. **Storage Sandbox Restriction**: 
   UXP cannot access arbitrary OS paths. To share image data or snapshots with the backend, you MUST save to a UXP temporary folder (`fs.getTemporaryFolder()`), convert to Base64, transmit via WebSocket, and then IMMEDIATELY delete the temporary file to prevent disk bloat.
2. **Event Debounce / Throttle**: 
   When listening to high-frequency Photoshop events (e.g., slider adjustments, selection changes) to push to the Python backend, you MUST implement a debounce or throttle mechanism (e.g., 200ms - 500ms). DO NOT emit raw events directly over Socket.IO to avoid event storms and UI lockups.
3. **executeAsModal Serialization**: 
   Any action that modifies the Photoshop document state MUST be wrapped in `require("photoshop").core.executeAsModal()`. Because Photoshop prohibits concurrent modals, you MUST enqueue incoming AI execution requests into a global, sequential **Modal Queue** instead of executing them immediately.
4. **Hybrid API Selection**: 
   Always prioritize the **DOM API v2** (e.g., `app.activeDocument`) for type safety, readability, and modern architecture. Fall back to **batchPlay** (ActionJSON) ONLY when the DOM API lacks the necessary capability or performs unacceptably. Always encapsulate batchPlay logic with clear comments and TypeScript interfaces.
