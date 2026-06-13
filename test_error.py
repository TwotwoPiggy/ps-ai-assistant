import json
from backend.engines import COMEngine
from backend.tools import ps_tools

engine = COMEngine()
ctx = engine.ctx

ps_tools.create_layer(ctx, name='TestEmptyError')
res = ps_tools.execute_jsx(ctx, """
try {
    executeAction(stringIDToTypeID("newPlacedLayer"), undefined, DialogModes.NO);
} catch(e) {
    return e.toString();
}
""")
print("JSX Error:", res)
