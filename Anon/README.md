# Anonimizador de Imágenes DICOM

## Descripción General

Esta aplicación permite anonimizar archivos DICOM médicos y aplicar un procesamiento específico a las imágenes sagitales para mejorar la privacidad del paciente. El programa está diseñado para facilitar el manejo de estudios médicos con fines de investigación o docencia, eliminando información personal y aplicando técnicas de protección para regiones faciales.

## Requisitos Previos

- Python 3.6 o superior
- Bibliotecas requeridas: `pydicom`, `numpy`, `tkinter` (generalmente incluido con Python)

Para instalar las dependencias:
```
pip install pydicom numpy
```

## Cómo Usar la Aplicación

1. Ejecute el programa haciendo doble clic en el ejecutable o mediante `python anonimizador_dicom_gui.py`
2. Seleccione la carpeta de entrada que contiene las imágenes DICOM originales
3. Seleccione la carpeta de salida donde se guardarán los archivos procesados
4. Haga clic en "Iniciar Proceso"
5. Observe el progreso en la barra de progreso y el área de registro
6. Al finalizar, recibirá una notificación

## Flujo de Trabajo Detallado

### 1. Estructura de Entrada

El programa está diseñado para trabajar con una estructura de carpetas donde:

```
Carpeta_Entrada/
├── Paciente1/
│   ├── Serie1/
│   │   ├── imagen1.dcm
│   │   ├── imagen2.dcm
│   ├── Serie2/
│   │   ├── ...
├── Paciente2/
│   ├── ...
```

También puede procesar una estructura plana donde todos los archivos DICOM estén en una sola carpeta.

### 2. Proceso por Cada Paciente

Por cada carpeta de paciente, el programa realiza los siguientes pasos:

1. **Identificación del paciente**: Asigna un nuevo identificador anónimo (ej. "Paciente_0001")
2. **Exploración de archivos**: Recorre recursivamente todas las subcarpetas buscando archivos DICOM
3. **Identificación de series**: Detecta las series de imágenes basándose en la etiqueta "SeriesDescription" de los archivos DICOM

### 3. Proceso por Cada Archivo DICOM

Para cada archivo DICOM encontrado:

1. **Lectura**: Lee el archivo DICOM con sus metadatos y contenido de píxeles
2. **Anonimización**: Elimina/modifica la siguiente información personal:
   - Nombre del paciente → Reemplazado por "Paciente_XXXX"
   - ID del paciente → Reemplazado por un número secuencial
   - IDs adicionales → Eliminados
   - Fecha de nacimiento → Eliminada
   - Sexo → Eliminado

3. **Clasificación del plano anatómico**: Analiza la orientación de la imagen para determinar si es:
   - Sagital (vista lateral)
   - Coronal (vista frontal)
   - Axial (vista superior/inferior)
   - Oblicuo (otros ángulos)
   - Desconocido (cuando no se puede determinar)

4. **Procesamiento específico para imágenes sagitales**:
   - Si la imagen es sagital, aplica una máscara para eliminar la región inferior izquierda
   - Esta máscara está diseñada específicamente para ocultar características faciales que podrían permitir la identificación del paciente

### 4. Estructura de Salida

Los archivos procesados se organizan en una nueva estructura:

```
Carpeta_Salida/
├── Paciente_0001/
│   ├── sagital/
│   │   ├── Serie_A/
│   │   │   ├── imagen1.dcm
│   │   │   ├── imagen2.dcm
│   ├── axial/
│   │   ├── Serie_B/
│   │   │   ├── ...
│   ├── coronal/
│   │   ├── ...
├── Paciente_0002/
│   ├── ...
```

Esta estructura organiza los archivos por:
1. Paciente (con identificador anónimo)
2. Plano anatómico (sagital, axial, coronal, etc.)
3. Descripción de la serie
4. Archivos individuales (manteniendo los nombres originales)

## Funciones Específicas

### Generación de Máscara

La función `generar_mascara_personalizada` crea una máscara binaria que:
- Mantiene todos los píxeles en la parte superior de la imagen
- En la parte inferior (y>150), elimina aproximadamente la mitad izquierda de la imagen
- Esta máscara está específicamente diseñada para eliminar las características faciales en imágenes sagitales de cabeza y cuello

### Clasificación de Planos

La función `clasificar_plano` analiza la orientación del paciente en la imagen (etiqueta DICOM "ImageOrientationPatient") para determinar con precisión si se trata de un plano sagital, coronal o axial, siguiendo estos pasos:
1. Extrae los vectores de orientación de la imagen
2. Calcula el vector normal al plano de la imagen
3. Determina qué eje (X, Y o Z) tiene la mayor proyección del vector normal
4. Clasifica la imagen según el eje dominante

## Notas Importantes

- Las imágenes sagitales son las únicas que reciben un procesamiento adicional con máscara para proteger la privacidad facial
- El programa mantiene la estructura original de los datos DICOM para preservar su utilidad clínica/científica
- Todos los datos DICOM anonimizados conservan su integridad técnica y son compatibles con cualquier visor DICOM estándar

## Resolución de Problemas

Si encuentra errores durante el procesamiento:
1. Verifique que los archivos de entrada sean archivos DICOM válidos
2. Asegúrese de tener permisos de lectura/escritura en las carpetas de entrada y salida
3. Consulte el registro de actividad para identificar errores específicos
4. Para errores persistentes, revise los mensajes de error en el área de registro
