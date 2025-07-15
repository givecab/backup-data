#!/usr/bin/env python3
"""
backup_data.py
Script con Tkinter para respaldar archivos por extensión.
- Excluye carpetas OneDrive y directorios de configuración.
- Crea carpeta backup_data_<fecha> en destino con subcarpetas por extensión.
- Copia archivo por archivo en un hilo para no bloquear la UI.
- Requiere elevación en Windows.
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

# Extensiones y exclusiones por defecto
default_exts = ['.pdf', '.xlsx', '.docx', '.jpg', '.png', '.mp4', '.mp3', '.txt']
default_excludes = ['AppData', 'Application Data', 'Local Settings', 'LocalSettings', '.config', '.cache', 'OneDrive']

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

def should_include_dir(root_dir, d, backup_root, excludes):
    full = os.path.join(root_dir, d)
    if any(ex.lower() in full.lower() for ex in excludes):
        return False
    if backup_root:
        try:
            if os.path.commonpath([os.path.abspath(backup_root), os.path.abspath(full)]) == os.path.abspath(backup_root):
                return False
        except ValueError:
            pass
    return True

def main():
    ensure_admin()
    root = tk.Tk()
    root.title('Backup Data')
    root.geometry('700x560')

    start_var = tk.StringVar(value=os.path.expanduser('~'))
    dest_var = tk.StringVar()
    excl_var = tk.StringVar()
    ext_vars = {e: tk.BooleanVar(value=True) for e in default_exts}

    frm1 = ttk.LabelFrame(root, text='1. Carpeta de inicio')
    frm1.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm1, textvariable=start_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm1, text='Seleccionar...', command=lambda: start_var.set(filedialog.askdirectory(initialdir=start_var.get()))).pack(side='left', padx=5)

    frm2 = ttk.LabelFrame(root, text='2. Seleccione extensiones')
    frm2.pack(fill='both', padx=10, pady=5, expand=True)
    for idx, e in enumerate(default_exts):
        ttk.Checkbutton(frm2, text=e, variable=ext_vars[e]).grid(row=idx//4, column=idx%4, sticky='w', padx=5, pady=2)
    new_ext = ttk.Entry(frm2, width=12)
    new_ext.grid(row=(len(default_exts)//4)+1, column=0, padx=5, pady=5)
    def add_ext():
        e = new_ext.get().strip().lower()
        new_ext.delete(0, 'end')
        if e and not e.startswith('.'):
            e = '.' + e
        if e and e not in ext_vars:
            ext_vars[e] = tk.BooleanVar(value=True)
            idx = list(ext_vars).index(e)
            ttk.Checkbutton(frm2, text=e, variable=ext_vars[e]).grid(row=idx//4, column=idx%4, sticky='w', padx=5, pady=2)
            print(f'Añadida extensión: {e}')
    ttk.Button(frm2, text='Añadir extensión', command=add_ext).grid(row=(len(default_exts)//4)+1, column=1, padx=5, pady=5)

    frm3 = ttk.LabelFrame(root, text='3. Excluir directorios (coma separados)')
    frm3.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm3, textvariable=excl_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Label(frm3, text='p.ej: temp,.git,node_modules').pack(side='left', padx=5)

    frm4 = ttk.LabelFrame(root, text='4. Carpeta destino')
    frm4.pack(fill='x', padx=10, pady=5)
    ttk.Entry(frm4, textvariable=dest_var).pack(fill='x', side='left', padx=5, pady=5, expand=True)
    ttk.Button(frm4, text='Seleccionar...', command=lambda: dest_var.set(filedialog.askdirectory(initialdir=dest_var.get() or os.path.expanduser('~')))).pack(side='left', padx=5)

    pbar = ttk.Progressbar(root, orient='horizontal', length=660, mode='indeterminate')
    pbar.pack(padx=10, pady=(10,0))
    status = ttk.Label(root, text='Esperando acción...')
    status.pack(padx=10, pady=(2,10))

    btnf = ttk.Frame(root); btnf.pack(pady=10)
    start_btn = ttk.Button(btnf, text='Iniciar Backup'); start_btn.pack(side='left', padx=5)
    cancel_btn = ttk.Button(btnf, text='Cancelar', state='disabled'); cancel_btn.pack(side='left', padx=5)

    backup_root = None
    cancel_flag = False

    def start_backup():
        nonlocal backup_root, cancel_flag
        s = start_var.get(); d = dest_var.get()
        exts = [e for e,v in ext_vars.items() if v.get()]
        excludes = default_excludes + [x.strip() for x in excl_var.get().split(',') if x.strip()]
        print(f'Start={s},Dest={d},exts={exts},excl={excludes}')
        if not os.path.isdir(s) or not d or not exts:
            messagebox.showerror('Error','Complete inicio,destino y ext'); return
        if not messagebox.askyesno('Confirmar','Iniciar?'):return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(d,f'backup_data_{ts}')
        backup_root = path
        os.makedirs(path,exist_ok=True)
        for e in exts: os.makedirs(os.path.join(path,e[1:]),exist_ok=True)
        print('Backup root',path)
        start_btn.config(state='disabled'); cancel_btn.config(state='normal'); pbar.start(); status.config(text='Copiando...')

        def worker():
            nonlocal cancel_flag
            cnt=0
            for rd,dirs,files in os.walk(s,topdown=True):
                dirs[:] = [d for d in dirs if should_include_dir(rd,d,backup_root,excludes)]
                print('RD',rd)
                if cancel_flag:
                    shutil.rmtree(backup_root,ignore_errors=True)
                    root.after(0,lambda:messagebox.showinfo('Cancel','Cancel'))
                    root.after(0,reset_ui);return
                for f in files:
                    ext=os.path.splitext(f)[1];
                    if ext in exts:
                        src=os.path.join(rd,f);dst=os.path.join(backup_root,ext[1:],f)
                        print(f'CP {src}->{dst}')
                        try:shutil.copy2(src,dst);cnt+=1;root.after(0,lambda c=cnt:status.config(text=f'CP {c}'))
                        except Exception as ex:print('E',ex);root.after(0,reset_ui);return
            print('DONE',cnt)
            root.after(0,pbar.stop);root.after(0,lambda:status.config(text=f'Done {cnt}'));root.after(0,lambda:messagebox.showinfo('Fin',f'{cnt}'));root.after(0,reset_ui)
        threading.Thread(target=worker,daemon=True).start()

    def cancel_backup():
        nonlocal cancel_flag
        cancel_flag=True

    def reset_ui():
        start_btn.config(state='normal');cancel_btn.config(state='disabled');pbar.stop();status.config(text='Ready')

    start_btn.config(command=start_backup)
    cancel_btn.config(command=cancel_backup)

    root.mainloop()

if __name__=='__main__':main()
