#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mostrar_sagitales_dicoms.py

Lee todos los ficheros DICOM de la carpeta especificada (aunque no tengan extensión),
clasifica cada uno según su plano y muestra únicamente los cortes sagitales
con Matplotlib.
"""

import os
import sys

try:
    import pydicom
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError:
    print("Instala primero las dependencias con:\n    pip install pydicom numpy matplotlib")
    sys.exit(1)


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
#  AQUI DEFINE TU CARPETA
FOLDER_PATH = '/Users/patricksext/PycharmProjects/PythonProject/18380000'
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←


def cargar_dicom_de_carpeta(folder_path):
    """Lee todos los archivos de folder_path como DICOM (force=True)."""
    datasets = []
    for fname in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, fname)
        if not os.path.isfile(full_path):
            continue
        try:
            ds = pydicom.dcmread(full_path, force=True)
            if hasattr(ds, 'pixel_array') and hasattr(ds, 'ImageOrientationPatient'):
                datasets.append((fname, ds))
        except Exception:
            continue
    if not datasets:
        raise RuntimeError(f"No se encontró ningún DICOM válido con píxeles y IOP en '{folder_path}'.")
    return datasets


def clasificar_plano(ds, umbral=0.8):
    """
    Devuelve 'axial', 'coronal', 'sagital' o 'oblicuo' según ImageOrientationPatient.
    """
    iop = ds.ImageOrientationPatient
    row = np.array(iop[0:3], dtype=float)
    col = np.array(iop[3:6], dtype=float)
    normal = np.cross(row, col)
    norm = np.linalg.norm(normal)
    if norm == 0:
        return "desconocido"
    normal /= norm
    ax, ay, az = abs(normal[0]), abs(normal[1]), abs(normal[2])
    if ax > umbral and ax > ay and ax > az:
        return "sagital"
    elif ay > umbral and ay > ax and ay > az:
        return "coronal"
    elif az > umbral and az > ax and az > ay:
        return "axial"
    else:
        return "oblicuo"


def mostrar_sagitales(datasets):
    """Muestra solo los DICOM clasificados como sagitales."""
    sagitales = [(fname, ds) for fname, ds in datasets if clasificar_plano(ds) == "sagital"]
    if not sagitales:
        print("No se encontraron cortes sagitales en la carpeta.")
        return

    print(f"Mostrando {len(sagitales)} cortes sagitales:\n")
    for idx, (fname, ds) in enumerate(sagitales, start=1):
        img = ds.pixel_array
        plt.figure(figsize=(6,6))
        plt.imshow(img, cmap='gray')
        inst = getattr(ds, 'InstanceNumber', idx)
        plt.title(f"{idx}/{len(sagitales)} – {fname}  (InstanceNumber={inst})")
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        # Si prefieres avanzar automático:
        # plt.pause(1)


def main():
    print(f"Cargando DICOMs de '{FOLDER_PATH}' …")
    datasets = cargar_dicom_de_carpeta(FOLDER_PATH)
    mostrar_sagitales(datasets)


if __name__ == '__main__':
    main()
