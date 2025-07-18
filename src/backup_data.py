#!/usr/bin/env python3
"""
backup_data.py

Script con Tkinter para respaldar archivos por extensión.
- Excluye carpetas de configuración local (AppData, .config, .cache, Configuracion Local) y rutas de usuario.
- Crea carpeta backup_data_<timestamp> en destino con subcarpetas por extensión.
- Copia archivo por archivo en un hilo no bloqueante.
- Requiere elevación de administrador en Windows.
- Muestra barra de progreso indeterminada y contador de archivos copiados.
- Loguea exclusiones y copias con print para depuración.
- Skips individual files that produce errors during copy.

Para excluir un archivo específico, añade su nombre exacto al parámetro `user_excludes` en la UI.
"""
import os
import shutil
import sys
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Extensiones y carpetas de configuración a excluir
default_exts = ['.pdf', '.xlsx', '.docx', '.jpg', '.png', '.mp4', '.mp3', '.txt']
config_excludes = ['AppData', '.config', '.cache', 'Local Settings', 'LocalSettings', 'Configuracion Local']


def ensure_admin():
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        if not is_admin:
            messagebox.showinfo('Elevación', 'Se requieren permisos de administrador. Reiniciando...')
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
            sys.exit()


def should_include_dir(root_dir, d, backup_root, user_excludes):
    full = os.path.join(root_dir, d)
    # Excluir carpetas de configuración o definidas por el usuario
    for ex in config_excludes + user_excludes:
        if ex and ex.lower() in full.lower():
            print(f"Excluyendo carpeta: {full} (patrón: {ex})")
            return False
    # No descender en la propia carpeta de backup
    if backup_root:
        try:
            if os.path.commonpath([os.path.abspath(backup_root), os.path.abspath(full)]) == os.path.abspath(backup_root):
                print(f"Omitiendo carpeta backup: {full}")
                return False
        except ValueError:
            pass
    return True


