import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, colorchooser, simpledialog
import os
import json
from datetime import datetime
import tkinter.font as tkfont
import re
import webbrowser

import pystray
from PIL import Image, ImageDraw


class Notepad:
    def __init__(self, root):
        self.root = root
        self.root.title("Untitled - Notepad")
        self.root.geometry("900x700")
        
        # Load settings (theme, etc.)
        self.settings_file = "notepad_settings.json"
        self.load_settings()
        
        # Text area
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, undo=True, font=(self.current_font_family, self.current_font_size)
        )
        self.text_area.pack(expand=True, fill=tk.BOTH)
        
        self.file_path = None
        self.last_saved_content = "" # For auto-save detection
        
        # Configure rich text tags
        self.configure_tags()
        
        self.line_numbers_var = tk.BooleanVar(value=True)
        self.syntax_var = tk.BooleanVar(value=False)
        self.create_menu()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ln 1, Col 1", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Right-click context menu
        self.create_context_menu()
        
        # Bind events
        self.text_area.bind("<KeyRelease>", self.update_status)
        self.text_area.bind("<ButtonRelease-1>", self.update_status)
        self.text_area.bind("<Button-3>", self.show_context_menu)
        
        # Key bindings
        self.bind_shortcuts()
        
        # Auto-save every 30 seconds
        self.auto_save_interval = 30000 # ms
        self.root.after(self.auto_save_interval, self.auto_save)
        
        # Theme
        self.apply_theme()
        
        # New features
        self.recent_files = []
        self.zoom_level = 100
        self.tabs = []  # For multiple tabs
        self.current_tab = None
        self.setup_tabs()
        self.setup_line_numbers()
        self.setup_syntax_highlighting()
        self.bind_auto_indent()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Tray (system tray icon)
        self.tray_icon = None
        self.setup_tray()
    
    def load_settings(self):
        """Load user settings like theme and font"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.current_theme = settings.get('theme', 'light')
                    self.current_font_family = settings.get('font_family', 'Consolas')
                    self.current_font_size = settings.get('font_size', 11)
                    self.recent_files = settings.get('recent_files', [])[:8]
            else:
                self.current_theme = 'light'
                self.current_font_family = 'Consolas'
                self.current_font_size = 11
                self.recent_files = []
        except:
            self.current_theme = 'light'
            self.current_font_family = 'Consolas'
            self.current_font_size = 11
            self.recent_files = []
    
    def save_settings(self):
        """Save user settings"""
        try:
            settings = {
                'theme': self.current_theme,
                'font_family': self.current_font_family,
                'font_size': self.current_font_size,
                'recent_files': self.recent_files[:8]
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def configure_tags(self):
        """Configure default tags"""
        self.text_area.tag_configure("bold", font=(self.current_font_family, self.current_font_size, "bold"))
        self.text_area.tag_configure("italic", font=(self.current_font_family, self.current_font_size, "italic"))
        self.text_area.tag_configure("underline", underline=True)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_as_file)
        
        # Recent Files
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self.update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Export to HTML", command=self.export_to_html)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_command(label="Delete", accelerator="Del", command=self.delete)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_replace_dialog)
        edit_menu.add_command(label="Replace...", command=self.find_replace_dialog)
        
        # Format menu
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        self.word_wrap_var = tk.BooleanVar(value=True)
        format_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var, command=self.toggle_word_wrap)
        format_menu.add_separator()
        
        format_menu.add_command(label="Bold", accelerator="Ctrl+B", command=self.toggle_bold)
        format_menu.add_command(label="Italic", accelerator="Ctrl+I", command=self.toggle_italic)
        format_menu.add_command(label="Underline", accelerator="Ctrl+U", command=self.toggle_underline)
        format_menu.add_separator()
        
        format_menu.add_command(label="Text Color...", command=self.choose_fg_color)
        format_menu.add_command(label="Background Color...", command=self.choose_bg_color)
        format_menu.add_command(label="Reset Formatting", command=self.reset_formatting)
        format_menu.add_separator()
        
        # Font size submenu
        font_menu = tk.Menu(format_menu, tearoff=0)
        format_menu.add_cascade(label="Font Size", menu=font_menu)
        for size in [8, 10, 11, 12, 14, 16, 18, 20, 24]:
            font_menu.add_command(label=str(size), command=lambda s=size: self.change_font_size(s))
        
        # Zoom
        format_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.zoom_in)
        format_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)
        format_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        
        # Theme submenu
        theme_menu = tk.Menu(format_menu, tearoff=0)
        format_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light", command=lambda: self.set_theme('light'))
        theme_menu.add_command(label="Dark", command=lambda: self.set_theme('dark'))
        theme_menu.add_command(label="Solarized Dark", command=lambda: self.set_theme('solarized'))
        
        # View menu for line numbers and syntax
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        self.line_numbers_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.line_numbers_var, command=self.toggle_line_numbers)
        self.syntax_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="Syntax Highlighting (Python/MD)", variable=self.syntax_var, command=self.toggle_syntax)
    
    def update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for file in self.recent_files:
            self.recent_menu.add_command(label=os.path.basename(file), command=lambda f=file: self.open_recent(f))
    
    def add_to_recent(self, filepath):
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:8]
        self.update_recent_menu()
        self.save_settings()
    
    def open_recent(self, filepath):
        if self.check_unsaved(): return
        self.file_path = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.text_area.delete("1.0", tk.END)
            if isinstance(data, dict) and "content_dump" in data:
                self.load_dump(data["content_dump"])
            else:
                self.text_area.insert(tk.END, data if isinstance(data, str) else str(data))
            self.root.title(os.path.basename(filepath) + " - Notepad")
            self.last_saved_content = self.text_area.get("1.0", tk.END)
            self.add_to_recent(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut)
        self.context_menu.add_command(label="Copy", command=self.copy)
        self.context_menu.add_command(label="Paste", command=self.paste)
        self.context_menu.add_command(label="Delete", command=self.delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Bold", command=self.toggle_bold)
        self.context_menu.add_command(label="Italic", command=self.toggle_italic)
        self.context_menu.add_command(label="Underline", command=self.toggle_underline)
    
    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def bind_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-b>", lambda e: self.toggle_bold())
        self.root.bind("<Control-i>", lambda e: self.toggle_italic())
        self.root.bind("<Control-u>", lambda e: self.toggle_underline())
        self.root.bind("<Control-f>", lambda e: self.find_replace_dialog())
        self.root.bind("<Control-plus>", self.zoom_in)
        self.root.bind("<Control-minus>", self.zoom_out)
        self.root.bind("<Control-MouseWheel>", self.on_mousewheel_zoom)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    # ====================== RICH TEXT SAVE/LOAD ======================
    def save_file(self):
        if not self.file_path:
            self.save_as_file()
            return
        self._save_to_file(self.file_path)
    
    def save_as_file(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".ntd",
            filetypes=[("Notepad Rich Text", "*.ntd"), ("All Files", "*.*")]
        )
        if file:
            if not file.endswith('.ntd'):
                file += '.ntd'
            self.file_path = file
            self._save_to_file(file)
    
    def _save_to_file(self, filepath):
        try:
            # Dump content with tags
            content_dump = self.text_area.dump("1.0", tk.END, text=True, tag=True, mark=False)
            data = {
                "content_dump": content_dump,
                "saved_at": datetime.now().isoformat()
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.root.title(os.path.basename(filepath) + " - Notepad")
            self.last_saved_content = self.text_area.get("1.0", tk.END)
            self.add_to_recent(filepath)
            messagebox.showinfo("Saved", f"File saved successfully with formatting!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def open_file(self):
        if self.check_unsaved(): return
        file = filedialog.askopenfilename(
            defaultextension=".ntd",
            filetypes=[("Notepad Rich Text", "*.ntd"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file:
            self.file_path = file
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.text_area.delete("1.0", tk.END)
                
                if isinstance(data, dict) and "content_dump" in data:
                    # Rich text load
                    self.load_dump(data["content_dump"])
                else:
                    # Plain text fallback
                    self.text_area.insert(tk.END, data if isinstance(data, str) else str(data))
                
                self.root.title(os.path.basename(file) + " - Notepad")
                self.last_saved_content = self.text_area.get("1.0", tk.END)
                self.add_to_recent(file)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def load_dump(self, dump_data):
        """Reconstruct text widget from dump data"""
        current_tags = []
        i = 0
        while i < len(dump_data):
            key, value, index = dump_data[i]
            if key == "text":
                self.text_area.insert(index, value, tuple(current_tags))
            elif key == "tagon":
                if value not in current_tags:
                    current_tags.append(value)
            elif key == "tagoff":
                if value in current_tags:
                    current_tags.remove(value)
            i += 1
    
    # ====================== FORMATTING ======================
    def toggle_bold(self): self.toggle_tag("bold")
    def toggle_italic(self): self.toggle_tag("italic")
    def toggle_underline(self): self.toggle_tag("underline")
    
    def toggle_tag(self, tag_name):
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
            if tag_name in self.text_area.tag_names(start):
                self.text_area.tag_remove(tag_name, start, end)
            else:
                self.text_area.tag_add(tag_name, start, end)
        except tk.TclError:
            pass
    
    def choose_fg_color(self):
        color = colorchooser.askcolor(title="Choose Text Color")[1]
        if color:
            self.apply_color_tag("fg", color)
    
    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")[1]
        if color:
            self.apply_color_tag("bg", color, is_bg=True)
    
    def apply_color_tag(self, tag_base, color, is_bg=False):
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
            tag_name = f"{tag_base}*{color.replace('#', '')}"
            
            if is_bg:
                self.text_area.tag_configure(tag_name, background=color)
            else:
                self.text_area.tag_configure(tag_name, foreground=color)
            
            # Remove old color tags
            for tag in list(self.text_area.tag_names(start)):
                if tag.startswith(tag_base):
                    self.text_area.tag_remove(tag, start, end)
            
            self.text_area.tag_add(tag_name, start, end)
        except tk.TclError:
            pass
    
    def reset_formatting(self):
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
            for tag in list(self.text_area.tag_names(start)):
                self.text_area.tag_remove(tag, start, end)
        except tk.TclError:
            pass
    
    def change_font_size(self, size):
        self.current_font_size = size
        new_font = (self.current_font_family, size)
        self.text_area.configure(font=new_font)
        # Reconfigure tags
        self.configure_tags()
        self.save_settings()
    
    def set_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()
        self.save_settings()
    
    def apply_theme(self):
        if self.current_theme == 'dark':
            bg = '#1e1e1e'
            fg = '#d4d4d4'
            select_bg = '#264f78'
        elif self.current_theme == 'solarized':
            bg = '#002b36'
            fg = '#839496'
            select_bg = '#268bd2'
        else: # light
            bg = 'white'
            fg = 'black'
            select_bg = '#c1d2ff'
        
        self.text_area.configure(bg=bg, fg=fg, insertbackground=fg, selectbackground=select_bg)
        self.status_bar.configure(bg='#f0f0f0' if self.current_theme == 'light' else '#333333', fg='black' if self.current_theme == 'light' else 'white')
    
    # ====================== NEW FEATURES ======================
    
    def setup_line_numbers(self):
        self.line_numbers = tk.Text(self.root, width=4, padx=4, takefocus=0, fg='gray', bg='lightgray', state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.text_area.bind('<KeyRelease>', self.update_line_numbers)
        self.text_area.bind('<ButtonRelease-1>', self.update_line_numbers)
        self.text_area.bind('<MouseWheel>', self.update_line_numbers)
        self.update_line_numbers()
    
    def toggle_line_numbers(self):
        if self.line_numbers_var.get():
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        else:
            self.line_numbers.pack_forget()
        self.update_line_numbers()
    
    def update_line_numbers(self, event=None):
        if not self.line_numbers_var.get():
            return
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        line_count = int(self.text_area.index('end-1c').split('.')[0])
        line_nums = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_nums)
        self.line_numbers.config(state='disabled')
    
    def setup_syntax_highlighting(self):
        self.syntax_tags = {}
        # Basic Python/Markdown tags
        self.text_area.tag_configure("keyword", foreground="blue")
        self.text_area.tag_configure("string", foreground="green")
        self.text_area.tag_configure("comment", foreground="gray")
    
    def toggle_syntax(self):
        if self.syntax_var.get():
            self.text_area.bind('<KeyRelease>', self.apply_syntax_highlighting)
        else:
            self.text_area.unbind('<KeyRelease>')
            # Remove tags
            for tag in ["keyword", "string", "comment"]:
                self.text_area.tag_remove(tag, "1.0", tk.END)
    
    def apply_syntax_highlighting(self, event=None):
        if not self.syntax_var.get():
            return
        # Basic implementation - simple regex for demo
        content = self.text_area.get("1.0", tk.END)
        # Remove previous
        for tag in ["keyword", "string", "comment"]:
            self.text_area.tag_remove(tag, "1.0", tk.END)
        # Very basic - keywords
        keywords = ["def", "class", "import", "if", "else", "for", "while"]
        for kw in keywords:
            for match in re.finditer(r'\b' + kw + r'\b', content):
                start = self.text_area.search(kw, "1.0", tk.END, regexp=True)
                if start:
                    end = f"{start}+{len(kw)}c"
                    self.text_area.tag_add("keyword", start, end)
        # TODO: expand for full highlighting if needed
    
    def zoom_in(self, event=None):
        self.current_font_size = min(48, self.current_font_size + 2)
        self.text_area.configure(font=(self.current_font_family, self.current_font_size))
        self.configure_tags()
        self.update_status()
    
    def zoom_out(self, event=None):
        self.current_font_size = max(6, self.current_font_size - 2)
        self.text_area.configure(font=(self.current_font_family, self.current_font_size))
        self.configure_tags()
        self.update_status()
    
    def reset_zoom(self):
        self.current_font_size = 11
        self.text_area.configure(font=(self.current_font_family, self.current_font_size))
        self.configure_tags()
    
    def on_mousewheel_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def update_status(self, event=None):
        line, col = self.text_area.index(tk.INSERT).split('.')
        word_count = len(self.text_area.get("1.0", tk.END).split())
        self.status_bar.config(text=f"Ln {line}, Col {int(col)+1} | Words: {word_count} | {self.current_theme.title()} Theme")
        self.update_line_numbers()
    
    # Auto-indent
    def bind_auto_indent(self):
        self.text_area.bind("<Return>", self.auto_indent)
    
    def auto_indent(self, event):
        # Get current line indentation
        current_line = self.text_area.get("insert linestart", "insert")
        indent = len(current_line) - len(current_line.lstrip())
        self.text_area.insert("insert", "\n" + " " * indent)
        return "break"
    
    # Find & Replace
    def find_replace_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Find & Replace")
        tk.Label(dialog, text="Find:").grid(row=0, column=0, padx=5, pady=5)
        find_entry = tk.Entry(dialog, width=30)
        find_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(dialog, text="Replace:").grid(row=1, column=0, padx=5, pady=5)
        replace_entry = tk.Entry(dialog, width=30)
        replace_entry.grid(row=1, column=1, padx=5, pady=5)
        
        regex_var = tk.BooleanVar()
        tk.Checkbutton(dialog, text="Regex", variable=regex_var).grid(row=2, column=1)
        
        def do_find():
            self.text_area.tag_remove("sel", "1.0", tk.END)
            term = find_entry.get()
            if not term: return
            start_pos = self.text_area.search(term, "1.0", tk.END, nocase=True, regexp=regex_var.get())
            if start_pos:
                end_pos = f"{start_pos}+{len(term)}c" if not regex_var.get() else self.text_area.search(term, start_pos, tk.END, regexp=True, count=1)[0] + "c"
                self.text_area.tag_add("sel", start_pos, end_pos)
                self.text_area.see(start_pos)
        
        def do_replace():
            term = find_entry.get()
            repl = replace_entry.get()
            if not term: return
            content = self.text_area.get("1.0", tk.END)
            if regex_var.get():
                new_content = re.sub(term, repl, content)
            else:
                new_content = content.replace(term, repl)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", new_content)
        
        tk.Button(dialog, text="Find", command=do_find).grid(row=3, column=0, pady=10)
        tk.Button(dialog, text="Replace All", command=do_replace).grid(row=3, column=1, pady=10)
    
    def export_to_html(self):
        if not self.text_area.get("1.0", tk.END).strip():
            messagebox.showwarning("Empty", "Nothing to export")
            return
        file = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if file:
            try:
                content = self.text_area.get("1.0", tk.END)
                # Basic HTML with some formatting (tags not fully preserved for simplicity)
                html = f"""<html><head><title>Exported Note</title><style>body {{font-family: {self.current_font_family};}}</style></head><body><pre>{content}</pre></body></html>"""
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(html)
                messagebox.showinfo("Exported", "Note exported to HTML successfully!")
                webbrowser.open(file)
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    # Tabs support - basic
    def setup_tabs(self):
        # Basic tabs placeholder - full multi-tab requires more refactoring.
        # For now keeping single document to avoid breaking original functionality.
        pass
    
    def create_new_tab(self):
        frame = tk.Frame(self.notebook)
        text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, undo=True, font=(self.current_font_family, self.current_font_size))
        text_area.pack(expand=True, fill=tk.BOTH)
        self.notebook.add(frame, text="Untitled")
        self.tabs.append((frame, text_area))
        self.notebook.select(frame)
        # Bind events to new text_area etc. - simplified for base
    
    # ====================== TRAY ICON ======================
    def create_tray_image(self):
        image = Image.new('RGB', (64, 64), color='#1e90ff')
        dc = ImageDraw.Draw(image)
        dc.rectangle([8, 8, 56, 56], fill='white', outline='black', width=4)
        dc.line([15, 20, 49, 20], fill='black', width=3)
        dc.line([15, 30, 49, 30], fill='black', width=3)
        dc.line([15, 40, 49, 40], fill='black', width=3)
        return image

    def setup_tray(self):
        # Original binding kept + new tray support
        self.root.bind("<Unmap>", self.minimize_to_tray)

    def minimize_to_tray(self, event=None):
        if self.root.state() == 'iconic' or event is None:  # Support both minimize and close
            self.root.withdraw()
            
            menu = (
                pystray.MenuItem('Show', self.show_window, default=True),
                pystray.MenuItem('New File', lambda: self.root.after(0, self.new_file)),
                pystray.MenuItem('Save', lambda: self.root.after(0, self.save_file)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('Quit', self.quit_app)
            )

            self.tray_icon = pystray.Icon(
                name="Notepad",
                icon=self.create_tray_image(),
                title="Enhanced Notepad",
                menu=menu
            )
            self.tray_icon.run_detached()

    def show_window(self, icon=None, item=None):
        if icon:
            icon.stop()
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def quit_app(self, icon=None, item=None):
        if icon:
            icon.stop()
        self.root.after(0, self.on_closing)

    # ====================== AUTO-SAVE & OTHER ======================
    def auto_save(self):
        if self.file_path and self.text_area.get("1.0", tk.END).strip() != self.last_saved_content.strip():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.file_path.replace('.ntd', f'_backup_{timestamp}.ntd')
                self._save_to_file(backup_path)
                print(f"Auto-backup saved: {backup_path}")
            except: pass
        self.root.after(self.auto_save_interval, self.auto_save)
    
    def find_text(self):  # Kept for org
        # Simple find dialog - now redirected
        self.find_replace_dialog()
    
    def new_file(self):
        if self.check_unsaved(): return
        self.text_area.delete("1.0", tk.END)
        self.file_path = None
        self.root.title("Untitled - Notepad")
        self.last_saved_content = ""
    
    def check_unsaved(self):
        current = self.text_area.get("1.0", tk.END).strip()
        if current and current != self.last_saved_content.strip():
            response = messagebox.askyesnocancel("Notepad", "Do you want to save changes?")
            if response:
                self.save_file()
                return False
            elif response is None:
                return True
        return False
    
    def on_closing(self):
        if self.check_unsaved():
            return
        self.save_settings()
        self.root.destroy()
    
    # Other methods remain mostly unchanged
    def toggle_word_wrap(self):
        if self.word_wrap_var.get():
            self.text_area.config(wrap=tk.WORD)
        else:
            self.text_area.config(wrap=tk.NONE)
    
    def undo(self):
        try: self.text_area.edit_undo()
        except: pass
    
    def cut(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST))
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except: pass
    
    def copy(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST))
        except: pass
    
    def paste(self):
        try:
            self.text_area.insert(tk.INSERT, self.root.clipboard_get())
        except: pass
    
    def delete(self):
        try:
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except: pass
    
    def select_all(self):
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, tk.END)
    
    def about(self):
        messagebox.showinfo("About Notepad", "Enhanced Rich Notepad\nRich text support (.ntd)\nThemes + Auto-backup\nBuilt with Tkinter")

if __name__ == "__main__":
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()