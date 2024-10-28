import os
import struct
import json
from tkinter import Tk, filedialog, Button, Listbox, Text, END
from datetime import datetime

class GIFExtractor:
    def __init__(self):
        self.data_file = 'gif_data.json'
        self.gif_data = []

    def find_gif_files(self, root_folder):
        gif_files = []
        for folder, _, files in os.walk(root_folder):
            for file in files:
                if file.lower().endswith('.gif'):
                    gif_files.append(os.path.join(folder, file))
        return gif_files

    def get_file_dates(self, file_path):
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)
        creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        modification_date = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
        return creation_date, modification_date

    def read_gif_metadata(self, file_path):
        with open(file_path, 'rb') as file:
            header = file.read(6).decode('ascii')
            width, height = struct.unpack('<HH', file.read(4))
            packed_byte = file.read(1)
            has_gct = (packed_byte[0] & 0b10000000) != 0
            color_resolution = ((packed_byte[0] & 0b01110000) >> 4) + 1
            background_color_index = struct.unpack('B', file.read(1))[0]
            pixel_aspect_ratio = struct.unpack('B', file.read(1))[0]

            color_count = 2 ** (color_resolution + 1) if has_gct else 0
            creation_date, modification_date = self.get_file_dates(file_path)
            compression_type = "LZW"
            numeric_format = "Little Endian"
            image_count, comments = self.count_images_and_comments(file)

            metadata = {
                "path": file_path,
                "version": header,
                "width": width,
                "height": height,
                "has_global_color_table": has_gct,
                "color_resolution": color_resolution,
                "background_color_index": background_color_index,
                "pixel_aspect_ratio": pixel_aspect_ratio,
                "color_count": color_count,
                "creation_date": creation_date,
                "modification_date": modification_date,
                "compression_type": compression_type,
                "numeric_format": numeric_format,
                "image_count": image_count,
                "comments": comments
            }
            return metadata

    def count_images_and_comments(self, file):
        image_count = 0
        comments = []
        file.seek(13)
        while True:
            block_id = file.read(1)
            if block_id == b'\x2C':
                image_count += 1
                file.seek(9, 1)
            elif block_id == b'\x21':
                ext_type = file.read(1)
                if ext_type == b'\xFE':
                    comment = ""
                    while True:
                        block_size = ord(file.read(1))
                        if block_size == 0:
                            break
                        comment += file.read(block_size).decode('ascii', errors='ignore')
                    comments.append(comment)
                else:
                    file.seek(1, 1)
            elif block_id == b'\x3B':
                break
            else:
                break
        return image_count, comments

    def save_metadata(self):
        with open(self.data_file, 'w') as file:
            json.dump(self.gif_data, file, indent=4)

    def load_metadata(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as file:
                self.gif_data = json.load(file)

    def add_gif_folder(self, folder_path):
        gif_files = self.find_gif_files(folder_path)
        for gif_file in gif_files:
            metadata = self.read_gif_metadata(gif_file)
            self.gif_data.append(metadata)
        self.save_metadata()

    def get_gif_info(self):
        return self.gif_data


class GIFApp:
    def __init__(self, root, extractor):
        self.root = root
        self.extractor = extractor
        self.extractor.load_metadata()

        # Crear GUI
        self.root.title("GIF Data Extractor")
        self.select_button = Button(root, text="Seleccionar carpeta", command=self.select_folder)
        self.select_button.pack()

        self.gif_listbox = Listbox(root)
        self.gif_listbox.pack(fill="both", expand=True)
        self.gif_listbox.bind('<<ListboxSelect>>', self.show_gif_info)

        self.info_text = Text(root)
        self.info_text.pack(fill="both", expand=True)

        self.populate_gif_list()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.extractor.add_gif_folder(folder_path)
            self.populate_gif_list()

    def populate_gif_list(self):
        self.gif_listbox.delete(0, END)
        for gif in self.extractor.get_gif_info():
            self.gif_listbox.insert(END, gif["path"])

    def show_gif_info(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            gif_info = self.extractor.get_gif_info()[index]
            self.info_text.delete("1.0", END)
            for key, value in gif_info.items():
                self.info_text.insert(END, f"{key}: {value}\n")


if __name__ == "__main__":
    root = Tk()
    extractor = GIFExtractor()
    app = GIFApp(root, extractor)
    root.mainloop()