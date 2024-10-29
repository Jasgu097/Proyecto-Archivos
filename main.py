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
                "Ruta": file_path,
                "Version": header,
                "Ancho": width,
                "Altura": height,
                "Tabla de color": has_gct,
                "Resolucion del color": color_resolution,
                "Indice de color de fondo": background_color_index,
                "Relacion de aspecto de los pixeles": pixel_aspect_ratio,
                "Contador de colores": color_count,
                "Fecha de creacion": creation_date,
                "Fecha de modificacion": modification_date,
                "Tipo de compresion": compression_type,
                "Formato numerioc": numeric_format,
                "Cantidad de imagenes": image_count,
                "Comentarios": comments
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

        self.bg_color = "#2e2e2e"
        self.fg_color = "#ffffff"
        self.btn_bg_color = "#4a4a4a"
        self.entry_bg_color = "#3a3a3a"
        self.entry_fg_color = "#e0e0e0"

        self.root.title("GIF Data Extractor")
        self.root.configure(bg=self.bg_color)

        self.select_button = Button(
            root, text="Seleccionar carpeta", command=self.select_folder,
            bg=self.btn_bg_color, fg=self.fg_color
        )
        self.select_button.pack(pady=5)

        self.gif_listbox = Listbox(
            root, bg=self.entry_bg_color, fg=self.entry_fg_color, selectbackground="#5c5c5c"
        )
        self.gif_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.gif_listbox.bind('<<ListboxSelect>>', self.show_gif_info)

        self.info_text = Text(root, bg=self.bg_color, fg=self.fg_color, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.edit_button = Button(
            root, text="Editar Información", command=self.open_edit_window,
            bg=self.btn_bg_color, fg=self.fg_color
        )
        self.edit_button.pack(pady=5)

        self.populate_gif_list()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.extractor.add_gif_folder(folder_path)
            self.populate_gif_list()

    def populate_gif_list(self):
        self.gif_listbox.delete(0, END)
        for gif in self.extractor.get_gif_info():
            self.gif_listbox.insert(END, gif["Ruta"])

    def show_gif_info(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.current_index = index
            gif_info = self.extractor.get_gif_info()[index]
            self.info_text.delete("1.0", END)
            for key, value in gif_info.items():
                self.info_text.insert(END, f"{key}: {value}\n")

    def open_edit_window(self):
        if hasattr(self, 'current_index'):
            gif_info = self.extractor.get_gif_info()[self.current_index]

            self.edit_window = Toplevel(self.root)
            self.edit_window.title("Editar Información")
            self.edit_window.configure(bg=self.bg_color)

            self.entries = {}
            row = 0
            for key, value in gif_info.items():
                Label(self.edit_window, text=key, bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0)
                entry = Entry(self.edit_window, bg=self.entry_bg_color, fg=self.entry_fg_color)
                entry.insert(END, str(value))
                entry.grid(row=row, column=1, padx=5, pady=2)
                self.entries[key] = entry
                row += 1

            save_button = Button(
                self.edit_window, text="Guardar Cambios", command=self.save_changes,
                bg=self.btn_bg_color, fg=self.fg_color
            )
            save_button.grid(row=row, columnspan=2, pady=5)

    def save_changes(self):
        updated_info = {key: entry.get() for key, entry in self.entries.items()}
        self.extractor.update_gif_info(self.current_index, updated_info)
        self.edit_window.destroy()
        self.populate_gif_list()
        self.show_gif_info(None)

if __name__ == "__main__":
    root = Tk()
    extractor = GIFExtractor()
    app = GIFApp(root, extractor)
    root.mainloop()
