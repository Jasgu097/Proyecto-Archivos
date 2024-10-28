import os
import struct
import json

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

    def read_gif_metadata(self, file_path):
        with open(file_path, 'rb') as file:
            header = file.read(6).decode('ascii')  # GIF87a o GIF89a
            width, height = struct.unpack('<HH', file.read(4))
            packed_byte = file.read(1)
            has_gct = (packed_byte[0] & 0b10000000) != 0
            color_resolution = ((packed_byte[0] & 0b01110000) >> 4) + 1
            background_color_index = struct.unpack('B', file.read(1))[0]
            pixel_aspect_ratio = struct.unpack('B', file.read(1))[0]

            metadata = {
                "path": file_path,
                "version": header,
                "width": width,
                "height": height,
                "has_global_color_table": has_gct,
                "color_resolution": color_resolution,
                "background_color_index": background_color_index,
                "pixel_aspect_ratio": pixel_aspect_ratio,
            }
            return metadata

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
