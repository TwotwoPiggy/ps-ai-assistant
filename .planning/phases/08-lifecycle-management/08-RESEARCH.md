# Phase 08 Research: 客户端生命周期管理

## 1. Technical Approach for Each Requirement

### 1.1 INST-01: 一键安装流程 (自动配置环境、依赖、快捷方式)
**技术方案：**
1. **统一入口**：提供 `install.bat`，内部检查是否具备管理员权限或直接调用具体的 `scripts/install.ps1` 脚本。
2. **环境检测与静默安装**：
   - **Python**：在 PowerShell 中检测 `python --version`。如不存在，通过 `Invoke-WebRequest` 下载 Python 安装包 (如 3.11)，并使用 `/quiet InstallAllUsers=0 PrependPath=1` 参数进行静默安装。
   - **Node.js**：同理检测 `node -v`，如不存在则下载官方 `.msi` 包，通过 `msiexec /i node_installer.msi /qn` 静默安装。
3. **依赖构建**：
   - 自动在项目根目录运行 `python -m venv .venv` 创建虚拟环境。
   - 调用预先存在的 `launcher.py` 逻辑。`launcher.py` 本身已经具备了自动检测和安装 `backend/requirements.txt` 及前端 `npm install / npm run build` 的能力，因此安装脚本只需成功配置好 Python 和 Node，直接启动一次 `python launcher.py --build-only` 即可完成全部初始化。
4. **快捷方式创建**：
   - 使用 PowerShell 的 `WScript.Shell` COM 对象，在 `$env:USERPROFILE\Desktop` 路径下生成 `PS AI Assistant.lnk`。
   - 快捷方式的 TargetPath 指向项目根目录下的 `start_silent.vbs`（目前已在项目中，用于无黑框启动），并可为快捷方式指定 `.ico` 图标。

### 1.2 UPD-01: 版本更新机制 (检查更新、拉取新代码与依赖)
**技术方案：**
1. **Web UI 触发**：在前端设置页面添加“检查更新”按钮。
2. **后端更新逻辑 (Socket.IO + API)**：
   - **增量拉取**：检查本地是否存在 `.git` 目录。如果存在，调用 `subprocess.run(["git", "pull"])`；如果不具备 Git 环境或属于 Zip 下载的单机版，使用 Python `requests` 访问 GitHub API 下载最新 Release 的 Source Zip，解压并覆盖。
   - **白名单保护**：覆盖时必须排除 `.venv/`, `backend/store/`, `node_modules/` 等用户数据目录。
   - **依赖更新**：源码覆盖后，子进程触发 `pip install -r backend/requirements.txt`。
3. **服务热重启**：
   - 由于 Windows 存在文件锁，如果后端 Python 正在运行可能无法覆写某些文件。
   - **安全策略**：生成一个独立的极简 `updater.py/bat`。后端接收到更新请求后，通过 `subprocess.Popen` 启动它，随后调用 `os._exit(0)` 主动关闭自己。`updater` 完成代码覆盖后，再重新拉起 `start_silent.vbs` 或 `launcher.py`。

### 1.3 UNINST-01: 一键卸载流程 (清理环境残留、快捷方式等)
**技术方案：**
1. **自毁脚本 (`uninstall.bat`)**：
   - 由于 Windows 无法删除正在运行的批处理文件自身所在目录，`uninstall.bat` 执行时，应首先将自身的清理逻辑块或 `cleanup.ps1` 拷贝到系统的 `%TEMP%` 目录下。
   - 结束相关的 Python 服务进程（避免文件锁导致目录删除失败）。可以通过读取运行时存放 PID 的锁文件，或者根据特定的端口 / Window Title 执行精准杀进程（例如 `taskkill /PID <id> /F`）。
2. **清理内容**：
   - 删除桌面的 `PS AI Assistant.lnk` 快捷方式。
   - 彻底删除项目所在的整个目录（满足 DECISION: "彻底清理所有内容包括配置文件、API Key 等"）。
3. **执行流转**：通过执行 `%TEMP%` 目录下的副本完成上述两步删除操作后，副本脚本最后再执行自我删除。

---

## 2. Existing Patterns in the Codebase to Reuse

1. **依赖自动维护 (`launcher.py`)**：
   项目中已存在完善的 `launcher.py`，其中 `ensure_backend_deps()`, `build_frontend()` 会自动检查并补全 FastAPI / Socket.IO / Node 依赖并构建产物。
   - **重用策略**：`install.bat` 仅需完成运行时环境安装，随后调用系统的构建机制，最大限度避免了重复编写依赖解决逻辑。
