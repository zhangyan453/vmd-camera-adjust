# -*- coding: utf-8 -*-
"""VMD 镜头位置微调工具 / VMD Camera Adjuster

用途：导入别人的 VMD 镜头（相机）动作后，批量对关键帧的位置 X / Y / Z
和距离（距離）做“加 / 减偏移”，用来修正因模型身高差异导致的取景问题
（例如高个子模型露不到脸）。

Use: after importing someone else's VMD camera motion, batch-add/subtract
offsets to the X / Y / Z position and distance of the camera keyframes,
to fix framing issues caused by model height differences.

特点 / Features:
- 只修改相机关键帧的位置与距离，镜头朝向、插值、视角等原样保留
  (only position & distance are modified; orientation / interpolation / FOV are preserved)
- 距离按 MMD 界面的正值显示（文件内部为负值，自动换算）
  (distance is shown as a positive value like the MMD UI; it is negative inside the file)
- 支持按“帧范围”选择要调整的关键帧 (adjust by frame range)
- X / Y / Z / 距离 四个滑块批量加减，动作曲线依旧连续 (batch sliders, curve stays smooth)
- 实时曲线预览（原始 vs 调整后）(live curve preview: original vs adjusted)
- 导出为新的 VMD 文件，原文件不会被覆盖 (exports a new file; the original is untouched)

界面语言 / UI language: 自动跟随系统（中文系统显示中文，其它显示英文），
也可用命令行参数强制指定 / Auto-detects system language; force with:
    python vmd_camera_tool.py --lang zh    # 中文
    python vmd_camera_tool.py --lang en    # English

依赖：仅 Python 标准库（tkinter），无需安装任何第三方库。
Deps: Python standard library only (tkinter), no third-party packages.

运行 / Run: python vmd_camera_tool.py
"""

import os
import sys
import struct
import locale
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# VMD 相机关键帧固定 61 字节 / each camera keyframe is fixed 61 bytes
CAMERA_KEYFRAME_SIZE = 61
# 关键帧内 距离(距離) 与 位置(x, y, z) 浮点数的起始偏移
DIST_OFFSET = 4
POS_OFFSET = 8
# 滑块范围与步长（步长 0.01，保留两位小数）
SLIDER_MIN, SLIDER_MAX, SLIDER_STEP = -300.0, 300.0, 0.01

# 内置窗口图标（64x64 PNG 的 base64），保证单文件也能显示自定义图标
_ICON_PNG_B64 = (
    "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"
    "kHwVbZdqJ/8ArdBqZPrPLH0AAAAASUVORK5CYII="
)


