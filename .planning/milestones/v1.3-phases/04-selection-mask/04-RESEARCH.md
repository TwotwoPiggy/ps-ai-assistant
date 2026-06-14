# Phase 04 Research: 选区与蒙版控制 (Selection & Mask)

## What I need to know to PLAN this phase well

1. **How `execute_jsx` is used**: The backend currently has `ps_tools.execute_jsx(ctx, jsx_code)`. Complex operations that cannot be done directly via DOM (like `Select Subject` or complex mask operations) will generate JSX strings internally and execute them.
2. **DOM Selection Capabilities**: Basic selection (Rectangle, Ellipse) can be done via `doc.Selection.Select(Array, Type, Feather, AntiAlias)`.
   The `selection_mode` (`replace`, `add`, `subtract`, `intersect`) maps to:
   - `replace`: `1` (psReplaceSelection)
   - `add`: `2` (psExtendSelection)
   - `subtract`: `3` (psDiminishSelection)
   - `intersect`: `4` (psIntersectSelection)
3. **Smart Selection (AI)**: `Select Subject` and `Remove Background` require ExtendScript (ActionManager) because DOM doesn't have `SelectSubject` directly in older versions, and even if it does, `ActionDescriptor` is more robust.
   JSX for Select Subject:
   ```javascript
   var idautoCutout = stringIDToTypeID( "autoCutout" );
   var desc = new ActionDescriptor();
   var idsampleAllLayers = stringIDToTypeID( "sampleAllLayers" );
   desc.putBoolean( idsampleAllLayers, false );
   executeAction( idautoCutout, desc, DialogModes.NO );
   ```
4. **Mask Operations**: Add Mask requires ActionManager.
5. **Channel Operations**: `doc.Channels.Add()`, `doc.Selection.Store(channel)`.

## Known Constraints
- When a smart selection fails, it throws an ActionManager error. We must wrap the `execute_jsx` call in a `try...except` and return a clean error like `{"success": False, "error": "AI 选择主体超时或未找到主体"}`.
- `force_apply` boolean is required for `apply_mask` to prevent accidental destructive actions.
