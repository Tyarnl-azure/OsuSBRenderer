[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# OsuSBRenderer (Alpha v1.0)
# 不想写，AI弄的

**OsuSBRenderer** 是一款基于 Python 开发的OSU故事板视频渲染工具。它能够将.osb或.osu(这部分有点多余)文件中的视觉效果导出为视频文件

---

## 特性

*   **并行渲染**：利用 Python 的 `ProcessPoolExecutor` 实现多核加速，显著提升渲染速度
*   **高精度数学模拟**：不完整实现 OSU 标准的缓动算法，确保动态效果与游戏内不完全一致
*   **内存优化管理**：内置纹理缓存管理机制，支持自定义最大内存限制，防止在渲染超大故事板时溢出

---

## 环境要求

在开始运行前，请确保系统中已安装：

1.  **Python 3.8+**
2.  **FFmpeg**：在系统环境变量中

---

## 快速开始

### 1. 安装依赖
```bash
pip install numpy opencv-python
```

### 2. 运行程序
```bash
python main.py
```

### 3. 操作流程
1.  启动后，在菜单中选择 `[3] Set rendering parameters` 设置分辨率和帧率。默认参数1080P和60FPS不用动
2.  选择 `[2] Set export path` 设置导出路径，我懒得写保存了
2.  选择 `[1] Render a new Storyboard`，在弹出的对话框中选择包含 `.osb` 文件的谱面文件夹
3.  设置渲染的起始和结束时间（毫秒），跳过为全部渲染
4.  等待渲染完成

---

## 项目架构

*   `main.py`: CLI 界面与多进程调度核心
*   `core/`:
    *   `parser.py`: 解析故事板事件逻辑
    *   `timeline.py`: 计算任意时间点的物件状态
    *   `easing.py`: 缓动函数数学库
    * 剩下的懒得写

---

代码中可能存在以下情况：
*   部分复循环和触发不完善
*   以及很多渲染问题

---

## 开源协议

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件