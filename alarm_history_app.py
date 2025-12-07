import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import DateEntry
import threading
import csv
import json
from database import DatabaseManager
from styled_button import StyledButton

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
        self.root.title("SPRC SPM Alarm History Log System")
        self.root.geometry("1500x750")
        
        # 🎨 **DARK MODE COLOR PALETTE**
        self.primary_bg = '#1a1a1a' # Very Dark Background
        self.secondary_bg = '#2d2d2d' # Dark Gray (Frames/Input)
        self.text_color = '#ffffff' # White Text
        self.accent_color = '#0066cc' # Bright Blue (Primary Action)
        self.success_color = '#28a745' # Green
        self.danger_color = '#ff4444' # Bright Red
        self.info_color = '#17a2b8' # Cyan/Info
        self.disabled_color = '#555555' # Medium Gray
        self.tree_fg = '#e0e0e0' # Light Gray Text
        self.button_hover = '#0052a3' # Darker Blue on hover
        self.border_color = '#444444' # Border color

        self.root.configure(bg=self.primary_bg)
        
        # Modbus Monitor
        self.modbus_monitor = None
        self.monitor_status_label = None
        
        # Load configuration from app_config.json
        try:
            with open('app_config.json', 'r') as f:
                config = json.load(f)
            print("Configuration loaded from app_config.json")
        except FileNotFoundError:
            print("app_config.json not found. Using default configuration.")
            config = {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'alarm_history',
                    'user': 'admin',
                    'password': 'admin123'
                }
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing app_config.json: {e}")
            config = {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'alarm_history',
                    'user': 'admin',
                    'password': 'admin123'
                }
            }
        
        try:
            self.db_manager = DatabaseManager(config)
            print("Database connection established successfully")
        except Exception as e:
            messagebox.showerror("Database Error", f"Cannot connect to database:\n{str(e)}")
            self.db_manager = None 

        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
        # Start status update timer
        self.update_monitor_status()
        
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
        
        # Start/Stop button - **ใช้ StyledButton เพื่อ fix สีบน macOS**
        self.modbus_btn = StyledButton(
            modbus_control_frame,
            text="Start Monitoring",
            command=self.toggle_modbus_monitor,
            bg_color=self.success_color,
            fg_color='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8,
            activebackground='#20c232'
        )
        self.modbus_btn.pack(side='left', padx=8)
        
        # Config button
        config_btn = StyledButton(
            modbus_control_frame,
            text="⚙ Config",
            command=self.open_config_window,
            bg_color=self.disabled_color,
            fg_color='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=8,
            activebackground='#666666'
        )
        config_btn.pack(side='left', padx=5)
        
        # 📦 **Filter Frame**
        filter_frame = tk.Frame(self.root, bg=self.primary_bg)
        filter_frame.pack(pady=10, padx=20, fill='x')
        
        # 🏷️ Label Style
        label_style = {'bg': self.primary_bg, 'font': ('Arial', 11, 'bold'), 'fg': self.text_color}
        
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
            selectforeground='white',
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        self.from_date.grid(row=1, column=0, padx=5, pady=(0, 5))
        
        # 🕐 Time Entry - **ใช้ tk.Entry เพื่อให้ได้สีที่สวยงาม**
        self.from_time = tk.Entry(
            filter_frame, 
            width=12,
            font=('Arial', 11),
            bg=self.secondary_bg,
            fg=self.tree_fg,
            insertbackground=self.text_color,
            relief='solid',
            borderwidth=1
        )
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
            selectforeground='white',
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        self.to_date.grid(row=1, column=2, padx=5, pady=(0, 5))
        
        self.to_time = tk.Entry(
            filter_frame, 
            width=12,
            font=('Arial', 11),
            bg=self.secondary_bg,
            fg=self.tree_fg,
            insertbackground=self.text_color,
            relief='solid',
            borderwidth=1
        )
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
        search_entry = tk.Entry(
            filter_frame, 
            textvariable=self.search_var,
            width=35,
            font=('Arial', 11),
            bg=self.secondary_bg,
            fg=self.tree_fg,
            insertbackground=self.text_color,
            relief='solid',
            borderwidth=1
        )
        search_entry.grid(row=3, column=4, padx=5, pady=(0, 5), sticky='ew')
        search_entry.bind('<Return>', lambda e: self.search_data())
        
        # 🔎 Search Button
        search_btn = StyledButton(
            filter_frame,
            text="🔍 Search",
            command=self.search_data,
            bg_color=self.accent_color,
            fg_color='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8,
            activebackground=self.button_hover
        )
        search_btn.grid(row=3, column=5, padx=8, pady=(0, 5))
        
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
        
        # Bind double-click event to show detail popup
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
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
            font=('Arial', 12, 'bold')
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
            selectcolor=self.accent_color,
            font=('Arial', 10),
            activebackground=self.primary_bg,
            activeforeground=self.accent_color
        )
        auto_refresh_cb.pack(side='left', padx=25)
        
        # 🔄 Refresh Button
        refresh_btn = StyledButton(
            bottom_frame,
            text="🔄 Refresh",
            command=self.load_data,
            bg_color=self.success_color,
            fg_color='white',
            font=('Arial', 11, 'bold'),
            padx=18,
            pady=8,
            activebackground='#20c232'
        )
        refresh_btn.pack(side='right', padx=8)
        
        # 📁 Export Button
        export_btn = StyledButton(
            bottom_frame,
            text="📊 Export CSV",
            command=self.export_csv,
            bg_color=self.info_color,
            fg_color='white',
            font=('Arial', 11, 'bold'),
            padx=18,
            pady=8,
            activebackground='#1a9ba8'
        )
        export_btn.pack(side='right', padx=8)
        
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
                self.modbus_btn.text = "Stop Monitoring"
                self.modbus_btn.bg_color = self.danger_color
                self.modbus_btn.active_bg = '#ff5555'
                self.modbus_btn.draw_button(self.danger_color)
                messagebox.showinfo("Success", "Modbus monitoring started")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start monitoring:\n{str(e)}")
        else:
            self.modbus_monitor.stop()
            self.modbus_btn.text = "Start Monitoring"
            self.modbus_btn.bg_color = self.success_color
            self.modbus_btn.active_bg = '#20c232'
            self.modbus_btn.draw_button(self.success_color)
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
        config_window.title("Application Configuration")
        config_window.geometry("500x300")
        config_window.configure(bg=self.primary_bg)
        config_window.resizable(False, False)
        
        try:
            with open('app_config.json', 'r') as f:
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
        
        tk.Label(form_frame, text="Host/IP:", bg=self.primary_bg, fg=self.text_color, font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=8)
        host_entry = tk.Entry(form_frame, width=35, font=('Arial', 11), bg=self.secondary_bg, fg=self.tree_fg, insertbackground=self.text_color, relief='solid', borderwidth=1)
        host_entry.insert(0, config['modbus']['host'])
        host_entry.grid(row=0, column=1, pady=8, padx=10)
        
        # Port
        tk.Label(form_frame, text="Port:", bg=self.primary_bg, fg=self.text_color, font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=8)
        port_entry = tk.Entry(form_frame, width=35, font=('Arial', 11), bg=self.secondary_bg, fg=self.tree_fg, insertbackground=self.text_color, relief='solid', borderwidth=1)
        port_entry.insert(0, str(config['modbus']['port']))
        port_entry.grid(row=1, column=1, pady=8, padx=10)
        
        # Scan interval
        tk.Label(form_frame, text="Scan Interval (sec):", bg=self.primary_bg, fg=self.text_color, font=('Arial', 11)).grid(row=2, column=0, sticky='w', pady=8)
        interval_entry = tk.Entry(form_frame, width=35, font=('Arial', 11), bg=self.secondary_bg, fg=self.tree_fg, insertbackground=self.text_color, relief='solid', borderwidth=1)
        interval_entry.insert(0, str(config['monitoring']['scan_interval']))
        interval_entry.grid(row=2, column=1, pady=8, padx=10)
        
        def save_config():
            try:
                config['modbus']['host'] = host_entry.get()
                config['modbus']['port'] = int(port_entry.get())
                config['monitoring']['scan_interval'] = float(interval_entry.get())
                
                with open('app_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                
                messagebox.showinfo("Success", "Configuration saved", parent=config_window)
                config_window.destroy()
            except ValueError:
                 messagebox.showerror("Error", "Port and Scan Interval must be numbers.", parent=config_window)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}", parent=config_window)
        
        tk.Button(config_window, text="💾 Save", command=save_config,
                 bg=self.success_color, fg='white', padx=30, pady=10, font=('Arial', 12, 'bold'), relief='flat', cursor='hand2', activebackground='#20c232', activeforeground='white', highlightthickness=0, bd=0, overrelief='flat').pack(pady=20)
    
    def auto_refresh_data(self):
        """Auto-refresh data every 5 seconds"""
        if self.auto_refresh_var.get():
            self.load_data()
        self.root.after(5000, self.auto_refresh_data)
    
    def load_descriptions(self):
        """Load unique descriptions for filter"""
        if not self.db_manager:
            return
        descriptions = self.db_manager.get_distinct_descriptions()
        self.description_combo['values'] = descriptions
    
    def load_data(self):
        """Load data from database (calls search to apply filters)"""
        self.search_data()
    
    def search_data(self):
        """Search data with filters"""
        if not self.db_manager:
            messagebox.showerror("Error", "Database manager not initialized")
            return
        
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Build filters dictionary
            filters = {}
            
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
                filters['start_date'] = from_datetime
                filters['end_date'] = to_datetime
            except ValueError:
                messagebox.showwarning("Warning", "Invalid time format (must be HH:MM:SS)")
                return
            except Exception as e:
                messagebox.showerror("Error", f"Date parsing error: {str(e)}")
                return
            
            if self.type_var.get() != 'All':
                filters['alarm_type'] = self.type_var.get()
            
            if self.description_var.get() != 'All':
                filters['description'] = self.description_var.get()
            
            if self.status_var.get() != 'All':
                filters['status'] = self.status_var.get()
            
            if self.search_var.get():
                filters['search_text'] = self.search_var.get()
            
            # Debug: Print filters
            # print(f"Search filters: {filters}")
            
            rows = self.db_manager.get_alarm_history(filters=filters)
            print(f"Found {len(rows)} records")
            
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
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            messagebox.showerror("Error", f"Error searching data:\n{str(e)}")
    
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
        
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close()
    
    def on_tree_double_click(self, event):
        """Handle double-click on tree row to show detail popup"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        
        if not values:
            return
        
        # Extract row data
        item_num, log_no, date_time_str, alarm_type, description, status, machine = values
        
        # Create detail popup window
        self.show_detail_popup(item_num, log_no, date_time_str, alarm_type, description, status, machine)
    
    def show_detail_popup(self, item_num, log_no, date_time_str, alarm_type, description, status, machine):
        """Show detailed information in a popup window"""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Alarm Detail - Log No. {log_no}")
        detail_window.geometry("600x500")
        detail_window.configure(bg=self.primary_bg)
        detail_window.resizable(True, True)
        
        # Make window stay on top
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        # Main frame with padding
        main_frame = tk.Frame(detail_window, bg=self.primary_bg)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text=f"Log No. {log_no}",
            bg=self.primary_bg,
            fg=self.accent_color,
            font=('Arial', 14, 'bold')
        )
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Create scrollable frame for details
        canvas = tk.Canvas(main_frame, bg=self.secondary_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.secondary_bg)
        
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Detail fields
        detail_fields = [
            ('Item Number', str(item_num)),
            ('Log Number', str(log_no)),
            ('Date & Time', str(date_time_str)),
            ('Alarm Type', str(alarm_type) if alarm_type else '-'),
            ('Status', str(status) if status else '-'),
            ('Machine', str(machine) if machine else '-'),
            ('Description', str(description) if description else '-'),
        ]
        
        for label_text, value in detail_fields:
            # Label
            label = tk.Label(
                scrollable_frame,
                text=f"{label_text}:",
                bg=self.secondary_bg,
                fg=self.accent_color,
                font=('Arial', 11, 'bold'),
                anchor='w'
            )
            label.pack(anchor='w', pady=(10, 2), padx=10)
            
            # Value
            if label_text == 'Description':
                # Use text widget for long description
                value_text = tk.Text(
                    scrollable_frame,
                    bg='#404040',
                    fg=self.text_color,
                    font=('Arial', 10),
                    height=4,
                    width=60,
                    wrap='word',
                    relief='sunken',
                    bd=1
                )
                value_text.pack(anchor='w', padx=10, pady=(2, 10), fill='both', expand=True)
                value_text.insert('1.0', value)
                value_text.config(state='disabled')
            else:
                value_label = tk.Label(
                    scrollable_frame,
                    text=value,
                    bg='#404040',
                    fg=self.tree_fg,
                    font=('Arial', 10),
                    anchor='w',
                    relief='sunken',
                    bd=1,
                    padx=8,
                    pady=5
                )
                value_label.pack(anchor='w', padx=10, pady=(2, 10), fill='x')
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.primary_bg)
        button_frame.pack(pady=(20, 0), fill='x')
        
        # Close button
        close_btn = StyledButton(
            button_frame,
            'Close',
            command=detail_window.destroy,
            bg_color=self.info_color,
            fg_color='white',
            font_spec=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        )
        close_btn.pack(side='right', padx=5)

def main():
    root = tk.Tk()
    app = AlarmHistoryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()