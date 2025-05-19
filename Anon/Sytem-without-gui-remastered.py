#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonimizar_y_recortar_por_plano.py

Recorre las subcarpetas de pacientes en INPUT_FOLDER,
anonimiza todos los DICOMs y aplica un recorte facial solamente
en los cortes sagitales, clasificando cada archivo en su carpeta
de plano correspondiente dentro de cada paciente.
"""

import os
import sys

try:
    import pydicom
    import numpy as np
except ImportError:
    print("Instala primero las dependencias con:\n    pip install pydicom numpy")
    sys.exit(1)


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
INPUT_FOLDER  = "/Users/patricksext/PycharmProjects/PythonProject/18380000"
OUTPUT_FOLDER = "salida"
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←


def aplicar_mascara(imagen, mascara):
    return np.where(mascara, imagen, 0)


def generar_mascara_personalizada(filas, cols):
    # máscara que elimina la región inferior-izquierda
    m = np.ones((filas, cols), dtype=np.uint8)
    for y in range(filas):
        if y > 150:
            m[y, :y//2] = 0
    return m


def clasificar_plano(ds, umbral=0.8):
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


def anonimizar_y_recortar_por_plano(input_folder, output_folder):
    if not os.path.isdir(input_folder):
        print(f"ERROR: '{input_folder}' no existe o no es carpeta.")
        return

    pacientes = [d for d in os.listdir(input_folder)
                 if os.path.isdir(os.path.join(input_folder, d))]
    if not pacientes:
        pacientes = [""]  # usar la raíz como un único paciente

    for idx_p, pac in enumerate(pacientes, start=1):
        tag_p = f"Paciente_{idx_p:04d}"
        in_p = os.path.join(input_folder, pac) if pac else input_folder
        out_p = os.path.join(output_folder, tag_p)
        os.makedirs(out_p, exist_ok=True)
        print(f"\nProcesando {tag_p}: {in_p}")

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
                    ds = pydicom.dcmread(ruta, force=True)

                    # 1) Anonimizar
                    ds.PatientName      = tag_p
                    ds.PatientID        = tag_p
                    ds.OtherPatientIDs  = None
                    ds.PatientBirthDate = ""
                    ds.PatientSex       = ""

                    # 2) Detectar plano
                    plano = "sin_pixel"
                    if hasattr(ds, "pixel_array"):
                        plano = clasificar_plano(ds)

                    # 3) Aplicar máscara solo en sagitales
                    if plano == "sagital":
                        img = ds.pixel_array
                        m   = generar_mascara_personalizada(*img.shape)
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

                    print(f"  • [{plano:8}] {serie}/{f} → guardado en {plano}/{serie}")

                except Exception as e:
                    print(f"  ⚠️ Error procesando '{ruta}': {e}")


if __name__ == "__main__":
    anonimizar_y_recortar_por_plano(INPUT_FOLDER, OUTPUT_FOLDER)
