import os
import threading
from tkinter import Tk, Text, END, StringVar, filedialog, Listbox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.messagebox import showinfo, showerror
import requests
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL
import json
from typing import Dict, List
from tkinter import messagebox
import pyperclip

class GoogleDriveTab:
    def __init__(self, parent):
        self.parent = parent
        self.API_KEY = None
        self.show_password = False
        
        # Main container with padding
        main_frame = ttk.Frame(parent, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # API Key section
        api_frame = ttk.LabelFrame(main_frame, text="Cấu hình API", padding="10")
        api_frame.pack(fill="x", pady=(0, 15))
        
        # API Key input container
        api_input_frame = ttk.Frame(api_frame)
        api_input_frame.pack(fill="x")
        
        # Left side - API Key input
        ttk.Label(api_input_frame, text="API Key:").pack(side="left", padx=5)
        self.api_key_entry = ttk.Entry(api_input_frame, width=40, show="*")  # Default to password mode
        self.api_key_entry.pack(side="left", padx=5)
        
        # Toggle password visibility button
        self.toggle_btn = ttk.Button(
            api_input_frame,
            text="👁",  # Eye symbol
            style="secondary.TButton",
            width=3,
            command=self.toggle_password_visibility
        )
        self.toggle_btn.pack(side="left", padx=2)
        
        ttk.Button(
            api_input_frame,
            text="Xác nhận",
            style="info.TButton",
            command=self.confirm_api_key,
            width=10
        ).pack(side="left", padx=5)
        
        # Right side - File selection
        ttk.Button(
            api_input_frame, 
            text="Chọn file",
            style="primary.TButton",
            command=self.select_api_key_file,
            width=10
        ).pack(side="right", padx=5)
        
        self.selected_api_key_file = StringVar()
        ttk.Label(
            api_input_frame,
            textvariable=self.selected_api_key_file,
            style="info.TLabel",
        ).pack(side="right", padx=5)

        # Links input section with file input option
        input_frame = ttk.LabelFrame(main_frame, text="Liên kết Drive", padding="10")
        input_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Buttons frame for URL input options
        url_buttons_frame = ttk.Frame(input_frame)
        url_buttons_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(
            url_buttons_frame,
            text="Dán từ Clipboard",
            style="info.TButton",
            command=self.paste_from_clipboard,
            width=18
        ).pack(side="left", padx=5)

        ttk.Button(
            url_buttons_frame,
            text="Xóa URL",
            style="info.TButton",
            command=self.clear_input,
            width=18
        ).pack(side="left", padx=5)

        ttk.Button(
            url_buttons_frame,
            text="Nhập từ file",
            style="info.TButton",
            command=self.load_urls_from_file,
            width=12
        ).pack(side="left", padx=5)
        
        self.url_file_label = ttk.Label(
            url_buttons_frame,
            text="",
            style="info.TLabel"
        )
        self.url_file_label.pack(side="left", padx=5)
        
        # Text area for links
        self.link_input = Text(
            input_frame,
            font=("Segoe UI", 10),
            height=8
        )
        self.link_input.pack(fill="both", expand=True, pady=5)
        
        # Folder selection and Download section
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", pady=(0, 15))
        
        # Folder selection
        ttk.Label(action_frame, text="Thư mục tải về:").pack(side="left", padx=5)
        self.output_folder = StringVar()
        ttk.Label(
            action_frame,
            textvariable=self.output_folder,
            style="info.TLabel"
        ).pack(side="left", padx=5, fill="x", expand=True)
        
        ttk.Button(
            action_frame,
            text="Chọn thư mục",
            style="secondary.TButton",
            command=self.select_folder,
            width=12
        ).pack(side="right", padx=5)

        # Download button
        ttk.Button(
            main_frame,
            text="Bắt đầu tải xuống",
            style="success.TButton",
            command=self.start_download,
            width=15
        ).pack(pady=(0, 15))

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Tiến trình", padding="10")
        progress_frame.pack(fill="both", expand=True)
        
        self.progress_list = Listbox(
            progress_frame,
            font=("Segoe UI", 9)
        )
        self.progress_list.pack(fill="both", expand=True, side="left")
        
        # Add scrollbar to progress list
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.progress_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.progress_list.config(yscrollcommand=scrollbar.set)

        # Status
        self.status = StringVar()
        ttk.Label(
            main_frame,
            textvariable=self.status,
            style="success.TLabel"
        ).pack(pady=5)

    def toggle_password_visibility(self):
        """Toggle between showing and hiding the API key"""
        self.show_password = not self.show_password
        self.api_key_entry.config(show="" if self.show_password else "*")
        self.toggle_btn.config(text="👁" if self.show_password else "👁")

    def confirm_api_key(self):
        """Xác nhận API key nhập từ bàn phím"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.API_KEY = api_key
            self.api_key_entry.config(show="*")  # Always switch to password mode after confirmation
            self.show_password = False
            self.toggle_btn.config(text="👁")
            showinfo("Thành công", "Đã cập nhật API Key")
        else:
            showerror("Lỗi", "Vui lòng nhập API Key")

    def select_api_key_file(self):
        """Chọn file chứa API_KEY."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.selected_api_key_file.set(os.path.basename(file_path))
            self.API_KEY = self.load_api_key(file_path)

    def load_api_key(self, file_path):
        """Đọc API_KEY từ file văn bản (file có thể chứa bất kỳ định dạng nào, chỉ chứa API_KEY)."""
        try:
            # Kiểm tra nếu file tồn tại
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File không tồn tại: {file_path}")
            
            # Kiểm tra xem file có trống hay không
            if os.path.getsize(file_path) == 0:
                raise ValueError("File rỗng.")

            # Mở và đọc nội dung file
            with open(file_path, 'r') as file:
                api_key = file.read().strip()  # Đọc toàn bộ nội dung và loại bỏ khoảng trắng thừa
                
                if not api_key:
                    raise ValueError("File không chứa API_KEY hợp lệ.")
                
                # Gán API Key vào trường nhập liệu
                self.api_key_entry.delete(0, END)
                self.api_key_entry.insert(0, api_key)
                self.api_key_entry.config(show="*")  # Always show as password after loading
                self.show_password = False
                self.toggle_btn.config(text="👁")
                
                return api_key

        except (FileNotFoundError, ValueError) as e:
            # Hiển thị thông báo lỗi cho người dùng
            showerror("Lỗi", f"Không thể đọc API_KEY từ file: {str(e)}")
            return None
        except Exception as e:
            # Xử lý lỗi khác
            showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")
            return None

    def paste_from_clipboard(self):
        # Lấy nội dung từ clipboard
        clipboard_content = pyperclip.paste()

        # Dán nội dung từ clipboard vào Textbox và tự động xuống dòng
        current_content = self.link_input.get("1.0", END)  # Lấy nội dung hiện tại trong Textbox
        self.link_input.insert(END, clipboard_content + "\n")  # Dán nội dung và thêm xuống dòng

    def clear_input(self):
        # Xóa nội dung trong Textbox
        self.link_input.delete("1.0", END)

    def load_urls_from_file(self):
        """Load URLs from a text file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    urls = file.read()
                    self.link_input.delete('1.0', END)
                    self.link_input.insert('1.0', urls)
                    self.url_file_label.config(text=f"Đã tải: {os.path.basename(file_path)}")
                    showinfo("Thành công", "Đã tải danh sách liên kết từ file")
            except Exception as e:
                showerror("Lỗi", f"Không thể đọc file: {str(e)}")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(os.path.basename(folder))
            self.output_folder.folder_path = folder

    def start_download(self):
        if not self.API_KEY:
            showerror("Lỗi", "Vui lòng nhập API Key hoặc chọn file chứa API Key.")
            return
        
        links = self.link_input.get("1.0", END).strip().split("\n")
        output_folder = getattr(self.output_folder, 'folder_path', None)

        if not links or not output_folder:
            showerror("Lỗi", "Vui lòng nhập liên kết và chọn thư mục tải về.")
            return

        self.status.set("Đang tải xuống...")
        threading.Thread(target=self.download_links, args=(links, output_folder)).start()

    def download_links(self, links, output_folder):
        total_folders = len([link for link in links if link.strip()])
        successful_downloads = 0
        failed_downloads = []

        for link in links:
            if not link.strip():  # Skip empty lines
                continue
                
            folder_id = self.extract_folder_id(link)
            if folder_id:
                try:
                    self.progress_list.insert(END, f"Bắt đầu tải thư mục: {link}")
                    self.progress_list.yview(END)
                    success = self.download_folder(folder_id, output_folder)
                    if success:
                        successful_downloads += 1
                        self.progress_list.insert(END, f"Đã tải xong: {link}")
                    else:
                        failed_downloads.append((link, "Có lỗi khi tải file trong thư mục"))
                except Exception as e:
                    failed_downloads.append((link, str(e)))
                    self.progress_list.insert(END, f"Lỗi khi tải thư mục: {link}\nLỗi: {e}")
            else:
                failed_downloads.append((link, "Không thể trích xuất ID thư mục"))
                self.progress_list.insert(END, f"Không thể trích xuất ID từ liên kết: {link}")

        # Show appropriate completion message based on results
        if failed_downloads:
            error_message = "Một số thư mục không tải được:\n\n"
            for link, error in failed_downloads:
                error_message += f"• {link}: {error}\n"
            if successful_downloads > 0:
                error_message += f"\nĐã tải thành công {successful_downloads}/{total_folders} thư mục."
            showerror("Hoàn tất với lỗi", error_message)
        else:
            showinfo("Hoàn tất", f"Đã tải thành công {successful_downloads} thư mục.")

        self.status.set("Hoàn tất!")

    def download_folder(self, folder_id, output_folder):
        """Tải xuống toàn bộ nội dung thư mục."""
        service = build('drive', 'v3', developerKey=self.API_KEY)
        success = True
        
        def list_files_in_folder(folder_id):
            try:
                query = f"'{folder_id}' in parents and trashed = false"
                results = service.files().list(
                    q=query,
                    fields="files(id, name, mimeType)"
                ).execute()
                return results.get('files', [])
            except Exception as e:
                self.progress_list.insert(END, f"Lỗi khi lấy danh sách file: {str(e)}")
                return []

        def download_file(file_id, file_name, folder_path):
            try:
                url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={self.API_KEY}"
                response = requests.get(url, stream=True)
                
                if response.status_code != 200:
                    self.progress_list.insert(END, f"Lỗi khi tải {file_name}: HTTP {response.status_code}")
                    return False

                file_path = os.path.join(folder_path, file_name)
                total_size = int(response.headers.get('content-length', 0))
                
                self.progress_list.insert(END, f"Đang tải: {file_name}")
                self.progress_list.yview(END)

                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                speed = downloaded / (1024 * 1024)
                                status = f"Đang tải {file_name}: {percent:.1f}% - {speed:.1f} MB"
                                
                                last_index = self.progress_list.size() - 1
                                if last_index >= 0 and file_name in self.progress_list.get(last_index):
                                    self.progress_list.delete(last_index)
                                self.progress_list.insert(END, status)
                                self.progress_list.yview(END)

                self.progress_list.insert(END, f"Đã tải xong: {file_name}")
                self.progress_list.yview(END)
                return True

            except Exception as e:
                self.progress_list.insert(END, f"Lỗi khi tải {file_name}: {str(e)}")
                self.progress_list.yview(END)
                return False

        try:
            files = list_files_in_folder(folder_id)
            if not files:
                self.progress_list.insert(END, "Không tìm thấy file nào trong thư mục")
                return False

            os.makedirs(output_folder, exist_ok=True)

            download_results = []
            for file in files:
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    subfolder_path = os.path.join(output_folder, file['name'])
                    os.makedirs(subfolder_path, exist_ok=True)
                    subfolder_success = self.download_folder(file['id'], subfolder_path)
                    download_results.append(subfolder_success)
                else:
                    file_success = download_file(file['id'], file['name'], output_folder)
                    download_results.append(file_success)

            # Return True only if all downloads were successful
            return all(download_results)

        except Exception as e:
            self.progress_list.insert(END, f"Lỗi khi tải thư mục: {str(e)}")
            self.progress_list.yview(END)
            return False

    @staticmethod
    def extract_folder_id(link):
        link = link.strip()
        folder_id = None
        
        if not link:
            return None
            
        try:
            # Pattern 1: /folders/FOLDER_ID
            if "drive.google.com/drive/folders/" in link:
                folder_id = link.split("/folders/")[1].split("?")[0].split("/")[0]
            
            # Pattern 2: /file/d/FOLDER_ID
            elif "drive.google.com/file/d/" in link:
                folder_id = link.split("/file/d/")[1].split("/")[0].split("?")[0]
            
            # Pattern 3: open?id=FOLDER_ID
            elif "drive.google.com/open?id=" in link:
                folder_id = link.split("open?id=")[1].split("&")[0]
            
            # Pattern 4: /u/0/folders/FOLDER_ID or /u/[NUMBER]/folders/FOLDER_ID
            elif "drive.google.com/drive/u/" in link and "/folders/" in link:
                folder_id = link.split("/folders/")[1].split("?")[0].split("/")[0]
            
            # Check if folder_id looks valid (typically 33 characters of letters, numbers, and special chars)
            if folder_id and len(folder_id) >= 25 and all(c.isalnum() or c in "-_" for c in folder_id):
                return folder_id
                
        except IndexError:
            return None
        return None

class YouTubeTab:
    def __init__(self, parent):
        self.parent = parent
        self.format_cache: Dict[str, List] = {}  # Cache for video formats
        self.current_format = StringVar()                

        # Main container
        main_frame = ttk.Frame(parent, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Liên kết YouTube", padding="10")
        input_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Buttons frame for URL input options
        url_buttons_frame = ttk.Frame(input_frame)
        url_buttons_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(
            url_buttons_frame,
            text="Nhập từ file",
            style="info.TButton",
            command=self.load_urls_from_file,
            width=12
        ).pack(side="left", padx=5)
        
        ttk.Button(
            url_buttons_frame,
            text="Dán từ Clipboard",
            style="info.TButton",
            command=self.paste_from_clipboard,
            width=18
        ).pack(side="left", padx=5)

        ttk.Button(
            url_buttons_frame,
            text="Xóa URL",
            style="info.TButton",
            command=self.clear_input,
            width=18
        ).pack(side="left", padx=5)

       # Format fetch button
        ttk.Button(
            url_buttons_frame,
            text="Lấy định dạng",
            style="info.TButton",
            command=self.fetch_formats,
            width=12
        ).pack(side="left", padx=5)

        self.url_file_label = ttk.Label(
            url_buttons_frame,
            text="",
            style="info.TLabel"
        )
        self.url_file_label.pack(side="left", padx=5)
        
        self.link_input = Text(
            input_frame,
            font=("Segoe UI", 10),
            height=8
        )
        self.link_input.pack(fill="both", expand=True, pady=5)
       
        # Format selection frame
        format_frame = ttk.LabelFrame(main_frame, text="Cấu hình tải xuống", padding="10")
        format_frame.pack(fill="x", pady=(0, 15))

        # Format selection combobox
        format_select_frame = ttk.Frame(format_frame)
        format_select_frame.pack(fill="x", pady=5)
        
        ttk.Label(format_select_frame, text="Định dạng:").pack(side="left", padx=5)
        
        self.format_combobox = ttk.Combobox(
            format_select_frame, 
            textvariable=self.current_format,
            state="readonly",
            width=100
        )
        self.format_combobox.pack(side="left", padx=5, fill="x", expand=True)
        
        # Set placeholder text
        self.format_combobox['values'] = ["Mặc định: Video chất lượng tốt nhất. Vui lòng nhấn 'Lấy định dạng' để xem các tùy chọn khác."]
        self.format_combobox.set("Mặc định: Video chất lượng tốt nhất. Vui lòng nhấn 'Lấy định dạng' để xem các tùy chọn khác.")     

        # Folder selection
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(folder_frame, text="Thư mục tải về:").pack(side="left", padx=5)
        self.output_folder = StringVar()
        ttk.Label(
            folder_frame,
            textvariable=self.output_folder,
            style="info.TLabel"
        ).pack(side="left", padx=5, fill="x", expand=True)
        
        ttk.Button(
            folder_frame,
            text="Chọn thư mục",
            style="secondary.TButton",
            command=self.select_folder,
            width=12
        ).pack(side="right", padx=5)

        # Download button
        ttk.Button(
            main_frame,
            text="Bắt đầu tải xuống",
            style="success.TButton",
            command=self.start_download,
            width=15
        ).pack(pady=(0, 15))

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Tiến trình", padding="10")
        progress_frame.pack(fill="both", expand=True)
        
        self.progress_list = Listbox(
            progress_frame,
            font=("Segoe UI", 9)
        )
        self.progress_list.pack(fill="both", expand=True, side="left")
        
        # Add scrollbar to progress list
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.progress_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.progress_list.config(yscrollcommand=scrollbar.set)

    def paste_from_clipboard(self):
        # Lấy nội dung từ clipboard
        clipboard_content = pyperclip.paste()

        # Dán nội dung từ clipboard vào Textbox và tự động xuống dòng
        current_content = self.link_input.get("1.0", END)  # Lấy nội dung hiện tại trong Textbox
        self.link_input.insert(END, clipboard_content + "\n")  # Dán nội dung và thêm xuống dòng

    def clear_input(self):
        # Xóa nội dung trong Textbox
        self.link_input.delete("1.0", END)

    def fetch_formats(self):
        # Lấy nội dung từ widget Text
        content = self.link_input.get("1.0", "end-1c")  # "1.0" là bắt đầu từ dòng đầu tiên
        links = [link.strip() for link in content.splitlines() if link.strip()]  # Tạo danh sách URL

        if len(links) > 1:
            # Nếu có nhiều URL, hỏi người dùng có muốn tiếp tục tải tất cả với chất lượng tốt nhất
            messagebox.showinfo(
                "Thông báo",
                "Chất lượng tốt nhất sẽ được tự động chọn cho tất cả các video khi bạn nhập nhiều url"
            )
            return

        """Fetch available formats for the first video in the input"""
        url = self.link_input.get("1.0", "end-1c").split('\n')[0].strip()
        if not url:
            showerror("Lỗi", "Vui lòng nhập ít nhất một liên kết YouTube")
            return

        messagebox.showinfo(
            "Thông báo",
            "Đang lấy dnh sách định dạng. Vui long đợi .... Vui lòng nhấn xác nhận để bắt đầu!"
        )
        
        try:
            if url in self.format_cache:
                self.update_format_combobox(self.format_cache[url])
                return

            self.progress_list.insert(END, f"Đang lấy danh sách định dạng cho: {url}")
            self.progress_list.yview(END)

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # Process formats with more detailed information
                format_list = []
                formats.reverse()  # Reverse to show highest quality first
                
                for f in formats:
                    # Get all relevant format information
                    format_id = f.get('format_id', 'N/A')
                    ext = f.get('ext', 'N/A')
                    resolution = f.get('resolution', 'N/A')
                    filesize = f.get('filesize', 0)
                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    abr = f.get('abr', 0)  # Audio bitrate
                    vbr = f.get('vbr', 0)  # Video bitrate
                    fps = f.get('fps', 0)
                    
                    # Convert filesize to appropriate unit
                    if filesize > 0:
                        if filesize > 1024*1024*1024:
                            size_str = f"{filesize/(1024*1024*1024):.1f}GB"
                        else:
                            size_str = f"{filesize/(1024*1024):.1f}MB"
                    else:
                        size_str = "N/A"

                    # Create detailed format description
                    format_parts = []
                    format_parts.append(f"ID: {format_id}")
                    
                    # Video information
                    if vcodec != 'none':
                        format_parts.append(f"{resolution}")
                        if fps:
                            format_parts.append(f"{fps}fps")
                        if vbr:
                            format_parts.append(f"{vbr/1024:.1f}kbps")
                            
                    # Audio information
                    if acodec != 'none':
                        format_parts.append("Audio" if vcodec == 'none' else "+ Audio")
                        if abr:
                            format_parts.append(f"{abr}kbps")
                            
                    format_parts.extend([
                        f"[{ext}]",
                        f"({size_str})",
                        f"- {vcodec}" if vcodec != 'none' else "",
                        f"- {acodec}" if acodec != 'none' else ""
                    ])
                    
                    format_str = " ".join(filter(None, format_parts))
                    format_list.append(f"{format_str}")

                # Cache the formats
                self.format_cache[url] = format_list
                self.update_format_combobox(format_list)
                
                self.progress_list.insert(END, f"Đã tìm thấy {len(format_list)} định dạng")
                self.progress_list.yview(END)

        except Exception as e:
            self.progress_list.insert(END, f"Lỗi khi lấy định dạng: {str(e)}")
            self.progress_list.yview(END)

    def update_format_combobox(self, format_list):
        """Update the format combobox with new formats"""
        self.format_combobox['values'] = format_list
        if format_list:
            self.format_combobox.set(format_list[0])  # Select first format by default

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(os.path.basename(folder))
            self.output_folder.folder_path = folder

    def load_urls_from_file(self):
        """Load URLs from a text file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    urls = file.read()
                    self.link_input.delete('1.0', END)
                    self.link_input.insert('1.0', urls)
                    self.url_file_label.config(text=f"Đã tải: {os.path.basename(file_path)}")
                    showinfo("Thành công", "Đã tải danh sách liên kết từ file")
            except Exception as e:
                showerror("Lỗi", f"Không thể đọc file: {str(e)}")

    def start_download(self):
        links = [link.strip() for link in self.link_input.get("1.0", END).strip().split("\n") if link.strip()]
        output_folder = getattr(self.output_folder, 'folder_path', None)
        selected_format = self.current_format.get()

        if not links or not output_folder:
            showerror("Lỗi", "Vui lòng nhập liên kết và chọn thư mục tải về.")
            return

        if not selected_format or selected_format == "Mặc định: Video chất lượng tốt nhất. Vui lòng nhấn 'Lấy định dạng' để xem các tùy chọn khác.":
            # Nếu không chọn định dạng, tải video chất lượng tốt nhất
            format_id = 'best'
            # Lấy nội dung từ widget Text
            content = self.link_input.get("1.0", "end-1c")  # "1.0" là bắt đầu từ dòng đầu tiên
            links = [link.strip() for link in content.splitlines() if link.strip()]  # Tạo danh sách URL

            if len(links) > 1:
                # Nếu có nhiều URL, hỏi người dùng có muốn tiếp tục tải tất cả với chất lượng tốt nhất
                messagebox.showinfo(
                    "Thông báo",
                    "Chất lượng tốt nhất đã được chọn cho tất cả các video. Đang tiến hành tải tất cả với chất lượng tốt nhất."
                )
            else:
                # Hiển thị hộp thoại xác nhận
                result = messagebox.askyesno(
                    "Thông báo", 
                    "Bạn đang tải video với chất lượng tốt nhất! Để tải video chất lượng tùy chọn, vui lòng chọn định dạng video. Bạn có muốn tiếp tục tải video với chất lượng tốt nhất?"
                )
                
                if not result:  # Người dùng chọn "No"
                    messagebox.showinfo(
                        "Thông báo",
                        "Đang lấy dnh sách định dạng. Vui long đợi .... Vui lòng nhấn xác nhận để bắt đầu!"
                    )
                    self.fetch_formats()
                    # Quay lại yêu cầu người dùng chọn định dạng
                    return
        else:
            # Extract format ID từ selected_format nếu có
            format_id = selected_format.split("ID: ")[1].split(" ")[0]

        threading.Thread(target=self.download_videos, args=(links, output_folder, format_id)).start()

    def download_videos(self, links, output_folder, format_id):
        ydl_opts = {
            'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'format': format_id,
            'merge_output_format': 'mp4' if not format_id.startswith('bestaudio') else 'm4a',
        }
        
        total_downloads = len(links)
        successful_downloads = 0
        failed_downloads = []
        
        with YoutubeDL(ydl_opts) as ydl:
            for link in links:
                try:
                    self.progress_list.insert(END, f"Bắt đầu tải video: {link}")
                    self.progress_list.yview(END)
                    ydl.download([link])
                    successful_downloads += 1
                    self.progress_list.insert(END, f"Đã tải xong: {link}")
                    self.progress_list.yview(END)
                except Exception as e:
                    failed_downloads.append((link, str(e)))
                    self.progress_list.insert(END, f"Lỗi khi tải {link}: {str(e)}")
                    self.progress_list.yview(END)

        # Show appropriate completion message based on results
        if failed_downloads:
            error_message = "Một số video không tải được:\n\n"
            for link, error in failed_downloads:
                error_message += f"• {link}: {error}\n"
            if successful_downloads > 0:
                error_message += f"\nĐã tải thành công {successful_downloads}/{total_downloads} video."
            showerror("Hoàn tất với lỗi", error_message)
        else:
            showinfo("Hoàn tất", f"Đã tải thành công {successful_downloads} video.")

        # Reset format combobox
        self.format_combobox['values'] = ["Mặc định: Video chất lượng tốt nhất. Vui lòng nhấn 'Lấy định dạng' để xem các tùy chọn khác."]
        self.format_combobox.set("Mặc định: Video chất lượng tốt nhất. Vui lòng nhấn 'Lấy định dạng' để xem các tùy chọn khác.")
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            filename = d.get('filename', 'Tệp không xác định').split('/')[-1]
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

            # Định dạng thông tin tải về
            downloaded_str = self._format_size(downloaded_bytes)
            speed_str = self._format_size(speed) + "/s" if speed != "Unknown" else "Unknown"

            # Thời gian ước tính (ETA)
            eta = d.get('eta', "Unknown")
            eta_str = self._format_eta(eta) if eta != "Unknown" else "Đang tính..."

            # Định dạng trạng thái hiển thị
            status_text = f"Đang tải {filename}: {progress:.1f}% ({downloaded_str} / {total_str}) - Tốc độ: {speed_str} - {eta_str}"
            
            # Update only the last line if it's for the same file
            last_index = self.progress_list.size() - 1
            if last_index >= 0 and "Đang tải" in self.progress_list.get(last_index):
                self.progress_list.delete(last_index)
            
            self.progress_list.insert(END, status_text)
            self.progress_list.yview(END)

        elif d['status'] == 'finished':
            # Khi tải xong, hiển thị thông báo hoàn thành
            filename = d.get('filename', 'Tệp không xác định').split('/')[-1]
            self.progress_list.insert(END, f"Đã tải xong: {filename}")
            self.progress_list.yview(END)

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

if __name__ == "__main__":
    root = ttk.Window(
        title="Download Tool",
        themename="cosmo",
        size=(1000, 700)
    )
    
    style = ttk.Style()
    style.configure("TLabelframe", borderwidth=1)
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    youtube_tab_frame = ttk.Frame(notebook)
    drive_tab_frame = ttk.Frame(notebook)
    
    notebook.add(youtube_tab_frame, text="YouTube")
    notebook.add(drive_tab_frame, text="Google Drive")
    
    YouTubeTab(youtube_tab_frame)
    GoogleDriveTab(drive_tab_frame)

    root.mainloop()