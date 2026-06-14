# Phase 07: 自动化与动作集成 (Automation & Actions) Research

## Technical Approach for Each Requirement

### AUTO-01: Execute Recorded Actions (`play_action`)
**Goal**: Allow the AI to directly trigger Photoshop Actions by name and set.
**Technical Approach**:
- Use `ActionManager` via ExtendScript, executed through our existing `execute_jsx` bridge.
- **JSX Snippet**:
  ```javascript
  (function() {
      var idPlay = charIDToTypeID( "Ply " );
      var desc = new ActionDescriptor();
      var idnull = charIDToTypeID( "null" );
      var ref = new ActionReference();
      ref.putName( charIDToTypeID( "Actn" ), "{action_name}" );
      ref.putName( charIDToTypeID( "ASet" ), "{action_set_name}" );
      desc.putReference( idnull, ref );
      // DialogModes.ALL respects D-02: allowing the action's native dialogs to pop up
      try {
          executeAction( idPlay, desc, DialogModes.ALL );
          return "success";
      } catch(e) {
          return "ERROR: " + e.message;
      }
  })();
  ```
- **Rationale**: `DialogModes.ALL` satisfies decision D-02 (状态指引 + 允许挂起). Like `apply_liquify` in Phase 06, we will print a status message before calling this blocking tool to guide the user to interact with any popups.

### AUTO-02: Execute Local JSX Scripts (`run_local_jsx`)
**Goal**: Execute arbitrary local `.jsx` scripts with a security authorization flow.
**Technical Approach**:
- Create a Python tool `run_local_jsx(ctx, file_path, confirmed=False)`.
- **Path Whitelist**: It automatically allows paths inside `backend/resources/scripts/`.
- **Authorization Flow (D-01)**: 
  If the path is outside the whitelist and `confirmed` is False, the tool returns `{"success": False, "requires_confirmation": True, "path": file_path}`.
  We will modify the async `COMEngine.execute_tool` in `backend/engines.py` to intercept this specific return value. It will then use `sio.call('request_auth', ...)` to block and prompt the frontend. If the user clicks "Allow", it recursively calls the tool with `confirmed=True`.
- **Execution**: Python reads the `.jsx` file via standard file I/O and passes the raw text to `ps_tools.execute_jsx(ctx, jsx_code)`.

### AUTO-03: Slice Export API (`export_for_web`)
**Goal**: Automatically export web formats respecting document slices.
**Technical Approach**:
- The standard COM `doc.Export()` doesn't granularly support slices. We must use `ActionManager` to trigger "Save for Web (Legacy)".
- **JSX Snippet**:
  ```javascript
  (function() {
      var idEpt = charIDToTypeID( "Ept " );
      var desc = new ActionDescriptor();
      var opt = new ActionDescriptor();
      opt.putEnumerated( charIDToTypeID( "Op  " ), charIDToTypeID( "SWOp" ), charIDToTypeID( "OpSa" ) );
      // Format switch: PN24 / PNG8 / JPEG
      opt.putEnumerated( charIDToTypeID( "Fmt " ), charIDToTypeID( "IRFm" ), charIDToTypeID( "{fmt_code}" ) );
      opt.putBoolean( charIDToTypeID( "Trns" ), true );
      // Slice switch: SLUs (User Slices) / SLAl (All Slices)
      opt.putEnumerated( charIDToTypeID( "SWsl" ), charIDToTypeID( "STsl" ), charIDToTypeID( "{slice_code}" ) );
      desc.putObject( charIDToTypeID( "Usng" ), charIDToTypeID( "SvFW" ), opt );
      desc.putPath( charIDToTypeID( "In  " ), new File( "{safe_path}" ) );
      try {
          executeAction( idEpt, desc, DialogModes.NO );
          return "success";
      } catch(e) {
          return "ERROR: " + e.message;
      }
  })();
  ```
- **Rationale**: Using ActionManager allows us to specify whether to export `SLUs` (User Slices) or `SLAl` (All Slices). The tool will intelligently default to the user's desktop with an auto-generated timestamp filename (Decision D-03).

## Existing Patterns to Reuse
- **`execute_jsx` Bridge**: Core foundation in `ps_tools.py` that we will reuse for ActionManager dispatches.
- **State UI Prompt in Agent**: In Phase 06 (`apply_liquify`), the pattern of printing a status before blocking COM calls was established. We will use this same pattern for `play_action`.
- **Tool Registration**: All new functions will be added to `registry.py` and fully typed to ensure OpenAI schema extraction works automatically.
- **Desktop Fallback Path**: `save_document` tool logic uses `os.path.expanduser("~/Desktop")` which we will borrow for the default `export_for_web` path.

## Potential Landmines & Error Handling Strategies
- **Path Escaping in JSX**: Windows file paths use backslashes `\`. When injecting these into JSX strings (e.g. `new File("...")`), they must be replaced with forward slashes `/` or double-escaped, otherwise the script will fail silently.
- **Action Not Found**: If an action name or set name does not exist, the ActionManager will throw an exception. We must wrap the JSX in a `try/catch` and return a descriptive `ERROR: Action/Set not found` string to Python so the LLM can recover gracefully.
- **Frontend Timeout**: The Socket.IO `request_auth` call needs a timeout (e.g., 60 seconds). If the user steps away, it shouldn't freeze the AI Engine indefinitely. A timeout exception will simply cancel the tool execution.
- **Save for Web 8192px Limit**: Photoshop's legacy Save for Web module has a hard limit of 8192px per side. The Python tool should check `doc.Width` / `doc.Height` before exporting and return an error to the LLM if it exceeds the limit, preventing a COM crash.

## Validation Architecture
This section outlines how the implementation of these APIs will be verified programmatically and manually during the verification phase.

1. **AUTO-01 (Actions) Validation**:
   - **Strategy**: Programmatically assert that calling a deliberately non-existent action (e.g., Action="NonExistent", Set="FakeSet") is successfully caught by our `try/catch` wrapper and returns `{"success": False, "error": "..."}` rather than crashing the COM engine.
2. **AUTO-02 (Local JSX) Validation**:
   - **Strategy**: Create a temporary dummy `.jsx` file within the safe `backend/resources/scripts/` directory and assert it executes without requesting confirmation.
   - **Strategy**: Create a dummy `.jsx` file in `tempfile.gettempdir()` (unsafe) and call `run_local_jsx` with `confirmed=False`. Assert that the return dictionary strictly contains `requires_confirmation: True`.
3. **AUTO-03 (Slice Export) Validation**:
   - **Strategy**: Create a new document with specific dimensions, and invoke `export_for_web(..., export_path=temp_dir)`. Assert via `os.path.exists()` that the exported output file(s) are actually written to the disk in the specified format.
