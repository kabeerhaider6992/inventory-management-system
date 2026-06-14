
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import os
import csv
from tkinter import filedialog
import tempfile
import random

class StationeryShopSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Faizan Paper Mart - POS System")
        self.root.geometry("1200x700")
        
        # Sidebar state
        self.sidebar_collapsed = False
        self.sidebar_width = 250
        self.collapsed_width = 70
        
        # Track current active menu
        self.current_menu = None
        # Dark mode state  <-- YEH LINE ADD KARO
        self.dark_mode = False
        # Cart for purchases
        self.purchase_cart = []
        
        # Database connection
        self.db_path = "stationery.db"
        
        # Configure grid weights FIRST before creating UI
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)  # Sidebar
        self.root.grid_columnconfigure(1, weight=1)  # Main content
        
        # Create UI components in correct order
        self.create_sidebar()
        self.create_main_content()
        self.create_status_bar()
        
        # Initialize database AFTER status bar is created
        self.init_database()
        # Ensure pack columns (Default Pack mode)
        self.ensure_pack_columns()
         # Update database for pack system
        self.update_database_for_pack_system()
        
        # Show dashboard by default
        self.show_dashboard()
         # Auto fix old products for sale (runs every startup)
        self.auto_fix_old_products_for_sale()
        # Auto-archive old data on startup (optional)
        self.auto_archive_old_data()
    
    def init_database(self):
        """Initialize database and create all tables"""
        try:
            # Connect to database (creates file if not exists)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # ========== 1. SUPPLIERS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========== 2. PRODUCTS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    brand TEXT,
                    category TEXT,
                    price REAL NOT NULL DEFAULT 0,
                    cost_price REAL NOT NULL DEFAULT 0,
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    reorder_level INTEGER DEFAULT 10,
                    supplier_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            ''')
            
            # ========== 3. PURCHASES TABLE (Stock IN) ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount REAL NOT NULL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            ''')
            
            # ========== 4. PURCHASE ITEMS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            # ========== 5. SALES TABLE (Stock OUT) ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT UNIQUE NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    customer_name TEXT DEFAULT 'Walk-in Customer',
                    total_amount REAL NOT NULL DEFAULT 0,
                    payment_method TEXT DEFAULT 'Cash',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========== 6. SALE ITEMS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    cost_price REAL NOT NULL,
                    profit REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            # ========== 7. EXPENSES TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'Cash',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========== 8. LEDGER TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_type TEXT NOT NULL,
                    reference_no TEXT,
                    description TEXT,
                    debit REAL DEFAULT 0,
                    credit REAL DEFAULT 0,
                    balance REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========== 9. STOCK TRANSFERS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_no TEXT UNIQUE NOT NULL,
                    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    destination_city TEXT NOT NULL,
                    recipient_name TEXT,
                    transfer_type TEXT,
                    total_amount REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Pending',
                    amount_paid REAL DEFAULT 0,
                    balance_due REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========== 10. TRANSFER ITEMS TABLE ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
                        # ========== 11. RETURNS TABLE (NO UNIQUE CONSTRAINT) ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_no TEXT NOT NULL,
                    return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    return_type TEXT NOT NULL,
                    reference_id INTEGER NOT NULL,
                    reference_no TEXT,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    refund_amount REAL NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'Processed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
                        # ========== CREATE INDEXES FOR PERFORMANCE ==========
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ledger_date ON ledger(transaction_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transfers_date ON stock_transfers(transfer_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_returns_date ON returns(return_date)')
            
            # ========== ADD THESE NEW INDEXES FOR LARGE DATA ==========
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sales_payment ON sales(payment_method)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock_quantity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchase_items_product ON purchase_items(product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger(transaction_type)')
            
            conn.commit()
            conn.close()
            
            self.update_status("✅ Database initialized successfully with all tables")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{str(e)}")
            self.update_status("❌ Database initialization failed")
    def ensure_pack_columns(self):
        """Ensure pack columns exist and set Pack as default"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'unit_type' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN unit_type TEXT DEFAULT 'Pack'")
            if 'pieces_per_pack' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN pieces_per_pack INTEGER DEFAULT 12")
            if 'pack_price' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN pack_price REAL DEFAULT 0")
            
            # Set default for existing products to Pack mode
            cursor.execute("UPDATE products SET unit_type = 'Pack' WHERE unit_type IS NULL OR unit_type = 'Piece'")
            cursor.execute("UPDATE products SET pieces_per_pack = 12 WHERE pieces_per_pack <= 1 AND unit_type = 'Pack'")
            cursor.execute("UPDATE products SET pack_price = price * pieces_per_pack WHERE pack_price <= 0 AND unit_type = 'Pack'")
            
            conn.commit()
            conn.close()
            self.update_status("✅ Pack system ready (Default: Pack)")
        except Exception as e:
            self.update_status(f"⚠️ Pack update: {str(e)}")
    def fix_old_products_to_pack(self):
        """Convert old products to Pack mode (Run once if needed)"""
        try:
            # Convert old products to Pack mode with default values
            self.execute_query("""
                UPDATE products 
                SET unit_type = 'Pack', 
                    pieces_per_pack = 12,
                    pack_price = price * 12
                WHERE unit_type IS NULL OR unit_type = 'Piece'
            """)
            
            count = self.fetch_one("SELECT COUNT(*) FROM products WHERE unit_type = 'Pack'")[0]
            self.update_status(f"✅ {count} products converted to Pack mode")
            
        except Exception as e:
            self.update_status(f"⚠️ Fix error: {str(e)}")
    def update_database_for_pack_system(self):
        """Add pack columns to products table"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'unit_type' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN unit_type TEXT DEFAULT 'Piece'")
                print("✅ Added unit_type column")
            if 'pieces_per_pack' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN pieces_per_pack INTEGER DEFAULT 1")
                print("✅ Added pieces_per_pack column")
            if 'pack_price' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN pack_price REAL DEFAULT 0")
                print("✅ Added pack_price column")
            
            conn.commit()
            conn.close()
            self.update_status("✅ Pack system ready")
        except Exception as e:
            self.update_status(f"⚠️ Pack update: {str(e)}")
    def auto_archive_old_data(self):
        """Automatically archive data older than 6 months"""
        cutoff_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check if archiving needed
            old_sales = cursor.execute("SELECT COUNT(*) FROM sales WHERE sale_date < ?", (cutoff_date,)).fetchone()[0]
            
            if old_sales > 10000:  # If more than 10,000 old records
                # Create archive tables
                cursor.execute("CREATE TABLE IF NOT EXISTS sales_archive AS SELECT * FROM sales WHERE 0")
                cursor.execute("CREATE TABLE IF NOT EXISTS sale_items_archive AS SELECT * FROM sale_items WHERE 0")
                
                # Move old data
                cursor.execute("INSERT INTO sales_archive SELECT * FROM sales WHERE sale_date < ?", (cutoff_date,))
                cursor.execute("INSERT INTO sale_items_archive SELECT si.* FROM sale_items si JOIN sales s ON si.sale_id = s.id WHERE s.sale_date < ?", (cutoff_date,))
                
                # Delete old data
                cursor.execute("DELETE FROM sale_items WHERE sale_id IN (SELECT id FROM sales WHERE sale_date < ?)", (cutoff_date,))
                cursor.execute("DELETE FROM sales WHERE sale_date < ?", (cutoff_date,))
                
                conn.commit()
                self.update_status(f"📦 Archived {old_sales} old sales records")
            
            conn.close()
        except Exception as e:
            self.update_status(f"Archive warning: {str(e)}")
    def auto_fix_old_products_for_sale(self):
        """Automatically fix old products stock quantity on every startup"""
        try:
            # Un sab products ki stock_quantity set karo jo 0 hain
            self.execute_query("""
                UPDATE products 
                SET stock_quantity = reorder_level 
                WHERE (stock_quantity = 0 OR stock_quantity IS NULL) 
                AND reorder_level > 0
            """)
            
            # Agar phir bhi koi 0 hai to default 10 set karo
            self.execute_query("""
                UPDATE products 
                SET stock_quantity = 10 
                WHERE stock_quantity = 0 OR stock_quantity IS NULL
            """)
            
            # Agar unit_type NULL hai to 'Pack' set karo
            self.execute_query("""
                UPDATE products 
                SET unit_type = 'Pack' 
                WHERE unit_type IS NULL
            """)
            
            # Agar pieces_per_pack NULL ya 0 hai to 12 set karo
            self.execute_query("""
                UPDATE products 
                SET pieces_per_pack = 12 
                WHERE pieces_per_pack IS NULL OR pieces_per_pack <= 0
            """)
            
            # Count kitni products fix hui
            fixed_count = self.fetch_one("""
                SELECT COUNT(*) FROM products 
                WHERE stock_quantity > 0 
                AND (stock_quantity = reorder_level OR stock_quantity = 10)
            """)[0]
            
            if fixed_count > 0:
                self.update_status(f"✅ Auto-fixed {fixed_count} old products for sale")
            
        except Exception as e:
            self.update_status(f"⚠️ Auto fix warning: {str(e)}")
    def get_db_connection(self):
        """Get database connection with large data optimization"""
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size = 20000")      # 20MB cache
        conn.execute("PRAGMA temp_store = MEMORY")     # Speed up temp operations
        conn.execute("PRAGMA mmap_size = 268435456")   # 256MB memory mapping
        conn.execute("PRAGMA page_size = 4096")        # Optimal page size
        return conn
    
    def execute_query(self, query, params=()):
        """Execute a query and return cursor"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return cursor
    
    def fetch_all(self, query, params=()):
        """Fetch all results from query"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def fetch_one(self, query, params=()):
        """Fetch single result from query"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result
    
    def create_sidebar(self):
        """Create sidebar with navigation buttons and toggle feature"""
        self.sidebar_frame = tk.Frame(self.root, bg="#1a1a2e", width=self.sidebar_width)
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False)
        
        self.sidebar_widgets = []
        
        header_frame = tk.Frame(self.sidebar_frame, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x", pady=(10, 0))
        header_frame.pack_propagate(False)
        
        self.shop_logo = tk.Label(
            header_frame,
            text="FPM",
            font=("Helvetica", 18, "bold"),
            bg="#1a1a2e",
            fg="#e94560",
            justify="center"
        )
        self.shop_logo.pack(side="left", padx=(15, 0))
        
        self.toggle_btn = tk.Button(
            header_frame,
            text="◀",
            command=self.toggle_sidebar,
            bg="#e94560",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            width=3,
            height=1
        )
        self.toggle_btn.pack(side="right", padx=(0, 15))
        
        separator = tk.Frame(self.sidebar_frame, bg="#e94560", height=2)
        separator.pack(fill="x", pady=(10, 10))
        
        self.nav_buttons = {}
        self.nav_labels = {}
        
        nav_items = [
            ("Dashboard", "📊", self.show_dashboard),
            ("Inventory", "📦", self.show_inventory),
            ("Purchases", "🛒", self.show_purchases),
            ("Sales", "💰", self.show_sales),
            ("Suppliers", "🏢", self.show_suppliers),
            ("Expenses", "💸", self.show_expenses),
            ("Ledger", "📒", self.show_ledger),
            ("Reports", "📈", self.show_reports),
            ("Backup", "💾", self.show_backup_restore)
        ]
        
        buttons_frame = tk.Frame(self.sidebar_frame, bg="#1a1a2e")
        buttons_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        for text, icon, command in nav_items:
            btn_frame = tk.Frame(buttons_frame, bg="#1a1a2e")
            btn_frame.pack(fill="x", pady=(0, 5), padx=(10, 15))
            
            label = tk.Label(
                btn_frame,
                text=text,
                bg="#1a1a2e",
                fg="white",
                font=("Arial", 11),
                anchor="w",
                cursor="hand2"
            )
            label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            btn = tk.Button(
                btn_frame,
                text=icon,
                command=lambda cmd=command, txt=text: self.navigate(cmd, txt),
                bg="#16213e",
                fg="#ffffff",
                font=("Arial", 14),
                pady=8,
                relief="flat",
                activebackground="#0f3460",
                activeforeground="#e94560",
                cursor="hand2",
                width=4
            )
            btn.pack(side="right", padx=(0, 0))
            
            self.nav_buttons[text] = btn
            self.nav_labels[text] = label
            
            label.bind("<Button-1>", lambda e, cmd=command, txt=text: self.navigate(cmd, txt))
            label.bind("<Enter>", lambda e, lbl=label: lbl.configure(fg="#e94560"))
            label.bind("<Leave>", lambda e, lbl=label: lbl.configure(fg="white"))
            
            self.sidebar_widgets.append(btn_frame)
        
        bottom_frame = tk.Frame(self.sidebar_frame, bg="#1a1a2e")
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 20))
        
        separator2 = tk.Frame(bottom_frame, bg="#e94560", height=1)
        separator2.pack(fill="x", pady=(10, 10))
        
        self.version_label = tk.Label(
            bottom_frame,
            text="Version 1.0",
            font=("Arial", 8),
            bg="#1a1a2e",
            fg="#666"
        )
        self.version_label.pack()
    
    def toggle_sidebar(self):
        """Toggle sidebar collapse/expand"""
        if self.sidebar_collapsed:
            self.sidebar_width = 250
            self.sidebar_frame.config(width=self.sidebar_width)
            self.toggle_btn.config(text="◀")
            
            for label in self.nav_labels.values():
                label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            self.shop_logo.config(text="FPM", font=("Helvetica", 18, "bold"))
            self.sidebar_collapsed = False
        else:
            self.sidebar_width = self.collapsed_width
            self.sidebar_frame.config(width=self.sidebar_width)
            self.toggle_btn.config(text="▶")
            
            for label in self.nav_labels.values():
                label.pack_forget()
            
            self.shop_logo.config(text="F", font=("Helvetica", 20, "bold"))
            self.sidebar_collapsed = True
        
        self.update_status(f"📁 Sidebar {'collapsed' if self.sidebar_collapsed else 'expanded'}")
    
    def navigate(self, command, menu_text):
        """Navigate to different sections with active menu highlighting"""
        for btn in self.nav_buttons.values():
            btn.configure(bg="#16213e", fg="#ffffff")
        
        for label in self.nav_labels.values():
            label.configure(fg="white")
        
        self.nav_buttons[menu_text].configure(bg="#e94560", fg="#ffffff")
        if menu_text in self.nav_labels:
            self.nav_labels[menu_text].configure(fg="#e94560")
        
        command()
    
    def create_main_content(self):
        """Create main content area"""
        self.main_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
    
    def create_status_bar(self):
        """Create professional status bar at bottom"""
        self.status_bar = tk.Frame(self.root, bg="#2c3e50", height=35)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        shop_info = tk.Label(
            self.status_bar,
            text="🏪 Faizan Paper Mart | Professional POS System | v1.0",
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        shop_info.pack(side="left", padx=10)
        
        self.status_label = tk.Label(
            self.status_bar,
            text="✓ System Ready",
            font=("Arial", 9, "italic"),
            bg="#2c3e50",
            fg="#2ecc71"
        )
        self.status_label.pack(side="left", padx=(20, 0))
        
        self.time_label = tk.Label(
            self.status_bar,
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        self.time_label.pack(side="right", padx=10)
        
        self.update_time()
    
    def update_time(self):
        """Update time in status bar"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d | %I:%M:%S %p")
            self.time_label.config(text=f"🕐 {current_time}")
            self.root.after(1000, self.update_time)
        except:
            pass
    
    def update_status(self, message):
        """Update status bar message"""
        try:
            self.status_label.config(text=f"✓ {message}")
            self.root.after(3000, lambda: self.status_label.config(text="✓ System Ready"))
        except:
            pass
    
    def clear_main_content(self):
        """Clear all widgets from main content area"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def create_professional_card(self, parent, title, value, icon, color):
        """Create a professional stats card"""
        card = tk.Frame(parent, bg="white", relief="ridge", bd=1)
        card.configure(highlightbackground="#ddd", highlightthickness=1)
        
        icon_label = tk.Label(card, text=icon, font=("Arial", 32), bg="white", fg=color)
        icon_label.pack(pady=(10, 0))
        
        value_label = tk.Label(card, text=value, font=("Arial", 24, "bold"), bg="white", fg=color)
        value_label.pack()
        
        title_label = tk.Label(card, text=title, font=("Arial", 10), bg="white", fg="#666")
        title_label.pack(pady=(0, 10))
        
        return card
    def animate_welcome_text(self, label, full_text, index=0):
        """Animate welcome text like typing"""
        try:
            if index <= len(full_text):
                label.config(text=full_text[:index])
                self.root.after(60, lambda: self.animate_welcome_text(label, full_text, index + 1))
        except:
            pass  # Ignore error if label is destroyed
    
    def show_dashboard(self):
        """Show professional dashboard view with real data"""
                # Force a quick connection check
        self.current_menu = "Dashboard"
        try:
            self.fetch_one("SELECT 1")
        except:
            pass
        self.clear_main_content()
        
        
        try:
            # Initialize variables to avoid UnboundLocalError
            today_profit = 0
            today_expenses = 0
            today_sales = 0
            db_total_products = 0
            low_stock = 0
            total_suppliers = 0
                        # DEBUG: Check products count
            debug_count = self.fetch_one("SELECT COUNT(*) FROM products")
            print(f"DEBUG: Total products in database: {debug_count[0] if debug_count else 0}")
            
            # Get real-time stats from database
                        # Get real-time stats from database
            db_total_products = self.fetch_one("SELECT COUNT(*) FROM products")
            db_total_products = db_total_products[0] if db_total_products else 0

            
                        # Today's sales (SALES + CITY TRANSFERS + SHOP TRANSFERS with Paid status)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Sales from ledger
            sales_from_ledger = self.fetch_one("""
                SELECT COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0) 
                FROM ledger 
                WHERE transaction_type IN ('SALE', 'SALE_RETURN') 
                AND DATE(transaction_date) = ?
            """, (today,))[0] or 0
            
            # City Transfers (Paid)
            city_transfer_total = self.fetch_one("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM stock_transfers 
                WHERE DATE(transfer_date) = ? AND payment_status = 'Paid'
            """, (today,))[0] or 0
            
            # Shop Transfers (Paid)
            shop_transfer_total = self.fetch_one("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM shop_transfers 
                WHERE DATE(transfer_date) = ? AND payment_status = 'Paid'
            """, (today,))[0] or 0
            
            today_sales = sales_from_ledger + city_transfer_total + shop_transfer_total
            
            # Low stock products
            low_stock = self.fetch_one("SELECT COUNT(*) FROM products WHERE stock_quantity <= reorder_level")
            low_stock = low_stock[0] if low_stock else 0
            
                                                # ===== TODAY'S DATA (Consistent) =====
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Today's Sales Profit (from sale_items)
            today_sales_profit = self.fetch_one("""
                SELECT COALESCE(SUM(si.profit), 0)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.sale_date) = ?
            """, (today,))[0] or 0
            
            # Today's Sales Returns (refund given to customers today)
            today_sales_returns = self.fetch_one("""
                SELECT COALESCE(SUM(refund_amount), 0) 
                FROM returns 
                WHERE return_type = 'SALE' AND DATE(return_date) = ?
            """, (today,))[0] or 0
            
            # Today's City Transfer Profit
            today_transfer_profit = self.fetch_one("""
                SELECT COALESCE(SUM(ti.total - (ti.quantity * p.cost_price)), 0)
                FROM transfer_items ti
                JOIN products p ON ti.product_id = p.id
                JOIN stock_transfers st ON ti.transfer_id = st.id
                WHERE DATE(st.transfer_date) = ? AND st.payment_status = 'Paid'
            """, (today,))[0] or 0
            
            # Today's Shop Transfer Profit
            today_shop_profit = self.fetch_one("""
                SELECT COALESCE(SUM(sti.total - (sti.quantity * p.cost_price)), 0)
                FROM shop_transfer_items sti
                JOIN products p ON sti.product_id = p.id
                JOIN shop_transfers st ON sti.transfer_id = st.id
                WHERE DATE(st.transfer_date) = ? AND st.payment_status = 'Paid'
            """, (today,))[0] or 0
            
            # Today's Shop Returns
            today_shop_returns = self.fetch_one("""
                SELECT COALESCE(SUM(refund_amount), 0) 
                FROM returns 
                WHERE return_type = 'SHOP_RETURN' AND DATE(return_date) = ?
            """, (today,))[0] or 0
            
            # Today's Expenses
            today_expenses = self.fetch_one("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM expenses 
                WHERE DATE(expense_date) = ?
            """, (today,))[0] or 0
            
            # TODAY'S TOTAL PROFIT
            today_profit = (today_sales_profit - today_sales_returns) + today_transfer_profit + today_shop_profit - today_shop_returns
            
            # Total suppliers
            total_suppliers = self.fetch_one("SELECT COUNT(*) FROM suppliers")
            total_suppliers = total_suppliers[0] if total_suppliers else 0
            
        except Exception as e:
            db_total_products = 0
            today_sales = 0
            low_stock = 0
            today_profit = 0
            today_expenses = 0
            total_suppliers = 0
            self.update_status(f"⚠️ Error loading stats: {str(e)}")
        
                        # Welcome Banner - Simple with Typing Effect
        banner_frame = tk.Frame(self.main_frame, bg="#f0f4f8", height=120)
        banner_frame.pack(fill="x", pady=(0, 20))
        banner_frame.pack_propagate(False)
        
        # Frame for text
        text_container = tk.Frame(banner_frame, bg="#f0f4f8")
        text_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Label for animated text (initially empty)
        welcome_label = tk.Label(
            text_container,
            text="",
            font=("Helvetica", 22, "bold"),
            bg="#f0f4f8",
            fg="#2c3e50",
            justify="center"
        )
        welcome_label.pack(pady=(0, 5))
        
        # Subtitle (static, no animation)
        subtitle = tk.Label(
            text_container,
            text="Your Complete Stationery Management Solution",
            font=("Helvetica", 11),
            bg="#f0f4f8",
            fg="#7f8c8d"
        )
        subtitle.pack()
        
        # Start typing animation after a short delay
        full_welcome_text = "✨ Welcome to Faizan Paper Mart ✨"
        self.root.after(100, lambda: self.animate_welcome_text(welcome_label, full_welcome_text))
        
        # Stats cards frame
        stats_frame = tk.Frame(self.main_frame, bg="#f5f5f5")
        stats_frame.pack(pady=20, fill="x")
       
                    # Professional stats cards with real data (including shop transfers)
        stats_data = [
                ("Total Products", str(db_total_products), "📦", "#e94560"),
                ("Today's Sales", f"Rs. {today_sales:,.0f}", "💰", "#4e73df"),
                ("Low Stock Alert", str(low_stock), "⚠️", "#f6c23e"),
                ("Today's Profit", f"Rs. {today_profit:,.0f}", "💎", "#1cc88a"),
                ("Today's Expenses", f"Rs. {today_expenses:,.0f}", "💸", "#f6c23e"),
                ("Suppliers", str(total_suppliers), "🏢", "#36b9cc")
            ]
        
        for i, (title, value, icon, color) in enumerate(stats_data):
            card = self.create_professional_card(stats_frame, title, value, icon, color)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
        
                                        # Quick Actions
        quick_frame = tk.LabelFrame(
            self.main_frame, 
            text="⚡ Quick Actions", 
            bg="#f5f5f5", 
            font=("Helvetica", 12, "bold"),
            fg="#1a1a2e",
            padx=10,
            pady=10
        )
        quick_frame.pack(pady=30, padx=20, fill="x")
        
        # Row 1 - 5 buttons
        actions_row1 = [
            ("🛒 New Sale", self.show_sales, "#e94560"),
            ("📦 New Purchase", self.show_purchases, "#4e73df"),
            ("➕ Add Product", self.show_inventory, "#1cc88a"),
            ("💸 Add Expense", self.show_expenses, "#f6c23e"),
            ("🚚 Transfer Stock", self.show_stock_transfer, "#36b9cc")
        ]
        
        for i, (text, cmd, color) in enumerate(actions_row1):
            btn = tk.Button(
                quick_frame,
                text=text,
                command=cmd,
                bg=color,
                fg="white",
                font=("Arial", 10, "bold"),
                padx=25,
                pady=8,
                relief="flat",
                cursor="hand2"
            )
            btn.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            quick_frame.grid_columnconfigure(i, weight=1)
        
        # Row 2 - 5 buttons
        # Button 1: Shop Transfer
        shop_transfer_btn = tk.Button(
            quick_frame,
            text="🏪 Shop Transfer",
            command=self.show_shop_transfer,
            bg="#1cc88a",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        shop_transfer_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Button 2: Returns Management
        returns_btn = tk.Button(
            quick_frame,
            text="🔄 Returns Management",
            command=self.show_returns,
            bg="#e94560",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        returns_btn.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Button 3: Insight Center (NEW)
        insight_btn = tk.Button(
            quick_frame,
            text="📊 Insight Center",
            command=self.show_insight_center,
            bg="#8b5cf6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        insight_btn.grid(row=1, column=2, padx=10, pady=10, sticky="ew")
        
        # Button 4: Saved Invoices
        saved_btn = tk.Button(
            quick_frame,
            text="📁 Saved Invoices",
            command=self.show_saved_invoices,
            bg="#36b9cc",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        saved_btn.grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        
        # Button 5: Return Slips
        return_slips_btn = tk.Button(
            quick_frame,
            text="📋 Return Slips",
            command=self.show_saved_return_slips,
            bg="#f6c23e",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        return_slips_btn.grid(row=1, column=4, padx=10, pady=10, sticky="ew")
                        # ========== RETURNS SUMMARY SECTION (WITH ERROR HANDLING) ==========
        returns_frame = tk.LabelFrame(self.main_frame, text="🔄 Recent Returns", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
        returns_frame.pack(fill="x", pady=10, padx=20)
        
        # Get recent returns - with safe error handling
        try:
            # Try to get returns from database
            recent_returns = self.fetch_all("""
                SELECT return_no, return_date, return_type, quantity, refund_amount
                FROM returns
                ORDER BY return_date DESC
                LIMIT 5
            """)
            
            if recent_returns:
                for ret in recent_returns:
                    ret_frame = tk.Frame(returns_frame, bg="#f5f5f5")
                    ret_frame.pack(fill="x", padx=10, pady=5)
                    tk.Label(ret_frame, text=f"📅 {ret[1][:10] if ret[1] else '-'} | {ret[2]} | Qty: {ret[3]} | Refund: Rs.{ret[4]:,.0f}", 
                            font=("Arial", 9), bg="#f5f5f5", fg="#666").pack(anchor="w")
            else:
                tk.Label(returns_frame, text="No returns recorded yet", font=("Arial", 10), bg="#f5f5f5", fg="#888").pack(pady=10)
        except:
            # If table doesn't exist yet, show this message
            tk.Label(returns_frame, text="No returns recorded yet", font=("Arial", 10), bg="#f5f5f5", fg="#888").pack(pady=10)
        # ========== END RETURNS SUMMARY ==========
        # Database info
        info_frame = tk.Frame(self.main_frame, bg="#f5f5f5")
        info_frame.pack(pady=20, fill="x")
        
        # Get database size
        try:
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            db_size_kb = db_size / 1024
        except:
            db_size_kb = 0
        
        info_text = tk.Label(
            info_frame,
            text=f"💡 Database Status: Connected | Size: {db_size_kb:.1f} KB | {db_total_products} Products Loaded | {total_suppliers} Suppliers",
            font=("Arial", 9, "italic"),
            bg="#f5f5f5",
            fg="#888"
        )
        info_text.pack()
        
        self.update_status(f"📊 Dashboard loaded with {db_total_products} products")
    
    # ========== PHASE 3: SUPPLIER MODULE ==========
    
    def show_suppliers(self):
        """Show supplier management interface"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        title = tk.Label(
            header_frame,
            text="🏢 Supplier Management",
            font=("Helvetica", 24, "bold"),
            bg="#f5f5f5",
            fg="#1a1a2e"
        )
        title.pack(side="left")
        
        btn_frame = tk.Frame(header_frame, bg="#f5f5f5")
        btn_frame.pack(side="right")
        
        add_btn = tk.Button(
            btn_frame,
            text="➕ Add New Supplier",
            command=self.open_add_supplier_dialog,
            bg="#e94560",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        add_btn.pack(side="left", padx=5)
        
        export_btn = tk.Button(
            btn_frame,
            text="📥 Export CSV",
            command=self.export_suppliers_to_csv,
            bg="#36b9cc",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        export_btn.pack(side="left", padx=5)
        
        search_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.supplier_search_var = tk.StringVar()
        self.supplier_search_var.trace('w', lambda *args: self.search_suppliers())
        search_entry = tk.Entry(search_frame, textvariable=self.supplier_search_var, font=("Arial", 11), width=40)
        search_entry.pack(side="left", padx=10, pady=8)
        
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True)
        
        suppliers_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(suppliers_tab, text="📋 Suppliers List")
        
        stats_info_frame = tk.Frame(suppliers_tab, bg="#f5f5f5")
        stats_info_frame.pack(fill="x", pady=(0, 10))
        
        self.supplier_stats_label = tk.Label(
            stats_info_frame,
            text="",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="#666"
        )
        self.supplier_stats_label.pack(side="left")
        
        tree_frame = tk.Frame(suppliers_tab, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Name", "Contact Person", "Phone", "Email", "Address", "Products", "Purchases", "Total Spent", "Created")
        
        self.supplier_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.supplier_tree.heading("ID", text="ID")
        self.supplier_tree.heading("Name", text="Supplier Name")
        self.supplier_tree.heading("Contact Person", text="Contact Person")
        self.supplier_tree.heading("Phone", text="Phone")
        self.supplier_tree.heading("Email", text="Email")
        self.supplier_tree.heading("Address", text="Address")
        self.supplier_tree.heading("Products", text="Products")
        self.supplier_tree.heading("Purchases", text="Purchases")
        self.supplier_tree.heading("Total Spent", text="Total Spent (Rs.)")
        self.supplier_tree.heading("Created", text="Created Date")
        
        self.supplier_tree.column("ID", width=50)
        self.supplier_tree.column("Name", width=150)
        self.supplier_tree.column("Contact Person", width=120)
        self.supplier_tree.column("Phone", width=100)
        self.supplier_tree.column("Email", width=150)
        self.supplier_tree.column("Address", width=150)
        self.supplier_tree.column("Products", width=80)
        self.supplier_tree.column("Purchases", width=80)
        self.supplier_tree.column("Total Spent", width=120)
        self.supplier_tree.column("Created", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.supplier_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.supplier_tree.xview)
        self.supplier_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.supplier_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.supplier_context_menu = tk.Menu(self.root, tearoff=0)
        self.supplier_context_menu.add_command(label="✏️ Edit", command=self.edit_selected_supplier)
        self.supplier_context_menu.add_command(label="🗑️ Delete", command=self.delete_selected_supplier)
        self.supplier_context_menu.add_separator()
        self.supplier_context_menu.add_command(label="📦 View Products", command=self.view_supplier_products)
        self.supplier_context_menu.add_command(label="📜 View Purchase History", command=self.view_supplier_purchase_history)
        
        self.supplier_tree.bind("<Button-3>", self.show_supplier_context_menu)
        self.supplier_tree.bind("<Double-1>", lambda e: self.edit_selected_supplier())
        
        self.history_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(self.history_tab, text="📜 Purchase History")
        
        history_select_frame = tk.Frame(self.history_tab, bg="white", relief="ridge", bd=1)
        history_select_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(history_select_frame, text="Select Supplier:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=10)
        self.history_supplier_var = tk.StringVar()
        self.history_supplier_combo = ttk.Combobox(history_select_frame, textvariable=self.history_supplier_var, font=("Arial", 11), width=40, state="readonly")
        self.history_supplier_combo.pack(side="left", padx=10, pady=10)
        self.history_supplier_combo.bind('<<ComboboxSelected>>', lambda e: self.load_purchase_history())
        
        history_tree_frame = tk.Frame(self.history_tab, bg="#f5f5f5")
        history_tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        history_columns = ("Invoice No", "Date", "Total Amount", "Notes", "Items")
        self.history_tree = ttk.Treeview(history_tree_frame, columns=history_columns, show="headings", height=15)
        
        self.history_tree.heading("Invoice No", text="Invoice No")
        self.history_tree.heading("Date", text="Purchase Date")
        self.history_tree.heading("Total Amount", text="Total Amount (Rs.)")
        self.history_tree.heading("Notes", text="Notes")
        self.history_tree.heading("Items", text="Items Count")
        
        self.history_tree.column("Invoice No", width=150)
        self.history_tree.column("Date", width=150)
        self.history_tree.column("Total Amount", width=150)
        self.history_tree.column("Notes", width=200)
        self.history_tree.column("Items", width=100)
        
        history_vsb = ttk.Scrollbar(history_tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_vsb.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_vsb.pack(side="right", fill="y")
        
        self.history_tree.bind("<Double-1>", lambda e: self.view_purchase_details())
        
        self.load_suppliers_for_history()
        self.load_suppliers()
    
    def load_suppliers_for_history(self):
        """Load suppliers into history combo box"""
        try:
            suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
            supplier_list = [f"{s[0]} - {s[1]}" for s in suppliers]
            self.history_supplier_combo['values'] = supplier_list
        except Exception as e:
            self.update_status(f"Error loading suppliers: {str(e)}")
    
    def load_purchase_history(self):
        """Load purchase history for selected supplier"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        selection = self.history_supplier_var.get()
        if not selection:
            return
        
        try:
            supplier_id = int(selection.split(" - ")[0])
            query = """
                SELECT p.invoice_no, p.purchase_date, p.total_amount, p.notes,
                       COUNT(pi.id) as items_count
                FROM purchases p
                LEFT JOIN purchase_items pi ON p.id = pi.purchase_id
                WHERE p.supplier_id = ?
                GROUP BY p.id
                ORDER BY p.purchase_date DESC
            """
            purchases = self.fetch_all(query, (supplier_id,))
            
            for purchase in purchases:
                self.history_tree.insert("", "end", values=(
                    purchase[0],
                    purchase[1][:19] if purchase[1] else "-",
                    f"Rs. {purchase[2]:,.2f}",
                    purchase[3] or "-",
                    purchase[4]
                ))
            
            if purchases:
                total_amount = sum(p[2] for p in purchases)
                self.update_status(f"Loaded {len(purchases)} purchase records, Total: Rs. {total_amount:,.2f}")
            else:
                self.update_status("No purchase history found for this supplier")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load purchase history: {str(e)}")
    
    def view_purchase_details(self):
        """View details of selected purchase"""
        selected = self.history_tree.selection()
        if not selected:
            return
        
        item = self.history_tree.item(selected[0])
        invoice_no = item['values'][0]
        
        purchase = self.fetch_one("SELECT * FROM purchases WHERE invoice_no = ?", (invoice_no,))
        if not purchase:
            return
        
        items = self.fetch_all("""
            SELECT pi.*, p.name 
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase[0],))
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Purchase Details - {invoice_no}")
        dialog.geometry("700x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Purchase Invoice: {invoice_no}", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        info_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = f"""
        Date: {purchase[3][:19] if purchase[3] else '-'}
        Total Amount: Rs. {purchase[4]:,.2f}
        Notes: {purchase[5] or '-'}
        """
        tk.Label(info_frame, text=info_text, font=("Arial", 11), bg="white", justify="left").pack(padx=20, pady=10)
        
        items_frame = tk.Frame(dialog, bg="#f5f5f5")
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(items_frame, text="Purchase Items:", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(anchor="w")
        
        tree_frame = tk.Frame(items_frame, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("Product", "Quantity", "Price", "Total")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        tree.heading("Product", text="Product Name")
        tree.heading("Quantity", text="Quantity")
        tree.heading("Price", text="Price (Rs.)")
        tree.heading("Total", text="Total (Rs.)")
        
        tree.column("Product", width=300)
        tree.column("Quantity", width=100)
        tree.column("Price", width=100)
        tree.column("Total", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for item in items:
            tree.insert("", "end", values=(
                item[5],
                item[2],
                f"Rs. {item[3]:,.2f}",
                f"Rs. {item[4]:,.2f}"
            ))
        
        tk.Button(dialog, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(pady=10)
    
    def load_suppliers(self, search_term=""):
        """Load suppliers into treeview with purchase statistics"""
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)
        
        try:
            if search_term:
                query = """
                    SELECT s.*, 
                           COUNT(DISTINCT p.id) as product_count,
                           COUNT(DISTINCT pu.id) as purchase_count,
                           COALESCE(SUM(pu.total_amount), 0) as total_spent
                    FROM suppliers s
                    LEFT JOIN products p ON s.id = p.supplier_id
                    LEFT JOIN purchases pu ON s.id = pu.supplier_id
                    WHERE s.name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ?
                    GROUP BY s.id
                    ORDER BY s.id DESC
                """
                params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
            else:
                query = """
                    SELECT s.*, 
                           COUNT(DISTINCT p.id) as product_count,
                           COUNT(DISTINCT pu.id) as purchase_count,
                           COALESCE(SUM(pu.total_amount), 0) as total_spent
                    FROM suppliers s
                    LEFT JOIN products p ON s.id = p.supplier_id
                    LEFT JOIN purchases pu ON s.id = pu.supplier_id
                    GROUP BY s.id
                    ORDER BY s.id DESC
                """
                params = ()
            
            suppliers = self.fetch_all(query, params)
            
            for supplier in suppliers:
                self.supplier_tree.insert("", "end", values=(
                    supplier[0],
                    supplier[1],
                    supplier[2] or "-",
                    supplier[3] or "-",
                    supplier[4] or "-",
                    supplier[5] or "-",
                    supplier[7],
                    supplier[8],
                    f"Rs. {supplier[9]:,.2f}",
                    supplier[6][:10] if supplier[6] else "-"
                ))
            
            total_suppliers = len(suppliers)
            total_products = sum(s[7] for s in suppliers)
            total_purchases = sum(s[8] for s in suppliers)
            total_spent = sum(s[9] for s in suppliers)
            
            self.supplier_stats_label.config(
                text=f"📊 Total Suppliers: {total_suppliers} | Total Products: {total_products} | "
                     f"Total Purchases: {total_purchases} | Total Spent: Rs. {total_spent:,.2f}"
            )
            
            self.update_status(f"Loaded {total_suppliers} suppliers")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load suppliers: {str(e)}")
    
    def search_suppliers(self):
        """Search suppliers based on search term"""
        search_term = self.supplier_search_var.get()
        self.load_suppliers(search_term)
    
    def open_add_supplier_dialog(self):
        """Open dialog to add new supplier"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Supplier")
        dialog.geometry("500x550")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="➕ Add New Supplier", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        form_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = {}
        labels = [
            ("Supplier Name *", "name"),
            ("Contact Person", "contact_person"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Address", "address")
        ]
        
        row = 0
        for label_text, field_key in labels:
            tk.Label(form_frame, text=label_text, font=("Arial", 11), bg="white", fg="#333").grid(row=row, column=0, sticky="w", padx=20, pady=10)
            
            if field_key == "address":
                entry = tk.Text(form_frame, height=4, width=35, font=("Arial", 11))
                entry.grid(row=row, column=1, padx=20, pady=10)
                fields[field_key] = entry
            else:
                entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
                entry.grid(row=row, column=1, padx=20, pady=10)
                fields[field_key] = entry
            row += 1
        
        button_frame = tk.Frame(dialog, bg="#f5f5f5")
        button_frame.pack(pady=20)
        
        def save_supplier():
            name = fields["name"].get().strip()
            contact_person = fields["contact_person"].get().strip()
            phone = fields["phone"].get().strip()
            email = fields["email"].get().strip()
            address = fields["address"].get("1.0", "end-1c").strip()
            
            if not name:
                messagebox.showwarning("Validation Error", "Supplier Name is required!")
                return
            
            try:
                self.execute_query(
                    "INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES (?, ?, ?, ?, ?)",
                    (name, contact_person, phone, email, address)
                )
                messagebox.showinfo("Success", "Supplier added successfully!")
                dialog.destroy()
                self.load_suppliers()
                self.load_suppliers_for_history()
                self.update_status(f"✅ Added supplier: {name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add supplier: {str(e)}")
        
        tk.Button(button_frame, text="💾 Save Supplier", command=save_supplier, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(button_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def show_supplier_context_menu(self, event):
        """Show right-click context menu for supplier tree"""
        item = self.supplier_tree.identify_row(event.y)
        if item:
            self.supplier_tree.selection_set(item)
            self.supplier_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_supplier_id(self):
        """Get selected supplier ID from treeview"""
        selected = self.supplier_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a supplier first!")
            return None
        item = self.supplier_tree.item(selected[0])
        return item['values'][0]
    
    def edit_selected_supplier(self):
        """Edit selected supplier"""
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            return
        
        supplier = self.fetch_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        if not supplier:
            messagebox.showerror("Error", "Supplier not found!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Supplier")
        dialog.geometry("500x550")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="✏️ Edit Supplier", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        form_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = {}
        labels = [
            ("Supplier Name *", "name"),
            ("Contact Person", "contact_person"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Address", "address")
        ]
        
        row = 0
        for label_text, field_key in labels:
            tk.Label(form_frame, text=label_text, font=("Arial", 11), bg="white", fg="#333").grid(row=row, column=0, sticky="w", padx=20, pady=10)
            
            if field_key == "address":
                entry = tk.Text(form_frame, height=4, width=35, font=("Arial", 11))
                entry.insert("1.0", supplier[5] or "")
                entry.grid(row=row, column=1, padx=20, pady=10)
                fields[field_key] = entry
            else:
                entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
                if field_key == "name":
                    entry.insert(0, supplier[1])
                elif field_key == "contact_person":
                    entry.insert(0, supplier[2] or "")
                elif field_key == "phone":
                    entry.insert(0, supplier[3] or "")
                elif field_key == "email":
                    entry.insert(0, supplier[4] or "")
                entry.grid(row=row, column=1, padx=20, pady=10)
                fields[field_key] = entry
            row += 1
        
        button_frame = tk.Frame(dialog, bg="#f5f5f5")
        button_frame.pack(pady=20)
        
        def update_supplier():
            name = fields["name"].get().strip()
            contact_person = fields["contact_person"].get().strip()
            phone = fields["phone"].get().strip()
            email = fields["email"].get().strip()
            address = fields["address"].get("1.0", "end-1c").strip()
            
            if not name:
                messagebox.showwarning("Validation Error", "Supplier Name is required!")
                return
            
            try:
                self.execute_query(
                    "UPDATE suppliers SET name=?, contact_person=?, phone=?, email=?, address=? WHERE id=?",
                    (name, contact_person, phone, email, address, supplier_id)
                )
                messagebox.showinfo("Success", "Supplier updated successfully!")
                dialog.destroy()
                self.load_suppliers()
                self.load_suppliers_for_history()
                self.update_status(f"✅ Updated supplier: {name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update supplier: {str(e)}")
        
        tk.Button(button_frame, text="💾 Update Supplier", command=update_supplier, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(button_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def delete_selected_supplier(self):
        """Delete selected supplier"""
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            return
        
        product_count = self.fetch_one("SELECT COUNT(*) FROM products WHERE supplier_id = ?", (supplier_id,))
        if product_count and product_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This supplier has {product_count[0]} products associated.")
            return
        
        purchase_count = self.fetch_one("SELECT COUNT(*) FROM purchases WHERE supplier_id = ?", (supplier_id,))
        if purchase_count and purchase_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This supplier has {purchase_count[0]} purchase records.")
            return
        
        supplier = self.fetch_one("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
        if not supplier:
            return
        
        confirm = messagebox.askyesno("Confirm Delete", f"Delete supplier '{supplier[0]}'?", icon='warning')
        if confirm:
            try:
                self.execute_query("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                messagebox.showinfo("Success", "Supplier deleted successfully!")
                self.load_suppliers()
                self.load_suppliers_for_history()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete supplier: {str(e)}")
    
    def view_supplier_products(self):
        """View products of selected supplier"""
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            return
        
        supplier = self.fetch_one("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
        if not supplier:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Products from {supplier[0]}")
        dialog.geometry("800x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"📦 Products: {supplier[0]}", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        tree_frame = tk.Frame(dialog, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Product Name", "Brand", "Price", "Stock")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        tree.heading("ID", text="ID")
        tree.heading("Product Name", text="Product Name")
        tree.heading("Brand", text="Brand")
        tree.heading("Price", text="Price (Rs.)")
        tree.heading("Stock", text="Stock")
        
        tree.column("ID", width=50)
        tree.column("Product Name", width=250)
        tree.column("Brand", width=120)
        tree.column("Price", width=100)
        tree.column("Stock", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        products = self.fetch_all("SELECT id, name, brand, price, stock_quantity FROM products WHERE supplier_id = ?", (supplier_id,))
        for product in products:
            tree.insert("", "end", values=(product[0], product[1], product[2] or "-", f"Rs. {product[3]:.0f}", product[4]))
        
        tk.Button(dialog, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(pady=10)
    
    def view_supplier_purchase_history(self):
        """View purchase history of selected supplier"""
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            return
        
        supplier = self.fetch_one("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
        if not supplier:
            return
        
        suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
        for s in suppliers:
            if s[0] == supplier_id:
                self.history_supplier_var.set(f"{s[0]} - {s[1]}")
                break
        
        self.load_purchase_history()
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.Notebook):
                child.select(1)
                break
        
        self.update_status(f"Viewing purchase history for {supplier[0]}")
    
    def export_suppliers_to_csv(self):
        """Export all suppliers to CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Suppliers Export")
            if not file_path:
                return
            
            suppliers = self.fetch_all("""
                SELECT s.*, COUNT(DISTINCT p.id) as product_count, COUNT(DISTINCT pu.id) as purchase_count, COALESCE(SUM(pu.total_amount), 0) as total_spent
                FROM suppliers s
                LEFT JOIN products p ON s.id = p.supplier_id
                LEFT JOIN purchases pu ON s.id = pu.supplier_id
                GROUP BY s.id ORDER BY s.name
            """)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Name', 'Contact Person', 'Phone', 'Email', 'Address', 'Products Count', 'Purchases Count', 'Total Spent (Rs.)', 'Created Date'])
                for supplier in suppliers:
                    writer.writerow([supplier[0], supplier[1], supplier[2] or '', supplier[3] or '', supplier[4] or '', supplier[5] or '', supplier[7], supplier[8], supplier[9], supplier[6]])
            
            messagebox.showinfo("Export Successful", f"Suppliers exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    # ========== PHASE 4: PURCHASE SYSTEM ==========
    
    def show_purchases(self):
        """Show purchase management interface"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True)
        
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_frame = tk.Frame(main_container, bg="#f5f5f5", width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        search_frame = tk.Frame(left_frame, bg="white", relief="ridge", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Search Product:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.purchase_search_var = tk.StringVar()
        self.purchase_search_var.trace('w', lambda *args: self.search_products_for_purchase())
        search_entry = tk.Entry(search_frame, textvariable=self.purchase_search_var, font=("Arial", 11), width=30)
        search_entry.pack(side="left", padx=10, pady=8)
        
        products_frame = tk.LabelFrame(left_frame, text="Available Products", font=("Arial", 12, "bold"), bg="#f5f5f5")
        products_frame.pack(fill="both", expand=True)
        
        product_columns = ("ID", "Name", "Brand", "Current Stock", "Cost Price")
        self.purchase_products_tree = ttk.Treeview(products_frame, columns=product_columns, show="headings", height=12)
        
        self.purchase_products_tree.heading("ID", text="ID")
        self.purchase_products_tree.heading("Name", text="Product Name")
        self.purchase_products_tree.heading("Brand", text="Brand")
        self.purchase_products_tree.heading("Current Stock", text="Current Stock")
        self.purchase_products_tree.heading("Cost Price", text="Cost Price (Rs.)")
        
        self.purchase_products_tree.column("ID", width=50)
        self.purchase_products_tree.column("Name", width=200)
        self.purchase_products_tree.column("Brand", width=100)
        self.purchase_products_tree.column("Current Stock", width=100)
        self.purchase_products_tree.column("Cost Price", width=120)
        
        vsb = ttk.Scrollbar(products_frame, orient="vertical", command=self.purchase_products_tree.yview)
        self.purchase_products_tree.configure(yscrollcommand=vsb.set)
        self.purchase_products_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        cart_frame = tk.LabelFrame(left_frame, text="Purchase Cart", font=("Arial", 12, "bold"), bg="#f5f5f5")
        cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        cart_columns = ("ID", "Product", "Quantity", "Price", "Total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=6)
        
        self.cart_tree.heading("ID", text="ID")
        self.cart_tree.heading("Product", text="Product Name")
        self.cart_tree.heading("Quantity", text="Quantity")
        self.cart_tree.heading("Price", text="Price (Rs.)")
        self.cart_tree.heading("Total", text="Total (Rs.)")
        
        self.cart_tree.column("ID", width=50)
        self.cart_tree.column("Product", width=200)
        self.cart_tree.column("Quantity", width=80)
        self.cart_tree.column("Price", width=100)
        self.cart_tree.column("Total", width=100)
        
        cart_vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        cart_vsb.pack(side="right", fill="y")
        
        cart_btn_frame = tk.Frame(cart_frame, bg="#f5f5f5")
        cart_btn_frame.pack(fill="x", pady=5)
        
        tk.Button(cart_btn_frame, text="🗑️ Remove Selected", command=self.remove_from_purchase_cart, bg="#e74a3b", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        tk.Button(cart_btn_frame, text="🔄 Clear Cart", command=self.clear_purchase_cart, bg="#f6c23e", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        
        form_frame = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(form_frame, text="📝 Purchase Details", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        tk.Label(form_frame, text="Supplier *", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        self.supplier_combo = ttk.Combobox(form_frame, font=("Arial", 11), width=30, state="readonly")
        self.supplier_combo.pack(padx=20, pady=5)
        self.load_suppliers_for_purchase()
        
        tk.Label(form_frame, text="Invoice Number", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        self.invoice_no_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.invoice_no_entry.pack(padx=20, pady=5)
        self.generate_invoice_number()
        
        tk.Label(form_frame, text="Notes", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        self.notes_text = tk.Text(form_frame, height=4, width=30, font=("Arial", 11))
        self.notes_text.pack(padx=20, pady=5)
        
        total_frame = tk.Frame(form_frame, bg="white")
        total_frame.pack(fill="x", pady=20)
        
        tk.Label(total_frame, text="Total Amount:", font=("Arial", 14, "bold"), bg="white", fg="#e94560").pack(side="left", padx=20)
        self.total_amount_label = tk.Label(total_frame, text="Rs. 0.00", font=("Arial", 16, "bold"), bg="white", fg="#e94560")
        self.total_amount_label.pack(side="right", padx=20)
        
        action_frame = tk.Frame(form_frame, bg="white")
        action_frame.pack(fill="x", pady=10)
        
        tk.Button(action_frame, text="➕ Add to Cart", command=self.open_quantity_dialog, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=10)
        tk.Button(action_frame, text="✅ Complete Purchase", command=self.complete_purchase, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="right", expand=True, padx=10)
        
        tk.Button(form_frame, text="🆕 Add New Product", command=self.open_add_product_dialog_for_purchase, bg="#e94560", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(pady=5)
        
        self.purchase_products_tree.bind("<Double-1>", lambda e: self.open_quantity_dialog())
        self.load_products_for_purchase()
    
    def load_suppliers_for_purchase(self):
        """Load suppliers into combo box for purchase"""
        try:
            suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
            supplier_list = [f"{s[0]} - {s[1]}" for s in suppliers]
            self.supplier_combo['values'] = supplier_list
            if supplier_list:
                self.supplier_combo.current(0)
        except Exception as e:
            self.update_status(f"Error loading suppliers: {str(e)}")
    
    def generate_invoice_number(self):
        """Generate unique invoice number for purchase"""
        try:
            last_invoice = self.fetch_one("SELECT invoice_no FROM purchases ORDER BY id DESC LIMIT 1")
            if last_invoice and last_invoice[0]:
                num = int(last_invoice[0].split('-')[-1]) + 1
                new_invoice = f"PO-{datetime.now().year}-{num:03d}"
            else:
                new_invoice = f"PO-{datetime.now().year}-001"
            self.invoice_no_entry.delete(0, tk.END)
            self.invoice_no_entry.insert(0, new_invoice)
        except:
            self.invoice_no_entry.delete(0, tk.END)
            self.invoice_no_entry.insert(0, f"PO-{datetime.now().year}-001")
    
    def load_products_for_purchase(self, search_term=""):
        """Load products for purchase selection"""
        for item in self.purchase_products_tree.get_children():
            self.purchase_products_tree.delete(item)
        
        try:
            if search_term:
                query = "SELECT id, name, brand, stock_quantity, cost_price FROM products WHERE name LIKE ? OR brand LIKE ? ORDER BY id DESC"
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = "SELECT id, name, brand, stock_quantity, cost_price FROM products ORDER BY id DESC"
                params = ()
            
            products = self.fetch_all(query, params)
            for product in products:
                self.purchase_products_tree.insert("", "end", values=(product[0], product[1], product[2] or "-", product[3], f"Rs. {product[4]:.2f}"))
            self.update_status(f"Loaded {len(products)} products")
        except Exception as e:
            self.update_status(f"Error loading products: {str(e)}")
    
    def search_products_for_purchase(self):
        """Search products for purchase"""
        search_term = self.purchase_search_var.get()
        self.load_products_for_purchase(search_term)
    
    def open_quantity_dialog(self):
        """Open dialog to enter quantity for adding to cart with Pack/Piece options"""
        selected = self.purchase_products_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return
        
        item = self.purchase_products_tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        current_stock = item['values'][3]
        cost_price = float(item['values'][4].replace('Rs. ', ''))
        
        # Get product pack info
        product_info = self.fetch_one("SELECT unit_type, pieces_per_pack, pack_price FROM products WHERE id = ?", (product_id,))
        unit_type = product_info[0] if product_info else "Piece"
        pieces_per_pack = product_info[1] if product_info else 1
        pack_price = product_info[2] if product_info else 0
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add to Purchase Cart - {product_name}")
        dialog.geometry("550x550")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product_name}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with scrollbar
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stock info
        info_frame = tk.Frame(content, bg="#f5f5f5")
        info_frame.pack(fill="x", pady=5)
        tk.Label(info_frame, text=f"Current Stock: {current_stock} units", font=("Arial", 11), bg="#f5f5f5").pack()
        tk.Label(info_frame, text=f"Cost Price: Rs. {cost_price:.2f} per piece", font=("Arial", 11), bg="#f5f5f5", fg="#e94560").pack()
        if unit_type == "Pack" and pack_price > 0:
            tk.Label(info_frame, text=f"Pack Price: Rs. {pack_price:.2f} per pack ({pieces_per_pack} pieces)", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Purchase Type Selection (if pack available)
        if unit_type == "Pack" and pack_price > 0:
            type_frame = tk.LabelFrame(content, text="Purchase Type", font=("Arial", 11, "bold"), bg="#f5f5f5")
            type_frame.pack(fill="x", pady=10)
            
            type_inner = tk.Frame(type_frame, bg="#f5f5f5")
            type_inner.pack(padx=15, pady=10)
            
            self.purchase_buy_type = tk.StringVar(value="Pack")
            
            piece_radio = tk.Radiobutton(type_inner, text=f"Buy by Piece (Rs. {cost_price:.2f} each)", 
                                          variable=self.purchase_buy_type, value="Piece", bg="#f5f5f5", font=("Arial", 10))
            piece_radio.pack(anchor="w", pady=5)
            
            pack_radio = tk.Radiobutton(type_inner, text=f"Buy by Pack (Rs. {pack_price:.2f} per pack - {pieces_per_pack} pieces)", 
                                          variable=self.purchase_buy_type, value="Pack", bg="#f5f5f5", font=("Arial", 10))
            pack_radio.pack(anchor="w", pady=5)
            
            # Separator
            tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
            
            # Quantity Frame
            qty_main_frame = tk.LabelFrame(content, text="Quantity", font=("Arial", 11, "bold"), bg="#f5f5f5")
            qty_main_frame.pack(fill="x", pady=10)
            
            qty_inner = tk.Frame(qty_main_frame, bg="#f5f5f5")
            qty_inner.pack(padx=15, pady=10)
            
            # For Piece mode
            piece_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(piece_qty_frame, text="Number of Pieces:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.purchase_piece_qty = tk.Entry(piece_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.purchase_piece_qty.pack(side="left", padx=10)
            self.purchase_piece_qty.insert(0, "1")
            
            # For Pack mode
            pack_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(pack_qty_frame, text="Number of Packs:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.purchase_pack_qty = tk.Entry(pack_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.purchase_pack_qty.pack(side="left", padx=10)
            self.purchase_pack_qty.insert(0, "1")
            
            tk.Label(pack_qty_frame, text=f"(= {pieces_per_pack} pieces each)", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack(side="left", padx=5)
            
            # Extra pieces frame
            extra_frame = tk.Frame(pack_qty_frame, bg="#f5f5f5")
            extra_frame.pack(pady=5)
            tk.Label(extra_frame, text="Extra Pieces (beyond packs):", font=("Arial", 10), bg="#f5f5f5").pack(side="left")
            self.purchase_extra_pieces = tk.Entry(extra_frame, font=("Arial", 11), width=8, justify="center")
            self.purchase_extra_pieces.pack(side="left", padx=10)
            self.purchase_extra_pieces.insert(0, "0")
            
            # Initially show pack mode (DEFAULT)
            piece_qty_frame.pack_forget()
            pack_qty_frame.pack()
            
            # Total pieces display
            total_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            total_frame.pack(pady=10)
            tk.Label(total_frame, text="Total Pieces:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
            self.purchase_total_pieces = tk.Label(total_frame, text="1", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
            self.purchase_total_pieces.pack(side="left", padx=10)
            
            # Total cost display
            cost_preview_frame = tk.Frame(content, bg="#f0f0f0", relief="ridge", bd=1)
            cost_preview_frame.pack(fill="x", pady=10)
            
            tk.Label(cost_preview_frame, text="💰 TOTAL COST:", font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#e94560").pack(side="left", padx=15, pady=10)
            self.purchase_total_cost = tk.Label(cost_preview_frame, text="Rs. 0.00", font=("Arial", 13, "bold"), bg="#f0f0f0", fg="#e94560")
            self.purchase_total_cost.pack(side="right", padx=15, pady=10)
            
            def update_purchase_total(*args):
                try:
                    if self.purchase_buy_type.get() == "Piece":
                        qty = int(self.purchase_piece_qty.get() or 0)
                        total_cost = qty * cost_price
                        self.purchase_total_pieces.config(text=str(qty))
                        self.purchase_total_cost.config(text=f"Rs. {total_cost:,.2f}")
                    else:
                        packs = int(self.purchase_pack_qty.get() or 0)
                        extra = int(self.purchase_extra_pieces.get() or 0)
                        qty = (packs * pieces_per_pack) + extra
                        total_cost = (packs * pack_price) + (extra * cost_price)
                        self.purchase_total_pieces.config(text=str(qty))
                        self.purchase_total_cost.config(text=f"Rs. {total_cost:,.2f}")
                except:
                    self.purchase_total_pieces.config(text="0")
                    self.purchase_total_cost.config(text="Rs. 0.00")
            
            def on_purchase_buy_type_change(*args):
                if self.purchase_buy_type.get() == "Piece":
                    piece_qty_frame.pack()
                    pack_qty_frame.pack_forget()
                    self.purchase_piece_qty.delete(0, tk.END)
                    self.purchase_piece_qty.insert(0, "1")
                else:
                    piece_qty_frame.pack_forget()
                    pack_qty_frame.pack()
                    self.purchase_pack_qty.delete(0, tk.END)
                    self.purchase_pack_qty.insert(0, "1")
                    self.purchase_extra_pieces.delete(0, tk.END)
                    self.purchase_extra_pieces.insert(0, "0")
                update_purchase_total()
            
            self.purchase_buy_type.trace('w', on_purchase_buy_type_change)
            self.purchase_piece_qty.bind("<KeyRelease>", update_purchase_total)
            self.purchase_pack_qty.bind("<KeyRelease>", update_purchase_total)
            self.purchase_extra_pieces.bind("<KeyRelease>", update_purchase_total)
            
            def add_to_cart_pack():
                try:
                    if self.purchase_buy_type.get() == "Piece":
                        quantity = int(self.purchase_piece_qty.get() or 0)
                    else:
                        packs = int(self.purchase_pack_qty.get() or 0)
                        extra = int(self.purchase_extra_pieces.get() or 0)
                        quantity = (packs * pieces_per_pack) + extra
                    
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    
                    total = quantity * cost_price
                    self.purchase_cart.append({'product_id': product_id, 'name': product_name, 'quantity': quantity, 'price': cost_price, 'total': total})
                    self.update_cart_display()
                    self.update_total_amount()
                    dialog.destroy()
                    self.update_status(f"Added {quantity} x {product_name} to purchase cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=15)
            tk.Button(btn_frame, text="Add to Cart", command=add_to_cart_pack, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            update_purchase_total()
        
        else:
            # Simple quantity dialog for products without pack
            tk.Label(content, text="Quantity:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
            quantity_entry = tk.Entry(content, font=("Arial", 12), width=15, justify="center")
            quantity_entry.pack()
            quantity_entry.focus()
            
            def add_to_cart_simple():
                try:
                    quantity = int(quantity_entry.get())
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    total = quantity * cost_price
                    self.purchase_cart.append({'product_id': product_id, 'name': product_name, 'quantity': quantity, 'price': cost_price, 'total': total})
                    self.update_cart_display()
                    self.update_total_amount()
                    dialog.destroy()
                    self.update_status(f"Added {quantity} x {product_name} to purchase cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="Add to Cart", command=add_to_cart_simple, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def update_cart_display(self):
        """Update cart treeview display"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        for i, item in enumerate(self.purchase_cart, 1):
            self.cart_tree.insert("", "end", values=(i, item['name'], item['quantity'], f"Rs. {item['price']:.2f}", f"Rs. {item['total']:.2f}"))
    
    def update_total_amount(self):
        """Update total amount display"""
        total = sum(item['total'] for item in self.purchase_cart)
        self.total_amount_label.config(text=f"Rs. {total:,.2f}")
    
    def remove_from_purchase_cart(self):
        """Remove selected item from cart"""
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an item to remove!")
            return
        item = self.cart_tree.item(selected[0])
        index = int(item['values'][0]) - 1
        if 0 <= index < len(self.purchase_cart):
            removed = self.purchase_cart.pop(index)
            self.update_cart_display()
            self.update_total_amount()
            self.update_status(f"Removed {removed['name']} from cart")
    
    def clear_purchase_cart(self):
        """Clear all items from cart"""
        if self.purchase_cart and messagebox.askyesno("Clear Cart", "Clear the entire cart?"):
            self.purchase_cart.clear()
            self.update_cart_display()
            self.update_total_amount()
            self.update_status("Cart cleared")
    
    def open_add_product_dialog_for_purchase(self):
        """Open dialog to add new product during purchase - WITH PACK SYSTEM (Same as Inventory Add Product)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Product to Purchase")
        dialog.geometry("650x750")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="➕ Add New Product to Purchase", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with scrollbar
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_frame = tk.Frame(content, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        fields = {}
        labels = [("Product Name *", "name"), ("Brand", "brand"), ("Category", "category"), 
                  ("Selling Price (Pack) Rs. *", "price"), ("Cost Price (Pack) Rs. *", "cost_price")]
        
        row = 0
        for label_text, field_key in labels:
            tk.Label(form_frame, text=label_text, font=("Arial", 11), bg="white", fg="#333").grid(row=row, column=0, sticky="w", padx=20, pady=8)
            entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
            entry.grid(row=row, column=1, padx=20, pady=8)
            fields[field_key] = entry
            row += 1
        
        # Purchase Quantity (in PACKS)
        qty_frame = tk.LabelFrame(form_frame, text="📦 Purchase Quantity (in PACKS)", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        qty_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        qty_inner = tk.Frame(qty_frame, bg="white")
        qty_inner.pack(padx=15, pady=10)
        
        tk.Label(qty_inner, text="Number of PACKS:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        purchase_packs_entry = tk.Entry(qty_inner, font=("Arial", 11), width=10)
        purchase_packs_entry.grid(row=0, column=1, padx=5, pady=5)
        purchase_packs_entry.insert(0, "1")
        fields["purchase_packs"] = purchase_packs_entry
        
        # Total pieces display
        tk.Label(qty_inner, text="Total Pieces:", font=("Arial", 10), bg="white").grid(row=0, column=2, sticky="w", padx=10, pady=5)
        total_pieces_label = tk.Label(qty_inner, text="0", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        total_pieces_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Reorder Level (in PACKS)
        reorder_frame = tk.Frame(form_frame, bg="white")
        reorder_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        tk.Label(reorder_frame, text="Reorder Level (in PACKS):", font=("Arial", 11), bg="white", fg="#333").pack(side="left", padx=(20, 10))
        reorder_entry = tk.Entry(reorder_frame, font=("Arial", 11), width=10)
        reorder_entry.pack(side="left")
        reorder_entry.insert(0, "5")
        fields["reorder_level_packs"] = reorder_entry
        
        # Pack Information Frame - DEFAULT PACK SELECTED
        pack_frame = tk.LabelFrame(form_frame, text="📦 Pack Information", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        pack_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        pack_inner = tk.Frame(pack_frame, bg="white")
        pack_inner.pack(padx=15, pady=10)
        
        # DEFAULT: Pack is selected (True)
        self.purchase_sell_as_pack_var = tk.BooleanVar(value=True)
        
        tk.Label(pack_inner, text="Pieces per Pack:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        pieces_per_pack_entry = tk.Entry(pack_inner, font=("Arial", 10), width=10)
        pieces_per_pack_entry.grid(row=0, column=1, padx=5, pady=5)
        pieces_per_pack_entry.insert(0, "12")
        
        # Piece price hint
        piece_hint = tk.Label(pack_inner, text="💡 Piece price will be: 0", font=("Arial", 8), bg="white", fg="#666")
        piece_hint.grid(row=1, column=0, columnspan=2, pady=5)
        
        def update_piece_hint(*args):
            try:
                pack_price = float(fields['price'].get() or 0)
                pieces = int(pieces_per_pack_entry.get() or 1)
                if pack_price > 0 and pieces > 0:
                    piece_price = pack_price / pieces
                    piece_hint.config(text=f"💡 Piece price: Rs. {piece_price:.2f} per piece")
                else:
                    piece_hint.config(text="💡 Enter pack price to calculate piece price")
            except:
                piece_hint.config(text="💡 Enter valid numbers")
        
        def update_total_pieces(*args):
            try:
                packs = int(purchase_packs_entry.get() or 0)
                pieces_per = int(pieces_per_pack_entry.get() or 1)
                total = packs * pieces_per
                total_pieces_label.config(text=str(total))
            except:
                total_pieces_label.config(text="0")
        
        fields['price'].bind("<KeyRelease>", update_piece_hint)
        pieces_per_pack_entry.bind("<KeyRelease>", update_piece_hint)
        pieces_per_pack_entry.bind("<KeyRelease>", update_total_pieces)
        purchase_packs_entry.bind("<KeyRelease>", update_total_pieces)
        
        # Note
        note_frame = tk.Frame(form_frame, bg="#e8f4f8", relief="ridge", bd=1)
        note_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        tk.Label(note_frame, text="💡 Note: Selling Price and Cost Price are per PACK.\nPurchase Quantity is in PACKS. Total pieces will be auto-calculated.\nStock will be added to inventory.", 
                font=("Arial", 9), bg="#e8f4f8", fg="#0c5460", justify="left").pack(padx=10, pady=8)
        
        def save_product():
            name = fields['name'].get().strip()
            brand = fields['brand'].get().strip()
            category = fields['category'].get().strip()
            
            try:
                pack_price = float(fields['price'].get())
                pack_cost = float(fields['cost_price'].get())
                purchase_packs = int(fields['purchase_packs'].get()) if fields['purchase_packs'].get() else 1
                reorder_packs = int(fields['reorder_level_packs'].get()) if fields['reorder_level_packs'].get() else 5
                pieces_per_pack = int(pieces_per_pack_entry.get()) if pieces_per_pack_entry.get() else 12
            except ValueError:
                messagebox.showwarning("Validation Error", "Please enter valid numeric values!")
                return
            
            if not name:
                messagebox.showwarning("Validation Error", "Product Name is required!")
                return
            if pack_price <= 0 or pack_cost <= 0:
                messagebox.showwarning("Validation Error", "Prices must be greater than 0!")
                return
            
            # Supplier will be selected from main purchase form (right side)
            supplier_id = None
            
            # Convert packs to pieces for database
            stock_quantity = purchase_packs * pieces_per_pack
            reorder_level = reorder_packs * pieces_per_pack
            
            try:
                # Insert product with pack info
                self.execute_query("""
                    INSERT INTO products (name, brand, category, price, cost_price, stock_quantity, reorder_level, supplier_id, unit_type, pieces_per_pack, pack_price) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, brand, category, pack_price, pack_cost, stock_quantity, reorder_level, supplier_id, "Pack", pieces_per_pack, pack_price))
                
                # Also add to purchase cart
                total_cost = purchase_packs * pack_cost
                product_id = self.fetch_one("SELECT id FROM products WHERE name = ?", (name,))[0]
                self.purchase_cart.append({
                    'product_id': product_id,
                    'name': name,
                    'quantity': stock_quantity,  # in pieces
                    'price': pack_cost,  # cost per pack
                    'total': total_cost
                })
                
                messagebox.showinfo("Success", f"Product '{name}' added successfully!\nPurchased: {purchase_packs} packs ({stock_quantity} pieces)\nPack Price: Rs.{pack_price:.2f}\nPiece Price: Rs.{pack_price/pieces_per_pack:.2f}")
                dialog.destroy()
                
                # Refresh cart display
                self.update_cart_display()
                self.update_total_amount()
                
                # Refresh product list
                self.load_products_for_purchase()
                self.update_status(f"✅ Added product: {name} ({purchase_packs} packs)")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product: {str(e)}")
        
        btn_frame = tk.Frame(content, bg="#f5f5f5")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="➕ Add to Cart", command=save_product, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        update_piece_hint()
        update_total_pieces()
    
    def complete_purchase(self):
        """Complete the purchase and update stock"""
        if not self.purchase_cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart first!")
            return
        
        # Check if all items are from "Add New Product" (have supplier_id in cart)
        # or from existing products
        has_new_product = any('supplier_id' in item for item in self.purchase_cart)
        has_existing_product = any('supplier_id' not in item for item in self.purchase_cart)
        
        # Determine which supplier to use
        if has_new_product and not has_existing_product:
            # All items are new products - use supplier from the first new product
            for item in self.purchase_cart:
                if 'supplier_id' in item:
                    supplier_id = item['supplier_id']
                    break
            supplier_selected = True
        elif has_existing_product:
            # There are existing products - must use right side supplier
            if not self.supplier_combo.get():
                messagebox.showwarning("Missing Supplier", "Please select a supplier for existing products!")
                return
            supplier_id = int(self.supplier_combo.get().split(" - ")[0])
            supplier_selected = True
        else:
            supplier_selected = False
        
        if not supplier_selected:
            messagebox.showwarning("Missing Supplier", "Please select a supplier!")
            return
        
        invoice_no = self.invoice_no_entry.get().strip()
        if not invoice_no:
            messagebox.showwarning("Missing Invoice", "Please enter invoice number!")
            return
        
        existing = self.fetch_one("SELECT id FROM purchases WHERE invoice_no = ?", (invoice_no,))
        if existing:
            messagebox.showwarning("Duplicate Invoice", f"Invoice number {invoice_no} already exists!")
            self.generate_invoice_number()
            return
        
        notes = self.notes_text.get("1.0", "end-1c").strip()
        total_amount = sum(item['total'] for item in self.purchase_cart)
        
        if not messagebox.askyesno("Confirm Purchase", f"Invoice: {invoice_no}\nItems: {len(self.purchase_cart)}\nTotal: Rs. {total_amount:,.2f}\n\nProceed?"):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO purchases (invoice_no, supplier_id, total_amount, notes) VALUES (?, ?, ?, ?)", (invoice_no, supplier_id, total_amount, notes))
            purchase_id = cursor.lastrowid
            
            for item in self.purchase_cart:
                cursor.execute("INSERT INTO purchase_items (purchase_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)", (purchase_id, item['product_id'], item['quantity'], item['price'], item['total']))
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ?, supplier_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item['quantity'], supplier_id, item['product_id']))
            
            cursor.execute("INSERT INTO ledger (transaction_type, reference_no, description, debit, credit, balance) VALUES (?, ?, ?, ?, ?, ?)", ("PURCHASE", invoice_no, f"Stock purchase from supplier", total_amount, 0, 0))
            conn.commit()
            conn.close()
            
            # Print purchase invoice
            self.print_purchase_invoice(invoice_no, supplier_id, total_amount)
            
            messagebox.showinfo("Success", f"Purchase completed!\nInvoice: {invoice_no}\nTotal: Rs. {total_amount:,.2f}")
            self.purchase_cart.clear()
            self.update_cart_display()
            self.update_total_amount()
            self.notes_text.delete("1.0", tk.END)
            self.generate_invoice_number()
            self.load_products_for_purchase()
            self.update_status(f"✅ Purchase completed: {invoice_no}")
            self.force_refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete purchase: {str(e)}")
    
    # ========== PHASE 5: INVENTORY MANAGEMENT ==========
    
    def show_inventory(self):
        """Show inventory management interface"""
        self.clear_main_content()
        
        # Initialize all variables FIRST
        self.inventory_search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.supplier_filter_var = tk.StringVar()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text="📦 Inventory Management", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        btn_frame = tk.Frame(header_frame, bg="#f5f5f5")
        btn_frame.pack(side="right")
        
        tk.Button(btn_frame, text="➕ Add New Product", command=self.open_add_product_dialog, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=15, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="📥 Export CSV", command=self.export_inventory_to_csv, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=15, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="⚠️ Low Stock Report", command=self.show_low_stock_report, bg="#f6c23e", fg="white", font=("Arial", 11, "bold"), padx=15, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(filter_frame, text="🔍 Search:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.inventory_search_var.trace('w', lambda *args: self.filter_inventory())
        tk.Entry(filter_frame, textvariable=self.inventory_search_var, font=("Arial", 11), width=25).pack(side="left", padx=5, pady=8)
        
        tk.Label(filter_frame, text="Category:", font=("Arial", 11), bg="white").pack(side="left", padx=(20, 5), pady=8)
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter_var, font=("Arial", 11), width=15, state="readonly")
        self.category_combo.pack(side="left", padx=5, pady=8)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_inventory())
        
        tk.Label(filter_frame, text="Supplier:", font=("Arial", 11), bg="white").pack(side="left", padx=(20, 5), pady=8)
        self.supplier_filter_combo = ttk.Combobox(filter_frame, textvariable=self.supplier_filter_var, font=("Arial", 11), width=20, state="readonly")
        self.supplier_filter_combo.pack(side="left", padx=5, pady=8)
        self.supplier_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_inventory())
        
        tk.Button(filter_frame, text="🗑️ Clear Filters", command=self.clear_inventory_filters, bg="#e74a3b", fg="white", font=("Arial", 9), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=10, pady=5)
        
        stats_frame = tk.Frame(main_container, bg="#f5f5f5")
        stats_frame.pack(fill="x", pady=(0, 10))
        self.inventory_stats_label = tk.Label(stats_frame, text="", font=("Arial", 10), bg="#f5f5f5", fg="#666")
        self.inventory_stats_label.pack(side="left")
        
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Product Name", "Brand", "Category", "Stock", "Reorder Level", "Status", "Cost Price", "Selling Price", "Supplier", "Profit Margin")
        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.inventory_tree.heading("ID", text="ID")
        self.inventory_tree.heading("Product Name", text="Product Name")
        self.inventory_tree.heading("Brand", text="Brand")
        self.inventory_tree.heading("Category", text="Category")
        self.inventory_tree.heading("Stock", text="Stock")
        self.inventory_tree.heading("Reorder Level", text="Reorder Level")
        self.inventory_tree.heading("Status", text="Status")
        self.inventory_tree.heading("Cost Price", text="Cost Price (Rs.)")
        self.inventory_tree.heading("Selling Price", text="Selling Price (Rs.)")
        self.inventory_tree.heading("Supplier", text="Supplier")
        self.inventory_tree.heading("Profit Margin", text="Profit Margin")
        
        self.inventory_tree.column("ID", width=50)
        self.inventory_tree.column("Product Name", width=180)
        self.inventory_tree.column("Brand", width=100)
        self.inventory_tree.column("Category", width=100)
        self.inventory_tree.column("Stock", width=80)
        self.inventory_tree.column("Reorder Level", width=100)
        self.inventory_tree.column("Status", width=80)
        self.inventory_tree.column("Cost Price", width=120)
        self.inventory_tree.column("Selling Price", width=120)
        self.inventory_tree.column("Supplier", width=150)
        self.inventory_tree.column("Profit Margin", width=100)
        
        self.inventory_tree.tag_configure('lowstock', background='#ffe6e6')
        self.inventory_tree.tag_configure('normal', background='white')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.inventory_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.inventory_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.inventory_context_menu = tk.Menu(self.root, tearoff=0)
        self.inventory_context_menu.add_command(label="✏️ Edit Product", command=self.edit_selected_product)
        self.inventory_context_menu.add_command(label="📊 Adjust Stock", command=self.adjust_stock)
        self.inventory_context_menu.add_separator()
        self.inventory_context_menu.add_command(label="🗑️ Delete Product", command=self.delete_selected_product)
        
        self.inventory_tree.bind("<Button-3>", self.show_inventory_context_menu)
        self.inventory_tree.bind("<Double-1>", lambda e: self.edit_selected_product())
        
        # Create summary frame with stock value label BEFORE loading inventory
        summary_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        summary_frame.pack(fill="x", pady=(10, 0))
        self.stock_value_label = tk.Label(summary_frame, text="", font=("Arial", 11, "bold"), bg="white", fg="#e94560", pady=8)
        self.stock_value_label.pack()
        
        # Now load filter options and inventory (after label is created)
        self.load_filter_options()
        self.load_inventory()
    
    def load_filter_options(self):
        """Load category and supplier filter options"""
        try:
            categories = self.fetch_all("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
            category_list = ["All"] + [c[0] for c in categories]
            self.category_combo['values'] = category_list
            self.category_combo.set("All")
            
            suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
            supplier_list = ["All"] + [f"{s[0]} - {s[1]}" for s in suppliers]
            self.supplier_filter_combo['values'] = supplier_list
            self.supplier_filter_combo.set("All")
        except Exception as e:
            self.update_status(f"Error loading filters: {str(e)}")
    
    def clear_inventory_filters(self):
        """Clear all filters and reset inventory view"""
        self.inventory_search_var.set("")
        self.category_combo.set("All")
        self.supplier_filter_combo.set("All")
        self.load_inventory()
    
    def filter_inventory(self):
        """Apply filters to inventory"""
        self.load_inventory()
    
        # ========== PHASE 5: INVENTORY MANAGEMENT ==========
    
    def load_filter_options(self):
        """Load category and supplier filter options"""
        try:
            categories = self.fetch_all("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
            category_list = ["All"] + [c[0] for c in categories]
            self.category_combo['values'] = category_list
            self.category_combo.set("All")
            
            suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
            supplier_list = ["All"] + [f"{s[0]} - {s[1]}" for s in suppliers]
            self.supplier_filter_combo['values'] = supplier_list
            self.supplier_filter_combo.set("All")
        except Exception as e:
            self.update_status(f"Error loading filters: {str(e)}")
    
    def clear_inventory_filters(self):
        """Clear all filters and reset inventory view"""
        self.inventory_search_var.set("")
        self.category_combo.set("All")
        self.supplier_filter_combo.set("All")
        self.load_inventory()
    
    def filter_inventory(self):
        """Apply filters to inventory"""
        self.load_inventory()
    
    def load_inventory(self):
        """Load inventory data into treeview with filters"""
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        try:
            # Build query with filters
            query = """
                SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, 
                       p.reorder_level, p.price, p.cost_price, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            
            # Search filter
            search_term = self.inventory_search_var.get().strip()
            if search_term:
                query += " AND (p.name LIKE ? OR p.brand LIKE ?)"
                params.extend([f'%{search_term}%', f'%{search_term}%'])
            
            # Category filter
            category = self.category_filter_var.get()
            if category and category != "All":
                query += " AND p.category = ?"
                params.append(category)
            
            # Supplier filter
            supplier_filter = self.supplier_filter_var.get()
            if supplier_filter and supplier_filter != "All":
                supplier_id = int(supplier_filter.split(" - ")[0])
                query += " AND p.supplier_id = ?"
                params.append(supplier_id)
            
                query += " ORDER BY p.id DESC LIMIT 1000"
            
            products = self.fetch_all(query, params)
            
            total_stock_value = 0
            low_stock_count = 0
            
            for product in products:
                # product tuple indices: 
                # 0=id, 1=name, 2=brand, 3=category, 4=stock_quantity, 
                # 5=reorder_level, 6=price, 7=cost_price, 8=supplier_name
                
                stock = product[4]
                reorder_level = product[5]
                is_low_stock = stock <= reorder_level
                
                if is_low_stock:
                    low_stock_count += 1
                
                status = "⚠️ LOW STOCK" if is_low_stock else "✓ In Stock"
                total_stock_value += stock * product[7]  # stock * cost_price
                                # Get pack info for display (ADD THIS)
                pieces_per_pack = product[10] if len(product) > 10 else 1
                unit_type = product[9] if len(product) > 9 else "Piece"
                
                if unit_type == "Pack" and pieces_per_pack > 1:
                    packs = stock // pieces_per_pack
                    pieces = stock % pieces_per_pack
                    stock_display = f"{packs} pk + {pieces} pcs"
                    reorder_display = f"{reorder_level // pieces_per_pack} pk"
                else:
                    stock_display = str(stock)
                    reorder_display = str(reorder_level)
                # Calculate profit margin
                cost_price = product[7]
                selling_price = product[6]
                if cost_price > 0:
                    margin_percent = ((selling_price - cost_price) / cost_price) * 100
                    margin_text = f"{margin_percent:.1f}%"
                else:
                    margin_text = "0%"
                
                tag = 'lowstock' if is_low_stock else 'normal'
                
                self.inventory_tree.insert("", "end", values=(
                    product[0],           # ID
                    product[1],           # Product Name
                    product[2] or "-",    # Brand
                    product[3] or "-",    # Category
                    stock_display,                # Stock
                    reorder_display,        # Reorder Level
                    status,               # Status
                    f"Rs. {product[7]:.2f}",   # Cost Price
                    f"Rs. {product[6]:.2f}",   # Selling Price
                    product[8] or "-",    # Supplier
                    margin_text           # Profit Margin
                ), tags=(tag,))
            
            # Update statistics
            total_products = len(products)
            self.inventory_stats_label.config(
                text=f"📊 Total Products: {total_products} | Low Stock: {low_stock_count}"
            )
            
            self.stock_value_label.config(
                text=f"💰 Total Inventory Value (at cost): Rs. {total_stock_value:,.2f}"
            )
            
            self.update_status(f"Loaded {total_products} products")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory: {str(e)}")
            self.update_status(f"❌ Failed to load inventory: {str(e)}")
    def load_inventory_paginated(self, page=1, page_size=200):
        """Load inventory with pagination for large data"""
        offset = (page - 1) * page_size
        self.current_inventory_page = page
        self.inventory_page_size = page_size
        
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        try:
            query = """
                SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, 
                       p.reorder_level, p.price, p.cost_price, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.id DESC
                LIMIT ? OFFSET ?
            """
            
            products = self.fetch_all(query, (page_size, offset))
            
            # ... rest of display code same as load_inventory ...
            
            # Update status with page info
            total_count = self.fetch_one("SELECT COUNT(*) FROM products")[0]
            self.update_status(f"Page {page} of {((total_count-1)//page_size)+1} | Showing {len(products)} of {total_count} products")
            
            # Add pagination buttons
            self.add_pagination_buttons(page, total_count, page_size)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory: {str(e)}")
    
    def add_pagination_buttons(self, current_page, total_count, page_size):
        """Add pagination buttons at bottom of inventory"""
        total_pages = ((total_count - 1) // page_size) + 1
        
        pagination_frame = tk.Frame(self.main_frame, bg="#f5f5f5")
        pagination_frame.pack(fill="x", pady=5)
        
        if current_page > 1:
            prev_btn = tk.Button(pagination_frame, text="◀ Previous", 
                                command=lambda: self.load_inventory_paginated(current_page-1, page_size),
                                bg="#36b9cc", fg="white", font=("Arial", 9), padx=10, pady=3)
            prev_btn.pack(side="left", padx=5)
        
        page_label = tk.Label(pagination_frame, text=f"Page {current_page} of {total_pages}", 
                              font=("Arial", 9), bg="#f5f5f5", fg="#666")
        page_label.pack(side="left", padx=10)
        
        if current_page < total_pages:
            next_btn = tk.Button(pagination_frame, text="Next ▶", 
                                command=lambda: self.load_inventory_paginated(current_page+1, page_size),
                                bg="#36b9cc", fg="white", font=("Arial", 9), padx=10, pady=3)
            next_btn.pack(side="left", padx=5)
    
    def open_add_product_dialog(self):
        """Open dialog to add new product - PACK MODE DEFAULT"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("650x750")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="➕ Add New Product", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with scrollbar
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_frame = tk.Frame(content, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        fields = {}
        labels = [("Product Name *", "name"), ("Brand", "brand"), ("Category", "category"), 
                  ("Selling Price (Pack) Rs. *", "price"), ("Cost Price (Pack) Rs. *", "cost_price")]
        
        row = 0
        for label_text, field_key in labels:
            tk.Label(form_frame, text=label_text, font=("Arial", 11), bg="white", fg="#333").grid(row=row, column=0, sticky="w", padx=20, pady=8)
            entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
            entry.grid(row=row, column=1, padx=20, pady=8)
            fields[field_key] = entry
            row += 1
        
        # Existing Stock Frame (in PACKS)
        stock_frame = tk.LabelFrame(form_frame, text="📦 Existing Stock (in PACKS)", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        stock_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        stock_inner = tk.Frame(stock_frame, bg="white")
        stock_inner.pack(padx=15, pady=10)
        
        tk.Label(stock_inner, text="Number of PACKS:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        stock_packs_entry = tk.Entry(stock_inner, font=("Arial", 11), width=15)
        stock_packs_entry.grid(row=0, column=1, padx=5, pady=5)
        stock_packs_entry.insert(0, "0")
        fields["stock_packs"] = stock_packs_entry
        
        # Total pieces display
        tk.Label(stock_inner, text="Total Pieces:", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        total_pieces_label = tk.Label(stock_inner, text="0", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        total_pieces_label.grid(row=1, column=1, padx=5, pady=5)
        
        # Reorder Level (in PACKS)
        reorder_frame = tk.Frame(form_frame, bg="white")
        reorder_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        tk.Label(reorder_frame, text="Reorder Level (in PACKS):", font=("Arial", 11), bg="white", fg="#333").pack(side="left", padx=(20, 10))
        reorder_entry = tk.Entry(reorder_frame, font=("Arial", 11), width=15)
        reorder_entry.pack(side="left")
        reorder_entry.insert(0, "5")
        fields["reorder_level_packs"] = reorder_entry
        
        # Pack Information Frame - DEFAULT PACK SELECTED
        pack_frame = tk.LabelFrame(form_frame, text="📦 Pack Information", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        pack_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        pack_inner = tk.Frame(pack_frame, bg="white")
        pack_inner.pack(padx=15, pady=10)
        
        # DEFAULT: Pack is selected
        self.sell_as_pack_var = tk.BooleanVar(value=True)
        
        tk.Label(pack_inner, text="Pieces per Pack:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        pieces_per_pack_entry = tk.Entry(pack_inner, font=("Arial", 10), width=10)
        pieces_per_pack_entry.grid(row=0, column=1, padx=5, pady=5)
        pieces_per_pack_entry.insert(0, "12")
        
        # Piece price hint
        piece_hint = tk.Label(pack_inner, text="💡 Piece price will be: 0", font=("Arial", 8), bg="white", fg="#666")
        piece_hint.grid(row=1, column=0, columnspan=2, pady=5)
        
        def update_piece_hint(*args):
            try:
                pack_price = float(fields['price'].get() or 0)
                pieces = int(pieces_per_pack_entry.get() or 1)
                if pack_price > 0 and pieces > 0:
                    piece_price = pack_price / pieces
                    piece_hint.config(text=f"💡 Piece price: Rs. {piece_price:.2f} per piece")
                else:
                    piece_hint.config(text="💡 Enter pack price to calculate piece price")
            except:
                piece_hint.config(text="💡 Enter valid numbers")
        
        def update_total_pieces(*args):
            try:
                packs = int(stock_packs_entry.get() or 0)
                pieces_per = int(pieces_per_pack_entry.get() or 1)
                total = packs * pieces_per
                total_pieces_label.config(text=str(total))
            except:
                total_pieces_label.config(text="0")
        
        fields['price'].bind("<KeyRelease>", update_piece_hint)
        pieces_per_pack_entry.bind("<KeyRelease>", update_piece_hint)
        pieces_per_pack_entry.bind("<KeyRelease>", update_total_pieces)
        stock_packs_entry.bind("<KeyRelease>", update_total_pieces)
        
        # Supplier (Optional)
        supplier_frame = tk.Frame(form_frame, bg="white")
        supplier_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        tk.Label(supplier_frame, text="Supplier (Optional):", font=("Arial", 11), bg="white", fg="#333").pack(side="left", padx=(20, 10))
        supplier_combo = ttk.Combobox(supplier_frame, font=("Arial", 11), width=30, state="readonly")
        supplier_combo.pack(side="left")
        
        suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
        supplier_list = ["-- None (No Supplier) --"] + [f"{s[0]} - {s[1]}" for s in suppliers]
        supplier_combo['values'] = supplier_list
        supplier_combo.current(0)
        
        # Note
        note_frame = tk.Frame(form_frame, bg="#e8f4f8", relief="ridge", bd=1)
        note_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        row += 1
        
        tk.Label(note_frame, text="💡 Note: Selling Price and Cost Price are per PACK.\nStock is entered in PACKS. Piece price will be auto-calculated.", 
                font=("Arial", 9), bg="#e8f4f8", fg="#0c5460", justify="left").pack(padx=10, pady=8)
        
        def save_product():
            name = fields['name'].get().strip()
            brand = fields['brand'].get().strip()
            category = fields['category'].get().strip()
            
            try:
                pack_price = float(fields['price'].get())
                pack_cost = float(fields['cost_price'].get())
                stock_packs = int(fields['stock_packs'].get()) if fields['stock_packs'].get() else 0
                reorder_packs = int(fields['reorder_level_packs'].get()) if fields['reorder_level_packs'].get() else 5
                pieces_per_pack = int(pieces_per_pack_entry.get()) if pieces_per_pack_entry.get() else 12
            except ValueError:
                messagebox.showwarning("Validation Error", "Please enter valid numeric values!")
                return
            
            if not name:
                messagebox.showwarning("Validation Error", "Product Name is required!")
                return
            if pack_price <= 0 or pack_cost <= 0:
                messagebox.showwarning("Validation Error", "Prices must be greater than 0!")
                return
            
            supplier_id = None
            if supplier_combo.get() and supplier_combo.get() != "-- None (No Supplier) --":
                try:
                    supplier_id = int(supplier_combo.get().split(" - ")[0])
                except:
                    pass
            
            # Convert packs to pieces for database
            stock_quantity = stock_packs * pieces_per_pack
            reorder_level = reorder_packs * pieces_per_pack
            
            try:
                self.execute_query("""
                    INSERT INTO products (name, brand, category, price, cost_price, stock_quantity, reorder_level, supplier_id, unit_type, pieces_per_pack, pack_price) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, brand, category, pack_price, pack_cost, stock_quantity, reorder_level, supplier_id, "Pack", pieces_per_pack, pack_price))
                
                messagebox.showinfo("Success", f"Product '{name}' added successfully!\nStock: {stock_packs} packs ({stock_quantity} pieces)\nPack Price: Rs.{pack_price:.2f}\nPiece Price: Rs.{pack_price/pieces_per_pack:.2f}")
                self.refresh_dashboard_after_add()
                dialog.destroy()
                self.load_inventory()
                self.load_filter_options()
                self.show_dashboard()
                self.update_status(f"✅ Added product: {name} ({stock_packs} packs)")
                self.force_refresh_dashboard()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product: {str(e)}")
        
        btn_frame = tk.Frame(content, bg="#f5f5f5")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="💾 Save Product", command=save_product, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        update_piece_hint()
        update_total_pieces()
    
    def show_inventory_context_menu(self, event):
        """Show right-click context menu for inventory tree"""
        item = self.inventory_tree.identify_row(event.y)
        if item:
            self.inventory_tree.selection_set(item)
            self.inventory_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_product_id(self):
        """Get selected product ID from inventory tree"""
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return None
        item = self.inventory_tree.item(selected[0])
        return item['values'][0]
    
    def edit_selected_product(self):
        """Edit selected product - SAFE VERSION with Pack System"""
        product_id = self.get_selected_product_id()
        if not product_id:
            return
        
        product = self.fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))
        if not product:
            messagebox.showerror("Error", "Product not found!")
            return
        
        # Safe column access with fallbacks
        try:
            product_name = product[1] if len(product) > 1 else ""
            product_brand = product[2] if len(product) > 2 else ""
            product_category = product[3] if len(product) > 3 else ""
            selling_price = float(product[4]) if len(product) > 4 and product[4] else 0
            cost_price = float(product[5]) if len(product) > 5 and product[5] else 0
            stock_quantity = int(product[6]) if len(product) > 6 and product[6] else 0
            reorder_level = int(product[7]) if len(product) > 7 and product[7] else 10
            supplier_id = product[8] if len(product) > 8 else None
            unit_type = product[9] if len(product) > 9 and product[9] else "Pack"
            
            # SAFE conversion for pieces_per_pack
            try:
                pieces_per_pack = int(product[10]) if len(product) > 10 and product[10] and str(product[10]).isdigit() else 12
            except (ValueError, TypeError):
                pieces_per_pack = 12
            
            # SAFE conversion for pack_price
            try:
                pack_price = float(product[11]) if len(product) > 11 and product[11] else selling_price
            except (ValueError, TypeError):
                pack_price = selling_price
            
        except Exception as e:
            messagebox.showerror("Error", f"Product data corrupted!\n{str(e)}")
            return
        
        # Convert to packs
        stock_packs = stock_quantity // pieces_per_pack if pieces_per_pack > 0 else stock_quantity
        stock_extra = stock_quantity % pieces_per_pack if pieces_per_pack > 0 else 0
        reorder_packs = reorder_level // pieces_per_pack if pieces_per_pack > 0 else reorder_level
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Product")
        dialog.geometry("600x700")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="✏️ Edit Product", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with scrollbar
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_frame = tk.Frame(content, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Product Name
        tk.Label(form_frame, text="Product Name *", font=("Arial", 11), bg="white", fg="#333").grid(row=0, column=0, sticky="w", padx=20, pady=8)
        name_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        name_entry.grid(row=0, column=1, padx=20, pady=8)
        name_entry.insert(0, product_name)
        
        # Brand
        tk.Label(form_frame, text="Brand", font=("Arial", 11), bg="white", fg="#333").grid(row=1, column=0, sticky="w", padx=20, pady=8)
        brand_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        brand_entry.grid(row=1, column=1, padx=20, pady=8)
        brand_entry.insert(0, product_brand)
        
        # Category
        tk.Label(form_frame, text="Category", font=("Arial", 11), bg="white", fg="#333").grid(row=2, column=0, sticky="w", padx=20, pady=8)
        category_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        category_entry.grid(row=2, column=1, padx=20, pady=8)
        category_entry.insert(0, product_category)
        
        # Selling Price (Pack)
        tk.Label(form_frame, text="Selling Price (Pack) Rs.", font=("Arial", 11), bg="white", fg="#333").grid(row=3, column=0, sticky="w", padx=20, pady=8)
        price_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        price_entry.grid(row=3, column=1, padx=20, pady=8)
        price_entry.insert(0, str(selling_price))
        
        # Cost Price (Pack)
        tk.Label(form_frame, text="Cost Price (Pack) Rs.", font=("Arial", 11), bg="white", fg="#333").grid(row=4, column=0, sticky="w", padx=20, pady=8)
        cost_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        cost_entry.grid(row=4, column=1, padx=20, pady=8)
        cost_entry.insert(0, str(cost_price))
        
        # Stock (in Packs)
        tk.Label(form_frame, text="Current Stock (in PACKS)", font=("Arial", 11), bg="white", fg="#333").grid(row=5, column=0, sticky="w", padx=20, pady=8)
        stock_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        stock_entry.grid(row=5, column=1, padx=20, pady=8)
        stock_entry.insert(0, str(stock_packs))
        
        # Extra pieces hint
        if stock_extra > 0:
            tk.Label(form_frame, text=f"(+ {stock_extra} extra pieces)", font=("Arial", 9), bg="white", fg="#e94560").grid(row=5, column=2, padx=5, pady=8)
        
        # Reorder Level (in Packs)
        tk.Label(form_frame, text="Reorder Level (in PACKS)", font=("Arial", 11), bg="white", fg="#333").grid(row=6, column=0, sticky="w", padx=20, pady=8)
        reorder_entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
        reorder_entry.grid(row=6, column=1, padx=20, pady=8)
        reorder_entry.insert(0, str(reorder_packs))
        
        # Pack Information
        pack_frame = tk.LabelFrame(form_frame, text="📦 Pack Information", font=("Arial", 11, "bold"), bg="white", fg="#e94560")
        pack_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        pack_inner = tk.Frame(pack_frame, bg="white")
        pack_inner.pack(padx=15, pady=10)
        
        tk.Label(pack_inner, text="Pieces per Pack:", font=("Arial", 10), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        pieces_entry = tk.Entry(pack_inner, font=("Arial", 10), width=10)
        pieces_entry.grid(row=0, column=1, padx=5, pady=5)
        pieces_entry.insert(0, str(pieces_per_pack))
        
        tk.Label(pack_inner, text="Pack Price (Rs.):", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        pack_price_entry = tk.Entry(pack_inner, font=("Arial", 10), width=10)
        pack_price_entry.grid(row=1, column=1, padx=5, pady=5)
        pack_price_entry.insert(0, str(pack_price))
        
        # Piece price hint
        piece_hint = tk.Label(pack_inner, text="", font=("Arial", 8), bg="white", fg="#666")
        piece_hint.grid(row=2, column=0, columnspan=2, pady=5)
        
        def update_hint(*args):
            try:
                p_price = float(pack_price_entry.get()) if pack_price_entry.get() else 0
                pcs = int(pieces_entry.get()) if pieces_entry.get() else 1
                if p_price > 0 and pcs > 0:
                    piece_hint.config(text=f"💡 Piece price: Rs. {p_price/pcs:.2f}")
                else:
                    piece_hint.config(text="💡 Enter pack price to calculate piece price")
            except:
                piece_hint.config(text="💡 Enter valid numbers")
        
        pack_price_entry.bind("<KeyRelease>", update_hint)
        pieces_entry.bind("<KeyRelease>", update_hint)
        
        # Supplier
        tk.Label(form_frame, text="Supplier (Optional)", font=("Arial", 11), bg="white", fg="#333").grid(row=8, column=0, sticky="w", padx=20, pady=8)
        supplier_combo = ttk.Combobox(form_frame, font=("Arial", 11), width=32, state="readonly")
        supplier_combo.grid(row=8, column=1, padx=20, pady=8)
        
        suppliers = self.fetch_all("SELECT id, name FROM suppliers ORDER BY name")
        supplier_list = ["-- None (No Supplier) --"] + [f"{s[0]} - {s[1]}" for s in suppliers]
        supplier_combo['values'] = supplier_list
        
        if supplier_id:
            current_supplier = self.fetch_one("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
            if current_supplier:
                supplier_combo.set(f"{supplier_id} - {current_supplier[0]}")
            else:
                supplier_combo.current(0)
        else:
            supplier_combo.current(0)
        
        # Save Function
        def save_product():
            try:
                new_name = name_entry.get().strip()
                new_brand = brand_entry.get().strip()
                new_category = category_entry.get().strip()
                new_price = float(price_entry.get()) if price_entry.get() else 0
                new_cost = float(cost_entry.get()) if cost_entry.get() else 0
                new_stock_packs = int(stock_entry.get()) if stock_entry.get() else 0
                new_reorder_packs = int(reorder_entry.get()) if reorder_entry.get() else 0
                new_pieces_per_pack = int(pieces_entry.get()) if pieces_entry.get() else 12
                new_pack_price = float(pack_price_entry.get()) if pack_price_entry.get() else new_price
                
                if not new_name:
                    messagebox.showwarning("Error", "Product Name required!")
                    return
                if new_price <= 0 or new_cost <= 0:
                    messagebox.showwarning("Error", "Prices must be greater than 0!")
                    return
                
                # Convert packs to pieces
                new_stock_quantity = new_stock_packs * new_pieces_per_pack
                new_reorder_level = new_reorder_packs * new_pieces_per_pack
                
                new_supplier_id = None
                sel = supplier_combo.get()
                if sel and sel != "-- None (No Supplier) --":
                    try:
                        new_supplier_id = int(sel.split(" - ")[0])
                    except:
                        pass
                
                self.execute_query("""
                    UPDATE products 
                    SET name=?, brand=?, category=?, price=?, cost_price=?, 
                        stock_quantity=?, reorder_level=?, supplier_id=?,
                        pieces_per_pack=?, pack_price=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (new_name, new_brand, new_category, new_price, new_cost, 
                      new_stock_quantity, new_reorder_level, new_supplier_id,
                      new_pieces_per_pack, new_pack_price, product_id))
                
                messagebox.showinfo("Success", "Product updated successfully!")
                self.refresh_dashboard_after_add()
                dialog.destroy()
                self.load_inventory()
                self.show_dashboard()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid value: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
        
        btn_frame = tk.Frame(content, bg="#f5f5f5")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="💾 Update Product", command=save_product, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        update_hint()
    
    def adjust_stock(self):
        """Manually adjust stock quantity"""
        product_id = self.get_selected_product_id()
        if not product_id:
            return
        
        product = self.fetch_one("SELECT id, name, stock_quantity FROM products WHERE id = ?", (product_id,))
        if not product:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Adjust Stock - {product[1]}")
        dialog.geometry("400x300")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product[1]}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        info_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(info_frame, text=f"Current Stock: {product[2]} units", font=("Arial", 12), bg="white", fg="#e94560").pack(pady=10)
        
        tk.Label(dialog, text="Adjustment Type:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        adjustment_type = tk.StringVar(value="add")
        type_frame = tk.Frame(dialog, bg="#f5f5f5")
        type_frame.pack()
        tk.Radiobutton(type_frame, text="➕ Add Stock", variable=adjustment_type, value="add", bg="#f5f5f5", font=("Arial", 11)).pack(side="left", padx=10)
        tk.Radiobutton(type_frame, text="➖ Remove Stock", variable=adjustment_type, value="remove", bg="#f5f5f5", font=("Arial", 11)).pack(side="left", padx=10)
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        quantity_entry = tk.Entry(dialog, font=("Arial", 12), width=15, justify="center")
        quantity_entry.pack()
        
        tk.Label(dialog, text="Reason:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        reason_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        reason_entry.pack()
        
        def save_adjustment():
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                    return
                reason = reason_entry.get().strip() or "Manual adjustment"
                new_stock = product[2]
                if adjustment_type.get() == "add":
                    new_stock += quantity
                    change_text = f"+{quantity}"
                else:
                    if quantity > product[2]:
                        messagebox.showwarning("Invalid", f"Cannot remove more than current stock ({product[2]})!")
                        return
                    new_stock -= quantity
                    change_text = f"-{quantity}"
                
                self.execute_query(
                    "UPDATE products SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_stock, product_id)
                )
                self.execute_query(
                    "INSERT INTO ledger (transaction_type, reference_no, description, debit, credit) VALUES (?, ?, ?, ?, ?)",
                    ("STOCK_ADJUST", f"ADJ-{product_id}", f"{reason}: {product[1]} {change_text}", 0, 0)
                )
                messagebox.showinfo("Success", f"Stock adjusted!\n{product[1]}: {product[2]} → {new_stock}")
                dialog.destroy()
                self.load_inventory()
                self.update_status(f"✅ Stock adjusted for {product[1]}")
                self.force_refresh_dashboard()
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid number!")
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="✅ Apply Adjustment", command=save_adjustment, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def delete_selected_product(self):
        """Delete selected product (with safety checks)"""
        product_id = self.get_selected_product_id()
        if not product_id:
            return
        
        sale_count = self.fetch_one("SELECT COUNT(*) FROM sale_items WHERE product_id = ?", (product_id,))
        if sale_count and sale_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This product has {sale_count[0]} sales records.")
            return
        
        purchase_count = self.fetch_one("SELECT COUNT(*) FROM purchase_items WHERE product_id = ?", (product_id,))
        if purchase_count and purchase_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This product has {purchase_count[0]} purchase records.")
            return
        
        product = self.fetch_one("SELECT name FROM products WHERE id = ?", (product_id,))
        if not product:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete product '{product[0]}'?", icon='warning'):
            try:
                self.execute_query("DELETE FROM products WHERE id = ?", (product_id,))
                messagebox.showinfo("Success", "Product deleted successfully!")
                self.load_inventory()
                self.load_filter_options()
                self.show_dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
    
    def show_low_stock_report(self):
        """Show low stock report dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ Low Stock Report")
        dialog.geometry("800x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="⚠️ Products Below Reorder Level", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#e94560").pack(pady=10)
        
        low_stock_products = self.fetch_all("""
            SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, p.reorder_level, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock_quantity <= p.reorder_level
            ORDER BY p.stock_quantity ASC
        """)
        
        tk.Label(dialog, text=f"Total Low Stock Products: {len(low_stock_products)}", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e74a3b").pack(pady=10)
        
        tree_frame = tk.Frame(dialog, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("ID", "Product Name", "Brand", "Category", "Current Stock", "Reorder Level", "Supplier")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        tree.heading("ID", text="ID")
        tree.heading("Product Name", text="Product Name")
        tree.heading("Brand", text="Brand")
        tree.heading("Category", text="Category")
        tree.heading("Current Stock", text="Current Stock")
        tree.heading("Reorder Level", text="Reorder Level")
        tree.heading("Supplier", text="Supplier")
        
        tree.column("ID", width=50)
        tree.column("Product Name", width=200)
        tree.column("Brand", width=100)
        tree.column("Category", width=100)
        tree.column("Current Stock", width=100)
        tree.column("Reorder Level", width=100)
        tree.column("Supplier", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for product in low_stock_products:
            tree.insert("", "end", values=(
                product[0], product[1], product[2] or "-", product[3] or "-", 
                product[4], product[5], product[6] or "-"
            ))
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        
        def export_report():
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Product Name', 'Brand', 'Category', 'Current Stock', 'Reorder Level', 'Supplier'])
                    for p in low_stock_products:
                        writer.writerow(p)
                messagebox.showinfo("Success", f"Report exported to {file_path}")
        
        tk.Button(btn_frame, text="📥 Export Report", command=export_report, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def export_inventory_to_csv(self):
        """Export inventory to CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Inventory Export"
            )
            if not file_path:
                return
            
            products = self.fetch_all("""
                SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, p.reorder_level,
                       p.price, p.cost_price, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.name
            """)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Product Name', 'Brand', 'Category', 'Stock Quantity', 'Reorder Level', 
                               'Selling Price (Rs.)', 'Cost Price (Rs.)', 'Supplier'])
                writer.writerows(products)
            
            messagebox.showinfo("Export Successful", f"Inventory exported to:\n{file_path}")
            self.update_status(f"📥 Exported {len(products)} products to CSV")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def show_inventory_context_menu(self, event):
        """Show right-click context menu for inventory tree"""
        item = self.inventory_tree.identify_row(event.y)
        if item:
            self.inventory_tree.selection_set(item)
            self.inventory_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_product_id(self):
        """Get selected product ID from inventory tree"""
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return None
        item = self.inventory_tree.item(selected[0])
        return item['values'][0]
    
    def adjust_stock(self):
        """Manually adjust stock quantity"""
        product_id = self.get_selected_product_id()
        if not product_id:
            return
        
        product = self.fetch_one("SELECT id, name, stock_quantity FROM products WHERE id = ?", (product_id,))
        if not product:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Adjust Stock - {product[1]}")
        dialog.geometry("400x300")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product[1]}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        info_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(info_frame, text=f"Current Stock: {product[2]} units", font=("Arial", 12), bg="white", fg="#e94560").pack(pady=10)
        
        tk.Label(dialog, text="Adjustment Type:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        adjustment_type = tk.StringVar(value="add")
        type_frame = tk.Frame(dialog, bg="#f5f5f5")
        type_frame.pack()
        tk.Radiobutton(type_frame, text="➕ Add Stock", variable=adjustment_type, value="add", bg="#f5f5f5", font=("Arial", 11)).pack(side="left", padx=10)
        tk.Radiobutton(type_frame, text="➖ Remove Stock", variable=adjustment_type, value="remove", bg="#f5f5f5", font=("Arial", 11)).pack(side="left", padx=10)
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        quantity_entry = tk.Entry(dialog, font=("Arial", 12), width=15, justify="center")
        quantity_entry.pack()
        
        tk.Label(dialog, text="Reason:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
        reason_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        reason_entry.pack()
        
        def save_adjustment():
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                    return
                reason = reason_entry.get().strip() or "Manual adjustment"
                new_stock = product[2]
                if adjustment_type.get() == "add":
                    new_stock += quantity
                    change_text = f"+{quantity}"
                else:
                    if quantity > product[2]:
                        messagebox.showwarning("Invalid", f"Cannot remove more than current stock ({product[2]})!")
                        return
                    new_stock -= quantity
                    change_text = f"-{quantity}"
                
                self.execute_query("UPDATE products SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stock, product_id))
                self.execute_query("INSERT INTO ledger (transaction_type, reference_no, description, debit, credit) VALUES (?, ?, ?, ?, ?)", ("STOCK_ADJUST", f"ADJ-{product_id}", f"{reason}: {product[1]} {change_text}", 0, 0))
                messagebox.showinfo("Success", f"Stock adjusted!\n{product[1]}: {product[2]} → {new_stock}")
                dialog.destroy()
                self.load_inventory()
                self.update_status(f"✅ Stock adjusted for {product[1]}")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid number!")
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="✅ Apply Adjustment", command=save_adjustment, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    
    def delete_selected_product(self):
        """Delete selected product (with safety checks)"""
        product_id = self.get_selected_product_id()
        if not product_id:
            return
        
        sale_count = self.fetch_one("SELECT COUNT(*) FROM sale_items WHERE product_id = ?", (product_id,))
        if sale_count and sale_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This product has {sale_count[0]} sales records.")
            return
        
        purchase_count = self.fetch_one("SELECT COUNT(*) FROM purchase_items WHERE product_id = ?", (product_id,))
        if purchase_count and purchase_count[0] > 0:
            messagebox.showwarning("Cannot Delete", f"This product has {purchase_count[0]} purchase records.")
            return
        
        product = self.fetch_one("SELECT name FROM products WHERE id = ?", (product_id,))
        if not product:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete product '{product[0]}'?", icon='warning'):
            try:
                self.execute_query("DELETE FROM products WHERE id = ?", (product_id,))
                messagebox.showinfo("Success", "Product deleted successfully!")
                self.load_inventory()
                self.load_filter_options()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
    
    def show_low_stock_report(self):
        """Show low stock report dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ Low Stock Report")
        dialog.geometry("800x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="⚠️ Products Below Reorder Level", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#e94560").pack(pady=10)
        
        low_stock_products = self.fetch_all("""
            SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, p.reorder_level, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock_quantity <= p.reorder_level
            ORDER BY p.stock_quantity ASC
        """)
        
        tk.Label(dialog, text=f"Total Low Stock Products: {len(low_stock_products)}", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e74a3b").pack(pady=10)
        
        tree_frame = tk.Frame(dialog, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("ID", "Product Name", "Brand", "Category", "Current Stock", "Reorder Level", "Supplier")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("ID", width=50)
        tree.column("Product Name", width=200)
        tree.column("Brand", width=100)
        tree.column("Category", width=100)
        tree.column("Current Stock", width=100)
        tree.column("Reorder Level", width=100)
        tree.column("Supplier", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for product in low_stock_products:
            tree.insert("", "end", values=(product[0], product[1], product[2] or "-", product[3] or "-", product[4], product[5], product[6] or "-"))
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        
        def export_report():
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Product Name', 'Brand', 'Category', 'Current Stock', 'Reorder Level', 'Supplier'])
                    for p in low_stock_products:
                        writer.writerow(p)
                messagebox.showinfo("Success", f"Report exported to {file_path}")
        
        tk.Button(btn_frame, text="📥 Export Report", command=export_report, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
    def show_shopping_list_window(self):
        """Show modern profile card style shopping list - One big card"""
        
        # Get LOW STOCK products
        low_stock = self.fetch_all("""
            SELECT id, name, brand, stock_quantity, reorder_level, 
                   (reorder_level - stock_quantity) as needed,
                   price, cost_price
            FROM products 
            WHERE stock_quantity <= reorder_level 
            AND stock_quantity > 0
            ORDER BY (reorder_level - stock_quantity) DESC
            LIMIT 15
        """)
        
        # Get OUT OF STOCK products
        out_of_stock = self.fetch_all("""
            SELECT id, name, brand, stock_quantity, reorder_level, 
                   reorder_level as needed,
                   price, cost_price
            FROM products 
            WHERE stock_quantity = 0
            ORDER BY name
            LIMIT 10
        """)
        
        if not low_stock and not out_of_stock:
            messagebox.showinfo("✅ All Good!", "All products have sufficient stock!")
            return
        
        # Create main window - Size adjusted for one card view
        window = tk.Toplevel(self.root)
        window.title("Shopping List - Faizan Paper Mart")
        window.configure(bg="#f0f4f8")
        window.attributes('-topmost', True)
        
        # Calculate window size based on content
        total_items = len(out_of_stock) + len(low_stock)
        window_height = min(750, 400 + (total_items * 45))
        window.geometry(f"520x{window_height}")
        
        # ===== MAIN CARD (Like Profile Card) =====
        main_card = tk.Frame(window, bg="white", relief="flat", bd=0)
        main_card.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Card shadow effect (using border)
        main_card.configure(highlightbackground="#e0e0e0", highlightthickness=1)
        
        # ===== HEADER SECTION (Profile Card Style) =====
        header_section = tk.Frame(main_card, bg="#1a1a2e", height=130)
        header_section.pack(fill="x")
        header_section.pack_propagate(False)
        
        # Decorative top bar
        top_decor = tk.Frame(header_section, bg="#e94560", height=4)
        top_decor.pack(fill="x")
        
        # Avatar/Icon Circle
        avatar_frame = tk.Frame(header_section, bg="#1a1a2e")
        avatar_frame.pack(pady=(15, 5))
        
        avatar_circle = tk.Frame(avatar_frame, bg="#e94560", width=50, height=50, relief="flat")
        avatar_circle.pack()
        avatar_circle.pack_propagate(False)
        
        tk.Label(avatar_circle, text="🛒", font=("Segoe UI", 28), bg="#e94560", fg="white").pack(expand=True)
        
        # Title
        tk.Label(header_section, text="PURCHASE REQUISITION", 
                font=("Segoe UI", 16, "bold"), bg="#1a1a2e", fg="white").pack()
        
        tk.Label(header_section, text=datetime.now().strftime("%A, %d %B %Y"), 
                font=("Segoe UI", 9), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # ===== SHOP INFO (Inside Card) =====
        shop_info = tk.Frame(main_card, bg="#f8f9fa", padx=20, pady=10)
        shop_info.pack(fill="x")
        
        tk.Label(shop_info, text="🏪 Faizan Paper Mart", 
                font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#1a1a2e").pack()
        tk.Label(shop_info, text="Rail Bazar Sargodha", 
                font=("Segoe UI", 9), bg="#f8f9fa", fg="#6c757d").pack()
        
        # ===== STATS BADGES (3-in-a-row) =====
        stats_frame = tk.Frame(main_card, bg="white", padx=15, pady=12)
        stats_frame.pack(fill="x")
        
        # Out of Stock Badge
        oos_frame = tk.Frame(stats_frame, bg="#dc2626", padx=12, pady=6)
        oos_frame.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(oos_frame, text=f"🔴 {len(out_of_stock)}", 
                font=("Segoe UI", 14, "bold"), bg="#dc2626", fg="white").pack()
        tk.Label(oos_frame, text="Out of Stock", 
                font=("Segoe UI", 8), bg="#dc2626", fg="#fecaca").pack()
        
        # Low Stock Badge
        low_frame = tk.Frame(stats_frame, bg="#f59e0b", padx=12, pady=6)
        low_frame.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(low_frame, text=f"🟡 {len(low_stock)}", 
                font=("Segoe UI", 14, "bold"), bg="#f59e0b", fg="white").pack()
        tk.Label(low_frame, text="Low Stock", 
                font=("Segoe UI", 8), bg="#f59e0b", fg="#fef3c7").pack()
        
        # Total Items Badge
        total_frame = tk.Frame(stats_frame, bg="#3b82f6", padx=12, pady=6)
        total_frame.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(total_frame, text=f"📦 {len(out_of_stock)+len(low_stock)}", 
                font=("Segoe UI", 14, "bold"), bg="#3b82f6", fg="white").pack()
        tk.Label(total_frame, text="Total Items", 
                font=("Segoe UI", 8), bg="#3b82f6", fg="#dbeafe").pack()
        
        # ===== ITEMS LIST (Scrollable if needed) =====
        list_label = tk.Label(main_card, text="📋 ITEMS REQUIRED", 
                              font=("Segoe UI", 11, "bold"), bg="white", fg="#1a1a2e")
        list_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Create frame for scrollable list
        list_container = tk.Frame(main_card, bg="white")
        list_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        total_cost = 0
        
        # Section: Out of Stock (Red theme)
        if out_of_stock:
            section_header = tk.Frame(scrollable_frame, bg="#fef2f2", padx=10, pady=5)
            section_header.pack(fill="x", pady=(5, 5))
            tk.Label(section_header, text="🔴 CRITICAL - OUT OF STOCK", 
                    font=("Segoe UI", 9, "bold"), bg="#fef2f2", fg="#dc2626").pack()
            
            for product in out_of_stock:
                item_frame = self.create_compact_item_row(scrollable_frame, product, is_critical=True)
                item_frame.pack(fill="x", pady=2)
                total_cost += product[6] * product[5]
        
        # Section: Low Stock (Orange theme)
        if low_stock:
            section_header = tk.Frame(scrollable_frame, bg="#fffbeb", padx=10, pady=5)
            section_header.pack(fill="x", pady=(5, 5))
            tk.Label(section_header, text="🟡 LOW STOCK - NEED REORDER", 
                    font=("Segoe UI", 9, "bold"), bg="#fffbeb", fg="#f59e0b").pack()
            
            for product in low_stock:
                item_frame = self.create_compact_item_row(scrollable_frame, product, is_critical=False)
                item_frame.pack(fill="x", pady=2)
                total_cost += product[6] * product[5]
        
        # ===== FOOTER WITH TOTAL =====
        footer = tk.Frame(main_card, bg="#f8f9fa", padx=20, pady=12)
        footer.pack(fill="x", side="bottom")
        
        # Separator
        sep = tk.Frame(footer, bg="#dee2e6", height=1)
        sep.pack(fill="x", pady=(0, 10))
        
        # Total Row
        total_row = tk.Frame(footer, bg="#f8f9fa")
        total_row.pack()
        
        tk.Label(total_row, text="ESTIMATED BUDGET", 
                font=("Segoe UI", 10), bg="#f8f9fa", fg="#6c757d").pack(side="left", padx=10)
        tk.Label(total_row, text=f"Rs. {total_cost:,.0f}", 
                font=("Segoe UI", 18, "bold"), bg="#f8f9fa", fg="#10b981").pack(side="left")
        
        # Action Buttons
        btn_row = tk.Frame(footer, bg="#f8f9fa")
        btn_row.pack(pady=(10, 0))
        
        photo_btn = tk.Button(btn_row, text="📸 TAKE PHOTO", 
                 command=lambda: messagebox.showinfo("📸 Ready", 
                     "Position your phone camera and take a clear photo!\n\nShare with purchasing team via WhatsApp."),
                 bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), 
                 padx=20, pady=6, relief="flat", cursor="hand2")
        photo_btn.pack(side="left", padx=5)
        
        close_btn = tk.Button(btn_row, text="CLOSE", 
                 command=window.destroy,
                 bg="#6c757d", fg="white", font=("Segoe UI", 10, "bold"), 
                 padx=20, pady=6, relief="flat", cursor="hand2")
        close_btn.pack(side="left", padx=5)
        
        # Instruction
        tk.Label(footer, text="📱 Point phone at this window → Take photo → Share on WhatsApp", 
                font=("Segoe UI", 8), bg="#f8f9fa", fg="#6c757d").pack(pady=(8, 0))
    
    def create_compact_item_row(self, parent, product, is_critical=False):
        """Create compact row for each product"""
        
        name = product[1]
        brand = product[2] or ""
        current = product[3]
        needed = product[5]
        price = product[6]
        
        if is_critical:
            bg_color = "#fef2f2"
            qty_bg = "#dc2626"
        else:
            bg_color = "#fffbeb"
            qty_bg = "#f59e0b"
        
        row = tk.Frame(parent, bg=bg_color, padx=10, pady=6)
        
        # Product name
        name_text = name[:25] + "..." if len(name) > 25 else name
        if brand:
            name_text = f"{name_text} ({brand[:10]})"
        
        tk.Label(row, text=name_text, font=("Segoe UI", 9), 
                bg=bg_color, fg="#1a1a2e", width=20, anchor="w").pack(side="left")
        
        # Stock info
        stock_text = f"Stock: {current}"
        tk.Label(row, text=stock_text, font=("Segoe UI", 8), 
                bg=bg_color, fg="#6c757d", width=10).pack(side="left")
        
        # Needed quantity badge
        qty_badge = tk.Frame(row, bg=qty_bg, padx=6, pady=2)
        qty_badge.pack(side="left", padx=5)
        tk.Label(qty_badge, text=f"Need: {needed}", 
                font=("Segoe UI", 8, "bold"), bg=qty_bg, fg="white").pack()
        
        # Price and total
        total = needed * price
        tk.Label(row, text=f"Rs.{total:,.0f}", font=("Segoe UI", 9, "bold"), 
                bg=bg_color, fg="#10b981", width=10, anchor="e").pack(side="right")
        
        return row
    def export_inventory_to_csv(self):
        """Export inventory to CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Inventory Export")
            if not file_path:
                return
            
            products = self.fetch_all("""
                SELECT p.id, p.name, p.brand, p.category, p.stock_quantity, p.reorder_level,
                       p.price, p.cost_price, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.name
            """)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Product Name', 'Brand', 'Category', 'Stock Quantity', 'Reorder Level', 'Selling Price (Rs.)', 'Cost Price (Rs.)', 'Supplier'])
                writer.writerows(products)
            
            messagebox.showinfo("Export Successful", f"Inventory exported to:\n{file_path}")
            self.update_status(f"📥 Exported {len(products)} products to CSV")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    # ========== PLACEHOLDER METHODS FOR OTHER PHASES ==========
    
        # ========== PHASE 6: POS SALES SYSTEM ==========
    
    def show_sales(self):
        """Show POS sales interface"""
        # Auto fix before showing sales
        self.auto_fix_old_products_for_sale()
        self.clear_main_content()
        
        # Main container with two columns
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True)
        
        # Left side - Products and Cart
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right side - Sale Form
        right_frame = tk.Frame(main_container, bg="#f5f5f5", width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # ===== LEFT SIDE =====
        # Search Product Frame
        search_frame = tk.Frame(left_frame, bg="white", relief="ridge", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Search Product:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.sale_search_var = tk.StringVar()
        self.sale_search_var.trace('w', lambda *args: self.search_sale_products())
        tk.Entry(search_frame, textvariable=self.sale_search_var, font=("Arial", 11), width=30).pack(side="left", padx=10, pady=8)
        
        # Products List Frame
        products_frame = tk.LabelFrame(left_frame, text="Available Products", font=("Arial", 12, "bold"), bg="#f5f5f5")
        products_frame.pack(fill="both", expand=True)
        
        # Products Treeview
        product_columns = ("ID", "Name", "Brand", "Stock", "Price")
        self.sale_products_tree = ttk.Treeview(products_frame, columns=product_columns, show="headings", height=12)
        
        self.sale_products_tree.heading("ID", text="ID")
        self.sale_products_tree.heading("Name", text="Product Name")
        self.sale_products_tree.heading("Brand", text="Brand")
        self.sale_products_tree.heading("Stock", text="Stock")
        self.sale_products_tree.heading("Price", text="Price (Rs.)")
        
        self.sale_products_tree.column("ID", width=50)
        self.sale_products_tree.column("Name", width=200)
        self.sale_products_tree.column("Brand", width=100)
        self.sale_products_tree.column("Stock", width=80)
        self.sale_products_tree.column("Price", width=100)
        
        vsb = ttk.Scrollbar(products_frame, orient="vertical", command=self.sale_products_tree.yview)
        self.sale_products_tree.configure(yscrollcommand=vsb.set)
        
        self.sale_products_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Cart Frame
        cart_frame = tk.LabelFrame(left_frame, text="Sale Cart", font=("Arial", 12, "bold"), bg="#f5f5f5")
        cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Cart Treeview
        cart_columns = ("ID", "Product", "Quantity", "Price", "Total")
        self.sale_cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=6)
        
        self.sale_cart_tree.heading("ID", text="#")
        self.sale_cart_tree.heading("Product", text="Product Name")
        self.sale_cart_tree.heading("Quantity", text="Quantity")
        self.sale_cart_tree.heading("Price", text="Price (Rs.)")
        self.sale_cart_tree.heading("Total", text="Total (Rs.)")
        
        self.sale_cart_tree.column("ID", width=40)
        self.sale_cart_tree.column("Product", width=200)
        self.sale_cart_tree.column("Quantity", width=80)
        self.sale_cart_tree.column("Price", width=100)
        self.sale_cart_tree.column("Total", width=100)
        
        cart_vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.sale_cart_tree.yview)
        self.sale_cart_tree.configure(yscrollcommand=cart_vsb.set)
        
        self.sale_cart_tree.pack(side="left", fill="both", expand=True)
        cart_vsb.pack(side="right", fill="y")
        
        # Cart Buttons
        cart_btn_frame = tk.Frame(cart_frame, bg="#f5f5f5")
        cart_btn_frame.pack(fill="x", pady=5)
        
        tk.Button(cart_btn_frame, text="🗑️ Remove Selected", command=self.remove_from_sale_cart, bg="#e74a3b", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        tk.Button(cart_btn_frame, text="🔄 Clear Cart", command=self.clear_sale_cart, bg="#f6c23e", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        
        # ===== RIGHT SIDE =====
        # Sale Form
        form_frame = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(form_frame, text="💰 Sale Details", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        # Customer Name
        tk.Label(form_frame, text="Customer Name", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        self.customer_name_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.customer_name_entry.pack(padx=20, pady=5)
        self.customer_name_entry.insert(0, "")
        
        # Payment Method
        tk.Label(form_frame, text="Payment Method", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        self.payment_method_var = tk.StringVar(value="Cash")
        payment_frame = tk.Frame(form_frame, bg="white")
        payment_frame.pack(padx=20, pady=5)
        tk.Radiobutton(payment_frame, text="Cash", variable=self.payment_method_var, value="Cash", bg="white", font=("Arial", 10)).pack(side="left", padx=10)
        tk.Radiobutton(payment_frame, text="Card", variable=self.payment_method_var, value="Card", bg="white", font=("Arial", 10)).pack(side="left", padx=10)
        tk.Radiobutton(payment_frame, text="Online", variable=self.payment_method_var, value="Online", bg="white", font=("Arial", 10)).pack(side="left", padx=10)
        
        # Total Amount
        total_frame = tk.Frame(form_frame, bg="white")
        total_frame.pack(fill="x", pady=20)
        
        tk.Label(total_frame, text="Total Amount:", font=("Arial", 14, "bold"), bg="white", fg="#e94560").pack(side="left", padx=20)
        self.sale_total_label = tk.Label(total_frame, text="Rs. 0.00", font=("Arial", 16, "bold"), bg="white", fg="#e94560")
        self.sale_total_label.pack(side="right", padx=20)
        
        # Action Buttons
        action_frame = tk.Frame(form_frame, bg="white")
        action_frame.pack(fill="x", pady=10)
        
        tk.Button(action_frame, text="➕ Add to Cart", command=self.open_sale_quantity_dialog, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=10)
        tk.Button(action_frame, text="✅ Complete Sale", command=self.complete_sale, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="right", expand=True, padx=10)
        
        # Print button
        tk.Button(form_frame, text="🖨️ Print Invoice", command=self.print_invoice, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(pady=5)
        
        # Double click to add to cart
        self.sale_products_tree.bind("<Double-1>", lambda e: self.open_sale_quantity_dialog())
        
        # Initialize variables
        self.sale_cart = []
        self.current_sale_id = None
        
        # Load products
        self.load_sale_products()
    
    def load_sale_products(self, search_term=""):
        """Load products for sale selection"""
        for item in self.sale_products_tree.get_children():
            self.sale_products_tree.delete(item)
        
        try:
            if search_term:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE (name LIKE ? OR brand LIKE ?) AND stock_quantity > 0 ORDER BY id DESC"
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE stock_quantity > 0 ORDER BY id DESC"
                params = ()
            
            products = self.fetch_all(query, params)
            
            for product in products:
                self.sale_products_tree.insert("", "end", values=(
                    product[0],
                    product[1],
                    product[2] or "-",
                    product[3],
                    f"Rs. {product[4]:.2f}"
                ))
            
            self.update_status(f"Loaded {len(products)} products available for sale")
        except Exception as e:
            self.update_status(f"Error loading products: {str(e)}")
    
    def search_sale_products(self):
        """Search products for sale"""
        search_term = self.sale_search_var.get()
        self.load_sale_products(search_term)
    
    def open_sale_quantity_dialog(self):
        """Open dialog with Pack/Piece selection and scrollbar"""
        selected = self.sale_products_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return
        
        item = self.sale_products_tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        current_stock = item['values'][3]
        piece_price = float(item['values'][4].replace('Rs. ', ''))
        
        # Get product pack info
        product_info = self.fetch_one("SELECT unit_type, pieces_per_pack, pack_price, cost_price FROM products WHERE id = ?", (product_id,))
        unit_type = product_info[0] if product_info else "Piece"
        pieces_per_pack = product_info[1] if product_info else 1
        pack_price = product_info[2] if product_info else 0
        cost_price = product_info[3] if product_info else 0
        
        # Calculate piece price from pack price
        if pack_price > 0 and pieces_per_pack > 0:
            piece_price = pack_price / pieces_per_pack
        
        if current_stock <= 0:
            messagebox.showwarning("Out of Stock", f"{product_name} is out of stock!")
            return
        
        # Main dialog with both scrollbars
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add to Cart - {product_name}")
        dialog.geometry("600x650")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product_name}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with both scrollbars
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        def on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stock info
        info_frame = tk.Frame(content, bg="#f5f5f5")
        info_frame.pack(fill="x", pady=5)
        
        # Calculate packs display
        stock_packs = current_stock // pieces_per_pack if pieces_per_pack > 0 else current_stock
        stock_pieces = current_stock % pieces_per_pack if pieces_per_pack > 0 else 0
        
        tk.Label(info_frame, text=f"Available Stock: {stock_packs} packs + {stock_pieces} pieces ({current_stock} total pieces)", 
                font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack()
        if unit_type == "Pack":
            tk.Label(info_frame, text=f"({pieces_per_pack} pieces per pack)", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Purchase Type
        type_frame = tk.LabelFrame(content, text="Purchase Type", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#1a1a2e")
        type_frame.pack(fill="x", pady=10)
        
        type_inner = tk.Frame(type_frame, bg="#f5f5f5")
        type_inner.pack(padx=15, pady=10)
        
        # DEFAULT: Pack is selected
        self.buy_type = tk.StringVar(value="Pack")
        
        piece_radio = tk.Radiobutton(type_inner, text=f"Buy by Piece (Rs. {piece_price:.2f} each)", 
                                      variable=self.buy_type, value="Piece", bg="#f5f5f5", font=("Arial", 10))
        piece_radio.pack(anchor="w", pady=5)
        
        pack_radio_frame = tk.Frame(type_inner, bg="#f5f5f5")
        pack_radio_frame.pack(anchor="w", pady=5)
        
        pack_radio = tk.Radiobutton(pack_radio_frame, text=f"Buy by Pack (Rs. {pack_price:.2f} per pack - {pieces_per_pack} pieces)", 
                                      variable=self.buy_type, value="Pack", bg="#f5f5f5", font=("Arial", 10))
        pack_radio.pack(side="left")
        
        if pack_price <= 0:
            pack_radio.config(state="disabled")
            tk.Label(pack_radio_frame, text=" (Not available)", font=("Arial", 9), bg="#f5f5f5", fg="#e74a3b").pack(side="left")
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Quantity Frame
        qty_main_frame = tk.LabelFrame(content, text="Quantity", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#1a1a2e")
        qty_main_frame.pack(fill="x", pady=10)
        
        qty_inner = tk.Frame(qty_main_frame, bg="#f5f5f5")
        qty_inner.pack(padx=15, pady=10)
        
        # For Piece mode
        piece_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
        tk.Label(piece_qty_frame, text="Number of Pieces:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.piece_qty_entry = tk.Entry(piece_qty_frame, font=("Arial", 12), width=10, justify="center")
        self.piece_qty_entry.pack(side="left", padx=10)
        self.piece_qty_entry.insert(0, "1")
        
        # For Pack mode
        pack_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
        
        tk.Label(pack_qty_frame, text="Number of Packs:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.pack_qty_entry = tk.Entry(pack_qty_frame, font=("Arial", 12), width=10, justify="center")
        self.pack_qty_entry.pack(side="left", padx=10)
        self.pack_qty_entry.insert(0, "1")
        
        tk.Label(pack_qty_frame, text=f"(= {pieces_per_pack} pieces each)", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack(side="left", padx=5)
        
        # Extra pieces frame
        extra_frame = tk.Frame(pack_qty_frame, bg="#f5f5f5")
        extra_frame.pack(pady=5)
        tk.Label(extra_frame, text="Extra Pieces (beyond packs):", font=("Arial", 10), bg="#f5f5f5").pack(side="left")
        self.extra_pieces_entry = tk.Entry(extra_frame, font=("Arial", 11), width=8, justify="center")
        self.extra_pieces_entry.pack(side="left", padx=10)
        self.extra_pieces_entry.insert(0, "0")
        
        # Initially show pack mode (DEFAULT)
        piece_qty_frame.pack_forget()
        pack_qty_frame.pack()
        
        # Total pieces display
        total_pieces_frame = tk.Frame(qty_inner, bg="#f5f5f5")
        total_pieces_frame.pack(pady=10)
        tk.Label(total_pieces_frame, text="Total Pieces:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
        self.total_pieces_label = tk.Label(total_pieces_frame, text=str(pieces_per_pack), font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
        self.total_pieces_label.pack(side="left", padx=10)
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Custom Price Option
        custom_frame = tk.LabelFrame(content, text="Price Option", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#1a1a2e")
        custom_frame.pack(fill="x", pady=10)
        
        custom_inner = tk.Frame(custom_frame, bg="#f5f5f5")
        custom_inner.pack(padx=15, pady=10)
        
        self.custom_price_var = tk.StringVar(value="default")
        default_radio = tk.Radiobutton(custom_inner, text=f"Default Price (Rs. {piece_price:.2f} per piece)", 
                                        variable=self.custom_price_var, value="default", bg="#f5f5f5", font=("Arial", 10))
        default_radio.pack(anchor="w", pady=3)
        
        custom_radio = tk.Radiobutton(custom_inner, text="Custom Price:", 
                                      variable=self.custom_price_var, value="custom", bg="#f5f5f5", font=("Arial", 10))
        custom_radio.pack(anchor="w", pady=3)
        
        custom_price_row = tk.Frame(custom_inner, bg="#f5f5f5")
        custom_price_row.pack(anchor="w", padx=20)
        tk.Label(custom_price_row, text="Rs.", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.custom_price_entry = tk.Entry(custom_price_row, font=("Arial", 11), width=12)
        self.custom_price_entry.pack(side="left", padx=5)
        self.custom_price_entry.insert(0, str(piece_price))
        self.custom_price_entry.config(state="disabled")
        
        # Loss warning
        self.loss_warning_label = tk.Label(custom_inner, text="", font=("Arial", 9), bg="#f5f5f5", fg="#e74a3b")
        self.loss_warning_label.pack(anchor="w", pady=5)
        
        # Total preview
        preview_frame = tk.Frame(content, bg="#f0f0f0", relief="ridge", bd=1)
        preview_frame.pack(fill="x", pady=10)
        
        tk.Label(preview_frame, text="💰 TOTAL AMOUNT:", font=("Arial", 13, "bold"), bg="#f0f0f0", fg="#e94560").pack(side="left", padx=15, pady=10)
        self.sale_preview_total = tk.Label(preview_frame, text="Rs. 0.00", font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#e94560")
        self.sale_preview_total.pack(side="right", padx=15, pady=10)
        
        # Profit/Loss preview
        self.pl_preview_label = tk.Label(content, text="", font=("Arial", 10), bg="#f5f5f5")
        self.pl_preview_label.pack(pady=5)
        
        # Helper functions
        def update_total_pieces(*args):
            try:
                if self.buy_type.get() == "Piece":
                    pieces = int(self.piece_qty_entry.get() or 0)
                    self.total_pieces_label.config(text=str(pieces))
                else:
                    packs = int(self.pack_qty_entry.get() or 0)
                    extra = int(self.extra_pieces_entry.get() or 0)
                    pieces = (packs * pieces_per_pack) + extra
                    self.total_pieces_label.config(text=str(pieces))
                update_preview()
            except:
                self.total_pieces_label.config(text="0")
                update_preview()
        
        def update_preview(*args):
            try:
                if self.buy_type.get() == "Piece":
                    qty = int(self.piece_qty_entry.get() or 0)
                else:
                    packs = int(self.pack_qty_entry.get() or 0)
                    extra = int(self.extra_pieces_entry.get() or 0)
                    qty = (packs * pieces_per_pack) + extra
                
                if self.custom_price_var.get() == "custom":
                    try:
                        price_per_piece = float(self.custom_price_entry.get())
                    except:
                        price_per_piece = piece_price
                else:
                    price_per_piece = piece_price
                
                total = qty * price_per_piece
                
                if self.buy_type.get() == "Pack" and qty > 0:
                    packs = qty // pieces_per_pack
                    remaining = qty % pieces_per_pack
                    self.sale_preview_total.config(text=f"Rs. {total:,.2f} ({packs} pack + {remaining} pcs)")
                else:
                    self.sale_preview_total.config(text=f"Rs. {total:,.2f}")
                
                if qty > 0:
                    if price_per_piece < cost_price:
                        loss_amount = (cost_price - price_per_piece) * qty
                        self.pl_preview_label.config(text=f"⚠️ LOSS: Rs. {loss_amount:,.2f}", fg="#e74a3b")
                    else:
                        profit_amount = (price_per_piece - cost_price) * qty
                        self.pl_preview_label.config(text=f"✓ PROFIT: Rs. {profit_amount:,.2f}", fg="#1cc88a")
                else:
                    self.pl_preview_label.config(text="")
            except:
                self.sale_preview_total.config(text="Rs. 0.00")
        
        def check_for_loss():
            try:
                if self.custom_price_var.get() == "custom":
                    custom_price = float(self.custom_price_entry.get())
                    if custom_price < cost_price:
                        loss_amount = cost_price - custom_price
                        self.loss_warning_label.config(
                            text=f"⚠️ WARNING: Loss of Rs. {loss_amount:.2f} per piece!",
                            fg="#e74a3b"
                        )
                    else:
                        self.loss_warning_label.config(text="")
                else:
                    self.loss_warning_label.config(text="")
            except:
                self.loss_warning_label.config(text="")
        
        def on_buy_type_change(*args):
            if self.buy_type.get() == "Piece":
                piece_qty_frame.pack()
                pack_qty_frame.pack_forget()
                self.piece_qty_entry.delete(0, tk.END)
                self.piece_qty_entry.insert(0, "1")
            else:
                piece_qty_frame.pack_forget()
                pack_qty_frame.pack()
                self.pack_qty_entry.delete(0, tk.END)
                self.pack_qty_entry.insert(0, "1")
                self.extra_pieces_entry.delete(0, tk.END)
                self.extra_pieces_entry.insert(0, "0")
            update_total_pieces()
        
        def on_custom_price_change(*args):
            if self.custom_price_var.get() == "custom":
                self.custom_price_entry.config(state="normal")
                self.custom_price_entry.focus()
                check_for_loss()
            else:
                self.custom_price_entry.config(state="disabled")
                self.custom_price_entry.delete(0, tk.END)
                self.custom_price_entry.insert(0, str(piece_price))
                self.loss_warning_label.config(text="")
            update_preview()
        
        # Bind events
        self.buy_type.trace('w', on_buy_type_change)
        self.custom_price_var.trace('w', on_custom_price_change)
        self.piece_qty_entry.bind("<KeyRelease>", update_total_pieces)
        self.pack_qty_entry.bind("<KeyRelease>", update_total_pieces)
        self.extra_pieces_entry.bind("<KeyRelease>", update_total_pieces)
        self.custom_price_entry.bind("<KeyRelease>", lambda e: [check_for_loss(), update_preview()])
        
        def add_to_cart():
            try:
                if self.buy_type.get() == "Piece":
                    qty = int(self.piece_qty_entry.get() or 0)
                else:
                    packs = int(self.pack_qty_entry.get() or 0)
                    extra = int(self.extra_pieces_entry.get() or 0)
                    qty = (packs * pieces_per_pack) + extra
                
                if qty <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                    return
                if qty > current_stock:
                    messagebox.showwarning("Insufficient Stock", f"Only {current_stock} pieces available!\nYou entered {qty} pieces.")
                    return
                
                if self.custom_price_var.get() == "custom":
                    try:
                        final_price_per_piece = float(self.custom_price_entry.get())
                        if final_price_per_piece <= 0:
                            messagebox.showwarning("Invalid Price", "Price must be greater than 0!")
                            return
                    except:
                        messagebox.showwarning("Invalid Price", "Please enter a valid price!")
                        return
                    
                    if final_price_per_piece < cost_price:
                        loss_amount = (cost_price - final_price_per_piece) * qty
                        confirm = messagebox.askyesno(
                            "⚠️ LOSS WARNING ⚠️",
                            f"Product: {product_name}\n"
                            f"Cost Price: Rs. {cost_price:.2f}\n"
                            f"Your Price: Rs. {final_price_per_piece:.2f}\n"
                            f"Quantity: {qty} pieces\n\n"
                            f"This will result in a LOSS of Rs. {loss_amount:,.2f}!\n\n"
                            f"Are you sure you want to continue?",
                            icon='warning'
                        )
                        if not confirm:
                            return
                else:
                    final_price_per_piece = piece_price
                
                total = qty * final_price_per_piece
                
                if self.buy_type.get() == "Pack":
                    packs_sold = int(self.pack_qty_entry.get() or 0)
                    extra_sold = int(self.extra_pieces_entry.get() or 0)
                    sale_note = f" ({packs_sold} pack + {extra_sold} pcs)"
                else:
                    sale_note = ""
                
                cart_item = {
                    'product_id': product_id,
                    'name': product_name + sale_note,
                    'quantity': qty,
                    'price': final_price_per_piece,
                    'total': total,
                    'is_custom_price': self.custom_price_var.get() == "custom",
                    'cost_price': cost_price,
                    'pieces': qty,
                    'buy_type': self.buy_type.get()
                }
                self.sale_cart.append(cart_item)
                self.update_sale_cart_display()
                self.update_sale_total()
                dialog.destroy()
                
                if cart_item['is_custom_price']:
                    if final_price_per_piece < cost_price:
                        self.update_status(f"⚠️ Added {qty} pieces of {product_name} at LOSS")
                    else:
                        self.update_status(f"Added {qty} pieces of {product_name} at custom price")
                else:
                    self.update_status(f"Added {qty} pieces of {product_name} to cart")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter valid numbers!")
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#f5f5f5")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="✅ ADD TO CART", command=add_to_cart, bg="#1cc88a", fg="white", font=("Arial", 12, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 12, "bold"), padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", padx=10)
        
        update_total_pieces()
    
    def update_sale_cart_display(self):
        """Update sale cart treeview display with loss indicator"""
        for item in self.sale_cart_tree.get_children():
            self.sale_cart_tree.delete(item)
        
        for i, item in enumerate(self.sale_cart, 1):
            # Show indicator for custom price items
            price_display = f"Rs. {item['price']:.2f}"
            if item.get('is_custom_price'):
                if item.get('price') < item.get('cost_price', 0):
                    price_display = f"⚠️ Rs. {item['price']:.2f}"  # Loss indicator
                else:
                    price_display = f"*Rs. {item['price']:.2f}"    # Custom price indicator
            
            self.sale_cart_tree.insert("", "end", values=(
                i,
                item['name'],
                item['quantity'],
                price_display,
                f"Rs. {item['total']:.2f}"
            ))
    
    def update_sale_total(self):
        """Update total amount display"""
        total = sum(item['total'] for item in self.sale_cart)
        self.sale_total_label.config(text=f"Rs. {total:,.2f}")
    
    def remove_from_sale_cart(self):
        """Remove selected item from sale cart"""
        selected = self.sale_cart_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an item to remove!")
            return
        
        item = self.sale_cart_tree.item(selected[0])
        index = int(item['values'][0]) - 1
        
        if 0 <= index < len(self.sale_cart):
            removed = self.sale_cart.pop(index)
            self.update_sale_cart_display()
            self.update_sale_total()
            self.update_status(f"Removed {removed['name']} from cart")
    
    def clear_sale_cart(self):
        """Clear all items from sale cart"""
        if self.sale_cart and messagebox.askyesno("Clear Cart", "Clear the entire cart?"):
            self.sale_cart.clear()
            self.update_sale_cart_display()
            self.update_sale_total()
            self.update_status("Cart cleared")
    
    def complete_sale(self):
        """Complete the sale and update stock"""
        if not self.sale_cart:
            messagebox.showwarning("Empty Cart", "Please add items to the cart first!")
            return
        
        customer_name = self.customer_name_entry.get().strip()
        if not customer_name:
            customer_name = "N/A"
        
        payment_method = self.payment_method_var.get()
        total_amount = sum(item['total'] for item in self.sale_cart)
        
        # Generate invoice number
        last_invoice = self.fetch_one("SELECT invoice_no FROM sales ORDER BY id DESC LIMIT 1")
        if last_invoice and last_invoice[0]:
            num = int(last_invoice[0].split('-')[-1]) + 1
            invoice_no = f"INV-{datetime.now().year}-{num:03d}"
        else:
            invoice_no = f"INV-{datetime.now().year}-001"
        
        confirm = messagebox.askyesno(
            "Confirm Sale",
            f"Invoice: {invoice_no}\nCustomer: {customer_name}\nItems: {len(self.sale_cart)}\nTotal: Rs. {total_amount:,.2f}\n\nProceed with sale?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert sale record
            cursor.execute(
                "INSERT INTO sales (invoice_no, customer_name, total_amount, payment_method) VALUES (?, ?, ?, ?)",
                (invoice_no, customer_name, total_amount, payment_method)
            )
            sale_id = cursor.lastrowid
            self.current_sale_id = sale_id
            
            # Insert sale items and update stock
            for item in self.sale_cart:
                # Get cost price for profit calculation
                product = self.fetch_one("SELECT cost_price FROM products WHERE id = ?", (item['product_id'],))
                cost_price = product[0] if product else 0
                profit = item['total'] - (item['quantity'] * cost_price)
                
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, product_id, quantity, price, total, cost_price, profit) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (sale_id, item['product_id'], item['quantity'], item['price'], item['total'], cost_price, profit)
                )
                
                # Update stock
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (item['quantity'], item['product_id'])
                )
            
            # Add to ledger
            cursor.execute(
                "INSERT INTO ledger (transaction_type, reference_no, description, debit, credit) VALUES (?, ?, ?, ?, ?)",
                ("SALE", invoice_no, f"Sale to {customer_name}", 0, total_amount)
            )
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Sale completed successfully!\nInvoice: {invoice_no}\nTotal: Rs. {total_amount:,.2f}")
            
            # Print invoice
                        # Generate and print HTML receipt
            html_receipt = self.generate_html_receipt(invoice_no, customer_name, total_amount, payment_method, self.sale_cart)
            self.print_html_receipt(html_receipt)
            
            # Save HTML receipt to file
            invoices_dir = "invoices"
            if not os.path.exists(invoices_dir):
                os.makedirs(invoices_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{invoices_dir}/sale_{invoice_no}_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_receipt)
            
            # Reset form
            self.sale_cart.clear()
            self.update_sale_cart_display()
            self.update_sale_total()
            self.customer_name_entry.delete(0, tk.END)
            self.customer_name_entry.insert(0, "Walk-in Customer")
            self.payment_method_var.set("Cash")
            self.load_sale_products()
            
            self.update_status(f"✅ Sale completed: {invoice_no} for Rs. {total_amount:,.2f}")
            self.force_refresh_dashboard()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete sale: {str(e)}")
    def generate_invoice_text(self, invoice_no, customer_name, total_amount, payment_method):
        """Generate formatted invoice text for 58mm thermal printer (max 32 chars per line)"""
        now = datetime.now()
        
        # Get sale items
        sale_items = self.fetch_all("""
            SELECT si.quantity, si.price, si.total, p.name
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (self.current_sale_id,))
        
        lines = []
        
        # Header (centered, max 32 chars)
        lines.append("=" * 32)
        lines.append("     FAIZAN PAPER MART")
        lines.append("     ================")
        lines.append("     Rail Bazar Sargodha")
        lines.append("     Ph: 0300-8706085")
        lines.append("=" * 32)
        lines.append("")
        
        # Invoice details
        lines.append(f"Invoice: {invoice_no}")
        lines.append(f"Date: {now.strftime('%d-%m-%Y %H:%M')}")
        lines.append(f"Customer: {self.shorten_text(customer_name, 25)}")
        lines.append(f"Payment: {payment_method}")
        lines.append("")
        
        # Items header
        lines.append("-" * 32)
        lines.append(f"{'#':<2} {'Item':<14} {'Qty':>3} {'Price':>6} {'Total':>5}")
        lines.append("-" * 32)
        
        # Items
        serial = 1
        for item in sale_items:
            name = self.shorten_text(item[3], 12)
            qty = item[0]
            price = item[1]
            total = item[2]
            lines.append(f"{serial:<2} {name:<14} {qty:>3} {price:>6.0f} {total:>5.0f}")
            serial += 1
        
        lines.append("-" * 32)
        
        # Total
        lines.append(f"{'Total':>25} Rs.{total_amount:>6.0f}")
        lines.append("=" * 32)
        lines.append("")
        lines.append("    Thank you for shopping!")
        lines.append("         Visit Again!")
        lines.append("")
        lines.append("=" * 32)
        
        return "\n".join(lines)
    
    def print_invoice_after_sale(self, invoice_no, customer_name, total_amount, payment_method):
        """Professional Sale Receipt"""
        now = datetime.now()
        
        lines = []
        width = 36
        
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "FAIZAN PAPER MART" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("Rail Bazar") - 2) // 2) + "Rail Bazar" + " " * ((width - len("Rail Bazar") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("0300-8706085") - 2) // 2) + "0300-8706085" + " " * ((width - len("0300-8706085") - 2) // 2) + "|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Slip : SALE INVOICE{' ' * (width - 22)}|")
        lines.append(f"| No   : {invoice_no:<{width-10}}|")
        lines.append(f"| Date : {now.strftime('%d-%m-%Y'):<{width-10}}|")
        lines.append(f"| User : {customer_name if customer_name else 'Walk-in':<{width-10}}|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Item{' ' * 10}Qty Rate{' ' * 5}Total|")
        lines.append("+" + "-" * (width - 2) + "+")
        
        # Get sale items from database
        sale_id = self.fetch_one("SELECT id FROM sales WHERE invoice_no = ?", (invoice_no,))
        if sale_id:
            items = self.fetch_all("""
                SELECT p.name, si.quantity, si.price, si.total
                FROM sale_items si JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            """, (sale_id[0],))
            
            for item in items:
                name = item[0][:12]
                qty = item[1]
                rate = item[2]
                total_amt = item[3]
                lines.append(f"| {name:<12} {qty:>3} {rate:>5.0f} {total_amt:>8.0f}|")
        
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Total               {total_amount:>8.0f} Rs|")
        lines.append(f"| Payment             {payment_method:<8}   |")
        lines.append(f"| Status              Paid        |")
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("THANK YOU") - 2) // 2) + "THANK YOU" + " " * ((width - len("THANK YOU") - 2) // 2) + "|")
        lines.append("+" + "=" * (width - 2) + "+")
        
        receipt = "\n".join(lines)
        self._direct_print(receipt)
        
        # Save copy
        invoices_dir = "invoices"
        if not os.path.exists(invoices_dir):
            os.makedirs(invoices_dir)
        filename = f"{invoices_dir}/sale_{invoice_no}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt)
    
    def _direct_print(self, text):
        """Direct thermal printer print"""
        try:
            import tempfile
            import subprocess
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(text)
            temp_file.close()
            subprocess.run(['notepad', '/p', temp_file.name], shell=True, timeout=5)
            os.unlink(temp_file.name)
        except:
            pass
    
    def print_invoice(self):
        """Print invoice for last completed sale or current cart"""
        # First, check if there's a last sale
        last_sale = self.fetch_one("SELECT id, invoice_no, customer_name, total_amount, payment_method FROM sales ORDER BY id DESC LIMIT 1")
        
        if last_sale:
            # Print last sale invoice
            sale_id = last_sale[0]
            invoice_no = last_sale[1]
            customer_name = last_sale[2] or "N/A"
            total_amount = last_sale[3]
            payment_method = last_sale[4]
            
            # Get sale items from last sale
            sale_items = self.fetch_all("""
                SELECT si.quantity, si.price, si.total, p.name
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            """, (sale_id,))
            
            if not sale_items:
                messagebox.showwarning("No Data", "No items found in last sale!")
                return
            
            now = datetime.now()
            
            lines = []
            lines.append("=" * 32)
            lines.append("     FAIZAN PAPER MART")
            lines.append("     ================")
            lines.append("     Rail Bazar Sargodha")
            lines.append("     Ph: 0300-8706085")
            lines.append("=" * 32)
            lines.append("")
            lines.append(f"Invoice: {invoice_no}")
            lines.append(f"Date: {now.strftime('%d-%m-%Y %H:%M')}")
            lines.append(f"Customer: {self.shorten_text(customer_name, 22)}")
            lines.append(f"Payment: {payment_method}")
            lines.append("")
            lines.append("-" * 32)
            lines.append(f"{'#':<2} {'Item':<14} {'Qty':>3} {'Price':>6} {'Total':>5}")
            lines.append("-" * 32)
            
            serial = 1
            for item in sale_items:
                name = self.shorten_text(item[3], 12)
                qty = item[0]
                price = item[1]
                total = item[2]
                lines.append(f"{serial:<2} {name:<14} {qty:>3} {price:>6.0f} {total:>5.0f}")
                serial += 1
            
            lines.append("-" * 32)
            lines.append(f"{'Total':>25} Rs.{total_amount:>6.0f}")
            lines.append("=" * 32)
            lines.append("")
            lines.append("    Thank you for shopping!")
            lines.append("         Visit Again!")
            lines.append("")
            lines.append("=" * 32)
            
            invoice_text = "\n".join(lines)
            
            # Show preview
            dialog = tk.Toplevel(self.root)
            dialog.title("Invoice Preview (58mm)")
            dialog.geometry("450x600")
            dialog.configure(bg="white")
            dialog.grab_set()
            
            text_widget = tk.Text(dialog, font=("Courier", 9), wrap="none", padx=10, pady=10)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", invoice_text)
            text_widget.config(state="disabled")
            
            btn_frame = tk.Frame(dialog, bg="white")
            btn_frame.pack(pady=10)
            
            tk.Button(btn_frame, text="🖨️ Print", command=lambda: self.send_to_printer(invoice_text, dialog), 
                      bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Close", command=dialog.destroy, 
                      bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
            
        elif self.sale_cart:
            # If no last sale but cart has items, print current cart
            self.print_invoice_after_sale("TEMP", "N/A", sum(item['total'] for item in self.sale_cart), "Cash")
        else:
            messagebox.showwarning("No Invoice", "No sale found to print!\nPlease complete a sale first.")
    
    def send_to_printer(self, text, dialog=None):
        """Send text to thermal printer and save invoice"""
        try:
            # Create invoices directory if not exists
            invoices_dir = "invoices"
            if not os.path.exists(invoices_dir):
                os.makedirs(invoices_dir)
            
            # Save invoice to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{invoices_dir}/invoice_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Print
            import tempfile
            import subprocess
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(text)
            temp_file.close()
            
            subprocess.run(['notepad', '/p', temp_file.name], shell=True)
            
            messagebox.showinfo("Print & Save", f"Invoice printed and saved!\nSaved to: {filename}")
            if dialog:
                dialog.destroy()
            
            os.unlink(temp_file.name)
            
        except Exception as e:
            result = messagebox.askyesno("Print Failed", 
                f"Could not print.\n\n{str(e)}\n\nSave invoice as text file?")
            if result:
                invoices_dir = "invoices"
                if not os.path.exists(invoices_dir):
                    os.makedirs(invoices_dir)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{invoices_dir}/invoice_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("Saved", f"Invoice saved to:\n{filename}")
            if dialog:
                dialog.destroy()
    def generate_html_receipt(self, invoice_no, customer_name, total_amount, payment_method, items):
        """Generate professional HTML receipt for thermal printer - SOLID LINES ONLY"""
        
        now = datetime.now()
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Faizan Paper Mart - Invoice</title>
            <style>
                @page {{
                    size: 80mm 297mm;
                    margin: 0mm;
                    padding: 0mm;
                }}
                
                body {{
                    font-family: 'Courier New', 'Lucida Console', monospace;
                    font-size: 11px;
                    width: 80mm;
                    margin: 0;
                    padding: 2mm;
                    background: white;
                    color: black;
                }}
                
                .receipt {{
                    width: 100%;
                    margin: 0;
                    padding: 0;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 5px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid black;
                }}
                
                .shop-name {{
                    font-size: 14px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }}
                
                .shop-address {{
                    font-size: 9px;
                    margin-top: 2px;
                }}
                
                .shop-phone {{
                    font-size: 9px;
                }}
                
                .info-section {{
                    margin: 8px 0;
                    padding: 5px 0;
                    border-bottom: 1px solid black;
                }}
                
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 3px 0;
                }}
                
                .info-label {{
                    font-weight: bold;
                }}
                
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 8px 0;
                    font-size: 10px;
                }}
                
                .items-table th {{
                    border-top: 1px solid black;
                    border-bottom: 1px solid black;
                    padding: 5px 2px;
                    text-align: center;
                    font-weight: bold;
                }}
                
                .items-table td {{
                    border-bottom: 1px solid black;
                    padding: 4px 2px;
                    text-align: center;
                }}
                
                .items-table td:first-child {{
                    text-align: center;
                }}
                
                .items-table td:nth-child(2) {{
                    text-align: left;
                }}
                
                .total-section {{
                    margin-top: 10px;
                    padding-top: 8px;
                    border-top: 1px solid black;
                    text-align: right;
                }}
                
                .total-row {{
                    display: flex;
                    justify-content: flex-end;
                    margin: 3px 0;
                }}
                
                .total-amount {{
                    font-size: 13px;
                    font-weight: bold;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 12px;
                    padding-top: 8px;
                    border-top: 1px solid black;
                    font-size: 9px;
                }}
                
                .thankyou {{
                    font-size: 10px;
                    font-weight: bold;
                    margin: 5px 0;
                }}
                
                @media print {{
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="receipt">
                <!-- Header -->
                <div class="header">
                    <div class="shop-name">🏪 FAIZAN PAPER MART</div>
                    <div class="shop-address">Rail Bazar Sargodha</div>
                    <div class="shop-phone">📞 0300-8706085</div>
                </div>
                
                <!-- Invoice Info -->
                <div class="info-section">
                    <div class="info-row">
                        <span class="info-label">INVOICE:</span>
                        <span>{invoice_no}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">DATE:</span>
                        <span>{now.strftime('%d-%m-%Y %H:%M:%S')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">CUSTOMER:</span>
                        <span>{customer_name[:30]}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">PAYMENT:</span>
                        <span>{payment_method}</span>
                    </div>
                </div>
                
                <!-- Items Table -->
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>ITEM NAME</th>
                            <th>QTY</th>
                            <th>PRICE</th>
                            <th>TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add items
        serial = 1
        for item in items:
            name = item['name'][:25]
            qty = item['quantity']
            price = item['price']
            total = item['total']
            
            html_template += f"""
                        <tr>
                            <td style="text-align:center">{serial}</td>
                            <td style="text-align:left">{name}</td>
                            <td style="text-align:center">{qty}</td>
                            <td style="text-align:right">{price:.0f}</td>
                            <td style="text-align:right">{total:.0f}</td>
                        </tr>
            """
            serial += 1
        
        html_template += f"""
                    </tbody>
                </table>
                
                <!-- Total Section -->
                <div class="total-section">
                    <div class="total-row" style="justify-content: flex-start;">
                        <span class="total-amount">TOTAL: Rs. {total_amount:,.0f}</span>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="footer">
                    <div class="thankyou">✨ THANK YOU! ✨</div>
                    <div>Please visit again</div>
                    <div style="font-size:8px; margin-top:5px;">*This is computer generated invoice*</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template 
    def print_html_receipt(self, html_content):
        """Print HTML receipt using default browser with print optimization"""
        try:
            import tempfile
            import webbrowser
            import time
            
            # Save HTML to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            # Open in browser and trigger print dialog
            webbrowser.open(temp_file.name)
            
            # Wait a moment then show instruction
            time.sleep(1)
            messagebox.showinfo("Print", "Please press Ctrl+P to print the receipt.\n\nMake sure printer is set to 80mm thermal paper.")
            
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print: {str(e)}")           
    def direct_print_80mm(self, text):
        """Print directly to 80mm thermal printer - NO MARGINS, NO EXTRA SPACES"""
        try:
            import tempfile
            import subprocess
            
            # Clean the text - remove any leading/trailing spaces from lines
            lines = text.split('\n')
            clean_lines = []
            for line in lines:
                # Remove trailing spaces but keep leading spaces for alignment
                clean_lines.append(line.rstrip())
            
            clean_text = '\n'.join(clean_lines)
            
            # Write to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(clean_text)
            temp_file.close()
            
            # Print using Notepad with minimal margins
            subprocess.run(['notepad', '/p', temp_file.name], shell=True, timeout=5)
            os.unlink(temp_file.name)
            
        except Exception as e:
            invoices_dir = "invoices"
            if not os.path.exists(invoices_dir):
                os.makedirs(invoices_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{invoices_dir}/receipt_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Info", f"Receipt saved to:\n{filename}")
    def direct_print(self, text):
        """Print directly - REMOVE ALL EXTRA SPACES"""
        try:
            import tempfile
            import subprocess
            
            # Remove ALL empty lines
            lines = text.split('\n')
            compact_lines = []
            for line in lines:
                # Keep only lines with content
                if line.strip() != '':
                    compact_lines.append(line.rstrip())
            
            compact_text = '\n'.join(compact_lines)
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(compact_text)
            temp_file.close()
            
            subprocess.run(['notepad', '/p', temp_file.name], shell=True, timeout=5)
            os.unlink(temp_file.name)
            
        except Exception as e:
            invoices_dir = "invoices"
            if not os.path.exists(invoices_dir):
                os.makedirs(invoices_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{invoices_dir}/invoice_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Info", f"Invoice saved to:\n{filename}")
    def print_return_slip(self, return_no, return_type, reference_no, items, total_refund, reason):
        """Professional Return Slip - Same format for all returns"""
        now = datetime.now()
        
        lines = []
        width = 36
        
        type_display = {
            'PURCHASE': 'PURCHASE RETURN',
            'SALE': 'SALE RETURN',
            'TRANSFER': 'TRANSFER RETURN',
            'SHOP_RETURN': 'SHOP RETURN'
        }
        
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "FAIZAN PAPER MART" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("Rail Bazar") - 2) // 2) + "Rail Bazar" + " " * ((width - len("Rail Bazar") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("0300-8706085") - 2) // 2) + "0300-8706085" + " " * ((width - len("0300-8706085") - 2) // 2) + "|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Slip : {type_display.get(return_type, 'RETURN SLIP')}{' ' * (width - 25)}|")
        lines.append(f"| No   : {return_no:<{width-10}}|")
        lines.append(f"| Date : {now.strftime('%d-%m-%Y'):<{width-10}}|")
        lines.append(f"| Ref  : {reference_no:<{width-10}}|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Item{' ' * 10}Qty Rate{' ' * 5}Total|")
        lines.append("+" + "-" * (width - 2) + "+")
        
        for item in items:
            name = item['name'][:12]
            qty = item['quantity']
            rate = item['total'] / qty if qty > 0 else 0
            total_amt = item['total']
            lines.append(f"| {name:<12} {qty:>3} {rate:>5.0f} {total_amt:>8.0f}|")
        
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Total               {total_refund:>8.0f} Rs|")
        lines.append(f"| Payment             Refund      |")
        lines.append(f"| Status              Processed   |")
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("THANK YOU") - 2) // 2) + "THANK YOU" + " " * ((width - len("THANK YOU") - 2) // 2) + "|")
        lines.append("+" + "=" * (width - 2) + "+")
        
        receipt = "\n".join(lines)
        self._direct_print(receipt)
        
        returns_dir = "returns"
        if not os.path.exists(returns_dir):
            os.makedirs(returns_dir)
        filename = f"{returns_dir}/return_{return_no}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt)
        # ========== PHASE 8: EXPENSE MANAGEMENT SYSTEM ==========
    
    def show_expenses(self):
        """Complete Expense Management System"""
        self.clear_main_content()
        # DEBUG - Check data
        count = self.fetch_one("SELECT COUNT(*) FROM expenses")[0]
        print(f"DEBUG: Total expenses in DB: {count}")
        
        # Main container with two columns
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Expense Form
        left_frame = tk.Frame(main_container, bg="#f5f5f5", width=400)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Right side - Expense List
        right_frame = tk.Frame(main_container, bg="#f5f5f5")
        right_frame.pack(side="right", fill="both", expand=True)
        
        # ===== LEFT SIDE - EXPENSE FORM =====
        form_frame = tk.LabelFrame(left_frame, text="Add New Expense", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_inner = tk.Frame(form_frame, bg="#f5f5f5")
        form_inner.pack(padx=20, pady=20)
        
        # Category
        tk.Label(form_inner, text="Category *", font=("Arial", 11), bg="#f5f5f5").grid(row=0, column=0, sticky="w", pady=8)
        self.expense_category = ttk.Combobox(form_inner, font=("Arial", 11), width=30, state="readonly")
        self.expense_category['values'] = ['Rent', 'Utilities', 'Salary', 'Maintenance', 'Transport', 'Marketing', 'Office Supplies', 'Taxes', 'Insurance', 'Other']
        self.expense_category.grid(row=0, column=1, pady=8, padx=10)
        self.expense_category.current(0)
        
        # Amount
        tk.Label(form_inner, text="Amount (Rs.) *", font=("Arial", 11), bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=8)
        self.expense_amount = tk.Entry(form_inner, font=("Arial", 11), width=33)
        self.expense_amount.grid(row=1, column=1, pady=8, padx=10)
        
        # Date
        tk.Label(form_inner, text="Date", font=("Arial", 11), bg="#f5f5f5").grid(row=2, column=0, sticky="w", pady=8)
        self.expense_date = tk.Entry(form_inner, font=("Arial", 11), width=33)
        self.expense_date.grid(row=2, column=1, pady=8, padx=10)
        self.expense_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Payment Method
        tk.Label(form_inner, text="Payment Method", font=("Arial", 11), bg="#f5f5f5").grid(row=3, column=0, sticky="w", pady=8)
        self.expense_payment = ttk.Combobox(form_inner, font=("Arial", 11), width=30, state="readonly")
        self.expense_payment['values'] = ['Cash', 'Bank Transfer', 'Credit Card', 'Cheque']
        self.expense_payment.grid(row=3, column=1, pady=8, padx=10)
        self.expense_payment.current(0)
        
        # Description
        tk.Label(form_inner, text="Description", font=("Arial", 11), bg="#f5f5f5").grid(row=4, column=0, sticky="w", pady=8)
        self.expense_desc = tk.Text(form_inner, height=5, width=32, font=("Arial", 11))
        self.expense_desc.grid(row=4, column=1, pady=8, padx=10)
        
        # Buttons
        btn_frame = tk.Frame(form_inner, bg="#f5f5f5")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="➕ Add Expense", command=self.add_expense, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️Clear", command=self.clear_expense_form, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        # Summary Cards
        summary_frame = tk.Frame(left_frame, bg="#f5f5f5")
        summary_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.expense_total_label = tk.Label(summary_frame, text="Total Expenses: Rs. 0", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
        self.expense_total_label.pack(pady=5)
        
        self.expense_avg_label = tk.Label(summary_frame, text="Average: Rs. 0", font=("Arial", 10), bg="#f5f5f5", fg="#666")
        self.expense_avg_label.pack()
        
        # ===== RIGHT SIDE - EXPENSE LIST =====
        # Filter Frame
        filter_frame = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=10, pady=10)
        
        tk.Label(filter_inner, text="Category:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.expense_filter_category = ttk.Combobox(filter_inner, font=("Arial", 10), width=12, state="readonly")
        self.expense_filter_category['values'] = ['All', 'Rent', 'Utilities', 'Salary', 'Maintenance', 'Transport', 'Marketing', 'Office Supplies', 'Taxes', 'Insurance', 'Other']
        self.expense_filter_category.pack(side="left", padx=5)
        self.expense_filter_category.current(0)
        self.expense_filter_category.bind('<<ComboboxSelected>>', lambda e: self.load_expenses())
        
        tk.Label(filter_inner, text="From:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.expense_filter_from = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.expense_filter_from.pack(side="left", padx=5)
        self.expense_filter_from.insert(0, "2024-01-01")
        
        tk.Label(filter_inner, text="To:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.expense_filter_to = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.expense_filter_to.pack(side="left", padx=5)
        self.expense_filter_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(filter_inner, text="🔍 Filter", command=self.load_expenses, bg="#36b9cc", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(side="left", padx=5)
        tk.Button(filter_inner, text="📥 Export", command=self.export_expenses_csv, bg="#e94560", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(side="left", padx=5)
        
        # Expense Treeview
        tree_frame = tk.Frame(right_frame, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Date", "Category", "Amount", "Payment", "Description")
        self.expense_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.expense_tree.heading("ID", text="ID")
        self.expense_tree.heading("Date", text="Date")
        self.expense_tree.heading("Category", text="Category")
        self.expense_tree.heading("Amount", text="Amount (Rs.)")
        self.expense_tree.heading("Payment", text="Payment Method")
        self.expense_tree.heading("Description", text="Description")
        
        self.expense_tree.column("ID", width=50)
        self.expense_tree.column("Date", width=100)
        self.expense_tree.column("Category", width=120)
        self.expense_tree.column("Amount", width=120)
        self.expense_tree.column("Payment", width=120)
        self.expense_tree.column("Description", width=200)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.expense_tree.yview)
        self.expense_tree.configure(yscrollcommand=vsb.set)
        
        self.expense_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Right-click menu
        self.expense_context_menu = tk.Menu(self.root, tearoff=0)
        self.expense_context_menu.add_command(label="✏️ Edit", command=self.edit_expense)
        self.expense_context_menu.add_command(label="🗑️ Delete", command=self.delete_expense)
        
        self.expense_tree.bind("<Button-3>", self.show_expense_menu)
        self.expense_tree.bind("<Double-1>", lambda e: self.edit_expense())
        
        # Load expenses
        self.load_expenses()
    
    def add_expense(self):
        """Add new expense - FIXED VERSION"""
        category = self.expense_category.get()
        if not category:
            messagebox.showwarning("Validation", "Please select a category!")
            return
        
        try:
            amount = float(self.expense_amount.get())
            if amount <= 0:
                messagebox.showwarning("Validation", "Amount must be greater than 0!")
                return
        except ValueError:
            messagebox.showwarning("Validation", "Please enter a valid amount!")
            return
        
        expense_date = self.expense_date.get().strip()
        if not expense_date:
            expense_date = datetime.now().strftime("%Y-%m-%d")
        
        payment_method = self.expense_payment.get()
        description = self.expense_desc.get("1.0", "end-1c").strip()
        if not description:
            description = f"{category} expense"
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert into expenses table
            cursor.execute("""
                INSERT INTO expenses (category, amount, expense_date, payment_method, description) 
                VALUES (?, ?, ?, ?, ?)
            """, (category, amount, expense_date, payment_method, description))
            
            expense_id = cursor.lastrowid
            
            # Add to ledger (Debit - money going out)
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("EXPENSE", f"EXP-{expense_id}", f"{category}: {description[:50]}", amount, 0, expense_date))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Expense added successfully!")
            self.clear_expense_form()
            self.load_expenses()
            
            # Refresh dashboard if visible
            self.update_status(f"✅ Added expense: {category} - Rs. {amount:,.2f}")
            self.force_refresh_dashboard()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add expense: {str(e)}")
    
    def clear_expense_form(self):
        """Clear expense form fields"""
        self.expense_category.current(0)
        self.expense_amount.delete(0, tk.END)
        self.expense_date.delete(0, tk.END)
        self.expense_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.expense_payment.current(0)
        self.expense_desc.delete("1.0", tk.END)
    
    def load_expenses(self):
        """Load expenses into treeview"""
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        try:
            expenses = self.fetch_all("SELECT id, expense_date, category, amount, payment_method, description FROM expenses ORDER BY expense_date DESC")
            
            print(f"DEBUG: Found {len(expenses)} expenses in load_expenses")  # Debug
            
            total_amount = 0
            for expense in expenses:
                total_amount += expense[3]
                self.expense_tree.insert("", "end", values=(
                    expense[0],
                    expense[1][:10] if expense[1] else "-",
                    expense[2],
                    f"Rs. {expense[3]:,.2f}",
                    expense[4] or "-",
                    (expense[5] or "-")[:40]
                ))
            
            self.expense_total_label.config(text=f"Total Expenses: Rs. {total_amount:,.2f}")
            if expenses:
                avg_amount = total_amount / len(expenses)
                self.expense_avg_label.config(text=f"Average: Rs. {avg_amount:.2f}")
            else:
                self.expense_avg_label.config(text="Average: Rs. 0")
            
            self.update_status(f"Loaded {len(expenses)} expenses")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load expenses: {str(e)}")
    
    def show_expense_menu(self, event):
        """Show right-click context menu"""
        item = self.expense_tree.identify_row(event.y)
        if item:
            self.expense_tree.selection_set(item)
            self.expense_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_expense_id(self):
        """Get selected expense ID"""
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an expense first!")
            return None
        item = self.expense_tree.item(selected[0])
        return item['values'][0]
    
    def edit_expense(self):
        """Edit selected expense"""
        expense_id = self.get_selected_expense_id()
        if not expense_id:
            return
        
        expense = self.fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        if not expense:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Expense")
        dialog.geometry("500x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="✏️ Edit Expense", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        form_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        form_inner = tk.Frame(form_frame, bg="white")
        form_inner.pack(padx=20, pady=20)
        
        # Category
        tk.Label(form_inner, text="Category *", font=("Arial", 11), bg="white").grid(row=0, column=0, sticky="w", pady=8)
        category_combo = ttk.Combobox(form_inner, font=("Arial", 11), width=30, state="readonly")
        category_combo['values'] = ['Rent', 'Utilities', 'Salary', 'Maintenance', 'Transport', 'Marketing', 'Office Supplies', 'Taxes', 'Insurance', 'Other']
        category_combo.grid(row=0, column=1, pady=8, padx=10)
        category_combo.set(expense[2])
        
        # Amount
        tk.Label(form_inner, text="Amount (Rs.) *", font=("Arial", 11), bg="white").grid(row=1, column=0, sticky="w", pady=8)
        amount_entry = tk.Entry(form_inner, font=("Arial", 11), width=33)
        amount_entry.grid(row=1, column=1, pady=8, padx=10)
        amount_entry.insert(0, str(expense[3]))
        
        # Date
        tk.Label(form_inner, text="Date", font=("Arial", 11), bg="white").grid(row=2, column=0, sticky="w", pady=8)
        date_entry = tk.Entry(form_inner, font=("Arial", 11), width=33)
        date_entry.grid(row=2, column=1, pady=8, padx=10)
        date_entry.insert(0, expense[1][:10] if expense[1] else "")
        
        # Payment Method
        tk.Label(form_inner, text="Payment Method", font=("Arial", 11), bg="white").grid(row=3, column=0, sticky="w", pady=8)
        payment_combo = ttk.Combobox(form_inner, font=("Arial", 11), width=30, state="readonly")
        payment_combo['values'] = ['Cash', 'Bank Transfer', 'Credit Card', 'Cheque']
        payment_combo.grid(row=3, column=1, pady=8, padx=10)
        payment_combo.set(expense[4] or "Cash")
        
        # Description
        tk.Label(form_inner, text="Description", font=("Arial", 11), bg="white").grid(row=4, column=0, sticky="w", pady=8)
        desc_text = tk.Text(form_inner, height=5, width=32, font=("Arial", 11))
        desc_text.grid(row=4, column=1, pady=8, padx=10)
        desc_text.insert("1.0", expense[5] or "")
        
        def update_expense():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    messagebox.showwarning("Validation", "Amount must be greater than 0!")
                    return
            except ValueError:
                messagebox.showwarning("Validation", "Please enter a valid amount!")
                return
            
            try:
                self.execute_query(
                    "UPDATE expenses SET category=?, amount=?, expense_date=?, payment_method=?, description=? WHERE id=?",
                    (category_combo.get(), amount, date_entry.get(), payment_combo.get(), desc_text.get("1.0", "end-1c").strip(), expense_id)
                )
                
                # Update ledger
                self.execute_query(
                    "UPDATE ledger SET debit=?, description=?, transaction_date=? WHERE transaction_type='EXPENSE' AND reference_no=? OR (description LIKE ? AND transaction_date LIKE ?) LIMIT 1",
                    (amount, f"{category_combo.get()} expense", date_entry.get(), f"%{expense_id}%", f"%{expense[2]}%")
                )
                
                messagebox.showinfo("Success", "Expense updated successfully!")
                dialog.destroy()
                self.load_expenses()
                self.update_status("✅ Expense updated")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {str(e)}")
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="💾 Update", command=update_expense, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
    
    def delete_expense(self):
        """Delete selected expense"""
        expense_id = self.get_selected_expense_id()
        if not expense_id:
            return
        
        confirm = messagebox.askyesno("Confirm Delete", "Delete this expense? This action cannot be undone!", icon='warning')
        if confirm:
            try:
                self.execute_query("DELETE FROM expenses WHERE id = ?", (expense_id,))
                self.execute_query("DELETE FROM ledger WHERE transaction_type='EXPENSE' AND id IN (SELECT id FROM ledger WHERE description LIKE ? LIMIT 1)", (f"%{expense_id}%",))
                messagebox.showinfo("Success", "Expense deleted successfully!")
                self.load_expenses()
                self.update_status("🗑️ Expense deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def export_expenses_csv(self):
        """Export expenses to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Expenses Export")
            if not file_path:
                return
            
            expenses = self.fetch_all("SELECT expense_date, category, amount, payment_method, description FROM expenses ORDER BY expense_date DESC")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Category', 'Amount (Rs.)', 'Payment Method', 'Description'])
                for expense in expenses:
                    writer.writerow([expense[0], expense[1], expense[2], expense[3] or '', expense[4] or ''])
            
            messagebox.showinfo("Success", f"Expenses exported to:\n{file_path}")
            self.update_status(f"📥 Exported {len(expenses)} expenses")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
        # ========== PHASE 7: LEDGER & FINANCIAL MANAGEMENT WITH ADVANCED FEATURES ==========
    
    def show_ledger(self):
        """Show complete ledger with financial reports and charts"""
        self.clear_main_content()
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: Transaction Ledger
        ledger_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(ledger_tab, text="📒 Transaction Ledger")
        self.create_ledger_tab(ledger_tab)
        
        # Tab 2: Profit & Loss Statement
        pl_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(pl_tab, text="📊 Profit & Loss")
        self.create_profit_loss_tab(pl_tab)
        
        # Tab 3: Monthly Summary
        monthly_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(monthly_tab, text="📅 Monthly Summary")
        self.create_monthly_summary_tab(monthly_tab)
        
        # Tab 4: Charts & Analytics
        charts_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(charts_tab, text="📈 Charts")
        self.create_charts_tab(charts_tab)
        
        # Tab 5: Expense Analysis
        expense_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(expense_tab, text="🍩 Expense Analysis")
        self.create_expense_analysis_tab(expense_tab)
        
        # Load initial data
        self.load_ledger()
    
    def create_ledger_tab(self, parent):
        """Create the transaction ledger tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Summary Cards Frame
        summary_frame = tk.Frame(main_container, bg="#f5f5f5")
        summary_frame.pack(fill="x", pady=(0, 10))
        
        # Get totals
        try:
            total_debit = self.fetch_one("SELECT COALESCE(SUM(debit), 0) FROM ledger")[0]
            total_credit = self.fetch_one("SELECT COALESCE(SUM(credit), 0) FROM ledger")[0]
            current_balance = total_credit - total_debit
        except:
            total_debit = 0
            total_credit = 0
            current_balance = 0
        
        # Create summary cards
        cards_data = [
            ("💰 Total Purchases", f"Rs. {total_debit:,.2f}", "#e94560"),
            ("💵 Total Sales", f"Rs. {total_credit:,.2f}", "#1cc88a"),
            ("📊 Current Balance", f"Rs. {current_balance:,.2f}", "#36b9cc")
        ]
        
        for i, (title_text, value, color) in enumerate(cards_data):
            card = tk.Frame(summary_frame, bg="white", relief="ridge", bd=1)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            summary_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(card, text=title_text, font=("Arial", 11), bg="white", fg="#666").pack(pady=(10, 0))
            tk.Label(card, text=value, font=("Arial", 18, "bold"), bg="white", fg=color).pack(pady=10)
        
        # Filter Frame
        filter_frame = tk.LabelFrame(main_container, text="Filters", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#1a1a2e")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        filter_inner = tk.Frame(filter_frame, bg="#f5f5f5")
        filter_inner.pack(padx=10, pady=10)
        
        tk.Label(filter_inner, text="Date From:", font=("Arial", 10), bg="#f5f5f5").grid(row=0, column=0, padx=5, pady=5)
        self.ledger_date_from = tk.Entry(filter_inner, font=("Arial", 10), width=12)
        self.ledger_date_from.grid(row=0, column=1, padx=5, pady=5)
        self.ledger_date_from.insert(0, "2024-01-01")
        
        tk.Label(filter_inner, text="To:", font=("Arial", 10), bg="#f5f5f5").grid(row=0, column=2, padx=5, pady=5)
        self.ledger_date_to = tk.Entry(filter_inner, font=("Arial", 10), width=12)
        self.ledger_date_to.grid(row=0, column=3, padx=5, pady=5)
        self.ledger_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Label(filter_inner, text="Type:", font=("Arial", 10), bg="#f5f5f5").grid(row=0, column=4, padx=5, pady=5)
        self.ledger_type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_inner, textvariable=self.ledger_type_var, values=["All", "PURCHASE", "SALE", "EXPENSE", "STOCK_ADJUST", "OPENING"], font=("Arial", 10), width=12, state="readonly")
        type_combo.grid(row=0, column=5, padx=5, pady=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.load_ledger())
        
        tk.Label(filter_inner, text="Search:", font=("Arial", 10), bg="#f5f5f5").grid(row=0, column=6, padx=5, pady=5)
        self.ledger_search_var = tk.StringVar()
        self.ledger_search_var.trace('w', lambda *args: self.load_ledger())
        tk.Entry(filter_inner, textvariable=self.ledger_search_var, font=("Arial", 10), width=15).grid(row=0, column=7, padx=5, pady=5)
        
        tk.Button(filter_inner, text="🔍 Apply", command=self.load_ledger, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5, relief="flat").grid(row=0, column=8, padx=5, pady=5)
        tk.Button(filter_inner, text="🗑️ Clear", command=self.clear_ledger_filters, bg="#e74a3b", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5, relief="flat").grid(row=0, column=9, padx=5, pady=5)
        tk.Button(filter_inner, text="📥 Export", command=self.export_ledger_to_csv, bg="#1cc88a", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5, relief="flat").grid(row=0, column=10, padx=5, pady=5)
        
        # Stats Label
        stats_frame = tk.Frame(main_container, bg="#f5f5f5")
        stats_frame.pack(fill="x", pady=(0, 10))
        self.ledger_stats_label = tk.Label(stats_frame, text="", font=("Arial", 10), bg="#f5f5f5", fg="#666")
        self.ledger_stats_label.pack(side="left")
        
        # Treeview Frame
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Date", "Type", "Reference", "Description", "Debit", "Credit", "Balance")
        self.ledger_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        for col in columns:
            self.ledger_tree.heading(col, text=col)
        
        self.ledger_tree.column("ID", width=50)
        self.ledger_tree.column("Date", width=120)
        self.ledger_tree.column("Type", width=120)
        self.ledger_tree.column("Reference", width=120)
        self.ledger_tree.column("Description", width=250)
        self.ledger_tree.column("Debit", width=120)
        self.ledger_tree.column("Credit", width=120)
        self.ledger_tree.column("Balance", width=120)
        
        self.ledger_tree.tag_configure('purchase', background='#ffe6e6')
        self.ledger_tree.tag_configure('sale', background='#e6ffe6')
        self.ledger_tree.tag_configure('expense', background='#fff3e6')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ledger_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.ledger_tree.xview)
        self.ledger_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.ledger_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bottom buttons
        bottom_btn_frame = tk.Frame(main_container, bg="#f5f5f5")
        bottom_btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(bottom_btn_frame, text="💰 Set Opening Balance", command=self.set_opening_balance, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        tk.Button(bottom_btn_frame, text="🖨️ Print Ledger", command=self.print_ledger_report, bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
    
    def create_profit_loss_tab(self, parent):
        """Create Profit & Loss Statement tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_container, text="📊 Profit & Loss Statement", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Date selection
        date_frame = tk.Frame(main_container, bg="#f5f5f5")
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="From:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.pl_date_from = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.pl_date_from.pack(side="left", padx=5)
        self.pl_date_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="To:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.pl_date_to = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.pl_date_to.pack(side="left", padx=5)
        self.pl_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(date_frame, text="Generate Report", command=self.update_profit_loss, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        tk.Button(date_frame, text="Export PDF", command=self.export_profit_loss_pdf, bg="#e94560", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        
        # Results frame
        self.pl_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        self.pl_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_profit_loss()
    
    def update_profit_loss(self):
        """Update Profit & Loss Statement with Shop Transfers included"""
        for widget in self.pl_frame.winfo_children():
            widget.destroy()
        
        date_from = self.pl_date_from.get()
        date_to = self.pl_date_to.get()
        
        try:
            # Total Sales (from sales table)
            total_sales = self.fetch_one("SELECT COALESCE(SUM(credit), 0) FROM ledger WHERE transaction_type = 'SALE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0]
            
            # Total City Transfers (Paid)
            total_city_transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE payment_status = 'Paid' AND DATE(transfer_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            
            # Total Shop Transfers (Paid)
            total_shop_transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM shop_transfers WHERE payment_status = 'Paid' AND DATE(transfer_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            
            # Total Revenue = Sales + City Transfers + Shop Transfers
            total_revenue = total_sales + total_city_transfers + total_shop_transfers
            
            # Total Purchases (Debit)
            total_purchases = self.fetch_one("SELECT COALESCE(SUM(debit), 0) FROM ledger WHERE transaction_type = 'PURCHASE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0]
            
            # Total Expenses
            total_expenses = self.fetch_one("SELECT COALESCE(SUM(debit), 0) FROM ledger WHERE transaction_type = 'EXPENSE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0]
            
            # Gross Profit
            gross_profit = total_revenue - total_purchases
            
            # Net Profit
            net_profit = gross_profit - total_expenses
            
            # Create display
            display_text = f"""
            ═══════════════════════════════════════════════════════════
                        PROFIT & LOSS STATEMENT
            ═══════════════════════════════════════════════════════════
            
            Period: {date_from} to {date_to}
            
            ═══════════════════════════════════════════════════════════
            INCOME
            ═══════════════════════════════════════════════════════════
            
            Sales Revenue                            Rs. {total_sales:>15,.2f}
            City Transfer Revenue                    Rs. {total_city_transfers:>15,.2f}
            Shop Transfer Revenue (Front Shop)       Rs. {total_shop_transfers:>15,.2f}
            ───────────────────────────────────────────────────────────────
            TOTAL REVENUE                            Rs. {total_revenue:>15,.2f}
            
            ═══════════════════════════════════════════════════════════
            COST OF GOODS SOLD
            ═══════════════════════════════════════════════════════════
            
            Total Purchases                          Rs. {total_purchases:>15,.2f}
            
            ═══════════════════════════════════════════════════════════
            GROSS PROFIT                             Rs. {gross_profit:>15,.2f}
            ═══════════════════════════════════════════════════════════
            
            EXPENSES
            ═══════════════════════════════════════════════════════════
            
            Total Operating Expenses                 Rs. {total_expenses:>15,.2f}
            
            ═══════════════════════════════════════════════════════════
            NET PROFIT / (LOSS)                      Rs. {net_profit:>15,.2f}
            ═══════════════════════════════════════════════════════════
            
            Profit Margin: {((net_profit/total_revenue)*100 if total_revenue > 0 else 0):.1f}%
            """
            
            tk.Label(self.pl_frame, text=display_text, font=("Courier", 11), bg="white", fg="#1a1a2e", justify="left").pack(padx=20, pady=20)
            
        except Exception as e:
            tk.Label(self.pl_frame, text=f"Error loading data: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack()
    
    def create_monthly_summary_tab(self, parent):
        """Create Monthly Summary tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="📅 Monthly Financial Summary", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Year selection
        year_frame = tk.Frame(main_container, bg="#f5f5f5")
        year_frame.pack(pady=10)
        
        tk.Label(year_frame, text="Select Year:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.summary_year_var = tk.StringVar(value=str(datetime.now().year))
        year_combo = ttk.Combobox(year_frame, textvariable=self.summary_year_var, values=[str(y) for y in range(2020, datetime.now().year + 2)], font=("Arial", 11), width=8, state="readonly")
        year_combo.pack(side="left", padx=5)
        year_combo.bind('<<ComboboxSelected>>', lambda e: self.update_monthly_summary())
        
        tk.Button(year_frame, text="Refresh", command=self.update_monthly_summary, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        
        # Treeview for monthly summary
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Month", "Sales", "Purchases", "Expenses", "Profit")
        self.monthly_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=13)
        
        self.monthly_tree.heading("Month", text="Month")
        self.monthly_tree.heading("Sales", text="Sales (Rs.)")
        self.monthly_tree.heading("Purchases", text="Purchases (Rs.)")
        self.monthly_tree.heading("Expenses", text="Expenses (Rs.)")
        self.monthly_tree.heading("Profit", text="Net Profit (Rs.)")
        
        self.monthly_tree.column("Month", width=120)
        self.monthly_tree.column("Sales", width=150)
        self.monthly_tree.column("Purchases", width=150)
        self.monthly_tree.column("Expenses", width=150)
        self.monthly_tree.column("Profit", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.monthly_tree.yview)
        self.monthly_tree.configure(yscrollcommand=vsb.set)
        
        self.monthly_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.update_monthly_summary()
    
    def update_monthly_summary(self):
        """Update monthly summary data with City Transfers included"""
        for item in self.monthly_tree.get_children():
            self.monthly_tree.delete(item)
        
        year = self.summary_year_var.get()
        
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        total_sales_year = 0
        total_city_transfers_year = 0
        total_purchases_year = 0
        total_expenses_year = 0
        
        for month_num, month_name in enumerate(months, 1):
            month_str = f"{month_num:02d}"
            date_from = f"{year}-{month_str}-01"
            
            if month_num == 12:
                date_to = f"{year}-12-31"
            else:
                date_to = f"{year}-{month_num+1:02d}-01"
            
            sales = self.fetch_one("SELECT COALESCE(SUM(credit), 0) FROM ledger WHERE transaction_type = 'SALE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            city_transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE payment_status = 'Paid' AND DATE(transfer_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            purchases = self.fetch_one("SELECT COALESCE(SUM(debit), 0) FROM ledger WHERE transaction_type = 'PURCHASE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            expenses = self.fetch_one("SELECT COALESCE(SUM(debit), 0) FROM ledger WHERE transaction_type = 'EXPENSE' AND DATE(transaction_date) BETWEEN ? AND ?", (date_from, date_to))[0] or 0
            
            total_revenue = sales + city_transfers
            profit = total_revenue - purchases - expenses
            
            total_sales_year += sales
            total_city_transfers_year += city_transfers
            total_purchases_year += purchases
            total_expenses_year += expenses
            
            color = '#e6ffe6' if profit > 0 else '#ffe6e6'
            self.monthly_tree.insert("", "end", values=(
                month_name, 
                f"Rs. {sales:,.2f}", 
                f"Rs. {city_transfers:,.2f}",
                f"Rs. {purchases:,.2f}", 
                f"Rs. {expenses:,.2f}", 
                f"Rs. {profit:,.2f}"
            ), tags=(color,))
        
        # Add total row
        total_revenue_year = total_sales_year + total_city_transfers_year
        total_profit = total_revenue_year - total_purchases_year - total_expenses_year
        self.monthly_tree.insert("", "end", values=(
            "TOTAL", 
            f"Rs. {total_sales_year:,.2f}", 
            f"Rs. {total_city_transfers_year:,.2f}",
            f"Rs. {total_purchases_year:,.2f}", 
            f"Rs. {total_expenses_year:,.2f}", 
            f"Rs. {total_profit:,.2f}"
        ), tags=('bold',))
    
    def create_charts_tab(self, parent):
        """Create Charts & Analytics tab with better visualization"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and Year selection
        top_frame = tk.Frame(main_container, bg="#f5f5f5")
        top_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(top_frame, text="📊 Sales vs Expenses Analysis", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        year_frame = tk.Frame(top_frame, bg="#f5f5f5")
        year_frame.pack(side="right")
        
        tk.Label(year_frame, text="Select Year:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.chart_year_var = tk.StringVar(value=str(datetime.now().year))
        chart_year_combo = ttk.Combobox(year_frame, textvariable=self.chart_year_var, 
                                        values=[str(y) for y in range(2020, datetime.now().year + 2)], 
                                        font=("Arial", 11), width=8, state="readonly")
        chart_year_combo.pack(side="left", padx=5)
        chart_year_combo.bind('<<ComboboxSelected>>', lambda e: self.update_chart_display())
        
        tk.Button(year_frame, text="Update Chart", command=self.update_chart_display, 
                  bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        
        # Summary cards
        summary_frame = tk.Frame(main_container, bg="#f5f5f5")
        summary_frame.pack(fill="x", pady=(0, 10))
        
        # Chart display frame with scrollbar
        chart_container = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        chart_container.pack(fill="both", expand=True, pady=10)
        
        # Canvas for scrolling
        canvas = tk.Canvas(chart_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(chart_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.chart_frame = scrollable_frame
        self.chart_canvas = canvas
        
        self.update_chart_display()
    
    def update_chart_display(self):
        """Update chart display with better visualization"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        year = self.chart_year_var.get()
        
        # Get monthly data
        months_data = []
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        max_sales = 0
        max_expenses = 0
        
        for month_num in range(1, 13):
            month_str = f"{month_num:02d}"
            date_from = f"{year}-{month_str}-01"
            
            if month_num == 12:
                date_to = f"{year}-12-31"
            else:
                date_to = f"{year}-{month_num+1:02d}-01"
            
            # Sales (from ledger - credit)
            sales = self.fetch_one("""
                SELECT COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0)
                FROM ledger 
                WHERE transaction_type IN ('SALE', 'SALE_RETURN')
                AND DATE(transaction_date) BETWEEN ? AND ?
            """, (date_from, date_to))[0] or 0
            
            # Expenses (from ledger - debit)
            expenses = self.fetch_one("""
                SELECT COALESCE(SUM(debit), 0)
                FROM ledger 
                WHERE transaction_type IN ('PURCHASE', 'EXPENSE')
                AND DATE(transaction_date) BETWEEN ? AND ?
            """, (date_from, date_to))[0] or 0
            
            months_data.append((months[month_num-1], sales, expenses))
            max_sales = max(max_sales, sales)
            max_expenses = max(max_expenses, expenses)
        
        max_value = max(max_sales, max_expenses)
        max_value = max(max_value, 1000)  # Minimum 1000 for scaling
        
        # Create header with summary
        total_sales = sum(m[1] for m in months_data)
        total_expenses = sum(m[2] for m in months_data)
        net_profit = total_sales - total_expenses
        
        # Summary cards
        summary_frame = tk.Frame(self.chart_frame, bg="white")
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        cards = [
            (f"Total Sales", f"Rs. {total_sales:,.0f}", "#1cc88a"),
            (f"Total Expenses", f"Rs. {total_expenses:,.0f}", "#e74a3b"),
            (f"Net Profit", f"Rs. {net_profit:,.0f}", "#e94560" if net_profit > 0 else "#e74a3b"),
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(summary_frame, bg=color, relief="flat", bd=0, padx=10, pady=5)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            summary_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(card, text=title, font=("Arial", 9), bg=color, fg="white").pack()
            tk.Label(card, text=value, font=("Arial", 12, "bold"), bg=color, fg="white").pack()
        
        # Chart title
        tk.Label(self.chart_frame, text=f"📊 Monthly Sales vs Expenses - {year}", 
                font=("Arial", 12, "bold"), bg="white", fg="#1a1a2e").pack(pady=(10, 5))
        
        # Create text-based bar chart
        chart_text = ""
        
        # Scale factor (max 40 chars for bar)
        scale_factor = 40 / max_value if max_value > 0 else 1
        
        # Create table header
        chart_text += "┌" + "─" * 58 + "┐\n"
        chart_text += f"│ {'Month':<6} {'Sales':>12} {'Expenses':>12} {'Profit':>12} │\n"
        chart_text += "├" + "─" * 58 + "┤\n"
        
        for month, sales, expenses in months_data:
            profit = sales - expenses
            profit_color = "🟢" if profit > 0 else "🔴"
            chart_text += f"│ {month:<6} Rs.{sales:>10,.0f} Rs.{expenses:>10,.0f} {profit_color} Rs.{abs(profit):>8,.0f} │\n"
        
        chart_text += "├" + "─" * 58 + "┤\n"
        chart_text += f"│ {'TOTAL':<6} Rs.{total_sales:>10,.0f} Rs.{total_expenses:>10,.0f} {'🟢' if net_profit>0 else '🔴'} Rs.{abs(net_profit):>8,.0f} │\n"
        chart_text += "└" + "─" * 58 + "┘\n\n"
        
        # Bar chart for Sales vs Expenses
        chart_text += "📊 SALES BAR CHART\n"
        chart_text += "─" * 50 + "\n"
        
        for month, sales, expenses in months_data:
            bar_length = int(sales * scale_factor)
            bar = "█" * bar_length if bar_length > 0 else "░"
            chart_text += f"{month:<6} {bar:<40} Rs.{sales:>8,.0f}\n"
        
        chart_text += "─" * 50 + "\n\n"
        
        chart_text += "📉 EXPENSES BAR CHART\n"
        chart_text += "─" * 50 + "\n"
        
        for month, sales, expenses in months_data:
            bar_length = int(expenses * scale_factor)
            bar = "█" * bar_length if bar_length > 0 else "░"
            chart_text += f"{month:<6} {bar:<40} Rs.{expenses:>8,.0f}\n"
        
        chart_text += "─" * 50 + "\n"
        chart_text += f"\n💡 Insight: "
        
        if total_sales > 0:
            profit_margin = (net_profit / total_sales) * 100
            if net_profit > 0:
                chart_text += f"Your profit margin is {profit_margin:.1f}%. "
                if profit_margin > 20:
                    chart_text += "Excellent performance! 🎉"
                elif profit_margin > 10:
                    chart_text += "Good performance! 📈"
                else:
                    chart_text += "Room for improvement 📊"
            else:
                chart_text += f"You are operating at a loss. Review your expenses and pricing. ⚠️"
        else:
            chart_text += "No sales data available for this year."
        
        # Best month analysis
        if months_data:
            best_month = max(months_data, key=lambda x: x[1] - x[2])
            worst_month = min(months_data, key=lambda x: x[1] - x[2])
            chart_text += f"\n\n🏆 Best Month: {best_month[0]} (Profit: Rs.{best_month[1] - best_month[2]:,.0f})"
            chart_text += f"\n⚠️ Worst Month: {worst_month[0]} (Profit: Rs.{worst_month[1] - worst_month[2]:,.0f})"
        
        # Text widget
        text_widget = tk.Text(self.chart_frame, font=("Courier", 9), bg="white", fg="#1a1a2e", wrap="none")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", chart_text)
        text_widget.config(state="disabled")
        
        self.update_status(f"Chart updated for {year}")
    
    def create_expense_analysis_tab(self, parent):
        """Create Expense Analysis tab with pie chart"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="🍩 Expense Category Analysis", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Date selection
        date_frame = tk.Frame(main_container, bg="#f5f5f5")
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="From:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.expense_date_from = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.expense_date_from.pack(side="left", padx=5)
        self.expense_date_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="To:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.expense_date_to = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.expense_date_to.pack(side="left", padx=5)
        self.expense_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(date_frame, text="Analyze", command=self.update_expense_analysis, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        
        # Results frame
        self.expense_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        self.expense_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_expense_analysis()
    
    def update_expense_analysis(self):
        """Update expense analysis display"""
        for widget in self.expense_frame.winfo_children():
            widget.destroy()
        
        date_from = self.expense_date_from.get()
        date_to = self.expense_date_to.get()
        
        try:
            # Get expense categories from expenses table
            expenses = self.fetch_all("""
                SELECT COALESCE(category, 'Other'), SUM(amount) 
                FROM expenses 
                WHERE DATE(expense_date) BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
            """, (date_from, date_to))
            
            if not expenses:
                tk.Label(self.expense_frame, text="No expense data found for this period", font=("Arial", 12), bg="white", fg="#666").pack(expand=True)
                return
            
            total_expenses = sum(exp[1] for exp in expenses)
            
            # Create display
            display_text = f"📊 Expense Analysis: {date_from} to {date_to}\n"
            display_text += f"Total Expenses: Rs. {total_expenses:,.2f}\n\n"
            display_text += "=" * 40 + "\n"
            display_text += f"{'Category':<20} {'Amount':>12} {'%':>8}\n"
            display_text += "=" * 40 + "\n"
            
            for category, amount in expenses:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                bar_length = int(percentage / 2)  # 2% per character
                bar = "█" * bar_length if bar_length > 0 else "░"
                display_text += f"{category[:18]:<20} Rs. {amount:>10,.0f} {percentage:>6.1f}% {bar}\n"
            
            display_text += "=" * 40 + "\n"
            display_text += "\n💡 Insight: "
            
            # Add insight
            top_category = expenses[0][0] if expenses else "None"
            top_percentage = (expenses[0][1] / total_expenses * 100) if expenses else 0
            display_text += f"Your biggest expense is '{top_category}' at {top_percentage:.1f}% of total expenses."
            
            tk.Label(self.expense_frame, text=display_text, font=("Courier", 10), bg="white", fg="#1a1a2e", justify="left").pack(padx=20, pady=20)
            
        except Exception as e:
            tk.Label(self.expense_frame, text=f"Error: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack(expand=True)
    
    def load_ledger(self):
        """Load ledger entries with filters"""
        for item in self.ledger_tree.get_children():
            self.ledger_tree.delete(item)
        
        try:
            query = """
                SELECT id, transaction_date, transaction_type, reference_no, description, 
                       debit, credit
                FROM ledger
                WHERE 1=1
            """
            params = []
            
            date_from = self.ledger_date_from.get().strip()
            date_to = self.ledger_date_to.get().strip()
            if date_from:
                query += " AND DATE(transaction_date) >= ?"
                params.append(date_from)
            if date_to:
                query += " AND DATE(transaction_date) <= ?"
                params.append(date_to)
            
            trans_type = self.ledger_type_var.get()
            if trans_type and trans_type != "All":
                query += " AND transaction_type = ?"
                params.append(trans_type)
            
            search_term = self.ledger_search_var.get().strip()
            if search_term:
                query += " AND (description LIKE ? OR reference_no LIKE ?)"
                params.extend([f'%{search_term}%', f'%{search_term}%'])
            
                query += " ORDER BY id DESC"
            
            entries = self.fetch_all(query, params)
            
            running_balance = 0
            total_debit = 0
            total_credit = 0
            
            for entry in entries:
                debit = entry[5] or 0
                credit = entry[6] or 0
                running_balance = running_balance + credit - debit
                total_debit += debit
                total_credit += credit
                
                trans_type_display = entry[2]
                tag = 'purchase' if trans_type_display == 'PURCHASE' else 'sale' if trans_type_display == 'SALE' else 'expense' if trans_type_display == 'EXPENSE' else ''
                
                self.ledger_tree.insert("", "end", values=(
                    entry[0],
                    entry[1][:19] if entry[1] else "-",
                    trans_type_display,
                    entry[3] or "-",
                    (entry[4] or "-")[:50],
                    f"Rs. {debit:,.2f}" if debit > 0 else "-",
                    f"Rs. {credit:,.2f}" if credit > 0 else "-",
                    f"Rs. {running_balance:,.2f}"
                ), tags=(tag,))
            
            self.ledger_stats_label.config(
                text=f"📊 Total: {len(entries)} entries | Debit: Rs. {total_debit:,.2f} | Credit: Rs. {total_credit:,.2f} | Balance: Rs. {running_balance:,.2f}"
            )
            
            self.update_status(f"Loaded {len(entries)} ledger entries")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ledger: {str(e)}")
    
    def clear_ledger_filters(self):
        """Clear all ledger filters"""
        self.ledger_date_from.delete(0, tk.END)
        self.ledger_date_from.insert(0, "2024-01-01")
        self.ledger_date_to.delete(0, tk.END)
        self.ledger_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ledger_type_var.set("All")
        self.ledger_search_var.set("")
        self.load_ledger()
    
    def set_opening_balance(self):
        """Set opening balance for the ledger"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Opening Balance")
        dialog.geometry("450x250")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text="💰 Set Opening Balance", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=20)
        
        form_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(form_frame, text="Opening Balance (Rs.):", font=("Arial", 11), bg="white").pack(pady=(20, 5))
        balance_entry = tk.Entry(form_frame, font=("Arial", 12), width=20, justify="center")
        balance_entry.pack(pady=5)
        
        tk.Label(form_frame, text="Positive = Cash in hand, Negative = Debt", font=("Arial", 9), bg="white", fg="#666").pack()
        
        existing = self.fetch_one("SELECT id FROM ledger WHERE transaction_type = 'OPENING'")
        if existing:
            tk.Label(form_frame, text="⚠️ Opening balance exists! This will overwrite.", font=("Arial", 9), bg="white", fg="#e94560").pack(pady=5)
        
        def save_balance():
            try:
                balance = float(balance_entry.get())
                
                if existing:
                    if balance >= 0:
                        self.execute_query("UPDATE ledger SET credit = ?, description = 'Opening Balance' WHERE transaction_type = 'OPENING'", (balance,))
                    else:
                        self.execute_query("UPDATE ledger SET debit = ?, description = 'Opening Balance' WHERE transaction_type = 'OPENING'", (abs(balance),))
                    messagebox.showinfo("Success", "Opening balance updated!")
                else:
                    if balance >= 0:
                        self.execute_query("INSERT INTO ledger (transaction_type, description, credit) VALUES (?, ?, ?)", ("OPENING", "Opening Balance", balance))
                    else:
                        self.execute_query("INSERT INTO ledger (transaction_type, description, debit) VALUES (?, ?, ?)", ("OPENING", "Opening Balance", abs(balance)))
                    messagebox.showinfo("Success", "Opening balance set!")
                
                dialog.destroy()
                self.load_ledger()
                self.update_profit_loss()
                self.update_status("Opening balance updated")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid number!")
        
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="✅ Save", command=save_balance, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(side="left", padx=10)
    
    def export_ledger_to_csv(self):
        """Export ledger to CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Ledger Export")
            if not file_path:
                return
            
            entries = self.fetch_all("SELECT transaction_date, transaction_type, reference_no, description, debit, credit FROM ledger ORDER BY transaction_date DESC")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Transaction Type', 'Reference No', 'Description', 'Debit (Rs.)', 'Credit (Rs.)'])
                
                for entry in entries:
                    writer.writerow([entry[0], entry[1], entry[2] or '', entry[3] or '', entry[4] or 0, entry[5] or 0])
            
            messagebox.showinfo("Export Successful", f"Ledger exported to:\n{file_path}")
            self.update_status(f"📥 Exported {len(entries)} ledger entries")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def print_ledger_report(self):
        """Print ledger report"""
        entries = self.fetch_all("SELECT transaction_date, transaction_type, reference_no, description, debit, credit FROM ledger ORDER BY transaction_date DESC LIMIT 100")
        
        if not entries:
            messagebox.showwarning("No Data", "No ledger entries to print!")
            return
        
        now = datetime.now()
        
        lines = []
        lines.append("=" * 60)
        lines.append("           FAIZAN PAPER MART")
        lines.append("           LEDGER REPORT")
        lines.append(f"           Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"{'Date':<12} {'Type':<12} {'Reference':<12} {'Debit':>10} {'Credit':>10}")
        lines.append("-" * 60)
        
        for entry in entries[:50]:
            date = entry[0][:10] if entry[0] else "-"
            trans_type = entry[1][:12] if entry[1] else "-"
            ref = (entry[2] or "-")[:12]
            debit = entry[4] or 0
            credit = entry[5] or 0
            lines.append(f"{date:<12} {trans_type:<12} {ref:<12} {debit:>10,.0f} {credit:>10,.0f}")
        
        lines.append("=" * 60)
        
        report_text = "\n".join(lines)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Ledger Report")
        dialog.geometry("600x500")
        dialog.configure(bg="white")
        dialog.grab_set()
        
        text_widget = tk.Text(dialog, font=("Courier", 10), wrap="word", padx=20, pady=20)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", report_text)
        text_widget.config(state="disabled")
        
        tk.Button(dialog, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(pady=10)
    
    def export_profit_loss_pdf(self):
        """Export Profit & Loss statement as text file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save Profit & Loss Statement")
        if file_path:
            # Get current display text
            for widget in self.pl_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    text = widget.cget("text")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
                    break
    
        # ========== PHASE 9: REPORTS & ANALYTICS DASHBOARD ==========
    
    def show_reports(self):
        """Complete Reports & Analytics Dashboard"""
        self.clear_main_content()
        
        # Create Notebook for different report types
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: Sales Report
        sales_report_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(sales_report_tab, text="📊 Sales Report")
        self.create_sales_report_tab(sales_report_tab)
        
        # Tab 2: Purchase Report
        purchase_report_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(purchase_report_tab, text="🛒 Purchase Report")
        self.create_purchase_report_tab(purchase_report_tab)
        
        # Tab 3: Inventory Report
        inventory_report_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(inventory_report_tab, text="📦 Inventory Report")
        self.create_inventory_report_tab(inventory_report_tab)
        
        # Tab 4: Top Products
        top_products_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(top_products_tab, text="🏆 Top Products")
        self.create_top_products_tab(top_products_tab)
        
        # Tab 5: Business Summary
        summary_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(summary_tab, text="📋 Business Summary")
        self.create_business_summary_tab(summary_tab)
    def show_saved_invoices(self):
        """Show list of all saved invoices with view and print options"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text="📁 Saved Invoices", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        # Refresh button
        tk.Button(header_frame, text="🔄 Refresh", command=self.load_saved_invoices_list, 
                  bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="right")
        
        # Stats label
        stats_frame = tk.Frame(main_container, bg="#f5f5f5")
        stats_frame.pack(fill="x", pady=(0, 10))
        self.invoices_stats_label = tk.Label(stats_frame, text="", font=("Arial", 10), bg="#f5f5f5", fg="#666")
        self.invoices_stats_label.pack(side="left")
        
        # Treeview Frame
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        columns = ("File Name", "Date", "Time", "Size")
        self.invoices_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.invoices_tree.heading("File Name", text="Invoice File")
        self.invoices_tree.heading("Date", text="Date")
        self.invoices_tree.heading("Time", text="Time")
        self.invoices_tree.heading("Size", text="Size (KB)")
        
        self.invoices_tree.column("File Name", width=250)
        self.invoices_tree.column("Date", width=120)
        self.invoices_tree.column("Time", width=100)
        self.invoices_tree.column("Size", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.invoices_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.invoices_tree.xview)
        self.invoices_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.invoices_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Right-click menu
        self.invoice_context_menu = tk.Menu(self.root, tearoff=0)
        self.invoice_context_menu.add_command(label="👁️ View Invoice", command=self.view_selected_invoice)
        self.invoice_context_menu.add_command(label="🖨️ Print Invoice", command=self.print_selected_invoice)
        self.invoice_context_menu.add_separator()
        self.invoice_context_menu.add_command(label="🗑️ Delete Invoice", command=self.delete_selected_invoice)
        
        self.invoices_tree.bind("<Button-3>", self.show_invoice_menu)
        self.invoices_tree.bind("<Double-1>", lambda e: self.view_selected_invoice())
        
        # Load invoices
        self.load_saved_invoices_list()
    def show_saved_return_slips(self):
        """Show list of all saved return slips with view, print, and delete options"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text="📋 Saved Return Slips", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        # Refresh button
        tk.Button(header_frame, text="🔄 Refresh", command=self.load_return_slips_list, 
                  bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="right")
        
        # Stats label
        stats_frame = tk.Frame(main_container, bg="#f5f5f5")
        stats_frame.pack(fill="x", pady=(0, 10))
        self.return_slips_stats_label = tk.Label(stats_frame, text="", font=("Arial", 10), bg="#f5f5f5", fg="#666")
        self.return_slips_stats_label.pack(side="left")
        
        # Treeview Frame
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        columns = ("File Name", "Return No", "Date", "Time", "Type", "Size")
        self.return_slips_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.return_slips_tree.heading("File Name", text="File Name")
        self.return_slips_tree.heading("Return No", text="Return No")
        self.return_slips_tree.heading("Date", text="Date")
        self.return_slips_tree.heading("Time", text="Time")
        self.return_slips_tree.heading("Type", text="Type")
        self.return_slips_tree.heading("Size", text="Size (KB)")
        
        self.return_slips_tree.column("File Name", width=200)
        self.return_slips_tree.column("Return No", width=120)
        self.return_slips_tree.column("Date", width=100)
        self.return_slips_tree.column("Time", width=100)
        self.return_slips_tree.column("Type", width=100)
        self.return_slips_tree.column("Size", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.return_slips_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.return_slips_tree.xview)
        self.return_slips_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.return_slips_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Right-click menu
        self.return_slip_context_menu = tk.Menu(self.root, tearoff=0)
        self.return_slip_context_menu.add_command(label="👁️ View Return Slip", command=self.view_selected_return_slip)
        self.return_slip_context_menu.add_command(label="🖨️ Print Return Slip", command=self.print_selected_return_slip)
        self.return_slip_context_menu.add_separator()
        self.return_slip_context_menu.add_command(label="🗑️ Delete Return Slip", command=self.delete_selected_return_slip)
        
        self.return_slips_tree.bind("<Button-3>", self.show_return_slip_menu)
        self.return_slips_tree.bind("<Double-1>", lambda e: self.view_selected_return_slip())
        
        # Load return slips
        self.load_return_slips_list()
    
    def load_return_slips_list(self):
        """Load list of saved return slips from returns folder (including shop returns) with color coding"""
        for item in self.return_slips_tree.get_children():
            self.return_slips_tree.delete(item)
        
        returns_dir = "returns"
        
        if not os.path.exists(returns_dir):
            os.makedirs(returns_dir)
            self.return_slips_stats_label.config(text="No return slips saved yet")
            return
        
        # Get all return slip files (including shop_return_)
        files = [f for f in os.listdir(returns_dir) if f.endswith('.txt') and (f.startswith('return_') or f.startswith('shop_return_'))]
        files.sort(reverse=True)  # Newest first
        
        # Define color tags for different return types
        # Sale Return = Green, Purchase Return = Red, Transfer Return = Blue, Shop Return = Orange
        self.return_slips_tree.tag_configure('SALE_RETURN', background='#e6ffe6')      # Light Green
        self.return_slips_tree.tag_configure('PURCHASE_RETURN', background='#ffe6e6')   # Light Red
        self.return_slips_tree.tag_configure('TRANSFER_RETURN', background='#e6f3ff')   # Light Blue
        self.return_slips_tree.tag_configure('SHOP_RETURN', background='#fff3e6')       # Light Orange
        
        for file in files:
            file_path = os.path.join(returns_dir, file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            date_str = mod_time.strftime("%Y-%m-%d")
            time_str = mod_time.strftime("%I:%M:%S %p")
            size = os.path.getsize(file_path) / 1024
            
            # Extract return number and type from filename
            if file.startswith('shop_return_'):
                # Shop Return file format: shop_return_RET-SHP-001_timestamp.txt
                parts = file.split('_')
                return_no = parts[2] if len(parts) > 2 else "Unknown"
                return_type = "SHOP RETURN"
                tag = 'SHOP_RETURN'
            else:
                # Regular return file format: return_RET-SALE-001_timestamp.txt
                parts = file.split('_')
                return_no = parts[1] if len(parts) > 1 else "Unknown"
                
                # Determine type from return number
                if "SALE" in return_no:
                    return_type = "SALE RETURN"
                    tag = 'SALE_RETURN'
                elif "PUR" in return_no or "PURCHASE" in return_no:
                    return_type = "PURCHASE RETURN"
                    tag = 'PURCHASE_RETURN'
                elif "TRF" in return_no or "TRANSFER" in return_no:
                    return_type = "TRANSFER RETURN"
                    tag = 'TRANSFER_RETURN'
                elif "SHP" in return_no:
                    return_type = "SHOP RETURN"
                    tag = 'SHOP_RETURN'
                else:
                    return_type = "RETURN"
                    tag = 'SALE_RETURN'  # Default
            
            self.return_slips_tree.insert("", "end", values=(
                file,
                return_no,
                date_str,
                time_str,
                return_type,
                f"{size:.1f} KB"
            ), tags=(tag,))
        
        self.return_slips_stats_label.config(text=f"📊 Total Return Slips: {len(files)}")
        self.update_status(f"Loaded {len(files)} return slips")
    
    def show_return_slip_menu(self, event):
        """Show right-click context menu for return slips"""
        item = self.return_slips_tree.identify_row(event.y)
        if item:
            self.return_slips_tree.selection_set(item)
            self.return_slip_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_return_slip_file(self):
        """Get selected return slip file path"""
        selected = self.return_slips_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a return slip first!")
            return None
        
        item = self.return_slips_tree.item(selected[0])
        file_name = item['values'][0]
        file_path = os.path.join("returns", file_name)
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Return slip file not found!")
            return None
        
        return file_path
    
    def view_selected_return_slip(self):
        """View selected return slip content"""
        file_path = self.get_selected_return_slip_file()
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Return Slip: {os.path.basename(file_path)}")
            dialog.geometry("550x650")
            dialog.configure(bg="white")
            dialog.grab_set()
            
            text_widget = tk.Text(dialog, font=("Courier", 9), wrap="none", padx=15, pady=15)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")
            
            btn_frame = tk.Frame(dialog, bg="white")
            btn_frame.pack(pady=10)
            
            tk.Button(btn_frame, text="🖨️ Print Again", 
                      command=lambda: self.print_return_slip_file(file_path, dialog),
                      bg="#e94560", fg="white", font=("Arial", 11, "bold"), 
                      padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            tk.Button(btn_frame, text="Close", command=dialog.destroy,
                      bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), 
                      padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open return slip: {str(e)}")
    
    def print_selected_return_slip(self):
        """Print selected return slip again"""
        file_path = self.get_selected_return_slip_file()
        if not file_path:
            return
        
        self.print_return_slip_file(file_path)
    
    def print_return_slip_file(self, file_path, dialog=None):
        """Print a return slip file to thermal printer"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                slip_text = f.read()
            
            import tempfile
            import subprocess
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(slip_text)
            temp_file.close()
            
            subprocess.run(['notepad', '/p', temp_file.name], shell=True)
            
            messagebox.showinfo("Print", "Return slip sent to printer!")
            if dialog:
                dialog.destroy()
            
            os.unlink(temp_file.name)
            
        except Exception as e:
            result = messagebox.askyesno("Print Failed", 
                f"Could not print.\n\n{str(e)}\n\nView return slip instead?")
            if result:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                view_dialog = tk.Toplevel(self.root)
                view_dialog.title("Return Slip")
                view_dialog.geometry("500x600")
                text_widget = tk.Text(view_dialog, font=("Courier", 9), wrap="none", padx=10, pady=10)
                text_widget.pack(fill="both", expand=True)
                text_widget.insert("1.0", content)
                text_widget.config(state="disabled")
                tk.Button(view_dialog, text="Close", command=view_dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(pady=10)
    
    def delete_selected_return_slip(self):
        """Delete selected return slip file"""
        file_path = self.get_selected_return_slip_file()
        if not file_path:
            return
        
        confirm = messagebox.askyesno("Confirm Delete", 
            f"Delete this return slip?\n\n{os.path.basename(file_path)}\n\nThis action cannot be undone!",
            icon='warning')
        
        if confirm:
            try:
                os.remove(file_path)
                messagebox.showinfo("Success", "Return slip deleted successfully!")
                self.load_return_slips_list()
                self.update_status("Return slip deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    def load_saved_invoices_list(self):
        """Load list of saved invoices from invoices folder"""
        for item in self.invoices_tree.get_children():
            self.invoices_tree.delete(item)
        
        invoices_dir = "invoices"
        
        if not os.path.exists(invoices_dir):
            os.makedirs(invoices_dir)
            self.invoices_stats_label.config(text="No invoices saved yet")
            return
        
        # Get all invoice files
        files = [f for f in os.listdir(invoices_dir) if f.endswith('.txt') and ('sale_' in f or 'purchase_' in f or 'invoice_' in f or 'transfer_' in f)]
        files.sort(reverse=True)  # Newest first
        
        for file in files:
            file_path = os.path.join(invoices_dir, file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            date_str = mod_time.strftime("%Y-%m-%d")
            time_str = mod_time.strftime("%I:%M:%S %p")
            size = os.path.getsize(file_path) / 1024
            
            # Extract type from filename or content
            invoice_type = self.get_invoice_type(file_path)
            
            self.invoices_tree.insert("", "end", values=(
                file,
                date_str,
                time_str,
                f"{size:.1f} KB"
            ), tags=(invoice_type,))
        
        # Color tags
        self.invoices_tree.tag_configure('SALE', background='#e6ffe6')
        self.invoices_tree.tag_configure('PURCHASE', background='#ffe6e6')
        self.invoices_tree.tag_configure('TRANSFER', background='#e6f3ff')
        
        self.invoices_stats_label.config(text=f"📊 Total Saved Invoices: {len(files)}")
        self.update_status(f"Loaded {len(files)} saved invoices")
    
    def get_invoice_type(self, file_path):
        """Determine invoice type from file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "PURCHASE ORDER" in content or "PO No" in content:
                    return "PURCHASE"
                elif "STOCK TRANSFER" in content or "Transfer No" in content:
                    return "TRANSFER"
                else:
                    return "SALE"
        except:
            return "SALE"
    
    def show_invoice_menu(self, event):
        """Show right-click context menu for invoices"""
        item = self.invoices_tree.identify_row(event.y)
        if item:
            self.invoices_tree.selection_set(item)
            self.invoice_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_invoice_file(self):
        """Get selected invoice file path"""
        selected = self.invoices_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an invoice first!")
            return None
        
        item = self.invoices_tree.item(selected[0])
        file_name = item['values'][0]
        file_path = os.path.join("invoices", file_name)
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Invoice file not found!")
            return None
        
        return file_path
    
    def view_selected_invoice(self):
        """View selected invoice content"""
        file_path = self.get_selected_invoice_file()
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Show dialog
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Invoice: {os.path.basename(file_path)}")
            dialog.geometry("550x650")
            dialog.configure(bg="white")
            dialog.grab_set()
            
            # Invoice display
            text_widget = tk.Text(dialog, font=("Courier", 9), wrap="none", padx=15, pady=15)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")
            
            # Buttons frame
            btn_frame = tk.Frame(dialog, bg="white")
            btn_frame.pack(pady=10)
            
            tk.Button(btn_frame, text="🖨️ Print Again", 
                      command=lambda: self.print_invoice_file(file_path, dialog),
                      bg="#e94560", fg="white", font=("Arial", 11, "bold"), 
                      padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            tk.Button(btn_frame, text="Close", command=dialog.destroy,
                      bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), 
                      padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open invoice: {str(e)}")
    
    def print_selected_invoice(self):
        """Print selected invoice again"""
        file_path = self.get_selected_invoice_file()
        if not file_path:
            return
        
        self.print_invoice_file(file_path)
    
    def print_invoice_file(self, file_path, dialog=None):
        """Print an invoice file to thermal printer"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                invoice_text = f.read()
            
            import tempfile
            import subprocess
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(invoice_text)
            temp_file.close()
            
            subprocess.run(['notepad', '/p', temp_file.name], shell=True)
            
            messagebox.showinfo("Print", "Invoice sent to printer!")
            if dialog:
                dialog.destroy()
            
            os.unlink(temp_file.name)
            
        except Exception as e:
            result = messagebox.askyesno("Print Failed", 
                f"Could not print.\n\n{str(e)}\n\nView invoice instead?")
            if result:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                view_dialog = tk.Toplevel(self.root)
                view_dialog.title("Invoice")
                view_dialog.geometry("500x600")
                text_widget = tk.Text(view_dialog, font=("Courier", 9), wrap="none", padx=10, pady=10)
                text_widget.pack(fill="both", expand=True)
                text_widget.insert("1.0", content)
                text_widget.config(state="disabled")
                tk.Button(view_dialog, text="Close", command=view_dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(pady=10)
    
    def delete_selected_invoice(self):
        """Delete selected invoice file"""
        file_path = self.get_selected_invoice_file()
        if not file_path:
            return
        
        confirm = messagebox.askyesno("Confirm Delete", 
            f"Delete this invoice?\n\n{os.path.basename(file_path)}\n\nThis action cannot be undone!",
            icon='warning')
        
        if confirm:
            try:
                os.remove(file_path)
                messagebox.showinfo("Success", "Invoice deleted successfully!")
                self.load_saved_invoices_list()
                self.update_status("Invoice deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def create_sales_report_tab(self, parent):
        """Create Sales Report tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="📊 Sales Report", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Filter Frame
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=10)
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=20, pady=15)
        
        tk.Label(filter_inner, text="From:", font=("Arial", 11), bg="white").pack(side="left", padx=5)
        self.sales_report_from = tk.Entry(filter_inner, font=("Arial", 11), width=12)
        self.sales_report_from.pack(side="left", padx=5)
        self.sales_report_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(filter_inner, text="To:", font=("Arial", 11), bg="white").pack(side="left", padx=5)
        self.sales_report_to = tk.Entry(filter_inner, font=("Arial", 11), width=12)
        self.sales_report_to.pack(side="left", padx=5)
        self.sales_report_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(filter_inner, text="Generate Report", command=self.update_sales_report, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=20)
        tk.Button(filter_inner, text="Export CSV", command=self.export_sales_report, bg="#e94560", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        
        # Results Frame
        self.sales_report_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        self.sales_report_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_sales_report()
    
    def update_sales_report(self):
        """Update sales report display with Transfers and Shop Transfers included"""
        for widget in self.sales_report_frame.winfo_children():
            widget.destroy()
        
        date_from = self.sales_report_from.get()
        date_to = self.sales_report_to.get()
        
        try:
            # Get sales data from sales table
            sales = self.fetch_all("""
                SELECT s.invoice_no, s.sale_date, s.customer_name, s.total_amount, s.payment_method,
                       COUNT(si.id) as item_count, 'Sale' as type
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY s.id
                ORDER BY s.sale_date DESC
            """, (date_from, date_to))
            
            # Get city transfer data (Paid ones act like sales)
            transfers = self.fetch_all("""
                SELECT st.transfer_no, st.transfer_date, st.recipient_name, st.total_amount, 
                       'Transfer' as payment_method, COUNT(ti.id) as item_count, 'City Transfer' as type
                FROM stock_transfers st
                LEFT JOIN transfer_items ti ON st.id = ti.transfer_id
                WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
                GROUP BY st.id
                ORDER BY st.transfer_date DESC
            """, (date_from, date_to))
            
            # Get Shop Transfer data (Paid ones act like sales)
            shop_transfers = self.fetch_all("""
                SELECT st.transfer_no, st.transfer_date, st.recipient_name, st.total_amount, 
                       'Shop Transfer' as payment_method, COUNT(sti.id) as item_count, 'Shop Transfer' as type
                FROM shop_transfers st
                LEFT JOIN shop_transfer_items sti ON st.id = sti.transfer_id
                WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
                GROUP BY st.id
                ORDER BY st.transfer_date DESC
            """, (date_from, date_to))
            
            # Combine all: sales + city transfers + shop transfers
            all_transactions = list(sales) + list(transfers) + list(shop_transfers)
            
            # Sort by date (newest first)
            all_transactions.sort(key=lambda x: x[1] if x[1] else "", reverse=True)
            
            # Calculate totals
            total_revenue = sum(t[3] for t in all_transactions)
            total_transactions = len(all_transactions)
            avg_sale = total_revenue / total_transactions if total_transactions > 0 else 0
            
            # Summary cards
            summary_frame = tk.Frame(self.sales_report_frame, bg="white")
            summary_frame.pack(fill="x", padx=20, pady=15)
            
            cards = [
                (f"Total Revenue", f"Rs. {total_revenue:,.2f}", "#1cc88a"),
                (f"Transactions", str(total_transactions), "#36b9cc"),
                (f"Average Sale", f"Rs. {avg_sale:,.2f}", "#e94560"),
                (f"Sales", str(len(sales)), "#4e73df"),
                (f"City Transfers", str(len(transfers)), "#f6c23e"),
                (f"Shop Transfers", str(len(shop_transfers)), "#1cc88a")
            ]
            
            # Create cards in rows (3 cards per row)
            for i, (title, value, color) in enumerate(cards):
                row = i // 3
                col = i % 3
                card = tk.Frame(summary_frame, bg=color, relief="flat", bd=0)
                card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                summary_frame.grid_columnconfigure(col, weight=1)
                
                tk.Label(card, text=title, font=("Arial", 9), bg=color, fg="white").pack(pady=(10, 0))
                tk.Label(card, text=value, font=("Arial", 12, "bold"), bg=color, fg="white").pack(pady=10)
            
            # Treeview
            tree_frame = tk.Frame(self.sales_report_frame, bg="white")
            tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            columns = ("Type", "Invoice/Transfer", "Date", "Customer/Recipient", "Items", "Amount", "Payment")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
            
            for col in columns:
                tree.heading(col, text=col)
            
            tree.column("Type", width=100)
            tree.column("Invoice/Transfer", width=130)
            tree.column("Date", width=100)
            tree.column("Customer/Recipient", width=150)
            tree.column("Items", width=60)
            tree.column("Amount", width=120)
            tree.column("Payment", width=100)
            
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            tree.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            hsb.pack(side="bottom", fill="x")
            
            # Color tags for different types
            tree.tag_configure('Sale', background='#e6ffe6')
            tree.tag_configure('City Transfer', background='#e6f3ff')
            tree.tag_configure('Shop Transfer', background='#fff3e6')
            
            for trans in all_transactions:
                trans_type = trans[6] if len(trans) > 6 else "Sale"
                tag = trans_type
                
                tree.insert("", "end", values=(
                    trans_type,
                    trans[0],
                    trans[1][:10] if trans[1] else "-",
                    trans[2] or "-",
                    trans[5] if len(trans) > 5 else 0,
                    f"Rs. {trans[3]:,.2f}",
                    trans[4]
                ), tags=(tag,))
            
            self.update_status(f"Sales report: {len(sales)} sales, {len(transfers)} city transfers, {len(shop_transfers)} shop transfers, Total: Rs. {total_revenue:,.2f}")
            
        except Exception as e:
            tk.Label(self.sales_report_frame, text=f"Error: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack(expand=True)
    
    def export_sales_report(self):
        """Export sales report to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Sales Report")
            if not file_path:
                return
            
            date_from = self.sales_report_from.get()
            date_to = self.sales_report_to.get()
            
            sales = self.fetch_all("""
                SELECT s.invoice_no, s.sale_date, s.customer_name, s.total_amount, s.payment_method
                FROM sales s
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                ORDER BY s.sale_date DESC
            """, (date_from, date_to))
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Invoice No', 'Date', 'Customer Name', 'Total Amount (Rs.)', 'Payment Method'])
                for sale in sales:
                    writer.writerow([sale[0], sale[1], sale[2] or "Walk-in", sale[3], sale[4]])
            
            messagebox.showinfo("Success", f"Sales report exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def create_purchase_report_tab(self, parent):
        """Create Purchase Report tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="🛒 Purchase Report", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Filter Frame
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=10)
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=20, pady=15)
        
        tk.Label(filter_inner, text="From:", font=("Arial", 11), bg="white").pack(side="left", padx=5)
        self.purchase_report_from = tk.Entry(filter_inner, font=("Arial", 11), width=12)
        self.purchase_report_from.pack(side="left", padx=5)
        self.purchase_report_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(filter_inner, text="To:", font=("Arial", 11), bg="white").pack(side="left", padx=5)
        self.purchase_report_to = tk.Entry(filter_inner, font=("Arial", 11), width=12)
        self.purchase_report_to.pack(side="left", padx=5)
        self.purchase_report_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(filter_inner, text="Generate Report", command=self.update_purchase_report, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=20)
        
        # Results Frame
        self.purchase_report_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        self.purchase_report_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_purchase_report()
    
    def update_purchase_report(self):
        """Update purchase report display"""
        for widget in self.purchase_report_frame.winfo_children():
            widget.destroy()
        
        date_from = self.purchase_report_from.get()
        date_to = self.purchase_report_to.get()
        
        try:
            purchases = self.fetch_all("""
                SELECT p.invoice_no, p.purchase_date, s.name as supplier_name, p.total_amount
                FROM purchases p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE DATE(p.purchase_date) BETWEEN ? AND ?
                ORDER BY p.purchase_date DESC
            """, (date_from, date_to))
            
            total_purchases = sum(p[3] for p in purchases)
            
            # Summary
            summary_frame = tk.Frame(self.purchase_report_frame, bg="white")
            summary_frame.pack(fill="x", padx=20, pady=15)
            
            tk.Label(summary_frame, text=f"Total Purchases: Rs. {total_purchases:,.2f}", font=("Arial", 14, "bold"), bg="white", fg="#e94560").pack()
            tk.Label(summary_frame, text=f"Number of Orders: {len(purchases)}", font=("Arial", 11), bg="white", fg="#666").pack()
            
            # Treeview
            tree_frame = tk.Frame(self.purchase_report_frame, bg="white")
            tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            columns = ("Invoice", "Date", "Supplier", "Amount")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
            
            for col in columns:
                tree.heading(col, text=col)
            
            tree.column("Invoice", width=150)
            tree.column("Date", width=150)
            tree.column("Supplier", width=200)
            tree.column("Amount", width=150)
            
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            
            tree.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            
            for purchase in purchases:
                tree.insert("", "end", values=(
                    purchase[0], purchase[1][:10] if purchase[1] else "-", purchase[2], f"Rs. {purchase[3]:,.2f}"
                ))
            
        except Exception as e:
            tk.Label(self.purchase_report_frame, text=f"Error: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack(expand=True)
    
    def create_inventory_report_tab(self, parent):
        """Create Inventory Report tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="📦 Inventory Status Report", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Summary Cards
        summary_frame = tk.Frame(main_container, bg="#f5f5f5")
        summary_frame.pack(fill="x", pady=10)
        
        try:
            total_products = self.fetch_one("SELECT COUNT(*) FROM products")[0]
            total_stock = self.fetch_one("SELECT COALESCE(SUM(stock_quantity), 0) FROM products")[0]
            low_stock = self.fetch_one("SELECT COUNT(*) FROM products WHERE stock_quantity <= reorder_level")[0]
            total_value = self.fetch_one("SELECT COALESCE(SUM(stock_quantity * cost_price), 0) FROM products")[0]
        except:
            total_products = 0
            total_stock = 0
            low_stock = 0
            total_value = 0
        
        cards = [
            ("Total Products", str(total_products), "#36b9cc"),
            ("Total Stock Units", str(total_stock), "#1cc88a"),
            ("Low Stock Items", str(low_stock), "#e94560"),
            ("Inventory Value", f"Rs. {total_value:,.2f}", "#f6c23e"),
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(summary_frame, bg="white", relief="ridge", bd=1)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            summary_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(card, text=title, font=("Arial", 10), bg="white", fg="#666").pack(pady=(10, 0))
            tk.Label(card, text=value, font=("Arial", 18, "bold"), bg="white", fg=color).pack(pady=10)
        
        # Low Stock Alert
        low_stock_label = tk.LabelFrame(main_container, text="⚠️ Low Stock Alert", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
        low_stock_label.pack(fill="both", expand=True, pady=10)
        
        low_stock_frame = tk.Frame(low_stock_label, bg="#f5f5f5")
        low_stock_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        low_stock_products = self.fetch_all("""
            SELECT p.name, p.brand, p.stock_quantity, p.reorder_level
            FROM products p
            WHERE p.stock_quantity <= p.reorder_level
            ORDER BY p.stock_quantity ASC
        """)
        
        if low_stock_products:
            columns = ("Product", "Brand", "Current Stock", "Reorder Level")
            tree = ttk.Treeview(low_stock_frame, columns=columns, show="headings", height=8)
            
            for col in columns:
                tree.heading(col, text=col)
            
            tree.column("Product", width=200)
            tree.column("Brand", width=120)
            tree.column("Current Stock", width=100)
            tree.column("Reorder Level", width=100)
            
            vsb = ttk.Scrollbar(low_stock_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            
            tree.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            
            for product in low_stock_products:
                tree.insert("", "end", values=(product[0], product[1] or "-", product[2], product[3]))
        else:
            tk.Label(low_stock_frame, text="✅ All products have sufficient stock!", font=("Arial", 12), bg="#f5f5f5", fg="#1cc88a").pack(pady=20)
                    # ===== SHOPPING LIST BUTTON =====
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill="x", pady=(15, 0))
        
        shopping_btn = tk.Button(
            button_frame,
            text="📋 GENERATE PURCHASE LIST",
            command=self.show_shopping_list_window,
            bg="#e94560",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        shopping_btn.pack(pady=5)
    
    def create_top_products_tab(self, parent):
        """Create Top Products tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="🏆 Top Selling Products", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Date selection
        date_frame = tk.Frame(main_container, bg="#f5f5f5")
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="From:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.top_products_from = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.top_products_from.pack(side="left", padx=5)
        self.top_products_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="To:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.top_products_to = tk.Entry(date_frame, font=("Arial", 11), width=12)
        self.top_products_to.pack(side="left", padx=5)
        self.top_products_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(date_frame, text="Refresh", command=self.update_top_products, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=20)
        
        # Results Frame
        self.top_products_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        self.top_products_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_top_products()
    
    def update_top_products(self):
        """Update top products display with Sales, City Transfers, and Shop Transfers"""
        for widget in self.top_products_frame.winfo_children():
            widget.destroy()
        
        date_from = self.top_products_from.get()
        date_to = self.top_products_to.get()
        
        try:
            # Get top products from sales
            top_sales = self.fetch_all("""
                SELECT p.name, p.brand, SUM(si.quantity) as total_sold, SUM(si.total) as total_revenue, 'Sale' as source
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
                GROUP BY si.product_id
            """, (date_from, date_to))
            
            # Get top products from city transfers
            top_city_transfers = self.fetch_all("""
                SELECT p.name, p.brand, SUM(ti.quantity) as total_sold, SUM(ti.total) as total_revenue, 'City Transfer' as source
                FROM transfer_items ti
                JOIN products p ON ti.product_id = p.id
                JOIN stock_transfers st ON ti.transfer_id = st.id
                WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
                GROUP BY ti.product_id
            """, (date_from, date_to))
            
            # Get top products from shop transfers
            top_shop = self.fetch_all("""
                SELECT p.name, p.brand, SUM(sti.quantity) as total_sold, SUM(sti.total) as total_revenue, 'Shop Transfer' as source
                FROM shop_transfer_items sti
                JOIN products p ON sti.product_id = p.id
                JOIN shop_transfers st ON sti.transfer_id = st.id
                WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
                GROUP BY sti.product_id
            """, (date_from, date_to))
            
            # Combine all products
            all_products = list(top_sales) + list(top_city_transfers) + list(top_shop)
            
            if not all_products:
                tk.Label(self.top_products_frame, text="No sales/transfer data for this period", font=("Arial", 12), bg="white", fg="#666").pack(expand=True)
                return
            
            # Sort by total sold quantity (descending)
            all_products.sort(key=lambda x: x[2], reverse=True)
            top_products = all_products[:10]  # Top 10
            
            # Calculate total revenue from top products
            total_revenue = sum(p[3] for p in top_products)
            
            # Create display
            display_text = f"🏆 TOP 10 PRODUCTS ({date_from} to {date_to})\n\n"
            display_text += "=" * 65 + "\n"
            display_text += f"{'#':<3} {'Product':<18} {'Brand':<10} {'Source':<12} {'Qty Sold':>10} {'Revenue':>12}\n"
            display_text += "=" * 65 + "\n"
            
            # Color codes for different sources
            for i, product in enumerate(top_products, 1):
                source = product[4]
                source_display = source
                
                # Add indicator for source type
                if source == 'Sale':
                    source_display = '🛒 Sale'
                elif source == 'City Transfer':
                    source_display = '🚚 City'
                else:
                    source_display = '🏪 Shop'
                
                display_text += f"{i:<3} {product[0][:16]:<18} {product[1][:8] or '-':<10} {source_display:<12} {product[2]:>10} Rs. {product[3]:>10,.0f}\n"
            
            display_text += "=" * 65 + "\n"
            display_text += f"{'Total Revenue from Top 10':>50} Rs. {total_revenue:>12,.0f}\n"
            display_text += "=" * 65 + "\n\n"
            
            # Add summary by source
            display_text += "📊 SUMMARY BY SOURCE:\n"
            display_text += "-" * 40 + "\n"
            
            sale_qty = sum(p[2] for p in top_products if p[4] == 'Sale')
            sale_rev = sum(p[3] for p in top_products if p[4] == 'Sale')
            city_qty = sum(p[2] for p in top_products if p[4] == 'City Transfer')
            city_rev = sum(p[3] for p in top_products if p[4] == 'City Transfer')
            shop_qty = sum(p[2] for p in top_products if p[4] == 'Shop Transfer')
            shop_rev = sum(p[3] for p in top_products if p[4] == 'Shop Transfer')
            
            if sale_qty > 0:
                display_text += f"🛒 Sales: {sale_qty} units | Rs. {sale_rev:,.0f}\n"
            if city_qty > 0:
                display_text += f"🚚 City Transfers: {city_qty} units | Rs. {city_rev:,.0f}\n"
            if shop_qty > 0:
                display_text += f"🏪 Shop Transfers: {shop_qty} units | Rs. {shop_rev:,.0f}\n"
            
            display_text += "-" * 40 + "\n"
            
            tk.Label(self.top_products_frame, text=display_text, font=("Courier", 9), bg="white", fg="#1a1a2e", justify="left").pack(padx=20, pady=20)
            
        except Exception as e:
            tk.Label(self.top_products_frame, text=f"Error: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack(expand=True)
    
    def create_business_summary_tab(self, parent):
        """Create Business Summary tab with scrollbar"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and Year selection (fixed at top)
        top_frame = tk.Frame(main_container, bg="#f5f5f5")
        top_frame.pack(fill="x")
        
        tk.Label(top_frame, text="📋 Business Performance Summary", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        # Year selection
        year_frame = tk.Frame(top_frame, bg="#f5f5f5")
        year_frame.pack(side="right")
        
        tk.Label(year_frame, text="Select Year:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.summary_year = ttk.Combobox(year_frame, font=("Arial", 11), width=8, state="readonly")
        self.summary_year['values'] = [str(y) for y in range(2020, datetime.now().year + 2)]
        self.summary_year.pack(side="left", padx=5)
        self.summary_year.set(str(datetime.now().year))
        self.summary_year.bind('<<ComboboxSelected>>', lambda e: self.update_business_summary())
        
        tk.Button(year_frame, text="Generate Summary", command=self.update_business_summary, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        tk.Button(year_frame, text="📥 Export CSV", command=self.export_business_summary_csv, bg="#e94560", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        
        # Scrollable area for summary
        canvas_frame = tk.Frame(main_container, bg="#f5f5f5")
        canvas_frame.pack(fill="both", expand=True, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white", relief="ridge", bd=1)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas_frame.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update canvas width when frame resizes
        def on_frame_configure(e):
            canvas.itemconfig(1, width=e.width)
        canvas_frame.bind("<Configure>", on_frame_configure)
        
        self.summary_frame = scrollable_frame
        self.summary_canvas = canvas
        
        self.update_business_summary()
    
    def update_business_summary(self):
        """Update business summary display with accurate calculations including Shop Transfers"""
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        year = self.summary_year.get()
        
        try:
            # Sales from sales table
            sales_total = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime('%Y', sale_date) = ?", (year,))[0] or 0
            
            # Sales Returns (refunds given to customers)
            sales_returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'SALE' AND strftime('%Y', return_date) = ?", (year,))[0] or 0
            
            # Net Sales = Sales - Returns
            net_sales = sales_total - sales_returns
            
            # Purchase Returns (refunds received from suppliers)
            purchase_returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'PURCHASE' AND strftime('%Y', return_date) = ?", (year,))[0] or 0
            
            # City Transfers (Paid)
            city_transfers_total = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE strftime('%Y', transfer_date) = ? AND payment_status = 'Paid'", (year,))[0] or 0
            
            # Shop Transfers (Paid)
            shop_transfers_total = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM shop_transfers WHERE strftime('%Y', transfer_date) = ? AND payment_status = 'Paid'", (year,))[0] or 0
            
            # Shop Returns (refund given to shop)
            shop_returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'SHOP_RETURN' AND strftime('%Y', return_date) = ?", (year,))[0] or 0
            
            # Total Purchases
            total_purchases = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases WHERE strftime('%Y', purchase_date) = ?", (year,))[0] or 0
            
            # Net Purchases after returns
            net_purchases = total_purchases - purchase_returns
            
            # Total Expenses
            total_expenses = self.fetch_one("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y', expense_date) = ?", (year,))[0] or 0
            
            # Total Revenue (including shop transfers)
            total_revenue = net_sales + city_transfers_total + shop_transfers_total - shop_returns
            
            # Gross Profit
            gross_profit = total_revenue - net_purchases
            
            # Net Profit
            net_profit = gross_profit - total_expenses
            profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Transaction counts
            total_customers = self.fetch_one("SELECT COUNT(DISTINCT customer_name) FROM sales WHERE customer_name NOT IN ('Walk-in Customer', 'N/A', '') AND strftime('%Y', sale_date) = ?", (year,))[0] or 0
            total_suppliers = self.fetch_one("SELECT COUNT(*) FROM suppliers")[0] or 0
            total_products = self.fetch_one("SELECT COUNT(*) FROM products")[0] or 0
            total_cities = self.fetch_one("SELECT COUNT(DISTINCT destination_city) FROM stock_transfers WHERE strftime('%Y', transfer_date) = ?", (year,))[0] or 0
            
            display_text = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    BUSINESS SUMMARY - {year}                      ║
╚═══════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────┐
│                    📊 FINANCIAL SUMMARY                       │
├───────────────────────────────────────────────────────────────┤
│  Sales Revenue                         Rs. {sales_total:>15,.2f} │
│  Less: Sales Returns                   Rs. {sales_returns:>15,.2f} │
│  ───────────────────────────────────────────────────────────── │
│  Net Sales                             Rs. {net_sales:>15,.2f} │
│  City Transfer Revenue                 Rs. {city_transfers_total:>15,.2f} │
│  Shop Transfer Revenue                 Rs. {shop_transfers_total:>15,.2f} │
│  Less: Shop Returns                    Rs. {shop_returns:>15,.2f} │
│  ───────────────────────────────────────────────────────────── │
│  TOTAL REVENUE                         Rs. {total_revenue:>15,.2f} │
│                                                               │
│  Cost of Goods Sold (Purchases)        Rs. {total_purchases:>15,.2f} │
│  Less: Purchase Returns                Rs. {purchase_returns:>15,.2f} │
│  ───────────────────────────────────────────────────────────── │
│  NET COGS                              Rs. {net_purchases:>15,.2f} │
│  ───────────────────────────────────────────────────────────── │
│  GROSS PROFIT                          Rs. {gross_profit:>15,.2f} │
│                                                               │
│  Operating Expenses                    Rs. {total_expenses:>15,.2f} │
│  ───────────────────────────────────────────────────────────── │
│  NET PROFIT / (LOSS)                   Rs. {net_profit:>15,.2f} │
│  Profit Margin                                    {profit_margin:>6.1f}% │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    📈 BUSINESS METRICS                        │
├───────────────────────────────────────────────────────────────┤
│  Total Customers                         {total_customers:>15} │
│  Total Suppliers                         {total_suppliers:>15} │
│  Total Products in Inventory             {total_products:>15} │
│  Cities Served (Transfer)                {total_cities:>15} │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    📅 MONTHLY BREAKDOWN                       │
└───────────────────────────────────────────────────────────────┘
"""
            
            # Add monthly breakdown
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            display_text += "\n" + "─" * 70 + "\n"
            display_text += f"{'Month':<6} {'Sales':>10} {'Returns':>10} {'City Trans':>10} {'Shop Trans':>10} {'Purchases':>10} {'Expenses':>10} {'Profit':>10}\n"
            display_text += "─" * 70 + "\n"
            
            for month_num, month_name in enumerate(months, 1):
                month_str = f"{month_num:02d}"
                sales = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime('%Y', sale_date) = ? AND strftime('%m', sale_date) = ?", (year, month_str))[0] or 0
                returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'SALE' AND strftime('%Y', return_date) = ? AND strftime('%m', return_date) = ?", (year, month_str))[0] or 0
                city_transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE strftime('%Y', transfer_date) = ? AND strftime('%m', transfer_date) = ? AND payment_status = 'Paid'", (year, month_str))[0] or 0
                shop_transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM shop_transfers WHERE strftime('%Y', transfer_date) = ? AND strftime('%m', transfer_date) = ? AND payment_status = 'Paid'", (year, month_str))[0] or 0
                purchases = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases WHERE strftime('%Y', purchase_date) = ? AND strftime('%m', purchase_date) = ?", (year, month_str))[0] or 0
                expenses = self.fetch_one("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y', expense_date) = ? AND strftime('%m', expense_date) = ?", (year, month_str))[0] or 0
                net_sales_month = sales - returns
                total_revenue_month = net_sales_month + city_transfers + shop_transfers
                profit = total_revenue_month - purchases - expenses
                
                display_text += f"{month_name:<6} {sales:>10,.0f} {returns:>10,.0f} {city_transfers:>10,.0f} {shop_transfers:>10,.0f} {purchases:>10,.0f} {expenses:>10,.0f} {profit:>10,.0f}\n"
            
            display_text += "═" * 70 + "\n"
            
            # Business Health
            if net_profit > 0:
                display_text += f"\n✅ Business Health: Profitable (Net Profit: Rs. {net_profit:,.2f})"
                if profit_margin > 20:
                    display_text += " - Excellent performance! 🎉"
                elif profit_margin > 10:
                    display_text += " - Good performance! 📈"
                else:
                    display_text += " - Moderate performance 📊"
            else:
                display_text += f"\n⚠️ Business Health: Loss Making (Net Loss: Rs. {abs(net_profit):,.2f}) - Review expenses and pricing"
            
            text_widget = tk.Text(self.summary_frame, font=("Courier", 9), bg="white", fg="#1a1a2e", wrap="none")
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", display_text)
            text_widget.config(state="disabled")
            
        except Exception as e:
            tk.Label(self.summary_frame, text=f"Error: {str(e)}", font=("Arial", 12), bg="white", fg="red").pack(expand=True)
    def export_business_summary_csv(self):
        """Export business summary to CSV file"""
        year = self.summary_year.get()
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title=f"Save Business Summary {year}"
            )
            if not file_path:
                return
            
            # Get data
            sales_total = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime('%Y', sale_date) = ?", (year,))[0] or 0
            sales_returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'SALE' AND strftime('%Y', return_date) = ?", (year,))[0] or 0
            transfers_total = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE strftime('%Y', transfer_date) = ? AND payment_status = 'Paid'", (year,))[0] or 0
            total_purchases = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases WHERE strftime('%Y', purchase_date) = ?", (year,))[0] or 0
            purchase_returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'PURCHASE' AND strftime('%Y', return_date) = ?", (year,))[0] or 0
            total_expenses = self.fetch_one("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y', expense_date) = ?", (year,))[0] or 0
            
            net_sales = sales_total - sales_returns
            net_purchases = total_purchases - purchase_returns
            total_revenue = net_sales + transfers_total
            gross_profit = total_revenue - net_purchases
            net_profit = gross_profit - total_expenses
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([f"Business Summary - {year}"])
                writer.writerow([])
                writer.writerow(["Financial Summary"])
                writer.writerow(["Metric", "Amount (Rs.)"])
                writer.writerow(["Sales Revenue", sales_total])
                writer.writerow(["Sales Returns", sales_returns])
                writer.writerow(["Net Sales", net_sales])
                writer.writerow(["Transfer Revenue", transfers_total])
                writer.writerow(["Total Revenue", total_revenue])
                writer.writerow(["Total Purchases", total_purchases])
                writer.writerow(["Purchase Returns", purchase_returns])
                writer.writerow(["Net COGS", net_purchases])
                writer.writerow(["Gross Profit", gross_profit])
                writer.writerow(["Operating Expenses", total_expenses])
                writer.writerow(["Net Profit", net_profit])
                writer.writerow([])
                writer.writerow(["Monthly Breakdown"])
                writer.writerow(["Month", "Sales", "Returns", "Net Sales", "Purchases", "Expenses", "Profit"])
                
                months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                for month_num, month_name in enumerate(months, 1):
                    month_str = f"{month_num:02d}"
                    sales = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE strftime('%Y', sale_date) = ? AND strftime('%m', sale_date) = ?", (year, month_str))[0] or 0
                    returns = self.fetch_one("SELECT COALESCE(SUM(refund_amount), 0) FROM returns WHERE return_type = 'SALE' AND strftime('%Y', return_date) = ? AND strftime('%m', return_date) = ?", (year, month_str))[0] or 0
                    transfers = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM stock_transfers WHERE strftime('%Y', transfer_date) = ? AND strftime('%m', transfer_date) = ? AND payment_status = 'Paid'", (year, month_str))[0] or 0
                    purchases = self.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases WHERE strftime('%Y', purchase_date) = ? AND strftime('%m', purchase_date) = ?", (year, month_str))[0] or 0
                    expenses = self.fetch_one("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y', expense_date) = ? AND strftime('%m', expense_date) = ?", (year, month_str))[0] or 0
                    net_sales_month = sales - returns
                    profit = (net_sales_month + transfers) - purchases - expenses
                    
                    writer.writerow([month_name, sales, returns, net_sales_month, purchases, expenses, profit])
            
            messagebox.showinfo("Success", f"Business summary exported to:\n{file_path}")
            self.update_status(f"📥 Exported business summary for {year}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")       
        
            # ========== PHASE 10: BACKUP & RESTORE SYSTEM ==========
    
    def show_backup_restore(self):
        """Show Backup & Restore interface"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_container, text="💾 Backup & Restore System", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        tk.Label(main_container, text="Protect your business data with automatic and manual backups", font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(pady=(0, 20))
        
        # Create two columns
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        right_frame = tk.Frame(main_container, bg="#f5f5f5")
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        # ===== LEFT SIDE - BACKUP SECTION =====
        backup_frame = tk.LabelFrame(left_frame, text="📤 Create Backup", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1cc88a")
        backup_frame.pack(fill="both", expand=True, pady=10)
        
        backup_inner = tk.Frame(backup_frame, bg="#f5f5f5")
        backup_inner.pack(padx=20, pady=20)
        
        tk.Label(backup_inner, text="Create a backup of your entire database:", font=("Arial", 11), bg="#f5f5f5").pack(pady=5)
        tk.Label(backup_inner, text="Includes all products, sales, purchases, expenses, and ledger data", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack()
        
        # Backup options
        options_frame = tk.Frame(backup_inner, bg="#f5f5f5")
        options_frame.pack(pady=15)
        
        self.backup_with_date = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Include date in filename", variable=self.backup_with_date, bg="#f5f5f5", font=("Arial", 10)).pack(anchor="w")
        
        self.backup_compress = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Create ZIP archive", variable=self.backup_compress, bg="#f5f5f5", font=("Arial", 10)).pack(anchor="w")
        
        btn_frame = tk.Frame(backup_inner, bg="#f5f5f5")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Create Manual Backup", command=self.create_backup, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10, relief="flat", cursor="hand2").pack(pady=5)
        
        # Auto Backup Settings
        auto_frame = tk.LabelFrame(backup_inner, text="⏰ Automatic Backup", font=("Arial", 11, "bold"), bg="#f5f5f5")
        auto_frame.pack(fill="x", pady=10)
        
        tk.Label(auto_frame, text="Schedule:", font=("Arial", 10), bg="#f5f5f5").pack(anchor="w", padx=10, pady=(10, 0))
        self.auto_backup_var = tk.StringVar(value="Daily")
        auto_combo = ttk.Combobox(auto_frame, textvariable=self.auto_backup_var, values=["Daily", "Weekly", "Monthly", "Never"], font=("Arial", 10), width=15, state="readonly")
        auto_combo.pack(padx=10, pady=5)
        auto_combo.bind('<<ComboboxSelected>>', lambda e: self.save_auto_backup_setting())
        
        tk.Label(auto_frame, text="Backup Location:", font=("Arial", 10), bg="#f5f5f5").pack(anchor="w", padx=10, pady=(10, 0))
        self.backup_location_var = tk.StringVar(value="backups")
        location_entry = tk.Entry(auto_frame, textvariable=self.backup_location_var, font=("Arial", 10), width=25)
        location_entry.pack(padx=10, pady=5)
        
        tk.Button(auto_frame, text="📁 Browse", command=self.select_backup_folder, bg="#36b9cc", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(pady=5)
        
        # ===== RIGHT SIDE - RESTORE SECTION =====
        restore_frame = tk.LabelFrame(right_frame, text="📥 Restore from Backup", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#e94560")
        restore_frame.pack(fill="both", expand=True, pady=10)
        
        restore_inner = tk.Frame(restore_frame, bg="#f5f5f5")
        restore_inner.pack(padx=20, pady=20)
        
        tk.Label(restore_inner, text="Select a backup file to restore:", font=("Arial", 11), bg="#f5f5f5").pack(pady=5)
        
        # Backup files list
        list_frame = tk.Frame(restore_inner, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.backup_files_listbox = tk.Listbox(list_frame, font=("Arial", 10), height=8, bg="white")
        self.backup_files_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.backup_files_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.backup_files_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        restore_btn_frame = tk.Frame(restore_inner, bg="#f5f5f5")
        restore_btn_frame.pack(pady=10)
        
        tk.Button(restore_btn_frame, text="🔄 Refresh List", command=self.refresh_backup_list, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        tk.Button(restore_btn_frame, text="⚠️ Restore Selected", command=self.restore_backup, bg="#e94560", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        
        # Warning
        warning_frame = tk.Frame(restore_inner, bg="#fff3cd", relief="ridge", bd=1)
        warning_frame.pack(fill="x", pady=10)
        tk.Label(warning_frame, text="⚠️ WARNING: Restoring will overwrite current data!", font=("Arial", 9), bg="#fff3cd", fg="#856404").pack(padx=10, pady=5)
        
        # Backup History
        history_frame = tk.LabelFrame(main_container, text="📋 Backup History", font=("Arial", 12, "bold"), bg="#f5f5f5")
        history_frame.pack(fill="x", pady=10)
        
        self.backup_history_text = tk.Text(history_frame, height=5, font=("Courier", 9), bg="#f5f5f5", fg="#666")
        self.backup_history_text.pack(fill="x", padx=10, pady=10)
        
        # Load backup list and history
        self.refresh_backup_list()
        self.load_backup_history()
        
        # Check for scheduled backup on startup
        self.check_scheduled_backup()
        # ========== PHASE 12: COMPLETE RETURN MANAGEMENT SYSTEM ==========
    
    def show_returns(self):
        """Main Returns Management Interface"""
        # Auto fix to ensure data consistency
        self.auto_fix_old_products_for_sale()
        
        self.clear_main_content()
        
        # Create Notebook for different return types
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Purchase Return (Supplier ko wapas)
        purchase_return_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(purchase_return_tab, text="📤 Purchase Return (Supplier)")
        self.create_purchase_return_tab(purchase_return_tab)
        
        # Tab 2: Sale Return (Customer sy wapas)
        sale_return_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(sale_return_tab, text="📥 Sale Return (Customer)")
        self.create_sale_return_tab(sale_return_tab)

        
        # Tab 3: Transfer Return (City sy wapas)
        transfer_return_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(transfer_return_tab, text="🔄 Transfer Return")
        self.create_transfer_return_tab(transfer_return_tab)
        
        # Tab 4: Receive Payment (Pending/Partial ko update)
        payment_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(payment_tab, text="💰 Receive Payment")
        self.create_payment_receive_tab(payment_tab)
        
                # Tab 5: Shop Return
        shop_return_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(shop_return_tab, text="🏪 Shop Return")
        self.create_shop_return_tab(shop_return_tab)
    def create_shop_return_tab(self, parent):
        """Shop Return Tab - Right Click Context Menu with Pack/Piece Window"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="🏪 SHOP RETURN (FROM FRONT SHOP)", 
                font=("Helvetica", 20, "bold"), bg="#f5f5f5", fg="#f6c23e").pack(pady=5)
        
        # Main Frame - All Shop Transfers List
        list_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="📋 ALL SHOP TRANSFERS", font=("Arial", 14, "bold"), 
                bg="#f6c23e", fg="white", pady=8).pack(fill="x")
        
        # Search
        search_frame = tk.Frame(list_frame, bg="white", padx=10, pady=5)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 10), bg="white").pack(side="left")
        self.shop_return_search = tk.Entry(search_frame, font=("Arial", 10), width=30)
        self.shop_return_search.pack(side="left", padx=5)
        self.shop_return_search.bind("<KeyRelease>", lambda e: self.load_all_shop_transfers())
        
        # Treeview
        tree_frame = tk.Frame(list_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Transfer No", "Date", "Recipient", "Total Amount", "Status", "Items")
        self.shop_transfer_list_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.shop_transfer_list_tree.heading("ID", text="ID", anchor="center")
        self.shop_transfer_list_tree.heading("Transfer No", text="Transfer No", anchor="center")
        self.shop_transfer_list_tree.heading("Date", text="Date", anchor="center")
        self.shop_transfer_list_tree.heading("Recipient", text="Recipient", anchor="center")
        self.shop_transfer_list_tree.heading("Total Amount", text="Total Amount (Rs.)", anchor="center")
        self.shop_transfer_list_tree.heading("Status", text="Status", anchor="center")
        self.shop_transfer_list_tree.heading("Items", text="Items", anchor="center")
        
        self.shop_transfer_list_tree.column("ID", width=50, anchor="center")
        self.shop_transfer_list_tree.column("Transfer No", width=130, anchor="center")
        self.shop_transfer_list_tree.column("Date", width=100, anchor="center")
        self.shop_transfer_list_tree.column("Recipient", width=150, anchor="w")
        self.shop_transfer_list_tree.column("Total Amount", width=120, anchor="e")
        self.shop_transfer_list_tree.column("Status", width=80, anchor="center")
        self.shop_transfer_list_tree.column("Items", width=80, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.shop_transfer_list_tree.yview)
        self.shop_transfer_list_tree.configure(yscrollcommand=vsb.set)
        self.shop_transfer_list_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Right Click Menu
        self.shop_transfer_context_menu = tk.Menu(self.root, tearoff=0)
        self.shop_transfer_context_menu.add_command(label="🔄 Return Items", command=self.open_shop_return_window)
        
        self.shop_transfer_list_tree.bind("<Button-3>", self.show_shop_transfer_context_menu)
        
        # Load all shop transfers
        self.load_all_shop_transfers()
    
    def load_all_shop_transfers(self):
        """Load all shop transfers into treeview"""
        for item in self.shop_transfer_list_tree.get_children():
            self.shop_transfer_list_tree.delete(item)
        
        search = self.shop_return_search.get().strip() if hasattr(self, 'shop_return_search') else ""
        
        try:
            if search:
                query = """
                    SELECT st.id, st.transfer_no, st.transfer_date, st.recipient_name, 
                           st.total_amount, st.payment_status,
                           (SELECT COUNT(*) FROM shop_transfer_items WHERE transfer_id = st.id) as item_count
                    FROM shop_transfers st
                    WHERE st.transfer_no LIKE ? OR st.recipient_name LIKE ?
                    ORDER BY st.id DESC
                """
                params = (f'%{search}%', f'%{search}%')
            else:
                query = """
                    SELECT st.id, st.transfer_no, st.transfer_date, st.recipient_name, 
                           st.total_amount, st.payment_status,
                           (SELECT COUNT(*) FROM shop_transfer_items WHERE transfer_id = st.id) as item_count
                    FROM shop_transfers st
                    ORDER BY st.id DESC
                """
                params = ()
            
            transfers = self.fetch_all(query, params)
            for t in transfers:
                self.shop_transfer_list_tree.insert("", "end", values=(
                    t[0], t[1], t[2][:10] if t[2] else "-", t[3] or "-", 
                    f"Rs. {t[4]:,.2f}", t[5] or "Pending", t[6]
                ))
            
            self.update_status(f"Loaded {len(transfers)} shop transfers")
        except Exception as e:
            self.update_status(f"Error loading shop transfers: {str(e)}")
    
    def show_shop_transfer_context_menu(self, event):
        """Show right click context menu for shop transfers"""
        item = self.shop_transfer_list_tree.identify_row(event.y)
        if item:
            self.shop_transfer_list_tree.selection_set(item)
            self.shop_transfer_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_shop_transfer_for_return(self):
        """Get selected shop transfer ID"""
        selected = self.shop_transfer_list_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a shop transfer first!")
            return None
        item = self.shop_transfer_list_tree.item(selected[0])
        return item['values'][0]
    
    def open_shop_return_window(self):
        """Open return window for selected shop transfer"""
        transfer_id = self.get_selected_shop_transfer_for_return()
        if not transfer_id:
            return
        
        # Get transfer details
        transfer = self.fetch_one("""
            SELECT st.id, st.transfer_no, st.recipient_name, st.transfer_date, st.total_amount
            FROM shop_transfers st
            WHERE st.id = ?
        """, (transfer_id,))
        
        if not transfer:
            messagebox.showerror("Error", "Shop transfer not found!")
            return
        
        # Get all items from this transfer
        items = self.fetch_all("""
            SELECT sti.product_id, p.name, sti.quantity, sti.price,
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, sti.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM shop_transfer_items sti
            JOIN products p ON sti.product_id = p.id
            WHERE sti.transfer_id = ?
        """, (transfer_id,))
        
        if not items:
            messagebox.showwarning("Error", "No items found in this shop transfer!")
            return
        
        # Create Return Window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Return Items - {transfer[1]} ({transfer[2]})")
        dialog.geometry("750x600")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"🏪 SHOP RETURN", font=("Helvetica", 16, "bold"),
                bg="#1a1a2e", fg="#f6c23e").pack(pady=(10, 0))
        tk.Label(header_frame, text=f"Transfer: {transfer[1]} | Recipient: {transfer[2] or '-'} | Date: {transfer[3][:10]}",
                font=("Arial", 10), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # Main scrollable area for items
        canvas_container = tk.Frame(dialog, bg="#f5f5f5")
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Header Row
        header_row = tk.Frame(scroll_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Product", 22), ("Transferred Qty", 8), ("Pack Price", 12), 
                   ("Piece Price", 12), ("Packs Return", 6), ("Pieces Return", 6), ("Refund", 12)]
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Arial", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        return_items_data = []
        
        for idx, item in enumerate(items):
            product_id = item[0]
            product_name = item[1]
            transferred_qty = item[2]
            transfer_price = item[3]
            pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
            pack_price = item[5] if item[5] and item[5] > 0 else transfer_price * pieces_per_pack
            piece_price = pack_price / pieces_per_pack if pieces_per_pack > 0 else transfer_price
            
            row = tk.Frame(scroll_frame, bg="white", relief="ridge", bd=1)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=product_name[:22], width=22, bg="white", anchor="w", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=str(transferred_qty), width=8, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            
            pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            pack_entry.pack(side="left", padx=2)
            pack_entry.insert(0, "0")
            
            piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            
            refund_label = tk.Label(row, text="Rs.0", width=12, bg="white", anchor="center",
                                    font=("Arial", 9, "bold"), fg="#f6c23e")
            refund_label.pack(side="left", padx=2)
            
            item_data = {
                'product_id': product_id, 'name': product_name,
                'pack_entry': pack_entry, 'piece_entry': piece_entry,
                'refund_label': refund_label, 'pack_price': pack_price,
                'piece_price': piece_price, 'pieces_per_pack': pieces_per_pack,
                'max_qty': transferred_qty
            }
            return_items_data.append(item_data)
            
            pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_shop_return_refund(return_items_data[i]))
            piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_shop_return_refund(return_items_data[i]))
        
        # Total Refund Frame
        total_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        total_inner = tk.Frame(total_frame, bg="white", padx=15, pady=10)
        total_inner.pack()
        
        tk.Label(total_inner, text="💰 TOTAL REFUND:", font=("Arial", 16, "bold"),
                bg="white", fg="#f6c23e").pack(side="left", padx=10)
        total_refund_label = tk.Label(total_inner, text="Rs. 0.00", font=("Arial", 18, "bold"),
                                      bg="white", fg="#f6c23e")
        total_refund_label.pack(side="left", padx=10)
        
        def calculate_total():
            total = 0
            for itm in return_items_data:
                try:
                    packs = int(itm['pack_entry'].get() or 0)
                    pieces = int(itm['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pcs = (packs * itm['pieces_per_pack']) + pieces
                        if total_pcs <= itm['max_qty']:
                            total += (packs * itm['pack_price']) + (pieces * itm['piece_price'])
                except:
                    pass
            total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        dialog.calculate_total = calculate_total
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="✅ COMPLETE SHOP RETURN", 
                 command=lambda: self.execute_shop_return(transfer_id, transfer[1], return_items_data, total_refund_label, dialog),
                 bg="#f6c23e", fg="white", font=("Arial", 12, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy,
                 bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        calculate_total()
    
    def update_shop_return_refund(self, item):
        """Update refund for a single shop return item - Packs + Pieces both work together"""
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Total pieces = (packs * pieces_per_pack) + extra pieces
            total_pcs = (packs * item['pieces_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text=f"Max {item['max_qty']}", fg="red")
            elif total_pcs == 0:
                item['refund_label'].config(text="Rs.0", fg="#f6c23e")
            else:
                # Calculate refund: (packs * pack_price) + (pieces * piece_price)
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                # Show what was returned
                if packs > 0 and pieces > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk+{pieces}pcs)", fg="#f6c23e")
                elif packs > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk)", fg="#f6c23e")
                else:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({pieces}pcs)", fg="#f6c23e")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        # Find parent window and update total
        try:
            dialog = item['refund_label'].winfo_toplevel()
            if hasattr(dialog, 'calculate_total'):
                dialog.calculate_total()
        except:
            pass
    
    def execute_shop_return(self, transfer_id, transfer_no, return_items_data, total_label, dialog):
        """Execute the shop return - Stock INCREASE and Payment AUTO-UPDATE"""
        return_items = []
        total_refund = 0
        
        for item in return_items_data:
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                if packs > 0 or pieces > 0:
                    total_pcs = (packs * item['pieces_per_pack']) + pieces
                    if total_pcs > item['max_qty']:
                        messagebox.showwarning("Invalid Quantity", 
                            f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                        return
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    return_items.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': total_pcs,
                        'total': refund,
                        'packs': packs,
                        'pieces': pieces
                    })
                    total_refund += refund
            except:
                pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please enter quantity to return!")
            return
        
        # Get current transfer details for payment update
        transfer = self.fetch_one("""
            SELECT id, transfer_no, total_amount, amount_paid, balance_due, payment_status
            FROM shop_transfers WHERE id = ?
        """, (transfer_id,))
        
        if not transfer:
            messagebox.showerror("Error", "Shop transfer not found!")
            return
        
        current_total = transfer[2] or 0
        current_paid = transfer[3] or 0
        current_balance = transfer[4] or 0
        
        # Calculate new values after return
        new_total = current_total - total_refund
        new_balance = current_balance - total_refund
        
        if new_balance <= 0:
            new_status = "Paid"
            new_paid = new_total
            new_balance = 0
        elif new_balance > 0 and current_paid > 0:
            new_status = "Partial"
            new_paid = current_paid
        else:
            new_status = "Pending"
            new_paid = 0
        
        confirm_msg = f"🏪 SHOP RETURN\n\nTransfer: {transfer_no}\n"
        confirm_msg += f"Original Total: Rs. {current_total:,.2f}\n"
        confirm_msg += f"Return Amount: Rs. {total_refund:,.2f}\n"
        confirm_msg += f"New Total: Rs. {new_total:,.2f}\n"
        confirm_msg += f"New Balance: Rs. {new_balance:,.2f}\n"
        confirm_msg += f"Payment Status: {new_status}\n\n"
        confirm_msg += "Items:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['packs']} pack + {item['pieces']} pcs = {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'SHOP_RETURN' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                new_num = int(parts[-1]) + 1 if len(parts) >= 3 else 1
            else:
                new_num = 1
            
            return_no = f"RET-SHP-{new_num:03d}"
            reason = "Return from Front Shop"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("SHOP_RETURN", return_no, transfer_id, item['product_id'], 
                      item['quantity'], item['total'], reason))
                
                # Stock INCREASE - mal wapas aa raha hai
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # UPDATE SHOP TRANSFER PAYMENT STATUS
            cursor.execute("""
                UPDATE shop_transfers 
                SET total_amount = ?, amount_paid = ?, balance_due = ?, payment_status = ?
                WHERE id = ?
            """, (new_total, new_paid, new_balance, new_status, transfer_id))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("SHOP_RETURN", return_no, f"Return from Front Shop: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "SHOP_RETURN", transfer_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Shop return processed!\n\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\n"
                f"Return Amount: Rs. {total_refund:,.2f}\n"
                f"New Transfer Total: Rs. {new_total:,.2f}\n"
                f"Payment Status: {new_status}\n"
                f"Balance Due: Rs. {new_balance:,.2f}")
            
            dialog.destroy()
            
            # Refresh all lists
            self.load_all_shop_transfers()
             
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_shop_transfers_for_return(self):
        """Load shop transfers for return selection - SAFE with search"""
        for item in self.shop_return_tree.get_children():
            self.shop_return_tree.delete(item)
        
        search_term = self.shop_return_search.get().strip() if hasattr(self, 'shop_return_search') else ""
        
        try:
            if search_term:
                query = """
                    SELECT id, transfer_no, transfer_date, recipient_name, total_amount, payment_status
                    FROM shop_transfers
                    WHERE transfer_no LIKE ? OR recipient_name LIKE ?
                    ORDER BY id DESC
                """
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = """
                    SELECT id, transfer_no, transfer_date, recipient_name, total_amount, payment_status
                    FROM shop_transfers
                    ORDER BY id DESC
                """
                params = ()
            
            transfers = self.fetch_all(query, params)
            
            for transfer in transfers:
                self.shop_return_tree.insert("", "end", values=(
                    transfer[0], transfer[1], transfer[2][:10] if transfer[2] else "-",
                    transfer[3] or "-", f"Rs. {transfer[4]:,.2f}", transfer[5]
                ))
        except:
            # Table doesn't exist yet
            pass
        # Tab 6: Return History
        history_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(history_tab, text="📜 Return History")
        self.create_return_history_tab(history_tab)
        # ========== BASE RETURN METHOD (COMMON FOR ALL) ==========
    def create_return_items_panel(self, parent, items_data, update_callback):
        """Create common return items panel with checkboxes and pack/piece inputs - WITH BOTH SCROLLBARS"""
        
        # Clear previous
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Store items and callbacks
        self.return_items_data = []
        self.return_update_callback = update_callback
        
        # Create frame with both scrollbars
        main_container = tk.Frame(parent, bg="white")
        main_container.pack(fill="both", expand=True)
        
        # Canvas with both scrollbars
        canvas = tk.Canvas(main_container, bg="white", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(main_container, orient="horizontal", command=canvas.xview)
        v_scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create header
        header = tk.Frame(scrollable_frame, bg="#e0e0e0", height=35)
        header.pack(fill="x", pady=(0, 5))
        
        # Header columns
        tk.Label(header, text="Select", width=8, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Product Name", width=30, bg="#e0e0e0", font=("Arial", 9, "bold"), anchor="w").pack(side="left", padx=2)
        tk.Label(header, text="Original Qty", width=12, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Pack Price", width=12, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Piece Price", width=12, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Packs", width=8, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Pieces", width=8, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Refund (Rs.)", width=12, bg="#e0e0e0", font=("Arial", 9, "bold")).pack(side="left", padx=2)
        
        # Add items
        for idx, item in enumerate(items_data):
            self.add_return_item_row(scrollable_frame, idx, item)
    
    
    def update_item_refund(self, idx):
        """Update refund amount for a single item"""
        item = self.return_items_data[idx]
        
        if not item['var'].get():
            item['refund_label'].config(text="Rs. 0")
            if self.return_update_callback:
                self.return_update_callback()
            return
        
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            total_pieces = (packs * item['pieces_per_pack']) + pieces
            
            if total_pieces > item['max_qty']:
                item['refund_label'].config(text="EXCEEDS", fg="red")
            else:
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
            
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        if self.return_update_callback:
            self.return_update_callback()
    
    def add_return_item_row(self, parent, idx, item):
        """Add a single item row with checkbox and pack/piece inputs"""
        
        row = tk.Frame(parent, bg="white", relief="ridge", bd=1)
        row.pack(fill="x", pady=2)
        
        # Checkbox
        var = tk.BooleanVar()
        cb = tk.Checkbutton(row, variable=var, bg="white", command=self.calculate_return_total)
        cb.pack(side="left", padx=5)
        
        # Product name (wider)
        name_label = tk.Label(row, text=item['name'][:30], bg="white", anchor="w", width=30, font=("Arial", 9))
        name_label.pack(side="left", padx=2)
        
        # Original quantity
        qty_label = tk.Label(row, text=f"{item['original_qty']} pcs", bg="white", width=12, font=("Arial", 9))
        qty_label.pack(side="left", padx=2)
        
        # Pack price
        pack_price_label = tk.Label(row, text=f"Rs.{item['pack_price']:.0f}", bg="white", width=12, font=("Arial", 9))
        pack_price_label.pack(side="left", padx=2)
        
        # Piece price
        piece_price_label = tk.Label(row, text=f"Rs.{item['piece_price']:.2f}", bg="white", width=12, font=("Arial", 9))
        piece_price_label.pack(side="left", padx=2)
        
        # Packs entry
        pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        pack_entry.pack(side="left", padx=2)
        pack_entry.insert(0, "0")
        
        # Pieces entry
        piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        piece_entry.pack(side="left", padx=2)
        piece_entry.insert(0, "0")
        
        # Refund label
        refund_label = tk.Label(row, text="Rs. 0", bg="white", width=12, font=("Arial", 9, "bold"), fg="#e94560")
        refund_label.pack(side="left", padx=2)
        
        # Store item data
        item_data = {
            'var': var,
            'pack_entry': pack_entry,
            'piece_entry': piece_entry,
            'refund_label': refund_label,
            'product_id': item['product_id'],
            'name': item['name'],
            'pack_price': item['pack_price'],
            'piece_price': item['piece_price'],
            'pieces_per_pack': item['pieces_per_pack'],
            'max_qty': item['original_qty']
        }
        
        self.return_items_data.append(item_data)
        
        # Bind events
        def on_change(e, idx=idx):
            self.update_item_refund(idx)
        
        pack_entry.bind("<KeyRelease>", on_change)
        piece_entry.bind("<KeyRelease>", on_change)
        cb.config(command=lambda: self.update_item_refund(idx))
    
    def add_return_item_row(self, parent, idx, item):
        """Add a single item row with checkbox and pack/piece inputs"""
        
        row = tk.Frame(parent, bg="white", relief="ridge", bd=1)
        row.pack(fill="x", pady=2)
        
        # Checkbox
        var = tk.BooleanVar()
        cb = tk.Checkbutton(row, variable=var, bg="white", command=self.calculate_return_total)
        cb.pack(side="left", padx=5)
        
        # Product name
        name_label = tk.Label(row, text=item['name'][:25], bg="white", anchor="w", width=25, font=("Arial", 9))
        name_label.pack(side="left", padx=2)
        
        # Original quantity
        qty_label = tk.Label(row, text=f"{item['original_qty']} pcs", bg="white", width=10, font=("Arial", 9))
        qty_label.pack(side="left", padx=2)
        
        # Pack price
        pack_price_label = tk.Label(row, text=f"Rs.{item['pack_price']:.0f}", bg="white", width=10, font=("Arial", 9))
        pack_price_label.pack(side="left", padx=2)
        
        # Piece price
        piece_price_label = tk.Label(row, text=f"Rs.{item['piece_price']:.2f}", bg="white", width=10, font=("Arial", 9))
        piece_price_label.pack(side="left", padx=2)
        
        # Packs entry
        pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        pack_entry.pack(side="left", padx=2)
        pack_entry.insert(0, "0")
        
        # Pieces entry
        piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        piece_entry.pack(side="left", padx=2)
        piece_entry.insert(0, "0")
        
        # Refund label
        refund_label = tk.Label(row, text="Rs. 0", bg="white", width=10, font=("Arial", 9, "bold"), fg="#e94560")
        refund_label.pack(side="left", padx=2)
        
        # Store item data
        item_data = {
            'var': var,
            'pack_entry': pack_entry,
            'piece_entry': piece_entry,
            'refund_label': refund_label,
            'product_id': item['product_id'],
            'name': item['name'],
            'pack_price': item['pack_price'],
            'piece_price': item['piece_price'],
            'pieces_per_pack': item['pieces_per_pack'],
            'max_qty': item['original_qty']
        }
        
        self.return_items_data.append(item_data)
        
        # Bind events
        pack_entry.bind("<KeyRelease>", lambda e: self.update_item_refund(idx))
        piece_entry.bind("<KeyRelease>", lambda e: self.update_item_refund(idx))
    
    def update_item_refund(self, idx):
        """Update refund amount for a single item"""
        item = self.return_items_data[idx]
        
        if not item['var'].get():
            item['refund_label'].config(text="Rs. 0")
            self.calculate_return_total()
            return
        
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Calculate total pieces
            total_pieces = (packs * item['pieces_per_pack']) + pieces
            
            # Validate
            if total_pieces > item['max_qty']:
                item['refund_label'].config(text="⚠️ EXCEEDS", fg="red")
                self.calculate_return_total()
                return
            
            # Calculate refund
            refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
            item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
            
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        self.calculate_return_total()
    
    def calculate_return_total(self):
        """Calculate total refund from all selected items"""
        total = 0
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        
        if hasattr(self, 'total_refund_label'):
            self.total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        return total
    def create_purchase_return_tab(self, parent):
        """Purchase Return Tab - Right Click Context Menu with Pack/Piece Window"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="📤 PURCHASE RETURN (TO SUPPLIER)", 
                font=("Helvetica", 20, "bold"), bg="#f5f5f5", fg="#e94560").pack(pady=5)
        
        # Main Frame - All Purchases List
        list_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="📋 ALL PURCHASES", font=("Arial", 14, "bold"), 
                bg="#e94560", fg="white", pady=8).pack(fill="x")
        
        # Search
        search_frame = tk.Frame(list_frame, bg="white", padx=10, pady=5)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 10), bg="white").pack(side="left")
        self.pur_return_search = tk.Entry(search_frame, font=("Arial", 10), width=30)
        self.pur_return_search.pack(side="left", padx=5)
        self.pur_return_search.bind("<KeyRelease>", lambda e: self.load_all_purchases())
        
        # Treeview
        tree_frame = tk.Frame(list_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Invoice No", "Date", "Supplier", "Total Amount", "Items")
        self.purchase_list_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.purchase_list_tree.heading("ID", text="ID", anchor="center")
        self.purchase_list_tree.heading("Invoice No", text="Invoice No", anchor="center")
        self.purchase_list_tree.heading("Date", text="Date", anchor="center")
        self.purchase_list_tree.heading("Supplier", text="Supplier", anchor="center")
        self.purchase_list_tree.heading("Total Amount", text="Total Amount (Rs.)", anchor="center")
        self.purchase_list_tree.heading("Items", text="Items", anchor="center")
        
        self.purchase_list_tree.column("ID", width=50, anchor="center")
        self.purchase_list_tree.column("Invoice No", width=130, anchor="center")
        self.purchase_list_tree.column("Date", width=100, anchor="center")
        self.purchase_list_tree.column("Supplier", width=180, anchor="w")
        self.purchase_list_tree.column("Total Amount", width=120, anchor="e")
        self.purchase_list_tree.column("Items", width=80, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.purchase_list_tree.yview)
        self.purchase_list_tree.configure(yscrollcommand=vsb.set)
        self.purchase_list_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Right Click Menu
        self.purchase_context_menu = tk.Menu(self.root, tearoff=0)
        self.purchase_context_menu.add_command(label="🔄 Return Items", command=self.open_return_window)
        
        self.purchase_list_tree.bind("<Button-3>", self.show_purchase_context_menu)
        
        # Load all purchases
        self.load_all_purchases()
    
    def load_all_purchases(self):
        """Load all purchases into treeview"""
        for item in self.purchase_list_tree.get_children():
            self.purchase_list_tree.delete(item)
        
        search = self.pur_return_search.get().strip() if hasattr(self, 'pur_return_search') else ""
        
        if search:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount,
                       (SELECT COUNT(*) FROM purchase_items WHERE purchase_id = p.id) as item_count
                FROM purchases p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.invoice_no LIKE ? OR s.name LIKE ?
                ORDER BY p.id DESC
            """
            params = (f'%{search}%', f'%{search}%')
        else:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount,
                       (SELECT COUNT(*) FROM purchase_items WHERE purchase_id = p.id) as item_count
                FROM purchases p
                JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.id DESC
            """
            params = ()
        
        purchases = self.fetch_all(query, params)
        for p in purchases:
            self.purchase_list_tree.insert("", "end", values=(
                p[0], p[1], p[2][:10] if p[2] else "-", p[3], f"Rs. {p[4]:,.2f}", p[5]
            ))
        
        self.update_status(f"Loaded {len(purchases)} purchases")
    
    def show_purchase_context_menu(self, event):
        """Show right click context menu"""
        item = self.purchase_list_tree.identify_row(event.y)
        if item:
            self.purchase_list_tree.selection_set(item)
            self.purchase_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_purchase_for_return(self):
        """Get selected purchase ID"""
        selected = self.purchase_list_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a purchase first!")
            return None
        item = self.purchase_list_tree.item(selected[0])
        return item['values'][0]
    
    def open_return_window(self):
        """Open return window for selected purchase"""
        purchase_id = self.get_selected_purchase_for_return()
        if not purchase_id:
            return
        
        # Get purchase details
        purchase = self.fetch_one("""
            SELECT p.id, p.invoice_no, s.name, p.purchase_date, p.total_amount
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        """, (purchase_id,))
        
        if not purchase:
            messagebox.showerror("Error", "Purchase not found!")
            return
        
        # Get all items from this purchase
        items = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price,
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, pi.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        if not items:
            messagebox.showwarning("Error", "No items found in this purchase!")
            return
        
        # Create Return Window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Return Items - {purchase[1]} ({purchase[2]})")
        dialog.geometry("750x600")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"📤 PURCHASE RETURN", font=("Helvetica", 16, "bold"),
                bg="#1a1a2e", fg="#e94560").pack(pady=(10, 0))
        tk.Label(header_frame, text=f"Invoice: {purchase[1]} | Supplier: {purchase[2]} | Date: {purchase[3][:10]}",
                font=("Arial", 10), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # Main scrollable area for items
        canvas_container = tk.Frame(dialog, bg="#f5f5f5")
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Header Row in scrollable area
        header_row = tk.Frame(scroll_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Product", 22), ("Purchased Qty", 10), ("Pack Price", 12), 
                   ("Piece Price", 12), ("Packs Return", 8), ("Pieces Return", 8), 
                   ("Refund (Rs.)", 12)]
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Arial", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        # Store item widgets
        return_items_data = []
        
        for idx, item in enumerate(items):
            product_id = item[0]
            product_name = item[1]
            purchased_qty = item[2]
            purchase_price = item[3]
            pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
            pack_price = item[5] if item[5] and item[5] > 0 else purchase_price * pieces_per_pack
            unit_type = item[6] if len(item) > 6 else "Piece"
            
            # Calculate piece price
            piece_price = pack_price / pieces_per_pack if pieces_per_pack > 0 else purchase_price
            
            # Row frame
            row = tk.Frame(scroll_frame, bg="white", relief="ridge", bd=1)
            row.pack(fill="x", pady=2)
            
            # Product Name
            tk.Label(row, text=product_name[:22], width=22, bg="white", anchor="w",
                    font=("Arial", 9)).pack(side="left", padx=2)
            
            # Purchased Quantity
            tk.Label(row, text=str(purchased_qty), width=10, bg="white", anchor="center",
                    font=("Arial", 9)).pack(side="left", padx=2)
            
            # Pack Price
            tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", anchor="center",
                    font=("Arial", 9)).pack(side="left", padx=2)
            
            # Piece Price (calculated)
            tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", anchor="center",
                    font=("Arial", 9)).pack(side="left", padx=2)
            
            # Packs Entry
            pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            pack_entry.pack(side="left", padx=2)
            pack_entry.insert(0, "0")
            
            # Pieces Entry
            piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            
            # Refund Label
            refund_label = tk.Label(row, text="Rs.0", width=12, bg="white", anchor="center",
                                    font=("Arial", 9, "bold"), fg="#e94560")
            refund_label.pack(side="left", padx=2)
            
            # Store item data
            item_data = {
                'product_id': product_id,
                'name': product_name,
                'pack_entry': pack_entry,
                'piece_entry': piece_entry,
                'refund_label': refund_label,
                'pack_price': pack_price,
                'piece_price': piece_price,
                'pieces_per_pack': pieces_per_pack,
                'max_qty': purchased_qty,
                'idx': idx
            }
            return_items_data.append(item_data)
            
            
            pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_return_refund(return_items_data[i]))
            piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_return_refund(return_items_data[i]))
        
        # Total Refund Frame
        total_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        total_inner = tk.Frame(total_frame, bg="white", padx=15, pady=10)
        total_inner.pack()
        
        tk.Label(total_inner, text="💰 TOTAL REFUND:", font=("Arial", 16, "bold"),
                bg="white", fg="#e94560").pack(side="left", padx=10)
        
        total_refund_label = tk.Label(total_inner, text="Rs. 0.00", font=("Arial", 18, "bold"),
                                      bg="white", fg="#e94560")
        total_refund_label.pack(side="left", padx=10)
        
        # Store total label in dialog for access
        dialog.total_refund_label = total_refund_label
        dialog.return_items_data = return_items_data
        
        # Function to calculate total refund
        def calculate_total():
            total = 0
            for item in return_items_data:
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pcs = (packs * item['pieces_per_pack']) + pieces
                        if total_pcs <= item['max_qty']:
                            total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
            total_refund_label.config(text=f"Rs. {total:,.2f}")
            return total
        
        # Update function for each item
        def update_refund(item):
            if not hasattr(item, 'pack_entry'):
                return
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                total_pcs = (packs * item['pieces_per_pack']) + pieces
                
                if total_pcs > item['max_qty']:
                    item['refund_label'].config(text="EXCEEDS", fg="red")
                elif total_pcs == 0:
                    item['refund_label'].config(text="Rs.0", fg="#e94560")
                else:
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
            except:
                item['refund_label'].config(text="Invalid", fg="red")
            calculate_total()
        
        # Store functions in dialog for access
        dialog.update_refund = update_refund
        dialog.calculate_total = calculate_total
        
        # Buttons Frame
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="✅ COMPLETE RETURN", 
                 command=lambda: self.execute_purchase_return(purchase_id, purchase[1], return_items_data, total_refund_label, dialog),
                 bg="#e94560", fg="white", font=("Arial", 12, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy,
                 bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        # Calculate initial total
        calculate_total()
    
    def update_return_refund(self, item):
        """Update refund for a single item - Packs + Pieces both work together"""
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Total pieces = (packs * pieces_per_pack) + extra pieces
            total_pcs = (packs * item['pieces_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text=f"Max {item['max_qty']}", fg="red")
            elif total_pcs == 0:
                item['refund_label'].config(text="Rs.0", fg="#e94560")
            else:
                # Calculate refund: (packs * pack_price) + (pieces * piece_price)
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        # Find parent window and update total
        try:
            dialog = item['refund_label'].winfo_toplevel()
            if hasattr(dialog, 'calculate_total'):
                dialog.calculate_total()
        except:
            pass
    
    def execute_purchase_return(self, purchase_id, invoice_no, return_items_data, total_label, dialog):
        """Execute the purchase return"""
        # Collect items to return
        return_items = []
        total_refund = 0
        
        for item in return_items_data:
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                if packs > 0 or pieces > 0:
                    total_pcs = (packs * item['pieces_per_pack']) + pieces
                    if total_pcs > item['max_qty']:
                        messagebox.showwarning("Invalid Quantity", 
                            f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                        return
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    return_items.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': total_pcs,
                        'total': refund,
                        'packs': packs,
                        'pieces': pieces
                    })
                    total_refund += refund
            except:
                pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please enter quantity to return!")
            return
        
        # Confirmation
        confirm_msg = f"📤 PURCHASE RETURN\n\nInvoice: {invoice_no}\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['packs']} pack + {item['pieces']} pcs = {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'PURCHASE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                new_num = int(parts[-1]) + 1 if len(parts) >= 3 else 1
            else:
                new_num = 1
            
            return_no = f"RET-PUR-{new_num:03d}"
            reason = "Return to supplier"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, purchase_id, item['product_id'], 
                      item['quantity'], item['total'], reason))
                
                # REDUCE stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "PURCHASE", invoice_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Purchase return processed!\n\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            dialog.destroy()
            
            # Refresh purchase list
            self.load_all_purchases()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_purchase_invoices(self):
        """Load all purchase invoices for return selection"""
        for item in self.purchase_invoice_tree.get_children():
            self.purchase_invoice_tree.delete(item)
        
        search = self.pur_return_search.get().strip() if hasattr(self, 'pur_return_search') else ""
        
        if search:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
                FROM purchases p JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.invoice_no LIKE ? OR s.name LIKE ?
                ORDER BY p.id DESC LIMIT 500
            """
            params = (f'%{search}%', f'%{search}%')
        else:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
                FROM purchases p JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.id DESC LIMIT 500
            """
            params = ()
        
        purchases = self.fetch_all(query, params)
        for p in purchases:
            self.purchase_invoice_tree.insert("", "end", values=(
                p[0], p[1], p[2][:10] if p[2] else "-", p[3], f"Rs. {p[4]:,.2f}"
            ))
    
    def on_purchase_invoice_click(self, event):
        """When invoice clicked, load its items with Pack/Piece options"""
        selected = self.purchase_invoice_tree.selection()
        if not selected:
            return
        
        item = self.purchase_invoice_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier = item['values'][3]
        
        self.selected_purchase_label.config(text=f"Invoice: {invoice_no} | Supplier: {supplier}")
        self.current_return_purchase_id = purchase_id
        self.current_return_purchase_total = float(item['values'][4].replace('Rs. ', '').replace(',', ''))
        
        # Clear previous items (keep header)
        children = self.pur_return_items_frame.winfo_children()
        for child in children:
            if child != children[0] if children else None:
                child.destroy()
        
        self.pur_return_items_list = []
        self.pur_return_select_all.set(False)
        
        # Get items from purchase with pack info
        items = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price, 
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, pi.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        for idx, itm in enumerate(items):
            self.add_purchase_return_row(idx, itm)
    
    def add_return_item_row(self, idx, item):
        """Add a row for return item"""
        product_id = item[0]
        name = item[1]
        qty = item[2]
        piece_price = item[3]
        pcs_per_pack = item[4] if item[4] and item[4] > 0 else 1
        pack_price = piece_price * pcs_per_pack
        
        row = tk.Frame(self.return_items_frame, bg="white", relief="ridge", bd=1)
        row.pack(fill="x", pady=2)
        
        var = tk.BooleanVar()
        cb = tk.Checkbutton(row, variable=var, bg="white", command=self.calc_return_total)
        cb.pack(side="left", padx=5)
        
        tk.Label(row, text=name[:25], width=25, bg="white", anchor="w", font=("Arial", 9)).pack(side="left", padx=2)
        tk.Label(row, text=f"{qty} pcs", width=10, bg="white", font=("Arial", 9)).pack(side="left", padx=2)
        tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", font=("Arial", 9)).pack(side="left", padx=2)
        tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", font=("Arial", 9)).pack(side="left", padx=2)
        
        pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        pack_entry.pack(side="left", padx=2)
        pack_entry.insert(0, "0")
        
        piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
        piece_entry.pack(side="left", padx=2)
        piece_entry.insert(0, "0")
        
        refund_label = tk.Label(row, text="Rs.0", width=10, bg="white", font=("Arial", 9, "bold"), fg="#e94560")
        refund_label.pack(side="left", padx=2)
        
        self.return_items_list.append({
            'var': var, 'pack_entry': pack_entry, 'piece_entry': piece_entry,
            'refund_label': refund_label, 'product_id': product_id, 'name': name,
            'pack_price': pack_price, 'piece_price': piece_price,
            'pcs_per_pack': pcs_per_pack, 'max_qty': qty
        })
        
        pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_item_refund(i))
        piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_item_refund(i))
        cb.config(command=lambda i=idx: self.update_item_refund(i))
    
    def update_item_refund(self, idx):
        """Update refund for single item"""
        item = self.return_items_list[idx]
        
        if not item['var'].get():
            item['refund_label'].config(text="Rs.0")
            self.calc_return_total()
            return
        
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            total_pcs = (packs * item['pcs_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text="EXCEEDS", fg="red")
            else:
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        self.calc_return_total()
    
    def calc_return_total(self):
        """Calculate total refund"""
        total = 0
        for item in self.return_items_list:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        self.return_total_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def toggle_all_items(self):
        """Select or deselect all items"""
        select = self.return_select_all.get()
        for idx, item in enumerate(self.return_items_list):
            item['var'].set(select)
            self.update_item_refund(idx)
    
    def process_purchase_return_final(self):
        """Process purchase return"""
        if not hasattr(self, 'current_return_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase invoice first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.return_items_list:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        qty = (packs * item['pcs_per_pack']) + pieces
                        if qty > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} of {item['name']}!")
                            return
                        refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': qty,
                            'total': refund
                        })
                        total_refund += refund
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select items to return!")
            return
        
        if not messagebox.askyesno("Confirm Return", f"Total Refund: Rs. {total_refund:,.2f}\n\nProceed?"):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            return_no = f"RET-PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            reason = "Return to supplier"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, self.current_return_purchase_id, 
                      item['product_id'], item['quantity'], item['total'], reason))
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Purchase return processed!\nReturn No: {return_no}\nRefund: Rs. {total_refund:,.2f}")
            
            # Refresh
            self.load_purchase_invoices()
            self.selected_invoice_label.config(text="No invoice selected")
            self.return_total_label.config(text="Rs. 0.00")
            for widget in self.pur_return_items_frame.winfo_children():
                if 'header_row' in locals() and widget != header_row:
                    widget.destroy()
                self.return_items_list = []
                self.return_select_all.set(False)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")


    def debug_purchase_items(self, purchase_id):
        """Debug - Check if items exist in purchase"""
        items = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        print(f"DEBUG: Purchase ID = {purchase_id}")
        print(f"DEBUG: Items found = {len(items)}")
        for item in items:
            print(f"  - {item[1]}: Qty={item[2]}, Price={item[3]}")
        
        if len(items) == 0:
            print("ERROR: No items found! Purchase may have been added without items.")
        
        return items
    def debug_purchase_items(self, purchase_id):
        """Debug - Check if items exist in purchase"""
        items = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        print(f"DEBUG: Purchase ID = {purchase_id}")
        print(f"DEBUG: Items found = {len(items)}")
        for item in items:
            print(f"  - {item[1]}: Qty={item[2]}, Price={item[3]}")
        
        if len(items) == 0:
            print("ERROR: No items found! Purchase may have been added without items.")
        
        return items
    def load_purchase_returns_list(self):
        """Load all purchases for return selection"""
        for item in self.purchase_return_tree.get_children():
            self.purchase_return_tree.delete(item)
        
        search_term = self.purchase_return_search.get().strip() if hasattr(self, 'purchase_return_search') else ""
        
        if search_term:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
                FROM purchases p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.invoice_no LIKE ? OR s.name LIKE ?
                ORDER BY p.id DESC LIMIT 500
            """
            params = (f'%{search_term}%', f'%{search_term}%')
        else:
            query = """
                SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
                FROM purchases p
                JOIN suppliers s ON p.supplier_id = s.id
                ORDER BY p.id DESC LIMIT 500
            """
            params = ()
        
        purchases = self.fetch_all(query, params)
        
        for purchase in purchases:
            self.purchase_return_tree.insert("", "end", values=(
                purchase[0], purchase[1], 
                purchase[2][:10] if purchase[2] else "-",
                purchase[3][:25], f"Rs. {purchase[4]:,.2f}"
            ))
        
        self.update_status(f"Loaded {len(purchases)} purchases")
    
    def on_purchase_return_selected(self, event):
        """When a purchase is selected, load its items"""
        selected = self.purchase_return_tree.selection()
        if not selected:
            return
        
        item = self.purchase_return_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier_name = item['values'][3]
        total_str = item['values'][4].replace('Rs. ', '').replace(',', '')
        
        print(f"DEBUG: Selected Purchase ID = {purchase_id}")
        
        self.selected_purchase_info.config(text=f"Invoice: {invoice_no} | Supplier: {supplier_name} | Total: Rs. {float(total_str):,.2f}")
        self.current_purchase_id = purchase_id
        self.current_purchase_total = float(total_str)
        
        # Clear previous items (SAFE WAY)
        for widget in self.purchase_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create new header row
        header_row = tk.Frame(self.purchase_scrollable_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Select", 8), ("Product Name", 28), ("Purchased", 10), 
                   ("Pack Price", 12), ("Piece Price", 12), ("Packs", 8), 
                   ("Pieces", 8), ("Refund (Rs.)", 12)]
        
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Segoe UI", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        self.purchase_return_data = []
        self.purchase_select_all_var.set(False)
        
        # Get items from this purchase
        items = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price, 
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   pi.total as item_total
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        print(f"DEBUG: Found {len(items)} items for purchase {purchase_id}")
        
        if not items:
            tk.Label(self.purchase_scrollable_frame, text="⚠️ No items found in this purchase!\n\nThis purchase may not have any items.", 
                    font=("Segoe UI", 11), bg="white", fg="#dc2626").pack(pady=50)
            return
        
        for idx, itm in enumerate(items):
            print(f"  Adding item: {itm[1]}, Qty: {itm[2]}")
            self.add_purchase_return_item_row(idx, itm)
    def add_purchase_return_item_row(self, idx, item):
        """Add a single item row for purchase return"""
        product_id = item[0]
        name = item[1]
        purchased_qty = item[2]
        piece_price = item[3]  # Actual purchase price per piece
        pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
        item_total = item[5]
        
        pack_price = piece_price * pieces_per_pack
        
        # Row frame
        row = tk.Frame(self.purchase_scrollable_frame, bg="white", relief="ridge", bd=1)
        row.pack(fill="x", pady=2)
        
        # Checkbox
        var = tk.BooleanVar()
        cb = tk.Checkbutton(row, variable=var, bg="white", 
                           command=lambda: self.calculate_purchase_return_total_v2())
        cb.pack(side="left", padx=5)
        
        # Product name
        name_label = tk.Label(row, text=name[:35], bg="white", anchor="w", width=28, 
                             font=("Segoe UI", 9))
        name_label.pack(side="left", padx=2)
        
        # Purchased quantity
        tk.Label(row, text=f"{purchased_qty} pcs", bg="white", width=10, 
                font=("Segoe UI", 9)).pack(side="left", padx=2)
        
        # Pack price
        tk.Label(row, text=f"Rs.{pack_price:.0f}", bg="white", width=12, 
                font=("Segoe UI", 9)).pack(side="left", padx=2)
        
        # Piece price
        tk.Label(row, text=f"Rs.{piece_price:.2f}", bg="white", width=12, 
                font=("Segoe UI", 9)).pack(side="left", padx=2)
        
        # Packs entry
        pack_entry = tk.Entry(row, width=6, font=("Segoe UI", 9), justify="center")
        pack_entry.pack(side="left", padx=2)
        pack_entry.insert(0, "0")
        
        # Pieces entry
        piece_entry = tk.Entry(row, width=6, font=("Segoe UI", 9), justify="center")
        piece_entry.pack(side="left", padx=2)
        piece_entry.insert(0, "0")
        
        # Refund label
        refund_label = tk.Label(row, text="Rs. 0", bg="white", width=12, 
                               font=("Segoe UI", 9, "bold"), fg="#e94560")
        refund_label.pack(side="left", padx=2)
        
        # Store item data
        item_data = {
            'var': var,
            'pack_entry': pack_entry,
            'piece_entry': piece_entry,
            'refund_label': refund_label,
            'product_id': product_id,
            'name': name,
            'pack_price': pack_price,
            'piece_price': piece_price,
            'pieces_per_pack': pieces_per_pack,
            'max_qty': purchased_qty,
            'item_total': item_total
        }
        
        self.purchase_return_data.append(item_data)
        
        # Bind events
        def on_change(e, i=idx):
            self.update_purchase_item_refund_v2(i)
        
        pack_entry.bind("<KeyRelease>", on_change)
        piece_entry.bind("<KeyRelease>", on_change)
        cb.config(command=lambda i=idx: self.update_purchase_item_refund_v2(i))
    
    def update_purchase_item_refund_v2(self, idx):
        """Update refund for a single purchase item"""
        item = self.purchase_return_data[idx]
        
        if not item['var'].get():
            item['refund_label'].config(text="Rs. 0")
            self.calculate_purchase_return_total_v2()
            return
        
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            total_pieces = (packs * item['pieces_per_pack']) + pieces
            
            if total_pieces > item['max_qty']:
                item['refund_label'].config(text=f"⚠️ Max {item['max_qty']}", fg="red")
                self.purchase_warning_label.config(text=f"⚠️ Warning: {item['name']} - Cannot return more than {item['max_qty']} pieces", fg="#dc2626")
                self.purchase_warning_label.pack(fill="x", padx=10, pady=5)
            else:
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                item['refund_label'].config(text=f"Rs.{refund:.0f}", fg="#e94560")
                self.purchase_warning_label.config(text="")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        self.calculate_purchase_return_total_v2()
    
    def calculate_purchase_return_total_v2(self):
        """Calculate total refund for purchase return"""
        total = 0
        all_valid = True
        
        for item in self.purchase_return_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total_pieces = (packs * item['pieces_per_pack']) + pieces
                    
                    if total_pieces > item['max_qty']:
                        all_valid = False
                    else:
                        total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        
        self.purchase_return_total.config(text=f"Rs. {total:,.2f}")
        
        if not all_valid and total > 0:
            self.purchase_warning_label.config(text="⚠️ Some quantities exceed available stock. Please adjust.", fg="#dc2626")
            self.purchase_warning_label.pack(fill="x", padx=10, pady=5)
        elif total == 0:
            if self.purchase_warning_label.winfo_ismapped():
                self.purchase_warning_label.pack_forget()
        else:
            self.purchase_warning_label.pack_forget()
        
        return total
    
    def toggle_purchase_select_all(self):
        """Select or deselect all items"""
        select = self.purchase_select_all_var.get()
        for idx, item in enumerate(self.purchase_return_data):
            item['var'].set(select)
            self.update_purchase_item_refund_v2(idx)
    
    def process_purchase_return_final_v2(self):
        """Process purchase return with full validation"""
        if not hasattr(self, 'current_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase first!")
            return
        
        return_items = []
        total_refund = 0
        has_error = False
        
        for item in self.purchase_return_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    
                    if packs > 0 or pieces > 0:
                        total_pieces = (packs * item['pieces_per_pack']) + pieces
                        
                        if total_pieces > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} pieces of {item['name']}!\n"
                                f"You tried to return {total_pieces} pieces.")
                            has_error = True
                            return
                        
                        refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': total_pieces,
                            'total': refund
                        })
                        total_refund += refund
                except:
                    pass
        
        if has_error:
            return
        
        if not return_items:
            messagebox.showwarning("Error", "Please select items to return!")
            return
        
        # Validation: Cannot exceed purchase total
        if total_refund > self.current_purchase_total + 0.01:
            messagebox.showwarning("Invalid Return", 
                f"Total refund Rs. {total_refund:,.2f} exceeds purchase total Rs. {self.current_purchase_total:,.2f}!\n\n"
                f"Please check your return quantities.")
            return
        
        # Get invoice number for confirmation
        selected = self.purchase_return_tree.selection()
        invoice_no = self.purchase_return_tree.item(selected[0])['values'][1] if selected else "Unknown"
        
        confirm_msg = f"📤 PURCHASE RETURN CONFIRMATION\n\n"
        confirm_msg += f"Invoice: {invoice_no}\n"
        confirm_msg += f"Total Refund: Rs. {total_refund:,.2f}\n\n"
        confirm_msg += f"Items to return:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'PURCHASE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-PUR-{new_num:03d}"
            reason = "Return to supplier"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, self.current_purchase_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # REDUCE stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "PURCHASE", invoice_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Purchase return processed successfully!\n\n"
                f"Return No: {return_no}\n"
                f"Items returned: {len(return_items)}\n"
                f"Total Refund: Rs. {total_refund:,.2f}")
            
            # Refresh everything
            self.load_purchase_returns_list()
            self.selected_purchase_info.config(text="No purchase selected")
            self.purchase_return_total.config(text="Rs. 0.00")
            
            # Clear items frame
            for widget in self.purchase_scrollable_frame.winfo_children():
                widget.destroy()
            
            self.purchase_return_data = []
            self.purchase_select_all_var.set(False)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_purchases_for_return_new(self):
        """Load all purchases for return selection"""
        for item in self.purchase_return_tree.get_children():
            self.purchase_return_tree.delete(item)
        
        purchases = self.fetch_all("""
            SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.id DESC LIMIT 500
        """)
        
        for purchase in purchases:
            self.purchase_return_tree.insert("", "end", values=(
                purchase[0], purchase[1], purchase[2][:10] if purchase[2] else "-",
                purchase[3], f"Rs. {purchase[4]:,.2f}"
            ))
    
    def on_purchase_return_new(self, event):
        """When purchase selected, load items for return"""
        selected = self.purchase_return_tree.selection()
        if not selected:
            return
        
        item = self.purchase_return_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier_name = item['values'][3]
        
        self.selected_purchase_label.config(text=f"Selected Purchase: {invoice_no} - {supplier_name}")
        self.current_purchase_id = purchase_id
        
        # Get items from this purchase
        products = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price, 
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        items_data = []
        for prod in products:
            product_id = prod[0]
            name = prod[1]
            purchased_qty = prod[2]
            piece_price = prod[3]
            pieces_per_pack = prod[4] if prod[4] and prod[4] > 0 else 1
            pack_price = piece_price * pieces_per_pack
            
            items_data.append({
                'product_id': product_id,
                'name': name,
                'original_qty': purchased_qty,
                'pack_price': pack_price,
                'piece_price': piece_price,
                'pieces_per_pack': pieces_per_pack
            })
        
        # Clear and create new panel
        for widget in self.purchase_return_items_frame.winfo_children():
            widget.destroy()
        
        self.return_items_data = []
        self.create_return_items_panel(self.purchase_return_items_frame, items_data, self.calculate_purchase_return_total)
    
    def calculate_purchase_return_total(self):
        """Calculate total for purchase return"""
        total = 0
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        
        self.purchase_total_refund_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def process_purchase_return_new(self):
        """Process purchase return with selected items"""
        if not hasattr(self, 'current_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pieces = (packs * item['pieces_per_pack']) + pieces
                        if total_pieces > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                            return
                        refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': total_pieces,
                            'total': refund
                        })
                        total_refund += refund
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select items to return!")
            return
        
        reason = "Return to supplier"
        
        confirm_msg = f"Purchase Return\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'PURCHASE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-PUR-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, self.current_purchase_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # Reduce stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "PURCHASE", str(self.current_purchase_id), return_items, total_refund, reason)
            
            messagebox.showinfo("Success", f"Purchase return processed!\nReturn No: {return_no}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            # Refresh
            self.load_purchases_for_return_new()
            self.selected_purchase_label.config(text="Selected Purchase: None")
            self.purchase_total_refund_label.config(text="Rs. 0.00")
            for widget in self.purchase_return_items_frame.winfo_children():
                widget.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def load_purchases_for_return_new(self):
        """Load all purchases for return selection"""
        for item in self.purchase_return_tree.get_children():
            self.purchase_return_tree.delete(item)
        
        purchases = self.fetch_all("""
            SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.id DESC LIMIT 500
        """)
        
        for purchase in purchases:
            self.purchase_return_tree.insert("", "end", values=(
                purchase[0], purchase[1], purchase[2][:10] if purchase[2] else "-",
                purchase[3], f"Rs. {purchase[4]:,.2f}"
            ))
    
    def on_purchase_return_new(self, event):
        """When purchase selected, load items for return"""
        selected = self.purchase_return_tree.selection()
        if not selected:
            return
        
        item = self.purchase_return_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier_name = item['values'][3]
        
        self.selected_purchase_label.config(text=f"Selected Purchase: {invoice_no} - {supplier_name}")
        self.current_purchase_id = purchase_id
        
        # Get items from this purchase
        products = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price, p.pieces_per_pack
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        items_data = []
        for prod in products:
            product_id = prod[0]
            name = prod[1]
            purchased_qty = prod[2]
            piece_price = prod[3]  # Actual purchase price per piece
            pieces_per_pack = prod[4] if prod[4] and prod[4] > 0 else 1
            pack_price = piece_price * pieces_per_pack
            
            items_data.append({
                'product_id': product_id,
                'name': name,
                'original_qty': purchased_qty,
                'pack_price': pack_price,
                'piece_price': piece_price,
                'pieces_per_pack': pieces_per_pack
            })
        
        # Clear and create new panel
        for widget in self.purchase_return_items_frame.winfo_children():
            widget.destroy()
        
        self.return_items_data = []
        self.create_return_items_panel(self.purchase_return_items_frame, items_data, self.calculate_purchase_return_total)
    
    def calculate_purchase_return_total(self):
        """Calculate total for purchase return"""
        total = 0
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        
        self.purchase_total_refund_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def process_purchase_return_new(self):
        """Process purchase return with selected items"""
        if not hasattr(self, 'current_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pieces = (packs * item['pieces_per_pack']) + pieces
                        if total_pieces > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                            return
                        refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': total_pieces,
                            'total': refund
                        })
                        total_refund += refund
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select items to return!")
            return
        
        reason = self.purchase_return_reason.get().strip()
        if not reason:
            reason = "Return to supplier"
        
        confirm_msg = f"Purchase Return\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            return_no = f"RET-PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, self.current_purchase_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # Reduce stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Purchase return processed!\nReturn No: {return_no}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            # Refresh
            self.load_purchases_for_return_new()
            self.selected_purchase_label.config(text="Selected Purchase: None")
            self.purchase_total_refund_label.config(text="Rs. 0.00")
            for widget in self.purchase_return_items_frame.winfo_children():
                widget.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def on_purchase_return_select(self, event):
        """When purchase is selected, load its products with Pack/Piece options"""
        selected = self.purchase_return_tree.selection()
        if not selected:
            return
        
        item = self.purchase_return_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier_name = item['values'][3]
        
        self.selected_purchase_label.config(text=f"Selected Purchase: {invoice_no} - {supplier_name}")
        self.current_purchase_id = purchase_id
        
        # Clear existing product widgets
        for widget in self.purchase_return_products_frame.winfo_children():
            widget.destroy()
        self.purchase_return_vars = []
        
        # Load products from this purchase
        products = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.price, pi.quantity, p.cost_price,
                   IFNULL(p.unit_type, 'Piece'), IFNULL(p.pieces_per_pack, 1), IFNULL(p.pack_price, 0)
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        self.current_purchase_products = products
        
        for product in products:
            product_id = product[0]
            product_name = product[1]
            purchase_price = product[2]
            purchased_qty = product[3]
            cost_price = product[4]
            unit_type = product[5] if len(product) > 5 else "Piece"
            pieces_per_pack = product[6] if len(product) > 6 and product[6] > 0 else 1
            pack_price = product[7] if len(product) > 7 and product[7] > 0 else 0
            
            # Main frame
            prod_frame = tk.Frame(self.purchase_return_products_frame, bg="white", relief="ridge", bd=1)
            prod_frame.pack(fill="x", padx=5, pady=5)
            prod_frame.configure(width=600)
            prod_frame.pack_propagate(False)
            
            # Checkbox
            var = tk.BooleanVar()
            cb = tk.Checkbutton(prod_frame, text=product_name, variable=var, 
                                bg="white", font=("Arial", 10, "bold"),
                                command=self.update_purchase_return_total)
            cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            # Info
            info_frame = tk.Frame(prod_frame, bg="white")
            info_frame.grid(row=0, column=1, padx=10, pady=5)
            tk.Label(info_frame, text=f"Purchased: {purchased_qty} units @ Rs.{purchase_price:.2f}", 
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            # Pack/Simple logic (same as sale return)
            product_data = {
                'var': var,
                'product_id': product_id,
                'name': product_name,
                'price': purchase_price,
                'max_qty': purchased_qty,
                'has_pack': False
            }
            
            if unit_type == "Pack" and pack_price > 0:
                product_data['has_pack'] = True
                product_data['pack_price'] = pack_price
                product_data['pieces_per_pack'] = pieces_per_pack
                product_data['piece_price'] = purchase_price
                
                # Type selection
                type_frame = tk.Frame(prod_frame, bg="white")
                type_frame.grid(row=0, column=2, padx=10, pady=5)
                
                return_type_var = tk.StringVar(value="Piece")
                piece_radio = tk.Radiobutton(type_frame, text="Piece", variable=return_type_var, value="Piece", bg="white", font=("Arial", 8))
                piece_radio.pack(side="left", padx=5)
                pack_radio = tk.Radiobutton(type_frame, text="Pack", variable=return_type_var, value="Pack", bg="white", font=("Arial", 8))
                pack_radio.pack(side="left", padx=5)
                
                product_data['return_type'] = return_type_var
                
                # Quantity frame
                qty_container = tk.Frame(prod_frame, bg="white")
                qty_container.grid(row=0, column=3, padx=10, pady=5, sticky="e")
                
                # Piece mode
                piece_qty_frame = tk.Frame(qty_container, bg="white")
                tk.Label(piece_qty_frame, text="Qty:", font=("Arial", 9), bg="white").pack(side="left")
                piece_qty_entry = tk.Entry(piece_qty_frame, width=5, font=("Arial", 10), justify="center")
                piece_qty_entry.pack(side="left", padx=5)
                piece_qty_entry.insert(0, "0")
                product_data['piece_qty'] = piece_qty_entry
                
                # Pack mode
                pack_qty_frame = tk.Frame(qty_container, bg="white")
                tk.Label(pack_qty_frame, text="Packs:", font=("Arial", 9), bg="white").pack(side="left")
                pack_qty_entry = tk.Entry(pack_qty_frame, width=4, font=("Arial", 10), justify="center")
                pack_qty_entry.pack(side="left", padx=2)
                pack_qty_entry.insert(0, "0")
                tk.Label(pack_qty_frame, text="Extra:", font=("Arial", 9), bg="white").pack(side="left", padx=2)
                extra_pcs_entry = tk.Entry(pack_qty_frame, width=4, font=("Arial", 10), justify="center")
                extra_pcs_entry.pack(side="left", padx=2)
                extra_pcs_entry.insert(0, "0")
                product_data['pack_qty'] = pack_qty_entry
                product_data['extra_pcs'] = extra_pcs_entry
                
                piece_qty_frame.pack()
                pack_qty_frame.pack_forget()
                
                def toggle_mode(pt=return_type_var, pf=piece_qty_frame, pkf=pack_qty_frame):
                    if pt.get() == "Piece":
                        pf.pack()
                        pkf.pack_forget()
                    else:
                        pf.pack_forget()
                        pkf.pack()
                    self.update_purchase_return_total()
                
                piece_radio.config(command=toggle_mode)
                pack_radio.config(command=toggle_mode)
                
                piece_qty_entry.bind("<KeyRelease>", lambda e: self.update_purchase_return_total())
                pack_qty_entry.bind("<KeyRelease>", lambda e: self.update_purchase_return_total())
                extra_pcs_entry.bind("<KeyRelease>", lambda e: self.update_purchase_return_total())
                
            else:
                # Simple product
                qty_frame = tk.Frame(prod_frame, bg="white")
                qty_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
                tk.Label(qty_frame, text="Return Qty:", font=("Arial", 9), bg="white").pack(side="left")
                qty_entry = tk.Entry(qty_frame, width=6, font=("Arial", 10), justify="center")
                qty_entry.pack(side="left", padx=5)
                qty_entry.insert(0, "0")
                product_data['qty_entry'] = qty_entry
                qty_entry.bind("<KeyRelease>", lambda e: self.update_purchase_return_total())
            
            self.purchase_return_vars.append(product_data)
        
        self.update_purchase_return_total()
    
    def update_purchase_return_total(self):
        """Calculate total refund for purchase return"""
        total = 0
        for item in self.purchase_return_vars:
            if item['var'].get():
                if item.get('has_pack', False):
                    return_type = item.get('return_type').get() if item.get('return_type') else "Piece"
                    if return_type == "Piece":
                        try:
                            qty = int(item.get('piece_qty').get() or 0)
                            if qty > 0 and qty <= item.get('max_qty', 0):
                                total += qty * item.get('price', 0)
                        except:
                            pass
                    else:
                        try:
                            packs = int(item.get('pack_qty').get() or 0)
                            extra = int(item.get('extra_pcs').get() or 0)
                            if packs > 0 or extra > 0:
                                pieces_per_pack = item.get('pieces_per_pack', 1)
                                total_pieces = (packs * pieces_per_pack) + extra
                                if total_pieces <= item.get('max_qty', 0):
                                    total += (packs * item.get('pack_price', 0)) + (extra * item.get('piece_price', 0))
                        except:
                            pass
                else:
                    try:
                        qty = int(item.get('qty_entry').get() or 0)
                        if qty > 0 and qty <= item.get('max_qty', 0):
                            total += qty * item.get('price', 0)
                    except:
                        pass
        self.purchase_total_refund_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def process_multi_purchase_return(self):
        """Process multiple product purchase return"""
        if not hasattr(self, 'current_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.purchase_return_vars:
            if item['var'].get():
                try:
                    qty = int(item['qty_entry'].get())
                    if qty > 0:
                        if qty > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity",
                                f"Cannot return more than {item['max_qty']} units of {item['name']}!")
                            return
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': qty,
                            'price': item['price'],
                            'total': qty * item['price']
                        })
                        total_refund += qty * item['price']
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select at least one product to return!")
            return
        
        reason = "Return to supplier"  # Default reason        reason = "Return to supplier"  # Fixed reason, no user input
        
        purchase = self.fetch_one("SELECT invoice_no, supplier_id FROM purchases WHERE id = ?", (self.current_purchase_id,))
        if not purchase:
            return
        
        confirm_msg = f"Purchase: {purchase[0]}\n\nReturn Items:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} x Rs.{item['price']:.0f} = Rs.{item['total']:.0f}\n"
        confirm_msg += f"\nTotal Refund: Rs. {total_refund:,.2f}\nReason: {reason}\n\nProceed?"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
                        # Get last return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'PURCHASE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-PUR-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("PURCHASE", return_no, self.current_purchase_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # REDUCE stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                VALUES (?, ?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {len(return_items)} items", total_refund, 0))
            
            conn.commit()
            conn.close()
                        # Print Return Slip
            self.print_return_slip(return_no, "PURCHASE", purchase[0], return_items, total_refund, reason)
            messagebox.showinfo("Success",
                f"Purchase return processed!\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            self.load_purchases_for_return()
            self.selected_purchase_label.config(text="Selected Purchase: None")
            self.purchase_total_refund_label.config(text="Rs. 0.00")
            
            for widget in self.purchase_return_products_frame.winfo_children():
                widget.destroy()
            self.purchase_return_vars = []
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def load_purchases_for_return(self):
        """Load all purchases for return selection"""
        for item in self.purchase_return_tree.get_children():
            self.purchase_return_tree.delete(item)
        
        purchases = self.fetch_all("""
            SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.id DESC LIMIT 500
        """)
        
        for purchase in purchases:
            self.purchase_return_tree.insert("", "end", values=(
                purchase[0], purchase[1], purchase[2][:10] if purchase[2] else "-",
                purchase[3], f"Rs. {purchase[4]:,.2f}"
            ))
    
    def load_purchases_for_return(self):
        """Load all purchases for return selection"""
        for item in self.purchase_return_tree.get_children():
            self.purchase_return_tree.delete(item)
        
        purchases = self.fetch_all("""
            SELECT p.id, p.invoice_no, p.purchase_date, s.name, p.total_amount
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY p.id DESC LIMIT 500
        """)
        
        for purchase in purchases:
            self.purchase_return_tree.insert("", "end", values=(
                purchase[0], purchase[1], purchase[2][:10] if purchase[2] else "-",
                purchase[3], f"Rs. {purchase[4]:,.2f}", "Active"
            ))
    
    def on_purchase_select(self, event):
        """When purchase is selected, load its products"""
        selected = self.purchase_return_tree.selection()
        if not selected:
            return
        
        item = self.purchase_return_tree.item(selected[0])
        purchase_id = item['values'][0]
        invoice_no = item['values'][1]
        supplier_name = item['values'][3]
        
        # Update label
        self.selected_purchase_label.config(text=f"Selected Purchase: {invoice_no} - {supplier_name}")
        self.current_purchase_id = purchase_id
        
        # Load products from this purchase
        products = self.fetch_all("""
            SELECT pi.product_id, p.name, pi.quantity, pi.price, p.stock_quantity
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        """, (purchase_id,))
        
        if products:
            product_list = [f"{p[0]} - {p[1]} (Qty Purchased: {p[2]}, Price: Rs.{p[3]})" for p in products]
            self.purchase_return_product['values'] = product_list
            self.purchase_return_product.current(0)
            
            # Store product details for later use
            self.current_product_details = products
            self.update_purchase_return_price()
        else:
            self.purchase_return_product['values'] = []
            messagebox.showinfo("Info", "No products found in this purchase")
    
    def update_purchase_return_price(self):
        """Auto-fill refund amount and available quantity when product selected"""
        if not hasattr(self, 'current_product_details') or not self.current_product_details:
            return
            
        if self.purchase_return_product.get():
            product_text = self.purchase_return_product.get()
            # Extract product ID
            try:
                product_id = int(product_text.split(" - ")[0])
                
                # Find product in details
                for prod in self.current_product_details:
                    if prod[0] == product_id:
                        # Available quantity (purchased quantity)
                        available_qty = prod[2]
                        price = prod[3]
                        
                        self.available_qty_label.config(text=str(available_qty))
                        self.purchase_return_refund.delete(0, tk.END)
                        self.purchase_return_refund.insert(0, str(price))
                        
                        # Store current product info
                        self.current_return_product_id = product_id
                        self.current_return_product_name = prod[1]
                        self.current_return_max_qty = available_qty
                        break
            except:
                pass
    
    def process_purchase_return(self):
        """Process purchase return - Stock kam, Supplier ko refund"""
        import time
        time.sleep(0.5)
        if not hasattr(self, 'current_purchase_id'):
            messagebox.showwarning("Error", "Please select a purchase first!")
            return
        
        if not self.purchase_return_product.get():
            messagebox.showwarning("Error", "Please select a product!")
            return
        
        try:
            quantity = int(self.purchase_return_qty.get())
            if quantity <= 0:
                messagebox.showwarning("Error", "Quantity must be greater than 0!")
                return
            if quantity > self.current_return_max_qty:
                messagebox.showwarning("Error", f"Maximum return quantity is {self.current_return_max_qty}!")
                return
        except:
            messagebox.showwarning("Error", "Invalid quantity!")
            return
        
        try:
            refund_amount = float(self.purchase_return_refund.get())
            if refund_amount <= 0:
                messagebox.showwarning("Error", "Refund amount must be greater than 0!")
                return
        except:
            messagebox.showwarning("Error", "Invalid refund amount!")
            return
        
        reason = self.purchase_return_reason.get()
        product_name = self.current_return_product_name
        
        # Get purchase details
        purchase = self.fetch_one("SELECT invoice_no, supplier_id FROM purchases WHERE id = ?", (self.current_purchase_id,))
        if not purchase:
            return
        
        confirm = messagebox.askyesno(
            "Confirm Return",
            f"Purchase: {purchase[0]}\n"
            f"Product: {product_name}\n"
            f"Quantity: {quantity}\n"
            f"Refund: Rs. {refund_amount:,.2f}\n"
            f"Reason: {reason}\n\n"
            f"Proceed with return?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            return_no = f"RET-PUR-{datetime.now().year}{datetime.now().strftime('%d%H%M%S')}"
            
            # Record return
            cursor.execute("""
                INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("PURCHASE", return_no, self.current_purchase_id, self.current_return_product_id, quantity, refund_amount, reason))
            
            # UPDATE STOCK - Reduce stock (product wapas gaya)
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (quantity, self.current_return_product_id))
            
            # Add to ledger (Refund given - Debit)
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                VALUES (?, ?, ?, ?, ?)
            """, ("PURCHASE_RETURN", return_no, f"Return to supplier: {product_name} x{quantity}", refund_amount, 0))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Purchase return processed!\nReturn No: {return_no}")
            self.update_status(f"✅ Returned {quantity} x {product_name} to supplier")
            
            # Refresh
            self.load_purchases_for_return()
            self.purchase_return_qty.delete(0, tk.END)
            self.purchase_return_refund.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def create_sale_return_tab(self, parent):
        """Sale Return Tab - Right Click Context Menu with Pack/Piece Window"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="📥 SALE RETURN (FROM CUSTOMER)", 
                font=("Helvetica", 20, "bold"), bg="#f5f5f5", fg="#1cc88a").pack(pady=5)
        
        # Main Frame - All Sales List
        list_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="📋 ALL SALES INVOICES", font=("Arial", 14, "bold"), 
                bg="#1cc88a", fg="white", pady=8).pack(fill="x")
        
        # Search
        search_frame = tk.Frame(list_frame, bg="white", padx=10, pady=5)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 10), bg="white").pack(side="left")
        self.sale_return_search = tk.Entry(search_frame, font=("Arial", 10), width=30)
        self.sale_return_search.pack(side="left", padx=5)
        self.sale_return_search.bind("<KeyRelease>", lambda e: self.load_all_sales())
        
        # Treeview
        tree_frame = tk.Frame(list_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Invoice No", "Date", "Customer", "Total Amount", "Items")
        self.sale_list_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.sale_list_tree.heading("ID", text="ID", anchor="center")
        self.sale_list_tree.heading("Invoice No", text="Invoice No", anchor="center")
        self.sale_list_tree.heading("Date", text="Date", anchor="center")
        self.sale_list_tree.heading("Customer", text="Customer", anchor="center")
        self.sale_list_tree.heading("Total Amount", text="Total Amount (Rs.)", anchor="center")
        self.sale_list_tree.heading("Items", text="Items", anchor="center")
        
        self.sale_list_tree.column("ID", width=50, anchor="center")
        self.sale_list_tree.column("Invoice No", width=130, anchor="center")
        self.sale_list_tree.column("Date", width=100, anchor="center")
        self.sale_list_tree.column("Customer", width=180, anchor="w")
        self.sale_list_tree.column("Total Amount", width=120, anchor="e")
        self.sale_list_tree.column("Items", width=80, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sale_list_tree.yview)
        self.sale_list_tree.configure(yscrollcommand=vsb.set)
        self.sale_list_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Right Click Menu
        self.sale_context_menu = tk.Menu(self.root, tearoff=0)
        self.sale_context_menu.add_command(label="🔄 Return Items", command=self.open_sale_return_window)
        
        self.sale_list_tree.bind("<Button-3>", self.show_sale_context_menu)
        
        # Load all sales
        self.load_all_sales()
    
    def load_all_sales(self):
        """Load all sales into treeview"""
        for item in self.sale_list_tree.get_children():
            self.sale_list_tree.delete(item)
        
        search = self.sale_return_search.get().strip() if hasattr(self, 'sale_return_search') else ""
        
        if search:
            query = """
                SELECT s.id, s.invoice_no, s.sale_date, s.customer_name, s.total_amount,
                       (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) as item_count
                FROM sales s
                WHERE s.invoice_no LIKE ? OR s.customer_name LIKE ?
                ORDER BY s.id DESC
            """
            params = (f'%{search}%', f'%{search}%')
        else:
            query = """
                SELECT s.id, s.invoice_no, s.sale_date, s.customer_name, s.total_amount,
                       (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) as item_count
                FROM sales s
                ORDER BY s.id DESC
            """
            params = ()
        
        sales = self.fetch_all(query, params)
        for s in sales:
            self.sale_list_tree.insert("", "end", values=(
                s[0], s[1], s[2][:10] if s[2] else "-", s[3] or "Walk-in", f"Rs. {s[4]:,.2f}", s[5]
            ))
        
        self.update_status(f"Loaded {len(sales)} sales invoices")
    
    def show_sale_context_menu(self, event):
        """Show right click context menu for sales"""
        item = self.sale_list_tree.identify_row(event.y)
        if item:
            self.sale_list_tree.selection_set(item)
            self.sale_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_sale_for_return(self):
        """Get selected sale ID"""
        selected = self.sale_list_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a sale first!")
            return None
        item = self.sale_list_tree.item(selected[0])
        return item['values'][0]
    
    def open_sale_return_window(self):
        """Open return window for selected sale"""
        sale_id = self.get_selected_sale_for_return()
        if not sale_id:
            return
        
        # Get sale details
        sale = self.fetch_one("""
            SELECT s.id, s.invoice_no, s.customer_name, s.sale_date, s.total_amount
            FROM sales s
            WHERE s.id = ?
        """, (sale_id,))
        
        if not sale:
            messagebox.showerror("Error", "Sale not found!")
            return
        
        # Get all items from this sale
        items = self.fetch_all("""
            SELECT si.product_id, p.name, si.quantity, si.price,
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, si.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        
        if not items:
            messagebox.showwarning("Error", "No items found in this sale!")
            return
        
        # Create Return Window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Return Items - {sale[1]} ({sale[2]})")
        dialog.geometry("750x600")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"📥 SALE RETURN", font=("Helvetica", 16, "bold"),
                bg="#1a1a2e", fg="#1cc88a").pack(pady=(10, 0))
        tk.Label(header_frame, text=f"Invoice: {sale[1]} | Customer: {sale[2]} | Date: {sale[3][:10]}",
                font=("Arial", 10), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # Main scrollable area for items
        canvas_container = tk.Frame(dialog, bg="#f5f5f5")
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Header Row
        header_row = tk.Frame(scroll_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Product", 22), ("Sold Qty", 8), ("Pack Price", 12), 
                   ("Piece Price", 12), ("Packs Return", 6), ("Pieces Return", 6), ("Refund", 12)]
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Arial", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        return_items_data = []
        
        for idx, item in enumerate(items):
            product_id = item[0]
            product_name = item[1]
            sold_qty = item[2]
            sale_price = item[3]
            pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
            pack_price = item[5] if item[5] and item[5] > 0 else sale_price * pieces_per_pack
            piece_price = pack_price / pieces_per_pack if pieces_per_pack > 0 else sale_price
            
            row = tk.Frame(scroll_frame, bg="white", relief="ridge", bd=1)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=product_name[:22], width=22, bg="white", anchor="w", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=str(sold_qty), width=8, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            
            pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            pack_entry.pack(side="left", padx=2)
            pack_entry.insert(0, "0")
            
            piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            
            refund_label = tk.Label(row, text="Rs.0", width=12, bg="white", anchor="center",
                                    font=("Arial", 9, "bold"), fg="#1cc88a")
            refund_label.pack(side="left", padx=2)
            
            item_data = {
                'product_id': product_id, 'name': product_name,
                'pack_entry': pack_entry, 'piece_entry': piece_entry,
                'refund_label': refund_label, 'pack_price': pack_price,
                'piece_price': piece_price, 'pieces_per_pack': pieces_per_pack,
                'max_qty': sold_qty
            }
            return_items_data.append(item_data)
            
            pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_sale_return_refund(return_items_data[i]))
            piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_sale_return_refund(return_items_data[i]))
        
        # Total Refund Frame
        total_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        total_inner = tk.Frame(total_frame, bg="white", padx=15, pady=10)
        total_inner.pack()
        
        tk.Label(total_inner, text="💰 TOTAL REFUND:", font=("Arial", 16, "bold"),
                bg="white", fg="#1cc88a").pack(side="left", padx=10)
        total_refund_label = tk.Label(total_inner, text="Rs. 0.00", font=("Arial", 18, "bold"),
                                      bg="white", fg="#1cc88a")
        total_refund_label.pack(side="left", padx=10)
        
        def calculate_total():
            total = 0
            for itm in return_items_data:
                try:
                    packs = int(itm['pack_entry'].get() or 0)
                    pieces = int(itm['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pcs = (packs * itm['pieces_per_pack']) + pieces
                        if total_pcs <= itm['max_qty']:
                            total += (packs * itm['pack_price']) + (pieces * itm['piece_price'])
                except:
                    pass
            total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        dialog.calculate_total = calculate_total
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="✅ COMPLETE SALE RETURN", 
                 command=lambda: self.execute_sale_return(sale_id, sale[1], return_items_data, total_refund_label, dialog),
                 bg="#1cc88a", fg="white", font=("Arial", 12, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy,
                 bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        calculate_total()
    
    def update_sale_return_refund(self, item):
        """Update refund for a single sale return item - Packs + Pieces both work together"""
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Total pieces = (packs * pieces_per_pack) + extra pieces
            total_pcs = (packs * item['pieces_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text=f"Max {item['max_qty']}", fg="red")
            elif total_pcs == 0:
                item['refund_label'].config(text="Rs.0", fg="#1cc88a")
            else:
                # Calculate refund: (packs * pack_price) + (pieces * piece_price)
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                # Show what was returned
                if packs > 0 and pieces > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk+{pieces}pcs)", fg="#1cc88a")
                elif packs > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk)", fg="#1cc88a")
                else:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({pieces}pcs)", fg="#1cc88a")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        # Find parent window and update total
        try:
            dialog = item['refund_label'].winfo_toplevel()
            if hasattr(dialog, 'calculate_total'):
                dialog.calculate_total()
        except:
            pass
    
    def execute_sale_return(self, sale_id, invoice_no, return_items_data, total_label, dialog):
        """Execute the sale return - Stock INCREASE hota hai"""
        return_items = []
        total_refund = 0
        
        for item in return_items_data:
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                if packs > 0 or pieces > 0:
                    total_pcs = (packs * item['pieces_per_pack']) + pieces
                    if total_pcs > item['max_qty']:
                        messagebox.showwarning("Invalid Quantity", 
                            f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                        return
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    return_items.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': total_pcs,
                        'total': refund,
                        'packs': packs,
                        'pieces': pieces
                    })
                    total_refund += refund
            except:
                pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please enter quantity to return!")
            return
        
        confirm_msg = f"📥 SALE RETURN\n\nInvoice: {invoice_no}\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['packs']} pack + {item['pieces']} pcs = {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'SALE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                new_num = int(parts[-1]) + 1 if len(parts) >= 3 else 1
            else:
                new_num = 1
            
            return_no = f"RET-SALE-{new_num:03d}"
            reason = "Customer return"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("SALE", return_no, sale_id, item['product_id'], 
                      item['quantity'], item['total'], reason))
                
                # IMPORTANT: Stock INCREASE - mal wapas warehouse mein aa raha hai
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Update sale total
            cursor.execute("UPDATE sales SET total_amount = total_amount - ? WHERE id = ?",
                          (total_refund, sale_id))
            
            # Ledger entry (Debit - refund diya)
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("SALE_RETURN", return_no, f"Return from customer: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "SALE", invoice_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Sale return processed!\n\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\nTotal Refund: Rs. {total_refund:,.2f}\n\n"
                f"📦 Stock has been INCREASED by {len(return_items)} items.")
            
            dialog.destroy()
            
            # Refresh sale list
            self.load_all_sales()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_sales_for_return_new(self):
        """Load all sales for return selection"""
        for item in self.sale_return_tree.get_children():
            self.sale_return_tree.delete(item)
        
        sales = self.fetch_all("""
            SELECT id, invoice_no, sale_date, customer_name, total_amount
            FROM sales
            ORDER BY id DESC LIMIT 500
        """)
        
        for sale in sales:
            self.sale_return_tree.insert("", "end", values=(
                sale[0], sale[1], sale[2][:10] if sale[2] else "-",
                sale[3] or "N/A", f"Rs. {sale[4]:,.2f}"
            ))
    
    def on_sale_return_new(self, event):
        """When sale selected, load items for return"""
        selected = self.sale_return_tree.selection()
        if not selected:
            return
        
        item = self.sale_return_tree.item(selected[0])
        sale_id = item['values'][0]
        invoice_no = item['values'][1]
        customer_name = item['values'][3]
        
        self.selected_sale_label.config(text=f"Selected Sale: {invoice_no} - {customer_name}")
        self.current_sale_id = sale_id
        
        # Get items from this sale
        products = self.fetch_all("""
            SELECT si.product_id, p.name, si.quantity, si.price, 
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        
        items_data = []
        for prod in products:
            product_id = prod[0]
            name = prod[1]
            sold_qty = prod[2]
            sold_price = prod[3]
            pieces_per_pack = prod[4] if prod[4] and prod[4] > 0 else 1
            pack_price = sold_price * pieces_per_pack
            
            items_data.append({
                'product_id': product_id,
                'name': name,
                'original_qty': sold_qty,
                'pack_price': pack_price,
                'piece_price': sold_price,
                'pieces_per_pack': pieces_per_pack
            })
        
        # Clear and create new panel
        for widget in self.sale_return_items_frame.winfo_children():
            widget.destroy()
        
        self.return_items_data = []
        self.create_return_items_panel(self.sale_return_items_frame, items_data, self.calculate_sale_return_total)
    
    def calculate_sale_return_total(self):
        """Calculate total for sale return"""
        total = 0
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    total += (packs * item['pack_price']) + (pieces * item['piece_price'])
                except:
                    pass
        
        self.sale_total_refund_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def process_sale_return_new(self):
        """Process sale return"""
        if not hasattr(self, 'current_sale_id'):
            messagebox.showwarning("Error", "Please select a sale first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.return_items_data:
            if item['var'].get():
                try:
                    packs = int(item['pack_entry'].get() or 0)
                    pieces = int(item['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pieces = (packs * item['pieces_per_pack']) + pieces
                        if total_pieces > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                            return
                        refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': total_pieces,
                            'total': refund
                        })
                        total_refund += refund
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select items to return!")
            return
        
        reason = "Customer return"
        
        confirm_msg = f"Sale Return\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'SALE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-SALE-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("SALE", return_no, self.current_sale_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # Increase stock
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
                
                # Update sale items
                cursor.execute("""
                    UPDATE sale_items 
                    SET quantity = quantity - ?, total = total - ?
                    WHERE sale_id = ? AND product_id = ?
                """, (item['quantity'], item['total'], self.current_sale_id, item['product_id']))
            
            # Update sale total
            cursor.execute("UPDATE sales SET total_amount = total_amount - ? WHERE id = ?",
                          (total_refund, self.current_sale_id))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit)
                VALUES (?, ?, ?, ?)
            """, ("SALE_RETURN", return_no, f"Return from customer: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "SALE", str(self.current_sale_id), return_items, total_refund, reason)
            
            messagebox.showinfo("Success", f"Sale return processed!\nReturn No: {return_no}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            # Refresh
            self.load_sales_for_return_new()
            self.selected_sale_label.config(text="Selected Sale: None")
            self.sale_total_refund_label.config(text="Rs. 0.00")
            for widget in self.sale_return_items_frame.winfo_children():
                widget.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def on_sale_return_select(self, event):
        """When sale is selected, load its products with Pack/Piece options"""
        selected = self.sale_return_tree.selection()
        if not selected:
            return
        
        item = self.sale_return_tree.item(selected[0])
        sale_id = item['values'][0]
        invoice_no = item['values'][1]
        customer_name = item['values'][3]
        
        self.selected_sale_label.config(text=f"Selected Sale: {invoice_no} - {customer_name}")
        self.current_sale_id = sale_id
        
        # Clear existing
        for widget in self.return_products_frame.winfo_children():
            widget.destroy()
        self.return_product_vars = []
        
        # Load products from this sale with ACTUAL sold prices
        products = self.fetch_all("""
            SELECT si.product_id, p.name, si.price, si.quantity, p.cost_price,
                   IFNULL(p.unit_type, 'Piece'), IFNULL(p.pieces_per_pack, 1), IFNULL(p.pack_price, 0)
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        
        for product in products:
            product_id = product[0]
            product_name = product[1]
            sold_price = product[2]      # Actual price per piece at sale time
            sold_qty = product[3]        # Total pieces sold
            cost_price = product[4]
            unit_type = product[5] if len(product) > 5 else "Piece"
            pieces_per_pack = product[6] if len(product) > 6 and product[6] > 0 else 1
            pack_price = product[7] if len(product) > 7 and product[7] > 0 else sold_price * pieces_per_pack
            
            # Calculate piece price from pack price if needed
            if unit_type == "Pack" and pieces_per_pack > 0:
                actual_piece_price = pack_price / pieces_per_pack
            else:
                actual_piece_price = sold_price
            
            # Main frame
            prod_frame = tk.Frame(self.return_products_frame, bg="white", relief="ridge", bd=1)
            prod_frame.pack(fill="x", padx=5, pady=5)
            prod_frame.configure(width=700)
            prod_frame.pack_propagate(False)
            
            # Checkbox
            var = tk.BooleanVar()
            cb = tk.Checkbutton(prod_frame, text=product_name, variable=var, 
                                bg="white", font=("Arial", 10, "bold"),
                                command=self.update_return_total)
            cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            # Info
            info_frame = tk.Frame(prod_frame, bg="white")
            info_frame.grid(row=0, column=1, padx=10, pady=5)
            tk.Label(info_frame, text=f"Sold: {sold_qty} pieces", 
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            if unit_type == "Pack" and pieces_per_pack > 1:
                tk.Label(info_frame, text=f"Pack: {pieces_per_pack} pcs @ Rs.{pack_price:.2f} | Piece: Rs.{actual_piece_price:.2f}", 
                        font=("Arial", 8), bg="white", fg="#e94560").pack()
            else:
                tk.Label(info_frame, text=f"Piece price: Rs.{actual_piece_price:.2f}", 
                        font=("Arial", 8), bg="white", fg="#e94560").pack()
            
            product_data = {
                'var': var,
                'product_id': product_id,
                'name': product_name,
                'piece_price': actual_piece_price,
                'pack_price': pack_price,
                'max_qty': sold_qty,
                'pieces_per_pack': pieces_per_pack,
                'has_pack': (unit_type == "Pack" and pieces_per_pack > 1)
            }
            
            # Quantity container
            qty_container = tk.Frame(prod_frame, bg="white")
            qty_container.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            # Packs field
            if product_data['has_pack']:
                tk.Label(qty_container, text="Packs:", font=("Arial", 9), bg="white").pack(side="left")
                pack_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
                pack_entry.pack(side="left", padx=2)
                pack_entry.insert(0, "0")
                product_data['pack_qty'] = pack_entry
                pack_entry.bind("<KeyRelease>", lambda e: self.update_return_total())
            
            # Pieces field
            tk.Label(qty_container, text="Pieces:", font=("Arial", 9), bg="white").pack(side="left", padx=(10 if product_data['has_pack'] else 0, 2))
            piece_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            product_data['piece_qty'] = piece_entry
            piece_entry.bind("<KeyRelease>", lambda e: self.update_return_total())
            
            self.return_product_vars.append(product_data)
        
        self.update_return_total()
    
    def update_return_total(self):
        """Calculate total refund for sale return with quantity validation"""
        total = 0
        warning_msg = ""
        
        for item in self.return_product_vars:
            if not item['var'].get():
                continue
            
            # Calculate total pieces being returned
            total_pieces = 0
            
            if item.get('has_pack', False):
                try:
                    packs = int(item.get('pack_qty').get() or 0)
                    total_pieces += packs * item.get('pieces_per_pack', 1)
                except:
                    pass
            
            try:
                pieces = int(item.get('piece_qty').get() or 0)
                total_pieces += pieces
            except:
                pass
            
            # Validation: cannot return more than purchased
            max_allowed = item.get('max_qty', 0)
            if total_pieces > max_allowed:
                warning_msg += f"⚠️ {item['name']}: Cannot return more than {max_allowed} pieces (You entered {total_pieces})\n"
                continue
            
            # Calculate total refund
            if item.get('has_pack', False):
                try:
                    packs = int(item.get('pack_qty').get() or 0)
                    if packs > 0:
                        total += packs * item.get('pack_price', 0)
                except:
                    pass
            
            try:
                pieces = int(item.get('piece_qty').get() or 0)
                if pieces > 0:
                    total += pieces * item.get('piece_price', 0)
            except:
                pass
        
        # Update total label
        self.total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        # Show warning if any
        if warning_msg:
            # Create or update warning label
            if hasattr(self, 'return_warning_label'):
                self.return_warning_label.config(text=warning_msg, fg="red")
            else:
                self.return_warning_label = tk.Label(self.return_products_frame.master, 
                                                      text=warning_msg, 
                                                      font=("Arial", 9), 
                                                      bg="#ffe6e6", 
                                                      fg="#dc2626",
                                                      justify="left")
                self.return_warning_label.pack(fill="x", padx=10, pady=5)
        else:
            # Clear warning if exists
            if hasattr(self, 'return_warning_label'):
                self.return_warning_label.config(text="")
        
        return total
    def process_multi_sale_return(self):
        """Process multiple product return with Pack/Piece support"""
        if not hasattr(self, 'current_sale_id'):
            messagebox.showwarning("Error", "Please select a sale first!")
            return
        
        # Collect items to return
        return_items = []
        total_refund = 0
        
        for item in self.return_product_vars:
            if item['var'].get():
                if item.get('has_pack', False):
                    # Pack mode
                    try:
                        packs = int(item.get('pack_qty_entry', tk.Entry()).get() or 0)
                        extra = int(item.get('extra_pcs_entry', tk.Entry()).get() or 0)
                        if packs > 0 or extra > 0:
                            total_pieces = (packs * item.get('pieces_per_pack', 1)) + extra
                            if total_pieces > item.get('max_qty', 0):
                                messagebox.showwarning("Invalid Quantity", 
                                    f"Cannot return more than {item['max_qty']} units of {item['name']}!")
                                return
                            refund_amount = (packs * item.get('pack_price', 0)) + (extra * item.get('piece_price', 0))
                            return_items.append({
                                'product_id': item['product_id'],
                                'name': item['name'],
                                'quantity': total_pieces,
                                'packs': packs,
                                'extra': extra,
                                'price': item.get('piece_price', 0),
                                'pack_price': item.get('pack_price', 0),
                                'total': refund_amount
                            })
                            total_refund += refund_amount
                    except:
                        pass
                else:
                    # Simple piece mode
                    try:
                        qty = int(item.get('qty_entry', tk.Entry()).get() or 0)
                        if qty > 0:
                            if qty > item.get('max_qty', 0):
                                messagebox.showwarning("Invalid Quantity", 
                                    f"Cannot return more than {item['max_qty']} units of {item['name']}!")
                                return
                            return_items.append({
                                'product_id': item['product_id'],
                                'name': item['name'],
                                'quantity': qty,
                                'packs': 0,
                                'extra': qty,
                                'price': item.get('price', 0),
                                'total': qty * item.get('price', 0)
                            })
                            total_refund += qty * item.get('price', 0)
                    except:
                        pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select at least one product to return!")
            return
        
        reason = "Customer return"
        
        sale = self.fetch_one("SELECT invoice_no, customer_name, total_amount FROM sales WHERE id = ?", (self.current_sale_id,))
        if not sale:
            messagebox.showerror("Error", "Sale not found!")
            return
        
        confirm_msg = f"Sale: {sale[0]}\nCustomer: {sale[1]}\n\nReturn Items:\n"
        for item in return_items:
            if item.get('packs', 0) > 0 or item.get('extra', 0) > 0:
                confirm_msg += f"  - {item['name']}: {item.get('packs',0)} pack + {item.get('extra',0)} pcs = Rs.{item['total']:.0f}\n"
            else:
                confirm_msg += f"  - {item['name']}: {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        confirm_msg += f"\nTotal Refund: Rs. {total_refund:,.2f}\nReason: {reason}\n\nProceed?"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'SALE' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-SALE-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("SALE", return_no, self.current_sale_id, item['product_id'], item['quantity'], item['total'], reason))
                
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", 
                              (item['quantity'], item['product_id']))
                
                cursor.execute("""
                    UPDATE sale_items 
                    SET quantity = quantity - ?, total = total - ?
                    WHERE sale_id = ? AND product_id = ?
                """, (item['quantity'], item['total'], self.current_sale_id, item['product_id']))
            
            current_sale = cursor.execute("SELECT total_amount FROM sales WHERE id = ?", (self.current_sale_id,)).fetchone()
            new_sale_total = current_sale[0] - total_refund
            cursor.execute("UPDATE sales SET total_amount = ? WHERE id = ?", (new_sale_total, self.current_sale_id))
            
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                VALUES (?, ?, ?, ?, ?)
            """, ("SALE_RETURN", return_no, f"Return from {sale[1]}: {len(return_items)} items", total_refund, 0))
            
            conn.commit()
            conn.close()
            
            self.print_return_slip(return_no, "SALE", sale[1], return_items, total_refund, reason)
            messagebox.showinfo("Success", 
                f"Sale return processed!\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\nTotal Refund: Rs. {total_refund:,.2f}")
            
            self.load_sales_for_return()
            self.selected_sale_label.config(text="Selected Sale: None")
            self.total_refund_label.config(text="Rs. 0.00")
            
            for widget in self.return_products_frame.winfo_children():
                widget.destroy()
            self.return_product_vars = []
            
            self.update_status(f"✅ Return processed: {len(return_items)} items, Refund: Rs.{total_refund:,.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def load_sales_for_return(self):
        """Load all sales for return selection"""
        for item in self.sale_return_tree.get_children():
            self.sale_return_tree.delete(item)
        
        sales = self.fetch_all("""
            SELECT id, invoice_no, sale_date, customer_name, total_amount
            FROM sales
            ORDER BY id DESC LIMIT 500
        """)
        
        for sale in sales:
            self.sale_return_tree.insert("", "end", values=(
                sale[0], sale[1], sale[2][:10] if sale[2] else "-",
                sale[3] or "N/A", f"Rs. {sale[4]:,.2f}"
            ))
    
    def on_sale_select(self, event):
        """When sale is selected, load its products with checkboxes"""
        selected = self.sale_return_tree.selection()
        if not selected:
            return
        
        item = self.sale_return_tree.item(selected[0])
        sale_id = item['values'][0]
        invoice_no = item['values'][1]
        customer_name = item['values'][3]
        
        self.selected_sale_label.config(text=f"Selected Sale: {invoice_no} - {customer_name}")
        self.current_sale_id = sale_id
        
        # Clear existing product widgets
        for widget in self.return_products_frame.winfo_children():
            widget.destroy()
        self.return_product_vars = []
        
        # Load products from this sale
        products = self.fetch_all("""
            SELECT si.product_id, p.name, p.price, si.quantity, p.stock_quantity
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        
        self.current_sale_products_data = products
        
        # Create checkbox for each product
        for i, product in enumerate(products):
            product_id = product[0]
            product_name = product[1]
            price = product[2]
            sold_qty = product[3]
            
            prod_frame = tk.Frame(self.return_products_frame, bg="white", relief="ridge", bd=1)
            prod_frame.pack(fill="x", padx=5, pady=5)
            prod_frame.configure(width=600)
            prod_frame.pack_propagate(False)
            
            # Checkbox
            var = tk.BooleanVar()
            cb = tk.Checkbutton(prod_frame, text=f"{product_name}", variable=var, 
                                bg="white", font=("Arial", 10, "bold"),
                                command=lambda: self.update_return_total())
            cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            # Product info
            info_frame = tk.Frame(prod_frame, bg="white")
            info_frame.grid(row=0, column=1, padx=10, pady=5)
            tk.Label(info_frame, text=f"Price: Rs.{price:.2f} | Sold: {sold_qty} units", 
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            # Quantity entry
            qty_frame = tk.Frame(prod_frame, bg="white")
            qty_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            tk.Label(qty_frame, text="Return Qty:", font=("Arial", 9), bg="white").pack(side="left")
            qty_entry = tk.Entry(qty_frame, width=6, font=("Arial", 10), justify="center")
            qty_entry.pack(side="left", padx=5)
            qty_entry.insert(0, "0")
            qty_entry.bind("<KeyRelease>", lambda e: self.update_return_total())
            
            # Configure column weights
            prod_frame.grid_columnconfigure(0, weight=0)
            prod_frame.grid_columnconfigure(1, weight=1)
            prod_frame.grid_columnconfigure(2, weight=0)
            
            self.return_product_vars.append({
                'var': var,
                'qty_entry': qty_entry,
                'product_id': product_id,
                'name': product_name,
                'price': price,
                'max_qty': sold_qty
            })
    
    def load_sales_for_return(self):
        """Load all sales for return selection"""
        for item in self.sale_return_tree.get_children():
            self.sale_return_tree.delete(item)
        
        sales = self.fetch_all("""
            SELECT id, invoice_no, sale_date, customer_name, total_amount
            FROM sales
            ORDER BY id DESC LIMIT 500
        """)
        
        for sale in sales:
            self.sale_return_tree.insert("", "end", values=(
                sale[0], sale[1], sale[2][:10] if sale[2] else "-",
                sale[3] or "N/A", f"Rs. {sale[4]:,.2f}", "Active"
            ))
    
    def update_sale_return_price(self, event=None):
        """Auto-fill refund amount when product selected"""
        if not hasattr(self, 'current_sale_products') or not self.current_sale_products:
            return
        
        if self.sale_return_product.get():
            try:
                product_id = int(self.sale_return_product.get().split(" - ")[0])
                for prod in self.current_sale_products:
                    if prod[0] == product_id:
                        self.sale_available_qty_label.config(text=str(prod[2]))
                        self.sale_return_refund.delete(0, tk.END)
                        self.sale_return_refund.insert(0, str(prod[3]))
                        self.current_return_product_id = product_id
                        self.current_return_product_name = prod[1]
                        self.current_return_max_qty = prod[2]
                        break
            except:
                pass
    
    def process_sale_return(self):
        """Process sale return - Updates Dashboard, Profit, and Stock"""
        import time
        time.sleep(0.3)
        
        
        if not hasattr(self, 'current_sale_id'):
            messagebox.showwarning("Error", "Please select a sale first!")
            return
        
        if not self.sale_return_product.get():
            messagebox.showwarning("Error", "Please select a product!")
            return
        
        try:
            quantity = int(self.sale_return_qty.get())
            if quantity <= 0:
                messagebox.showwarning("Error", "Quantity must be greater than 0!")
                return
            if quantity > self.current_return_max_qty:
                messagebox.showwarning("Error", f"Maximum return quantity is {self.current_return_max_qty}!")
                return
        except:
            messagebox.showwarning("Error", "Invalid quantity!")
            return
        
        try:
            refund_amount = float(self.sale_return_refund.get())
            if refund_amount <= 0:
                messagebox.showwarning("Error", "Refund amount must be greater than 0!")
                return
        except:
            messagebox.showwarning("Error", "Invalid refund amount!")
            return
        
        reason = self.sale_return_reason.get()
        product_name = self.current_return_product_name
        
        sale = self.fetch_one("SELECT invoice_no, customer_name, total_amount FROM sales WHERE id = ?", (self.current_sale_id,))
        if not sale:
            messagebox.showerror("Error", "Sale not found!")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Return",
            f"Sale: {sale[0]}\nCustomer: {sale[1]}\nProduct: {product_name}\nQuantity: {quantity}\nRefund: Rs. {refund_amount:,.2f}\nReason: {reason}\n\nProceed?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            return_no = f"RET-SALE-{datetime.now().year}{datetime.now().strftime('%d%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("SALE", return_no, self.current_sale_id, self.current_return_product_id, quantity, refund_amount, reason))
            
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", (quantity, self.current_return_product_id))
            
            current_sale = cursor.execute("SELECT total_amount FROM sales WHERE id = ?", (self.current_sale_id,)).fetchone()
            new_sale_total = current_sale[0] - refund_amount
            cursor.execute("UPDATE sales SET total_amount = ? WHERE id = ?", (new_sale_total, self.current_sale_id))
            
            cursor.execute("""
                UPDATE sale_items 
                SET quantity = quantity - ?, total = total - ?
                WHERE sale_id = ? AND product_id = ?
            """, (quantity, refund_amount, self.current_sale_id, self.current_return_product_id))
            
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                VALUES (?, ?, ?, ?, ?)
            """, ("SALE_RETURN", return_no, f"Return from {sale[1]}: {product_name} x{quantity}", refund_amount, 0))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Sale return processed!\nRefund: Rs. {refund_amount:,.2f}")
            self.sale_return_qty.delete(0, tk.END)
            self.load_sales_for_return()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def create_transfer_return_tab(self, parent):
        """Transfer Return Tab - Right Click Context Menu with Pack/Piece Window"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="🔄 TRANSFER RETURN (FROM CITY)", 
                font=("Helvetica", 20, "bold"), bg="#f5f5f5", fg="#36b9cc").pack(pady=5)
        
        # Main Frame - All Transfers List
        list_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="📋 ALL CITY TRANSFERS", font=("Arial", 14, "bold"), 
                bg="#36b9cc", fg="white", pady=8).pack(fill="x")
        
        # Search
        search_frame = tk.Frame(list_frame, bg="white", padx=10, pady=5)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 10), bg="white").pack(side="left")
        self.transfer_return_search = tk.Entry(search_frame, font=("Arial", 10), width=30)
        self.transfer_return_search.pack(side="left", padx=5)
        self.transfer_return_search.bind("<KeyRelease>", lambda e: self.load_all_transfers())
        
        # Treeview
        tree_frame = tk.Frame(list_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Transfer No", "Date", "City", "Recipient", "Total Amount", "Items")
        self.transfer_list_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        self.transfer_list_tree.heading("ID", text="ID", anchor="center")
        self.transfer_list_tree.heading("Transfer No", text="Transfer No", anchor="center")
        self.transfer_list_tree.heading("Date", text="Date", anchor="center")
        self.transfer_list_tree.heading("City", text="City", anchor="center")
        self.transfer_list_tree.heading("Recipient", text="Recipient", anchor="center")
        self.transfer_list_tree.heading("Total Amount", text="Total Amount (Rs.)", anchor="center")
        self.transfer_list_tree.heading("Items", text="Items", anchor="center")
        
        self.transfer_list_tree.column("ID", width=50, anchor="center")
        self.transfer_list_tree.column("Transfer No", width=130, anchor="center")
        self.transfer_list_tree.column("Date", width=100, anchor="center")
        self.transfer_list_tree.column("City", width=120, anchor="center")
        self.transfer_list_tree.column("Recipient", width=150, anchor="w")
        self.transfer_list_tree.column("Total Amount", width=120, anchor="e")
        self.transfer_list_tree.column("Items", width=80, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.transfer_list_tree.yview)
        self.transfer_list_tree.configure(yscrollcommand=vsb.set)
        self.transfer_list_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Right Click Menu
        self.transfer_context_menu = tk.Menu(self.root, tearoff=0)
        self.transfer_context_menu.add_command(label="🔄 Return Items", command=self.open_transfer_return_window)
        
        self.transfer_list_tree.bind("<Button-3>", self.show_transfer_context_menu)
        
        # Load all transfers
        self.load_all_transfers()
    
    def load_all_transfers(self):
        """Load all transfers into treeview"""
        for item in self.transfer_list_tree.get_children():
            self.transfer_list_tree.delete(item)
        
        search = self.transfer_return_search.get().strip() if hasattr(self, 'transfer_return_search') else ""
        
        if search:
            query = """
                SELECT st.id, st.transfer_no, st.transfer_date, st.destination_city, 
                       st.recipient_name, st.total_amount,
                       (SELECT COUNT(*) FROM transfer_items WHERE transfer_id = st.id) as item_count
                FROM stock_transfers st
                WHERE st.transfer_no LIKE ? OR st.destination_city LIKE ? OR st.recipient_name LIKE ?
                ORDER BY st.id DESC
            """
            params = (f'%{search}%', f'%{search}%', f'%{search}%')
        else:
            query = """
                SELECT st.id, st.transfer_no, st.transfer_date, st.destination_city, 
                       st.recipient_name, st.total_amount,
                       (SELECT COUNT(*) FROM transfer_items WHERE transfer_id = st.id) as item_count
                FROM stock_transfers st
                ORDER BY st.id DESC
            """
            params = ()
        
        transfers = self.fetch_all(query, params)
        for t in transfers:
            self.transfer_list_tree.insert("", "end", values=(
                t[0], t[1], t[2][:10] if t[2] else "-", t[3], t[4] or "-", f"Rs. {t[5]:,.2f}", t[6]
            ))
        
        self.update_status(f"Loaded {len(transfers)} transfers")
    
    def show_transfer_context_menu(self, event):
        """Show right click context menu for transfers"""
        item = self.transfer_list_tree.identify_row(event.y)
        if item:
            self.transfer_list_tree.selection_set(item)
            self.transfer_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_transfer_for_return(self):
        """Get selected transfer ID"""
        selected = self.transfer_list_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a transfer first!")
            return None
        item = self.transfer_list_tree.item(selected[0])
        return item['values'][0]
    
    def open_transfer_return_window(self):
        """Open return window for selected transfer"""
        transfer_id = self.get_selected_transfer_for_return()
        if not transfer_id:
            return
        
        # Get transfer details
        transfer = self.fetch_one("""
            SELECT st.id, st.transfer_no, st.destination_city, st.recipient_name, st.transfer_date, st.total_amount
            FROM stock_transfers st
            WHERE st.id = ?
        """, (transfer_id,))
        
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        # Get all items from this transfer
        items = self.fetch_all("""
            SELECT ti.product_id, p.name, ti.quantity, ti.price,
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, ti.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transfer_id = ?
        """, (transfer_id,))
        
        if not items:
            messagebox.showwarning("Error", "No items found in this transfer!")
            return
        
        # Create Return Window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Return Items - {transfer[1]} ({transfer[2]})")
        dialog.geometry("750x600")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"🔄 TRANSFER RETURN", font=("Helvetica", 16, "bold"),
                bg="#1a1a2e", fg="#36b9cc").pack(pady=(10, 0))
        tk.Label(header_frame, text=f"Transfer: {transfer[1]} | City: {transfer[2]} | Recipient: {transfer[3] or '-'} | Date: {transfer[4][:10]}",
                font=("Arial", 10), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # Main scrollable area for items
        canvas_container = tk.Frame(dialog, bg="#f5f5f5")
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Header Row
        header_row = tk.Frame(scroll_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Product", 22), ("Transferred Qty", 8), ("Pack Price", 12), 
                   ("Piece Price", 12), ("Packs Return", 6), ("Pieces Return", 6), ("Refund", 12)]
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Arial", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        return_items_data = []
        
        for idx, item in enumerate(items):
            product_id = item[0]
            product_name = item[1]
            transferred_qty = item[2]
            transfer_price = item[3]
            pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
            pack_price = item[5] if item[5] and item[5] > 0 else transfer_price * pieces_per_pack
            piece_price = pack_price / pieces_per_pack if pieces_per_pack > 0 else transfer_price
            
            row = tk.Frame(scroll_frame, bg="white", relief="ridge", bd=1)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=product_name[:22], width=22, bg="white", anchor="w", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=str(transferred_qty), width=8, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            
            pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            pack_entry.pack(side="left", padx=2)
            pack_entry.insert(0, "0")
            
            piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            
            refund_label = tk.Label(row, text="Rs.0", width=12, bg="white", anchor="center",
                                    font=("Arial", 9, "bold"), fg="#36b9cc")
            refund_label.pack(side="left", padx=2)
            
            item_data = {
                'product_id': product_id, 'name': product_name,
                'pack_entry': pack_entry, 'piece_entry': piece_entry,
                'refund_label': refund_label, 'pack_price': pack_price,
                'piece_price': piece_price, 'pieces_per_pack': pieces_per_pack,
                'max_qty': transferred_qty
            }
            return_items_data.append(item_data)
            
            pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_transfer_return_refund(return_items_data[i]))
            piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_transfer_return_refund(return_items_data[i]))
        
        # Total Refund Frame
        total_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        total_inner = tk.Frame(total_frame, bg="white", padx=15, pady=10)
        total_inner.pack()
        
        tk.Label(total_inner, text="💰 TOTAL REFUND:", font=("Arial", 16, "bold"),
                bg="white", fg="#36b9cc").pack(side="left", padx=10)
        total_refund_label = tk.Label(total_inner, text="Rs. 0.00", font=("Arial", 18, "bold"),
                                      bg="white", fg="#36b9cc")
        total_refund_label.pack(side="left", padx=10)
        
        def calculate_total():
            total = 0
            for itm in return_items_data:
                try:
                    packs = int(itm['pack_entry'].get() or 0)
                    pieces = int(itm['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pcs = (packs * itm['pieces_per_pack']) + pieces
                        if total_pcs <= itm['max_qty']:
                            total += (packs * itm['pack_price']) + (pieces * itm['piece_price'])
                except:
                    pass
            total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        dialog.calculate_total = calculate_total
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="✅ COMPLETE TRANSFER RETURN", 
                 command=lambda: self.execute_transfer_return(transfer_id, transfer[1], return_items_data, total_refund_label, dialog),
                 bg="#36b9cc", fg="white", font=("Arial", 12, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy,
                 bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        calculate_total()
    
    def update_transfer_return_refund(self, item):
        """Update refund for a single transfer return item - Packs + Pieces both work together"""
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Total pieces = (packs * pieces_per_pack) + extra pieces
            total_pcs = (packs * item['pieces_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text=f"Max {item['max_qty']}", fg="red")
            elif total_pcs == 0:
                item['refund_label'].config(text="Rs.0", fg="#36b9cc")
            else:
                # Calculate refund: (packs * pack_price) + (pieces * piece_price)
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                # Show what was returned
                if packs > 0 and pieces > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk+{pieces}pcs)", fg="#36b9cc")
                elif packs > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk)", fg="#36b9cc")
                else:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({pieces}pcs)", fg="#36b9cc")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        # Find parent window and update total
        try:
            dialog = item['refund_label'].winfo_toplevel()
            if hasattr(dialog, 'calculate_total'):
                dialog.calculate_total()
        except:
            pass
    
    def execute_transfer_return(self, transfer_id, transfer_no, return_items_data, total_label, dialog):
        """Execute the transfer return - Stock INCREASE and Payment AUTO-UPDATE"""
        return_items = []
        total_refund = 0
        
        for item in return_items_data:
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                if packs > 0 or pieces > 0:
                    total_pcs = (packs * item['pieces_per_pack']) + pieces
                    if total_pcs > item['max_qty']:
                        messagebox.showwarning("Invalid Quantity", 
                            f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                        return
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    return_items.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': total_pcs,
                        'total': refund,
                        'packs': packs,
                        'pieces': pieces
                    })
                    total_refund += refund
            except:
                pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please enter quantity to return!")
            return
        
        # Get current transfer details for payment update
        transfer = self.fetch_one("""
            SELECT id, transfer_no, total_amount, amount_paid, balance_due, payment_status
            FROM stock_transfers WHERE id = ?
        """, (transfer_id,))
        
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        current_total = transfer[2] or 0
        current_paid = transfer[3] or 0
        current_balance = transfer[4] or 0
        
        # Calculate new values after return
        new_total = current_total - total_refund
        new_balance = current_balance - total_refund
        
        if new_balance <= 0:
            new_status = "Paid"
            new_paid = new_total
            new_balance = 0
        elif new_balance > 0 and current_paid > 0:
            new_status = "Partial"
            new_paid = current_paid
        else:
            new_status = "Pending"
            new_paid = 0
        
        confirm_msg = f"🔄 TRANSFER RETURN\n\nTransfer: {transfer_no}\n"
        confirm_msg += f"Original Total: Rs. {current_total:,.2f}\n"
        confirm_msg += f"Return Amount: Rs. {total_refund:,.2f}\n"
        confirm_msg += f"New Total: Rs. {new_total:,.2f}\n"
        confirm_msg += f"New Balance: Rs. {new_balance:,.2f}\n"
        confirm_msg += f"Payment Status: {new_status}\n\n"
        confirm_msg += "Items:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['packs']} pack + {item['pieces']} pcs = {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'TRANSFER' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                new_num = int(parts[-1]) + 1 if len(parts) >= 3 else 1
            else:
                new_num = 1
            
            return_no = f"RET-TRF-{new_num:03d}"
            reason = "Return from city"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("TRANSFER", return_no, transfer_id, item['product_id'], 
                      item['quantity'], item['total'], reason))
                
                # Stock INCREASE - mal wapas aa raha hai
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # UPDATE TRANSFER PAYMENT STATUS
            cursor.execute("""
                UPDATE stock_transfers 
                SET total_amount = ?, amount_paid = ?, balance_due = ?, payment_status = ?
                WHERE id = ?
            """, (new_total, new_paid, new_balance, new_status, transfer_id))
            
            # Ledger entry
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("TRANSFER_RETURN", return_no, f"Return from city: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "TRANSFER", transfer_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Transfer return processed!\n\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\n"
                f"Return Amount: Rs. {total_refund:,.2f}\n"
                f"New Transfer Total: Rs. {new_total:,.2f}\n"
                f"Payment Status: {new_status}\n"
                f"Balance Due: Rs. {new_balance:,.2f}")
            
            dialog.destroy()
            
            # Refresh all lists
            self.load_all_transfers()
            self.load_pending_transfers()  # Refresh Receive Payment tab
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_all_transfers(self):
        """Load all transfers into treeview"""
        for item in self.transfer_list_tree.get_children():
            self.transfer_list_tree.delete(item)
        
        search = self.transfer_return_search.get().strip() if hasattr(self, 'transfer_return_search') else ""
        
        if search:
            query = """
                SELECT st.id, st.transfer_no, st.transfer_date, st.destination_city, 
                       st.recipient_name, st.total_amount,
                       (SELECT COUNT(*) FROM transfer_items WHERE transfer_id = st.id) as item_count
                FROM stock_transfers st
                WHERE st.transfer_no LIKE ? OR st.destination_city LIKE ? OR st.recipient_name LIKE ?
                ORDER BY st.id DESC
            """
            params = (f'%{search}%', f'%{search}%', f'%{search}%')
        else:
            query = """
                SELECT st.id, st.transfer_no, st.transfer_date, st.destination_city, 
                       st.recipient_name, st.total_amount,
                       (SELECT COUNT(*) FROM transfer_items WHERE transfer_id = st.id) as item_count
                FROM stock_transfers st
                ORDER BY st.id DESC
            """
            params = ()
        
        transfers = self.fetch_all(query, params)
        for t in transfers:
            self.transfer_list_tree.insert("", "end", values=(
                t[0], t[1], t[2][:10] if t[2] else "-", t[3], t[4] or "-", f"Rs. {t[5]:,.2f}", t[6]
            ))
        
        self.update_status(f"Loaded {len(transfers)} transfers")
    
    def show_transfer_context_menu(self, event):
        """Show right click context menu for transfers"""
        item = self.transfer_list_tree.identify_row(event.y)
        if item:
            self.transfer_list_tree.selection_set(item)
            self.transfer_context_menu.post(event.x_root, event.y_root)
    
    def get_selected_transfer_for_return(self):
        """Get selected transfer ID"""
        selected = self.transfer_list_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a transfer first!")
            return None
        item = self.transfer_list_tree.item(selected[0])
        return item['values'][0]
    
    def open_transfer_return_window(self):
        """Open return window for selected transfer"""
        transfer_id = self.get_selected_transfer_for_return()
        if not transfer_id:
            return
        
        # Get transfer details
        transfer = self.fetch_one("""
            SELECT st.id, st.transfer_no, st.destination_city, st.recipient_name, st.transfer_date, st.total_amount
            FROM stock_transfers st
            WHERE st.id = ?
        """, (transfer_id,))
        
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        # Get all items from this transfer
        items = self.fetch_all("""
            SELECT ti.product_id, p.name, ti.quantity, ti.price,
                   COALESCE(p.pieces_per_pack, 1) as pieces_per_pack,
                   COALESCE(p.pack_price, ti.price * COALESCE(p.pieces_per_pack, 1)) as pack_price,
                   COALESCE(p.unit_type, 'Piece') as unit_type
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transfer_id = ?
        """, (transfer_id,))
        
        if not items:
            messagebox.showwarning("Error", "No items found in this transfer!")
            return
        
        # Create Return Window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Return Items - {transfer[1]} ({transfer[2]})")
        dialog.geometry("750x600")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg="#1a1a2e", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"🔄 TRANSFER RETURN", font=("Helvetica", 16, "bold"),
                bg="#1a1a2e", fg="#36b9cc").pack(pady=(10, 0))
        tk.Label(header_frame, text=f"Transfer: {transfer[1]} | City: {transfer[2]} | Recipient: {transfer[3] or '-'} | Date: {transfer[4][:10]}",
                font=("Arial", 10), bg="#1a1a2e", fg="#a8d8ea").pack()
        
        # Main scrollable area for items
        canvas_container = tk.Frame(dialog, bg="#f5f5f5")
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Header Row
        header_row = tk.Frame(scroll_frame, bg="#2c3e50", height=35)
        header_row.pack(fill="x", pady=(0, 5))
        
        headers = [("Product", 22), ("Transferred Qty", 8), ("Pack Price", 12), 
                   ("Piece Price", 12), ("Packs Return", 6), ("Pieces Return", 6), ("Refund", 12)]
        for text, width in headers:
            tk.Label(header_row, text=text, width=width, bg="#2c3e50", 
                    font=("Arial", 9, "bold"), fg="white").pack(side="left", padx=2)
        
        return_items_data = []
        
        for idx, item in enumerate(items):
            product_id = item[0]
            product_name = item[1]
            transferred_qty = item[2]
            transfer_price = item[3]
            pieces_per_pack = item[4] if item[4] and item[4] > 0 else 1
            pack_price = item[5] if item[5] and item[5] > 0 else transfer_price * pieces_per_pack
            piece_price = pack_price / pieces_per_pack if pieces_per_pack > 0 else transfer_price
            
            row = tk.Frame(scroll_frame, bg="white", relief="ridge", bd=1)
            row.pack(fill="x", pady=2)
            
            tk.Label(row, text=product_name[:22], width=22, bg="white", anchor="w", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=str(transferred_qty), width=8, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{pack_price:.0f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            tk.Label(row, text=f"Rs.{piece_price:.2f}", width=12, bg="white", anchor="center", font=("Arial", 9)).pack(side="left", padx=2)
            
            pack_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            pack_entry.pack(side="left", padx=2)
            pack_entry.insert(0, "0")
            
            piece_entry = tk.Entry(row, width=6, font=("Arial", 9), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            
            refund_label = tk.Label(row, text="Rs.0", width=12, bg="white", anchor="center",
                                    font=("Arial", 9, "bold"), fg="#36b9cc")
            refund_label.pack(side="left", padx=2)
            
            item_data = {
                'product_id': product_id, 'name': product_name,
                'pack_entry': pack_entry, 'piece_entry': piece_entry,
                'refund_label': refund_label, 'pack_price': pack_price,
                'piece_price': piece_price, 'pieces_per_pack': pieces_per_pack,
                'max_qty': transferred_qty
            }
            return_items_data.append(item_data)
            
            pack_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_transfer_return_refund(return_items_data[i]))
            piece_entry.bind("<KeyRelease>", lambda e, i=idx: self.update_transfer_return_refund(return_items_data[i]))
        
        # Total Refund Frame
        total_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=10)
        
        total_inner = tk.Frame(total_frame, bg="white", padx=15, pady=10)
        total_inner.pack()
        
        tk.Label(total_inner, text="💰 TOTAL REFUND:", font=("Arial", 16, "bold"),
                bg="white", fg="#36b9cc").pack(side="left", padx=10)
        total_refund_label = tk.Label(total_inner, text="Rs. 0.00", font=("Arial", 18, "bold"),
                                      bg="white", fg="#36b9cc")
        total_refund_label.pack(side="left", padx=10)
        
        def calculate_total():
            total = 0
            for itm in return_items_data:
                try:
                    packs = int(itm['pack_entry'].get() or 0)
                    pieces = int(itm['piece_entry'].get() or 0)
                    if packs > 0 or pieces > 0:
                        total_pcs = (packs * itm['pieces_per_pack']) + pieces
                        if total_pcs <= itm['max_qty']:
                            total += (packs * itm['pack_price']) + (pieces * itm['piece_price'])
                except:
                    pass
            total_refund_label.config(text=f"Rs. {total:,.2f}")
        
        dialog.calculate_total = calculate_total
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="✅ COMPLETE TRANSFER RETURN", 
                 command=lambda: self.execute_transfer_return(transfer_id, transfer[1], return_items_data, total_refund_label, dialog),
                 bg="#36b9cc", fg="white", font=("Arial", 12, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        tk.Button(btn_frame, text="❌ CANCEL", command=dialog.destroy,
                 bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                 padx=25, pady=10, relief="flat", cursor="hand2").pack(side="left", expand=True, padx=5)
        
        calculate_total()
    
    def update_transfer_return_refund(self, item):
        """Update refund for a single transfer return item - Packs + Pieces both work together"""
        try:
            packs = int(item['pack_entry'].get() or 0)
            pieces = int(item['piece_entry'].get() or 0)
            
            # Total pieces = (packs * pieces_per_pack) + extra pieces
            total_pcs = (packs * item['pieces_per_pack']) + pieces
            
            if total_pcs > item['max_qty']:
                item['refund_label'].config(text=f"Max {item['max_qty']}", fg="red")
            elif total_pcs == 0:
                item['refund_label'].config(text="Rs.0", fg="#36b9cc")
            else:
                # Calculate refund: (packs * pack_price) + (pieces * piece_price)
                refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                # Show what was returned
                if packs > 0 and pieces > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk+{pieces}pcs)", fg="#36b9cc")
                elif packs > 0:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({packs}pk)", fg="#36b9cc")
                else:
                    item['refund_label'].config(text=f"Rs.{refund:.0f} ({pieces}pcs)", fg="#36b9cc")
        except:
            item['refund_label'].config(text="Invalid", fg="red")
        
        # Find parent window and update total
        try:
            dialog = item['refund_label'].winfo_toplevel()
            if hasattr(dialog, 'calculate_total'):
                dialog.calculate_total()
        except:
            pass
    
    def execute_transfer_return(self, transfer_id, transfer_no, return_items_data, total_label, dialog):
        """Execute the transfer return - Stock INCREASE hota hai (mal wapas aa raha hai)"""
        return_items = []
        total_refund = 0
        
        for item in return_items_data:
            try:
                packs = int(item['pack_entry'].get() or 0)
                pieces = int(item['piece_entry'].get() or 0)
                if packs > 0 or pieces > 0:
                    total_pcs = (packs * item['pieces_per_pack']) + pieces
                    if total_pcs > item['max_qty']:
                        messagebox.showwarning("Invalid Quantity", 
                            f"Cannot return more than {item['max_qty']} pieces of {item['name']}!")
                        return
                    refund = (packs * item['pack_price']) + (pieces * item['piece_price'])
                    return_items.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': total_pcs,
                        'total': refund,
                        'packs': packs,
                        'pieces': pieces
                    })
                    total_refund += refund
            except:
                pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please enter quantity to return!")
            return
        
        confirm_msg = f"🔄 TRANSFER RETURN\n\nTransfer: {transfer_no}\nTotal Refund: Rs. {total_refund:,.2f}\n\nItems:\n"
        for item in return_items:
            confirm_msg += f"  • {item['name']}: {item['packs']} pack + {item['pieces']} pcs = {item['quantity']} pcs = Rs.{item['total']:.0f}\n"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'TRANSFER' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                new_num = int(parts[-1]) + 1 if len(parts) >= 3 else 1
            else:
                new_num = 1
            
            return_no = f"RET-TRF-{new_num:03d}"
            reason = "Return from city"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("TRANSFER", return_no, transfer_id, item['product_id'], 
                      item['quantity'], item['total'], reason))
                
                # IMPORTANT: Stock INCREASE - mal wapas warehouse mein aa raha hai
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                              (item['quantity'], item['product_id']))
            
            # Ledger entry (Credit - mal wapas aya)
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("TRANSFER_RETURN", return_no, f"Return from city: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print return slip
            self.print_return_slip(return_no, "TRANSFER", transfer_no, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"✅ Transfer return processed!\n\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\nTotal Refund: Rs. {total_refund:,.2f}\n\n"
                f"📦 Stock has been INCREASED by {len(return_items)} items.")
            
            dialog.destroy()
            
            # Refresh transfer list
            self.load_all_transfers()
            self.load_pending_transfers()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {str(e)}")
    
    def load_transfers_for_return(self):
        """Load all transfers for return selection"""
        for item in self.transfer_return_tree.get_children():
            self.transfer_return_tree.delete(item)
        
        transfers = self.fetch_all("""
            SELECT id, transfer_no, transfer_date, destination_city, recipient_name, total_amount
            FROM stock_transfers
            ORDER BY id DESC
        """)
        
        for transfer in transfers:
            self.transfer_return_tree.insert("", "end", values=(
                transfer[0], transfer[1], transfer[2][:10] if transfer[2] else "-",
                transfer[3], transfer[4] or "-", f"Rs. {transfer[5]:,.2f}"
            ))
    
    def on_transfer_return_select(self, event):
        """When transfer is selected, load its products with Pack/Piece options"""
        selected = self.transfer_return_tree.selection()
        if not selected:
            return
        
        item = self.transfer_return_tree.item(selected[0])
        transfer_id = item['values'][0]
        transfer_no = item['values'][1]
        city = item['values'][3]
        
        self.selected_transfer_label.config(text=f"Selected Transfer: {transfer_no} - {city}")
        self.current_transfer_id = transfer_id
        
        # Clear existing
        for widget in self.transfer_return_products_frame.winfo_children():
            widget.destroy()
        self.transfer_return_vars = []
        
        # Load products from this transfer
        products = self.fetch_all("""
            SELECT ti.product_id, p.name, ti.price, ti.quantity, p.cost_price,
                   IFNULL(p.unit_type, 'Piece'), IFNULL(p.pieces_per_pack, 1), IFNULL(p.pack_price, 0)
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transfer_id = ?
        """, (transfer_id,))
        
        for product in products:
            product_id = product[0]
            product_name = product[1]
            transfer_price = product[2]     # Price per piece at transfer time
            transferred_qty = product[3]
            cost_price = product[4]
            unit_type = product[5] if len(product) > 5 else "Piece"
            pieces_per_pack = product[6] if len(product) > 6 and product[6] > 0 else 1
            pack_price = product[7] if len(product) > 7 and product[7] > 0 else transfer_price * pieces_per_pack
            
            # Calculate piece price
            if unit_type == "Pack" and pieces_per_pack > 0:
                actual_piece_price = pack_price / pieces_per_pack
            else:
                actual_piece_price = transfer_price
            
            # Main frame
            prod_frame = tk.Frame(self.transfer_return_products_frame, bg="white", relief="ridge", bd=1)
            prod_frame.pack(fill="x", padx=5, pady=5)
            prod_frame.configure(width=700)
            prod_frame.pack_propagate(False)
            
            # Checkbox
            var = tk.BooleanVar()
            cb = tk.Checkbutton(prod_frame, text=product_name, variable=var, 
                                bg="white", font=("Arial", 10, "bold"),
                                command=self.update_transfer_return_total)
            cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            # Info
            info_frame = tk.Frame(prod_frame, bg="white")
            info_frame.grid(row=0, column=1, padx=10, pady=5)
            tk.Label(info_frame, text=f"Transferred: {transferred_qty} pieces", 
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            if unit_type == "Pack" and pieces_per_pack > 1:
                tk.Label(info_frame, text=f"Pack: {pieces_per_pack} pcs @ Rs.{pack_price:.2f} | Piece: Rs.{actual_piece_price:.2f}", 
                        font=("Arial", 8), bg="white", fg="#e94560").pack()
            
            product_data = {
                'var': var,
                'product_id': product_id,
                'name': product_name,
                'piece_price': actual_piece_price,
                'pack_price': pack_price,
                'max_qty': transferred_qty,
                'pieces_per_pack': pieces_per_pack,
                'has_pack': (unit_type == "Pack" and pieces_per_pack > 1)
            }
            
            # Quantity container
            qty_container = tk.Frame(prod_frame, bg="white")
            qty_container.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            if product_data['has_pack']:
                tk.Label(qty_container, text="Packs:", font=("Arial", 9), bg="white").pack(side="left")
                pack_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
                pack_entry.pack(side="left", padx=2)
                pack_entry.insert(0, "0")
                product_data['pack_qty'] = pack_entry
                pack_entry.bind("<KeyRelease>", lambda e: self.update_transfer_return_total())
            
            tk.Label(qty_container, text="Pieces:", font=("Arial", 9), bg="white").pack(side="left", padx=(10 if product_data['has_pack'] else 0, 2))
            piece_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            product_data['piece_qty'] = piece_entry
            piece_entry.bind("<KeyRelease>", lambda e: self.update_transfer_return_total())
            
            self.transfer_return_vars.append(product_data)
        
        self.update_transfer_return_total()
    def update_transfer_return_total(self):
        """Calculate total refund for transfer return - Packs + Pieces"""
        total = 0
        for item in self.transfer_return_vars:
            if not item['var'].get():
                continue
            
            if item.get('has_pack', False):
                try:
                    packs = int(item.get('pack_qty').get() or 0)
                    if packs > 0:
                        total += packs * item.get('pack_price', 0)
                except:
                    pass
            
            try:
                pieces = int(item.get('piece_qty').get() or 0)
                if pieces > 0:
                    total += pieces * item.get('piece_price', 0)
            except:
                pass
        
        self.transfer_return_total_label.config(text=f"Rs. {total:,.2f}")
        return total
    def process_multi_transfer_return(self):
        """Process multiple product transfer return"""
        if not hasattr(self, 'current_transfer_id'):
            messagebox.showwarning("Error", "Please select a transfer first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.transfer_return_vars:
            if item['var'].get():
                try:
                    qty = int(item['qty_entry'].get())
                    if qty > 0:
                        if qty > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} units of {item['name']}!")
                            return
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': qty,
                            'price': item['price'],
                            'total': qty * item['price']
                        })
                        total_refund += qty * item['price']
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select at least one product to return!")
            return
        
        reason = "Transfer return from city"  # Default reason
        
        transfer = self.fetch_one("SELECT transfer_no, destination_city, recipient_name FROM stock_transfers WHERE id = ?", (self.current_transfer_id,))
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        confirm_msg = f"Transfer: {transfer[0]}\nCity: {transfer[1]}\n\nReturn Items:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} x Rs.{item['price']:.0f} = Rs.{item['total']:.0f}\n"
        confirm_msg += f"\nTotal Refund: Rs. {total_refund:,.2f}\nReason: {reason}\n\nProceed?"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
                        # Get last return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'TRANSFER' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-TRF-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("TRANSFER", return_no, self.current_transfer_id, item['product_id'], item['quantity'], item['total'], reason))
                
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", 
                              (item['quantity'], item['product_id']))
            
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("TRANSFER_RETURN", return_no, f"Return from {transfer[1]}: {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
                        # Print Return Slip
            self.print_return_slip(return_no, "TRANSFER", transfer[0], return_items, total_refund, reason)
            messagebox.showinfo("Success", f"Transfer return processed!\nReturn No: {return_no}\nItems: {len(return_items)}\nRefund: Rs.{total_refund:,.2f}")
            
            self.load_transfers_for_return()
            self.selected_transfer_label.config(text="Selected Transfer: None")
            self.transfer_return_total_label.config(text="Rs. 0.00")
            
            for widget in self.transfer_return_products_frame.winfo_children():
                widget.destroy()
            self.transfer_return_vars = []
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")     
    def update_transfer_return_price(self, event=None):
        """Auto-fill refund amount when product selected"""
        if not hasattr(self, 'current_transfer_products') or not self.current_transfer_products:
            return
        
        if self.transfer_return_product.get():
            try:
                product_id = int(self.transfer_return_product.get().split(" - ")[0])
                for prod in self.current_transfer_products:
                    if prod[0] == product_id:
                        self.transfer_available_qty_label.config(text=str(prod[2]))
                        self.transfer_return_refund.delete(0, tk.END)
                        self.transfer_return_refund.insert(0, str(prod[3]))
                        self.current_transfer_return_product_id = product_id
                        self.current_transfer_return_product_name = prod[1]
                        self.current_transfer_return_max_qty = prod[2]
                        break
            except:
                pass
    def process_transfer_return(self):
        """Process transfer return - Stock barhaye, Refund/Adjustment"""
        if not hasattr(self, 'current_transfer_id'):
            messagebox.showwarning("Error", "Please select a transfer first!")
            return
        
        if not self.transfer_return_product.get():
            messagebox.showwarning("Error", "Please select a product!")
            return
        
        try:
            quantity = int(self.transfer_return_qty.get())
            if quantity <= 0:
                messagebox.showwarning("Error", "Quantity must be greater than 0!")
                return
            if quantity > self.current_transfer_return_max_qty:
                messagebox.showwarning("Error", f"Maximum return quantity is {self.current_transfer_return_max_qty}!")
                return
        except:
            messagebox.showwarning("Error", "Invalid quantity!")
            return
        
        try:
            refund_amount = float(self.transfer_return_refund.get())
            if refund_amount <= 0:
                messagebox.showwarning("Error", "Refund amount must be greater than 0!")
                return
        except:
            messagebox.showwarning("Error", "Invalid refund amount!")
            return
        
        reason = "Transfer return from city"  # Default reason
        
        confirm = messagebox.askyesno(
            "Confirm Return",
            f"Transfer: {self.current_transfer_id}\n"
            f"Product: {self.current_transfer_return_product_name}\n"
            f"Quantity: {quantity}\n"
            f"Refund: Rs. {refund_amount:,.2f}\n"
            f"Reason: {reason}\n\nProceed?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            return_no = f"RET-TRF-{datetime.now().year}{datetime.now().strftime('%d%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("TRANSFER", return_no, self.current_transfer_id, self.current_transfer_return_product_id, quantity, refund_amount, reason))
            
            # INCREASE stock (product wapas aya)
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", (quantity, self.current_transfer_return_product_id))
            
            # Add to ledger (Credit adjustment)
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                VALUES (?, ?, ?, ?, ?)
            """, ("TRANSFER_RETURN", return_no, f"Return from city: {self.current_transfer_return_product_name} x{quantity}", 0, refund_amount))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Transfer return processed!\nReturn No: {return_no}")
            self.update_status(f"✅ Transfer return: {quantity} x {self.current_transfer_return_product_name}")
            
            self.transfer_return_qty.delete(0, tk.END)
            self.load_transfers_for_return()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def create_payment_receive_tab(self, parent):
        """Receive Payment for Pending/Partial Transfers - FULLY WORKING"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="💰 Receive Payment (Pending/Partial Transfers)", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#f6c23e").pack(pady=10)
        
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        right_frame = tk.Frame(main_container, bg="#f5f5f5", width=400)
        right_frame.pack(side="right", fill="y", padx=5)
        right_frame.pack_propagate(False)
        
        # Left side - Pending/Partial Transfers
        columns = ("ID", "Transfer No", "Date", "City", "Total", "Paid", "Balance", "Status")
        self.payment_transfer_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        self.payment_transfer_tree.heading("ID", text="ID")
        self.payment_transfer_tree.heading("Transfer No", text="Transfer No")
        self.payment_transfer_tree.heading("Date", text="Date")
        self.payment_transfer_tree.heading("City", text="City")
        self.payment_transfer_tree.heading("Total", text="Total (Rs.)")
        self.payment_transfer_tree.heading("Paid", text="Paid (Rs.)")
        self.payment_transfer_tree.heading("Balance", text="Balance (Rs.)")
        self.payment_transfer_tree.heading("Status", text="Status")
        
        self.payment_transfer_tree.column("ID", width=50)
        self.payment_transfer_tree.column("Transfer No", width=120)
        self.payment_transfer_tree.column("Date", width=100)
        self.payment_transfer_tree.column("City", width=100)
        self.payment_transfer_tree.column("Total", width=100)
        self.payment_transfer_tree.column("Paid", width=100)
        self.payment_transfer_tree.column("Balance", width=100)
        self.payment_transfer_tree.column("Status", width=80)
        
        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.payment_transfer_tree.yview)
        self.payment_transfer_tree.configure(yscrollcommand=vsb.set)
        self.payment_transfer_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.payment_transfer_tree.bind("<<TreeviewSelect>>", self.on_payment_select)
        
        # Right side form
        form_frame = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(form_frame, text="Payment Details", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        self.selected_payment_label = tk.Label(form_frame, text="Selected Transfer: None", font=("Arial", 10), bg="white", fg="#f6c23e")
        self.selected_payment_label.pack(pady=5)
        
        tk.Label(form_frame, text="Balance Due (Rs.):", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=5)
        self.balance_due_label = tk.Label(form_frame, text="0", font=("Arial", 12, "bold"), bg="white", fg="#e94560")
        self.balance_due_label.pack(anchor="w", padx=20, pady=5)
        
        tk.Label(form_frame, text="Amount to Receive (Rs.):", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=5)
        self.payment_amount = tk.Entry(form_frame, font=("Arial", 11), width=38)
        self.payment_amount.pack(padx=20, pady=5)
        
        tk.Label(form_frame, text="Payment Method:", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=5)
        self.payment_method_combo = ttk.Combobox(form_frame, font=("Arial", 11), width=35, state="readonly")
        self.payment_method_combo['values'] = ['Cash', 'Bank Transfer', 'Cheque', 'Online']
        self.payment_method_combo.pack(padx=20, pady=5)
        self.payment_method_combo.current(0)
        
        tk.Label(form_frame, text="Reference/Cheque No:", font=("Arial", 11), bg="white").pack(anchor="w", padx=20, pady=5)
        self.payment_ref_entry = tk.Entry(form_frame, font=("Arial", 11), width=38)
        self.payment_ref_entry.pack(padx=20, pady=5)
        
        tk.Button(form_frame, text="✅ RECEIVE PAYMENT", command=self.process_payment, 
                  bg="#f6c23e", fg="white", font=("Arial", 12, "bold"), 
                  padx=20, pady=10, relief="flat", cursor="hand2").pack(pady=20)
        
        self.load_pending_payments()
    
    def load_pending_payments(self):
        """Load transfers with pending or partial payment (including Shop Transfers)"""
        for item in self.payment_transfer_tree.get_children():
            self.payment_transfer_tree.delete(item)
        
        # Load City Transfers
        city_transfers = self.fetch_all("""
            SELECT id, transfer_no, transfer_date, destination_city, total_amount, amount_paid, balance_due, payment_status, 'CITY' as type
            FROM stock_transfers
            WHERE payment_status IN ('Pending', 'Partial')
            ORDER BY transfer_date DESC
        """)
        
        # Load Shop Transfers (Front Shop) - SAFE
        shop_transfers = []
        try:
            shop_transfers = self.fetch_all("""
                SELECT id, transfer_no, transfer_date, shop_name, total_amount, amount_paid, balance_due, payment_status, 'SHOP' as type
                FROM shop_transfers
                WHERE payment_status IN ('Pending', 'Partial')
                ORDER BY transfer_date DESC
            """)
        except:
            # Table doesn't exist yet
            pass
        
        # Combine both
        all_transfers = list(city_transfers) + list(shop_transfers)
        
        for transfer in all_transfers:
            transfer_type = transfer[8] if len(transfer) > 8 else 'CITY'
            if transfer_type == 'CITY':
                name_display = transfer[3] if len(transfer) > 3 else ""
            else:
                name_display = transfer[3] if len(transfer) > 3 else "Front Shop"
            
            self.payment_transfer_tree.insert("", "end", values=(
                transfer[0],
                transfer[1],
                transfer[2][:10] if transfer[2] else "-",
                name_display,
                f"Rs. {transfer[4]:,.2f}",
                f"Rs. {transfer[5]:,.2f}",
                f"Rs. {transfer[6]:,.2f}",
                transfer[7] if len(transfer) > 7 else "Pending",
                transfer_type
            ))
        
        self.update_status(f"Loaded {len(all_transfers)} pending/partial transfers (City + Shop)")
    
    def on_payment_select(self, event):
        """When transfer selected, show balance due (Handles both City and Shop)"""
        selected = self.payment_transfer_tree.selection()
        if not selected:
            return
        
        item = self.payment_transfer_tree.item(selected[0])
        self.current_payment_transfer_id = item['values'][0]
        self.current_payment_transfer_type = item['values'][8]  # 'CITY' or 'SHOP'
        transfer_no = item['values'][1]
        balance_str = item['values'][6].replace('Rs. ', '').replace(',', '')
        balance = float(balance_str)
        
        self.selected_payment_label.config(text=f"Selected Transfer: {transfer_no} ({self.current_payment_transfer_type})")
        self.balance_due_label.config(text=f"Rs. {balance:,.2f}")
        self.payment_amount.delete(0, tk.END)
        self.payment_amount.insert(0, str(balance))
    
    def process_payment(self):
        """Process payment for pending/partial transfer (City or Shop)"""
        if not hasattr(self, 'current_payment_transfer_id'):
            messagebox.showwarning("Error", "Please select a transfer first!")
            return
        
        try:
            amount = float(self.payment_amount.get())
            if amount <= 0:
                messagebox.showwarning("Error", "Amount must be greater than 0!")
                return
        except:
            messagebox.showwarning("Error", "Invalid amount!")
            return
        
        payment_method = self.payment_method_combo.get()
        payment_ref = self.payment_ref_entry.get().strip()
        
        # Get current transfer details based on type
        if self.current_payment_transfer_type == 'CITY':
            transfer = self.fetch_one("""
                SELECT transfer_no, total_amount, amount_paid, balance_due, payment_status, destination_city
                FROM stock_transfers WHERE id = ?
            """, (self.current_payment_transfer_id,))
            table_name = "stock_transfers"
        else:  # SHOP
            transfer = self.fetch_one("""
                SELECT transfer_no, total_amount, amount_paid, balance_due, payment_status, shop_name
                FROM shop_transfers WHERE id = ?
            """, (self.current_payment_transfer_id,))
            table_name = "shop_transfers"
        
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        current_paid = transfer[2] or 0
        current_balance = transfer[3] or 0
        location_name = transfer[5]  # city or shop_name
        
        if amount > current_balance:
            messagebox.showwarning("Error", f"Amount cannot exceed balance due (Rs. {current_balance:,.2f})!")
            return
        
        new_paid = current_paid + amount
        new_balance = current_balance - amount
        new_status = "Paid" if new_balance <= 0 else "Partial"
        
        confirm = messagebox.askyesno(
            "Confirm Payment",
            f"Transfer: {transfer[0]}\n"
            f"Location: {location_name}\n"
            f"Type: {self.current_payment_transfer_type}\n"
            f"Amount: Rs. {amount:,.2f}\n"
            f"Method: {payment_method}\n"
            f"New Balance: Rs. {new_balance:,.2f}\n\n"
            f"Proceed?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Update transfer
            cursor.execute(f"""
                UPDATE {table_name} 
                SET amount_paid = ?, balance_due = ?, payment_status = ?
                WHERE id = ?
            """, (new_paid, new_balance, new_status, self.current_payment_transfer_id))
            
            # Add to ledger
            payment_no = f"PAY-{datetime.now().year}{datetime.now().strftime('%d%H%M%S')}"
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("PAYMENT", payment_no, f"Payment received for {transfer[0]} - {location_name} - {payment_method} {payment_ref}", amount))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Payment of Rs. {amount:,.2f} received!\nNew Balance: Rs. {new_balance:,.2f}")
            self.update_status(f"✅ Payment received: Rs. {amount:,.2f}")
            self.force_refresh_dashboard()
            # Refresh
            self.load_pending_payments()
            self.payment_amount.delete(0, tk.END)
            self.payment_ref_entry.delete(0, tk.END)
            self.selected_payment_label.config(text="Selected Transfer: None")
            self.balance_due_label.config(text="0")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payment: {str(e)}")
    
    def create_return_history_tab(self, parent):
        """Return History - All returns in one place"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="📜 Complete Return History", font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Filter frame
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=10)
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=10, pady=10)
        
        tk.Label(filter_inner, text="Search Return No:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.history_search_var = tk.StringVar()
        self.history_search_var.trace('w', lambda *args: self.load_return_history())
        tk.Entry(filter_inner, textvariable=self.history_search_var, font=("Arial", 10), width=20).pack(side="left", padx=5)
        
        tk.Button(filter_inner, text="Clear", command=self.clear_return_search, bg="#e74a3b", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(side="left", padx=10)
        
        # Treeview
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Return No", "Date", "Type", "Product", "Quantity", "Refund", "Reason")
        self.return_history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.return_history_tree.heading("Return No", text="Return No")
        self.return_history_tree.heading("Date", text="Date")
        self.return_history_tree.heading("Type", text="Return Type")
        self.return_history_tree.heading("Product", text="Product")
        self.return_history_tree.heading("Quantity", text="Quantity")
        self.return_history_tree.heading("Refund", text="Refund (Rs.)")
        self.return_history_tree.heading("Reason", text="Reason")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.return_history_tree.yview)
        self.return_history_tree.configure(yscrollcommand=vsb.set)
        self.return_history_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.load_return_history()
    
    def load_shop_transfers_for_return(self):
        """Load shop transfers for return selection - SAFE with search"""
        for item in self.shop_return_tree.get_children():
            self.shop_return_tree.delete(item)
        
        search_term = self.shop_return_search.get().strip() if hasattr(self, 'shop_return_search') else ""
        
        try:
            if search_term:
                query = """
                    SELECT id, transfer_no, transfer_date, recipient_name, total_amount, payment_status
                    FROM shop_transfers
                    WHERE transfer_no LIKE ? OR recipient_name LIKE ?
                    ORDER BY id DESC
                """
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = """
                    SELECT id, transfer_no, transfer_date, recipient_name, total_amount, payment_status
                    FROM shop_transfers
                    ORDER BY id DESC
                """
                params = ()
            
            transfers = self.fetch_all(query, params)
            
            for transfer in transfers:
                self.shop_return_tree.insert("", "end", values=(
                    transfer[0], transfer[1], transfer[2][:10] if transfer[2] else "-",
                    transfer[3] or "-", f"Rs. {transfer[4]:,.2f}", transfer[5]
                ))
        except:
            # Table doesn't exist yet
            pass
    
    def load_shop_transfers_for_return(self):
        """Load shop transfers for return selection - SAFE"""
        for item in self.shop_return_tree.get_children():
            self.shop_return_tree.delete(item)
        
        try:
            transfers = self.fetch_all("""
                SELECT id, transfer_no, transfer_date, recipient_name, total_amount, payment_status
                FROM shop_transfers
                ORDER BY id DESC
            """)
            
            for transfer in transfers:
                self.shop_return_tree.insert("", "end", values=(
                    transfer[0], transfer[1], transfer[2][:10] if transfer[2] else "-",
                    transfer[3] or "-", f"Rs. {transfer[4]:,.2f}", transfer[5]
                ))
        except:
            # Table doesn't exist yet
            pass
    
    def on_shop_return_select(self, event):
        """When shop transfer is selected, load its products with Pack/Piece options"""
        selected = self.shop_return_tree.selection()
        if not selected:
            return
        
        item = self.shop_return_tree.item(selected[0])
        transfer_id = item['values'][0]
        transfer_no = item['values'][1]
        recipient = item['values'][3]
        
        self.selected_shop_transfer_label.config(text=f"Selected Transfer: {transfer_no} - {recipient}")
        self.current_shop_transfer_id = transfer_id
        
        # Clear existing
        for widget in self.shop_return_products_frame.winfo_children():
            widget.destroy()
        self.shop_return_vars = []
        
        # Load products from this shop transfer
        products = self.fetch_all("""
            SELECT sti.product_id, p.name, sti.price, sti.quantity, p.cost_price,
                   IFNULL(p.unit_type, 'Piece'), IFNULL(p.pieces_per_pack, 1), IFNULL(p.pack_price, 0)
            FROM shop_transfer_items sti
            JOIN products p ON sti.product_id = p.id
            WHERE sti.transfer_id = ?
        """, (transfer_id,))
        
        for product in products:
            product_id = product[0]
            product_name = product[1]
            transfer_price = product[2]
            transferred_qty = product[3]
            cost_price = product[4]
            unit_type = product[5] if len(product) > 5 else "Piece"
            pieces_per_pack = product[6] if len(product) > 6 and product[6] > 0 else 1
            pack_price = product[7] if len(product) > 7 and product[7] > 0 else transfer_price * pieces_per_pack
            
            if unit_type == "Pack" and pieces_per_pack > 0:
                actual_piece_price = pack_price / pieces_per_pack
            else:
                actual_piece_price = transfer_price
            
            # Main frame
            prod_frame = tk.Frame(self.shop_return_products_frame, bg="white", relief="ridge", bd=1)
            prod_frame.pack(fill="x", padx=5, pady=5)
            prod_frame.configure(width=700)
            prod_frame.pack_propagate(False)
            
            var = tk.BooleanVar()
            cb = tk.Checkbutton(prod_frame, text=product_name, variable=var, 
                                bg="white", font=("Arial", 10, "bold"),
                                command=self.update_shop_return_total)
            cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            info_frame = tk.Frame(prod_frame, bg="white")
            info_frame.grid(row=0, column=1, padx=10, pady=5)
            tk.Label(info_frame, text=f"Transferred: {transferred_qty} pieces", 
                    font=("Arial", 9), bg="white", fg="#666").pack()
            
            if unit_type == "Pack" and pieces_per_pack > 1:
                tk.Label(info_frame, text=f"Pack: {pieces_per_pack} pcs @ Rs.{pack_price:.2f} | Piece: Rs.{actual_piece_price:.2f}", 
                        font=("Arial", 8), bg="white", fg="#e94560").pack()
            
            product_data = {
                'var': var,
                'product_id': product_id,
                'name': product_name,
                'piece_price': actual_piece_price,
                'pack_price': pack_price,
                'max_qty': transferred_qty,
                'pieces_per_pack': pieces_per_pack,
                'has_pack': (unit_type == "Pack" and pieces_per_pack > 1)
            }
            
            qty_container = tk.Frame(prod_frame, bg="white")
            qty_container.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            if product_data['has_pack']:
                tk.Label(qty_container, text="Packs:", font=("Arial", 9), bg="white").pack(side="left")
                pack_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
                pack_entry.pack(side="left", padx=2)
                pack_entry.insert(0, "0")
                product_data['pack_qty'] = pack_entry
                pack_entry.bind("<KeyRelease>", lambda e: self.update_shop_return_total())
            
            tk.Label(qty_container, text="Pieces:", font=("Arial", 9), bg="white").pack(side="left", padx=(10 if product_data['has_pack'] else 0, 2))
            piece_entry = tk.Entry(qty_container, width=5, font=("Arial", 10), justify="center")
            piece_entry.pack(side="left", padx=2)
            piece_entry.insert(0, "0")
            product_data['piece_qty'] = piece_entry
            piece_entry.bind("<KeyRelease>", lambda e: self.update_shop_return_total())
            
            self.shop_return_vars.append(product_data)
        
        self.update_shop_return_total()
    
    def update_shop_return_total(self):
        """Calculate total refund for shop return - Packs + Pieces"""
        total = 0
        for item in self.shop_return_vars:
            if not item['var'].get():
                continue
            
            if item.get('has_pack', False):
                try:
                    packs = int(item.get('pack_qty').get() or 0)
                    if packs > 0:
                        total += packs * item.get('pack_price', 0)
                except:
                    pass
            
            try:
                pieces = int(item.get('piece_qty').get() or 0)
                if pieces > 0:
                    total += pieces * item.get('piece_price', 0)
            except:
                pass
        
        self.shop_return_total_label.config(text=f"Rs. {total:,.2f}")
        return total
    
    def process_shop_return(self):
        """Process shop return - Stock wapas main warehouse mein, aur payment auto-adjust"""
        if not hasattr(self, 'current_shop_transfer_id'):
            messagebox.showwarning("Error", "Please select a shop transfer first!")
            return
        
        return_items = []
        total_refund = 0
        
        for item in self.shop_return_vars:
            if item['var'].get():
                try:
                    qty = int(item['qty_entry'].get())
                    if qty > 0:
                        if qty > item['max_qty']:
                            messagebox.showwarning("Invalid Quantity", 
                                f"Cannot return more than {item['max_qty']} units of {item['name']}!")
                            return
                        return_items.append({
                            'product_id': item['product_id'],
                            'name': item['name'],
                            'quantity': qty,
                            'price': item['price'],
                            'total': qty * item['price']
                        })
                        total_refund += qty * item['price']
                except:
                    pass
        
        if not return_items:
            messagebox.showwarning("Error", "Please select at least one product to return!")
            return
        
        reason = self.shop_return_reason.get().strip() or "Return from Front Shop"
        
        # Get transfer details
        transfer = self.fetch_one("SELECT transfer_no, recipient_name, total_amount, amount_paid, balance_due, payment_status FROM shop_transfers WHERE id = ?", (self.current_shop_transfer_id,))
        if not transfer:
            messagebox.showerror("Error", "Transfer not found!")
            return
        
        transfer_no = transfer[0]
        recipient = transfer[1]
        original_total = transfer[2]
        current_paid = transfer[3] or 0
        current_balance = transfer[4] or 0
        
        confirm_msg = f"Shop Transfer: {transfer_no}\nRecipient: {recipient}\n\nReturn Items:\n"
        for item in return_items:
            confirm_msg += f"  - {item['name']}: {item['quantity']} x Rs.{item['price']:.0f} = Rs.{item['total']:.0f}\n"
        confirm_msg += f"\nTotal Return Value: Rs. {total_refund:,.2f}\n\n"
        
        # Check if return affects payment
        if current_balance > 0:
            confirm_msg += f"⚠️ Note: This transfer has balance due of Rs. {current_balance:,.2f}\n"
            confirm_msg += f"The return value will be adjusted automatically.\n"
        
        confirm_msg += f"\nProceed with return?"
        
        if not messagebox.askyesno("Confirm Return", confirm_msg):
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get last return number
            last_return = self.fetch_one("SELECT return_no FROM returns WHERE return_type = 'SHOP_RETURN' ORDER BY id DESC LIMIT 1")
            if last_return and last_return[0]:
                parts = last_return[0].split('-')
                if len(parts) >= 3:
                    try:
                        last_num = int(parts[2])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            return_no = f"RET-SHP-{new_num:03d}"
            
            for item in return_items:
                cursor.execute("""
                    INSERT INTO returns (return_no, return_type, reference_id, product_id, quantity, refund_amount, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("SHOP_RETURN", return_no, self.current_shop_transfer_id, item['product_id'], item['quantity'], item['total'], reason))
                
                # INCREASE stock (product wapas main warehouse mein aya)
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?", 
                              (item['quantity'], item['product_id']))
            
            # ===== UPDATE PAYMENT STATUS BASED ON RETURN =====
            # Calculate new total after return
            new_total = original_total - total_refund
            
            if new_total <= 0:
                # Sab kuch return ho gaya
                cursor.execute("""
                    UPDATE shop_transfers 
                    SET total_amount = 0, amount_paid = 0, balance_due = 0, payment_status = 'Returned'
                    WHERE id = ?
                """, (self.current_shop_transfer_id,))
            else:
                # Kuch return hua hai, payment adjust karo
                # Agar paid amount return value se zyada hai toh refund dena hoga
                if current_paid > new_total:
                    # Overpayment hai - refund dena hoga
                    refund_needed = current_paid - new_total
                    new_paid = new_total
                    new_balance = 0
                    new_status = "Paid"
                    
                    confirm_refund = messagebox.askyesno(
                        "⚠️ Overpayment Detected",
                        f"Customer has paid Rs. {current_paid:,.2f}\n"
                        f"After return, new total is Rs. {new_total:,.2f}\n\n"
                        f"Need to refund Rs. {refund_needed:,.2f} to customer!\n\n"
                        f"Create refund entry?"
                    )
                    
                    if confirm_refund:
                        cursor.execute("""
                            INSERT INTO ledger (transaction_type, reference_no, description, debit)
                            VALUES (?, ?, ?, ?)
                        """, ("REFUND", return_no, f"Refund to customer for {transfer_no} - Return", refund_needed))
                    
                else:
                    # Normal adjustment - payment status unchanged
                    new_paid = current_paid
                    new_balance = new_total - current_paid
                    if new_balance <= 0:
                        new_status = "Paid"
                    elif new_paid > 0:
                        new_status = "Partial"
                    else:
                        new_status = "Pending"
                
                cursor.execute("""
                    UPDATE shop_transfers 
                    SET total_amount = ?, amount_paid = ?, balance_due = ?, payment_status = ?
                    WHERE id = ?
                """, (new_total, new_paid, new_balance, new_status, self.current_shop_transfer_id))
            
            # Add to ledger for return
            cursor.execute("""
                INSERT INTO ledger (transaction_type, reference_no, description, credit)
                VALUES (?, ?, ?, ?)
            """, ("SHOP_RETURN", return_no, f"Return from Front Shop: {transfer_no} - {len(return_items)} items", total_refund))
            
            conn.commit()
            conn.close()
            
            # Print Return Slip
            self.print_shop_return_slip(return_no, transfer_no, recipient, return_items, total_refund, reason)
            
            messagebox.showinfo("Success", 
                f"Shop return processed!\nReturn No: {return_no}\n"
                f"Items returned: {len(return_items)}\n"
                f"Total Refund: Rs. {total_refund:,.2f}\n"
                f"New Transfer Total: Rs. {new_total:,.2f}")
            
            # Refresh
            self.load_shop_transfers_for_return()
            self.selected_shop_transfer_label.config(text="Selected Transfer: None")
            self.shop_return_total_label.config(text="Rs. 0.00")
            self.shop_return_reason.delete(0, tk.END)
            self.shop_return_reason.insert(0, "Return from Front Shop")
            
            for widget in self.shop_return_products_frame.winfo_children():
                widget.destroy()
            self.shop_return_vars = []
            
            # Also refresh pending payments if that tab is open
            self.load_pending_payments()
            
            self.update_status(f"✅ Shop return processed: {len(return_items)} items, Refund: Rs.{total_refund:,.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def print_shop_return_slip(self, return_no, transfer_no, recipient, items, total_refund, reason):
        """Print Shop Return Slip - MAXIMUM COMPACT"""
        now = datetime.now()
        
        lines = []
        lines.append("=" * 32)
        lines.append("FAIZAN PAPER MART")
        lines.append("Rail Bazar Sargodha")
        lines.append("=" * 32)
        lines.append(f"RET:{return_no} {now.strftime('%d-%m-%y %H:%M')}")
        lines.append(f"SHP:{transfer_no} From:{self.shorten_text(recipient, 22)}")
        lines.append("-" * 32)
        lines.append(f"{'#':<2}{'ITEM':<16}{'QTY':>4}{'AMT':>6}")
        lines.append("-" * 32)
        
        serial = 1
        for item in items:
            name = self.shorten_text(item['name'], 14)
            qty = item['quantity']
            amount = item['total']
            lines.append(f"{serial:<2}{name:<16}{qty:>4}{amount:>6.0f}")
            serial += 1
        
        lines.append("-" * 32)
        lines.append(f"{'REFUND':>25}{total_refund:>7.0f}")
        lines.append(f"Reason:{self.shorten_text(reason, 24)}")
        lines.append("=" * 32)
        lines.append("THANK YOU")
        lines.append("=" * 32)
        
        slip_text = "\n".join(lines)
        
        # Save to returns folder
        returns_dir = "returns"
        if not os.path.exists(returns_dir):
            os.makedirs(returns_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{returns_dir}/shop_return_{return_no}_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(slip_text)
        
        self.direct_print(slip_text)

    def load_return_history(self):
        """Load return history with search by Return No"""
        for item in self.return_history_tree.get_children():
            self.return_history_tree.delete(item)
        
        search_term = self.history_search_var.get().strip() if hasattr(self, 'history_search_var') else ""
        
        if search_term:
            query = """
                SELECT r.return_no, r.return_date, r.return_type, p.name, r.quantity, r.refund_amount, r.reason
                FROM returns r
                JOIN products p ON r.product_id = p.id
                WHERE r.return_no LIKE ?
                ORDER BY r.id DESC
            """
            params = (f'%{search_term}%',)
        else:
            query = """
                SELECT r.return_no, r.return_date, r.return_type, p.name, r.quantity, r.refund_amount, r.reason
                FROM returns r
                JOIN products p ON r.product_id = p.id
                ORDER BY r.id DESC
            """
            params = ()
        
        returns = self.fetch_all(query, params)
        
        for ret in returns:
            self.return_history_tree.insert("", "end", values=(
                ret[0],
                ret[1][:10] if ret[1] else "-",
                ret[2],
                ret[3],
                ret[4],
                f"Rs. {ret[5]:,.2f}",
                ret[6] or "-"
            ))
        
        if search_term:
            self.update_status(f"Found {len(returns)} returns matching '{search_term}'")
        else:
            self.update_status(f"Loaded {len(returns)} return records")
    def clear_return_search(self):
        """Clear search and reload all returns"""
        if hasattr(self, 'history_search_var'):
            self.history_search_var.set("")
        self.load_return_history()
    def select_backup_folder(self):
        """Select backup folder location"""
        folder = filedialog.askdirectory(title="Select Backup Folder")
        if folder:
            self.backup_location_var.set(folder)
            self.save_auto_backup_setting()
    
    def save_auto_backup_setting(self):
        """Save auto backup settings to file"""
        try:
            settings = {
                'schedule': self.auto_backup_var.get(),
                'location': self.backup_location_var.get()
            }
            with open('backup_settings.json', 'w') as f:
                import json
                json.dump(settings, f)
        except:
            pass
    
    def load_auto_backup_settings(self):
        """Load auto backup settings from file"""
        try:
            import json
            with open('backup_settings.json', 'r') as f:
                settings = json.load(f)
                self.auto_backup_var.set(settings.get('schedule', 'Daily'))
                self.backup_location_var.set(settings.get('location', 'backups'))
        except:
            pass
    
    def check_scheduled_backup(self):
        """Check if scheduled backup is needed"""
        self.load_auto_backup_settings()
        
        last_backup_file = "last_backup.txt"
        last_backup_date = None
        
        if os.path.exists(last_backup_file):
            with open(last_backup_file, 'r') as f:
                last_backup_date = f.read().strip()
        
        schedule = self.auto_backup_var.get()
        if schedule == "Never":
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if last_backup_date != today:
            should_backup = False
            
            if schedule == "Daily":
                should_backup = True
            elif schedule == "Weekly":
                # Backup on Mondays
                should_backup = datetime.now().weekday() == 0
            elif schedule == "Monthly":
                # Backup on 1st of month
                should_backup = datetime.now().day == 1
            
            if should_backup:
                result = messagebox.askyesno("Auto Backup", f"Time for scheduled {schedule} backup. Create backup now?")
                if result:
                    self.create_backup(auto=True)
                    with open(last_backup_file, 'w') as f:
                        f.write(today)
    
    def create_backup(self, auto=False):
        """Create database backup"""
        try:
            # Create backup directory
            backup_dir = self.backup_location_var.get()
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Generate filename
            if self.backup_with_date.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"stationery_backup_{timestamp}"
            else:
                backup_name = "stationery_backup"
            
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Copy database file
            import shutil
            db_file = self.db_path
            
            if os.path.exists(db_file):
                shutil.copy2(db_file, backup_path + ".db")
                
                # Create ZIP if selected
                if self.backup_compress.get():
                    import zipfile
                    with zipfile.ZipFile(backup_path + ".zip", 'w') as zipf:
                        zipf.write(backup_path + ".db", arcname=backup_name + ".db")
                    os.remove(backup_path + ".db")
                    final_path = backup_path + ".zip"
                else:
                    final_path = backup_path + ".db"
                
                # Record backup history
                self.record_backup_history(final_path)
                
                if not auto:
                    messagebox.showinfo("Backup Success", f"Backup created successfully!\n\nLocation: {final_path}")
                
                self.refresh_backup_list()
                self.update_status(f"✅ Backup created: {backup_name}")
            else:
                messagebox.showwarning("Backup Failed", "Database file not found!")
                
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {str(e)}")
    
    def record_backup_history(self, backup_path):
        """Record backup in history"""
        history_file = "backup_history.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
        size_kb = size / 1024
        
        history_entry = f"{timestamp} | {backup_path} | {size_kb:.1f} KB\n"
        
        with open(history_file, 'a') as f:
            f.write(history_entry)
        
        self.load_backup_history()
    
    def load_backup_history(self):
        """Load backup history display"""
        self.backup_history_text.delete("1.0", tk.END)
        history_file = "backup_history.txt"
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = f.readlines()
                # Show last 10 backups
                for line in history[-10:]:
                    self.backup_history_text.insert(tk.END, line)
        else:
            self.backup_history_text.insert(tk.END, "No backup history found. Create your first backup!")
    
    def refresh_backup_list(self):
        """Refresh the list of backup files"""
        self.backup_files_listbox.delete(0, tk.END)
        
        backup_dir = self.backup_location_var.get()
        if not os.path.exists(backup_dir):
            return
        
        # Find all backup files
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith("stationery_backup") and (file.endswith(".db") or file.endswith(".zip")):
                file_path = os.path.join(backup_dir, file)
                mod_time = os.path.getmtime(file_path)
                backup_files.append((mod_time, file, file_path))
        
        # Sort by date (newest first)
        backup_files.sort(reverse=True)
        
        for mod_time, file, file_path in backup_files:
            date_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            size = os.path.getsize(file_path) / 1024
            self.backup_files_listbox.insert(tk.END, f"{date_str} - {file} ({size:.1f} KB)")
            # Store full path as a separate attribute
            if not hasattr(self, 'backup_file_paths'):
                self.backup_file_paths = {}
            self.backup_file_paths[f"{date_str} - {file} ({size:.1f} KB)"] = file_path
    
    def restore_backup(self):
        """Restore database from selected backup"""
        selection = self.backup_files_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup file to restore!")
            return
        
        selected_text = self.backup_files_listbox.get(selection[0])
        backup_path = self.backup_file_paths.get(selected_text)
        
        if not backup_path or not os.path.exists(backup_path):
            messagebox.showerror("Error", "Backup file not found!")
            return
        
        # Confirm restore
        confirm = messagebox.askyesno(
            "⚠️ Confirm Restore ⚠️",
            f"WARNING: This will overwrite ALL current data!\n\nBackup: {os.path.basename(backup_path)}\n\nThis action cannot be undone!\n\nAre you absolutely sure?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Second confirmation for safety
        confirm2 = messagebox.askyesno(
            "Final Confirmation",
            "Type 'RESTORE' in the box below to confirm.",
            icon='warning'
        )
        
        if not confirm2:
            return
        
        try:
            import shutil
            
            # Close current database connection
            # (will reconnect automatically)
            
            # Extract if zip file
            if backup_path.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # Extract to temp location
                    zipf.extractall(tempfile.gettempdir())
                    extracted_db = os.path.join(tempfile.gettempdir(), os.path.basename(backup_path).replace('.zip', '.db'))
                    shutil.copy2(extracted_db, self.db_path)
                    os.remove(extracted_db)
            else:
                shutil.copy2(backup_path, self.db_path)
            
            messagebox.showinfo("Restore Complete", "Database restored successfully!\n\nThe application will now restart to apply changes.")
            
            # Restart the application
            self.root.destroy()
            os.system(f"python {__file__}")
            
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore backup: {str(e)}")
    
    def show_backup_restore(self):
        """Show Backup & Restore interface - Main entry point"""
        self.clear_main_content()
        
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(main_container, bg="#f5f5f5")
        title_frame.pack(fill="x")
        
        tk.Label(title_frame, text="💾 Backup & Restore System", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        # Add to sidebar navigation
        self.backup_restore_btn = tk.Button(
            title_frame,
            text="🏠 Back to Dashboard",
            command=self.show_dashboard,
            bg="#36b9cc",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        self.backup_restore_btn.pack(side="right")
        
        tk.Label(main_container, text="Protect your business data with automatic and manual backups", font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(pady=(0, 20))
        
        # Create two columns
        columns_frame = tk.Frame(main_container, bg="#f5f5f5")
        columns_frame.pack(fill="both", expand=True)
        
        left_frame = tk.Frame(columns_frame, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        right_frame = tk.Frame(columns_frame, bg="#f5f5f5")
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        # ===== LEFT SIDE - BACKUP SECTION =====
        backup_frame = tk.LabelFrame(left_frame, text="📤 Create Backup", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1cc88a")
        backup_frame.pack(fill="both", expand=True, pady=10)
        
        backup_inner = tk.Frame(backup_frame, bg="#f5f5f5")
        backup_inner.pack(padx=20, pady=20)
        
        tk.Label(backup_inner, text="Create a backup of your entire database:", font=("Arial", 11), bg="#f5f5f5").pack(pady=5)
        tk.Label(backup_inner, text="Includes all products, sales, purchases, expenses, and ledger data", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack()
        
        # Backup options
        options_frame = tk.Frame(backup_inner, bg="#f5f5f5")
        options_frame.pack(pady=15)
        
        self.backup_with_date = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Include date in filename", variable=self.backup_with_date, bg="#f5f5f5", font=("Arial", 10)).pack(anchor="w")
        
        self.backup_compress = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Create ZIP archive", variable=self.backup_compress, bg="#f5f5f5", font=("Arial", 10)).pack(anchor="w")
        
        btn_frame = tk.Frame(backup_inner, bg="#f5f5f5")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Create Manual Backup", command=self.create_backup, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10, relief="flat", cursor="hand2").pack(pady=5)
        
        # Auto Backup Settings
        auto_frame = tk.LabelFrame(backup_inner, text="⏰ Automatic Backup", font=("Arial", 11, "bold"), bg="#f5f5f5")
        auto_frame.pack(fill="x", pady=10)
        
        tk.Label(auto_frame, text="Schedule:", font=("Arial", 10), bg="#f5f5f5").pack(anchor="w", padx=10, pady=(10, 0))
        self.auto_backup_var = tk.StringVar(value="Daily")
        auto_combo = ttk.Combobox(auto_frame, textvariable=self.auto_backup_var, values=["Daily", "Weekly", "Monthly", "Never"], font=("Arial", 10), width=15, state="readonly")
        auto_combo.pack(padx=10, pady=5)
        auto_combo.bind('<<ComboboxSelected>>', lambda e: self.save_auto_backup_setting())
        
        tk.Label(auto_frame, text="Backup Location:", font=("Arial", 10), bg="#f5f5f5").pack(anchor="w", padx=10, pady=(10, 0))
        self.backup_location_var = tk.StringVar(value="backups")
        location_entry = tk.Entry(auto_frame, textvariable=self.backup_location_var, font=("Arial", 10), width=25)
        location_entry.pack(padx=10, pady=5)
        
        tk.Button(auto_frame, text="📁 Browse", command=self.select_backup_folder, bg="#36b9cc", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(pady=5)
        
        # ===== RIGHT SIDE - RESTORE SECTION =====
        restore_frame = tk.LabelFrame(right_frame, text="📥 Restore from Backup", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#e94560")
        restore_frame.pack(fill="both", expand=True, pady=10)
        
        restore_inner = tk.Frame(restore_frame, bg="#f5f5f5")
        restore_inner.pack(padx=20, pady=20)
        
        tk.Label(restore_inner, text="Select a backup file to restore:", font=("Arial", 11), bg="#f5f5f5").pack(pady=5)
        
        # Backup files list
        list_frame = tk.Frame(restore_inner, bg="white", relief="ridge", bd=1)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.backup_files_listbox = tk.Listbox(list_frame, font=("Arial", 10), height=8, bg="white")
        self.backup_files_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.backup_files_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.backup_files_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        restore_btn_frame = tk.Frame(restore_inner, bg="#f5f5f5")
        restore_btn_frame.pack(pady=10)
        
        tk.Button(restore_btn_frame, text="🔄 Refresh List", command=self.refresh_backup_list, bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        tk.Button(restore_btn_frame, text="⚠️ Restore Selected", command=self.restore_backup, bg="#e94560", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5, relief="flat").pack(side="left", padx=5)
        
        # Warning
        warning_frame = tk.Frame(restore_inner, bg="#fff3cd", relief="ridge", bd=1)
        warning_frame.pack(fill="x", pady=10)
        tk.Label(warning_frame, text="⚠️ WARNING: Restoring will overwrite current data!", font=("Arial", 9), bg="#fff3cd", fg="#856404").pack(padx=10, pady=5)
        
        # Backup History
        history_frame = tk.LabelFrame(main_container, text="📋 Backup History", font=("Arial", 12, "bold"), bg="#f5f5f5")
        history_frame.pack(fill="x", pady=10)
        
        self.backup_history_text = tk.Text(history_frame, height=5, font=("Courier", 9), bg="#f5f5f5", fg="#666")
        self.backup_history_text.pack(fill="x", padx=10, pady=10)
        
        # Load backup list and history
        self.refresh_backup_list()
        self.load_backup_history()
        
        # Check for scheduled backup on startup
        self.check_scheduled_backup()

        # ========== PHASE 11: INTER-CITY STOCK TRANSFER SYSTEM ==========
    
    def show_stock_transfer(self):
        """Show Stock Transfer interface for inter-city distribution"""
        self.clear_main_content()
        
        # ===== CREATE TABLES IF NOT EXISTS =====
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create stock_transfers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_no TEXT UNIQUE NOT NULL,
                    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    destination_city TEXT NOT NULL,
                    recipient_name TEXT,
                    transfer_type TEXT,
                    total_amount REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Pending',
                    amount_paid REAL DEFAULT 0,
                    balance_due REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create transfer_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            self.update_status("✅ Transfer tables ready")
        except Exception as e:
            self.update_status(f"⚠️ Table check: {str(e)}")
        
        # Main container
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text="🚚 Inter-City Stock Transfer", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: New Transfer
        new_transfer_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(new_transfer_tab, text="➕ New Transfer")
        self.create_new_transfer_tab(new_transfer_tab)
        
        # Tab 2: Transfer History
        history_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(history_tab, text="📜 Transfer History")
        self.create_transfer_history_tab(history_tab)
        
        # Tab 3: City Stock View
        city_stock_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(city_stock_tab, text="🏙️ City Stock View")
        self.create_city_stock_tab(city_stock_tab)
    
    def create_new_transfer_tab(self, parent):
        """Create New Stock Transfer interface with scrollable right panel"""
        # Main container with two columns
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Product Selection (fixed height, scrollable)
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right side - Transfer Form (with scrollbar)
        right_container = tk.Frame(main_container, bg="#f5f5f5", width=420, height=650)
        right_container.pack(side="right", fill="y", padx=(5, 0))
        right_container.pack_propagate(False)
        
        # Create canvas and scrollbar for right panel
        right_canvas = tk.Canvas(right_container, bg="#f5f5f5", highlightthickness=0)
        right_scrollbar = tk.Scrollbar(right_container, orient="vertical", command=right_canvas.yview)
        right_scrollable_frame = tk.Frame(right_canvas, bg="#f5f5f5")
        
        right_scrollable_frame.bind(
            "<Configure>",
            lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all"))
        )
        
        right_canvas.create_window((0, 0), window=right_scrollable_frame, anchor="nw", width=400)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        
        right_canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def on_mousewheel(event):
            right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        right_canvas.bind("<MouseWheel>", on_mousewheel)
        
        # ===== LEFT SIDE =====
        # Search Products
        search_frame = tk.Frame(left_frame, bg="white", relief="ridge", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Search Product:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.transfer_search_var = tk.StringVar()
        self.transfer_search_var.trace('w', lambda *args: self.load_transfer_products(self.transfer_search_var.get()))
        tk.Entry(search_frame, textvariable=self.transfer_search_var, font=("Arial", 11), width=30).pack(side="left", padx=10, pady=8)
        
        # Products List
        products_frame = tk.LabelFrame(left_frame, text="Available Stock (Main Warehouse)", font=("Arial", 12, "bold"), bg="#f5f5f5")
        products_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Product", "Brand", "Stock", "Price")
        self.transfer_products_tree = ttk.Treeview(products_frame, columns=columns, show="headings", height=12)
        
        self.transfer_products_tree.heading("ID", text="ID")
        self.transfer_products_tree.heading("Product", text="Product Name")
        self.transfer_products_tree.heading("Brand", text="Brand")
        self.transfer_products_tree.heading("Stock", text="Available Stock")
        self.transfer_products_tree.heading("Price", text="Price (Rs.)")
        
        self.transfer_products_tree.column("ID", width=50)
        self.transfer_products_tree.column("Product", width=200)
        self.transfer_products_tree.column("Brand", width=100)
        self.transfer_products_tree.column("Stock", width=100)
        self.transfer_products_tree.column("Price", width=100)
        
        vsb = ttk.Scrollbar(products_frame, orient="vertical", command=self.transfer_products_tree.yview)
        self.transfer_products_tree.configure(yscrollcommand=vsb.set)
        
        self.transfer_products_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Transfer Cart
        cart_frame = tk.LabelFrame(left_frame, text="Transfer Cart", font=("Arial", 12, "bold"), bg="#f5f5f5")
        cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        cart_columns = ("ID", "Product", "Quantity", "Price", "Total")
        self.transfer_cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=6)
        
        self.transfer_cart_tree.heading("ID", text="#")
        self.transfer_cart_tree.heading("Product", text="Product Name")
        self.transfer_cart_tree.heading("Quantity", text="Quantity")
        self.transfer_cart_tree.heading("Price", text="Price (Rs.)")
        self.transfer_cart_tree.heading("Total", text="Total (Rs.)")
        
        self.transfer_cart_tree.column("ID", width=40)
        self.transfer_cart_tree.column("Product", width=200)
        self.transfer_cart_tree.column("Quantity", width=80)
        self.transfer_cart_tree.column("Price", width=100)
        self.transfer_cart_tree.column("Total", width=100)
        
        cart_vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.transfer_cart_tree.yview)
        self.transfer_cart_tree.configure(yscrollcommand=cart_vsb.set)
        self.transfer_cart_tree.pack(side="left", fill="both", expand=True)
        cart_vsb.pack(side="right", fill="y")
        
        # Cart Buttons
        cart_btn_frame = tk.Frame(cart_frame, bg="#f5f5f5")
        cart_btn_frame.pack(fill="x", pady=5)
        tk.Button(cart_btn_frame, text="🗑️ Remove", command=self.remove_from_transfer_cart, bg="#e74a3b", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat").pack(side="right", padx=5)
        tk.Button(cart_btn_frame, text="🔄 Clear Cart", command=self.clear_transfer_cart, bg="#f6c23e", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat").pack(side="right", padx=5)
        
                # ===== RIGHT SIDE (COMPACT - NO SCROLLING NEEDED) =====
        form_frame = tk.Frame(right_scrollable_frame, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(form_frame, text="📝 TRANSFER DETAILS", font=("Arial", 13, "bold"), bg="white", fg="#1a1a2e").pack(pady=8)
        
        # Two column layout for compactness
        row1 = tk.Frame(form_frame, bg="white")
        row1.pack(fill="x", padx=15, pady=5)
        tk.Label(row1, text="Destination City:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.destination_city = ttk.Combobox(row1, font=("Arial", 10), width=20, state="readonly")
        self.destination_city['values'] = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan', 'Peshawar', 'Quetta', 'Other']
        self.destination_city.pack(side="left", padx=5)
        self.destination_city.current(0)
        
        row2 = tk.Frame(form_frame, bg="white")
        row2.pack(fill="x", padx=15, pady=5)
        tk.Label(row2, text="Other City:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.custom_city_entry = tk.Entry(row2, font=("Arial", 10), width=22)
        self.custom_city_entry.pack(side="left", padx=5)
        
        row3 = tk.Frame(form_frame, bg="white")
        row3.pack(fill="x", padx=15, pady=5)
        tk.Label(row3, text="Recipient Name:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.recipient_name = tk.Entry(row3, font=("Arial", 10), width=22)
        self.recipient_name.pack(side="left", padx=5)
        
        row4 = tk.Frame(form_frame, bg="white")
        row4.pack(fill="x", padx=15, pady=5)
        tk.Label(row4, text="Transfer Type:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.transfer_type = ttk.Combobox(row4, font=("Arial", 10), width=20, state="readonly")
        self.transfer_type['values'] = ['Sale to Customer', 'Stock Transfer to Branch', 'Wholesale Supply']
        self.transfer_type.pack(side="left", padx=5)
        self.transfer_type.current(0)
        
        row5 = tk.Frame(form_frame, bg="white")
        row5.pack(fill="x", padx=15, pady=5)
        tk.Label(row5, text="Payment Status:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.payment_status = ttk.Combobox(row5, font=("Arial", 10), width=20, state="readonly")
        self.payment_status['values'] = ['Paid', 'Partial', 'Pending']
        self.payment_status.pack(side="left", padx=5)
        self.payment_status.current(0)
        
        row6 = tk.Frame(form_frame, bg="white")
        row6.pack(fill="x", padx=15, pady=5)
        tk.Label(row6, text="Amount Paid:", font=("Arial", 10), bg="white", width=14, anchor="w").pack(side="left")
        self.amount_paid_entry = tk.Entry(row6, font=("Arial", 10), width=22)
        self.amount_paid_entry.pack(side="left", padx=5)
        self.amount_paid_entry.insert(0, "0")
        
        # Separator
        tk.Frame(form_frame, height=2, bg="#e94560").pack(fill="x", padx=15, pady=10)
        
        # Total Amount
        total_frame = tk.Frame(form_frame, bg="white")
        total_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(total_frame, text="TOTAL AMOUNT:", font=("Arial", 12, "bold"), bg="white", fg="#e94560").pack(side="left")
        self.transfer_total_label = tk.Label(total_frame, text="Rs. 0.00", font=("Arial", 14, "bold"), bg="white", fg="#e94560")
        self.transfer_total_label.pack(side="right")
        
        # ===== BUTTONS - ALL VISIBLE WITHOUT SCROLLING =====
        tk.Frame(form_frame, height=5, bg="white").pack()
        
        # Add to Cart Button
        add_btn = tk.Button(form_frame, text="➕ ADD TO CART", command=self.open_transfer_quantity_dialog, 
                            bg="#36b9cc", fg="white", font=("Arial", 11, "bold"), 
                            padx=20, pady=8, relief="flat", cursor="hand2")
        add_btn.pack(pady=5, padx=15, fill="x")
        
        # Complete Transfer Button (Prominent)
        complete_btn = tk.Button(form_frame, text="✅ COMPLETE TRANSFER", command=self.complete_transfer, 
                                  bg="#1cc88a", fg="white", font=("Arial", 12, "bold"), 
                                  padx=20, pady=10, relief="flat", cursor="hand2")
        complete_btn.pack(pady=8, padx=15, fill="x")
        
        # Print Invoice Button
        print_btn = tk.Button(form_frame, text="🖨️ PRINT INVOICE", command=self.print_transfer_invoice, 
                              bg="#e94560", fg="white", font=("Arial", 11, "bold"), 
                              padx=20, pady=8, relief="flat", cursor="hand2")
        print_btn.pack(pady=5, padx=15, fill="x")
        
        # Double click to add
        self.transfer_products_tree.bind("<Double-1>", lambda e: self.open_transfer_quantity_dialog())
        
        # Initialize
        self.transfer_cart = []
        self.load_transfer_products()
    
    def load_transfer_products(self, search_term=""):
        """Load products for transfer"""
        for item in self.transfer_products_tree.get_children():
            self.transfer_products_tree.delete(item)
        
        try:
            if search_term:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE (name LIKE ? OR brand LIKE ?) AND stock_quantity > 0 ORDER BY id DESC"
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE stock_quantity > 0 ORDER BY id DESC"
                params = ()
            
            products = self.fetch_all(query, params)
            for product in products:
                self.transfer_products_tree.insert("", "end", values=(
                    product[0], product[1], product[2] or "-", product[3], f"Rs. {product[4]:.2f}"
                ))
            self.update_status(f"Loaded {len(products)} products available for transfer")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def open_transfer_quantity_dialog(self):
        """Open dialog to enter transfer quantity with custom price and loss warning - with Pack/Piece"""
        selected = self.transfer_products_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return
        
        item = self.transfer_products_tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        available_stock = item['values'][3]
        default_price = float(item['values'][4].replace('Rs. ', ''))
        
        # Get cost price and pack info for loss calculation
        product_info = self.fetch_one("SELECT cost_price, unit_type, pieces_per_pack, pack_price FROM products WHERE id = ?", (product_id,))
        cost_price = product_info[0] if product_info else 0
        unit_type = product_info[1] if product_info else "Piece"
        pieces_per_pack = product_info[2] if product_info else 1
        pack_price = product_info[3] if product_info else 0
        
        if available_stock <= 0:
            messagebox.showwarning("Out of Stock", f"{product_name} is out of stock!")
            return
        
        # Main dialog with both scrollbars
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Transfer Quantity - {product_name}")
        dialog.geometry("600x700")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product_name}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with both scrollbars
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        def on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stock info
        info_frame = tk.Frame(content, bg="#f5f5f5")
        info_frame.pack(fill="x", pady=5)
        tk.Label(info_frame, text=f"Available Stock: {available_stock} pieces", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack()
        tk.Label(info_frame, text=f"Cost Price: Rs. {cost_price:.2f} per piece", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        if unit_type == "Pack" and pack_price > 0:
            tk.Label(info_frame, text=f"Pack Price: Rs. {pack_price:.2f} per pack ({pieces_per_pack} pieces)", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Price Options
        price_frame = tk.LabelFrame(content, text="Price Options", font=("Arial", 12, "bold"), bg="#f5f5f5")
        price_frame.pack(fill="x", pady=10)
        
        price_inner = tk.Frame(price_frame, bg="#f5f5f5")
        price_inner.pack(padx=15, pady=10)
        
        self.transfer_price_option = tk.StringVar(value="default")
        
        default_radio = tk.Radiobutton(price_inner, text=f"Default Price: Rs. {default_price:.2f} per piece", 
                                        variable=self.transfer_price_option, value="default", bg="#f5f5f5", font=("Arial", 10))
        default_radio.pack(anchor="w", pady=3)
        
        custom_radio = tk.Radiobutton(price_inner, text="Custom Price:", 
                                      variable=self.transfer_price_option, value="custom", bg="#f5f5f5", font=("Arial", 10))
        custom_radio.pack(anchor="w", pady=3)
        
        custom_frame = tk.Frame(price_inner, bg="#f5f5f5")
        custom_frame.pack(anchor="w", padx=20)
        tk.Label(custom_frame, text="Rs.", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.transfer_custom_price = tk.Entry(custom_frame, font=("Arial", 11), width=12)
        self.transfer_custom_price.pack(side="left", padx=5)
        self.transfer_custom_price.insert(0, str(default_price))
        self.transfer_custom_price.config(state="disabled")
        
        # Loss warning
        self.transfer_loss_label = tk.Label(price_inner, text="", font=("Arial", 9), bg="#f5f5f5", fg="#e74a3b")
        self.transfer_loss_label.pack(anchor="w", pady=5)
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Purchase Type Selection (if pack available)
        if unit_type == "Pack" and pack_price > 0:
            type_frame = tk.LabelFrame(content, text="Transfer Type", font=("Arial", 11, "bold"), bg="#f5f5f5")
            type_frame.pack(fill="x", pady=10)
            
            type_inner = tk.Frame(type_frame, bg="#f5f5f5")
            type_inner.pack(padx=15, pady=10)
            
            self.transfer_buy_type = tk.StringVar(value="Pack")
            
            piece_radio = tk.Radiobutton(type_inner, text=f"Transfer by Piece (Rs. {default_price:.2f} each)", 
                                          variable=self.transfer_buy_type, value="Piece", bg="#f5f5f5", font=("Arial", 10))
            piece_radio.pack(anchor="w", pady=5)
            
            pack_radio = tk.Radiobutton(type_inner, text=f"Transfer by Pack (Rs. {pack_price:.2f} per pack - {pieces_per_pack} pieces)", 
                                          variable=self.transfer_buy_type, value="Pack", bg="#f5f5f5", font=("Arial", 10))
            pack_radio.pack(anchor="w", pady=5)
            
            # Separator
            tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
            
            # Quantity Frame
            qty_main_frame = tk.LabelFrame(content, text="Quantity", font=("Arial", 11, "bold"), bg="#f5f5f5")
            qty_main_frame.pack(fill="x", pady=10)
            
            qty_inner = tk.Frame(qty_main_frame, bg="#f5f5f5")
            qty_inner.pack(padx=15, pady=10)
            
            # Piece mode
            piece_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(piece_qty_frame, text="Number of Pieces:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.transfer_piece_qty = tk.Entry(piece_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.transfer_piece_qty.pack(side="left", padx=10)
            self.transfer_piece_qty.insert(0, "1")
            
            # Pack mode
            pack_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(pack_qty_frame, text="Number of Packs:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.transfer_pack_qty = tk.Entry(pack_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.transfer_pack_qty.pack(side="left", padx=10)
            self.transfer_pack_qty.insert(0, "1")
            
            tk.Label(pack_qty_frame, text=f"(= {pieces_per_pack} pieces each)", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack(side="left", padx=5)
            
            # Extra pieces
            extra_frame = tk.Frame(pack_qty_frame, bg="#f5f5f5")
            extra_frame.pack(pady=5)
            tk.Label(extra_frame, text="Extra Pieces:", font=("Arial", 10), bg="#f5f5f5").pack(side="left")
            self.transfer_extra_pieces = tk.Entry(extra_frame, font=("Arial", 11), width=8, justify="center")
            self.transfer_extra_pieces.pack(side="left", padx=10)
            self.transfer_extra_pieces.insert(0, "0")
            
            # Initially show pack mode (DEFAULT)
            piece_qty_frame.pack_forget()
            pack_qty_frame.pack()
            
            # Total pieces display
            total_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            total_frame.pack(pady=10)
            tk.Label(total_frame, text="Total Pieces:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
            self.transfer_total_pieces = tk.Label(total_frame, text="1", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
            self.transfer_total_pieces.pack(side="left", padx=10)
            
            # Total preview
            preview_frame = tk.Frame(content, bg="#f0f0f0", relief="ridge", bd=1)
            preview_frame.pack(fill="x", pady=10)
            
            tk.Label(preview_frame, text="💰 TOTAL AMOUNT:", font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#e94560").pack(side="left", padx=15, pady=10)
            self.transfer_preview_total = tk.Label(preview_frame, text="Rs. 0.00", font=("Arial", 13, "bold"), bg="#f0f0f0", fg="#e94560")
            self.transfer_preview_total.pack(side="right", padx=15, pady=10)
            
            # Profit/Loss preview
            self.transfer_pl_label = tk.Label(content, text="", font=("Arial", 10), bg="#f5f5f5")
            self.transfer_pl_label.pack(pady=5)
            
            def update_transfer_total(*args):
                try:
                    if self.transfer_buy_type.get() == "Piece":
                        qty = int(self.transfer_piece_qty.get() or 0)
                        self.transfer_total_pieces.config(text=str(qty))
                    else:
                        packs = int(self.transfer_pack_qty.get() or 0)
                        extra = int(self.transfer_extra_pieces.get() or 0)
                        qty = (packs * pieces_per_pack) + extra
                        self.transfer_total_pieces.config(text=str(qty))
                    update_transfer_preview()
                except:
                    self.transfer_total_pieces.config(text="0")
                    update_transfer_preview()
            
            def update_transfer_preview(*args):
                try:
                    if self.transfer_buy_type.get() == "Piece":
                        qty = int(self.transfer_piece_qty.get() or 0)
                    else:
                        packs = int(self.transfer_pack_qty.get() or 0)
                        extra = int(self.transfer_extra_pieces.get() or 0)
                        qty = (packs * pieces_per_pack) + extra
                    
                    if self.transfer_price_option.get() == "custom":
                        try:
                            price_per_piece = float(self.transfer_custom_price.get())
                        except:
                            price_per_piece = default_price
                    else:
                        price_per_piece = default_price
                    
                    total = qty * price_per_piece
                    
                    if self.transfer_buy_type.get() == "Pack" and qty > 0:
                        packs = qty // pieces_per_pack
                        remaining = qty % pieces_per_pack
                        self.transfer_preview_total.config(text=f"Rs. {total:,.2f} ({packs} pack + {remaining} pcs)")
                    else:
                        self.transfer_preview_total.config(text=f"Rs. {total:,.2f}")
                    
                    if qty > 0:
                        if price_per_piece < cost_price:
                            loss_amount = (cost_price - price_per_piece) * qty
                            self.transfer_pl_label.config(text=f"⚠️ LOSS: Rs. {loss_amount:,.2f}", fg="#e74a3b")
                        else:
                            profit_amount = (price_per_piece - cost_price) * qty
                            self.transfer_pl_label.config(text=f"✓ PROFIT: Rs. {profit_amount:,.2f}", fg="#1cc88a")
                    else:
                        self.transfer_pl_label.config(text="")
                except:
                    self.transfer_preview_total.config(text="Rs. 0.00")
            
            def check_transfer_loss():
                try:
                    if self.transfer_price_option.get() == "custom":
                        custom_price = float(self.transfer_custom_price.get())
                        if custom_price < cost_price:
                            loss_amount = cost_price - custom_price
                            self.transfer_loss_label.config(text=f"⚠️ Loss of Rs. {loss_amount:.2f} per piece!", fg="#e74a3b")
                        else:
                            self.transfer_loss_label.config(text="")
                    else:
                        self.transfer_loss_label.config(text="")
                except:
                    self.transfer_loss_label.config(text="")
            
            def on_transfer_buy_type_change(*args):
                if self.transfer_buy_type.get() == "Piece":
                    piece_qty_frame.pack()
                    pack_qty_frame.pack_forget()
                    self.transfer_piece_qty.delete(0, tk.END)
                    self.transfer_piece_qty.insert(0, "1")
                else:
                    piece_qty_frame.pack_forget()
                    pack_qty_frame.pack()
                    self.transfer_pack_qty.delete(0, tk.END)
                    self.transfer_pack_qty.insert(0, "1")
                    self.transfer_extra_pieces.delete(0, tk.END)
                    self.transfer_extra_pieces.insert(0, "0")
                update_transfer_total()
            
            def on_transfer_price_change(*args):
                if self.transfer_price_option.get() == "custom":
                    self.transfer_custom_price.config(state="normal")
                    self.transfer_custom_price.focus()
                    check_transfer_loss()
                else:
                    self.transfer_custom_price.config(state="disabled")
                    self.transfer_custom_price.delete(0, tk.END)
                    self.transfer_custom_price.insert(0, str(default_price))
                    self.transfer_loss_label.config(text="")
                update_transfer_preview()
            
            self.transfer_buy_type.trace('w', on_transfer_buy_type_change)
            self.transfer_price_option.trace('w', on_transfer_price_change)
            self.transfer_piece_qty.bind("<KeyRelease>", update_transfer_total)
            self.transfer_pack_qty.bind("<KeyRelease>", update_transfer_total)
            self.transfer_extra_pieces.bind("<KeyRelease>", update_transfer_total)
            self.transfer_custom_price.bind("<KeyRelease>", lambda e: [check_transfer_loss(), update_transfer_preview()])
            
            def add_to_transfer_cart():
                try:
                    if self.transfer_buy_type.get() == "Piece":
                        quantity = int(self.transfer_piece_qty.get() or 0)
                    else:
                        packs = int(self.transfer_pack_qty.get() or 0)
                        extra = int(self.transfer_extra_pieces.get() or 0)
                        quantity = (packs * pieces_per_pack) + extra
                    
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    if quantity > available_stock:
                        messagebox.showwarning("Insufficient Stock", f"Only {available_stock} units available!")
                        return
                    
                    if self.transfer_price_option.get() == "custom":
                        try:
                            final_price = float(self.transfer_custom_price.get())
                            if final_price <= 0:
                                messagebox.showwarning("Invalid Price", "Price must be greater than 0!")
                                return
                        except:
                            messagebox.showwarning("Invalid Price", "Please enter a valid price!")
                            return
                        
                        if final_price < cost_price:
                            loss_amount = (cost_price - final_price) * quantity
                            confirm = messagebox.askyesno(
                                "⚠️ LOSS WARNING ⚠️",
                                f"Product: {product_name}\n"
                                f"Cost Price: Rs. {cost_price:.2f}\n"
                                f"Transfer Price: Rs. {final_price:.2f}\n"
                                f"Quantity: {quantity} pieces\n\n"
                                f"This will result in a LOSS of Rs. {loss_amount:,.2f}!",
                                icon='warning'
                            )
                            if not confirm:
                                return
                    else:
                        final_price = default_price
                    
                    total = quantity * final_price
                    
                    if self.transfer_buy_type.get() == "Pack":
                        packs_sold = int(self.transfer_pack_qty.get() or 0)
                        extra_sold = int(self.transfer_extra_pieces.get() or 0)
                        sale_note = f" ({packs_sold} pack + {extra_sold} pcs)"
                    else:
                        sale_note = ""
                    
                    cart_item = {
                        'product_id': product_id,
                        'name': product_name + sale_note,
                        'quantity': quantity,
                        'price': final_price,
                        'original_price': default_price,
                        'total': total,
                        'is_custom_price': self.transfer_price_option.get() == "custom",
                        'cost_price': cost_price
                    }
                    self.transfer_cart.append(cart_item)
                    self.update_transfer_cart_display()
                    self.update_transfer_total()
                    dialog.destroy()
                    
                    if cart_item['is_custom_price']:
                        if final_price < cost_price:
                            self.update_status(f"⚠️ Added {quantity} x {product_name} at LOSS")
                        else:
                            self.update_status(f"Added {quantity} x {product_name} at custom price")
                    else:
                        self.update_status(f"Added {quantity} x {product_name} to transfer cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=15)
            tk.Button(btn_frame, text="Add to Cart", command=add_to_transfer_cart, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            update_transfer_total()
        
        else:
            # Simple dialog for products without pack
            # Quantity
            tk.Label(content, text="Quantity:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
            quantity_entry = tk.Entry(content, font=("Arial", 12), width=15, justify="center")
            quantity_entry.pack()
            quantity_entry.focus()
            
            # Total preview
            preview_frame = tk.Frame(content, bg="#f5f5f5")
            preview_frame.pack(pady=10)
            tk.Label(preview_frame, text="Total Amount:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
            simple_preview_total = tk.Label(preview_frame, text="Rs. 0.00", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
            simple_preview_total.pack(side="left", padx=10)
            
            def update_simple_preview(event=None):
                try:
                    qty = int(quantity_entry.get() or 0)
                    if self.transfer_price_option.get() == "custom":
                        try:
                            price = float(self.transfer_custom_price.get())
                        except:
                            price = default_price
                    else:
                        price = default_price
                    total = qty * price
                    simple_preview_total.config(text=f"Rs. {total:,.2f}")
                except:
                    simple_preview_total.config(text="Rs. 0.00")
            
            quantity_entry.bind("<KeyRelease>", update_simple_preview)
            
            def add_simple_to_cart():
                try:
                    quantity = int(quantity_entry.get())
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    if quantity > available_stock:
                        messagebox.showwarning("Insufficient Stock", f"Only {available_stock} units available!")
                        return
                    
                    if self.transfer_price_option.get() == "custom":
                        try:
                            final_price = float(self.transfer_custom_price.get())
                            if final_price <= 0:
                                messagebox.showwarning("Invalid Price", "Price must be greater than 0!")
                                return
                        except:
                            messagebox.showwarning("Invalid Price", "Please enter a valid price!")
                            return
                        
                        if final_price < cost_price:
                            loss_amount = (cost_price - final_price) * quantity
                            confirm = messagebox.askyesno(
                                "⚠️ LOSS WARNING ⚠️",
                                f"Product: {product_name}\n"
                                f"Cost Price: Rs. {cost_price:.2f}\n"
                                f"Your Price: Rs. {final_price:.2f}\n"
                                f"Quantity: {quantity}\n\n"
                                f"This will result in a LOSS of Rs. {loss_amount:,.2f}!",
                                icon='warning'
                            )
                            if not confirm:
                                return
                    else:
                        final_price = default_price
                    
                    total = quantity * final_price
                    cart_item = {
                        'product_id': product_id,
                        'name': product_name,
                        'quantity': quantity,
                        'price': final_price,
                        'original_price': default_price,
                        'total': total,
                        'is_custom_price': self.transfer_price_option.get() == "custom",
                        'cost_price': cost_price
                    }
                    self.transfer_cart.append(cart_item)
                    self.update_transfer_cart_display()
                    self.update_transfer_total()
                    dialog.destroy()
                    
                    if cart_item['is_custom_price']:
                        if final_price < cost_price:
                            self.update_status(f"⚠️ Added {quantity} x {product_name} at LOSS")
                        else:
                            self.update_status(f"Added {quantity} x {product_name} at custom price")
                    else:
                        self.update_status(f"Added {quantity} x {product_name} to transfer cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="Add to Cart", command=add_simple_to_cart, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            update_simple_preview()
    
    def update_transfer_cart_display(self):
        """Update transfer cart display with custom price and loss indicator"""
        for item in self.transfer_cart_tree.get_children():
            self.transfer_cart_tree.delete(item)
        
        for i, item in enumerate(self.transfer_cart, 1):
            price_display = f"Rs. {item['price']:.2f}"
            if item.get('is_custom_price'):
                if item.get('price') < item.get('cost_price', 0):
                    price_display = f"⚠️ Rs. {item['price']:.2f}"
                else:
                    price_display = f"*Rs. {item['price']:.2f}"
            
            self.transfer_cart_tree.insert("", "end", values=(
                i,
                item['name'],
                item['quantity'],
                price_display,
                f"Rs. {item['total']:.2f}"
            ))
    
    def update_transfer_total(self):
        """Update transfer total display"""
        total = sum(item['total'] for item in self.transfer_cart)
        self.transfer_total_label.config(text=f"Rs. {total:,.2f}")
    
    def remove_from_transfer_cart(self):
        """Remove item from transfer cart"""
        selected = self.transfer_cart_tree.selection()
        if not selected:
            return
        item = self.transfer_cart_tree.item(selected[0])
        index = int(item['values'][0]) - 1
        if 0 <= index < len(self.transfer_cart):
            removed = self.transfer_cart.pop(index)
            self.update_transfer_cart_display()
            self.update_transfer_total()
            self.update_status(f"Removed {removed['name']} from cart")
    
    def clear_transfer_cart(self):
        """Clear transfer cart"""
        if self.transfer_cart and messagebox.askyesno("Clear Cart", "Clear entire transfer cart?"):
            self.transfer_cart.clear()
            self.update_transfer_cart_display()
            self.update_transfer_total()
            self.update_status("Transfer cart cleared")
    
    def complete_transfer(self):
        """Complete the stock transfer"""
        if not self.transfer_cart:
            messagebox.showwarning("Empty Cart", "Please add items to transfer!")
            return
        
        # Get city
        city = self.destination_city.get()
        if city == "Other":
            city = self.custom_city_entry.get().strip()
            if not city:
                messagebox.showwarning("Missing City", "Please enter city name!")
                return
        
        transfer_type = self.transfer_type.get()
        recipient = self.recipient_name.get().strip() or "Branch Transfer"
        total_amount = sum(item['total'] for item in self.transfer_cart)
        
        # Payment info
        payment_status = self.payment_status.get()
        amount_paid = float(self.amount_paid_entry.get() or 0)
        balance_due = total_amount - amount_paid if payment_status == "Partial" else (0 if payment_status == "Paid" else total_amount)
        
        # Generate transfer invoice number
        last_transfer = self.fetch_one("SELECT transfer_no FROM stock_transfers ORDER BY id DESC LIMIT 1")
        if last_transfer and last_transfer[0]:
            num = int(last_transfer[0].split('-')[-1]) + 1
            transfer_no = f"TRF-{datetime.now().year}-{num:03d}"
        else:
            transfer_no = f"TRF-{datetime.now().year}-001"
        
        confirm = messagebox.askyesno(
            "Confirm Transfer",
            f"Transfer No: {transfer_no}\n"
            f"Destination: {city}\n"
            f"Type: {transfer_type}\n"
            f"Recipient: {recipient}\n"
            f"Items: {len(self.transfer_cart)}\n"
            f"Total: Rs. {total_amount:,.2f}\n"
            f"Payment: {payment_status} (Paid: Rs. {amount_paid:,.2f})\n\n"
            f"Proceed with transfer?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create transfer table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_no TEXT UNIQUE NOT NULL,
                    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    destination_city TEXT NOT NULL,
                    recipient_name TEXT,
                    transfer_type TEXT,
                    total_amount REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Pending',
                    amount_paid REAL DEFAULT 0,
                    balance_due REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            # Insert transfer record
            cursor.execute("""
                INSERT INTO stock_transfers 
                (transfer_no, destination_city, recipient_name, transfer_type, total_amount, payment_status, amount_paid, balance_due)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (transfer_no, city, recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due))
            
            transfer_id = cursor.lastrowid
            
            # Insert transfer items and update stock
            for item in self.transfer_cart:
                cursor.execute("""
                    INSERT INTO transfer_items (transfer_id, product_id, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (transfer_id, item['product_id'], item['quantity'], item['price'], item['total']))
                
                # REDUCE stock from main warehouse
                cursor.execute("""
                    UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (item['quantity'], item['product_id']))
            
                        # Add to ledger - CORRECT WAY (Credit for payments received)
            if payment_status == "Paid":
                # پوری رقم آگئی - Credit میں ڈالیں
                cursor.execute("""
                    INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, ("TRANSFER", transfer_no, f"Stock transfer to {city} - {recipient} (Paid)", 0, total_amount))
            elif payment_status == "Partial":
                # صرف جزوی رقم آئی - اتنی Credit میں ڈالیں
                cursor.execute("""
                    INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, ("TRANSFER", transfer_no, f"Stock transfer to {city} - {recipient} (Partial: Rs.{amount_paid:,.0f} paid)", 0, amount_paid))
            # Pending کے لیے Ledger میں کوئی اندراج نہیں - جب پیسے آئیں گے تب ڈالیں گے
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Stock transfer completed!\nTransfer No: {transfer_no}\nTotal: Rs. {total_amount:,.2f}\nDestination: {city}")
            
            # Print invoice
            self.print_transfer_invoice_after(transfer_no, city, recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due)
            
            # Reset form
            self.transfer_cart.clear()
            self.update_transfer_cart_display()
            self.update_transfer_total()
            self.custom_city_entry.delete(0, tk.END)
            self.recipient_name.delete(0, tk.END)
            self.amount_paid_entry.delete(0, tk.END)
            self.amount_paid_entry.insert(0, "0")
            self.transfer_type.current(0)
            self.payment_status.current(0)
            self.load_transfer_products()
            self.load_transfer_history()
            
            self.update_status(f"✅ Transfer completed: {transfer_no}")
            self.force_refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete transfer: {str(e)}")
    
    def create_transfer_history_tab(self, parent):
        """Create Transfer History tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="📜 Stock Transfer History", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Filter Frame
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=10)
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=10, pady=10)
        
        tk.Label(filter_inner, text="City:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.history_city_filter = ttk.Combobox(filter_inner, font=("Arial", 10), width=12, state="readonly")
        self.history_city_filter['values'] = ['All', 'Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan', 'Peshawar']
        self.history_city_filter.pack(side="left", padx=5)
        self.history_city_filter.current(0)
        
        tk.Label(filter_inner, text="From:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.history_date_from = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.history_date_from.pack(side="left", padx=5)
        self.history_date_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(filter_inner, text="To:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.history_date_to = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.history_date_to.pack(side="left", padx=5)
        self.history_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(filter_inner, text="🔍 Filter", command=self.load_transfer_history, bg="#36b9cc", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(side="left", padx=10)
        
        # Treeview with scrollbars
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Transfer No", "Date", "City", "Recipient", "Type", "Total", "Payment", "Balance")
        self.transfer_history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.transfer_history_tree.heading("Transfer No", text="Transfer No")
        self.transfer_history_tree.heading("Date", text="Date")
        self.transfer_history_tree.heading("City", text="City")
        self.transfer_history_tree.heading("Recipient", text="Recipient")
        self.transfer_history_tree.heading("Type", text="Type")
        self.transfer_history_tree.heading("Total", text="Total (Rs.)")
        self.transfer_history_tree.heading("Payment", text="Payment")
        self.transfer_history_tree.heading("Balance", text="Balance Due")
        
        self.transfer_history_tree.column("Transfer No", width=120)
        self.transfer_history_tree.column("Date", width=100)
        self.transfer_history_tree.column("City", width=100)
        self.transfer_history_tree.column("Recipient", width=120)
        self.transfer_history_tree.column("Type", width=120)
        self.transfer_history_tree.column("Total", width=100)
        self.transfer_history_tree.column("Payment", width=80)
        self.transfer_history_tree.column("Balance", width=100)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.transfer_history_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.transfer_history_tree.xview)
        self.transfer_history_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.transfer_history_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Double click to view details
        self.transfer_history_tree.bind("<Double-1>", lambda e: self.view_transfer_details())
        
        self.load_transfer_history()
    
    def load_transfer_history(self):
        """Load transfer history with filters"""
        for item in self.transfer_history_tree.get_children():
            self.transfer_history_tree.delete(item)
        
        try:
            query = "SELECT * FROM stock_transfers WHERE 1=1"
            params = []
            
            city = self.history_city_filter.get()
            if city and city != "All":
                query += " AND destination_city = ?"
                params.append(city)
            
            date_from = self.history_date_from.get()
            date_to = self.history_date_to.get()
            if date_from:
                query += " AND DATE(transfer_date) >= ?"
                params.append(date_from)
            if date_to:
                query += " AND DATE(transfer_date) <= ?"
                params.append(date_to)
            
            query += " ORDER BY transfer_date DESC"
            
            transfers = self.fetch_all(query, params)
            
            for transfer in transfers:
                self.transfer_history_tree.insert("", "end", values=(
                    transfer[1], transfer[2][:10] if transfer[2] else "-",
                    transfer[3], transfer[4] or "-", transfer[5] or "-",
                    f"Rs. {transfer[6]:,.2f}", transfer[7] or "-",
                    f"Rs. {transfer[9]:,.2f}" if transfer[9] > 0 else "Paid"
                ))
            
            self.update_status(f"Loaded {len(transfers)} transfer records")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def view_transfer_details(self):
        """View transfer details"""
        selected = self.transfer_history_tree.selection()
        if not selected:
            return
        
        item = self.transfer_history_tree.item(selected[0])
        transfer_no = item['values'][0]
        
        transfer = self.fetch_one("SELECT * FROM stock_transfers WHERE transfer_no = ?", (transfer_no,))
        if not transfer:
            return
        
        items = self.fetch_all("""
            SELECT ti.*, p.name 
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transfer_id = ?
        """, (transfer[0],))
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Transfer Details - {transfer_no}")
        dialog.geometry("700x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        
        tk.Label(dialog, text=f"📋 Transfer Details: {transfer_no}", font=("Helvetica", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Info Frame
        info_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = f"""
        Date: {transfer[2][:19] if transfer[2] else '-'}
        Destination: {transfer[3]}
        Recipient: {transfer[4] or '-'}
        Transfer Type: {transfer[5] or '-'}
        Payment Status: {transfer[7] or '-'}
        Amount Paid: Rs. {transfer[8]:,.2f}
        Balance Due: Rs. {transfer[9]:,.2f}
        Total Amount: Rs. {transfer[6]:,.2f}
        """
        tk.Label(info_frame, text=info_text, font=("Arial", 10), bg="white", justify="left").pack(padx=20, pady=10)
        
        # Items Treeview
        items_frame = tk.Frame(dialog, bg="#f5f5f5")
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(items_frame, text="Transferred Items:", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor="w")
        
        tree_frame = tk.Frame(items_frame, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("Product", "Quantity", "Price", "Total")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        tree.heading("Product", text="Product")
        tree.heading("Quantity", text="Quantity")
        tree.heading("Price", text="Price (Rs.)")
        tree.heading("Total", text="Total (Rs.)")
        
        tree.column("Product", width=300)
        tree.column("Quantity", width=80)
        tree.column("Price", width=100)
        tree.column("Total", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for item in items:
            tree.insert("", "end", values=(item[5], item[2], f"Rs. {item[3]:,.2f}", f"Rs. {item[4]:,.2f}"))
        
        tk.Button(dialog, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(pady=10)
    
    def create_city_stock_tab(self, parent):
        """Create City Stock View tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="🏙️ City-wise Stock Summary", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # City selection
        select_frame = tk.Frame(main_container, bg="#f5f5f5")
        select_frame.pack(pady=10)
        
        tk.Label(select_frame, text="Select City:", font=("Arial", 11), bg="#f5f5f5").pack(side="left", padx=5)
        self.city_stock_combo = ttk.Combobox(select_frame, font=("Arial", 11), width=15, state="readonly")
        self.city_stock_combo.pack(side="left", padx=5)
        self.city_stock_combo.bind('<<ComboboxSelected>>', lambda e: self.load_city_stock())
        
        # Load cities from transfers (with error handling)
        try:
            cities = self.fetch_all("SELECT DISTINCT destination_city FROM stock_transfers ORDER BY destination_city")
            city_list = ["All"] + [c[0] for c in cities]
            self.city_stock_combo['values'] = city_list
        except:
            self.city_stock_combo['values'] = ["All"]
        if self.city_stock_combo['values']:
            self.city_stock_combo.current(0)
        
        # Summary cards
        self.city_summary_frame = tk.Frame(main_container, bg="#f5f5f5")
        self.city_summary_frame.pack(fill="x", pady=10)
        
        # Treeview
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Product", "Total Transferred", "Total Value", "Last Transfer")
        self.city_stock_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        self.city_stock_tree.heading("Product", text="Product Name")
        self.city_stock_tree.heading("Total Transferred", text="Total Transferred")
        self.city_stock_tree.heading("Total Value", text="Total Value (Rs.)")
        self.city_stock_tree.heading("Last Transfer", text="Last Transfer Date")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.city_stock_tree.yview)
        self.city_stock_tree.configure(yscrollcommand=vsb.set)
        self.city_stock_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.load_city_stock()
    
    def load_city_stock(self):
        """Load city-wise stock data"""
        for item in self.city_stock_tree.get_children():
            self.city_stock_tree.delete(item)
        
        city = self.city_stock_combo.get()
        
        try:
            if city == "All":
                query = """
                    SELECT p.name, COALESCE(SUM(ti.quantity), 0) as total_qty, 
                           COALESCE(SUM(ti.total), 0) as total_value,
                           MAX(st.transfer_date) as last_transfer
                    FROM products p
                    LEFT JOIN transfer_items ti ON p.id = ti.product_id
                    LEFT JOIN stock_transfers st ON ti.transfer_id = st.id
                    GROUP BY p.id
                    HAVING total_qty > 0
                    ORDER BY total_qty DESC
                """
                params = ()
            else:
                query = """
                    SELECT p.name, COALESCE(SUM(ti.quantity), 0) as total_qty, 
                           COALESCE(SUM(ti.total), 0) as total_value,
                           MAX(st.transfer_date) as last_transfer
                    FROM products p
                    LEFT JOIN transfer_items ti ON p.id = ti.product_id
                    LEFT JOIN stock_transfers st ON ti.transfer_id = st.id
                    WHERE st.destination_city = ?
                    GROUP BY p.id
                    HAVING total_qty > 0
                    ORDER BY total_qty DESC
                """
                params = (city,)
            
            transfers = self.fetch_all(query, params)
            
            total_qty_all = 0
            total_value_all = 0
            
            for transfer in transfers:
                total_qty_all += transfer[1]
                total_value_all += transfer[2]
                self.city_stock_tree.insert("", "end", values=(
                    transfer[0], transfer[1], f"Rs. {transfer[2]:,.2f}",
                    transfer[3][:10] if transfer[3] else "-"
                ))
            
            # Update summary
            for widget in self.city_summary_frame.winfo_children():
                widget.destroy()
            
            summary_text = f"📊 Summary for {city}: Total Products Transferred: {len(transfers)} | Total Units: {total_qty_all} | Total Value: Rs. {total_value_all:,.2f}"
            tk.Label(self.city_summary_frame, text=summary_text, font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack()
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def print_transfer_invoice(self):
        """Print transfer invoice for current cart"""
        if not self.transfer_cart:
            messagebox.showwarning("No Transfer", "Please add items to transfer first!")
            return
        
        city = self.destination_city.get()
        if city == "Other":
            city = self.custom_city_entry.get().strip() or "Unknown"
        
        recipient = self.recipient_name.get().strip() or "Branch Transfer"
        total = sum(item['total'] for item in self.transfer_cart)
        
        transfer_no = f"TRF-{datetime.now().year}-{datetime.now().strftime('%d')}"
        
        self.show_transfer_invoice_preview(transfer_no, city, recipient, total)
    
    def print_transfer_invoice_after(self, transfer_no, city, recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due):
        """Professional Transfer Receipt"""
        now = datetime.now()
        
        lines = []
        width = 36
        
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "FAIZAN PAPER MART" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("Rail Bazar") - 2) // 2) + "Rail Bazar" + " " * ((width - len("Rail Bazar") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("0300-8706085") - 2) // 2) + "0300-8706085" + " " * ((width - len("0300-8706085") - 2) // 2) + "|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Slip : TRANSFER NOTE{' ' * (width - 24)}|")
        lines.append(f"| No   : {transfer_no:<{width-10}}|")
        lines.append(f"| Date : {now.strftime('%d-%m-%Y'):<{width-10}}|")
        lines.append(f"| User : {city:<{width-10}}|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Item{' ' * 10}Qty Rate{' ' * 5}Total|")
        lines.append("+" + "-" * (width - 2) + "+")
        
        # Get transfer items
        transfer = self.fetch_one("SELECT id FROM stock_transfers WHERE transfer_no = ?", (transfer_no,))
        if transfer:
            items = self.fetch_all("""
                SELECT p.name, ti.quantity, ti.price, ti.total
                FROM transfer_items ti JOIN products p ON ti.product_id = p.id
                WHERE ti.transfer_id = ?
            """, (transfer[0],))
            
            for item in items:
                name = item[0][:12]
                qty = item[1]
                rate = item[2]
                total_amt = item[3]
                lines.append(f"| {name:<12} {qty:>3} {rate:>5.0f} {total_amt:>8.0f}|")
        
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Total               {total_amount:>8.0f} Rs|")
        lines.append(f"| Payment             {payment_status:<8}   |")
        lines.append(f"| Status              {'Completed' if payment_status == 'Paid' else 'Pending'}|")
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("THANK YOU") - 2) // 2) + "THANK YOU" + " " * ((width - len("THANK YOU") - 2) // 2) + "|")
        lines.append("+" + "=" * (width - 2) + "+")
        
        receipt = "\n".join(lines)
        self._direct_print(receipt)
        
        invoices_dir = "invoices"
        if not os.path.exists(invoices_dir):
            os.makedirs(invoices_dir)
        filename = f"{invoices_dir}/transfer_{transfer_no}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt)
    
    def show_transfer_invoice_preview(self, transfer_no, city, recipient, total, transfer_type="", payment_status="", amount_paid=0, balance_due=0):
        """Print transfer invoice - MAXIMUM COMPACT"""
        now = datetime.now()
        
        lines = []
        lines.append("=" * 32)
        lines.append("FAIZAN PAPER MART")
        lines.append("Rail Bazar Sargodha")
        lines.append("=" * 32)
        lines.append(f"TRF:{transfer_no} {now.strftime('%d-%m-%y %H:%M')}")
        lines.append(f"City:{self.shorten_text(city, 24)}")
        lines.append(f"To:{self.shorten_text(recipient, 20)}")
        if transfer_type:
            lines.append(f"Type:{self.shorten_text(transfer_type, 20)}")
        lines.append("-" * 32)
        lines.append(f"{'#':<2}{'ITEM':<16}{'QTY':>4}{'PR':>5}{'TOTAL':>5}")
        lines.append("-" * 32)
        
        serial = 1
        for item in self.transfer_cart:
            name = self.shorten_text(item['name'], 14)
            qty = item['quantity']
            price = item['price']
            total_item = item['total']
            lines.append(f"{serial:<2}{name:<16}{qty:>4}{price:>5.0f}{total_item:>5.0f}")
            serial += 1
        
        lines.append("-" * 32)
        lines.append(f"{'TOTAL':>25}{total:>7.0f}")
        if payment_status:
            lines.append(f"Status:{payment_status}")
            if amount_paid > 0:
                lines.append(f"Paid:{amount_paid:>7.0f}")
            if balance_due > 0:
                lines.append(f"Due:{balance_due:>7.0f}")
        lines.append("=" * 32)
        lines.append("THANK YOU")
        lines.append("=" * 32)
        
        invoice_text = "\n".join(lines)
        self.direct_print(invoice_text)
    def shorten_text(self, text, max_len):
        """Shorten text to fit printer width (32 chars max for 58mm)"""
        if not text:
            return "-"
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text
    def print_purchase_invoice(self, invoice_no, supplier_id, total_amount):
        """Professional Purchase Receipt"""
        now = datetime.now()
        
        supplier = self.fetch_one("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
        supplier_name = supplier[0] if supplier else "Unknown"
        
        lines = []
        width = 36
        
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "FAIZAN PAPER MART" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("Rail Bazar") - 2) // 2) + "Rail Bazar" + " " * ((width - len("Rail Bazar") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("0300-8706085") - 2) // 2) + "0300-8706085" + " " * ((width - len("0300-8706085") - 2) // 2) + "|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Slip : PURCHASE ORDER{' ' * (width - 23)}|")
        lines.append(f"| No   : {invoice_no:<{width-10}}|")
        lines.append(f"| Date : {now.strftime('%d-%m-%Y'):<{width-10}}|")
        lines.append(f"| User : {supplier_name:<{width-10}}|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Item{' ' * 10}Qty Rate{' ' * 5}Total|")
        lines.append("+" + "-" * (width - 2) + "+")
        
        # Get purchase items
        purchase = self.fetch_one("SELECT id FROM purchases WHERE invoice_no = ?", (invoice_no,))
        if purchase:
            items = self.fetch_all("""
                SELECT p.name, pi.quantity, pi.price, pi.total
                FROM purchase_items pi JOIN products p ON pi.product_id = p.id
                WHERE pi.purchase_id = ?
            """, (purchase[0],))
            
            for item in items:
                name = item[0][:12]
                qty = item[1]
                rate = item[2]
                total_amt = item[3]
                lines.append(f"| {name:<12} {qty:>3} {rate:>5.0f} {total_amt:>8.0f}|")
        
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Total               {total_amount:>8.0f} Rs|")
        lines.append(f"| Payment             Credit      |")
        lines.append(f"| Status              Pending     |")
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("THANK YOU") - 2) // 2) + "THANK YOU" + " " * ((width - len("THANK YOU") - 2) // 2) + "|")
        lines.append("+" + "=" * (width - 2) + "+")
        
        receipt = "\n".join(lines)
        self._direct_print(receipt)
        
        invoices_dir = "invoices"
        if not os.path.exists(invoices_dir):
            os.makedirs(invoices_dir)
        filename = f"{invoices_dir}/purchase_{invoice_no}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt)
        
        # ========== SHOP TRANSFER SYSTEM (FRONT SHOP) ==========
    
    def show_shop_transfer(self):
        """Show Shop Transfer interface for front shop stock transfer"""
        self.clear_main_content()
        
        # Create tables if not exists
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create shop_transfers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shop_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_no TEXT UNIQUE NOT NULL,
                    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    shop_name TEXT DEFAULT 'Front Shop',
                    recipient_name TEXT,
                    transfer_type TEXT,
                    total_amount REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Pending',
                    amount_paid REAL DEFAULT 0,
                    balance_due REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create shop_transfer_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shop_transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES shop_transfers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            self.update_status("✅ Shop transfer tables ready")
        except Exception as e:
            self.update_status(f"⚠️ Table check: {str(e)}")
        
        # Main container with two columns
        main_container = tk.Frame(self.main_frame, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#f5f5f5")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text="🏪 Front Shop Stock Transfer", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(side="left")
        tk.Label(header_frame, text="Send stock to your front shop", font=("Arial", 11), bg="#f5f5f5", fg="#666").pack(side="left", padx=20)
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: New Transfer
        new_transfer_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(new_transfer_tab, text="➕ New Shop Transfer")
        self.create_shop_transfer_tab(new_transfer_tab)
        
        # Tab 2: Transfer History
        history_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(history_tab, text="📜 Shop Transfer History")
        self.create_shop_transfer_history_tab(history_tab)
    
    def create_shop_transfer_tab(self, parent):
        """Create New Shop Transfer interface"""
        # Main container with two columns
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Product Selection (60% width)
        left_frame = tk.Frame(main_container, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right side - Transfer Form (35% width, fixed)
        right_frame = tk.Frame(main_container, bg="#f5f5f5", width=380)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # ===== LEFT SIDE =====
        # Search Products
        search_frame = tk.Frame(left_frame, bg="white", relief="ridge", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Search Product:", font=("Arial", 11), bg="white").pack(side="left", padx=10, pady=8)
        self.shop_transfer_search_var = tk.StringVar()
        self.shop_transfer_search_var.trace('w', lambda *args: self.load_shop_transfer_products(self.shop_transfer_search_var.get()))
        tk.Entry(search_frame, textvariable=self.shop_transfer_search_var, font=("Arial", 11), width=30).pack(side="left", padx=10, pady=8)
        
        # Products List
        products_frame = tk.LabelFrame(left_frame, text="📦 Available Stock (Main Warehouse)", font=("Arial", 12, "bold"), bg="#f5f5f5")
        products_frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Product", "Brand", "Stock", "Price")
        self.shop_transfer_products_tree = ttk.Treeview(products_frame, columns=columns, show="headings", height=14)
        
        self.shop_transfer_products_tree.heading("ID", text="ID")
        self.shop_transfer_products_tree.heading("Product", text="Product Name")
        self.shop_transfer_products_tree.heading("Brand", text="Brand")
        self.shop_transfer_products_tree.heading("Stock", text="Available Stock")
        self.shop_transfer_products_tree.heading("Price", text="Price (Rs.)")
        
        self.shop_transfer_products_tree.column("ID", width=50)
        self.shop_transfer_products_tree.column("Product", width=200)
        self.shop_transfer_products_tree.column("Brand", width=100)
        self.shop_transfer_products_tree.column("Stock", width=100)
        self.shop_transfer_products_tree.column("Price", width=100)
        
        vsb = ttk.Scrollbar(products_frame, orient="vertical", command=self.shop_transfer_products_tree.yview)
        self.shop_transfer_products_tree.configure(yscrollcommand=vsb.set)
        
        self.shop_transfer_products_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Transfer Cart
        cart_frame = tk.LabelFrame(left_frame, text="🛒 Shop Transfer Cart", font=("Arial", 12, "bold"), bg="#f5f5f5")
        cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        cart_columns = ("ID", "Product", "Quantity", "Price", "Total")
        self.shop_transfer_cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=6)
        
        self.shop_transfer_cart_tree.heading("ID", text="#")
        self.shop_transfer_cart_tree.heading("Product", text="Product Name")
        self.shop_transfer_cart_tree.heading("Quantity", text="Quantity")
        self.shop_transfer_cart_tree.heading("Price", text="Price (Rs.)")
        self.shop_transfer_cart_tree.heading("Total", text="Total (Rs.)")
        
        self.shop_transfer_cart_tree.column("ID", width=40)
        self.shop_transfer_cart_tree.column("Product", width=200)
        self.shop_transfer_cart_tree.column("Quantity", width=80)
        self.shop_transfer_cart_tree.column("Price", width=100)
        self.shop_transfer_cart_tree.column("Total", width=100)
        
        cart_vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.shop_transfer_cart_tree.yview)
        self.shop_transfer_cart_tree.configure(yscrollcommand=cart_vsb.set)
        self.shop_transfer_cart_tree.pack(side="left", fill="both", expand=True)
        cart_vsb.pack(side="right", fill="y")
        
        # Cart Buttons
        cart_btn_frame = tk.Frame(cart_frame, bg="#f5f5f5")
        cart_btn_frame.pack(fill="x", pady=5)
        tk.Button(cart_btn_frame, text="🗑️ Remove Selected", command=self.remove_from_shop_transfer_cart, bg="#e74a3b", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        tk.Button(cart_btn_frame, text="🔄 Clear Cart", command=self.clear_shop_transfer_cart, bg="#f6c23e", fg="white", font=("Arial", 10), padx=10, pady=5, relief="flat", cursor="hand2").pack(side="right", padx=5)
        
        # Double click to add
        self.shop_transfer_products_tree.bind("<Double-1>", lambda e: self.open_shop_transfer_quantity_dialog())
        
        # ===== RIGHT SIDE - COMPACT FORM (NO SCROLLING NEEDED) =====
        form_frame = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        tk.Label(form_frame, text="🏪 SHOP TRANSFER DETAILS", font=("Arial", 13, "bold"), bg="white", fg="#1a1a2e").pack(pady=8)
        
        # Shop Info (Fixed - Prominent)
        shop_frame = tk.Frame(form_frame, bg="#e8f5e9", relief="ridge", bd=1)
        shop_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(shop_frame, text="🏬 FRONT SHOP", font=("Arial", 11, "bold"), bg="#e8f5e9", fg="#2e7d32").pack(pady=3)
        tk.Label(shop_frame, text="(Same City - Adjacent Shop)", font=("Arial", 8), bg="#e8f5e9", fg="#666").pack()
        
        # Recipient Name
        tk.Label(form_frame, text="Recipient Name:", font=("Arial", 10), bg="white").pack(anchor="w", padx=10, pady=(8, 0))
        self.shop_recipient_name = tk.Entry(form_frame, font=("Arial", 10), width=35)
        self.shop_recipient_name.pack(padx=10, pady=3)
        self.shop_recipient_name.insert(0, "Front Shop Manager")
        
        # Transfer Type
        tk.Label(form_frame, text="Transfer Type:", font=("Arial", 10), bg="white").pack(anchor="w", padx=10, pady=(5, 0))
        self.shop_transfer_type = ttk.Combobox(form_frame, font=("Arial", 10), width=32, state="readonly")
        self.shop_transfer_type['values'] = ['Stock Replenishment', 'Daily Supply', 'Bulk Transfer', 'Consignment']
        self.shop_transfer_type.pack(padx=10, pady=3)
        self.shop_transfer_type.current(0)
        
        # Payment Status
        tk.Label(form_frame, text="Payment Status:", font=("Arial", 10), bg="white").pack(anchor="w", padx=10, pady=(5, 0))
        self.shop_payment_status = ttk.Combobox(form_frame, font=("Arial", 10), width=32, state="readonly")
        self.shop_payment_status['values'] = ['Paid', 'Partial', 'Pending']
        self.shop_payment_status.pack(padx=10, pady=3)
        self.shop_payment_status.current(0)
        self.shop_payment_status.bind('<<ComboboxSelected>>', self.on_shop_payment_status_change)
        
        # Amount Paid Frame
        self.shop_amount_paid_frame = tk.Frame(form_frame, bg="white")
        self.shop_amount_paid_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(self.shop_amount_paid_frame, text="Amount Paid (Rs.):", font=("Arial", 10), bg="white").pack(anchor="w")
        self.shop_amount_paid = tk.Entry(self.shop_amount_paid_frame, font=("Arial", 10), width=35)
        self.shop_amount_paid.pack(pady=3)
        self.shop_amount_paid.insert(0, "0")
        
        # Separator
        tk.Frame(form_frame, height=2, bg="#e94560").pack(fill="x", padx=10, pady=8)
        
        # TOTAL AMOUNT - PROMINENT DISPLAY (ALWAYS VISIBLE)
        total_frame = tk.Frame(form_frame, bg="#f0f0f0", relief="ridge", bd=1)
        total_frame.pack(fill="x", padx=10, pady=8)
        
        tk.Label(total_frame, text="💰 TOTAL AMOUNT:", font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#e94560").pack(side="left", padx=10, pady=8)
        self.shop_transfer_total_label = tk.Label(total_frame, text="Rs. 0.00", font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#e94560")
        self.shop_transfer_total_label.pack(side="right", padx=10, pady=8)
        
        # ===== BUTTONS SECTION (ALL VISIBLE, NO SCROLLING NEEDED) =====
        btn_container = tk.Frame(form_frame, bg="white")
        btn_container.pack(fill="x", padx=10, pady=8)
        
        # Add to Cart Button
        add_btn = tk.Button(btn_container, text="➕ ADD TO CART", command=self.open_shop_transfer_quantity_dialog, 
                            bg="#36b9cc", fg="white", font=("Arial", 10, "bold"), 
                            padx=15, pady=6, relief="flat", cursor="hand2")
        add_btn.pack(fill="x", pady=4)
        
        # Complete Transfer Button (Prominent - Always Visible)
        complete_btn = tk.Button(btn_container, text="✅ COMPLETE SHOP TRANSFER", command=self.complete_shop_transfer, 
                                  bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), 
                                  padx=15, pady=8, relief="flat", cursor="hand2")
        complete_btn.pack(fill="x", pady=6)
        
        # Print Invoice Button (Optional - Current Cart Preview)
        print_btn = tk.Button(btn_container, text="🖨️ PRINT INVOICE (Preview)", command=self.print_shop_transfer_current_invoice, 
                              bg="#e94560", fg="white", font=("Arial", 10, "bold"), 
                              padx=15, pady=6, relief="flat", cursor="hand2")
        print_btn.pack(fill="x", pady=4)
        
        # Initialize cart
        self.shop_transfer_cart = []
        
        # Load products - IMPORTANT: This must be called AFTER all UI is created
        self.load_shop_transfer_products()
    
    def on_shop_payment_status_change(self, event=None):
        """Handle payment status change"""
        if self.shop_payment_status.get() == "Paid":
            self.shop_amount_paid_frame.pack(fill="x", padx=10, pady=5)
            self.shop_amount_paid.delete(0, tk.END)
            self.shop_amount_paid.insert(0, str(self.shop_transfer_total_label.cget("text").replace("Rs. ", "").replace(",", "")))
        elif self.shop_payment_status.get() == "Partial":
            self.shop_amount_paid_frame.pack(fill="x", padx=10, pady=5)
        else:  # Pending
            self.shop_amount_paid_frame.pack_forget()
            self.shop_amount_paid.delete(0, tk.END)
            self.shop_amount_paid.insert(0, "0")
    
    def load_shop_transfer_products(self, search_term=""):
        """Load products for shop transfer"""
        for item in self.shop_transfer_products_tree.get_children():
            self.shop_transfer_products_tree.delete(item)
        
        try:
            if search_term:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE (name LIKE ? OR brand LIKE ?) AND stock_quantity > 0 ORDER BY id DESC"
                params = (f'%{search_term}%', f'%{search_term}%')
            else:
                query = "SELECT id, name, brand, stock_quantity, price FROM products WHERE stock_quantity > 0 ORDER BY id DESC"
                params = ()
            
            products = self.fetch_all(query, params)
            for product in products:
                self.shop_transfer_products_tree.insert("", "end", values=(
                    product[0], product[1], product[2] or "-", product[3], f"Rs. {product[4]:.2f}"
                ))
            self.update_status(f"Loaded {len(products)} products for shop transfer")
        except Exception as e:
            self.update_status(f"Error loading products: {str(e)}")
            # Also show in console for debugging
            print(f"Error in load_shop_transfer_products: {e}")
    
    def open_shop_transfer_quantity_dialog(self):
        """Open dialog to enter quantity for shop transfer with custom price and pack/piece"""
        selected = self.shop_transfer_products_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a product first!")
            return
        
        item = self.shop_transfer_products_tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        available_stock = item['values'][3]
        default_price = float(item['values'][4].replace('Rs. ', ''))
        
        # Get cost price and pack info
        product_info = self.fetch_one("SELECT cost_price, unit_type, pieces_per_pack, pack_price FROM products WHERE id = ?", (product_id,))
        cost_price = product_info[0] if product_info else 0
        unit_type = product_info[1] if product_info else "Piece"
        pieces_per_pack = product_info[2] if product_info else 1
        pack_price = product_info[3] if product_info else 0
        
        if available_stock <= 0:
            messagebox.showwarning("Out of Stock", f"{product_name} is out of stock!")
            return
        
        # Main dialog with both scrollbars
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Shop Transfer Quantity - {product_name}")
        dialog.geometry("600x700")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"Product: {product_name}", font=("Arial", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Main frame with both scrollbars
        main_frame = tk.Frame(dialog, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_frame, bg="#f5f5f5", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        def on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        
        content = tk.Frame(scrollable_frame, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stock info
        info_frame = tk.Frame(content, bg="#f5f5f5")
        info_frame.pack(fill="x", pady=5)
        tk.Label(info_frame, text=f"Available Stock: {available_stock} pieces", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack()
        tk.Label(info_frame, text=f"Cost Price: Rs. {cost_price:.2f} per piece", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        if unit_type == "Pack" and pack_price > 0:
            tk.Label(info_frame, text=f"Pack Price: Rs. {pack_price:.2f} per pack ({pieces_per_pack} pieces)", font=("Arial", 10), bg="#f5f5f5", fg="#666").pack()
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Price Options
        price_frame = tk.LabelFrame(content, text="Price Options", font=("Arial", 12, "bold"), bg="#f5f5f5")
        price_frame.pack(fill="x", pady=10)
        
        price_inner = tk.Frame(price_frame, bg="#f5f5f5")
        price_inner.pack(padx=15, pady=10)
        
        self.shop_price_option = tk.StringVar(value="default")
        
        default_radio = tk.Radiobutton(price_inner, text=f"Default Price: Rs. {default_price:.2f} per piece", 
                                        variable=self.shop_price_option, value="default", bg="#f5f5f5", font=("Arial", 10))
        default_radio.pack(anchor="w", pady=3)
        
        custom_radio = tk.Radiobutton(price_inner, text="Custom Price:", 
                                      variable=self.shop_price_option, value="custom", bg="#f5f5f5", font=("Arial", 10))
        custom_radio.pack(anchor="w", pady=3)
        
        custom_frame = tk.Frame(price_inner, bg="#f5f5f5")
        custom_frame.pack(anchor="w", padx=20)
        tk.Label(custom_frame, text="Rs.", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.shop_custom_price_entry = tk.Entry(custom_frame, font=("Arial", 11), width=12)
        self.shop_custom_price_entry.pack(side="left", padx=5)
        self.shop_custom_price_entry.insert(0, str(default_price))
        self.shop_custom_price_entry.config(state="disabled")
        
        # Loss warning
        self.shop_loss_warning = tk.Label(price_inner, text="", font=("Arial", 9), bg="#f5f5f5", fg="#e74a3b")
        self.shop_loss_warning.pack(anchor="w", pady=5)
        
        # Separator
        tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
        
        # Purchase Type Selection (if pack available)
        if unit_type == "Pack" and pack_price > 0:
            type_frame = tk.LabelFrame(content, text="Transfer Type", font=("Arial", 11, "bold"), bg="#f5f5f5")
            type_frame.pack(fill="x", pady=10)
            
            type_inner = tk.Frame(type_frame, bg="#f5f5f5")
            type_inner.pack(padx=15, pady=10)
            
            self.shop_buy_type = tk.StringVar(value="Pack")
            
            piece_radio = tk.Radiobutton(type_inner, text=f"Transfer by Piece (Rs. {default_price:.2f} each)", 
                                          variable=self.shop_buy_type, value="Piece", bg="#f5f5f5", font=("Arial", 10))
            piece_radio.pack(anchor="w", pady=5)
            
            pack_radio = tk.Radiobutton(type_inner, text=f"Transfer by Pack (Rs. {pack_price:.2f} per pack - {pieces_per_pack} pieces)", 
                                          variable=self.shop_buy_type, value="Pack", bg="#f5f5f5", font=("Arial", 10))
            pack_radio.pack(anchor="w", pady=5)
            
            # Separator
            tk.Frame(content, height=2, bg="#ddd").pack(fill="x", pady=10)
            
            # Quantity Frame
            qty_main_frame = tk.LabelFrame(content, text="Quantity", font=("Arial", 11, "bold"), bg="#f5f5f5")
            qty_main_frame.pack(fill="x", pady=10)
            
            qty_inner = tk.Frame(qty_main_frame, bg="#f5f5f5")
            qty_inner.pack(padx=15, pady=10)
            
            # Piece mode
            piece_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(piece_qty_frame, text="Number of Pieces:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.shop_piece_qty = tk.Entry(piece_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.shop_piece_qty.pack(side="left", padx=10)
            self.shop_piece_qty.insert(0, "1")
            
            # Pack mode
            pack_qty_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            tk.Label(pack_qty_frame, text="Number of Packs:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
            self.shop_pack_qty = tk.Entry(pack_qty_frame, font=("Arial", 12), width=10, justify="center")
            self.shop_pack_qty.pack(side="left", padx=10)
            self.shop_pack_qty.insert(0, "1")
            
            tk.Label(pack_qty_frame, text=f"(= {pieces_per_pack} pieces each)", font=("Arial", 9), bg="#f5f5f5", fg="#666").pack(side="left", padx=5)
            
            # Extra pieces
            extra_frame = tk.Frame(pack_qty_frame, bg="#f5f5f5")
            extra_frame.pack(pady=5)
            tk.Label(extra_frame, text="Extra Pieces:", font=("Arial", 10), bg="#f5f5f5").pack(side="left")
            self.shop_extra_pieces = tk.Entry(extra_frame, font=("Arial", 11), width=8, justify="center")
            self.shop_extra_pieces.pack(side="left", padx=10)
            self.shop_extra_pieces.insert(0, "0")
            
            # Initially show pack mode (DEFAULT)
            piece_qty_frame.pack_forget()
            pack_qty_frame.pack()
            
            # Total pieces display
            total_frame = tk.Frame(qty_inner, bg="#f5f5f5")
            total_frame.pack(pady=10)
            tk.Label(total_frame, text="Total Pieces:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
            self.shop_total_pieces = tk.Label(total_frame, text="1", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
            self.shop_total_pieces.pack(side="left", padx=10)
            
            # Total preview
            preview_frame = tk.Frame(content, bg="#f0f0f0", relief="ridge", bd=1)
            preview_frame.pack(fill="x", pady=10)
            
            tk.Label(preview_frame, text="💰 TOTAL AMOUNT:", font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#e94560").pack(side="left", padx=15, pady=10)
            self.shop_preview_total = tk.Label(preview_frame, text="Rs. 0.00", font=("Arial", 13, "bold"), bg="#f0f0f0", fg="#e94560")
            self.shop_preview_total.pack(side="right", padx=15, pady=10)
            
            # Profit/Loss preview
            self.shop_pl_label = tk.Label(content, text="", font=("Arial", 10), bg="#f5f5f5")
            self.shop_pl_label.pack(pady=5)
            
            def update_shop_total(*args):
                try:
                    if self.shop_buy_type.get() == "Piece":
                        qty = int(self.shop_piece_qty.get() or 0)
                        self.shop_total_pieces.config(text=str(qty))
                    else:
                        packs = int(self.shop_pack_qty.get() or 0)
                        extra = int(self.shop_extra_pieces.get() or 0)
                        qty = (packs * pieces_per_pack) + extra
                        self.shop_total_pieces.config(text=str(qty))
                    update_shop_preview()
                except:
                    self.shop_total_pieces.config(text="0")
                    update_shop_preview()
            
            def update_shop_preview(*args):
                try:
                    if self.shop_buy_type.get() == "Piece":
                        qty = int(self.shop_piece_qty.get() or 0)
                    else:
                        packs = int(self.shop_pack_qty.get() or 0)
                        extra = int(self.shop_extra_pieces.get() or 0)
                        qty = (packs * pieces_per_pack) + extra
                    
                    if self.shop_price_option.get() == "custom":
                        try:
                            price_per_piece = float(self.shop_custom_price_entry.get())
                        except:
                            price_per_piece = default_price
                    else:
                        price_per_piece = default_price
                    
                    total = qty * price_per_piece
                    
                    if self.shop_buy_type.get() == "Pack" and qty > 0:
                        packs = qty // pieces_per_pack
                        remaining = qty % pieces_per_pack
                        self.shop_preview_total.config(text=f"Rs. {total:,.2f} ({packs} pack + {remaining} pcs)")
                    else:
                        self.shop_preview_total.config(text=f"Rs. {total:,.2f}")
                    
                    if qty > 0:
                        if price_per_piece < cost_price:
                            loss_amount = (cost_price - price_per_piece) * qty
                            self.shop_pl_label.config(text=f"⚠️ LOSS: Rs. {loss_amount:,.2f}", fg="#e74a3b")
                        else:
                            profit_amount = (price_per_piece - cost_price) * qty
                            self.shop_pl_label.config(text=f"✓ PROFIT: Rs. {profit_amount:,.2f}", fg="#1cc88a")
                    else:
                        self.shop_pl_label.config(text="")
                except:
                    self.shop_preview_total.config(text="Rs. 0.00")
            
            def check_shop_loss():
                try:
                    if self.shop_price_option.get() == "custom":
                        custom_price = float(self.shop_custom_price_entry.get())
                        if custom_price < cost_price:
                            loss_amount = cost_price - custom_price
                            self.shop_loss_warning.config(text=f"⚠️ Loss of Rs. {loss_amount:.2f} per piece!", fg="#e74a3b")
                        else:
                            self.shop_loss_warning.config(text="")
                    else:
                        self.shop_loss_warning.config(text="")
                except:
                    self.shop_loss_warning.config(text="")
            
            def on_shop_buy_type_change(*args):
                if self.shop_buy_type.get() == "Piece":
                    piece_qty_frame.pack()
                    pack_qty_frame.pack_forget()
                    self.shop_piece_qty.delete(0, tk.END)
                    self.shop_piece_qty.insert(0, "1")
                else:
                    piece_qty_frame.pack_forget()
                    pack_qty_frame.pack()
                    self.shop_pack_qty.delete(0, tk.END)
                    self.shop_pack_qty.insert(0, "1")
                    self.shop_extra_pieces.delete(0, tk.END)
                    self.shop_extra_pieces.insert(0, "0")
                update_shop_total()
            
            def on_shop_price_change(*args):
                if self.shop_price_option.get() == "custom":
                    self.shop_custom_price_entry.config(state="normal")
                    self.shop_custom_price_entry.focus()
                    check_shop_loss()
                else:
                    self.shop_custom_price_entry.config(state="disabled")
                    self.shop_custom_price_entry.delete(0, tk.END)
                    self.shop_custom_price_entry.insert(0, str(default_price))
                    self.shop_loss_warning.config(text="")
                update_shop_preview()
            
            self.shop_buy_type.trace('w', on_shop_buy_type_change)
            self.shop_price_option.trace('w', on_shop_price_change)
            self.shop_piece_qty.bind("<KeyRelease>", update_shop_total)
            self.shop_pack_qty.bind("<KeyRelease>", update_shop_total)
            self.shop_extra_pieces.bind("<KeyRelease>", update_shop_total)
            self.shop_custom_price_entry.bind("<KeyRelease>", lambda e: [check_shop_loss(), update_shop_preview()])
            
            def add_to_shop_cart():
                try:
                    if self.shop_buy_type.get() == "Piece":
                        quantity = int(self.shop_piece_qty.get() or 0)
                    else:
                        packs = int(self.shop_pack_qty.get() or 0)
                        extra = int(self.shop_extra_pieces.get() or 0)
                        quantity = (packs * pieces_per_pack) + extra
                    
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    if quantity > available_stock:
                        messagebox.showwarning("Insufficient Stock", f"Only {available_stock} units available!")
                        return
                    
                    if self.shop_price_option.get() == "custom":
                        try:
                            final_price = float(self.shop_custom_price_entry.get())
                            if final_price <= 0:
                                messagebox.showwarning("Invalid Price", "Price must be greater than 0!")
                                return
                        except:
                            messagebox.showwarning("Invalid Price", "Please enter a valid price!")
                            return
                        
                        if final_price < cost_price:
                            loss_amount = (cost_price - final_price) * quantity
                            confirm = messagebox.askyesno(
                                "⚠️ LOSS WARNING ⚠️",
                                f"Product: {product_name}\n"
                                f"Cost Price: Rs. {cost_price:.2f}\n"
                                f"Transfer Price: Rs. {final_price:.2f}\n"
                                f"Quantity: {quantity} pieces\n\n"
                                f"This will result in a LOSS of Rs. {loss_amount:,.2f}!",
                                icon='warning'
                            )
                            if not confirm:
                                return
                    else:
                        final_price = default_price
                    
                    total = quantity * final_price
                    
                    if self.shop_buy_type.get() == "Pack":
                        packs_sold = int(self.shop_pack_qty.get() or 0)
                        extra_sold = int(self.shop_extra_pieces.get() or 0)
                        sale_note = f" ({packs_sold} pack + {extra_sold} pcs)"
                    else:
                        sale_note = ""
                    
                    cart_item = {
                        'product_id': product_id,
                        'name': product_name + sale_note,
                        'quantity': quantity,
                        'price': final_price,
                        'original_price': default_price,
                        'total': total,
                        'is_custom_price': self.shop_price_option.get() == "custom",
                        'cost_price': cost_price
                    }
                    self.shop_transfer_cart.append(cart_item)
                    self.update_shop_transfer_cart_display()
                    self.update_shop_transfer_total()
                    dialog.destroy()
                    
                    if cart_item['is_custom_price']:
                        if final_price < cost_price:
                            self.update_status(f"⚠️ Added {quantity} x {product_name} at LOSS")
                        else:
                            self.update_status(f"Added {quantity} x {product_name} at custom price")
                    else:
                        self.update_status(f"Added {quantity} x {product_name} to shop transfer cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=15)
            tk.Button(btn_frame, text="Add to Cart", command=add_to_shop_cart, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=25, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            update_shop_total()
        
        else:
            # Simple dialog for products without pack
            tk.Label(content, text="Quantity:", font=("Arial", 11), bg="#f5f5f5").pack(pady=(10, 5))
            quantity_entry = tk.Entry(content, font=("Arial", 12), width=15, justify="center")
            quantity_entry.pack()
            quantity_entry.focus()
            
            preview_frame = tk.Frame(content, bg="#f5f5f5")
            preview_frame.pack(pady=10)
            tk.Label(preview_frame, text="Total Amount:", font=("Arial", 11, "bold"), bg="#f5f5f5", fg="#e94560").pack(side="left")
            simple_preview = tk.Label(preview_frame, text="Rs. 0.00", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#e94560")
            simple_preview.pack(side="left", padx=10)
            
            def update_simple(event=None):
                try:
                    qty = int(quantity_entry.get() or 0)
                    if self.shop_price_option.get() == "custom":
                        try:
                            price = float(self.shop_custom_price_entry.get())
                        except:
                            price = default_price
                    else:
                        price = default_price
                    total = qty * price
                    simple_preview.config(text=f"Rs. {total:,.2f}")
                except:
                    simple_preview.config(text="Rs. 0.00")
            
            quantity_entry.bind("<KeyRelease>", update_simple)
            
            def add_simple():
                try:
                    quantity = int(quantity_entry.get())
                    if quantity <= 0:
                        messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0!")
                        return
                    if quantity > available_stock:
                        messagebox.showwarning("Insufficient Stock", f"Only {available_stock} units available!")
                        return
                    
                    if self.shop_price_option.get() == "custom":
                        try:
                            final_price = float(self.shop_custom_price_entry.get())
                            if final_price <= 0:
                                messagebox.showwarning("Invalid Price", "Price must be greater than 0!")
                                return
                        except:
                            messagebox.showwarning("Invalid Price", "Please enter a valid price!")
                            return
                        
                        if final_price < cost_price:
                            loss_amount = (cost_price - final_price) * quantity
                            confirm = messagebox.askyesno(
                                "⚠️ LOSS WARNING ⚠️",
                                f"Product: {product_name}\n"
                                f"Cost Price: Rs. {cost_price:.2f}\n"
                                f"Your Price: Rs. {final_price:.2f}\n"
                                f"Quantity: {quantity}\n\n"
                                f"This will result in a LOSS of Rs. {loss_amount:,.2f}!",
                                icon='warning'
                            )
                            if not confirm:
                                return
                    else:
                        final_price = default_price
                    
                    total = quantity * final_price
                    cart_item = {
                        'product_id': product_id,
                        'name': product_name,
                        'quantity': quantity,
                        'price': final_price,
                        'original_price': default_price,
                        'total': total,
                        'is_custom_price': self.shop_price_option.get() == "custom",
                        'cost_price': cost_price
                    }
                    self.shop_transfer_cart.append(cart_item)
                    self.update_shop_transfer_cart_display()
                    self.update_shop_transfer_total()
                    dialog.destroy()
                    
                    if cart_item['is_custom_price']:
                        if final_price < cost_price:
                            self.update_status(f"⚠️ Added {quantity} x {product_name} at LOSS")
                        else:
                            self.update_status(f"Added {quantity} x {product_name} at custom price")
                    else:
                        self.update_status(f"Added {quantity} x {product_name} to shop transfer cart")
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter a valid number!")
            
            btn_frame = tk.Frame(content, bg="#f5f5f5")
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="Add to Cart", command=add_simple, bg="#1cc88a", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg="#e74a3b", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat", cursor="hand2").pack(side="left", padx=10)
            
            update_simple()
    
    def update_shop_transfer_cart_display(self):
        """Update shop transfer cart display"""
        for item in self.shop_transfer_cart_tree.get_children():
            self.shop_transfer_cart_tree.delete(item)
        
        for i, item in enumerate(self.shop_transfer_cart, 1):
            price_display = f"Rs. {item['price']:.2f}"
            if item.get('is_custom_price'):
                if item.get('price') < item.get('cost_price', 0):
                    price_display = f"⚠️ Rs. {item['price']:.2f}"
                else:
                    price_display = f"*Rs. {item['price']:.2f}"
            
            self.shop_transfer_cart_tree.insert("", "end", values=(
                i,
                item['name'],
                item['quantity'],
                price_display,
                f"Rs. {item['total']:.2f}"
            ))
    
    def update_shop_transfer_total(self):
        """Update shop transfer total display"""
        total = sum(item['total'] for item in self.shop_transfer_cart)
        self.shop_transfer_total_label.config(text=f"Rs. {total:,.2f}")
    
    def remove_from_shop_transfer_cart(self):
        """Remove item from shop transfer cart"""
        selected = self.shop_transfer_cart_tree.selection()
        if not selected:
            return
        item = self.shop_transfer_cart_tree.item(selected[0])
        index = int(item['values'][0]) - 1
        if 0 <= index < len(self.shop_transfer_cart):
            removed = self.shop_transfer_cart.pop(index)
            self.update_shop_transfer_cart_display()
            self.update_shop_transfer_total()
            self.update_status(f"Removed {removed['name']} from cart")
    
    def clear_shop_transfer_cart(self):
        """Clear shop transfer cart"""
        if self.shop_transfer_cart and messagebox.askyesno("Clear Cart", "Clear entire shop transfer cart?"):
            self.shop_transfer_cart.clear()
            self.update_shop_transfer_cart_display()
            self.update_shop_transfer_total()
            self.update_status("Shop transfer cart cleared")
    
    def complete_shop_transfer(self):
        """Complete the shop stock transfer"""
        if not self.shop_transfer_cart:
            messagebox.showwarning("Empty Cart", "Please add items to transfer!")
            return
        
        recipient = self.shop_recipient_name.get().strip() or "Front Shop Manager"
        transfer_type = self.shop_transfer_type.get()
        total_amount = sum(item['total'] for item in self.shop_transfer_cart)
        
        # Payment info
        payment_status = self.shop_payment_status.get()
        amount_paid = float(self.shop_amount_paid.get() or 0) if payment_status in ["Paid", "Partial"] else 0
        balance_due = total_amount - amount_paid if payment_status == "Partial" else (0 if payment_status == "Paid" else total_amount)
        
        # Generate transfer invoice number
        last_transfer = self.fetch_one("SELECT transfer_no FROM shop_transfers ORDER BY id DESC LIMIT 1")
        if last_transfer and last_transfer[0]:
            try:
                num = int(last_transfer[0].split('-')[-1]) + 1
            except:
                num = 1
            transfer_no = f"SHP-{datetime.now().year}-{num:03d}"
        else:
            transfer_no = f"SHP-{datetime.now().year}-001"
        
        confirm = messagebox.askyesno(
            "Confirm Shop Transfer",
            f"Transfer No: {transfer_no}\n"
            f"Shop: Front Shop\n"
            f"Recipient: {recipient}\n"
            f"Type: {transfer_type}\n"
            f"Items: {len(self.shop_transfer_cart)}\n"
            f"Total: Rs. {total_amount:,.2f}\n"
            f"Payment: {payment_status}\n"
            f"Amount Paid: Rs. {amount_paid:,.2f}\n"
            f"Balance Due: Rs. {balance_due:,.2f}\n\n"
            f"Proceed with shop transfer?"
        )
        
        if not confirm:
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert transfer record (NO notes field)
            cursor.execute("""
                INSERT INTO shop_transfers 
                (transfer_no, shop_name, recipient_name, transfer_type, total_amount, payment_status, amount_paid, balance_due)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (transfer_no, "Front Shop", recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due))
            
            transfer_id = cursor.lastrowid
            
            # Insert transfer items and update stock
            for item in self.shop_transfer_cart:
                cursor.execute("""
                    INSERT INTO shop_transfer_items (transfer_id, product_id, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (transfer_id, item['product_id'], item['quantity'], item['price'], item['total']))
                
                # REDUCE stock from main warehouse
                cursor.execute("""
                    UPDATE products SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (item['quantity'], item['product_id']))
            
            # Add to ledger
            if payment_status == "Paid":
                cursor.execute("""
                    INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, ("SHOP_TRANSFER", transfer_no, f"Stock transfer to Front Shop - {recipient} (Paid)", 0, total_amount))
            elif payment_status == "Partial":
                cursor.execute("""
                    INSERT INTO ledger (transaction_type, reference_no, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, ("SHOP_TRANSFER", transfer_no, f"Stock transfer to Front Shop - {recipient} (Partial: Rs.{amount_paid:,.0f} paid)", 0, amount_paid))
            # Pending: No ledger entry until payment received
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Shop transfer completed!\nTransfer No: {transfer_no}\nTotal: Rs. {total_amount:,.2f}")
            
            # Print invoice
            self.print_shop_transfer_invoice(transfer_no, recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due)
            
            # Reset form
            self.shop_transfer_cart.clear()
            self.update_shop_transfer_cart_display()
            self.update_shop_transfer_total()
            self.shop_recipient_name.delete(0, tk.END)
            self.shop_recipient_name.insert(0, "Front Shop Manager")
            self.shop_amount_paid.delete(0, tk.END)
            self.shop_amount_paid.insert(0, "0")
            self.shop_transfer_type.current(0)
            self.shop_payment_status.current(0)
            self.load_shop_transfer_products()
            self.load_shop_transfer_history()
            
            self.update_status(f"✅ Shop transfer completed: {transfer_no}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete shop transfer: {str(e)}")
    
    def print_shop_transfer_invoice(self, transfer_no, recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due):
        """Professional Shop Transfer Receipt"""
        now = datetime.now()
        
        lines = []
        width = 36
        
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "FAIZAN PAPER MART" + " " * ((width - len("FAIZAN PAPER MART") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("Rail Bazar") - 2) // 2) + "Rail Bazar" + " " * ((width - len("Rail Bazar") - 2) // 2) + "|")
        lines.append("|" + " " * ((width - len("0300-8706085") - 2) // 2) + "0300-8706085" + " " * ((width - len("0300-8706085") - 2) // 2) + "|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Slip : SHOP TRANSFER{' ' * (width - 24)}|")
        lines.append(f"| No   : {transfer_no:<{width-10}}|")
        lines.append(f"| Date : {now.strftime('%d-%m-%Y'):<{width-10}}|")
        lines.append(f"| User : {recipient:<{width-10}}|")
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Item{' ' * 10}Qty Rate{' ' * 5}Total|")
        lines.append("+" + "-" * (width - 2) + "+")
        
        # Get shop transfer items
        transfer = self.fetch_one("SELECT id FROM shop_transfers WHERE transfer_no = ?", (transfer_no,))
        if transfer:
            items = self.fetch_all("""
                SELECT p.name, sti.quantity, sti.price, sti.total
                FROM shop_transfer_items sti JOIN products p ON sti.product_id = p.id
                WHERE sti.transfer_id = ?
            """, (transfer[0],))
            
            for item in items:
                name = item[0][:12]
                qty = item[1]
                rate = item[2]
                total_amt = item[3]
                lines.append(f"| {name:<12} {qty:>3} {rate:>5.0f} {total_amt:>8.0f}|")
        
        lines.append("+" + "-" * (width - 2) + "+")
        lines.append(f"| Total               {total_amount:>8.0f} Rs|")
        lines.append(f"| Payment             {payment_status:<8}   |")
        lines.append(f"| Status              {'Completed' if payment_status == 'Paid' else 'Pending'}|")
        lines.append("+" + "=" * (width - 2) + "+")
        lines.append("|" + " " * ((width - len("THANK YOU") - 2) // 2) + "THANK YOU" + " " * ((width - len("THANK YOU") - 2) // 2) + "|")
        lines.append("+" + "=" * (width - 2) + "+")
        
        receipt = "\n".join(lines)
        self._direct_print(receipt)
        
        invoices_dir = "invoices"
        if not os.path.exists(invoices_dir):
            os.makedirs(invoices_dir)
        filename = f"{invoices_dir}/shop_transfer_{transfer_no}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(receipt)
    
    def create_shop_transfer_history_tab(self, parent):
        """Create Shop Transfer History tab"""
        main_container = tk.Frame(parent, bg="#f5f5f5")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(main_container, text="📜 Front Shop Transfer History", font=("Helvetica", 16, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        # Filter Frame
        filter_frame = tk.Frame(main_container, bg="white", relief="ridge", bd=1)
        filter_frame.pack(fill="x", pady=10)
        
        filter_inner = tk.Frame(filter_frame, bg="white")
        filter_inner.pack(padx=10, pady=10)
        
        tk.Label(filter_inner, text="From:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.shop_history_date_from = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.shop_history_date_from.pack(side="left", padx=5)
        self.shop_history_date_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(filter_inner, text="To:", font=("Arial", 10), bg="white").pack(side="left", padx=5)
        self.shop_history_date_to = tk.Entry(filter_inner, font=("Arial", 10), width=10)
        self.shop_history_date_to.pack(side="left", padx=5)
        self.shop_history_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(filter_inner, text="🔍 Filter", command=self.load_shop_transfer_history, bg="#36b9cc", fg="white", font=("Arial", 9, "bold"), padx=10, pady=3, relief="flat").pack(side="left", padx=10)
        
        # Treeview
        tree_frame = tk.Frame(main_container, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Transfer No", "Date", "Recipient", "Type", "Total", "Payment", "Balance")
        self.shop_transfer_history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.shop_transfer_history_tree.heading("Transfer No", text="Transfer No")
        self.shop_transfer_history_tree.heading("Date", text="Date")
        self.shop_transfer_history_tree.heading("Recipient", text="Recipient")
        self.shop_transfer_history_tree.heading("Type", text="Type")
        self.shop_transfer_history_tree.heading("Total", text="Total (Rs.)")
        self.shop_transfer_history_tree.heading("Payment", text="Payment")
        self.shop_transfer_history_tree.heading("Balance", text="Balance Due")
        
        self.shop_transfer_history_tree.column("Transfer No", width=120)
        self.shop_transfer_history_tree.column("Date", width=100)
        self.shop_transfer_history_tree.column("Recipient", width=150)
        self.shop_transfer_history_tree.column("Type", width=120)
        self.shop_transfer_history_tree.column("Total", width=100)
        self.shop_transfer_history_tree.column("Payment", width=80)
        self.shop_transfer_history_tree.column("Balance", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.shop_transfer_history_tree.yview)
        self.shop_transfer_history_tree.configure(yscrollcommand=vsb.set)
        self.shop_transfer_history_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Double click to view details
        self.shop_transfer_history_tree.bind("<Double-1>", lambda e: self.view_shop_transfer_details())
        
        self.load_shop_transfer_history()
    
    def load_shop_transfer_history(self):
        """Load shop transfer history with filters"""
        for item in self.shop_transfer_history_tree.get_children():
            self.shop_transfer_history_tree.delete(item)
        
        try:
            query = "SELECT * FROM shop_transfers WHERE 1=1"
            params = []
            
            date_from = self.shop_history_date_from.get()
            date_to = self.shop_history_date_to.get()
            if date_from:
                query += " AND DATE(transfer_date) >= ?"
                params.append(date_from)
            if date_to:
                query += " AND DATE(transfer_date) <= ?"
                params.append(date_to)
            
            query += " ORDER BY transfer_date DESC"
            
            transfers = self.fetch_all(query, params)
            
            for transfer in transfers:
                self.shop_transfer_history_tree.insert("", "end", values=(
                    transfer[1], transfer[2][:10] if transfer[2] else "-",
                    transfer[4] or "-", transfer[5] or "-",
                    f"Rs. {transfer[6]:,.2f}", transfer[7] or "-",
                    f"Rs. {transfer[9]:,.2f}" if transfer[9] > 0 else "Paid"
                ))
            
            self.update_status(f"Loaded {len(transfers)} shop transfer records")
        except Exception as e:
            self.update_status(f"Error loading shop transfers: {str(e)}")
    
    def view_shop_transfer_details(self):
        """View shop transfer details"""
        selected = self.shop_transfer_history_tree.selection()
        if not selected:
            return
        
        item = self.shop_transfer_history_tree.item(selected[0])
        transfer_no = item['values'][0]
        
        transfer = self.fetch_one("SELECT * FROM shop_transfers WHERE transfer_no = ?", (transfer_no,))
        if not transfer:
            return
        
        items = self.fetch_all("""
            SELECT sti.*, p.name 
            FROM shop_transfer_items sti
            JOIN products p ON sti.product_id = p.id
            WHERE sti.transfer_id = ?
        """, (transfer[0],))
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Shop Transfer Details - {transfer_no}")
        dialog.geometry("700x500")
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()
        
        tk.Label(dialog, text=f"🏪 Shop Transfer Details: {transfer_no}", font=("Helvetica", 14, "bold"), bg="#f5f5f5", fg="#1a1a2e").pack(pady=10)
        
        info_frame = tk.Frame(dialog, bg="white", relief="ridge", bd=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = f"""
        Date: {transfer[2][:19] if transfer[2] else '-'}
        Shop: Front Shop
        Recipient: {transfer[4] or '-'}
        Transfer Type: {transfer[5] or '-'}
        Payment Status: {transfer[7] or '-'}
        Amount Paid: Rs. {transfer[8]:,.2f}
        Balance Due: Rs. {transfer[9]:,.2f}
        Total Amount: Rs. {transfer[6]:,.2f}
        """
        tk.Label(info_frame, text=info_text, font=("Arial", 10), bg="white", justify="left").pack(padx=20, pady=10)
        
        items_frame = tk.Frame(dialog, bg="#f5f5f5")
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(items_frame, text="Transferred Items:", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor="w")
        
        tree_frame = tk.Frame(items_frame, bg="#f5f5f5")
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("Product", "Quantity", "Price", "Total")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        tree.heading("Product", text="Product")
        tree.heading("Quantity", text="Quantity")
        tree.heading("Price", text="Price (Rs.)")
        tree.heading("Total", text="Total (Rs.)")
        
        tree.column("Product", width=300)
        tree.column("Quantity", width=80)
        tree.column("Price", width=100)
        tree.column("Total", width=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for item in items:
            tree.insert("", "end", values=(item[5], item[2], f"Rs. {item[3]:,.2f}", f"Rs. {item[4]:,.2f}"))
        
        tk.Button(dialog, text="Close", command=dialog.destroy, bg="#e94560", fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, relief="flat").pack(pady=10)
    def show_insight_center(self):
        """Show Insight Center in main content area (not popup)"""
        
        # Clear main content
        self.clear_main_content()
        
        # Main container
        main_container = tk.Frame(self.main_frame, bg="#f8fafc")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#1e293b", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📊 INSIGHT CENTER", 
                font=("Segoe UI", 18, "bold"), bg="#1e293b", fg="#e94560").pack(pady=15)
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Tab 1: Best Selling Products
        tab1 = tk.Frame(notebook, bg="#f8fafc")
        notebook.add(tab1, text="🏆 Best Sellers")
        self.create_best_sellers_tab(tab1)
        
        # Tab 2: Peak Hours
        tab2 = tk.Frame(notebook, bg="#f8fafc")
        notebook.add(tab2, text="⏰ Peak Hours")
        self.create_peak_hours_tab(tab2)
        
        # Tab 3: Busiest Days
        tab3 = tk.Frame(notebook, bg="#f8fafc")
        notebook.add(tab3, text="📅 Busiest Days")
        self.create_busiest_days_tab(tab3)
        
        # Tab 4: Digital Notepad
        tab4 = tk.Frame(notebook, bg="#f8fafc")
        notebook.add(tab4, text="📝 Notepad")
        self.create_notepad_tab(tab4)
    def create_best_sellers_tab(self, parent):
        """Tab 1: Best Selling Products with Date Range"""
        
        # Main container
        container = tk.Frame(parent, bg="#f8fafc")
        container.pack(fill="both", expand=True)
        
        # Filter Frame (ye destroy nahi hoga)
        filter_frame = tk.Frame(container, bg="#f8fafc")
        filter_frame.pack(fill="x", padx=15, pady=5)
        
        # Date from
        tk.Label(filter_frame, text="From:", font=("Segoe UI", 9), bg="#f8fafc").pack(side="left", padx=2)
        self.bs_date_from = tk.Entry(filter_frame, font=("Segoe UI", 9), width=12)
        self.bs_date_from.pack(side="left", padx=2)
        self.bs_date_from.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        # Date to
        tk.Label(filter_frame, text="To:", font=("Segoe UI", 9), bg="#f8fafc").pack(side="left", padx=2)
        self.bs_date_to = tk.Entry(filter_frame, font=("Segoe UI", 9), width=12)
        self.bs_date_to.pack(side="left", padx=2)
        self.bs_date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Refresh button
        refresh_btn = tk.Button(filter_frame, text="🔄 Refresh", 
                                command=self.refresh_best_sellers_wrapper,
                                bg="#3b82f6", fg="white", font=("Arial", 9, "bold"),
                                padx=10, pady=3, relief="flat", cursor="hand2")
        refresh_btn.pack(side="left", padx=10)
        
        # Display frame (ye refresh hota rahega)
        self.best_sellers_display_frame = tk.Frame(container, bg="#f8fafc")
        self.best_sellers_display_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initial load
        self.refresh_best_sellers_data()
    
    def refresh_best_sellers_wrapper(self):
        """Wrapper for refresh - only updates display frame"""
        self.refresh_best_sellers_data()
    
    def refresh_best_sellers_data(self):
        """Refresh only the data display, not the whole tab"""
        
        # Clear only the display frame
        for widget in self.best_sellers_display_frame.winfo_children():
            widget.destroy()
        
        # Get date range
        date_from = self.bs_date_from.get().strip()
        date_to = self.bs_date_to.get().strip()
        
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Get top products from sales
        top_products = self.fetch_all("""
            SELECT p.name, SUM(si.quantity) as total_sold, SUM(si.total) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY si.product_id
            ORDER BY total_sold DESC
            LIMIT 10
        """, (date_from, date_to))
        
        # City transfers
        city_products = self.fetch_all("""
            SELECT p.name, SUM(ti.quantity) as total_sold, SUM(ti.total) as total_revenue
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN stock_transfers st ON ti.transfer_id = st.id
            WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
            GROUP BY ti.product_id
        """, (date_from, date_to))
        
        # NO SHOP TRANSFERS QUERY
        
        # Combine
        all_products = {}
        
        for p in top_products:
            all_products[p[0]] = {'sold': p[1], 'revenue': p[2]}
        
        for p in city_products:
            if p[0] in all_products:
                all_products[p[0]]['sold'] += p[1]
                all_products[p[0]]['revenue'] += p[2]
            else:
                all_products[p[0]] = {'sold': p[1], 'revenue': p[2]}
        
        # NO SHOP PRODUCTS LOOP
        
        # Sort
        sorted_products = sorted(all_products.items(), key=lambda x: x[1]['sold'], reverse=True)[:10]
        
        # No data case
        if not sorted_products:
            msg_label = tk.Label(self.best_sellers_display_frame, 
                text="📭 No sales/transfers in selected date range\n\n💡 Try changing the date range",
                font=("Segoe UI", 12), bg="#f8fafc", fg="#94a3b8", justify="center")
            msg_label.pack(expand=True, pady=50)
            return
        
        # Header
        header_frame = tk.Frame(self.best_sellers_display_frame, bg="#f8fafc")
        header_frame.pack(fill="x", pady=5)
        
        tk.Label(header_frame, text=f"📅 {date_from} to {date_to}", 
                font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b").pack()
        
        # Display products
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "📦", "📦", "📦", "📦", "📦"]
        
        for i, (name, data) in enumerate(sorted_products):
            card = tk.Frame(self.best_sellers_display_frame, bg="white", relief="ridge", bd=1)
            card.pack(fill="x", pady=5, padx=10)
            card.configure(highlightbackground="#e2e8f0", highlightthickness=1)
            
            medal = medals[i] if i < len(medals) else "📦"
            
            tk.Label(card, text=f"{medal} {name}", 
                    font=("Segoe UI", 11, "bold"), bg="white", fg="#1e293b").pack(side="left", padx=15, pady=12)
            
            tk.Label(card, text=f"Sold: {data['sold']} units", 
                    font=("Segoe UI", 10), bg="white", fg="#64748b").pack(side="left", padx=15)
            
            tk.Label(card, text=f"Rs. {data['revenue']:,.0f}", 
                    font=("Segoe UI", 10, "bold"), bg="white", fg="#10b981").pack(side="right", padx=15)
        
        # Summary
        total_sold = sum(data['sold'] for name, data in sorted_products)
        total_revenue = sum(data['revenue'] for name, data in sorted_products)
        
        summary_frame = tk.Frame(self.best_sellers_display_frame, bg="#f1f5f9", relief="flat")
        summary_frame.pack(fill="x", pady=10, padx=10)
        
        tk.Label(summary_frame, text=f"📊 Total: {total_sold} units | Rs. {total_revenue:,.0f}", 
                font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#1e293b", pady=8).pack()
    
    def refresh_best_sellers(self, parent):
        """Refresh best sellers data with date range"""
        
        # Clear previous widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get date range
        date_from = self.bs_date_from.get().strip()
        date_to = self.bs_date_to.get().strip()
        
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Get top products from sales with date range
        top_products = self.fetch_all("""
            SELECT p.name, SUM(si.quantity) as total_sold, SUM(si.total) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY si.product_id
            ORDER BY total_sold DESC
            LIMIT 10
        """, (date_from, date_to))
        
        # Also get from city transfers
        city_products = self.fetch_all("""
            SELECT p.name, SUM(ti.quantity) as total_sold, SUM(ti.total) as total_revenue
            FROM transfer_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN stock_transfers st ON ti.transfer_id = st.id
            WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
            GROUP BY ti.product_id
        """, (date_from, date_to))
        
        # Also get from shop transfers
        shop_products = self.fetch_all("""
            SELECT p.name, SUM(sti.quantity) as total_sold, SUM(sti.total) as total_revenue
            FROM shop_transfer_items sti
            JOIN products p ON sti.product_id = p.id
            JOIN shop_transfers st ON sti.transfer_id = st.id
            WHERE DATE(st.transfer_date) BETWEEN ? AND ? AND st.payment_status = 'Paid'
            GROUP BY sti.product_id
        """, (date_from, date_to))
        
        # Combine all products
        all_products = {}
        
        for p in top_products:
            all_products[p[0]] = {'sold': p[1], 'revenue': p[2]}
        
        for p in city_products:
            if p[0] in all_products:
                all_products[p[0]]['sold'] += p[1]
                all_products[p[0]]['revenue'] += p[2]
            else:
                all_products[p[0]] = {'sold': p[1], 'revenue': p[2]}
        
        for p in shop_products:
            if p[0] in all_products:
                all_products[p[0]]['sold'] += p[1]
                all_products[p[0]]['revenue'] += p[2]
            else:
                all_products[p[0]] = {'sold': p[1], 'revenue': p[2]}
        
        # Sort and get top 10
        sorted_products = sorted(all_products.items(), key=lambda x: x[1]['sold'], reverse=True)[:10]
        
        # ===== NO DATA CASE =====
        if not sorted_products:
            msg_label = tk.Label(parent, 
                text="📭 No sales/transfers in selected date range\n\n💡 Tip: Try changing the date range",
                font=("Segoe UI", 12), bg="#f8fafc", fg="#94a3b8", justify="center")
            msg_label.pack(expand=True, pady=50)
            return
        
        # ===== DATA EXISTS - SHOW RESULTS =====
        # Header with date range
        header_frame = tk.Frame(parent, bg="#f8fafc")
        header_frame.pack(fill="x", pady=5)
        
        tk.Label(header_frame, text=f"📅 {date_from} to {date_to}", 
                font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b").pack()
        
        # Display with visual
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "📦", "📦", "📦", "📦", "📦"]
        
        for i, (name, data) in enumerate(sorted_products):
            card = tk.Frame(parent, bg="white", relief="ridge", bd=1)
            card.pack(fill="x", pady=5, padx=10)
            
            card.configure(highlightbackground="#e2e8f0", highlightthickness=1)
            
            medal = medals[i] if i < len(medals) else "📦"
            
            tk.Label(card, text=f"{medal} {name}", 
                    font=("Segoe UI", 11, "bold"), bg="white", fg="#1e293b").pack(side="left", padx=15, pady=12)
            
            tk.Label(card, text=f"Sold: {data['sold']} units", 
                    font=("Segoe UI", 10), bg="white", fg="#64748b").pack(side="left", padx=15)
            
            tk.Label(card, text=f"Rs. {data['revenue']:,.0f}", 
                    font=("Segoe UI", 10, "bold"), bg="white", fg="#10b981").pack(side="right", padx=15)
        
        # Total summary
        total_sold = sum(data['sold'] for name, data in sorted_products)
        total_revenue = sum(data['revenue'] for name, data in sorted_products)
        
        summary_frame = tk.Frame(parent, bg="#f1f5f9", relief="flat")
        summary_frame.pack(fill="x", pady=10, padx=10)
        
        tk.Label(summary_frame, text=f"📊 Total: {total_sold} units | Rs. {total_revenue:,.0f}", 
                font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#1e293b", pady=8).pack()
    def create_peak_hours_tab(self, parent):
        """Tab 2: Peak Hour Sales"""
        
        # Main container
        container = tk.Frame(parent, bg="#f8fafc")
        container.pack(fill="both", expand=True)
        
        # Filter Frame
        filter_frame = tk.Frame(container, bg="#f8fafc")
        filter_frame.pack(fill="x", padx=15, pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(filter_frame, text="🔄 Refresh", 
                                command=self.refresh_peak_hours_wrapper,
                                bg="#3b82f6", fg="white", font=("Arial", 9, "bold"),
                                padx=10, pady=3, relief="flat", cursor="hand2")
        refresh_btn.pack(side="left", padx=10)
        
        # Display frame
        self.peak_hours_display_frame = tk.Frame(container, bg="#f8fafc")
        self.peak_hours_display_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initial load
        self.refresh_peak_hours_data()
    
    def refresh_peak_hours_wrapper(self):
        """Wrapper for refresh - only updates display frame"""
        self.refresh_peak_hours_data()
    
    def refresh_peak_hours_data(self):
        """Refresh peak hours data"""
        
        # Clear only the display frame
        for widget in self.peak_hours_display_frame.winfo_children():
            widget.destroy()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get sales by hour
        hours_data = []
        for hour in range(9, 21):  # 9 AM to 9 PM
            sales = self.fetch_one("""
                SELECT COALESCE(COUNT(*), 0), COALESCE(SUM(total_amount), 0)
                FROM sales
                WHERE DATE(sale_date) = ? 
                AND strftime('%H', sale_date) = ?
            """, (today, f"{hour:02d}"))
            
            count = sales[0] if sales else 0
            amount = sales[1] if sales else 0
            hours_data.append((hour, count, amount))
        
        # Find best hour
        best_hour = max(hours_data, key=lambda x: x[1])
        
        # Display as bars
        max_count = max([h[1] for h in hours_data]) or 1
        
        for hour, count, amount in hours_data:
            if count == 0:
                continue
                
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            
            hour_str = f"{hour}:00"
            time_label = f"{hour_str} {'AM' if hour < 12 else 'PM'}"
            
            row = tk.Frame(self.peak_hours_display_frame, bg="#f8fafc")
            row.pack(fill="x", pady=3)
            
            tk.Label(row, text=f"{time_label:>8}", font=("Courier", 10), 
                    bg="#f8fafc", fg="#475569", width=10, anchor="w").pack(side="left")
            
            tk.Label(row, text=bar, font=("Courier", 9), 
                    bg="#f8fafc", fg="#3b82f6").pack(side="left", padx=5)
            
            tk.Label(row, text=f"{count} sales", font=("Courier", 9), 
                    bg="#f8fafc", fg="#64748b", width=10).pack(side="left", padx=5)
            
            tk.Label(row, text=f"Rs.{amount:,.0f}", font=("Courier", 9, "bold"), 
                    bg="#f8fafc", fg="#10b981").pack(side="right", padx=5)
        
        # Best time insight
        if hours_data:
            best_time = f"{best_hour[0]}:00 {'AM' if best_hour[0] < 12 else 'PM'}"
            insight_frame = tk.Frame(self.peak_hours_display_frame, bg="#fef3c7", relief="flat")
            insight_frame.pack(fill="x", pady=15, padx=10)
            tk.Label(insight_frame, text=f"💡 Best Time: {best_time} ({best_hour[1]} sales)", 
                    font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#92400e", pady=8).pack()
    
    def refresh_peak_hours(self, parent):
        """Refresh peak hours data"""
        for widget in parent.winfo_children():
            widget.destroy()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get sales by hour
        hours_data = []
        for hour in range(9, 21):  # 9 AM to 9 PM
            hour_start = f"{hour:02d}:00"
            hour_end = f"{hour:02d}:59"
            
            sales = self.fetch_one("""
                SELECT COALESCE(COUNT(*), 0), COALESCE(SUM(total_amount), 0)
                FROM sales
                WHERE DATE(sale_date) = ? 
                AND strftime('%H', sale_date) = ?
            """, (today, f"{hour:02d}"))
            
            count = sales[0] if sales else 0
            amount = sales[1] if sales else 0
            hours_data.append((hour, count, amount))
        
        # Find best hour
        best_hour = max(hours_data, key=lambda x: x[1])
        
        # Display as bars
        max_count = max([h[1] for h in hours_data]) or 1
        
        for hour, count, amount in hours_data:
            if count == 0:
                continue
                
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            
            hour_str = f"{hour}:00"
            time_label = f"{hour_str} {'AM' if hour < 12 else 'PM'}"
            
            row = tk.Frame(parent, bg="#f8fafc")
            row.pack(fill="x", pady=3)
            
            tk.Label(row, text=f"{time_label:>8}", font=("Courier", 10), 
                    bg="#f8fafc", fg="#475569", width=10, anchor="w").pack(side="left")
            
            tk.Label(row, text=bar, font=("Courier", 9), 
                    bg="#f8fafc", fg="#3b82f6").pack(side="left", padx=5)
            
            tk.Label(row, text=f"{count} sales", font=("Courier", 9), 
                    bg="#f8fafc", fg="#64748b", width=10).pack(side="left", padx=5)
            
            tk.Label(row, text=f"Rs.{amount:,.0f}", font=("Courier", 9, "bold"), 
                    bg="#f8fafc", fg="#10b981").pack(side="right", padx=5)
        
        # Best time insight
        insight_frame = tk.Frame(parent, bg="#fef3c7", relief="flat")
        insight_frame.pack(fill="x", pady=15, padx=10)
        
        best_time = f"{best_hour[0]}:00 {'AM' if best_hour[0] < 12 else 'PM'}"
        tk.Label(insight_frame, text=f"💡 Best Time: {best_time} ({best_hour[1]} sales)", 
                font=("Segoe UI", 10, "bold"), bg="#fef3c7", fg="#92400e", pady=8).pack() 
    def create_busiest_days_tab(self, parent):
        """Tab 3: Busiest Days of the Week"""
        
        # Main container
        container = tk.Frame(parent, bg="#f8fafc")
        container.pack(fill="both", expand=True)
        
        # Filter Frame
        filter_frame = tk.Frame(container, bg="#f8fafc")
        filter_frame.pack(fill="x", padx=15, pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(filter_frame, text="🔄 Refresh", 
                                command=self.refresh_busiest_days_wrapper,
                                bg="#3b82f6", fg="white", font=("Arial", 9, "bold"),
                                padx=10, pady=3, relief="flat", cursor="hand2")
        refresh_btn.pack(side="left", padx=10)
        
        # Display frame
        self.busiest_days_display_frame = tk.Frame(container, bg="#f8fafc")
        self.busiest_days_display_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initial load
        self.refresh_busiest_days_data()
    
    def refresh_busiest_days_wrapper(self):
        """Wrapper for refresh - only updates display frame"""
        self.refresh_busiest_days_data()
    
    def refresh_busiest_days_data(self):
        """Refresh busiest days data"""
        
        # Clear only the display frame
        for widget in self.busiest_days_display_frame.winfo_children():
            widget.destroy()
        
        # Get this week's data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_data = []
        
        for i, day in enumerate(days):
            today = datetime.now()
            days_ahead = i - today.weekday()
            target_date = today + timedelta(days=days_ahead)
            date_str = target_date.strftime("%Y-%m-%d")
            
            sales = self.fetch_one("""
                SELECT COALESCE(SUM(total_amount), 0), COALESCE(COUNT(*), 0)
                FROM sales
                WHERE DATE(sale_date) = ?
            """, (date_str,))
            
            amount = sales[0] if sales else 0
            count = sales[1] if sales else 0
            day_data.append((day, count, amount, date_str))
        
        max_count = max([d[1] for d in day_data]) or 1
        
        # Find best day
        best_day = max(day_data, key=lambda x: x[1])
        
        for day, count, amount, date in day_data:
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            
            row = tk.Frame(self.busiest_days_display_frame, bg="#f8fafc")
            row.pack(fill="x", pady=4)
            
            day_color = "#e94560" if day == best_day[0] else "#1e293b"
            day_font = ("Segoe UI", 10, "bold") if day == best_day[0] else ("Segoe UI", 10)
            
            tk.Label(row, text=day, font=day_font, bg="#f8fafc", fg=day_color, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=bar, font=("Courier", 9), bg="#f8fafc", fg="#8b5cf6").pack(side="left", padx=5)
            tk.Label(row, text=f"{count} sales", font=("Courier", 9), bg="#f8fafc", fg="#64748b", width=10).pack(side="left", padx=5)
            tk.Label(row, text=f"Rs.{amount:,.0f}", font=("Courier", 9, "bold"), bg="#f8fafc", fg="#10b981").pack(side="right", padx=5)
        
        # Insight
        if day_data:
            insight_frame = tk.Frame(self.busiest_days_display_frame, bg="#dcfce7", relief="flat")
            insight_frame.pack(fill="x", pady=15, padx=10)
            tk.Label(insight_frame, text=f"🏆 Busiest Day: {best_day[0]} ({best_day[1]} sales)", 
                    font=("Segoe UI", 10, "bold"), bg="#dcfce7", fg="#166534", pady=8).pack()
    
    def refresh_busiest_days(self, parent):
        """Refresh busiest days data"""
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get this week's data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_data = []
        
        for i, day in enumerate(days):
            # Calculate date for this day this week
            today = datetime.now()
            days_ahead = i - today.weekday()
            target_date = today + timedelta(days=days_ahead)
            date_str = target_date.strftime("%Y-%m-%d")
            
            sales = self.fetch_one("""
                SELECT COALESCE(SUM(total_amount), 0), COALESCE(COUNT(*), 0)
                FROM sales
                WHERE DATE(sale_date) = ?
            """, (date_str,))
            
            amount = sales[0] if sales else 0
            count = sales[1] if sales else 0
            day_data.append((day, count, amount, date_str))
        
        max_count = max([d[1] for d in day_data]) or 1
        
        # Find best day
        best_day = max(day_data, key=lambda x: x[1])
        
        for day, count, amount, date in day_data:
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            
            row = tk.Frame(parent, bg="#f8fafc")
            row.pack(fill="x", pady=4)
            
            # Day name with highlight if best
            day_color = "#e94560" if day == best_day[0] else "#1e293b"
            day_font = ("Segoe UI", 10, "bold") if day == best_day[0] else ("Segoe UI", 10)
            
            tk.Label(row, text=day, font=day_font, bg="#f8fafc", fg=day_color, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=bar, font=("Courier", 9), bg="#f8fafc", fg="#8b5cf6").pack(side="left", padx=5)
            tk.Label(row, text=f"{count} sales", font=("Courier", 9), bg="#f8fafc", fg="#64748b", width=10).pack(side="left", padx=5)
            tk.Label(row, text=f"Rs.{amount:,.0f}", font=("Courier", 9, "bold"), bg="#f8fafc", fg="#10b981").pack(side="right", padx=5)
        
        # Insight
        insight_frame = tk.Frame(parent, bg="#dcfce7", relief="flat")
        insight_frame.pack(fill="x", pady=15, padx=10)
        
        tk.Label(insight_frame, text=f"🏆 Busiest Day: {best_day[0]} ({best_day[1]} sales)", 
                font=("Segoe UI", 10, "bold"), bg="#dcfce7", fg="#166534", pady=8).pack()
    def create_notepad_tab(self, parent):
        """Tab 4: Digital Notepad - Right side list with right-click menu"""
        
        # Main frame with two columns
        main_frame = tk.Frame(parent, bg="#f8fafc")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # LEFT SIDE - Editor
        left_frame = tk.Frame(main_frame, bg="#f8fafc", width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Title entry
        tk.Label(left_frame, text="Title:", font=("Segoe UI", 10, "bold"), 
                bg="#f8fafc", fg="#1e293b").pack(anchor="w")
        
        self.note_title = tk.Entry(left_frame, font=("Segoe UI", 11), width=45)
        self.note_title.pack(fill="x", pady=(5, 10))
        
        # Text area
        tk.Label(left_frame, text="Content:", font=("Segoe UI", 10, "bold"), 
                bg="#f8fafc", fg="#1e293b").pack(anchor="w")
        
        self.note_text = tk.Text(left_frame, font=("Segoe UI", 10), wrap="word",
                                  bg="white", fg="#1e293b", height=18, padx=10, pady=10)
        self.note_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Save button (only button left)
        save_btn = tk.Button(left_frame, text="💾 SAVE NOTE", command=self.save_note_final,
                            bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                            padx=20, pady=6, relief="flat", cursor="hand2")
        save_btn.pack(pady=5)
        
        # RIGHT SIDE - Notes List
        right_frame = tk.Frame(main_frame, bg="#f8fafc", width=280)
        right_frame.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_frame, text="📋 SAVED NOTES", font=("Segoe UI", 10, "bold"), 
                bg="#f8fafc", fg="#1e293b").pack(anchor="w")
        
        # Listbox with scrollbar
        list_container = tk.Frame(right_frame, bg="white", relief="ridge", bd=1)
        list_container.pack(fill="both", expand=True, pady=(5, 0))
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.notes_listbox = tk.Listbox(list_container, font=("Segoe UI", 10), 
                                         bg="white", fg="#1e293b", 
                                         selectbackground="#e94560",
                                         yscrollcommand=scrollbar.set)
        self.notes_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.notes_listbox.yview)
        
        # Bind right-click menu
        self.notes_listbox.bind("<Button-3>", self.show_note_context_menu)
        
        # Create notes directory in AppData (hidden from user folder)
        import sys
        if getattr(sys, 'frozen', False):
            self.notes_dir = os.path.join(os.path.expanduser("~"), "FaizanPaperMart", "notes")
        else:
            self.notes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes")
        
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
        
        # Store note paths
        self.note_paths = {}
        
        # Refresh list
        self.refresh_notes_list_final()
    
    def show_note_context_menu(self, event):
        """Show right-click context menu for notes"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="👁️ VIEW NOTE", command=self.view_selected_note_final)
        menu.add_separator()
        menu.add_command(label="🗑️ DELETE NOTE", command=self.delete_selected_note_final)
        menu.post(event.x_root, event.y_root)
    
    def save_note_final(self):
        """Save note with title (stores in app folder)"""
        title = self.note_title.get().strip()
        content = self.note_text.get("1.0", "end-1c").strip()
        
        if not title:
            messagebox.showwarning("Warning", "Please enter a title!")
            return
        
        if not content:
            messagebox.showwarning("Warning", "Please enter some content!")
            return
        
        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.txt"
        filepath = os.path.join(self.notes_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            f.write(content)
        
        messagebox.showinfo("Success", "Note saved successfully!")
        self.note_title.delete(0, tk.END)
        self.note_text.delete("1.0", tk.END)
        self.refresh_notes_list_final()
    
    def refresh_notes_list_final(self):
        """Refresh the notes listbox"""
        self.notes_listbox.delete(0, tk.END)
        self.note_paths.clear()
        
        if os.path.exists(self.notes_dir):
            notes = [f for f in os.listdir(self.notes_dir) if f.endswith('.txt')]
            notes.sort(reverse=True)
            for note in notes:
                # Extract title from filename
                display_name = note.replace('.txt', '')
                # Remove timestamp from display name
                if '_' in display_name:
                    parts = display_name.split('_')
                    if len(parts) > 1 and parts[-1].isdigit():
                        display_name = ' '.join(parts[:-1])
                
                self.notes_listbox.insert(tk.END, display_name)
                self.note_paths[display_name] = os.path.join(self.notes_dir, note)
    
    def view_selected_note_final(self):
        """View selected note in the editor"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        display_name = self.notes_listbox.get(selection[0])
        filepath = self.note_paths.get(display_name)
        
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Error", "Note file not found!")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse content
            lines = content.split('\n')
            if len(lines) > 3:
                # Extract title
                title_line = lines[0].replace("Title: ", "")
                self.note_title.delete(0, tk.END)
                self.note_title.insert(0, title_line)
                
                # Extract content (skip first 3 lines)
                note_content = '\n'.join(lines[3:])
                self.note_text.delete("1.0", tk.END)
                self.note_text.insert("1.0", note_content)
                
                self.update_status(f"📝 Loaded note: {title_line}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load note: {str(e)}")
    
    def delete_selected_note_final(self):
        """Delete selected note and clear editor if open"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        display_name = self.notes_listbox.get(selection[0])
        filepath = self.note_paths.get(display_name)
        
        if not filepath:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete note '{display_name}'?"):
            os.remove(filepath)
            
            # Check if this was the currently loaded note
            current_title = self.note_title.get().strip()
            if current_title == display_name:
                # Clear the editor
                self.note_title.delete(0, tk.END)
                self.note_text.delete("1.0", tk.END)
            
            self.refresh_notes_list_final()
            messagebox.showinfo("Success", "Note deleted!")
    
    def save_note(self):
        """Save current note to file"""
        title = self.note_title.get().strip()
        content = self.note_text.get("1.0", "end-1c").strip()
        
        if not title:
            messagebox.showwarning("Warning", "Please enter a title!")
            return
        
        if not content:
            messagebox.showwarning("Warning", "Please enter some content!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.notes_dir}/{title}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            f.write(content)
        
        messagebox.showinfo("Success", "Note saved successfully!")
        self.refresh_notes_list()
        self.note_title.delete(0, tk.END)
        self.note_text.delete("1.0", tk.END)
    
    def delete_note(self):
        """Delete selected note"""
        selection = self.notes_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a note to delete!")
            return
        
        file_path = self.notes_listbox.get(selection[0])
        full_path = f"{self.notes_dir}/{file_path}"
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{file_path}'?"):
            os.remove(full_path)
            self.refresh_notes_list()
            messagebox.showinfo("Success", "Note deleted!")
    
    def load_selected_note(self, event):
        """Load selected note content"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        file_path = self.notes_listbox.get(selection[0])
        full_path = f"{self.notes_dir}/{file_path}"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse title and content
            lines = content.split('\n')
            if len(lines) > 3:
                # Extract title
                title_line = lines[0].replace("Title: ", "")
                self.note_title.delete(0, tk.END)
                self.note_title.insert(0, title_line)
                
                # Extract content (skip first 3 lines)
                note_content = '\n'.join(lines[3:])
                self.note_text.delete("1.0", tk.END)
                self.note_text.insert("1.0", note_content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load note: {str(e)}")
    
    def copy_note_to_clipboard(self):
        """Copy note content to clipboard"""
        content = self.note_text.get("1.0", "end-1c").strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Copied", "Note copied to clipboard!")
    
    def refresh_notes_list(self):
        """Refresh the notes listbox"""
        self.notes_listbox.delete(0, tk.END)
        
        if os.path.exists(self.notes_dir):
            notes = [f for f in os.listdir(self.notes_dir) if f.endswith('.txt')]
            notes.sort(reverse=True)
            for note in notes:
                self.notes_listbox.insert(tk.END, note)
    def force_refresh_dashboard(self):
        """Force refresh dashboard with a small delay to ensure database is updated"""
        try:
            self.root.update_idletasks()
            if hasattr(self, 'current_menu') and self.current_menu == "Dashboard":
                self.show_dashboard()
            else:
                self.update_status("✅ Data saved successfully")
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
    def force_refresh_dashboard(self):
        """Force refresh dashboard"""
        try:
            self.root.update_idletasks()
            if hasattr(self, 'current_menu') and self.current_menu == "Dashboard":
                self.show_dashboard()
            else:
                self.update_status("✅ Data saved successfully")
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
    def refresh_dashboard_after_add(self):
        """Force dashboard refresh immediately"""
        try:
            # Directly call show_dashboard without any condition
            self.root.after(100, self.force_dashboard_refresh)
        except Exception as e:
            print(f"Refresh error: {e}")
    
    def force_dashboard_refresh(self):
        """Force dashboard refresh immediately"""
        try:
            if hasattr(self, 'current_menu') and self.current_menu == "Dashboard":
                self.clear_main_content()
                self.show_dashboard()
            else:
                self.update_status("✅ Product added successfully")
        except Exception as e:
            print(f"Refresh error: {e}")
    def print_shop_transfer_current_invoice(self):
        """Print invoice for current cart without completing transfer"""
        if not hasattr(self, 'shop_transfer_cart') or not self.shop_transfer_cart:
            messagebox.showwarning("No Items", "Please add items to cart first!")
            return
        
        recipient = self.shop_recipient_name.get().strip() or "Front Shop Manager"
        transfer_type = self.shop_transfer_type.get()
        total_amount = sum(item['total'] for item in self.shop_transfer_cart)
        payment_status = self.shop_payment_status.get()
        amount_paid = float(self.shop_amount_paid.get() or 0) if payment_status in ["Paid", "Partial"] else 0
        balance_due = total_amount - amount_paid if payment_status == "Partial" else (0 if payment_status == "Paid" else total_amount)
        
        self.print_shop_transfer_invoice("PREVIEW", recipient, transfer_type, total_amount, payment_status, amount_paid, balance_due)
if __name__ == "__main__":
    root = tk.Tk()
    app = StationeryShopSystem(root)
    root.mainloop()