#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visualizar_dicoms_individuales.py

Lee todos los ficheros DICOM de la carpeta especificada (aunque no tengan extensión),
y los muestra uno a uno con Matplotlib.
"""

import os
import sys

try:
    import pydicom
    import matplotlib.pyplot as plt
except ImportError:
    print("Instala primero las dependencias con:\n    pip install pydicom matplotlib")
    sys.exit(1)


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
#  AQUI DEFINE TU CARPETA
FOLDER_PATH = '/Users/patricksext/PycharmProjects/PythonProject/salida/Paciente_0001 (raíz)/SinDesc'
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
            if hasattr(ds, 'pixel_array'):
                datasets.append((fname, ds))
        except Exception:
            # No es un DICOM válido o está corrupto
            continue
    if not datasets:
        raise RuntimeError(f"No se encontró ningún DICOM válido en '{folder_path}'.")
    return datasets


def mostrar_dicoms_individuales(datasets):
    """Muestra cada DICOM por separado con Matplotlib."""
    for idx, (fname, ds) in enumerate(datasets, start=1):
        img = ds.pixel_array
        plt.figure(figsize=(6, 6))
        plt.imshow(img, cmap='gray')
        title = getattr(ds, 'InstanceNumber', idx)
        plt.title(f"{idx}/{len(datasets)} – {fname}  (InstanceNumber={title})")
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        # Si prefieres pausa automática, descomenta la siguiente línea:
        # plt.pause(1)


def main():
    print(f"Cargando DICOM de {FOLDER_PATH} …")
    datasets = cargar_dicom_de_carpeta(FOLDER_PATH)

    print(f"Mostrando {len(datasets)} imágenes DICOM …")
    mostrar_dicoms_individuales(datasets)


if __name__ == '__main__':
    main()
