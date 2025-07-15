#!/usr/bin/env python3
"""
backup_data.py
Script con Tkinter para respaldo de archivos por extensión.
- Excluye carpetas OneDrive y directorios específicos.
- Crea backup_data_<fecha> en destino y subcarpetas por extensión.
- Copia archivo por archivo durante la iteración inmediatamente.
- Pide elevación en Windows.
- Muestra barra de progreso indeterminada y contador de archivos copiados.
- Botón de cancelación que detiene el proceso y elimina backup creado.
"""
import os
import shutil
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Verificar permisos de administrador en Windows
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
# Directorios de configuración a excluir
config_excludes = ['AppData', 'Application Data', 'Local Settings', 'LocalSettings', '.config', '.cache']

# Flag global de cancelación
dGlobal_cancel = False

def main():
    ensure_admin()
    root = tk.Tk()
    root.title('Backup Data')
    root.geometry('700x600')

    # Variables
    start_var = tk.StringVar(value=os.path.expanduser('~'))
    dest_var = tk.StringVar()
    excl_var = tk.StringVar()
    ext_vars = {}

    # 1. Carpeta inicio
    frm1 = ttk.LabelFrame(root, text='1. Carpeta de inicio')
    frm1.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm1, textvariable=start_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm1, text='Seleccionar...', command=lambda: start_var.set(filedialog.askdirectory(initialdir=start_var.get()))).pack(side='left', padx=5)

    # 2. Extensiones
    frm2 = ttk.LabelFrame(root, text='2. Seleccione extensiones')
    frm2.pack(fill='both', padx=10, pady=5, expand=True)
    for idx, ext in enumerate(default_exts):
        var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm2, text=ext, variable=var).grid(row=idx//4, column=idx%4, sticky='w', padx=5, pady=2)
        ext_vars[ext] = var
    new_ext = ttk.Entry(frm2, width=12)
    new_ext.grid(row=(len(default_exts)//4)+1, column=0, padx=5, pady=5)
    ttk.Button(frm2, text='Añadir extensión', command=lambda:
        (lambda e=new_ext.get().strip().lower():
            new_ext.delete(0, 'end') or (ext_vars.setdefault(e if e.startswith('.') else '.'+e, tk.BooleanVar(value=True)) and ttk.Checkbutton(frm2, text=e, variable=ext_vars[e if e.startswith('.') else '.'+e]).grid(row=len(ext_vars)//4, column=len(ext_vars)%4, sticky='w', padx=5, pady=2)) 
        )()
    ).grid(row=(len(default_exts)//4)+1, column=1, padx=5, pady=5)

    # 3. Excluir dirs
    frm3 = ttk.LabelFrame(root, text='3. Excluir directorios (coma separados)')
    frm3.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm3, textvariable=excl_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Label(frm3, text='ej: temp,.git,node_modules').pack(side='left', padx=5)

    # 4. Carpeta destino
    frm4 = ttk.LabelFrame(root, text='4. Carpeta destino')
    frm4.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm4, textvariable=dest_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm4, text='Seleccionar...', command=lambda: dest_var.set(filedialog.askdirectory(initialdir=dest_var.get() or os.path.expanduser('~')))).pack(side='left', padx=5)

    # Barra y estado
    pbar = ttk.Progressbar(root, orient='horizontal', length=660, mode='indeterminate')
    pbar.pack(padx=10, pady=(10,0))
    status = ttk.Label(root, text='Esperando acción...')
    status.pack(padx=10, pady=(2,10))

    # Funciones
    def cancel_backup():
        global dGlobal_cancel
        dGlobal_cancel = True

    def start_backup():
        global dGlobal_cancel
        dGlobal_cancel = False
        start = start_var.get(); dest = dest_var.get()
        exts = [e for e, var in ext_vars.items() if var.get()]
        excludes = [d.strip() for d in excl_var.get().split(',') if d.strip()]
        if not os.path.isdir(start) or not dest or not exts:
            messagebox.showerror('Error', 'Complete inicio, destino y extensiones.')
            return
        if not messagebox.askyesno('Confirmar', 'Iniciar backup?'): return
        # Estructura
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_root = os.path.join(dest, f'backup_data_{date_str}')
        try:
            os.makedirs(backup_root, exist_ok=True)
            for ext in exts: os.makedirs(os.path.join(backup_root, ext[1:]), exist_ok=True)
        except Exception as e:
            messagebox.showerror('Error', f'{e}')
            return
        # UI
        start_btn.config(state='disabled'); cancel_btn.config(state='normal'); pbar.start(10); status.config(text='Copiando archivos...')

        def worker():
            count = 0
            for root_dir, dirs, files in os.walk(start, topdown=True):
                dirs[:] = [d for d in dirs if not any(ce.lower() in d.lower() for ce in config_excludes) and not any(ex.lower() in os.path.join(root_dir, d).lower() for ex in excludes) and os.path.commonpath([os.path.abspath(backup_root), os.path.abspath(os.path.join(root_dir, d))]) != os.path.abspath(backup_root)]
                if dGlobal_cancel:
                    shutil.rmtree(backup_root, ignore_errors=True)
                    root.after(0, lambda: messagebox.showinfo('Cancelado', 'Backup cancelado'))
                    root.after(0, reset_ui)
                    return
                for f in files:
                    if dGlobal_cancel: break
                    ext = os.path.splitext(f)[1].lower()
                    if ext in exts:
                        try:
                            shutil.copy2(os.path.join(root_dir, f), os.path.join(backup_root, ext[1:], f))
                            count += 1
                            root.after(0, lambda c=count: status.config(text=f'Copiados: {c} archivos'))
                        except Exception as e:
                            root.after(0, lambda f=f, e=e: messagebox.showwarning('Error copia', f'Error copiando {f}: {e}'))
                            shutil.rmtree(backup_root, ignore_errors=True)
                            root.after(0, reset_ui)
                            return
            root.after(0, lambda: pbar.stop())
            root.after(0, lambda: status.config(text=f'Backup completado: {count} archivos'))
            root.after(0, lambda: messagebox.showinfo('Terminado', f'Se copiaron {count} archivos.'))
            root.after(0, lambda: reset_ui())

        threading.Thread(target=worker, daemon=True).start()

    def reset_ui():
        start_btn.config(state='normal'); cancel_btn.config(state='disabled'); pbar.stop(); status.config(text='Esperando acción...')

    # Botones
    btn_frame = ttk.Frame(root); btn_frame.pack(pady=10)
    start_btn = ttk.Button(btn_frame, text='Iniciar Backup', command=start_backup); start_btn.pack(side='left', padx=5)
    cancel_btn = ttk.Button(btn_frame, text='Cancelar', command=cancel_backup, state='disabled'); cancel_btn.pack(side='left', padx=5)

    root.mainloop()

if __name__ == '__main__':
    main()
