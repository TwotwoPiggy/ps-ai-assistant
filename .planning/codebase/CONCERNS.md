# Concerns & Tech Debt

*Last updated: 2026-06-12*

## Platform Dependency
- Hard dependency on Windows OS due to `pywin32`. Cannot be easily mocked or run on macOS/Linux.

## AI / Token Limits
- Large Base64 images are sent to Gemini for visual understanding (`get_canvas_snapshot`). The agent implements a cleanup routine to remove old Base64 images from history to prevent token exhaustion, but heavy visual usage may still consume tokens rapidly.

## Error Recovery
- The agent implements basic retry logic for 429 and 503 errors from the Gemini API, but deep nested function call failures or Photoshop COM hanging might require application restarts.

## Security
- API keys are stored locally.
- WebSockets accept all CORS origins (`cors_allowed_origins="*"`), which is acceptable for a local tool but should be locked down if exposed.
