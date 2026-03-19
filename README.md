[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# OsuSBRenderer (Alpha v1.0)
# 不想写，README是AI弄的
# 为什么还要继续看啊啊啊啊啊啊啊

**OsuSBRenderer** 是一款基于 Python 开发的OSU故事板视频渲染工具。它能够将.osb或.osu(这部分有点多余)文件中的视觉效果导出为视频文件

---

## 环境要求

在开始运行前，确保系统中已安装：

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
2.  选择 `[2] Set export path` 设置导出路径，路径保存以后写
3.  选择 `[1] Render a new Storyboard`，在弹出的对话框中选择包含 `.osb` 文件的谱面文件夹
4.  设置渲染的起始和结束时间（毫秒），跳过为全部渲染
5.  等

---

## 项目架构

*   `main.py`: CLI 界面与多进程调度核心
*   `core/`:
    *   `parser.py`: 解析故事板事件逻辑
    *   `timeline.py`: 计算任意时间点的物件状态
    *   `easing.py`: 缓动函数数学库
    *   剩下的不想写了

---

代码中可能存在以下情况：
*   部分复循环和触发不完善
*   以及很多渲染问题

---

## 开源协议

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件