2. **无黑框启动 (`start_silent.vbs` & `start.bat`)**：
   根目录下已有 `start_silent.vbs` 搭配 `vbHide` 模式运行，且 `start.bat` 会自动寻找 `.venv\Scripts\python.exe`。
   - **重用策略**：桌面快捷方式直接指向 `start_silent.vbs`，可达到完全原生桌面的体验。
3. **配置文件路径 (`backend/config.py`)**：
   `ai_config.json` 储存在 `backend/store/`。
   - **重用策略**：更新时明确将 `backend/store` 纳入豁免白名单；卸载时只需 rm -rf 项目根目录，无需去 `%APPDATA%` 搜寻残留文件。

---

## 3. Potential Landmines & Strategies

| 潜在风险 (Landmine) | 应对策略 (Strategy) |
| --- | --- |
| **网络环境限制导致静默安装失败** | Python/Node 官方下载在部分地区可能受阻。需在 PowerShell 中增加 `try/catch`，若静默下载超时，中止并给出包含国内镜像站的手动下载指引。 |
| **Git 不存在导致更新失败** | 不能假设普通用户已安装 `git`。**策略**：必须提供混合更新模式。首选 `git pull`，后备方案为直接通过 HTTP 覆盖更新（ZIP模式），确保任何形态的部署包均能自更新。 |
| **更新时的 Windows 文件锁覆盖失败** | 正在被加载的模块在更新覆写时会报 `PermissionError`。**策略**：必须采用"甩锅"策略 (Handoff)，让独立的更新进程接管文件覆写，主进程主动停止并释放句柄，更新完毕后再重新拉起。 |
| **杀进程误伤** | 卸载时简单粗暴地 `taskkill /F /IM python.exe` 会导致用户的其他 Python 程序崩溃。**策略**：后端启动时在根目录写入一个 `.pid` 文件，卸载脚本读取该 PID 进行精准绞杀。 |

---

## 4. Validation Architecture

> **CRITICAL**: The orchestrator explicitly relies on this block to generate the Nyquist `VALIDATION.md` artifact.

### 4.1 测试与验证策略 (Validation Strategy)
本阶段涉及系统底层（文件系统修改、进程管控、环境部署），不适合纯单元测试。应当采用**核心逻辑单元测试**结合**环境变量拦截的干跑测试 (Dry Run)**。

### 4.2 验证维度 (Validation Dimensions)

1. **环境配置与安装验证 (Installation Scripts)**:
   - **Mock验证**: `scripts/install.ps1` 需支持 `-DryRun` 参数。在 Python 侧编写测试用例 `test_installer.py`，断言干跑模式下是否能正确识别当前机器的 Python 状态，并模拟输出快捷方式创建指令，而不发生实质影响。
   - **产物验证**: 安装脚本需返回统一的状态码或生成 `install.lock`。
2. **自更新机制验证 (Update Mechanism)**:
   - **功能验证 (Zip更新模式)**: 在测试套件 `test_updater.py` 中，使用本地临时目录模拟旧版工程；调用更新模块 API，传入本地构建好的一个包含新版本文件的 `dummy_update.zip`。
   - **白名单验证**: 断言更新完毕后，模拟工程里的 `backend/store/ai_config.json` 等配置信息未被覆盖或丢失。
3. **进程控制与卸载验证 (Lifecycle & Uninstall)**:
   - **PID锁定测试**: 验证服务启动后是否正确创建 `.pid` 文件；关闭服务后该文件是否正常移除。
   - **卸载干跑验证**: `uninstall.bat` 需响应环境变量 `TEST_MODE=1`，在此模式下，记录原本要被删除的目标路径及即将被结束的进程 PID 到本地日志文件。在测试中验证日志输出的路径与 PID 准确无误。

### 4.3 Nyquist Acceptance Criteria
- [ ] **UAT-INST-01**: 在未配置 Python / Node PATH 的终端中双击运行安装程序，能够成功拉取并在桌面生成 `PS AI Assistant.lnk`（且双击快捷方式能无黑框启动应用）。
- [ ] **UAT-UPD-01**: 在前端触发版本更新时，后端能够完成代码层面的拉取/覆盖，并实现自身的平滑自重启；更新过程中 `backend/store/` 内的 API 配置必须原样保留。
- [ ] **UAT-UNINST-01**: 运行卸载脚本后，桌面快捷方式消失，整个应用程序目录（含环境和历史数据）从硬盘移除，且操作过程没有发生因文件被占用导致删除失败的报错。
