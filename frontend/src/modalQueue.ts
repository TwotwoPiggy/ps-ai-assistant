declare const require: any;

const photoshop = (() => {
  try {
    return require('photoshop');
  } catch (e) {
    return null;
  }
})();

type Task = () => Promise<any>;

class ModalQueue {
  private queue: Task[] = [];
  private isProcessing = false;

  /**
   * 将一个 Photoshop 操作排入队列并在 executeAsModal 中串行执行
   * 
   * @param action 要在 modal 下执行的操作
   * @param commandName 给 Photoshop 记录历史步骤的动作名称
   */
  async enqueue<T>(action: (context: any) => Promise<T> | T, commandName: string): Promise<T> {
    if (!photoshop || !photoshop.core || !photoshop.core.executeAsModal) {
      // 浏览器非 UXP 调试环境直接执行
      return await action(null);
    }

    return new Promise<T>((resolve, reject) => {
      const task = async () => {
        try {
          const result = await photoshop.core.executeAsModal(async (context: any) => {
            return await action(context);
          }, {
            commandName: commandName
          });
          resolve(result);
        } catch (error) {
          reject(error);
        }
      };

      this.queue.push(task);
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.isProcessing) return;
    this.isProcessing = true;

    while (this.queue.length > 0) {
      const task = this.queue.shift();
      if (task) {
        try {
          await task();
        } catch (e) {
          console.error("[ModalQueue] 任务执行报错:", e);
        }
      }
    }

    this.isProcessing = false;
  }
}

export const modalQueue = new ModalQueue();
