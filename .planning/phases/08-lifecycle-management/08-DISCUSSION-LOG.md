# Phase 08 Discussion Log

## 运行环境部署
**Presented Options:**
- 编写 bat/ps1 安装脚本，自动为用户安装 Python/Node 并拉取依赖（保持源码结构，利于后续热更新代码）。
- 使用 PyInstaller / pkg 打包为免安装的单体 EXE（体积大、打包复杂，但用户无需环境双击即用）。

**User Selected:**
- 编写 bat/ps1 安装脚本，自动为用户安装 Python/Node 并拉取依赖（保持源码结构，利于后续热更新代码）。

**Notes:**
采用脚本化部署以方便后续版本代码热更新，免除重复打包成本。

---

## 版本更新机制
**Presented Options:**
- 增加独立的 "update.bat" 脚本，用户需要更新时手动双击执行（通过 git pull 拉取代码并更新依赖）。
- 应用每次启动时后台检查更新，如果发现新版本则弹窗提示，用户确认后自动执行更新。
- 在 Web UI 面板中增加“检查更新”按钮，点击后由后端触发更新流。

**User Selected:**
- 在 Web UI 面板中增加“检查更新”按钮，点击后由后端触发更新流。

**Notes:**
更新操作将集成到前端界面中，提供更好的用户体验。

---

## 卸载数据保留
**Presented Options:**
- 彻底清理所有内容（包括配置文件、API Key 等），不留残余。
- 保留配置目录（如 `.env`），只删除运行代码和环境，方便下次重装复用。

**User Selected:**
- 彻底清理所有内容（包括配置文件、API Key 等），不留残余。

**Notes:**
实现无痕卸载。

---

## 快捷方式放置
**Presented Options:**
- 仅在桌面生成快捷方式。
- 同时在桌面和开始菜单生成快捷方式。

**User Selected:**
- 仅在桌面生成快捷方式。

**Notes:**
保持简洁。