# ---------------- 界面文字 / UI strings ----------------
_STRINGS = {
    'zh': {
        'app_title': 'VMD 镜头微调工具（批量加减 X / Y / Z / 距离）',
        'open_btn': '打开 VMD 镜头文件…',
        'export_btn': '导出为新的 VMD…',
        'reset_btn': '全部复位',
        'no_file': '尚未打开文件',
        'range_label': '选择要调整的帧范围：',
        'start_label': '起始帧',
        'end_label': '结束帧',
        'apply_range_btn': '应用范围',
        'select_all_btn': '全选关键帧',
        'col_idx': '序号',
        'col_frame': '帧号',
        'col_dist': '距离',
        'preview_label': '曲线预览（灰色虚线=原始，彩色实线=调整后，浅色高亮=选中区间）',
        'batch_title': '批量加减偏移（拖滑块或直接填数值，可重复对不同区段操作）',
        'axis_d': '距',
        'apply_val_btn': '应用填值',
        'zero_btn': '归零',
        'hint': '说明：先选好帧范围 → 拖动滑块，或在框内直接输入偏移值（两位小数，如 +12.75）'
                '后按回车或点“应用填值” → 满意后“导出为新的 VMD”。'
                '距离按 MMD 界面正值显示：加=拉远、减=拉近。导出的是新文件，原文件不会被改动。',
        'err_invalid_vmd': '不是有效的 VMD 文件',
        'err_camera_section': '相机段长度与文件不符（可能不是标准 VMD 相机数据）',
        'err_open_title': '打开失败',
        'warn_no_camera_title': '没有相机数据',
        'warn_no_camera': '这个 VMD 文件里没有相机（镜头）关键帧，无法调整。',
        'dlg_open_title': '选择 VMD 镜头文件',
        'ft_vmd': 'VMD 文件',
        'ft_all': '所有文件',
        'info_opened': '已打开：%s   相机关键帧 %d 个，帧区间 %d ~ %d',
        'dlg_save_title': '导出为新的 VMD 文件',
        'err_save_title': '导出失败',
        'done_title': '导出完成',
        'done_msg': '已保存到：\n%s',
        'err_input_title': '输入有误',
        'err_frame_num': '帧号必须是数字。',
        'err_offset_num': '%s 轴偏移值必须是数字（可带正负号，两位小数）。',
        'warn_range_title': '超出范围',
        'warn_offset_range': '偏移值限制在 %+.2f ~ %+.2f 之间，已自动收敛到边界。',
        'info_no_sel_title': '未选择帧',
        'info_no_sel': '请先选择要调整的帧范围。',
        'sel_none': '未选择任何帧',
        'sel_count': '已选中 %d 个关键帧（帧 %d ~ %d）',
        'plot_empty': '打开 VMD 文件后在此显示曲线',
        'plot_frames': '帧 %d ~ %d',
    },
    'en': {
        'app_title': 'VMD Camera Adjuster (Batch Offset X / Y / Z / Distance)',
        'open_btn': 'Open VMD Camera File…',
        'export_btn': 'Export as New VMD…',
        'reset_btn': 'Reset All',
        'no_file': 'No file opened',
        'range_label': 'Frame range to adjust:',
        'start_label': 'Start frame',
        'end_label': 'End frame',
        'apply_range_btn': 'Apply Range',
        'select_all_btn': 'Select All',
        'col_idx': '#',
        'col_frame': 'Frame',
        'col_dist': 'Distance',
        'preview_label': 'Curve preview (gray dashed = original, colored solid = adjusted, light band = selected range)',
        'batch_title': 'Batch Offset (drag a slider or type a value; repeat for different frame sections)',
        'axis_d': 'D',
        'apply_val_btn': 'Apply',
        'zero_btn': 'Zero',
        'hint': 'How to use: select a frame range → drag a slider, or type an offset (two decimals, e.g. +12.75) '
                'and press Enter / click "Apply" → when satisfied, "Export as New VMD". '
                'Distance is shown as a positive value like the MMD UI: plus = move away, minus = move closer. '
                'Export writes a NEW file; the original is never modified.',
        'err_invalid_vmd': 'Not a valid VMD file',
        'err_camera_section': 'Camera section size mismatch (may not be standard VMD camera data)',
        'err_open_title': 'Open failed',
        'warn_no_camera_title': 'No camera data',
        'warn_no_camera': 'This VMD file contains no camera keyframes, so there is nothing to adjust.',
        'dlg_open_title': 'Select a VMD camera file',
        'ft_vmd': 'VMD files',
        'ft_all': 'All files',
        'info_opened': 'Opened: %s   %d camera keyframes, frame range %d ~ %d',
        'dlg_save_title': 'Export as a new VMD file',
        'err_save_title': 'Export failed',
        'done_title': 'Export complete',
        'done_msg': 'Saved to:\n%s',
        'err_input_title': 'Invalid input',
        'err_frame_num': 'Frame numbers must be numeric.',
        'err_offset_num': 'The %s offset must be a number (optional sign, two decimals).',
        'warn_range_title': 'Out of range',
        'warn_offset_range': 'Offsets are limited to %+.2f ~ %+.2f; the value has been clamped.',
        'info_no_sel_title': 'No frames selected',
        'info_no_sel': 'Please select a frame range first.',
        'sel_none': 'No frames selected',
        'sel_count': '%d keyframes selected (frames %d ~ %d)',
        'plot_empty': 'Open a VMD file to see the curves here',
        'plot_frames': 'Frames %d ~ %d',
    },
}


