import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from lr1_parser import LR1Parser
from lexer import tokenize_file, Lexer, TokenKind
from PIL import Image, ImageTk
#from semantic_checker import run_semantic_checks
from semantic_checker import SemanticChecker, SemanticError
import traceback
from ir_generator import IRGenerator
from tkinter import ttk

TOKEN_COLORS = {
    'KEYWORD': '#cc7832',
    'IDENT': 'white',
    'NUMBER': '#6897bb',
    'OP': '#a9b7c6',
    'DELIM': '#a9b7c6',
    'ERROR': '#ff0000',
    'COMMENT': '#629755'
}

class CompilerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rust-like Compiler GUI")
        self.geometry("1400x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.original_image = None
        self.zoom_ratio = 1.0
        self.current_file_path = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_file())
        self.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.bind("<Control-o>", lambda e: self.load_file())
        self.bind("<Control-O>", lambda e: self.load_file())

        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        top_bar.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(top_bar, text="打开文件", command=self.load_file).grid(row=0, column=0, padx=10)
        ctk.CTkButton(top_bar, text="保存", command=self.save_file).grid(row=0, column=1, padx=10)
        ctk.CTkButton(top_bar, text="另存为", command=self.save_file_as).grid(row=0, column=2, padx=10)
        ctk.CTkButton(top_bar, text="开始分析", command=self.run_analysis).grid(row=0, column=3, padx=10)

        self.appearance_option = ctk.CTkOptionMenu(top_bar, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode)
        self.appearance_option.set("Dark")
        self.appearance_option.grid(row=0, column=4, sticky="e", padx=10)

        code_frame = tk.Frame(self, bg="#1e1e1e")
        code_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        code_frame.grid_rowconfigure(0, weight=1)
        code_frame.grid_columnconfigure(0, weight=1)

        self.code_input = tk.Text(code_frame, bg="#1e1e1e", fg="white", insertbackground="white", font=("Courier", 11), undo=True)
        self.code_input.grid(row=0, column=0, sticky="nsew")
        code_scroll = tk.Scrollbar(code_frame, command=self.code_input.yview)
        code_scroll.grid(row=0, column=1, sticky="ns")
        self.code_input.config(yscrollcommand=code_scroll.set)
        self.code_input.bind("<KeyRelease>", lambda e: self.highlight_code())

        self.result_tabs = ctk.CTkTabview(self)
        self.result_tabs.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

        self.token_tab = self.result_tabs.add("词法分析")
        token_frame = tk.Frame(self.token_tab, bg="#262626")
        token_frame.pack(fill="both", expand=True, padx=10, pady=10)
        token_frame.grid_rowconfigure(0, weight=1)
        token_frame.grid_columnconfigure(0, weight=1)

        self.token_output = tk.Text(token_frame, bg="#262626", fg="white", insertbackground="white",
                                    font=("Courier", 10), state="disabled", wrap="none")  # ← 加 wrap="none" 禁用自动换行
        self.token_output.grid(row=0, column=0, sticky="nsew")

        token_scroll_y = tk.Scrollbar(token_frame, command=self.token_output.yview)
        token_scroll_y.grid(row=0, column=1, sticky="ns")

        token_scroll_x = tk.Scrollbar(token_frame, orient="horizontal", command=self.token_output.xview)
        token_scroll_x.grid(row=1, column=0, sticky="ew")

        self.token_output.config(yscrollcommand=token_scroll_y.set, xscrollcommand=token_scroll_x.set)

        self.ast_tab = self.result_tabs.add("AST 可视化")
        self.ast_canvas = tk.Canvas(self.ast_tab, bg="#262626")
        self.ast_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.ast_canvas.bind("<ButtonPress-1>", self.start_move)
        self.ast_canvas.bind("<B1-Motion>", self.do_move)
        self.ast_canvas.bind("<MouseWheel>", self.zoom)
        self._drag_data = {"x": 0, "y": 0}

        self.reduction_tab = self.result_tabs.add("归约过程")
        reduction_frame = tk.Frame(self.reduction_tab, bg="#262626")
        reduction_frame.pack(fill="both", expand=True, padx=10, pady=10)
        reduction_frame.grid_rowconfigure(0, weight=1)
        reduction_frame.grid_columnconfigure(0, weight=1)

        self.reduction_table = ttk.Treeview(
            reduction_frame,
            columns=("state",  "input", "action"),
            show="headings"
        )
        self.reduction_table.heading("state", text="状态栈")
        self.reduction_table.heading("input", text="输入串")
        self.reduction_table.heading("action", text="动作")
        self.reduction_table.column("state", width=140)
        self.reduction_table.column("input", width=400)  # 可以加宽一些
        self.reduction_table.column("action", width=180)
        self.reduction_table.grid(row=0, column=0, sticky="nsew")

        self.ir_tab = self.result_tabs.add("中间代码")
        ir_frame = tk.Frame(self.ir_tab, bg="#262626")
        ir_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ir_frame.grid_rowconfigure(0, weight=1)
        ir_frame.grid_columnconfigure(0, weight=1)

        self.ir_table = ttk.Treeview(
            ir_frame,
            columns=("op", "arg1", "arg2", "result"),
            show="headings"
        )
        self.ir_table.heading("op", text="操作")
        self.ir_table.heading("arg1", text="参数1")
        self.ir_table.heading("arg2", text="参数2")
        self.ir_table.heading("result", text="结果")

        self.ir_table.column("op", width=100)
        self.ir_table.column("arg1", width=120)
        self.ir_table.column("arg2", width=120)
        self.ir_table.column("result", width=150)
        self.ir_table.grid(row=0, column=0, sticky="nsew")

        scroll_y = tk.Scrollbar(reduction_frame, command=self.reduction_table.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")

        scroll_x = tk.Scrollbar(reduction_frame, orient="horizontal", command=self.reduction_table.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.reduction_table.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)


        for kind in TokenKind:
            self.code_input.tag_config(kind.name, foreground=TOKEN_COLORS.get(kind.name, "white"))

    def highlight_code(self):
        code = self.code_input.get("1.0", "end-1c")
        lexer = Lexer(code)
        tokens = []
        while True:
            tok = lexer.next_token()
            if tok.kind == TokenKind.EOF:
                break
            tokens.append(tok)

        for kind in TokenKind:
            self.code_input.tag_remove(kind.name, "1.0", "end")

        for token in tokens:
            start = f"{token.line}.{token.col - 1}"
            end = f"{token.line}.{token.col - 1 + len(token.value)}"
            self.code_input.tag_add(token.kind.name, start, end)

        self.highlight_comments(code)

    def highlight_comments(self, code):
        self.code_input.tag_remove("COMMENT", "1.0", "end")
        lines = code.split('\n')
        for lineno, line in enumerate(lines, start=1):
            idx = line.find("//")
            if idx != -1:
                start = f"{lineno}.{idx}"
                end = f"{lineno}.{len(line)}"
                self.code_input.tag_add("COMMENT", start, end)
        self.code_input.tag_config("COMMENT", foreground=TOKEN_COLORS["COMMENT"])

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Rust-like Source", "*.rs")])
        if file_path:
            with open(file_path, encoding="utf-8") as f:
                self.code_input.delete("1.0", tk.END)
                self.code_input.insert("end", f.read())
            self.current_file_path = file_path
            self.highlight_code()

    def save_file(self):
        if self.current_file_path:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.code_input.get("1.0", "end-1c"))
            messagebox.showinfo("保存成功", f"文件已保存到\n{self.current_file_path}")
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".rs", filetypes=[("Rust-like Source", "*.rs")])
        if path:
            self.current_file_path = path
            self.save_file()

    def run_analysis(self):
        code = self.code_input.get("1.0", tk.END).strip()
        with open("temp_test.rs", "w", encoding="utf-8") as f:
            f.write(code)

        self.token_output.config(state="normal")
        self.token_output.delete("1.0", tk.END)
        self.token_output.config(state="disabled")
        self.reduction_table.delete(*self.reduction_table.get_children())
        self.ast_canvas.delete("all")

        try:
        # 词法分析
            tokens = tokenize_file("temp_test.rs")
            self.token_output.config(state="normal")
            for t in tokens:
                self.token_output.insert("end", f"{t}\n")
            self.token_output.config(state="disabled")

        # 语法分析
            parser = LR1Parser()
            parser.reduction_trace = []
            ast = parser.parse(tokens, trace_output=parser.reduction_trace)

            for row in parser.reduction_trace:
                self.reduction_table.insert("", "end", values=(
                    ",".join(map(str, row["state"])),
                    " ".join(row["input"]),
                    row["action"]
                ))
            self.reduction_table.update_idletasks()

        # === 语义分析 ===
            checker = SemanticChecker()
            checker.check(ast)
            print("语义检查通过！")


        # === 中间代码生成 ===
            irgen = IRGenerator()
            irgen.generate(ast)
            ir_output = irgen.code
            # 清空旧表格内容
            self.ir_table.delete(*self.ir_table.get_children())

            # 插入新四元组数据
            for quad in ir_output:
                op, arg1, arg2, res = quad
                self.ir_table.insert("", "end", values=(op, arg1, arg2, res))

            self.ir_table.update_idletasks()


        # AST 图可视化
            dot = ast.graphviz()
            dot.attr(rankdir='TB')
            dot.render('ast_graph', format='png', cleanup=True)

            img = Image.open('ast_graph.png')
            self.original_image = img
            w, h = self.ast_canvas.winfo_width(), self.ast_canvas.winfo_height()
            if w <= 1 or h <= 1:
                w, h = 800, 600
            ratio = min(w / img.width, h / img.height)
            self.zoom_ratio = ratio

            resized_img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_img)
            self.ast_canvas.create_image(0, 0, image=self.photo, anchor="nw", tags="ast_image")
            self.ast_canvas.config(scrollregion=self.ast_canvas.bbox("all"))

            self.highlight_code()

        except (SemanticError, SyntaxError) as e:
            messagebox.showerror("分析错误", f"发生了一个错误：\n{str(e)}")
        except Exception:
            messagebox.showerror("分析错误", "发生了一个未知错误，请检查代码。\n\n" + traceback.format_exc())

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
