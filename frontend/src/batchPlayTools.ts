declare const require: any;

const photoshop = (() => {
  try {
    return require('photoshop');
  } catch (e) {
    return null;
  }
})();

export const batchPlayTools: Record<string, (args: any) => Promise<any> | any> = {
  get_layer_tree: async (_args) => {
    throw new Error("fallback: get_layer_tree no batchPlay implementation");
  },

  get_canvas_snapshot: async (_args) => {
    throw new Error("fallback: get_canvas_snapshot no batchPlay implementation");
  },

  create_layer: async (args) => {
    const { name, opacity = 100.0 } = args;
    await photoshop.action.batchPlay([{
      "_obj": "make",
      "_target": [{"_ref": "layer"}],
      "using": {
        "_obj": "layer",
        "name": name,
        "opacity": { "_unit": "percentUnit", "_value": opacity }
      }
    }], {});
    return { success: true, message: `[batchPlay] 成功创建图层 '${name}'` };
  },

  delete_layer: async (args) => {
    const { layer_identify } = args;
    await photoshop.action.batchPlay([{
      "_obj": "delete",
      "_target": [{"_ref": "layer", "_id": parseInt(layer_identify)}]
    }], {});
    return { success: true, message: `[batchPlay] 成功删除图层 ${layer_identify}` };
  },

  rename_layer: async (args) => {
    const { layer_identify, new_name } = args;
    await photoshop.action.batchPlay([{
      "_obj": "set",
      "_target": [{"_ref": "layer", "_id": parseInt(layer_identify)}],
      "to": { "_obj": "layer", "name": new_name }
    }], {});
    return { success: true, message: `[batchPlay] 已将图层重命名为 '${new_name}'` };
  },

  set_layer_visibility: async (args) => {
    const { layer_identify, visible } = args;
    await photoshop.action.batchPlay([{
      "_obj": visible ? "show" : "hide",
      "_target": [{"_ref": "layer", "_id": parseInt(layer_identify)}]
    }], {});
    return { success: true, message: `[batchPlay] 已将图层可见性设置为 ${visible}` };
  },

  reorder_layer: async (_args) => {
    // placeholder for now
    throw new Error("fallback: reorder_layer batchPlay implementation incomplete");
  },

  adjust_brightness_contrast: async (args) => {
    const { brightness, contrast } = args;
    await photoshop.action.batchPlay([{
      "_obj": "brightnessEvent",
      "brightness": brightness,
      "contrast": contrast
    }], {});
    return { success: true, message: `[batchPlay] 成功调整亮度 ${brightness} 对比度 ${contrast}` };
  },

  crop_canvas: async (args) => {
    const { top, left, bottom, right } = args;
    await photoshop.action.batchPlay([{
      "_obj": "crop",
      "to": {
        "_obj": "rectangle",
        "top": { "_unit": "pixelsUnit", "_value": top },
        "left": { "_unit": "pixelsUnit", "_value": left },
        "bottom": { "_unit": "pixelsUnit", "_value": bottom },
        "right": { "_unit": "pixelsUnit", "_value": right }
      }
    }], {});
    return { success: true, message: `[batchPlay] 成功裁剪画布` };
  },

  resize_canvas: async (args) => {
    const { width, height } = args;
    await photoshop.action.batchPlay([{
      "_obj": "canvasSize",
      "width": { "_unit": "pixelsUnit", "_value": width },
      "height": { "_unit": "pixelsUnit", "_value": height }
    }], {});
    return { success: true, message: `[batchPlay] 画布尺寸调整为 ${width}x${height}` };
  },

  flip_image: async (args) => {
    const { direction } = args;
    const axis = direction === "horizontal" ? "horizontal" : "vertical";
    await photoshop.action.batchPlay([{
      "_obj": "flip",
      "axis": { "_enum": "orientation", "_value": axis }
    }], {});
    return { success: true, message: `[batchPlay] 画布已成功进行了 ${direction} 翻转` };
  }
};
