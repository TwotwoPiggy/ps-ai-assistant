import { batchPlayTools } from './batchPlayTools';
declare const require: any;

const photoshop = (() => {
  try {
    return require('photoshop');
  } catch (e) {
    return null;
  }
})();

const uxp = (() => {
  try {
    return require('uxp');
  } catch (e) {
    return null;
  }
})();

function getActiveDocument() {
  if (!photoshop) {
    throw new Error("非 Photoshop UXP 运行环境，无法操作文档。");
  }
  const app = photoshop.app;
  if (!app.activeDocument) {
    throw new Error("当前 Photoshop 中没有打开的文档，请先创建或打开一个文档。");
  }
  return app.activeDocument;
}

function findLayerById(layers: any[], id: string): any {
  for (const layer of layers) {
    if (layer.id.toString() === id) {
      return layer;
    }
    if (layer.kind === "group" && layer.layers) {
      const found = findLayerById(layer.layers, id);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

/**
 * UXP 插件内实现的 11 个核心 Photoshop 工具函数
 */
export const uxpTools: Record<string, (args: any) => Promise<any> | any> = {
  // 1. 获取图层树
  get_layer_tree: async () => {
    const doc = getActiveDocument();
    
    function traverse(layers: any[]): any[] {
      return layers.map(layer => {
        const node: any = {
          id: layer.id.toString(),
          name: layer.name,
          type: layer.kind === "group" ? "LayerSet" : "ArtLayer",
          visible: layer.visible,
          opacity: layer.opacity || 100.0
        };
        if (layer.kind === "group") {
          node.children = traverse(layer.layers || []);
        }
        return node;
      });
    }

    const layers = traverse(doc.layers || []);
    return { success: true, layers };
  },

  // 2. 获取画布快照截图
  get_canvas_snapshot: async () => {
    if (!uxp) {
      throw new Error("Storage API 仅在 UXP 环境中可用");
    }
    const doc = getActiveDocument();
    const tempFolder = await uxp.storage.localFileSystem.getTemporaryFolder();
    const tempFile = await tempFolder.createFile(`ps_snap_${Date.now()}.jpg`, { overwrite: true });

    try {
      // 另存为 JPEG 副本
      await doc.saveAs.jpeg(tempFile, { quality: 6 }, true);

      // 读取为 ArrayBuffer
      const arrayBuffer = await tempFile.read({ format: uxp.storage.formats.binary });
      
      // 转换为 Base64
      let binary = '';
      const bytes = new Uint8Array(arrayBuffer);
      const len = bytes.byteLength;
      for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64 = btoa(binary);

      return {
        success: true,
        imageBase64: base64,
        width: doc.width,
        height: doc.height
      };
    } finally {
      try {
        await tempFile.delete();
      } catch (e) {
        // 忽略删除报错
      }
    }
  },

  // 3. 创建图层
  create_layer: async (args: { name: string; opacity?: number; above?: string }) => {
    const doc = getActiveDocument();
    const { name, opacity = 100.0, above } = args;

    // 创建普通图层
    const newLayer = await doc.createLayer({ name });
    if (newLayer) {
      newLayer.opacity = opacity;
      
      // 如果指定了在哪个图层上方
      if (above) {
        const target = findLayerById(doc.layers, above);
        if (target) {
          const { ElementPlacement } = photoshop.app.constants;
          await newLayer.move(target, ElementPlacement.PLACEBEFORE);
        }
      }
      return { success: true, message: `成功创建图层 '${name}'` };
    }
    return { success: false, error: "创建图层失败" };
  },

  // 4. 删除图层
  delete_layer: async (args: { layer_identify: string }) => {
    const doc = getActiveDocument();
    const { layer_identify } = args;
    const layer = findLayerById(doc.layers, layer_identify);
    if (!layer) {
      return { success: false, error: `未找到 ID 为 ${layer_identify} 的图层` };
    }
    const layerName = layer.name;
    await layer.delete();
    return { success: true, message: `成功删除图层 '${layerName}'` };
  },

  // 5. 重命名图层
  rename_layer: async (args: { layer_identify: string; new_name: string }) => {
    const doc = getActiveDocument();
    const { layer_identify, new_name } = args;
    const layer = findLayerById(doc.layers, layer_identify);
    if (!layer) {
      return { success: false, error: `未找到 ID 为 ${layer_identify} 的图层` };
    }
    const oldName = layer.name;
    layer.name = new_name;
    return { success: true, message: `已将图层 '${oldName}' 重命名为 '${new_name}'` };
  },

  // 6. 设置图层可见性
  set_layer_visibility: async (args: { layer_identify: string; visible: boolean }) => {
    const doc = getActiveDocument();
    const { layer_identify, visible } = args;
    const layer = findLayerById(doc.layers, layer_identify);
    if (!layer) {
      return { success: false, error: `未找到 ID 为 ${layer_identify} 的图层` };
    }
    layer.visible = visible;
    const state = visible ? "显示" : "隐藏";
    return { success: true, message: `已将图层 '${layer.name}' 设置为${state}` };
  },

  // 7. 移动图层顺序
  reorder_layer: async (args: { layer_identify: string; target_identify: string; placement: string }) => {
    const doc = getActiveDocument();
    const { layer_identify, target_identify, placement } = args;

    const layer = findLayerById(doc.layers, layer_identify);
    const target = findLayerById(doc.layers, target_identify);
    if (!layer || !target) {
      return { success: false, error: "未找到移动源图层或参照目标图层" };
    }

    const { ElementPlacement } = photoshop.app.constants;
    let uxpPlacement = ElementPlacement.PLACEBEFORE;
    if (placement === "placeAfter") {
      uxpPlacement = ElementPlacement.PLACEAFTER;
    } else if (placement === "placeInside") {
      uxpPlacement = ElementPlacement.PLACEINSIDE;
    }

    await layer.move(target, uxpPlacement);
    return { success: true, message: `已将图层 '${layer.name}' 移至 '${target.name}' 的 ${placement} 位置` };
  },

  // 8. 调整亮度和对比度
  adjust_brightness_contrast: async (args: { brightness: number; contrast: number; layer_identify?: string }) => {
    const doc = getActiveDocument();
    const { brightness, contrast, layer_identify } = args;

    let layer = doc.activeLayers[0];
    if (layer_identify) {
      layer = findLayerById(doc.layers, layer_identify);
    }
    if (!layer) {
      return { success: false, error: "未找到指定的图层" };
    }

    if (layer.kind === "group") {
      return { success: false, error: "无法在图层组上调整亮度对比度，必须是带图像的图层" };
    }

    // UXP DOM v2 调整亮度和对比度
    await layer.adjustBrightnessContrast(brightness, contrast);
    return { success: true, message: `成功将图层 '${layer.name}' 的亮度调整为 ${brightness}，对比度调整为 ${contrast}` };
  },

  // 9. 裁剪画布
  crop_canvas: async (args: { top: number; left: number; bottom: number; right: number }) => {
    const doc = getActiveDocument();
    const { top, left, bottom, right } = args;

    await doc.crop([left, top, right, bottom]);
    return { success: true, message: `画布成功裁剪至区域: left=${left}, top=${top}, right=${right}, bottom=${bottom}` };
  },

  // 10. 调整画布大小
  resize_canvas: async (args: { width: number; height: number; anchor?: string }) => {
    const doc = getActiveDocument();
    const { width, height, anchor = 'middleCenter' } = args;

    const { AnchorPosition } = photoshop.app.constants;
    const anchorMap: Record<string, any> = {
      'topLeft': AnchorPosition.TOPLEFT,
      'topCenter': AnchorPosition.TOPCENTER, 'top': AnchorPosition.TOPCENTER,
      'topRight': AnchorPosition.TOPRIGHT,
      'leftCenter': AnchorPosition.LEFTCENTER, 'left': AnchorPosition.LEFTCENTER,
      'middleCenter': AnchorPosition.MIDDLECENTER, 'center': AnchorPosition.MIDDLECENTER,
      'rightCenter': AnchorPosition.RIGHTCENTER, 'right': AnchorPosition.RIGHTCENTER,
      'bottomLeft': AnchorPosition.BOTTOMLEFT,
      'bottomCenter': AnchorPosition.BOTTOMCENTER, 'bottom': AnchorPosition.BOTTOMCENTER,
      'bottomRight': AnchorPosition.BOTTOMRIGHT
    };

    const uxpAnchor = anchorMap[anchor] || AnchorPosition.MIDDLECENTER;
    await doc.resizeCanvas(width, height, uxpAnchor);
    return { success: true, message: `画布尺寸已成功调整为 ${width}x${height}` };
  },

  // 11. 翻转图像
  flip_image: async (args: { direction: string }) => {
    const doc = getActiveDocument();
    const { direction } = args;

    const { Direction } = photoshop.app.constants;
    const uxpDirection = direction === "horizontal" ? Direction.HORIZONTAL : Direction.VERTICAL;

    await doc.flipCanvas(uxpDirection);
    return { success: true, message: `画布已成功进行了 ${direction} 翻转` };
  }
};

/**
 * 分发执行 UXP 插件指令
 */
export async function executeUXPTool(name: string, args: any): Promise<any> {
  const isBatchPlay = args._use_batchplay === true;
  let tool = uxpTools[name];
  
  if (isBatchPlay && batchPlayTools[name]) {
    tool = batchPlayTools[name];
  }

  if (!tool) {
    return { success: false, error: `UXP 插件中找不到工具函数 '${name}'` };
  }

  try {
    return await tool(args);
  } catch (err: any) {
    if (isBatchPlay && err.message && err.message.includes('fallback:')) {
      if (uxpTools[name]) {
        console.warn(`[PS-AI UXP] 工具 ${name} batchPlay 方案不可用，回退至 DOM API`);
        return await uxpTools[name](args);
      }
    }
    return { success: false, error: err.message || err.toString() };
  }
}
