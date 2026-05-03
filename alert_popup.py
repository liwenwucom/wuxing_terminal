# -*- coding: utf-8 -*-
"""
五行韭菜盘 —— 弹窗提醒独立脚本
由 monitor.py 通过 subprocess 调用，接收 JSON 数据展示预警列表
"""

import sys
import json
import tkinter as tk
from tkinter import ttk


def build_window(data: dict):
    root = tk.Tk()
    root.title("五行韭菜盘 · 实时预警")
    root.geometry("580x480")
    root.configure(bg="#1a1a2e")
    root.resizable(True, True)

    # 样式
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background="#16213e",
                    foreground="#e0e0e0",
                    fieldbackground="#16213e",
                    rowheight=32,
                    font=("Microsoft YaHei UI", 10))
    style.configure("Treeview.Heading",
                    background="#0f3460",
                    foreground="#e0c068",
                    font=("Microsoft YaHei UI", 10, "bold"))
    style.map("Treeview", background=[("selected", "#e94560")])

    # 标题栏
    header_frame = tk.Frame(root, bg="#0f3460", height=56)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    tk.Label(
        header_frame,
        text="五行韭菜盘 · 实时预警",
        font=("Microsoft YaHei UI", 14, "bold"),
        fg="#e0c068", bg="#0f3460",
    ).pack(side="left", padx=16, pady=10)

    timestamp = data.get("timestamp", "")
    tk.Label(
        header_frame,
        text=timestamp,
        font=("Microsoft YaHei UI", 9),
        fg="#888888", bg="#0f3460",
    ).pack(side="right", padx=16, pady=10)

    # 干支/气场 信息条
    info = data.get("context", {})
    if info:
        ctx_frame = tk.Frame(root, bg="#1a1a2e")
        ctx_frame.pack(fill="x", padx=8, pady=(8, 0))

        parts = []
        if info.get("ganzhi"):
            parts.append(f"干支: {info['ganzhi']}")
        if info.get("dominant_wuxing"):
            parts.append(f"五行: {info['dominant_wuxing']}")
        if info.get("boost_level"):
            parts.append(f"气场: {info['boost_level']}")
        if info.get("ai_sentiment"):
            parts.append(f"AI: {info['ai_sentiment']}")

        ctx_text = "  |  ".join(parts)
        tk.Label(
            ctx_frame,
            text=ctx_text,
            font=("Microsoft YaHei UI", 9),
            fg="#aaaaaa", bg="#1a1a2e",
        ).pack(anchor="w", padx=4)

    # 树状列表
    tree_frame = tk.Frame(root, bg="#1a1a2e")
    tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

    tree = ttk.Treeview(
        tree_frame,
        columns=("品种", "承载力", "择时", "预期", "操作提示"),
        show="headings",
    )

    tree.heading("品种", text="品种")
    tree.heading("承载力", text="承载力")
    tree.heading("择时", text="择时")
    tree.heading("预期", text="预期方向")
    tree.heading("操作提示", text="操作提示")

    tree.column("品种", width=150, anchor="center")
    tree.column("承载力", width=80, anchor="center")
    tree.column("择时", width=60, anchor="center")
    tree.column("预期", width=120, anchor="center")
    tree.column("操作提示", width=150, anchor="w")

    # 插入数据
    items = data.get("items", [])
    tags = []
    for item in items:
        name = item.get("name", "")
        code = item.get("code", "")
        capacity = item.get("stage", "")
        timing = item.get("timing", "")
        expected = item.get("expected", "")
        hint = item.get("hint", "")

        display_name = f"{name} {code}" if code else name

        # 颜色标记
        tag = "normal"
        if capacity == "帝旺":
            tag = "diwang"
        elif capacity in ("临官", "冠带"):
            tag = "lingguan"

        tree.insert("", "end", values=(display_name, capacity, timing, expected, hint), tags=(tag,))
        tags.append(tag)

    tree.tag_configure("diwang", background="#4a1a1a", foreground="#ff6b6b")
    tree.tag_configure("lingguan", background="#1a3a1a", foreground="#6bff6b")
    tree.tag_configure("normal", foreground="#cccccc")

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 底部按钮栏
    btn_frame = tk.Frame(root, bg="#1a1a2e")
    btn_frame.pack(fill="x", padx=8, pady=(0, 12))

    summary = data.get("summary", "")
    if summary:
        tk.Label(
            btn_frame,
            text=summary,
            font=("Microsoft YaHei UI", 9),
            fg="#888888", bg="#1a1a2e",
            wraplength=520, justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

    close_btn = tk.Button(
        btn_frame,
        text="关闭",
        font=("Microsoft YaHei UI", 10),
        bg="#0f3460", fg="#e0e0e0",
        activebackground="#e94560", activeforeground="#ffffff",
        relief="flat", padx=24, pady=6,
        cursor="hand2",
        command=root.destroy,
    )
    close_btn.pack(side="right", padx=4)

    # 居中
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"+{x}+{y}")

    root.mainloop()


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {"items": [], "summary": "无预警数据"}
    except Exception:
        data = {"items": [], "summary": "数据解析失败"}

    build_window(data)


if __name__ == "__main__":
    main()
