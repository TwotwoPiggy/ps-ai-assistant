from backend.engines import COMEngine
from backend.tools import ps_tools

engine = COMEngine()
ctx = engine.ctx
doc = ctx.get_doc()

ps_tools.create_layer(ctx, name='TestEmpty4')
layer = doc.ArtLayers["TestEmpty4"]

bounds = layer.Bounds
print("Bounds:", bounds)
w = bounds[2] - bounds[0]
h = bounds[3] - bounds[1]
print("W:", w, "H:", h)
