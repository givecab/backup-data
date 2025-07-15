import os
import shutil
import psutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def list_drives():
    """Devuelve la lista de puntos de montaje o letras de unidad."""
    partitions = psutil.disk_partitions(all=False)
    drives = []
    for p in partitions:
        # Windows: device letra, Linux/macOS: mountpoint
        drives.append(p.device if os.name == 'nt' else p.mountpoint)
    return drives


def backup_files(src, dest, extensions):
    """Copia archivos de src a dest filtrando por extensions."""
    count = 0
    base = src.rstrip(os.sep) + os.sep
    for root, _, files in os.walk(base):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                src_path = os.path.join(root, file)
                rel = os.path.relpath(src_path, base)
                target_dir = os.path.join(dest, os.path.dirname(rel))
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(src_path, os.path.join(dest, rel))
                count += 1
    return count


def main():
    root = tk.Tk()
    root.title("Backup Data")
    root.geometry("600x250")

    drives = list_drives()
    extensions = ['.pdf', '.xlsx', '.docx']

    # Frame disco
    frame1 = ttk.LabelFrame(root, text="Seleccionar unidad")
    frame1.pack(fill='x', padx=10, pady=5)
    drive_var = tk.StringVar(value=drives[0] if drives else '')
    drive_cb = ttk.Combobox(frame1, textvariable=drive_var, values=drives, state='readonly')
    drive_cb.pack(fill='x', padx=5, pady=5)

    # Frame extensiones
    frame2 = ttk.LabelFrame(root, text="Extensiones (ctrl+click para multi)")
    frame2.pack(fill='x', padx=10, pady=5)
    ext_vars = []
    for ext in extensions:
        var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(frame2, text=ext, variable=var)
        chk.pack(side='left', padx=5)
        ext_vars.append((ext, var))
    new_ext_entry = ttk.Entry(frame2, width=10)
    new_ext_entry.pack(side='left', padx=5)
    def add_ext():
        e = new_ext_entry.get().strip().lower()
        if e:
            if not e.startswith('.'):
                e = '.' + e
            if e not in [v[0] for v in ext_vars]:
                var = tk.BooleanVar(value=True)
                chk = ttk.Checkbutton(frame2, text=e, variable=var)
                chk.pack(side='left', padx=5)
                ext_vars.append((e, var))
        new_ext_entry.delete(0, tk.END)
    ttk.Button(frame2, text="Añadir", command=add_ext).pack(side='left', padx=5)

    # Frame destino
    frame3 = ttk.LabelFrame(root, text="Carpeta destino")
    frame3.pack(fill='x', padx=10, pady=5)
    dest_var = tk.StringVar()
    dest_entry = ttk.Entry(frame3, textvariable=dest_var)
    dest_entry.pack(fill='x', side='left', padx=5, pady=5, expand=True)
    def browse_dest():
        path = filedialog.askdirectory()
        if path:
            dest_var.set(path)
    ttk.Button(frame3, text="Seleccionar", command=browse_dest).pack(side='left', padx=5)

    # Botón
    def start_backup():
        drive = drive_var.get()
        dest = dest_var.get()
        exts = [ext for ext, var in ext_vars if var.get()]
        if not drive or not dest or not exts:
            messagebox.showerror("Error", "Complete todos los campos.")
            return
        if messagebox.askyesno("Confirmar", f"Backup {exts} de {drive} a {dest}?"):
            count = backup_files(drive, dest, exts)
            messagebox.showinfo("Completado", f"Archivos copiados: {count}")

    ttk.Button(root, text="Iniciar Backup", command=start_backup).pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
