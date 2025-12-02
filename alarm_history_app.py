import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import psycopg2
from psycopg2 import pool
from tkcalendar import DateEntry
import threading
import csv
import json

# สมมติว่าไฟล์นี้มีอยู่จริงสำหรับการรันโค้ด
# from modbus_alarm_service import ModbusAlarmMonitor 
# หากไม่มีไฟล์ modbus_alarm_service ให้ใช้ ModbusAlarmMonitor_Dummy แทน
class ModbusAlarmMonitor_Dummy:
    def __init__(self):
        self.running = False
        self.active_alarms = 0
    def start(self):
        self.running = True
    def stop(self):
        self.running = False
    def get_status(self):
        # จำลองสถานะ
        if self.running:
            self.active_alarms = (self.active_alarms + 1) % 5
            return {'modbus_connected': True, 'active_alarms': self.active_alarms}
        return {'modbus_connected': False, 'active_alarms': 0}
ModbusAlarmMonitor = ModbusAlarmMonitor_Dummy

class AlarmHistoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alarm History Log System with Modbus Monitor")
        self.root.geometry("1500x750")
        
        # 🎨 **DARK MODE COLOR PALETTE**
        self.primary_bg = '#212529' # Dark Gray Background (Main)
        self.secondary_bg = '#343a40' # Slightly Lighter Dark Gray (Frames/Input)
        self.text_color = '#f8f9fa' # Light Text
        self.accent_color = '#007bff' # Blue (Primary Action)
        self.success_color = '#28a745' # Green
        self.danger_color = '#dc3545' # Red
        self.info_color = '#17a2b8' # Cyan/Info
        self.disabled_color = '#495057' # Darker Gray for disabled elements
        self.tree_fg = '#ced4da' # Light Gray Text for Treeview

        self.root.configure(bg=self.primary_bg)
        
        # Modbus Monitor
        self.modbus_monitor = None
        self.monitor_status_label = None
        
        # Database connection pool - *ใช้การตั้งค่าเดิม*
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                user="admin",
                password="admin123",
                host="localhost",
                port="5432",
                database="alarm_history"
            )
            if self.connection_pool:
                print("Connection pool created successfully")
        except Exception as e:
            messagebox.showerror("Database Error", f"Cannot connect to database:\n{str(e)}")
            # self.connection_pool = None 

        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
        # Start status update timer
        self.update_monitor_status()
        
    def get_connection(self):
        """Get connection from pool"""
        if hasattr(self, 'connection_pool') and self.connection_pool:
            return self.connection_pool.getconn()
        return None
    
    def return_connection(self, connection):
        """Return connection to pool"""
        if hasattr(self, 'connection_pool') and self.connection_pool and connection:
            self.connection_pool.putconn(connection)

    def setup_styles(self):
        """Configure ttk styles for Dark Mode"""
        style = ttk.Style()
        style.theme_use('clam') 
        
        # 🎨 **Universal Text Style**
        style.configure('.', background=self.primary_bg, foreground=self.text_color)
        
        # 🎨 **TButton (Standard Button)**
        style.configure('TButton', font=('Arial', 10, 'bold'), borderwidth='1', relief='flat', foreground=self.text_color, background=self.secondary_bg)
        style.map('TButton', 
                 foreground=[('active', self.text_color), ('disabled', self.disabled_color)],
                 background=[('!disabled', self.secondary_bg), ('active', self.disabled_color)])

        # 🎨 **TCombobox & TEntry**
        style.configure('TCombobox', font=('Arial', 10), fieldbackground=self.secondary_bg, background=self.secondary_bg, foreground=self.tree_fg, bordercolor=self.disabled_color)
        style.map('TCombobox', fieldbackground=[('readonly', self.secondary_bg)], background=[('readonly', self.secondary_bg)])
        
        # 🎨 **Treeview (ตาราง)**
        style.configure('Treeview', 
                        font=('Arial', 10), 
                        rowheight=25,
                        background=self.secondary_bg,
                        foreground=self.tree_fg,
                        fieldbackground=self.secondary_bg,
                        borderwidth=0)
        
        # 🎨 **Treeview Heading**
        style.configure('Treeview.Heading', 
                        font=('Arial', 11, 'bold'), 
                        background=self.disabled_color, # Darker Header background
                        foreground=self.text_color,
                        relief='flat')
        style.map('Treeview.Heading', background=[('active','#6c757d')]) # Slightly lighter on hover
        
        # 🎨 **Treeview Selection (Important for readability)**
        style.map('Treeview', background=[('selected', self.accent_color)], foreground=[('selected', self.text_color)])
        
        # 🎨 **Scrollbar**
        style.configure('Vertical.TScrollbar', gripcount=0, background=self.disabled_color, darkcolor=self.disabled_color, lightcolor=self.secondary_bg, troughcolor=self.primary_bg, bordercolor=self.primary_bg, arrowcolor=self.tree_fg)
        style.configure('Horizontal.TScrollbar', gripcount=0, background=self.disabled_color, darkcolor=self.disabled_color, lightcolor=self.secondary_bg, troughcolor=self.primary_bg, bordercolor=self.primary_bg, arrowcolor=self.tree_fg)

    def create_widgets(self):
        """Create UI widgets"""
        
        # 📦 **Title and Control Frame**
        header_frame = tk.Frame(self.root, bg=self.primary_bg)
        header_frame.pack(pady=10, padx=20, fill='x')
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Alarm History Log System", 
            font=('Arial', 24, 'bold'),
            bg=self.primary_bg,
            fg=self.text_color
        )
        title_label.pack(side='left')
        
        # Modbus Control Frame
        modbus_control_frame = tk.Frame(header_frame, bg=self.primary_bg)
        modbus_control_frame.pack(side='right', padx=10)
        
        # Status indicator
        self.monitor_status_label = tk.Label(
            modbus_control_frame,
            text="● Disconnected",
            font=('Arial', 12, 'bold'),
            fg=self.danger_color,
            bg=self.primary_bg
        )
        self.monitor_status_label.pack(side='left', padx=10)
        
        # Start/Stop button - **ใช้ tk.Button เพื่อควบคุมสีพื้นหลังของปุ่มโดยตรง**
        self.modbus_btn = tk.Button(
            modbus_control_frame,
            text="Start Monitoring",
            bg=self.success_color,
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.toggle_modbus_monitor,
            padx=15,
            pady=5,
            relief='flat' 
        )
        self.modbus_btn.pack(side='left', padx=5)
        
        # Config button
        config_btn = tk.Button(
            modbus_control_frame,
            text="⚙ Config",
            bg=self.disabled_color, # สีเทาเข้ม
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.open_config_window,
            padx=10,
            pady=5,
            relief='flat' 
        )
        config_btn.pack(side='left', padx=5)
        
        # 📦 **Filter Frame**
        filter_frame = tk.Frame(self.root, bg=self.primary_bg)
        filter_frame.pack(pady=10, padx=20, fill='x')
        
        # 🏷️ Label Style
        label_style = {'bg': self.primary_bg, 'font': ('Arial', 10), 'fg': self.text_color}
        
        # Row 0 & 1: Date Range
        tk.Label(filter_frame, text="From Date", **label_style).grid(row=0, column=0, sticky='w', padx=5, pady=(5, 0))
        tk.Label(filter_frame, text="To Date", **label_style).grid(row=0, column=2, sticky='w', padx=5, pady=(5, 0))
        tk.Label(filter_frame, text="Type", **label_style).grid(row=0, column=4, sticky='w', padx=5, pady=(5, 0))
        
        # 📅 DateEntry - **ใช้สีเข้มสำหรับพื้นหลัง**
        self.from_date = DateEntry(
            filter_frame, 
            width=12, 
            background=self.secondary_bg, 
            foreground=self.tree_fg, 
            borderwidth=2,
            date_pattern='dd/mm/yyyy',
            selectbackground=self.accent_color, # สีเมื่อเลือกวันที่
            selectforeground='white'
        )
        self.from_date.grid(row=1, column=0, padx=5, pady=(0, 5))
        
        # 🕐 Time Entry - **ใช้ ttk.Entry เพื่อให้ได้ Style ที่เข้ากัน**
        self.from_time = ttk.Entry(filter_frame, width=10, font=('Arial', 10))
        self.from_time.insert(0, "00:00:00")
        self.from_time.grid(row=1, column=1, padx=5, pady=(0, 5))
        
        self.to_date = DateEntry(
            filter_frame, 
            width=12, 
            background=self.secondary_bg, 
            foreground=self.tree_fg, 
            borderwidth=2,
            date_pattern='dd/mm/yyyy',
            selectbackground=self.accent_color,
            selectforeground='white'
        )
        self.to_date.grid(row=1, column=2, padx=5, pady=(0, 5))
        
        self.to_time = ttk.Entry(filter_frame, width=10, font=('Arial', 10))
        self.to_time.insert(0, "23:59:59")
        self.to_time.grid(row=1, column=3, padx=5, pady=(0, 5))
        
        # 🔽 Type Filter
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.type_var,
            values=['All', 'Alarm', 'Event'],
            state='readonly',
            width=15
        )
        self.type_combo.set('All')
        self.type_combo.grid(row=1, column=4, padx=5, pady=(0, 5), sticky='w')
        
        # Row 2 & 3: Description, Status, Search
        tk.Label(filter_frame, text="Description", **label_style).grid(row=2, column=0, sticky='w', padx=5, pady=(5, 0))
        tk.Label(filter_frame, text="Status", **label_style).grid(row=2, column=2, sticky='w', padx=5, pady=(5, 0))
        tk.Label(filter_frame, text="Search (Keyword)", **label_style).grid(row=2, column=4, sticky='w', padx=5, pady=(5, 0))
        
        # 🔽 Description Filter
        self.description_var = tk.StringVar()
        self.description_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.description_var,
            state='readonly',
            width=30
        )
        self.description_combo.set('All')
        self.description_combo.grid(row=3, column=0, columnspan=2, padx=5, pady=(0, 5), sticky='ew')
        
        # 🔽 Status Filter
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.status_var,
            values=['All', 'Normal', 'Fault', 'Restart', 'Clear', 'Test'],
            state='readonly',
            width=15
        )
        self.status_combo.set('All')
        self.status_combo.grid(row=3, column=2, padx=5, pady=(0, 5), sticky='w')
        
        # 🔍 Search Box
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            filter_frame, 
            textvariable=self.search_var,
            width=30,
            font=('Arial', 10)
        )
        search_entry.grid(row=3, column=4, padx=5, pady=(0, 5), sticky='ew')
        
        # 🔎 Search Button
        search_btn = tk.Button(
            filter_frame,
            text="Search",
            bg=self.accent_color,
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.search_data,
            padx=15,
            pady=5,
            relief='flat'
        )
        search_btn.grid(row=3, column=5, padx=5, pady=(0, 5))
        
        # 📦 **Table Frame**
        table_frame = tk.Frame(self.root, bg=self.secondary_bg)
        table_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical')
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # 📋 Treeview
        columns = ('Item', 'Log no.', 'Date/Time', 'Type', 'Description', 'Status', 'Machine')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=15,
            selectmode='browse' 
        )
        
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Configure columns (ใช้ค่าเดิม)
        column_widths = {
            'Item': 60,
            'Log no.': 120,
            'Date/Time': 180,
            'Type': 80,
            'Description': 300,
            'Status': 100,
            'Machine': 150
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor='center')
            self.tree.column(col, width=column_widths[col], anchor='center')
        
        self.tree.pack(fill='both', expand=True)
        
        # 🎨 **Configure row colors (Tags) - ใช้สีอ่อนลงและนุ่มนวลขึ้นใน Dark Mode**
        self.tree.tag_configure('alarm', background='#3e3e3e', foreground='#ffc107') # Yellowish text on dark gray
        self.tree.tag_configure('event', background='#3e3e3e', foreground='#28a745') # Green text on dark gray
        self.tree.tag_configure('fault', background='#3e3e3e', foreground='#dc3545') # Red text on dark gray
        self.tree.tag_configure('normal', background=self.secondary_bg, foreground=self.tree_fg) # Default Dark Gray
        
        # 📦 **Bottom Frame**
        bottom_frame = tk.Frame(self.root, bg=self.primary_bg)
        bottom_frame.pack(pady=10, padx=20, fill='x')
        
        # Record count
        self.record_label = tk.Label(
            bottom_frame,
            text="Total Records: 0",
            bg=self.primary_bg,
            fg=self.text_color,
            font=('Arial', 10, 'bold')
        )
        self.record_label.pack(side='left')
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = tk.Checkbutton(
            bottom_frame,
            text="Auto-refresh (5s)",
            variable=self.auto_refresh_var,
            bg=self.primary_bg,
            fg=self.text_color,
            selectcolor=self.secondary_bg, 
            font=('Arial', 9)
        )
        auto_refresh_cb.pack(side='left', padx=20)
        
        # 🔄 Refresh Button
        refresh_btn = tk.Button(
            bottom_frame,
            text="Refresh",
            bg=self.success_color,
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.load_data,
            padx=15,
            pady=5,
            relief='flat'
        )
        refresh_btn.pack(side='right', padx=5)
        
        # 📁 Export Button
        export_btn = tk.Button(
            bottom_frame,
            text="Export CSV",
            bg=self.info_color,
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.export_csv,
            padx=15,
            pady=5,
            relief='flat'
        )
        export_btn.pack(side='right', padx=5)
        
        # Load descriptions for filter
        self.load_descriptions()
        
        # Start auto-refresh timer
        self.auto_refresh_data()
    
    # เมธอดที่เหลือใช้การทำงานเดิม โดยมีการปรับสีใน config_window ด้วย
    
    def toggle_modbus_monitor(self):
        """Start or stop Modbus monitoring"""
        if self.modbus_monitor is None:
            self.modbus_monitor = ModbusAlarmMonitor()
            
        if not self.modbus_monitor.running:
            try:
                threading.Thread(target=self.modbus_monitor.start, daemon=True).start()
                self.modbus_btn.config(text="Stop Monitoring", bg=self.danger_color)
                messagebox.showinfo("Success", "Modbus monitoring started")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start monitoring:\n{str(e)}")
        else:
            self.modbus_monitor.stop()
            self.modbus_btn.config(text="Start Monitoring", bg=self.success_color)
            messagebox.showinfo("Success", "Modbus monitoring stopped")

    def update_monitor_status(self):
        """Update Modbus monitor status display"""
        if self.modbus_monitor and self.modbus_monitor.running:
            status = self.modbus_monitor.get_status()
            if status['modbus_connected']:
                self.monitor_status_label.config(
                    text=f"● Connected ({status['active_alarms']} active)",
                    fg=self.success_color
                )
            else:
                self.monitor_status_label.config(
                    text="● Connecting...",
                    fg='orange'
                )
        else:
            self.monitor_status_label.config(
                text="● Disconnected",
                fg=self.danger_color
            )
        self.root.after(2000, self.update_monitor_status)

    def open_config_window(self):
        """Open configuration window"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Modbus Configuration")
        config_window.geometry("500x300")
        config_window.configure(bg=self.primary_bg)
        config_window.resizable(False, False)
        
        try:
            with open('modbus_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {
                "modbus": {"host": "192.168.1.100", "port": 502},
                "monitoring": {"scan_interval": 1.0}
            }
        
        tk.Label(config_window, text="Modbus TCP Settings", 
                font=('Arial', 14, 'bold'), bg=self.primary_bg, fg=self.text_color).pack(pady=10)
        
        form_frame = tk.Frame(config_window, bg=self.primary_bg)
        form_frame.pack(pady=10, padx=20, fill='x')
        
        # Host
        tk.Label(form_frame, text="Host/IP:", bg=self.primary_bg, fg=self.text_color).grid(row=0, column=0, sticky='w', pady=5)
        host_entry = ttk.Entry(form_frame, width=30)
        host_entry.insert(0, config['modbus']['host'])
        host_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Port
        tk.Label(form_frame, text="Port:", bg=self.primary_bg, fg=self.text_color).grid(row=1, column=0, sticky='w', pady=5)
        port_entry = ttk.Entry(form_frame, width=30)
        port_entry.insert(0, str(config['modbus']['port']))
        port_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Scan interval
        tk.Label(form_frame, text="Scan Interval (sec):", bg=self.primary_bg, fg=self.text_color).grid(row=2, column=0, sticky='w', pady=5)
        interval_entry = ttk.Entry(form_frame, width=30)
        interval_entry.insert(0, str(config['monitoring']['scan_interval']))
        interval_entry.grid(row=2, column=1, pady=5, padx=10)
        
        def save_config():
            try:
                config['modbus']['host'] = host_entry.get()
                config['modbus']['port'] = int(port_entry.get())
                config['monitoring']['scan_interval'] = float(interval_entry.get())
                
                with open('modbus_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                
                messagebox.showinfo("Success", "Configuration saved", parent=config_window)
                config_window.destroy()
            except ValueError:
                 messagebox.showerror("Error", "Port and Scan Interval must be numbers.", parent=config_window)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}", parent=config_window)
        
        tk.Button(config_window, text="Save", command=save_config,
                 bg=self.success_color, fg='white', padx=30, pady=5, relief='flat').pack(pady=20)
    
    def auto_refresh_data(self):
        """Auto-refresh data every 5 seconds"""
        if self.auto_refresh_var.get():
            self.load_data()
        self.root.after(5000, self.auto_refresh_data)
    
    def load_descriptions(self):
        """Load unique descriptions for filter"""
        connection = None
        try:
            connection = self.get_connection()
            if not connection: return
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT description FROM alarm_history ORDER BY description")
            descriptions = ['All'] + [row[0] for row in cursor.fetchall()]
            self.description_combo['values'] = descriptions
            cursor.close()
        except Exception:
            pass
        finally:
            if connection:
                self.return_connection(connection)
    
    def load_data(self):
        """Load data from database"""
        connection = None
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            connection = self.get_connection()
            if not connection: return
            cursor = connection.cursor()
            
            query = """
                SELECT log_no, date_time, type, description, status, machine 
                FROM alarm_history 
                ORDER BY date_time DESC
                LIMIT 1000
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for idx, row in enumerate(rows, start=1):
                log_no, date_time, alarm_type, description, status, machine = row
                date_time_str = date_time.strftime('%d/%m/%Y %H:%M:%S')
                
                tag = ''
                if alarm_type and alarm_type.lower() == 'alarm':
                    tag = 'alarm'
                elif alarm_type and alarm_type.lower() == 'event':
                    tag = 'event'
                
                if status and status.lower() == 'fault':
                    tag = 'fault'
                elif status and status.lower() == 'normal':
                    tag = 'normal'
                
                self.tree.insert('', 'end', values=(
                    idx, log_no, date_time_str, alarm_type, description, status, machine
                ), tags=(tag,))
            
            self.record_label.config(text=f"Total Records: {len(rows)}")
            cursor.close()
            
        except Exception:
            pass
        finally:
            if connection:
                self.return_connection(connection)
    
    def search_data(self):
        """Search data with filters"""
        connection = None
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            connection = self.get_connection()
            if not connection: return
            cursor = connection.cursor()
            
            query = """
                SELECT log_no, date_time, type, description, status, machine 
                FROM alarm_history 
                WHERE 1=1
            """
            params = []
            
            # Date range filter
            try:
                from_datetime = datetime.strptime(
                    f"{self.from_date.get_date().strftime('%Y-%m-%d')} {self.from_time.get()}",
                    '%Y-%m-%d %H:%M:%S'
                )
                to_datetime = datetime.strptime(
                    f"{self.to_date.get_date().strftime('%Y-%m-%d')} {self.to_time.get()}",
                    '%Y-%m-%d %H:%M:%S'
                )
                query += " AND date_time BETWEEN %s AND %s"
                params.extend([from_datetime, to_datetime])
            except ValueError:
                messagebox.showwarning("Warning", "Invalid time format (must be HH:MM:SS)", parent=self.root)
                return
            except Exception:
                pass
            
            if self.type_var.get() != 'All':
                query += " AND type = %s"
                params.append(self.type_var.get())
            
            if self.description_var.get() != 'All':
                query += " AND description = %s"
                params.append(self.description_var.get())
            
            if self.status_var.get() != 'All':
                query += " AND status = %s"
                params.append(self.status_var.get())
            
            if self.search_var.get():
                query += " AND (description ILIKE %s OR log_no ILIKE %s OR machine ILIKE %s)"
                search_term = f"%{self.search_var.get()}%"
                params.extend([search_term, search_term, search_term])
            
            query += " ORDER BY date_time DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for idx, row in enumerate(rows, start=1):
                log_no, date_time, alarm_type, description, status, machine = row
                date_time_str = date_time.strftime('%d/%m/%Y %H:%M:%S')
                
                tag = ''
                if alarm_type and alarm_type.lower() == 'alarm':
                    tag = 'alarm'
                elif alarm_type and alarm_type.lower() == 'event':
                    tag = 'event'
                
                if status and status.lower() == 'fault':
                    tag = 'fault'
                elif status and status.lower() == 'normal':
                    tag = 'normal'
                
                self.tree.insert('', 'end', values=(
                    idx, log_no, date_time_str, alarm_type, description, status, machine
                ), tags=(tag,))
            
            self.record_label.config(text=f"Total Records: {len(rows)}")
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error searching data:\n{str(e)}")
        finally:
            if connection:
                self.return_connection(connection)
    
    def export_csv(self):
        """Export data to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Alarm History Log"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Item', 'Log no.', 'Date/Time', 'Type', 'Description', 'Status', 'Machine'])
                    
                    for item in self.tree.get_children():
                        values = self.tree.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("Success", f"Data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting data:\n{str(e)}")
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'modbus_monitor') and self.modbus_monitor:
            self.modbus_monitor.stop()
        
        if hasattr(self, 'connection_pool') and self.connection_pool:
            self.connection_pool.closeall()

def main():
    root = tk.Tk()
    app = AlarmHistoryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()