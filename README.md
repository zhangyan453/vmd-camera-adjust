<p align="center"><img src="icon.png" width="96" alt="VMD Camera Adjuster"></p>

# VMD Camera Adjuster / VMD 镜头微调工具

**中文** | [English](#english)

---

## 中文

一个用于 MMD（MikuMikuDance）的小工具：导入别人的 VMD 镜头（相机）动作后，
对关键帧的位置 X / Y / Z 和**距离**做**批量加 / 减偏移**，用来修正因模型身高差异
导致的取景问题（比如高个子模型露不到脸）。

### 功能特点

- 只修改相机关键帧的**位置与距离**，镜头朝向、插值、视角等原样保留
- 距离按 MMD 界面的**正值**显示（VMD 文件内部为负值，自动换算）：加 = 拉远、减 = 拉近
- 支持**按帧范围**选择要调整的关键帧，也可以全选
- X / Y / Z / 距离 四个滑块 + 数值输入框，步长 0.01（两位小数）
- 快照基准设计：多次滑动不会累积误差
- 实时曲线预览（灰色虚线 = 原始，彩色实线 = 调整后）
- **导出为新文件**，原 VMD 不会被覆盖
- 界面**中英文自适应**（中文系统显示中文，其它显示英文），也可手动切换
- 纯 Python 标准库（tkinter），**无需安装任何第三方库**

### 环境要求

- Python 3.8 及以上（自带 tkinter 即可，Windows 官方安装包默认包含）

### 使用方法

**Windows**：双击 `start_vmd_tool.bat` 即可启动。

或者命令行运行：

```
python vmd_camera_tool.py
python vmd_camera_tool.py --lang en   # 强制英文界面 / force English UI
python vmd_camera_tool.py --lang zh   # 强制中文界面 / force Chinese UI
```

操作步骤：

1. 点 **打开 VMD 镜头文件…**，选择一个含相机关键帧的 VMD
2. 设置**起始帧 / 结束帧**，点 **应用范围**（或直接 **全选关键帧**）
3. 拖动 X / Y / Z / 距离 滑块，或在输入框里填偏移值（如 `+12.75`）后回车
4. 观察右侧曲线预览，满意后点 **导出为新的 VMD…**

### 技术说明（VMD 相机数据格式）

- VMD 相机关键帧为固定 **61 字节 / 帧**：帧号(u32) + 距离(f32, 文件内为负值)
  + 位置 XYZ(f32×3) + 朝向 + 插值参数 + 视角
- 本工具只重写其中的距离与位置 12 字节，其余字节逐字节保留；
  对未做修改的文件进行“读入 → 导出”的结果与源文件**二进制一致**（已测试验证）

### 免责声明

本工具按“现状”提供，请导出前自行备份 VMD 文件。

## License / 许可证

[MIT](LICENSE)

---

<a id="english"></a>
## English

A small utility for MMD (MikuMikuDance): after importing someone else's VMD
camera motion, batch-add/subtract offsets to the X / Y / Z position and
**distance** of camera keyframes, to fix framing issues caused by model height
differences (e.g. a taller model's face being out of frame).

### Features

- Only the **position and distance** of camera keyframes are modified;
  orientation, interpolation and FOV are preserved byte-for-byte
- Distance is displayed as a **positive** value like the MMD UI (it is negative
  inside the VMD file, converted automatically): plus = move away, minus = move closer
- Select keyframes **by frame range**, or select all
- Four sliders (X / Y / Z / Distance) + numeric input boxes, step 0.01 (two decimals)
- Snapshot-based design: repeated slider drags do not accumulate errors
- Live curve preview (gray dashed = original, colored solid = adjusted)
- **Exports a new file**; the original VMD is never overwritten
- **Chinese / English UI** auto-detected from system language; can be forced
  with `--lang`
- Pure Python standard library (tkinter), **no third-party dependencies**

### Requirements

- Python 3.8+ (with tkinter; included by default in the official Windows installer)

### Usage

**Windows**: double-click `start_vmd_tool.bat`.

Or from the command line:

```
python vmd_camera_tool.py
python vmd_camera_tool.py --lang en   # force English UI / 强制英文界面
python vmd_camera_tool.py --lang zh   # force Chinese UI / 强制中文界面
```

Steps:

1. Click **Open VMD Camera File…** and pick a VMD that contains camera keyframes
2. Set **start / end frame**, click **Apply Range** (or **Select All**)
3. Drag the X / Y / Z / Distance sliders, or type an offset (e.g. `+12.75`) and press Enter
4. Watch the curve preview on the right, then click **Export as New VMD…**

### Technical notes (VMD camera data format)

- Each VMD camera keyframe is a fixed **61 bytes**: frame number (u32) +
  distance (f32, negative inside the file) + position XYZ (f32×3) + orientation
  + interpolation parameters + viewing angle
- The tool rewrites only the distance and position (12 bytes) and keeps every
  other byte intact; round-tripping an unmodified file produces a file
  **binary-identical** to the source (verified by test)

### Disclaimer

Provided as-is. Please back up your VMD files before exporting.

## License

[MIT](LICENSE)
