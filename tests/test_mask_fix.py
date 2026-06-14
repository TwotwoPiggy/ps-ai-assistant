import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.engines import COMEngine
from backend.tools import ps_tools

engine = COMEngine()
ctx = engine.ctx

ps_tools.create_document(ctx, 800, 600)
ps_tools.create_layer(ctx, "MaskTest")
ps_tools.basic_selection(ctx, "rect", [100, 100, 200, 200])

jsx = """
var idMk = charIDToTypeID( "Mk  " );
var desc2 = new ActionDescriptor();
desc2.putClass( charIDToTypeID( "Nw  " ), charIDToTypeID( "Chnl" ) );
var ref1 = new ActionReference();
ref1.putEnumerated( charIDToTypeID( "Chnl" ), charIDToTypeID( "Chnl" ), charIDToTypeID( "Msk " ) );
desc2.putReference( charIDToTypeID( "At  " ), ref1 );
desc2.putEnumerated( charIDToTypeID( "Usng" ), charIDToTypeID( "UsrM" ), charIDToTypeID( "RvlS" ) );
executeAction( idMk, desc2, DialogModes.NO );
"""
res = ps_tools.execute_jsx(ctx, jsx)
print('Make Mask:', res)