def _detect_lang():
    """系统语言自适应 / auto-detect system language (zh -> Chinese, else English)."""
    forced = os.environ.get('VMD_TOOL_LANG', '')
    if forced:
        return 'zh' if forced.lower().startswith('zh') else 'en'
    try:
        loc = locale.getdefaultlocale()[0] or ''
    except Exception:
        loc = ''
    return 'zh' if loc.lower().startswith('zh') else 'en'


_LANG = _detect_lang()


def t(key, *args):
    s = _STRINGS.get(_LANG, _STRINGS['en']).get(key)
    if s is None:
        s = _STRINGS['en'].get(key, key)
    return s % args if args else s


class VmdCamera:
    """解析 / 保存 VMD 中的相机动作段（只改位置与距离，其它字节原样保留）。

    距离在文件内部为负值，这里统一换算为 MMD 界面的正值（ui = -raw）。
    """

    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as fp:
            self.raw = fp.read()
        self._parse()

    def _parse(self):
        d = self.raw
        if len(d) < 54 or not d.startswith(b'Vocaloid Motion Data'):
            raise ValueError(t('err_invalid_vmd'))

        self.header = d[:30]
        self.model_name = d[30:50]

        off = 50
        self.bone_count = struct.unpack_from('<I', d, off)[0]
        off += 4 + self.bone_count * 111

        self.morph_count = struct.unpack_from('<I', d, off)[0]
        off += 4 + self.morph_count * 23

        self.camera_count = struct.unpack_from('<I', d, off)[0]
        off += 4
        self.camera_start = off

        cam_bytes = self.camera_count * CAMERA_KEYFRAME_SIZE
        if off + cam_bytes > len(d):
            raise ValueError(t('err_camera_section'))

        self.camera_bytes = bytearray(d[off:off + cam_bytes])

        # 预解析每个关键帧的 帧号、原始距离 与 原始位置
        self.frames = []
        self.orig_dist = []
        self.orig_pos = []
        for i in range(self.camera_count):
            b = i * CAMERA_KEYFRAME_SIZE
            self.frames.append(struct.unpack_from('<I', self.camera_bytes, b)[0])
            self.orig_dist.append(-struct.unpack_from(
                '<f', self.camera_bytes, b + DIST_OFFSET)[0])
            self.orig_pos.append(list(struct.unpack_from(
                '<fff', self.camera_bytes, b + POS_OFFSET)))

        # 当前值（滑块滑动时直接修改这里，写文件时以它为准）
        self.cur_pos = [list(p) for p in self.orig_pos]
        self.cur_dist = list(self.orig_dist)

    def set_pos(self, i, xyz):
        """设置第 i 个关键帧的位置。"""
        self.cur_pos[i] = [float(xyz[0]), float(xyz[1]), float(xyz[2])]
        struct.pack_into('<fff', self.camera_bytes,
                         i * CAMERA_KEYFRAME_SIZE + POS_OFFSET, *self.cur_pos[i])

    def set_dist(self, i, dist):
        """设置第 i 个关键帧的距离（MMD 界面正值）。"""
        self.cur_dist[i] = float(dist)
        struct.pack_into('<f', self.camera_bytes,
                         i * CAMERA_KEYFRAME_SIZE + DIST_OFFSET, -self.cur_dist[i])

    def reset_all(self):
        """全部关键帧恢复为原始位置与距离。"""
        for i in range(self.camera_count):
            self.set_pos(i, self.orig_pos[i])
            self.set_dist(i, self.orig_dist[i])

    def save(self, path):
        """另存为新的 VMD 文件（其余数据原样保留）。"""
        for i in range(self.camera_count):
            b = i * CAMERA_KEYFRAME_SIZE
            struct.pack_into('<fff', self.camera_bytes, b + POS_OFFSET, *self.cur_pos[i])
            struct.pack_into('<f', self.camera_bytes, b + DIST_OFFSET, -self.cur_dist[i])
        out = bytearray(self.raw)
        end = self.camera_start + self.camera_count * CAMERA_KEYFRAME_SIZE
        out[self.camera_start:end] = self.camera_bytes
        with open(path, 'wb') as fp:
            fp.write(out)

    def has_change(self):
        return any(self.cur_pos[i] != self.orig_pos[i]
                   or self.cur_dist[i] != self.orig_dist[i]
                   for i in range(self.camera_count))


