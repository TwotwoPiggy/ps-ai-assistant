import json
from backend.engines import COMEngine
from backend.tools import ps_tools

engine = COMEngine()
ctx = engine.ctx

ps_tools.create_layer(ctx, name='TestEmpty3')
jsx_code = """
var layer = app.activeDocument.activeLayer;
if (layer.kind != LayerKind.SMARTOBJECT) {
    var isEmpty = false;
    try {
        var bounds = layer.bounds;
        var w = bounds[2].value - bounds[0].value;
        var h = bounds[3].value - bounds[1].value;
        if (w <= 0 || h <= 0) { isEmpty = true; }
    } catch(e) {
        isEmpty = true;
    }
    if (isEmpty) {
        throw new Error("EMPTY_LAYER_BOUNDS");
    }
    executeAction(stringIDToTypeID("newPlacedLayer"), undefined, DialogModes.NO);
}
"""
res = ps_tools.execute_jsx(ctx, jsx_code)
print("JSX Result:", res)
