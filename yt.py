import threading
import os
import json
import yt_dlp
import pyperclip
import webbrowser
import subprocess
import requests
from tkinter import (
    Tk, Label, Entry, Button, filedialog, StringVar, Frame, messagebox, Toplevel, BOTH
)
from tkinter.ttk import Combobox, Progressbar, Style

class Config:
    FILE_NAME = "config.json"
    
    @staticmethod
    def load():
        if os.path.exists(Config.FILE_NAME):
            with open(Config.FILE_NAME, "r") as f:
                return json.load(f)
        return {"output_dir": ""}
    
    @staticmethod
    def save(config):
        with open(Config.FILE_NAME, "w") as f:
            json.dump(config, f)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {'quiet': True}
        self.video_info = None
        
    def fetch_formats(self, url):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return self._process_formats(info['formats'])
    
    def _process_formats(self, formats):
        processed_formats = []
        for f in formats:
            ext = f.get('ext', 'N/A')
            resolution = f.get('height', 'N/A')
            tbr = f.get('tbr', 'N/A')
            
            resolution_str = f", {resolution}p" if resolution != 'N/A' else f", {resolution}"
            tbr_str = f", {tbr} kbps" if tbr not in ['N/A', None] else f", {tbr}"
            
            format_info = (
                f"{f['format_id']} - {f.get('format_note', 'N/A')} "
                f"({ext}{resolution_str}{tbr_str})"
            ).strip()
            processed_formats.append(format_info)
        return processed_formats

    def download(self, url, format_id, output_path, progress_callback):
        ydl_opts = {
            "format": format_id,
            "progress_hooks": [progress_callback],
            "outtmpl": os.path.join(
                output_path,
                "%(title)s-%(format_id)s-%(height)s-%(tbr)s.%(ext)s"
            ),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

class UIManager:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._create_styles()
        
    def _setup_window(self):
        self.root.title("HDZ YouTube Downloader")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
    def _create_styles(self):
        style = Style()
        style.configure("TButton", padding=5, font=("Helvetica", 10))
        style.configure("TCombobox", padding=5, font=("Helvetica", 10))
        style.configure(
            "TProgressbar",
            thickness=10,
            troughcolor="#ddd",
            background="#4caf50"
        )

class YouTubeDownloader:
    def __init__(self):
        self.version = "1.0.0"
        self.root = Tk()
        self.ui_manager = UIManager(self.root)
        self.downloader = VideoDownloader()
        self.config = Config.load()
        
        self._init_variables()
        self._create_gui()
        self.download_thread = None
        self.footer_update_label = None 
        self.check_for_updates()
        
    def _init_variables(self):
        self.output_path = StringVar(value=self.config.get("output_dir", ""))
        self.quality_var = StringVar(value="Chọn chất lượng")
        self.progress_var = StringVar(value=0)
        self.status_var = StringVar(value="Trạng thái: Chờ nhập URL")
        self.available_formats = []

    def _create_gui(self):
        self._create_header()
        self._create_url_section()
        self._create_output_section()
        self._create_quality_section()
        self._create_download_section()
        self._create_footer()
        self._configure_grid()

    def _create_header(self):
        Label(
            self.root,
            text="YouTube Downloader",
            font=("Helvetica", 14, "bold"),
            fg="#333"
        ).grid(row=0, column=0, columnspan=3, pady=10, sticky="n")

    def _create_url_section(self):
        Label(
            self.root,
            text="URL Video YouTube:",
            font=("Helvetica", 10)
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.url_entry = Entry(self.root, font=("Helvetica", 10), width=40)
        self.url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.url_entry.bind("<Return>", self.on_enter_pressed)
        
        Button(
            self.root,
            text="Dán từ Clipboard",
            command=self.paste_from_clipboard
        ).grid(row=1, column=2, padx=10, pady=10)

    def _create_output_section(self):
        Label(
            self.root,
            text="Thư mục lưu:",
            font=("Helvetica", 10)
        ).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        Button(
            self.root,
            text="Chọn thư mục",
            command=self.select_output_folder
        ).grid(row=2, column=2, padx=10, pady=10)
        
        Label(
            self.root,
            textvariable=self.output_path,
            font=("Helvetica", 9),
            fg="#555"
        ).grid(row=2, column=1, padx=10, pady=10, sticky="w")

    def _create_quality_section(self):
        Label(
            self.root,
            text="Chọn chất lượng:",
            font=("Helvetica", 10)
        ).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        self.quality_combo = Combobox(
            self.root,
            textvariable=self.quality_var,
            state="readonly",
            values=[],
            width=40
        )
        self.quality_combo.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.quality_combo.bind("<<ComboboxSelected>>", self.update_quality_status)

    def _create_download_section(self):
        self.download_button = Button(
            self.root,
            text="Tải Video",
            command=self.start_download
        )
        self.download_button.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.progress_bar = Progressbar(
            self.root,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(
            row=5,
            column=0,
            columnspan=3,
            padx=10,
            pady=10,
            sticky="ew"
        )
        
        Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            fg="#555"
        ).grid(row=6, column=0, columnspan=3, pady=5)
        
        Button(
            self.root,
            text="Mở thư mục tải về",
            command=self.open_output_folder
        ).grid(row=7, column=0, columnspan=3, pady=10)

    def _create_footer(self):
        footer = Frame(self.root)
        footer.grid(row=8, column=0, columnspan=3, pady=10, sticky="ew")
        
        Label(
            footer,
            text=f"Version {self.version}",
            font=("Helvetica", 8),
            fg="#888"
        ).pack(side="left", padx=10)
        
        for link_text, url in [
            ("GitHub", "https://github.com/hdzungx"),
            ("Telegram", "https://t.me/hdzungx"),
            ("Donate", "https://linktr.ee/hdzungx")
        ]:
            Button(
                footer,
                text=link_text,
                font=("Helvetica", 8),
                command=lambda u=url: self.open_link(u)
            ).pack(side="left", padx=5)

    def _configure_grid(self):
        self.root.grid_columnconfigure(1, weight=1)
        for i in range(9):
            self.root.grid_rowconfigure(i, weight=0)
        self.root.grid_rowconfigure(8, weight=1)
        
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def check_for_updates(self):
        url = "https://api.github.com/repos/hdzungx/ytdl/releases/latest"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("tag_name", None)
            
            # Kiểm tra nếu phiên bản mới có sự khác biệt
            if latest_version != self.version:
                self._show_update_message(latest_version)
            else:
                self._clear_update_message()
        except requests.RequestException as e:
            # Hiển thị lỗi nếu không thể kiểm tra phiên bản
            self._show_error_message(f"Không thể kiểm tra phiên bản")

    def _show_update_message(self, latest_version):
        update_message = f"Có phiên bản mới {latest_version}! Tải xuống từ GitHub."
        github_url = "https://github.com/hdzungx/ytdl/releases/latest"  # URL của trang GitHub

        # Cập nhật thông báo nếu đã có footer_update_label
        if self.footer_update_label:
            self.footer_update_label.config(text=update_message)
        else:
            # Tạo mới thông báo nếu chưa có
            self.footer_update_label = Label(
                self.root, 
                text=update_message,
                font=("Helvetica", 8),
                fg="red",
                anchor="e",  # Canh phải
                cursor="hand2"  # Thay đổi con trỏ khi di chuột vào
            )
            self.footer_update_label.grid(row=8, column=2, padx=10, sticky="e")

        # Gắn sự kiện nhấp chuột để mở trang GitHub
        self.footer_update_label.bind("<Button-1>", lambda event: webbrowser.open(github_url))

    def _clear_update_message(self):
        # Xóa thông báo nếu không có phiên bản mới
        if self.footer_update_label:
            self.footer_update_label.config(text="")
            
    def _show_error_message(self, message):
        # Hiển thị thông báo lỗi trong GUI thay vì in ra console
        if self.footer_update_label:
            self.footer_update_label.config(text=message, fg="orange")
        else:
            self.footer_update_label = Label(
                self.root, 
                text=message,
                font=("Helvetica", 8),
                fg="black",
                anchor="e"
            )
            self.footer_update_label.grid(row=8, column=2, padx=10, sticky="e")

    def disable_widgets(self):
        for child in self.root.winfo_children():
            if isinstance(child, (Button, Entry, Combobox)) and child.cget("text") not in ["GitHub", "Telegram"]:
                child.config(state="disabled")

    def enable_widgets(self):
        for child in self.root.winfo_children():
            if isinstance(child, (Button, Entry, Combobox)):
                child.config(state="normal")

    def open_link(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở liên kết: {str(e)}")

    def on_enter_pressed(self, event):
        self.fetch_video_formats()

    def update_quality_status(self, event):
        selected_quality = self.quality_var.get()
        status = (
            "Trạng thái: Vui lòng chọn chất lượng video"
            if selected_quality == "Chọn chất lượng video"
            else f"Chất lượng video đã chọn: {selected_quality}"
        )
        self.status_var.set(status)

    def paste_from_clipboard(self):
        clipboard_text = pyperclip.paste()
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, clipboard_text)
        self.fetch_video_formats()

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_path.set(folder)
            Config.save({"output_dir": folder})

    def fetch_video_formats(self):
        url = self.url_entry.get()
        if not url.startswith("http"):
            self.status_var.set(
                "Trạng thái: URL không hợp lệ! "
                "Vui lòng nhập URL bắt đầu bằng 'http'"
            )
            messagebox.showwarning(
                "Cảnh báo",
                "URL không hợp lệ! Vui lòng nhập URL bắt đầu bằng 'http'"
            )
            return
            
        self.status_var.set("Trạng thái: Đang lấy thông tin video...")

        def fetch():
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    # Fetch full video info
                    self.video_info = ydl.extract_info(url, download=False)
                
                formats = self.downloader.fetch_formats(url)
                self.root.after(0, lambda: self.update_formats(formats))
                self.root.after(
                    0,
                    lambda: self.status_var.set("Trạng thái: Chọn chất lượng video.")
                )
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror(
                        "Lỗi",
                        f"Không thể tải thông tin video: {str(e)}"
                    ),
                    self.status_var.set("Trạng thái: Lỗi khi lấy thông tin video.")
                ])

        threading.Thread(target=fetch, daemon=True).start()

    def start_download(self):
        if not self._validate_download():
            return
            
        if self.download_thread and self.download_thread.is_alive():
            return

        # Show download confirmation popup
        self._show_download_confirmation()

    def _show_download_confirmation(self):
        # Create confirmation popup
        confirm_window = Toplevel(self.root)
        confirm_window.title("Xác nhận tải video")
        confirm_window.geometry("400x300")
        confirm_window.transient(self.root)
        confirm_window.grab_set()

        # Get selected format details
        selected_format_str = self.quality_var.get()
        selected_format_id = selected_format_str.split(" - ")[0]

        # Find the full format details
        selected_format = None
        for f in self.video_info['formats']:
            if f['format_id'] == selected_format_id:
                selected_format = f
                break

        # Create confirmation labels
        Label(confirm_window, text="Xác nhận tải video", font=("Helvetica", 14, "bold")).pack(pady=10)

        details_frame = Frame(confirm_window)
        details_frame.pack(padx=20, pady=10, fill=BOTH, expand=True)

        details = [
            ("Tiêu đề:", self.video_info.get('title', 'Không xác định')),
            ("Kênh:", self.video_info.get('uploader', 'Không xác định')),
            ("Định dạng:", selected_format.get('ext', 'Không xác định')),
            ("Độ phân giải:", f"{selected_format.get('height', 'N/A')}p"),
            ("Bitrate:", f"{selected_format.get('tbr', 'N/A')} kbps"),
            ("Kích thước (ước tính):", f"{selected_format.get('filesize', 0) / (1024*1024):.2f} MB" if selected_format.get('filesize') else "Chưa xác định"),
        ]

        for label, value in details:
            row = Frame(details_frame)
            row.pack(fill='x', pady=5)
            Label(row, text=label, font=("Helvetica", 10, "bold"), width=15, anchor='w').pack(side='left')
            Label(row, text=value, font=("Helvetica", 10), anchor='w', wraplength=300, justify='left').pack(side='left')

        # Buttons frame
        button_frame = Frame(confirm_window)
        button_frame.pack(pady=10)

        def confirm_download():
            confirm_window.destroy()
            self._reset_progress()
            self.disable_widgets()
            self.download_thread = threading.Thread(
                target=self.download_video,
                daemon=True
            )
            self.download_thread.start()

        def cancel_download():
            confirm_window.destroy()

        Button(button_frame, text="Tải xuống", command=confirm_download).pack(side='left', padx=10)
        Button(button_frame, text="Hủy", command=cancel_download).pack(side='left', padx=10)

    def update_formats(self, formats):
        self.available_formats = formats
        self.quality_combo['values'] = ["Chọn chất lượng video"] + formats
        self.quality_combo.set("Chọn chất lượng video")

    def start_download(self):
        if not self._validate_download():
            return
            
        if self.download_thread and self.download_thread.is_alive():
            return

        # Create a confirmation dialog
        confirm = messagebox.askyesno(
            "Xác nhận tải video", 
            f"Bạn có chắc muốn tải video này không?\n\n"
            f"Tiêu đề: {self.video_info.get('title', 'Không xác định')}\n"
            f"Định dạng: {self.quality_var.get()}"
        )
        
        if confirm:
            self._reset_progress()
            self.disable_widgets()
            self.download_thread = threading.Thread(
                target=self.download_video,
                daemon=True
            )
            self.download_thread.start()


    def _validate_download(self):
        if not self.url_entry.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL video")
            return False
            
        if not self.output_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục lưu")
            return False
            
        if self.quality_var.get() == "Chọn chất lượng video":
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn chất lượng video")
            return False
            
        return True

    def _reset_progress(self):
        self.progress_var.set(0)
        self.progress_bar.update_idletasks()
        self.status_var.set("Trạng thái: Đang tải video...")

    def download_video(self):
        try:
            self.downloader.download(
                self.url_entry.get(),
                self.quality_var.get().split(" - ")[0],
                self.output_path.get(),
                self._progress_hook
            )
        except yt_dlp.DownloadError as e:
            messagebox.showerror("Lỗi", f"Không thể tải video: {str(e)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            self._update_download_progress(d)
        elif d['status'] == 'finished':
            self._finish_download()

    def _update_download_progress(self, d):
        # Lấy thông tin tiến trình tải
        downloaded_bytes = d.get('downloaded_bytes', 0)
        total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', "Unknown")  # Gán "Unknown" nếu không có giá trị

        # Kiểm tra total_bytes
        if total_bytes == "Unknown" or not total_bytes:
            progress = 0
            total_str = "Unknown"
        else:
            progress = min((downloaded_bytes / total_bytes) * 100, 100)
            total_str = self._format_size(total_bytes)

        # Cập nhật giá trị tiến trình
        self.progress_var.set(progress)
        self.progress_bar.update_idletasks()

        # Định dạng thông tin tải về
        downloaded_str = self._format_size(downloaded_bytes)
        speed_str = self._format_size(speed) + "/s" if speed != "Unknown" else "Unknown"

        # Thời gian ước tính (ETA)
        eta = d.get('eta', "Unknown")
        eta_str = self._format_eta(eta) if eta != "Unknown" else "Đang tính..."

        # Cập nhật trạng thái hiển thị
        self.status_var.set(
            f"Đang tải: {progress:.1f}% ({downloaded_str} / {total_str}) - "
            f"Tốc độ: {speed_str} - {eta_str}"
        )
        self.root.update_idletasks()

    def _format_size(self, bytes_or_unknown):
        if bytes_or_unknown == "Unknown" or not bytes_or_unknown:
            return "Unknown"
        bytes = bytes_or_unknown  # Đảm bảo bytes là số
        if bytes >= 1024 * 1024 * 1024:  # >= 1GB
            return f"{bytes / (1024 * 1024 * 1024):.2f}GB"
        return f"{bytes / (1024 * 1024):.2f}MB"

    def _format_eta(self, eta_or_unknown):
        if eta_or_unknown == "Unknown" or not eta_or_unknown:
            return "Đang tính..."
        eta = eta_or_unknown  # Đảm bảo eta là số
        eta_minutes = eta // 60
        eta_seconds = eta % 60
        return f"ETA: {eta_minutes:.0f} phút {eta_seconds:.0f} giây"


    def _finish_download(self):
        self.progress_var.set(100)
        self.progress_bar.update_idletasks()
        self.status_var.set("Tải xong! Video đã được lưu.")
        self.enable_widgets()
        self.root.update_idletasks()

    def open_output_folder(self):
        output_dir = self.output_path.get()
        if not os.path.exists(output_dir):
            return
            
        if os.name == "nt":  # Windows
            subprocess.run(["explorer", output_dir])
        else:  # Linux or MacOS
            subprocess.run(["xdg-open", output_dir])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()