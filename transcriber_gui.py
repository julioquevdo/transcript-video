import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import subprocess
import time
from pathlib import Path
import json
import shutil
from datetime import datetime

try:
    from video_transcriber import (
        extract_speech_from_video, 
        download_youtube_video, 
        create_video_folder
    )
except ImportError:
    messagebox.showerror("Erro", "O arquivo video_transcriber.py não foi encontrado. Por favor, certifique-se de que ele está no mesmo diretório que este script.")
    sys.exit(1)

class VideoTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Texto de Vídeos")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        self.style.configure("TButton", padding=6, relief="flat", background="#4a7abc")
        self.style.configure("Accent.TButton", background="#47a447", foreground="white")
        self.style.configure("Danger.TButton", background="#d9534f", foreground="white")
        self.style.map('TButton', background=[('active', '#5a8ac9')])
        self.style.map('Accent.TButton', background=[('active', '#57b457')])
        self.style.map('Danger.TButton', background=[('active', '#e9635f')])
        
        self.video_path = tk.StringVar()
        self.youtube_url = tk.StringVar()
        self.output_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.language = tk.StringVar(value="pt-BR")
        self.chunk_size = tk.IntVar(value=30)
        self.input_mode = tk.StringVar(value="youtube")
        
        self.processing_thread = None
        self.is_processing = False
        self.download_progress = 0
        self.transcription_progress = 0
        self.current_folder = None
        
        self.create_widgets()
        
        if not os.path.exists("videos"):
            os.makedirs("videos")
            
        self.output_folder.set(os.path.abspath("videos"))
        
        self.update_ui_for_mode()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(
            title_frame, 
            text="Extrator de Texto de Vídeos", 
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(side=tk.TOP, anchor=tk.W)
        
        desc_label = ttk.Label(
            title_frame, 
            text="Extraia texto de vídeos locais ou do YouTube usando reconhecimento de fala.",
            font=("Helvetica", 10),
            foreground="#555555"
        )
        desc_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 10))
        
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.X, pady=10)
        
        youtube_tab = ttk.Frame(notebook, padding=10)
        notebook.add(youtube_tab, text=" YouTube ", underline=0)
        
        file_tab = ttk.Frame(notebook, padding=10)
        notebook.add(file_tab, text=" Arquivo Local ", underline=0)
        
        self.create_youtube_tab(youtube_tab)
        
        self.create_file_tab(file_tab)
        
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_grid, text="Idioma:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        language_frame = ttk.Frame(config_grid)
        language_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        language_combobox = ttk.Combobox(language_frame, textvariable=self.language, width=15)
        language_combobox['values'] = (
            'pt-BR (Português)', 
            'en-US (Inglês)', 
            'es-ES (Espanhol)', 
            'fr-FR (Francês)', 
            'de-DE (Alemão)', 
            'it-IT (Italiano)', 
            'ja-JP (Japonês)', 
            'ko-KR (Coreano)', 
            'zh-CN (Chinês)'
        )
        language_combobox.pack(side=tk.LEFT)
        
        language_help = ttk.Label(language_frame, text="?", cursor="hand2", foreground="blue")
        language_help.pack(side=tk.LEFT, padx=5)
        language_help.bind("<Button-1>", lambda e: self.show_tooltip(
            language_help, 
            "Selecione o idioma principal falado no vídeo para melhorar a precisão do reconhecimento de fala."
        ))
        
        ttk.Label(config_grid, text="Tamanho do segmento:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        segment_frame = ttk.Frame(config_grid)
        segment_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        segment_spinbox = ttk.Spinbox(segment_frame, from_=5, to=60, textvariable=self.chunk_size, width=5)
        segment_spinbox.pack(side=tk.LEFT)
        
        ttk.Label(segment_frame, text="segundos").pack(side=tk.LEFT, padx=(5, 10))
        
        segment_help = ttk.Label(segment_frame, text="?", cursor="hand2", foreground="blue")
        segment_help.pack(side=tk.LEFT)
        segment_help.bind("<Button-1>", lambda e: self.show_segment_help())
        
        ttk.Label(config_grid, text="Pasta de saída:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        output_frame = ttk.Frame(config_grid)
        output_frame.grid(row=2, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Procurar...", command=self.browse_output_folder).pack(side=tk.LEFT, padx=5)
        
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.pack(fill=tk.X, pady=10)
        
        start_big_button_frame = ttk.Frame(main_frame)
        start_big_button_frame.pack(fill=tk.X, pady=15)
        
        self.style.configure("Huge.TButton", 
                            font=("Helvetica", 14, "bold"), 
                            foreground="white",
                            background="#2ecc71", 
                            padding=(20, 15))
        
        self.start_big_button = tk.Button(
            start_big_button_frame, 
            text="▶ INICIAR EXTRAÇÃO",
            command=self.start_processing,
            bg="#2ecc71",
            fg="white",
            font=("Helvetica", 14, "bold"),
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.start_big_button.pack(expand=True, fill=tk.X, padx=50)
        
        separator_after_button = ttk.Separator(main_frame, orient='horizontal')
        separator_after_button.pack(fill=tk.X, pady=10)
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Pronto para processar")
        self.progress_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        
        self.progress_frame_details = ttk.Frame(progress_frame)
        self.progress_frame_details.pack(fill=tk.X)
        
        self.progress_percent = ttk.Label(self.progress_frame_details, text="0%", width=6)
        self.progress_percent.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame_details, orient=tk.HORIZONTAL, mode='determinate', length=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_details = ttk.Label(progress_frame, text="", foreground="#555555", font=("Helvetica", 9))
        self.progress_details.pack(side=tk.TOP, anchor=tk.W, pady=(5, 0))
        
        log_frame = ttk.LabelFrame(main_frame, text="Log de Processamento", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.style.configure("Large.TButton", padding=(15, 10), font=("Helvetica", 11, "bold"))
        self.style.configure("Large.Accent.TButton", padding=(15, 10), font=("Helvetica", 11, "bold"), background="#47a447", foreground="white")
        self.style.configure("Large.Danger.TButton", padding=(15, 10), font=("Helvetica", 11, "bold"), background="#d9534f", foreground="white")
        self.style.map('Large.Accent.TButton', background=[('active', '#57b457')])
        self.style.map('Large.Danger.TButton', background=[('active', '#e9635f')])
        
        separator3 = ttk.Separator(main_frame, orient='horizontal')
        separator3.pack(fill=tk.X, pady=10)
        
        action_label = ttk.Label(
            control_frame, 
            text="Ações:",
            font=("Helvetica", 10, "bold")
        )
        action_label.pack(side=tk.LEFT, padx=(0, 15), pady=5)
        
        self.open_folder_button = ttk.Button(
            control_frame, 
            text="Abrir Pasta de Saída", 
            command=self.open_output_folder,
            width=20,
            state=tk.DISABLED
        )
        self.open_folder_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.cancel_button = ttk.Button(
            control_frame, 
            text="Cancelar", 
            command=self.cancel_processing, 
            state=tk.DISABLED,
            style="Large.Danger.TButton",
            width=15
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        self.start_button = ttk.Button(
            control_frame, 
            text="▶ INICIAR EXTRAÇÃO", 
            command=self.start_processing,
            style="Large.Accent.TButton",
            width=20
        )
        self.start_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def create_youtube_tab(self, parent):
        youtube_frame = ttk.Frame(parent)
        youtube_frame.pack(fill=tk.X, pady=5)
        
        icon_label = ttk.Label(youtube_frame, text="📺", font=("Helvetica", 24))
        icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        
        ttk.Label(
            youtube_frame, 
            text="Insira o URL do vídeo do YouTube que deseja transcrever:",
            font=("Helvetica", 10, "bold")
        ).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(
            youtube_frame, 
            text="O vídeo será baixado automaticamente e o texto extraído.",
            foreground="#555555"
        ).grid(row=1, column=1, sticky=tk.W)
        
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(url_frame, textvariable=self.youtube_url, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        help_button = ttk.Label(url_frame, text="?", cursor="hand2", foreground="blue")
        help_button.pack(side=tk.LEFT, padx=5)
        help_button.bind("<Button-1>", lambda e: self.show_tooltip(
            help_button, 
            "Cole o URL completo do YouTube, exemplo:\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ))
        
        example_frame = ttk.Frame(parent)
        example_frame.pack(fill=tk.X)
        
        ttk.Label(
            example_frame, 
            text="Exemplo: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            foreground="#777777",
            font=("Helvetica", 9, "italic")
        ).pack(side=tk.LEFT)
    
    def create_file_tab(self, parent):
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, pady=5)
        
        icon_label = ttk.Label(file_frame, text="🎬", font=("Helvetica", 24))
        icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        
        ttk.Label(
            file_frame, 
            text="Selecione um arquivo de vídeo do seu computador:",
            font=("Helvetica", 10, "bold")
        ).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(
            file_frame, 
            text="Formatos suportados: MP4, AVI, MKV, WEBM, MOV",
            foreground="#555555"
        ).grid(row=1, column=1, sticky=tk.W)
        
        file_select_frame = ttk.Frame(parent)
        file_select_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(file_select_frame, text="Arquivo:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(file_select_frame, textvariable=self.video_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(file_select_frame, text="Procurar...", command=self.browse_video).pack(side=tk.LEFT)
    
    def on_tab_changed(self, event):
        tab_id = event.widget.index("current")
        
        if tab_id == 0:
            self.input_mode.set("youtube")
        else:
            self.input_mode.set("file")
        
        self.update_ui_for_mode()
    
    def update_ui_for_mode(self):
        if self.input_mode.get() == "youtube":
            self.video_path.set("")
        else:
            self.youtube_url.set("")
    
    def show_tooltip(self, widget, text):
        x, y, _, _ = widget.bbox("all")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(tooltip, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        
        label = ttk.Label(frame, text=text, justify="left", wraplength=300, padding=5)
        label.pack()
        
        def close_tooltip(event=None):
            tooltip.destroy()
        
        tooltip.bind("<Button-1>", close_tooltip)
        tooltip.after(5000, close_tooltip)
    
    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Selecione um arquivo de vídeo",
            filetypes=(
                ("Arquivos de vídeo", "*.mp4 *.avi *.mkv *.webm *.mov"), 
                ("Todos os arquivos", "*.*")
            )
        )
        if filename:
            self.video_path.set(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(
            title="Selecione a pasta para salvar os arquivos"
        )
        if folder:
            self.output_folder.set(folder)
    
    def open_output_folder(self):
        folder_to_open = self.current_folder if self.current_folder else self.output_folder.get()
        
        if os.path.exists(folder_to_open):
            if sys.platform == 'win32':
                os.startfile(folder_to_open)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder_to_open])
            else:
                subprocess.run(['xdg-open', folder_to_open])
        else:
            messagebox.showerror("Erro", "A pasta de saída não existe.")
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def update_progress(self, percent, phase="processamento", details=None):
        self.progress_bar["value"] = percent
        self.progress_percent["text"] = f"{int(percent)}%"
        
        phases = {
            "download": "Baixando vídeo",
            "extract": "Extraindo áudio",
            "transcribe": "Transcrevendo áudio",
            "process": "Processando",
            "complete": "Concluído"
        }
        
        phase_text = phases.get(phase, "Processando")
        self.progress_label["text"] = f"{phase_text}..."
        
        if details:
            self.progress_details["text"] = details
        
        self.root.update_idletasks()
    
    def start_processing(self):
        self.start_big_button.config(
            text="PROCESSANDO...",
            bg="#f39c12",
            state=tk.DISABLED
        )
        self.root.update_idletasks()
        
        if self.input_mode.get() == "youtube" and not self.youtube_url.get():
            messagebox.showerror("Erro", "Por favor, informe uma URL do YouTube.")
            self.start_big_button.config(
                text="▶ INICIAR EXTRAÇÃO",
                bg="#2ecc71",
                state=tk.NORMAL
            )
            return
        elif self.input_mode.get() == "file" and not self.video_path.get():
            messagebox.showerror("Erro", "Por favor, selecione um arquivo de vídeo.")
            self.start_big_button.config(
                text="▶ INICIAR EXTRAÇÃO",
                bg="#2ecc71",
                state=tk.NORMAL
            )
            return
        
        if not self.output_folder.get():
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de saída.")
            self.start_big_button.config(
                text="▶ INICIAR EXTRAÇÃO",
                bg="#2ecc71",
                state=tk.NORMAL
            )
            return
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.open_folder_button.config(state=tk.DISABLED)
        
        self.progress_bar["value"] = 0
        self.progress_percent["text"] = "0%"
        self.progress_details["text"] = ""
        
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.root.after(100, self.check_thread)
    
    def process_video(self):
        try:
            class StreamRedirector:
                def __init__(self, log_function):
                    self.log_function = log_function
                    self.buffer = ""
                
                def write(self, text):
                    self.buffer += text
                    if '\n' in self.buffer:
                        lines = self.buffer.split('\n')
                        for line in lines[:-1]:
                            if line:
                                self.log_function(line)
                        self.buffer = lines[-1]
                
                def flush(self):
                    if self.buffer:
                        self.log_function(self.buffer)
                        self.buffer = ""
            
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = StreamRedirector(self.log_message)
            sys.stderr = StreamRedirector(self.log_message)
            
            try:
                language_code = self.language.get().split(" ")[0]
                
                if self.input_mode.get() == "youtube":
                    url = self.youtube_url.get()
                    self.log_message(f"Obtendo informações do vídeo do YouTube: {url}")
                    
                    self.log_message(f"Baixando vídeo do YouTube: {url}")
                    self.update_progress(0, "download", "Iniciando download...")
                    
                    def update_download_progress(percent):
                        self.update_progress(
                            percent, 
                            "download", 
                            f"Baixado {percent:.1f}% do vídeo"
                        )
                    
                    temp_folder = os.path.join("videos", "temp_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
                    if not os.path.exists(temp_folder):
                        os.makedirs(temp_folder)
                    
                    result = download_youtube_video(url, temp_folder, update_download_progress)
                    
                    if isinstance(result, tuple) and len(result) == 2:
                        video_path, video_title = result
                    else:
                        video_path = result
                        video_title = "youtube_video"
                    
                    if not video_path:
                        self.log_message("Falha ao baixar o vídeo do YouTube.")
                        return
                        
                    self.current_folder = create_video_folder(video_title or "youtube_video", True, url)
                    self.log_message(f"Criada pasta para o vídeo: {self.current_folder}")
                    
                    if video_path and os.path.exists(video_path):
                        new_video_path = os.path.join(self.current_folder, os.path.basename(video_path))
                        try:
                            shutil.move(video_path, new_video_path)
                            video_path = new_video_path
                        except Exception as e:
                            self.log_message(f"Erro ao mover arquivo: {str(e)}")
                            try:
                                shutil.copy2(video_path, new_video_path)
                                video_path = new_video_path
                            except:
                                pass
                    
                    try:
                        if os.path.exists(temp_folder):
                            shutil.rmtree(temp_folder)
                    except:
                        pass
                else:
                    video_file = self.video_path.get()
                    video_name = os.path.splitext(os.path.basename(video_file))[0]
                    
                    self.current_folder = create_video_folder(video_name)
                    self.log_message(f"Criada pasta para o vídeo: {self.current_folder}")
                    
                    dest_path = os.path.join(self.current_folder, os.path.basename(video_file))
                    self.log_message(f"Copiando arquivo de vídeo para a pasta de processamento...")
                    self.update_progress(0, "process", "Copiando arquivo de vídeo...")
                    
                    try:
                        shutil.copy2(video_file, dest_path)
                        video_path = dest_path
                    except Exception as e:
                        self.log_message(f"Erro ao copiar arquivo: {str(e)}")
                        video_path = video_file
                
                if video_path:
                    base_name = os.path.splitext(os.path.basename(video_path))[0]
                    output_text_path = os.path.join(self.current_folder, f"{base_name}_transcricao.txt")
                else:
                    output_text_path = os.path.join(self.current_folder, "transcricao.txt")
                
                self.log_message(f"Iniciando extração de texto do vídeo: {os.path.basename(video_path)}")
                self.log_message(f"Idioma selecionado: {language_code}")
                self.log_message(f"Tamanho do segmento: {self.chunk_size.get()} segundos")
                
                def update_transcription_progress(percent):
                    phase = "extract" if percent < 25 else "transcribe"
                    detail = "Extraindo áudio..." if percent < 25 else f"Transcrevendo áudio: {percent-25:.1f}% de 75%"
                    self.update_progress(percent, phase, detail)
                
                result = extract_speech_from_video(
                    video_path, 
                    output_text_path, 
                    language_code, 
                    self.chunk_size.get(),
                    update_transcription_progress
                )
                
                self.update_progress(100, "complete", "Processamento concluído!")
                self.log_message("\nExtração concluída!")
                self.log_message(f"Texto salvo em: {output_text_path}")
                
                if result:
                    preview = result[:500] + "..." if len(result) > 500 else result
                    self.log_message("\nPrévia do texto extraído:")
                    self.log_message(preview)
                    self.log_message(f"\nComprimento total do texto: {len(result)} caracteres")
                
                self.open_folder_button.config(state=tk.NORMAL)
                
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
        except Exception as e:
            self.log_message(f"Erro durante o processamento: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
    
    def check_thread(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            self.is_processing = False
            
            self.start_big_button.config(
                text="▶ INICIAR EXTRAÇÃO",
                bg="#2ecc71",
                state=tk.NORMAL
            )
            
            if self.current_folder and os.path.exists(self.current_folder):
                self.open_folder_button.config(state=tk.NORMAL)
    
    def show_segment_help(self):
        help_text = """O tamanho do segmento define em quantos segundos cada parte do áudio será dividida para processamento.

Por que isso é importante:
• O Google Speech Recognition tem um limite de tamanho para cada requisição
• Segmentos muito grandes (mais de 60 segundos) frequentemente causam erros "Bad Request"
• Segmentos muito pequenos (menos de 5 segundos) podem quebrar frases no meio
• O processamento fica mais confiável com segmentos menores, mas leva mais tempo

Recomendações:
• Para áudio com boa qualidade: 30-45 segundos
• Para áudio com ruído ou baixa qualidade: 15-30 segundos
• Para idiomas não-inglês: 20-30 segundos é ideal

Melhor precisão: 15-30 segundos
Melhor velocidade: 45-60 segundos"""

        help_window = tk.Toplevel(self.root)
        help_window.title("Ajuda - Tamanho do Segmento")
        help_window.geometry("500x350")
        help_window.transient(self.root)
        help_window.grab_set()
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Fechar", command=help_window.destroy).pack(pady=10)
    
    def cancel_processing(self):
        if self.is_processing:
            self.log_message("Cancelando operação...")
            self.is_processing = False
            
            self.update_progress(0, "process", "Operação cancelada")
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            
            self.start_big_button.config(
                text="▶ INICIAR EXTRAÇÃO",
                bg="#2ecc71",
                state=tk.NORMAL
            )
            
            try:
                if sys.platform == 'win32':
                    os.system('taskkill /f /im ffmpeg.exe > NUL 2>&1')
                    os.system('taskkill /f /im yt-dlp.exe > NUL 2>&1')
                else:
                    os.system('pkill -f ffmpeg > /dev/null 2>&1')
                    os.system('pkill -f yt-dlp > /dev/null 2>&1')
            except:
                pass


def check_dependencies():
    missing_deps = []
    
    try:
        import speech_recognition
    except ImportError:
        missing_deps.append("speech_recognition")
    
    try:
        import moviepy.video
    except ImportError:
        missing_deps.append("moviepy")
    
    try:
        import pydub
    except ImportError:
        missing_deps.append("pydub")
    
    if missing_deps:
        message = "As seguintes dependências estão faltando:\n"
        message += "\n".join(missing_deps)
        message += "\n\nDeseja instalá-las agora?"
        
        if messagebox.askyesno("Dependências faltando", message):
            try:
                for dep in missing_deps:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                messagebox.showinfo("Instalação concluída", "Todas as dependências foram instaladas com sucesso.")
                python = sys.executable
                os.execl(python, python, *sys.argv)
            except Exception as e:
                messagebox.showerror("Erro de instalação", f"Erro ao instalar dependências: {str(e)}")
                sys.exit(1)
        else:
            messagebox.showwarning("Aviso", "O aplicativo pode não funcionar corretamente sem as dependências necessárias.")


def check_ffmpeg():
    try:
        ffmpeg_path = Path("C:/ffmpeg/bin/ffmpeg.exe")
        if not ffmpeg_path.exists():
            try:
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                return False
        return True
    except:
        return False


def main():
    if not check_ffmpeg():
        messagebox.showwarning(
            "FFmpeg não encontrado", 
            "O FFmpeg não foi encontrado em C:/ffmpeg/bin/ffmpeg.exe ou no PATH.\n"
            "O aplicativo pode não funcionar corretamente sem o FFmpeg.\n\n"
            "Por favor, instale o FFmpeg de https://ffmpeg.org/download.html"
        )
    
    root = tk.Tk()
    
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except:
        pass
    
    root.title("Extrator de Texto de Vídeos")
    
    app = VideoTranscriberApp(root)
    
    check_dependencies()
    
    root.mainloop()


if __name__ == "__main__":
    main()