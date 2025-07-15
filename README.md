# backup-data

Aplicación en Python con interfaz gráfica para:
- Listar unidades/discos disponibles.
- Seleccionar un disco.
- Filtrar archivos por extensiones (pdf, xlsx, docx, etc.).
- Copiar todos los archivos coincidentes a un directorio de destino, conservando la estructura de carpetas.

---

## Requisitos

- Python 3.8 o superior  
- Windows o Linux  
- Dependencias en `requirements.txt`

---

## Estructura del proyecto

```
backup-data/
├── README.md
├── .gitignore
├── requirements.txt
├── setup.py
├── src/
│   └── backup_data.py
└── venv/
    tests/
    └── test_backup.py
```

---

## Instalación y uso

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/tu-usuario/backup-data.git
   cd backup-data
   ```

2. **Crear y activar entorno virtual**  
   - **Unix/macOS**  
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```  
   - **Windows**  
     ```powershell
     python -m venv venv
     venv\Scripts\activate.bat
     ```

3. **Instalar dependencias**  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**  
   ```bash
   python src/backup_data.py
   ```

---

## Generar instalador MSI (Windows)

1. Instalar cx_Freeze:  
   ```bash
   pip install cx_Freeze
   ```

2. Crear el paquete:  
   ```bash
   python setup.py bdist_msi
   ```

3. El instalador `.msi` se generará en `dist/backup_data-0.1.msi`.

---

## Contribuciones

Pull requests y issues son bienvenidos.  
Por favor, abre un issue antes de enviar cambios mayores.

---