def main():
    ensure_admin()
    root = tk.Tk()
    root.title('Backup Data')
    root.geometry('720x640')

    # Variables UI
    start_var = tk.StringVar(value=os.path.expanduser('~'))
    dest_var = tk.StringVar()
    excl_var = tk.StringVar()
    file_excl_var = tk.StringVar()  # para excluir archivos por nombre exacto
    ext_vars = {ext: tk.BooleanVar(value=True) for ext in default_exts}

    # UI: Carpeta inicio
    frm1 = ttk.LabelFrame(root, text='1. Carpeta de inicio')
    frm1.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm1, textvariable=start_var).pack(side='left', fill='x', expand=True, padx=5)
    ttk.Button(frm1, text='Seleccionar...',
               command=lambda: start_var.set(filedialog.askdirectory(initialdir=start_var.get()))).pack(side='left', padx=5)

    # UI: Extensiones
    frm2 = ttk.LabelFrame(root, text='2. Seleccione extensiones')
    frm2.pack(fill='both', padx=10, pady=5, expand=True)
    for i, ext in enumerate(default_exts):
        ttk.Checkbutton(frm2, text=ext, variable=ext_vars[ext]).grid(row=i//4, column=i%4, sticky='w', padx=5, pady=2)
    new_ext = ttk.Entry(frm2, width=12)
    new_ext.grid(row=(len(default_exts)//4)+1, column=0, padx=5, pady=5)
    def add_ext():
        e = new_ext.get().strip().lower(); new_ext.delete(0,'end')
        if e and not e.startswith('.'):
            e = '.' + e
        if e and e not in ext_vars:
            ext_vars[e] = tk.BooleanVar(value=True)
            idx = list(ext_vars).index(e)
            ttk.Checkbutton(frm2, text=e, variable=ext_vars[e]).grid(row=idx//4, column=idx%4, sticky='w', padx=5, pady=2)
            print(f'Extensión añadida: {e}')
    ttk.Button(frm2, text='Añadir ext', command=add_ext).grid(row=(len(default_exts)//4)+1, column=1, padx=5, pady=5)

    # UI: Excluir dirs
    frm3 = ttk.LabelFrame(root, text='3. Excluir directorios (coma separados)')
    frm3.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm3, textvariable=excl_var).pack(side='left', fill='x', expand=True, padx=5)
    ttk.Label(frm3, text='ej: temp,.git,node_modules').pack(side='left', padx=5)

    # UI: Excluir archivos específicos
    frm_file_excl = ttk.LabelFrame(root, text='4. Excluir archivos (por nombre, coma separados)')
    frm_file_excl.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm_file_excl, textvariable=file_excl_var).pack(side='left', fill='x', expand=True, padx=5)
    ttk.Label(frm_file_excl, text='ej: secret.pdf,temp.xlsx').pack(side='left', padx=5)

    # UI: Carpeta destino
    frm4 = ttk.LabelFrame(root, text='5. Carpeta destino')
    frm4.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm4, textvariable=dest_var).pack(side='left', fill='x', expand=True, padx=5)
    ttk.Button(frm4, text='Seleccionar...',
               command=lambda: dest_var.set(filedialog.askdirectory(initialdir=dest_var.get() or os.path.expanduser('~')))
              ).pack(side='left', padx=5)

    # Barra y estado
    pbar = ttk.Progressbar(root, orient='horizontal', length=700, mode='indeterminate')
    pbar.pack(pady=5)
    status = ttk.Label(root, text='Esperando acción...')
    status.pack()

    # Botones control
    ctrl = ttk.Frame(root); ctrl.pack(pady=10)
    btn_start = ttk.Button(ctrl, text='Iniciar Backup')
    btn_start.pack(side='left', padx=5)
    btn_cancel = ttk.Button(ctrl, text='Cancelar', state='disabled')
    btn_cancel.pack(side='left', padx=5)

    backup_root = None
    cancel_flag = False

    def start_backup():
        nonlocal backup_root, cancel_flag
        src = start_var.get(); dst = dest_var.get()
        exts = [e for e, v in ext_vars.items() if v.get()]
        user_excl_dirs = [x.strip() for x in excl_var.get().split(',') if x.strip()]
        user_excl_files = [x.strip() for x in file_excl_var.get().split(',') if x.strip()]
        print(f"Inicio={src}, Dest={dst}, Exts={exts}, DirExcl={user_excl_dirs}, FileExcl={user_excl_files}")
        if not os.path.isdir(src) or not dst or not exts:
            messagebox.showerror('Error', 'Complete origen, destino y extensiones.'); return
        if not messagebox.askyesno('Confirmar', '¿Iniciar backup?'): return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_root = os.path.join(dst, f'backup_data_{ts}')
        try:
            os.makedirs(backup_root, exist_ok=True)
            for e in exts:
                os.makedirs(os.path.join(backup_root, e[1:]), exist_ok=True)
        except Exception as err:
            messagebox.showerror('Error', f'Error creando estructura: {err}')
            return
        print(f"Estructura en {backup_root}")
        btn_start.config(state='disabled'); btn_cancel.config(state='normal'); pbar.start(10); status.config(text='Copiando archivos...')
        cancel_flag = False

        def worker():
            count = 0
            for rd, dirs, files in os.walk(src, topdown=True):
                dirs[:] = [d for d in dirs if should_include_dir(rd, d, backup_root, user_excl_dirs)]
                print(f"Procesando carpeta: {rd}, subdirs={dirs}")
                if cancel_flag:
                    shutil.rmtree(backup_root, ignore_errors=True)
                    root.after(0, lambda: messagebox.showinfo('Cancelado', 'Backup cancelado'))
                    root.after(0, reset_ui)
                    return
                for f in files:
                    if f in user_excl_files:
                        print(f"Saltando archivo excluido: {f}")
                        continue
                    ext = os.path.splitext(f)[1].lower()
                    if ext in exts:
                        src_path = os.path.join(rd, f)
                        dst_dir = os.path.join(backup_root, ext[1:])
                        print(f"Copiando {src_path} -> {dst_dir}")
                        try:
                            shutil.copy2(src_path, os.path.join(dst_dir, f))
                            count += 1
                            root.after(0, lambda c=count: status.config(text=f'Copiados: {c} archivos'))
                        except Exception as e:
                            print(f"Error copiando {f}: {e}, saltando")
                            continue
            print(f"Backup finalizado, total: {count} archivos copiados")
            root.after(0, pbar.stop)
            root.after(0, lambda: status.config(text=f'Backup completado: {count} archivos'))
            root.after(0, lambda: messagebox.showinfo('Terminado', f'Se copiaron {count} archivos.'))
            root.after(0, reset_ui)
        threading.Thread(target=worker, daemon=True).start()

    def cancel_backup():
        nonlocal cancel_flag
        cancel_flag = True
        print('Cancelación solicitada')

    def reset_ui():
        btn_start.config(state='normal')
        btn_cancel.config(state='disabled')
        pbar.stop()
        status.config(text='Esperando acción...')

    btn_start.config(command=start_backup)
    btn_cancel.config(command=cancel_backup)

    root.mainloop()

if __name__ == '__main__':
    main()