class App:
    def __init__(self, root):
        self.root = root
        root.title(t('app_title'))
        root.geometry('1080x720')
        root.minsize(900, 600)

        self.vmd = None          # VmdCamera 实例
        self.sel = set()         # 当前选中的关键帧索引集合
        self._snapshot = None    # 一次“滑动会话”开始时的位置快照（防止多次累加误差）
        self._tree_items = []    # Treeview 行 id

        self._build_top()
        self._build_middle()
        self._build_bottom()
        self._set_controls_state(False)

    # ---------------- 界面搭建 ----------------
    def _build_top(self):
        bar = ttk.Frame(self.root, padding=(10, 8))
        bar.pack(fill='x')

        ttk.Button(bar, text=t('open_btn'), command=self.open_file).pack(side='left')
        ttk.Button(bar, text=t('export_btn'), command=self.save_file).pack(side='left', padx=6)
        ttk.Button(bar, text=t('reset_btn'), command=self.reset_all).pack(side='left', padx=6)

        self.info = ttk.Label(bar, text=t('no_file'), foreground='#555')
        self.info.pack(side='left', padx=14)

        sel_bar = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        sel_bar.pack(fill='x')

        ttk.Label(sel_bar, text=t('range_label')).pack(side='left')
        ttk.Label(sel_bar, text=t('start_label')).pack(side='left', padx=(10, 2))
        self.entry_start = ttk.Entry(sel_bar, width=8)
        self.entry_start.pack(side='left')
        ttk.Label(sel_bar, text=t('end_label')).pack(side='left', padx=(10, 2))
        self.entry_end = ttk.Entry(sel_bar, width=8)
        self.entry_end.pack(side='left')
        ttk.Button(sel_bar, text=t('apply_range_btn'), command=self.apply_range).pack(side='left', padx=6)
        ttk.Button(sel_bar, text=t('select_all_btn'), command=self.select_all).pack(side='left')

        self.sel_label = ttk.Label(sel_bar, text='', foreground='#0a7')
        self.sel_label.pack(side='left', padx=14)

    def _build_middle(self):
        pane = ttk.Panedwindow(self.root, orient='horizontal')
        pane.pack(fill='both', expand=True, padx=10, pady=(0, 4))

        # 左：关键帧表格
        left = ttk.Frame(pane)
        cols = ('idx', 'frame', 'x', 'y', 'z', 'dist')
        self.tree = ttk.Treeview(left, columns=cols, show='headings', height=20)
        for c, tt, w in (('idx', t('col_idx'), 55), ('frame', t('col_frame'), 65),
                         ('x', 'X', 115), ('y', 'Y', 115), ('z', 'Z', 115),
                         ('dist', t('col_dist'), 115)):
            self.tree.heading(c, text=tt)
            self.tree.column(c, width=w, anchor='center')
        vsb = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        pane.add(left, weight=1)

        # 右：曲线预览
        right = ttk.Frame(pane)
        ttk.Label(right, text=t('preview_label')).pack(anchor='w', padx=4, pady=(2, 0))
        self.canvas = tk.Canvas(right, bg='white', highlightthickness=1,
                                highlightbackground='#ccc')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.draw_plot())
        pane.add(right, weight=2)

    def _build_bottom(self):
        box = ttk.LabelFrame(self.root, text=t('batch_title'), padding=(10, 6))
        box.pack(fill='x', padx=10, pady=(2, 10))

        self.sliders = {}
        self.value_entries = {}
        for key, name, color in (('x', 'X', '#2563eb'),
                                 ('y', 'Y', '#16a34a'),
                                 ('z', 'Z', '#ea580c'),
                                 ('d', t('axis_d'), '#7c3aed')):
            row = ttk.Frame(box)
            row.pack(fill='x', pady=3)
            tk.Label(row, text=name, fg=color, width=2,
                     font=('Segoe UI', 11, 'bold')).pack(side='left')
            s = ttk.Scale(row, from_=SLIDER_MIN, to=SLIDER_MAX, orient='horizontal',
                          length=560, command=lambda v, k=key: self.on_slider(k))
            s.pack(side='left', padx=6)
            s.set(0.0)
            ent = ttk.Entry(row, width=9, justify='center')
            ent.insert(0, '+0.00')
            ent.pack(side='left', padx=(2, 2))
            ent.bind('<Return>', lambda e, k=key: self.apply_entry(k))
            ttk.Button(row, text=t('apply_val_btn'), width=8,
                       command=lambda k=key: self.apply_entry(k)).pack(side='left')
            ttk.Button(row, text=t('zero_btn'), width=5,
                       command=lambda k=key: self.zero_slider(k)).pack(side='left', padx=6)
            self.sliders[key] = s
            self.value_entries[key] = ent

        hint = ttk.Label(box, foreground='#666', text=t('hint'))
        hint.pack(anchor='w', pady=(4, 0))

    def _set_controls_state(self, enabled):
        for k in self.sliders:
            self.sliders[k].state(['!disabled'] if enabled else ['disabled'])
            self.value_entries[k].state(['!disabled'] if enabled else ['disabled'])
        self.entry_start.state(['!disabled'] if enabled else ['disabled'])
        self.entry_end.state(['!disabled'] if enabled else ['disabled'])

    # ---------------- 文件操作 ----------------
    def open_file(self):
        path = filedialog.askopenfilename(
            title=t('dlg_open_title'),
            filetypes=[(t('ft_vmd'), '*.vmd'), (t('ft_all'), '*.*')])
        if not path:
            return
        try:
            vmd = VmdCamera(path)
        except Exception as e:
            messagebox.showerror(t('err_open_title'), str(e))
            return
        if vmd.camera_count == 0:
            messagebox.showwarning(t('warn_no_camera_title'), t('warn_no_camera'))
            return

        self.vmd = vmd
        self._populate_tree()
        fmin, fmax = min(vmd.frames), max(vmd.frames)
        self.entry_start.delete(0, 'end')
        self.entry_start.insert(0, str(fmin))
        self.entry_end.delete(0, 'end')
        self.entry_end.insert(0, str(fmax))
        self.sel = set(range(vmd.camera_count))
        self._snapshot = None
        self._reset_sliders()
        self.info.config(text=t('info_opened', os.path.basename(path),
                                vmd.camera_count, fmin, fmax),
                         foreground='#333')
        self.refresh()
        self._set_controls_state(True)

    def save_file(self):
        if not self.vmd:
            return
        base = os.path.splitext(os.path.basename(self.vmd.path))[0]
        path = filedialog.asksaveasfilename(
            title=t('dlg_save_title'),
            defaultextension='.vmd',
            initialfile=base + '_adjusted.vmd',
            filetypes=[(t('ft_vmd'), '*.vmd')])
        if not path:
            return
        try:
            self.vmd.save(path)
        except Exception as e:
            messagebox.showerror(t('err_save_title'), str(e))
            return
        messagebox.showinfo(t('done_title'), t('done_msg', path))

    def reset_all(self):
        if not self.vmd:
            return
        self.vmd.reset_all()
        self._snapshot = None
        self._reset_sliders()
        self.refresh()

    # ---------------- 选择与滑块 ----------------
    def _parse_frame_entry(self):
        try:
            a = int(float(self.entry_start.get()))
            b = int(float(self.entry_end.get()))
        except ValueError:
            messagebox.showerror(t('err_input_title'), t('err_frame_num'))
            return None
        if a > b:
            a, b = b, a
        return a, b

    def apply_range(self):
        if not self.vmd:
            return
        rng = self._parse_frame_entry()
        if not rng:
            return
        a, b = rng
        self.sel = {i for i, f in enumerate(self.vmd.frames) if a <= f <= b}
        self._begin_session()
        self.refresh()

    def select_all(self):
        if not self.vmd:
            return
        self.sel = set(range(self.vmd.camera_count))
        self._begin_session()
        self.refresh()

    def _begin_session(self):
        """进入一次新的滑动会话：记录当前选中关键帧位置作为基准，滑块归零。"""
        self._snapshot = None
        self._reset_sliders()

    def _reset_sliders(self):
        for k in self.sliders:
            self.sliders[k].set(0.0)
            self._set_entry_text(k, 0.0)

    def zero_slider(self, key):
        self.sliders[key].set(0.0)
        self._set_entry_text(key, 0.0)
        self._snapshot = None
        self.on_slider(key)

    def _slider_val(self, key):
        return round(self.sliders[key].get(), 2)

    def _set_entry_text(self, key, val):
        ent = self.value_entries[key]
        state = ent.cget('state')
        if state == 'disabled':
            ent.state(['!disabled'])
        ent.delete(0, 'end')
        ent.insert(0, '%+.2f' % val)
        if state == 'disabled':
            ent.state(['disabled'])

    def apply_entry(self, key):
        """把输入框里的数值作为该轴的偏移量直接应用（支持两位小数）。"""
        if not self.vmd:
            return
        try:
            val = round(float(self.value_entries[key].get().strip()), 2)
        except ValueError:
            messagebox.showerror(t('err_input_title'),
                                 t('err_offset_num', key.upper()))
            return
        if val < SLIDER_MIN or val > SLIDER_MAX:
            messagebox.showwarning(t('warn_range_title'),
                                   t('warn_offset_range', SLIDER_MIN, SLIDER_MAX))
            val = max(SLIDER_MIN, min(SLIDER_MAX, val))
        # 同步滑块位置（会触发 on_slider），再显式应用一次确保生效
        self.sliders[key].set(val)
        self._set_entry_text(key, val)
        self.on_slider(key)

    def on_slider(self, key):
        if not self.vmd:
            return
        if not self.sel:
            messagebox.showinfo(t('info_no_sel_title'), t('info_no_sel'))
            return
        if self._snapshot is None:
            # 本次滑动开始，记录选中关键帧的当前位置与距离作为基准
            self._snapshot = {i: (list(self.vmd.cur_pos[i]), self.vmd.cur_dist[i])
                              for i in self.sel}

        dx = self._slider_val('x')
        dy = self._slider_val('y')
        dz = self._slider_val('z')
        dd = self._slider_val('d')
        # 同步四个输入框显示当前偏移量（正在输入的框不打扰）
        for k, v in (('x', dx), ('y', dy), ('z', dz), ('d', dd)):
            ent = self.value_entries[k]
            if self.root.focus_get() is not ent:
                self._set_entry_text(k, v)

        for i in self.sel:
            (bx, by, bz), bd = self._snapshot[i]
            self.vmd.set_pos(i, (bx + dx, by + dy, bz + dz))
            self.vmd.set_dist(i, bd + dd)

        self._update_tree_rows()
        self.draw_plot()
        self._update_sel_label()

    # ---------------- 显示刷新 ----------------
    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._tree_items = []
        for i in range(self.vmd.camera_count):
            item = self.tree.insert('', 'end', values=self._row_values(i))
            self._tree_items.append(item)

    def _row_values(self, i):
        x, y, z = self.vmd.cur_pos[i]
        return (i, self.vmd.frames[i], '%.2f' % x, '%.2f' % y, '%.2f' % z,
                '%.2f' % self.vmd.cur_dist[i])

    def _update_tree_rows(self):
        for i in range(self.vmd.camera_count):
            self.tree.item(self._tree_items[i], values=self._row_values(i))

    def refresh(self):
        if not self.vmd:
            return
        self._update_tree_rows()
        self._highlight_selection()
        self.draw_plot()
        self._update_sel_label()

    def _highlight_selection(self):
        self.tree.tag_configure('sel', background='#e8f5e9')
        for i, item in enumerate(self._tree_items):
            self.tree.item(item, tags=('sel',) if i in self.sel else ())

    def _update_sel_label(self):
        if not self.vmd:
            return
        if not self.sel:
            self.sel_label.config(text=t('sel_none'))
            return
        fs = [self.vmd.frames[i] for i in self.sel]
        self.sel_label.config(text=t('sel_count', len(self.sel), min(fs), max(fs)))

    # ---------------- 曲线绘制 ----------------
    def draw_plot(self):
        c = self.canvas
        c.delete('all')
        if not self.vmd:
            c.create_text(20, 20, anchor='nw', text=t('plot_empty'), fill='#999')
            return
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50 or h < 50:
            return

        pad_l, pad_r, pad_t, pad_b = 46, 12, 22, 18
        bands = [
            ('X', '#2563eb',
             lambda i: self.vmd.orig_pos[i][0], lambda i: self.vmd.cur_pos[i][0]),
            ('Y', '#16a34a',
             lambda i: self.vmd.orig_pos[i][1], lambda i: self.vmd.cur_pos[i][1]),
            ('Z', '#ea580c',
             lambda i: self.vmd.orig_pos[i][2], lambda i: self.vmd.cur_pos[i][2]),
            (t('axis_d'), '#7c3aed',
             lambda i: self.vmd.orig_dist[i], lambda i: self.vmd.cur_dist[i]),
        ]
        band_h = (h - pad_t - pad_b) / len(bands)
        # 依据帧号排序，保证 X 轴按帧递增
        order = sorted(range(self.vmd.camera_count), key=lambda i: self.vmd.frames[i])
        frames = [self.vmd.frames[i] for i in order]
        fmin, fmax = frames[0], frames[-1]
        span = max(1, fmax - fmin)

        for bi, (name, color, get_orig, get_cur) in enumerate(bands):
            top = pad_t + bi * band_h
            bottom = top + band_h - 8

            o_vals = [get_orig(i) for i in order]
            c_vals = [get_cur(i) for i in order]
            lo = min(min(o_vals), min(c_vals))
            hi = max(max(o_vals), max(c_vals))
            if hi - lo < 1e-6:
                hi = lo + 1.0
            vspan = hi - lo

            def to_xy(idx_in_order, val):
                px = pad_l + (frames[idx_in_order] - fmin) / span * (w - pad_l - pad_r)
                py = bottom - (val - lo) / vspan * (band_h - 28)
                return px, py

            # 选中区间高亮
            sel_idx = [k for k, i in enumerate(order) if i in self.sel]
            if sel_idx:
                x0 = pad_l + (min(frames[k] for k in sel_idx) - fmin) / span * (w - pad_l - pad_r)
                x1 = pad_l + (max(frames[k] for k in sel_idx) - fmin) / span * (w - pad_l - pad_r)
                c.create_rectangle(x0, top + 2, max(x1, x0 + 2), bottom,
                                   fill='#f0f7ff', outline='')
                # 由于矩形在底层，重新画刻度文字
            # 原始曲线（虚线）
            pts = []
            for k in range(len(order)):
                pts.extend(to_xy(k, o_vals[k]))
            c.create_line(*pts, fill='#9aa5b1', dash=(4, 3), width=1)
            # 调整后曲线（实线彩色）
            pts = []
            for k in range(len(order)):
                pts.extend(to_xy(k, c_vals[k]))
            c.create_line(*pts, fill=color, width=1.8)

            # 名称与数值范围
            c.create_text(6, top + 6, anchor='nw', text=name, fill=color,
                          font=('Segoe UI', 10, 'bold'))
            c.create_text(pad_l, top + 4, anchor='nw',
                          text='%.2f ~ %.2f' % (lo, hi), fill='#888')
            c.create_line(pad_l, bottom, w - pad_r, bottom, fill='#ddd')
        c.create_text(w - pad_r, h - 6, anchor='se',
                      text=t('plot_frames', fmin, fmax), fill='#888')


def _apply_window_icon(root):
    """设置窗口 / 任务栏图标：优先用同目录的 icon.ico，否则用内置 PNG。"""
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    try:
        if os.name == 'nt' and os.path.exists(ico):
            root.iconbitmap(ico)
            return
    except Exception:
        pass
    try:
        img = tk.PhotoImage(data=_ICON_PNG_B64)
        root.iconphoto(True, img)
        root._icon_image = img  # 保持引用，防止图标被回收
    except Exception:
        pass


def main():
    global _LANG
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a in ('--lang', '-l') and i + 1 < len(argv):
            _LANG = 'zh' if argv[i + 1].lower().startswith('zh') else 'en'
        elif a.startswith('--lang='):
            v = a.split('=', 1)[1]
            _LANG = 'zh' if v.lower().startswith('zh') else 'en'

    root = tk.Tk()
    try:
        root.call('tk', 'scaling', 1.2)
    except Exception:
        pass
    _apply_window_icon(root)
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
