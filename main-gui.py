import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from lr1_parser import LR1Parser
from lexer import tokenize_file
from PIL import Image, ImageTk
from semantic_checker import run_semantic_checks
import traceback

class CompilerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Rust-like Compiler GUI")
        self.geometry("1000x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # 状态变量
        self.original_image = None
        self.zoom_ratio = 1.0

        # 总体布局配置
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ===== 顶部按钮栏 =====
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        top_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(top_bar, text="打开文件", command=self.load_file).grid(row=0, column=0, padx=10)
        ctk.CTkButton(top_bar, text="开始分析", command=self.run_analysis).grid(row=0, column=1, padx=10)

        self.appearance_option = ctk.CTkOptionMenu(
            top_bar, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode)
        self.appearance_option.set("Dark")
        self.appearance_option.grid(row=0, column=2, sticky="e", padx=10)

        # ===== 左侧代码输入区域（含滚动条） =====
        code_frame = tk.Frame(self, bg="#1e1e1e")
        code_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        code_frame.grid_rowconfigure(0, weight=1)
        code_frame.grid_columnconfigure(0, weight=1)

        self.code_input = tk.Text(code_frame, bg="#1e1e1e", fg="white",
                                  insertbackground="white", font=("Courier", 11))
        self.code_input.grid(row=0, column=0, sticky="nsew")
        code_scroll = tk.Scrollbar(code_frame, command=self.code_input.yview)
        code_scroll.grid(row=0, column=1, sticky="ns")
        self.code_input.config(yscrollcommand=code_scroll.set)

        # ===== 右侧标签页 =====
        self.result_tabs = ctk.CTkTabview(self)
        self.result_tabs.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

        # ---- 标签1：词法分析（含滚动条） ----
        self.token_tab = self.result_tabs.add("词法分析")
        token_frame = tk.Frame(self.token_tab, bg="#262626")
        token_frame.pack(fill="both", expand=True, padx=10, pady=10)
        token_frame.grid_rowconfigure(0, weight=1)
        token_frame.grid_columnconfigure(0, weight=1)

        self.token_output = tk.Text(token_frame, bg="#262626", fg="white",
                                    insertbackground="white", font=("Courier", 10), state="disabled")
        self.token_output.grid(row=0, column=0, sticky="nsew")
        token_scroll = tk.Scrollbar(token_frame, command=self.token_output.yview)
        token_scroll.grid(row=0, column=1, sticky="ns")
        self.token_output.config(yscrollcommand=token_scroll.set)

        # ---- 标签2：语法分析（含滚动条） ----
        self.ast_raw_tab = self.result_tabs.add("语法分析")
        ast_frame = tk.Frame(self.ast_raw_tab, bg="#262626")
        ast_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ast_frame.grid_rowconfigure(0, weight=1)
        ast_frame.grid_columnconfigure(0, weight=1)

        self.ast_output = tk.Text(ast_frame, bg="#262626", fg="white",
                                  insertbackground="white", font=("Courier", 10), state="disabled")
        self.ast_output.grid(row=0, column=0, sticky="nsew")
        ast_scroll = tk.Scrollbar(ast_frame, command=self.ast_output.yview)
        ast_scroll.grid(row=0, column=1, sticky="ns")
        self.ast_output.config(yscrollcommand=ast_scroll.set)

        # ---- 标签3：AST 可视化 ----
        self.ast_tab = self.result_tabs.add("AST 可视化")
        self.ast_canvas = tk.Canvas(self.ast_tab, bg="#262626")
        self.ast_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 拖动 + 缩放功能绑定
        self.ast_canvas.bind("<ButtonPress-1>", self.start_move)
        self.ast_canvas.bind("<B1-Motion>", self.do_move)
        self.ast_canvas.bind("<MouseWheel>", self.zoom)
        self._drag_data = {"x": 0, "y": 0}

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Rust-like Source", "*.rs")])
        if file_path:
            with open(file_path, encoding="utf-8") as f:
                self.code_input.delete("1.0", tk.END)
                self.code_input.insert("end", f.read())

    def run_analysis(self):
        code = self.code_input.get("1.0", tk.END).strip()
        with open("temp_test.rs", "w", encoding="utf-8") as f:
            f.write(code)

        self.token_output.config(state="normal")
        self.token_output.delete("1.0", tk.END)
        self.token_output.config(state="disabled")

        self.ast_output.config(state="normal")
        self.ast_output.delete("1.0", tk.END)
        self.ast_output.config(state="disabled")

        self.ast_canvas.delete("all")

        try:
            # 词法分析
            tokens = tokenize_file("temp_test.rs")
            self.token_output.config(state="normal")
            for t in tokens:
                self.token_output.insert("end", f"{t}\n")
            self.token_output.config(state="disabled")

            # 语法分析生成 AST
            parser = LR1Parser()
            ast = parser.parse(tokens)

            semantic_errors = run_semantic_checks(ast)
            if semantic_errors:
                messagebox.showerror("语义错误", "\n".join(semantic_errors))
                return

            self.ast_output.config(state="normal")
            self.ast_output.insert("end", str(ast))
            self.ast_output.config(state="disabled")

            # 生成AST图
            dot = ast.graphviz()
            dot.attr(rankdir='TB')
            dot.render('ast_graph', format='png', cleanup=True)

            # 打开原始图像
            img = Image.open('ast_graph.png')
            self.original_image = img

            canvas_width = self.ast_canvas.winfo_width()
            canvas_height = self.ast_canvas.winfo_height()
            if canvas_width == 1 or canvas_height == 1:
                canvas_width, canvas_height = 800, 600

            ratio = min(canvas_width / img.width, canvas_height / img.height)
            self.zoom_ratio = ratio

            resized_img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_img)

            self.ast_canvas.create_image(0, 0, image=self.photo, anchor="nw", tags="ast_image")
            self.ast_canvas.config(scrollregion=self.ast_canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("分析错误", traceback.format_exc())

    def start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.ast_canvas.move("ast_image", dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def zoom(self, event):
        if self.original_image is None:
            return

        if event.delta > 0:
            self.zoom_ratio *= 1.1
        else:
            self.zoom_ratio /= 1.1

        img = self.original_image
        new_size = (int(img.width * self.zoom_ratio), int(img.height * self.zoom_ratio))
        resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

        self.photo = ImageTk.PhotoImage(resized_img)
        self.ast_canvas.delete("all")
        self.ast_canvas.create_image(0, 0, image=self.photo, anchor="nw", tags="ast_image")
        self.ast_canvas.config(scrollregion=self.ast_canvas.bbox("all"))

if __name__ == "__main__":
    app = CompilerApp()
    app.mainloop()
