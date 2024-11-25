import threading
import os
import json
import yt_dlp
import pyperclip
from tkinter import Tk, Label, Entry, Button, filedialog, StringVar, DoubleVar, Frame, messagebox
from tkinter.ttk import Combobox, Progressbar, Style
from threading import Thread
import subprocess
import webbrowser

CONFIG_FILE = "config.json"


class YouTubeDownloader:
    def __init__(self):
        self.root = Tk()
        self.root.title("HDZ YouTube Downloader")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.setup_variables()
        self.setup_styles()
        self.load_config()
        self.create_gui()

    def setup_variables(self):
        self.output_path = StringVar()
        self.quality_var = StringVar(value="Chọn chất lượng")
        self.progress_var = StringVar(value=0)
        self.status_var = StringVar(value="Trạng thái: Chờ nhập URL")
        self.available_formats = []
        self.download_thread = None

    def setup_styles(self):
        style = Style()
        style.configure("TButton", padding=5, font=("Helvetica", 10))
        style.configure("TCombobox", padding=5, font=("Helvetica", 10))
        style.configure("TProgressbar", thickness=10, troughcolor="#ddd", background="#4caf50")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.output_path.set(config.get("output_dir", ""))

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"output_dir": self.output_path.get()}, f)

    def create_gui(self):
        # Thêm tiêu đề chính giữa
        Label(self.root, text="YouTube Downloader By HDZ", font=("Helvetica", 14, "bold"), fg="#333").grid(
            row=0, column=0, columnspan=3, pady=10, sticky="n"
        )

        # URL input
        Label (self.root, text="URL Video YouTube:", font=("Helvetica", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.url_entry = Entry(self.root, font=("Helvetica", 10), width=40)
        self.url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.url_entry.bind("<Return>", self.on_enter_pressed)  
        Button(self.root, text="Dán từ Clipboard", command=self.paste_from_clipboard).grid(row=1, column=2, padx=10, pady=10)

        # Output folder
        Label(self.root, text="Thư mục lưu:", font=("Helvetica", 10)).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        Button(self.root, text="Chọn thư mục", command=self.select_output_folder).grid(row=2, column=2, padx=10, pady=10)
        Label(self.root, textvariable=self.output_path, font=("Helvetica", 9), fg="#555").grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Quality selection (Combobox for formats)
        Label(self.root, text="Chọn chất lượng:", font=("Helvetica", 10)).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.quality_combo = Combobox(self.root, textvariable=self.quality_var, state="readonly", values=[], width=40)
        self.quality_combo.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.quality_combo.bind("<<ComboboxSelected>>", self.update_quality_status)
        
        # Download button and progress
        self.download_button = Button(self.root, text="Tải Video", command=self.start_download)
        self.download_button.grid(row=4, column=0, columnspan=3, pady=10)
        self.progress_bar = Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        Label(self.root, textvariable=self.status_var, font=("Helvetica", 9), fg="#555").grid(row=6, column=0, columnspan=3, pady=5)

        # Open folder button
        Button(self.root, text="Mở thư mục tải về", command=self.open_output_folder).grid(row=7, column=0, columnspan=3, pady=10)

        # Configure grid weight for dynamic resizing
        self.root.grid_columnconfigure(1, weight=1)  # Make column 1 resizable
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_rowconfigure(4, weight=0)
        self.root.grid_rowconfigure(5, weight=0)
        self.root.grid_rowconfigure(6, weight=0)
        self.root.grid_rowconfigure(7, weight=0)

        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())  # Ensure minimum size is set

        # Thêm khu vực thông tin liên kết và phiên bản
        footer_frame = Frame(self.root)
        footer_frame.grid(row=8, column=0, columnspan=3, pady=10, sticky="ew")

        version_label = Label(footer_frame, text="Version 1.0.0", font=("Helvetica", 8), fg="#888")
        version_label.pack(side="left", padx=10)

        github_button = Button(footer_frame, text="GitHub", font=("Helvetica", 8), command=lambda: self.open_link("https://github.com/hdzungx"))
        github_button.pack(side="left", padx=5)

        telegram_button = Button(footer_frame, text="Telegram", font=("Helvetica", 8), command=lambda: self.open_link("https://t.me/hdzungx"))
        telegram_button.pack(side="left", padx=5)

        donate_button = Button(footer_frame, text="Donate", font=("Helvetica", 8), command=lambda: self.open_link("https://linktr.ee/hdzungx"))
        donate_button.pack(side="left", padx=5)

        # Tùy chỉnh lại grid weight cho footer
        self.root.grid_rowconfigure(8, weight=1)

    def open_link(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở liên kết: {str(e)}")


    def on_enter_pressed(self, event):
        self.status_var.set("Trạng thái: Đang lấy thông tin video...")
        self.fetch_video_formats()  # Lấy danh sách định dạng

    def update_quality_status(self, event):
        selected_quality = self.quality_var.get()

        if selected_quality == "Chọn chất lượng video":
            self.status_var.set("Trạng thái: Vui lòng chọn chất lượng video")
        else:
            self.status_var.set(f"Chất lượng video đã chọn: {selected_quality}")

    def paste_from_clipboard(self):
        clipboard_text = pyperclip.paste()
        if clipboard_text.startswith("http"):
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, clipboard_text)
            self.fetch_video_formats()  # Lấy danh sách định dạng

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_path.set(folder)
            self.save_config()

    def fetch_video_formats(self):
        url = self.url_entry.get()
        if not url.startswith("http"):
            self.status_var.set("Trạng thái: URL không hợp lệ! Vui lòng nhập URL bắt đầu bằng 'http'")
            messagebox.showwarning("Cảnh báo", "URL không hợp lệ! Vui lòng nhập URL bắt đầu bằng 'http'")
            return
        self.status_var.set("Trạng thái: Đang lấy thông tin video...")
        def fetch():
            try:
                ydl_opts = {'quiet': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = []

                    # Duyệt qua tất cả các định dạng và chuẩn hóa độ dài của các trường
                    for f in info['formats']:
                        ext = f.get('ext', 'N/A')
                        resolution = f.get('height', 'N/A')
                        fps = f.get('fps', 'N/A')
                        size = f.get('filesize', 0)
                        size_mb = f"{size / (1024 * 1024):.2f} MB" if size else "Không rõ"
                        tbr = f.get('tbr', 'N/A')
                        
                        # Kiểm tra nếu resolution là N/A thì không thêm đơn vị p
                        resolution_str = f", {resolution}p" if resolution != 'N/A' else f", {resolution}"

                        # Kiểm tra nếu tbr là None hoặc "N/A"
                        tbr_str = f", {tbr} kbps" if tbr not in ['N/A', None] else f", {tbr}"

                        # Tạo chuỗi cho mỗi định dạng, bao gồm TBR và resolution nếu có
                        format_info = f"{f['format_id']} - {f.get('format_note', 'N/A')} ({ext} {resolution_str} {tbr_str})".strip()

                        # Thêm vào danh sách formats
                        formats.append(format_info)


                    # Cập nhật UI với danh sách định dạng
                    self.root.after(0, lambda: self.update_formats(formats))
                    self.root.after(0, lambda: self.status_var.set("Trạng thái: Chọn chất lượng video."))
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Lỗi", f"Không thể tải thông tin video: {str(e)}"),
                    self.status_var.set("Trạng thái: Lỗi khi lấy thông tin video.")
                ])

        threading.Thread(target=fetch, daemon=True).start()


    def update_formats(self, formats):
        self.available_formats = formats
        self.quality_combo['values'] = ["Chọn chất lượng video"] + formats
        if formats:
            self.quality_combo.set("Chọn chất lượng video")  

    def start_download(self):
        if not self.url_entry.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL video")
            return

        if not self.output_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục lưu")
            return

        if self.quality_var.get() == "Chọn chất lượng video":
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn chất lượng video")
            return

        if self.download_thread and self.download_thread.is_alive():
            return

        # Reset thanh tiến trình và trạng thái
        self.progress_var.set(0)
        self.progress_bar.update_idletasks()  # Cập nhật thanh tiến trình
        self.status_var.set("Trạng thái: Đang tải video...")

        self.download_thread = Thread(target=self.download_video, daemon=True)
        self.download_thread.start()
        self.download_button.config(state="disabled")

    def download_video(self):
        url = self.url_entry.get()
        quality = self.quality_var.get()
        output_path = self.output_path.get()

        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)

                if total_bytes > 0:
                    # Tính phần trăm tiến trình (giới hạn tối đa 100%)
                    progress = min((downloaded_bytes / total_bytes) * 100, 100)

                    # Cập nhật thanh tiến trình
                    self.progress_var.set(progress)  # Use self.progress_var
                    self.progress_bar.update_idletasks()

                    # Chuyển đổi sang đơn vị phù hợp (MB hoặc GB)
                    def format_size(bytes):
                        if bytes >= 1024 * 1024 * 1024:  # >= 1GB
                            return f"{bytes / (1024 * 1024 * 1024):.2f}GB"
                        else:  # MB
                            return f"{bytes / (1024 * 1024):.2f}MB"

                    downloaded_str = format_size(downloaded_bytes)
                    total_str = format_size(total_bytes)
                    speed_str = format_size(speed) + "/s"

                    # Tính thời gian còn lại
                    eta = d.get('eta', None)
                    if eta:
                        eta_minutes = eta // 60
                        eta_seconds = eta % 60
                        eta_str = f"ETA: {eta_minutes:.0f} phút {eta_seconds:.0f} giây"
                    else:
                        eta_str = "Đang tính..."

                    # Cập nhật thông báo trạng thái
                    self.status_var.set(
                        f"Đang tải: {progress:.1f}% ({downloaded_str} / {total_str}) - "
                        f"Tốc độ: {speed_str} - {eta_str}"
                    )
                    self.root.update_idletasks()

            elif d['status'] == 'finished':
                # Khi tải xong, cập nhật trạng thái và thanh tiến trình là 100%
                self.progress_var.set(100)
                self.progress_bar.update_idletasks()
                self.status_var.set("Tải xong! Video đã được lưu.")
                self.root.update_idletasks()

        # Tùy chỉnh lại template tên file
        ydl_opts = {
            "format": quality.split(" - ")[0],  # Sử dụng format_id để tải về video
            "progress_hooks": [progress_hook],
            "outtmpl": os.path.join(output_path, "%(title)s-%(format_id)s-%(height)s-%(tbr)s.%(ext)s"),  # Thêm thông tin độ phân giải vào tên file
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except yt_dlp.DownloadError as e:
            # Nếu xảy ra lỗi trong quá trình tải video, thông báo lỗi cho người dùng
            messagebox.showerror("Lỗi", f"Không thể tải video: {str(e)}")
        except Exception as e:
            # Xử lý các lỗi khác
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
        finally:
            self.download_button.config(state="normal")

    def open_output_folder(self):
        if os.path.exists(self.output_path.get()):
            if os.name == "nt":  # Windows
                subprocess.run(["explorer", self.output_path.get()])
            else:  # Linux or MacOS
                subprocess.run(["xdg-open", self.output_path.get()])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()
