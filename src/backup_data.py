#!/usr/bin/env python3
"""
backup_data.py
Script con Tkinter para respaldo de archivos por extensión.
- Excluye carpetas OneDrive y directorios específicos.
- Crea backup_data_<fecha> en destino y subcarpetas por extensión.
- Copia archivo por archivo durante la iteración inmediatamente.
- Pide elevación en Windows.
- Muestra barra de progreso indeterminada y contador de archivos copiados.
- Incluye logs con print para depuración.
"""
import os
import shutil
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Solicitar permisos de administrador en Windows
def ensure_admin():
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        if not is_admin:
            messagebox.showinfo('Elevación', 'Se requieren permisos de administrador. Reiniciando con privilegios...')
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
            sys.exit()

# Extensiones por defecto
default_exts = ['.pdf', '.xlsx', '.docx', '.jpg', '.png', '.mp4', '.mp3', '.txt']

def main():
    ensure_admin()
    root = tk.Tk()
    root.title('Backup Data')
    root.geometry('700x560')

    # Variables
    start_var = tk.StringVar(value=os.path.expanduser('~'))
    dest_var = tk.StringVar()
    excl_var = tk.StringVar()
    ext_vars = {}

    # 1. Carpeta de inicio
    frm_start = ttk.LabelFrame(root, text='1. Carpeta de inicio')
    frm_start.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm_start, textvariable=start_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm_start, text='Seleccionar...', command=lambda:
        start_var.set(filedialog.askdirectory(initialdir=start_var.get()))
    ).pack(side='left', padx=5)

    # 2. Extensiones en cuadrícula 4 columnas
    frm_ext = ttk.LabelFrame(root, text='2. Seleccione extensiones')
    frm_ext.pack(fill='both', padx=10, pady=5, expand=True)
    for idx, ext in enumerate(default_exts):
        var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(frm_ext, text=ext, variable=var)
        chk.grid(row=idx//4, column=idx%4, sticky='w', padx=5, pady=2)
        ext_vars[ext] = var
    # Campo para añadir extensiones
    new_ext = ttk.Entry(frm_ext, width=12)
    new_ext.grid(row=(len(default_exts)//4)+1, column=0, padx=5, pady=5)
    def add_extension():
        e = new_ext.get().strip().lower()
        new_ext.delete(0, 'end')
        if e and not e.startswith('.'):
            e = '.' + e
        if e and e not in ext_vars:
            idx = len(ext_vars)
            row, col = divmod(idx, 4)
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(frm_ext, text=e, variable=var)
            chk.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            ext_vars[e] = var
            print(f"Añadida extensión: {e}")
    ttk.Button(frm_ext, text='Añadir extensión', command=add_extension).grid(
        row=(len(default_exts)//4)+1, column=1, padx=5, pady=5
    )

    # 3. Directorios a excluir
    frm_excl = ttk.LabelFrame(root, text='3. Excluir directorios (coma separados)')
    frm_excl.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm_excl, textvariable=excl_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Label(frm_excl, text='p.ej: temp,.git,node_modules').pack(side='left', padx=5)

    # 4. Carpeta destino
    frm_dest = ttk.LabelFrame(root, text='4. Carpeta de destino')
    frm_dest.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm_dest, textvariable=dest_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm_dest, text='Seleccionar...', command=lambda:
        dest_var.set(filedialog.askdirectory(initialdir=dest_var.get() or os.path.expanduser('~')))
    ).pack(side='left', padx=5)

    # Barra de progreso y estado
    pbar = ttk.Progressbar(root, orient='horizontal', length=660, mode='indeterminate')
    pbar.pack(padx=10, pady=(10,0))
    status = ttk.Label(root, text='Esperando acción...')
    status.pack(padx=10, pady=(2,10))

    # Botón Iniciar Backup
    def start_backup():
        start = start_var.get()
        dest = dest_var.get()
        exts = [e for e, var in ext_vars.items() if var.get()]
        excludes = [d.strip() for d in excl_var.get().split(',') if d.strip()]
        print(f"Iniciando backup: start={start}, dest={dest}, exts={exts}, excludes={excludes}")
        # Validar
        if not os.path.isdir(start) or not dest or not exts:
            messagebox.showerror('Error', 'Complete inicio, destino y extensiones.')
            return
        if not messagebox.askyesno('Confirmar', 'Iniciar backup?'):
            return
        # Crear estructura de backup
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_root = os.path.join(dest, f'backup_data_{date_str}')
        try:
            os.makedirs(backup_root, exist_ok=True)
            for ext in exts:
                os.makedirs(os.path.join(backup_root, ext[1:]), exist_ok=True)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo crear estructura: {e}')
            return
        print(f"Estructura creada en {backup_root}")
        # Preparar UI
        start_btn.config(state='disabled')
        pbar.start(10)
        status.config(text='Copiando archivos...')

        # Worker Thread
        def worker():
            count = 0
            print("Worker iniciado")
            for root_dir, dirs, files in os.walk(start, topdown=True):
                print(f"Procesando carpeta: {root_dir}")
                dirs[:] = [d for d in dirs if 'OneDrive' not in d and not any(ex.lower() in os.path.join(root_dir, d).lower() for ex in excludes)]
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in exts:
                        src = os.path.join(root_dir, f)
                        dest_dir = os.path.join(backup_root, ext[1:])
                        print(f"Copiando {src} -> {dest_dir}")
                        try:
                            shutil.copy2(src, os.path.join(dest_dir, f))
                            count += 1
                            root.after(0, lambda c=count: status.config(text=f'Copiados: {c} archivos'))
                        except Exception as e:
                            print(f"Error copiando {f}: {e}")
                            root.after(0, lambda f=f, e=e: messagebox.showwarning('Error copia', f'Error copiando {f}: {e}'))
                            break
            print(f"Worker finalizado, total copiados: {count}")
            # Finalizar UI
            root.after(0, pbar.stop)
            root.after(0, lambda: status.config(text=f'Backup completado: {count} archivos'))
            root.after(0, lambda: messagebox.showinfo('Terminado', f'Se copiaron {count} archivos.'))
            root.after(0, lambda: start_btn.config(state='normal'))
        threading.Thread(target=worker, daemon=True).start()

    start_btn = ttk.Button(root, text='Iniciar Backup', command=start_backup)
    start_btn.pack(pady=(0,10))
    root.mainloop()

if __name__ == '__main__':
    main()
