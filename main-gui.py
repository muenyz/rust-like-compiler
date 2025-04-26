import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from lr1_parser import LR1Parser
from lexer import tokenize_file

class CompilerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Rust-like Compiler GUI")
        self.geometry("1000x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Layout setup
        self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=3)
        self.grid_columnconfigure(0, weight=1)

        # ===== 顶部按钮栏 =====
        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(top_bar, text="打开文件", command=self.load_file).grid(row=0, column=0, padx=10)
        ctk.CTkButton(top_bar, text="开始分析", command=self.run_analysis).grid(row=0, column=1, padx=10)

        self.appearance_option = ctk.CTkOptionMenu(top_bar, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode)
        self.appearance_option.set("Dark")
        self.appearance_option.grid(row=0, column=2, sticky="e", padx=10)

        # ===== 代码输入区域 =====
        self.code_input = tk.Text(self, bg="#1e1e1e", fg="white", insertbackground="white", font=("Courier", 11))
        self.code_input.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # ===== 输出区域 =====
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        output_frame.grid_rowconfigure((1, 3), weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(output_frame, text="词法分析结果").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.token_output = tk.Text(output_frame, bg="#262626", fg="white", insertbackground="white", font=("Courier", 10))
        self.token_output.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        ctk.CTkLabel(output_frame, text="AST 输出结果").grid(row=2, column=0, sticky="w", padx=10)
        self.ast_output = tk.Text(output_frame, bg="#262626", fg="white", insertbackground="white", font=("Courier", 10))
        self.ast_output.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

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

        self.token_output.delete("1.0", tk.END)
        self.ast_output.delete("1.0", tk.END)

        try:
            tokens = tokenize_file("temp_test.rs")
            for t in tokens:
                self.token_output.insert("end", f"{t}\n")

        except Exception as e:
            messagebox.showerror("分析错误", str(e))

if __name__ == "__main__":
    app = CompilerApp()
    app.mainloop()