import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os

def create_users_table():
    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aadhaar_number TEXT,
            mobile_number TEXT,
            fingerprint BLOB,
            age INTEGER
        )
    ''')

    connection.commit()
    connection.close()

def insert_data(aadhaar_number, mobile_number, fingerprint_file_path, age):
    create_users_table()  # Make sure the table exists

    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    # Read the image file as binary data
    with open(fingerprint_file_path, 'rb') as file:
        fingerprint_data = file.read()

    cursor.execute('INSERT INTO users (aadhaar_number, mobile_number, fingerprint, age) VALUES (?, ?, ?, ?)',
                   (aadhaar_number, mobile_number, fingerprint_data, age))

    connection.commit()
    connection.close()

    messagebox.showinfo("Success", f"Record with Aadhaar number {aadhaar_number} added successfully!")

def show_users_table():
    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()

    connection.close()

    table_window = tk.Toplevel()
    table_window.title("Users Table")

    tree = ttk.Treeview(table_window)

    tree["columns"] = ("ID", "Aadhaar Number", "Mobile Number", "Fingerprint", "Age")

    tree.column("#0", width=0, stretch=tk.NO)
    tree.column("ID", anchor=tk.W, width=100)
    tree.column("Aadhaar Number", anchor=tk.W, width=100)
    tree.column("Mobile Number", anchor=tk.W, width=100)
    tree.column("Fingerprint", anchor=tk.W, width=100)
    tree.column("Age", anchor=tk.W, width=100)

    tree.heading("#0", text="", anchor=tk.W)
    tree.heading("ID", text="ID", anchor=tk.W)
    tree.heading("Aadhaar Number", text="Aadhaar Number", anchor=tk.W)
    tree.heading("Mobile Number", text="Mobile Number", anchor=tk.W)
    tree.heading("Fingerprint", text="Fingerprint", anchor=tk.W)
    tree.heading("Age", text="Age", anchor=tk.W)

    for row in data:
        tree.insert("", tk.END, values=row)

    tree.pack(expand=tk.YES, fill=tk.BOTH)

def delete_data(aadhaar_number):
    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM users WHERE aadhaar_number = ?', (aadhaar_number,))

    connection.commit()
    connection.close()

    messagebox.showinfo("Success", f"Record with Aadhaar number {aadhaar_number} deleted successfully!")

def browse_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
    fingerprint_entry.delete(0, tk.END)
    fingerprint_entry.insert(0, file_path)

# Tkinter GUI section
create_users_table()

root = tk.Tk()
root.title("biometric_data.db")
root.configure(bg="#F8F8FF")

aadhaar_label = tk.Label(root, text="Aadhaar Number:", bg="#F8F8FF")
aadhaar_label.pack(pady=5)
aadhaar_entry = tk.Entry(root)
aadhaar_entry.pack(pady=5)

mobile_label = tk.Label(root, text="Mobile Number:", bg="#F8F8FF")
mobile_label.pack(pady=5)
mobile_entry = tk.Entry(root)
mobile_entry.pack(pady=5)

age_label = tk.Label(root, text="Age:", bg="#F8F8FF")
age_label.pack(pady=5)
age_entry = tk.Entry(root)
age_entry.pack(pady=5)

fingerprint_label = tk.Label(root, text="Fingerprint Image:", bg="#F8F8FF")
fingerprint_label.pack(pady=5)
fingerprint_entry = tk.Entry(root)
fingerprint_entry.pack(pady=5, side=tk.LEFT)
browse_button = tk.Button(root, text="Browse", command=browse_image, bg="#32CD32", fg="white")
browse_button.pack(pady=5, side=tk.RIGHT)

insert_button = tk.Button(root, text="Insert Data",
                          command=lambda: insert_data(aadhaar_entry.get(), mobile_entry.get(), fingerprint_entry.get(), age_entry.get()),
                          bg="#32CD32", fg="white")
insert_button.pack(pady=10)

show_table_button = tk.Button(root, text="Show Users Table", command=show_users_table, bg="#32CD32", fg="white")
show_table_button.pack(pady=10)

delete_label = tk.Label(root, text="Aadhaar Number to Delete:", bg="#F8F8FF")
delete_label.pack(pady=5)
delete_entry = tk.Entry(root)
delete_entry.pack(pady=5)

delete_button = tk.Button(root, text="Delete Data", command=lambda: delete_data(delete_entry.get()), bg="#FF6347", fg="white")
delete_button.pack(pady=10)

root.mainloop()
