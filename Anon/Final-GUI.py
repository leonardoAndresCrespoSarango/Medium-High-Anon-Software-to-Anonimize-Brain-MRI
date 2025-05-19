#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonimizar_dicom_gui.py

Aplicación gráfica para anonimizar archivos DICOM y aplicar un recorte facial
solamente en los cortes sagitales, clasificando cada archivo en su carpeta
de plano correspondiente dentro de cada paciente.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

try:
    import pydicom
    import numpy as np
except ImportError:
    messagebox.showerror("Error de Dependencias",
                         "Por favor, instala las dependencias requeridas con:\n\npip install pydicom numpy")
    sys.exit(1)


def aplicar_mascara(imagen, mascara):
    """Aplica una máscara a la imagen."""
    return np.where(mascara, imagen, 0)


def generar_mascara_personalizada(filas, cols):
    """Genera una máscara que elimina la región inferior-izquierda."""
    m = np.ones((filas, cols), dtype=np.uint8)
    for y in range(filas):
        if y > 150:
            m[y, :y // 2] = 0
    return m


def clasificar_plano(ds, umbral=0.8):
    """Clasifica el plano de la imagen (sagital, coronal, axial, etc.)."""
    iop = getattr(ds, 'ImageOrientationPatient', None)
    if iop is None:
        return "desconocido"
    row = np.array(iop[0:3], float)
    col = np.array(iop[3:6], float)
    normal = np.cross(row, col)
    norm = np.linalg.norm(normal)
    if norm == 0:
        return "desconocido"
    normal /= norm
    ax, ay, az = abs(normal[0]), abs(normal[1]), abs(normal[2])
    if ax > umbral and ax > ay and ax > az:
        return "sagital"
    if ay > umbral and ay > ax and ay > az:
        return "coronal"
    if az > umbral and az > ax and az > ay:
        return "axial"
    return "oblicuo"


class AnonimizadorDicomApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anonimizador de Imágenes DICOM")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # Variables para las rutas
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # Variables para el progreso
        self.current_operation = tk.StringVar(value="Esperando inicio...")
        self.progress_value = tk.DoubleVar(value=0.0)
        self.total_files = 0
        self.processed_files = 0

        # Crear la interfaz
        self.create_widgets()

        # Configuración de estilos
        self.configure_styles()

    def configure_styles(self):
        """Configura los estilos de la interfaz."""
        self.root.configure(bg="#f5f5f5")
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))

    def create_widgets(self):
        """Crea los elementos de la interfaz."""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(main_frame, text="Anonimizador de Imágenes DICOM",
                                style="Header.TLabel")
        title_label.pack(pady=(0, 20))

        # Marco para selección de carpetas
        folders_frame = ttk.Frame(main_frame)
        folders_frame.pack(fill=tk.X, pady=10)

        # Carpeta de entrada
        input_label = ttk.Label(folders_frame, text="Carpeta de entrada:")
        input_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        input_entry = ttk.Entry(folders_frame, textvariable=self.input_path, width=50)
        input_entry.grid(row=0, column=1, padx=5, pady=5)

        input_button = ttk.Button(folders_frame, text="Examinar...",
                                  command=self.browse_input_folder)
        input_button.grid(row=0, column=2, pady=5)

        # Carpeta de salida
        output_label = ttk.Label(folders_frame, text="Carpeta de salida:")
        output_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        output_entry = ttk.Entry(folders_frame, textvariable=self.output_path, width=50)
        output_entry.grid(row=1, column=1, padx=5, pady=5)

        output_button = ttk.Button(folders_frame, text="Examinar...",
                                   command=self.browse_output_folder)
        output_button.grid(row=1, column=2, pady=5)

        # Botones de acción
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)

        start_button = ttk.Button(buttons_frame, text="Iniciar Proceso",
                                  command=self.start_process)
        start_button.pack(side=tk.RIGHT, padx=5)

        # Información de progreso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)

        operation_label = ttk.Label(progress_frame, textvariable=self.current_operation)
        operation_label.pack(fill=tk.X, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_value,
                                            mode="determinate", length=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Área de log
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        log_label = ttk.Label(log_frame, text="Registro de actividad:")
        log_label.pack(anchor=tk.W)

        self.log_text = tk.Text(log_frame, height=10, width=50, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Estado inicial
        self.log_text.insert(tk.END, "Aplicación iniciada. Seleccione las carpetas de entrada y salida.\n")
        self.log_text.config(state=tk.DISABLED)

    def browse_input_folder(self):
        """Abre un diálogo para seleccionar la carpeta de entrada."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de entrada")
        if folder:
            self.input_path.set(folder)
            self.update_log(f"Carpeta de entrada seleccionada: {folder}")

    def browse_output_folder(self):
        """Abre un diálogo para seleccionar la carpeta de salida."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_path.set(folder)
            self.update_log(f"Carpeta de salida seleccionada: {folder}")

    def update_log(self, message):
        """Actualiza el área de registro con un nuevo mensaje."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_progress(self, message, increment=False):
        """Actualiza la información de progreso."""
        self.current_operation.set(message)
        if increment and self.total_files > 0:
            self.processed_files += 1
            self.progress_value.set((self.processed_files / self.total_files) * 100)
        self.root.update_idletasks()  # Actualizar la interfaz

    def count_total_files(self, input_folder):
        """Cuenta el número total de archivos DICOM en la carpeta de entrada."""
        total = 0
        self.update_log("Contando archivos...")
        for root, _, files in os.walk(input_folder):
            dicoms = [f for f in files if not f.startswith('.')]
            total += len(dicoms)
        return total

    def start_process(self):
        """Inicia el proceso de anonimización en un hilo separado."""
        input_folder = self.input_path.get()
        output_folder = self.output_path.get()

        if not input_folder or not os.path.isdir(input_folder):
            messagebox.showerror("Error", "La carpeta de entrada no es válida.")
            return

        if not output_folder:
            messagebox.showerror("Error", "Debe seleccionar una carpeta de salida.")
            return

        # Crear carpeta de salida si no existe
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Reiniciar variables de progreso
        self.processed_files = 0
        self.progress_value.set(0)
        self.update_progress("Contando archivos...")
        self.total_files = self.count_total_files(input_folder)
        self.update_log(f"Se encontraron {self.total_files} archivos para procesar.")

        # Iniciar proceso en un hilo separado
        thread = threading.Thread(target=self.process_files,
                                  args=(input_folder, output_folder))
        thread.daemon = True
        thread.start()

    def process_files(self, input_folder, output_folder):
        """Procesa los archivos DICOM en la carpeta de entrada."""
        try:
            self.update_progress("Iniciando procesamiento...")
            self.update_log("Iniciando procesamiento de archivos DICOM...")

            pacientes = [d for d in os.listdir(input_folder)
                         if os.path.isdir(os.path.join(input_folder, d))]
            if not pacientes:
                pacientes = [""]  # usar la raíz como un único paciente

            for idx_p, pac in enumerate(pacientes, start=1):
                tag_p = f"Paciente_{idx_p:04d}"
                in_p = os.path.join(input_folder, pac) if pac else input_folder
                out_p = os.path.join(output_folder, tag_p)
                os.makedirs(out_p, exist_ok=True)

                self.update_progress(f"Procesando {tag_p}: {in_p}")
                self.update_log(f"Procesando {tag_p}: {in_p}")

                for root, _, files in os.walk(in_p):
                    dicoms = [f for f in files if not f.startswith('.')]
                    if not dicoms:
                        continue

                    # Leer la serie para usar su descripción
                    try:
                        ds0 = pydicom.dcmread(os.path.join(root, dicoms[0]), force=True)
                        serie = ds0.get("SeriesDescription", "SinDescripcion").replace(" ", "_")
                    except Exception:
                        serie = "SinDescripcion"

                    for f in dicoms:
                        ruta = os.path.join(root, f)
                        try:
                            self.update_progress(f"Procesando {serie}/{f}", increment=False)

                            ds = pydicom.dcmread(ruta, force=True)

                            # 1) Anonimizar
                            ds.PatientName = tag_p
                            ds.PatientID = tag_p
                            ds.OtherPatientIDs = None
                            ds.PatientBirthDate = ""
                            ds.PatientSex = ""

                            # 2) Detectar plano
                            plano = "sin_pixel"
                            if hasattr(ds, "pixel_array"):
                                plano = clasificar_plano(ds)

                            # 3) Aplicar máscara solo en sagitales
                            if plano == "sagital":
                                img = ds.pixel_array
                                m = generar_mascara_personalizada(*img.shape)
                                rec = aplicar_mascara(img, m)
                                ds.PixelData = rec.tobytes()

                            # 4) Construir carpeta de destino:
                            #    OUTPUT/Paciente_XXXX/plano/SerieDescription/
                            plano_dir = os.path.join(out_p, plano)
                            serie_dir = os.path.join(plano_dir, serie)
                            os.makedirs(serie_dir, exist_ok=True)

                            # 5) Guardar el DICOM procesado
                            destino = os.path.join(serie_dir, f)
                            ds.save_as(destino)

                            self.update_log(f"[{plano}] {serie}/{f} → guardado en {plano}/{serie}")
                            self.update_progress(f"Procesado: {serie}/{f}", increment=True)

                        except Exception as e:
                            self.update_log(f"⚠️ Error procesando '{ruta}': {e}")
                            self.update_progress(f"Error: {ruta}", increment=True)

            # Proceso completado
            self.update_progress("Proceso completado", increment=False)
            self.update_log("¡Proceso de anonimización completado con éxito!")

            # Mostrar mensaje de finalización
            messagebox.showinfo("Proceso Completado",
                                f"Se han anonimizado {self.processed_files} archivos DICOM.\n"
                                f"Los archivos se han guardado en:\n{output_folder}")

        except Exception as e:
            self.update_log(f"Error general: {e}")
            messagebox.showerror("Error", f"Ha ocurrido un error durante el procesamiento:\n{e}")
            self.update_progress("Error en el proceso", increment=False)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnonimizadorDicomApp(root)
    root.mainloop()