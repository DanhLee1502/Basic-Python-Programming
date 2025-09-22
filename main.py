import sys
import sqlite3
import os # Cần cho việc kiểm tra sự tồn tại của file database

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QTableView, QDialogButtonBox, QWidget, QHeaderView, QSpacerItem,
    QSizePolicy # Cần cho QSpacerItem
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.uic import loadUi # Hàm để load file .ui

# --- Cấu hình Database ---
DATABASE_NAME = "cosmetics.db"

def create_connection():
    """ Tạo kết nối đến cơ sở dữ liệu SQLite """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_tables():
    """ Tạo các bảng cần thiết nếu chưa tồn tại """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    brand TEXT,
                    category TEXT,
                    price REAL NOT NULL,
                    sku TEXT UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE,
                    address TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    customer_id INTEGER,
                    total_amount REAL NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            conn.commit()
            print("Tables created or already exist.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()
    else:
        print("Could not create database connection.")

def add_initial_data():
    """ Thêm dữ liệu sản phẩm ban đầu và tồn kho """
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            initial_products = [
                ("Kem chống nắng A", "Brand X", "Chăm sóc da", 250000, "SKU001"),
                ("Son lì màu đỏ B", "Brand Y", "Trang điểm", 180000, "SKU002"),
                ("Sữa rửa mặt C", "Brand Z", "Chăm sóc da", 150000, "SKU003"),
                ("Kem dưỡng ẩm D", "Brand X", "Chăm sóc da", 300000, "SKU004"),
                ("Phấn nước E", "Brand Y", "Trang điểm", 450000, "SKU005"),
                ("Tẩy trang F", "Brand Z", "Chăm sóc da", 200000, "SKU006"),
                ("Mascara G", "Brand Y", "Trang điểm", 220000, "SKU007"),
                ("Serum H", "Brand X", "Chăm sóc da", 500000, "SKU008"),
                ("Chì kẻ mày I", "Brand Y", "Trang điểm", 100000, "SKU009"),
                ("Mặt nạ J", "Brand Z", "Chăm sóc da", 50000, "SKU010")
            ]

            # Kiểm tra và thêm sản phẩm/tồn kho chỉ nếu SKU chưa tồn tại
            for name, brand, category, price, sku in initial_products:
                cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
                existing_product = cursor.fetchone()
                if existing_product is None:
                    cursor.execute("INSERT INTO products (name, brand, category, price, sku) VALUES (?, ?, ?, ?, ?)",
                                   (name, brand, category, price, sku))
                    product_id = cursor.lastrowid
                    # Thêm vào bảng inventory với số lượng 100
                    cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)", (product_id, 100))
                else:
                     # Tùy chọn: có thể in thông báo hoặc bỏ qua
                     print(f"Product with SKU {sku} already exists. Skipping initial data for this SKU.")


            conn.commit()
            print("Initial data added.")
        except sqlite3.Error as e:
            print(f"Error adding initial data: {e}")
            conn.rollback()
        finally:
            conn.close()
    else:
        print("Could not create database connection.")

# --- Data Management ---

class DataManager:
    def get_all_products(self):
        """ Lấy tất cả sản phẩm từ CSDL cùng với số lượng tồn kho """
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Sử dụng LEFT JOIN để vẫn hiển thị sản phẩm dù không có trong inventory (trạng thái lạ)
                # hoặc INNER JOIN nếu chỉ muốn SP có tồn kho. INNER JOIN phổ biến hơn cho quản lý tồn kho.
                cursor.execute("""
                    SELECT p.id, p.name, p.brand, p.category, p.price, p.sku, inv.quantity
                    FROM products p
                    JOIN inventory inv ON p.id = inv.product_id
                """)
                rows = cursor.fetchall()
                return rows
            except sqlite3.Error as e:
                print(f"Error fetching products: {e}")
                return []
            finally:
                conn.close()
        return []

    def add_product(self, name, brand, category, price, sku, initial_quantity):
        """ Thêm sản phẩm mới và cập nhật tồn kho ban đầu """
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Bắt đầu transaction
                conn.execute("BEGIN")

                # Thêm sản phẩm
                cursor.execute("INSERT INTO products (name, brand, category, price, sku) VALUES (?, ?, ?, ?, ?)",
                               (name, brand, category, price, sku))
                product_id = cursor.lastrowid

                # Thêm vào inventory
                cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)",
                               (product_id, initial_quantity))

                conn.commit() # Commit transaction nếu thành công
                print(f"Product '{name}' added successfully.")
                return True
            except sqlite3.IntegrityError:
                print(f"Error: Product with SKU '{sku}' already exists.")
                conn.rollback() # Rollback nếu có lỗi
                return False
            except sqlite3.Error as e:
                print(f"Error adding product: {e}")
                conn.rollback() # Rollback nếu có lỗi
                return False
            finally:
                conn.close()
        return False

    def update_product(self, product_id, name, brand, category, price, sku):
         """ Cập nhật thông tin sản phẩm (không bao gồm tồn kho) """
         conn = create_connection()
         if conn:
             try:
                 cursor = conn.cursor()
                 cursor.execute("""
                    UPDATE products
                    SET name = ?, brand = ?, category = ?, price = ?, sku = ?
                    WHERE id = ?
                 """, (name, brand, category, price, sku, product_id))
                 conn.commit()
                 print(f"Product ID {product_id} updated.")
                 return True
             except sqlite3.IntegrityError:
                 print(f"Error: SKU '{sku}' already exists for another product.")
                 return False
             except sqlite3.Error as e:
                 print(f"Error updating product: {e}")
                 conn.rollback()
                 return False
             finally:
                 conn.close()
         return False

    def delete_product(self, product_id):
        """ Xóa sản phẩm và tồn kho liên quan """
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                 # Bắt đầu transaction
                conn.execute("BEGIN")

                # TODO: Cần kiểm tra xem sản phẩm có trong sale_items không
                # Nếu có, có thể không cho xóa hoặc đánh dấu là không hoạt động

                # Xóa trong inventory trước (để tránh lỗi khóa ngoại nếu có)
                cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
                # Xóa trong products
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

                conn.commit() # Commit transaction nếu thành công
                print(f"Product ID {product_id} deleted.")
                return True
            except sqlite3.Error as e:
                print(f"Error deleting product: {e}")
                conn.rollback() # Rollback nếu có lỗi
                return False
            finally:
                conn.close()
        return False

    def update_inventory(self, product_id, quantity_change):
        """ Cập nhật số lượng tồn kho của sản phẩm (thêm/bớt) """
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?",
                               (quantity_change, product_id))
                conn.commit()
                print(f"Inventory updated for product ID {product_id}.")
                return True
            except sqlite3.Error as e:
                print(f"Error updating inventory: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    # TODO: Add methods for Customers, Sales, Reports

# --- UI Logic for Product Dialog ---

class ProductDialog(QDialog):
    def __init__(self, product_data=None):
        """
        Khởi tạo ProductDialog bằng cách load UI từ file .ui.
        product_data: List/Tuple chứa dữ liệu sản phẩm nếu đang ở chế độ Sửa.
        """
        super().__init__()
        # Load UI từ file .ui
        # Đảm bảo file 'ui/product_dialog.ui' tồn tại
        try:
             loadUi("ui/product_dialog.ui", self)
        except FileNotFoundError:
             QMessageBox.critical(self, "Lỗi UI", "Không tìm thấy file ui/product_dialog.ui. Vui lòng kiểm tra lại đường dẫn.")
             self.close() # Đóng dialog nếu không load được UI
             return

        self.product_data = product_data
        self.is_edit_mode = product_data is not None

        self.setWindowTitle("Thêm Sản phẩm Mới" if not self.is_edit_mode else "Sửa Thông tin Sản phẩm")

        # Load data if in edit mode
        if self.is_edit_mode:
            self._load_product_data()
            # Disable SKU field in edit mode to prevent changing unique key
            self.lineEditSku.setEnabled(False)
            # Disable Quantity field in edit mode - stock should be managed via stock adjustments
            self.lineEditQuantity.setEnabled(False)


        # Connect signals (Assuming object names from .ui file)
        # QDialogButtonBox standard signals are 'accepted' and 'rejected'
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def _load_product_data(self):
        """ Load existing product data into the form fields """
        # product_data format from DataManager.get_all_products:
        # (id, name, brand, category, price, sku, quantity)
        if self.product_data and len(self.product_data) >= 7:
            self.lineEditName.setText(str(self.product_data[1])) # name
            self.lineEditBrand.setText(str(self.product_data[2])) # brand
            self.lineEditCategory.setText(str(self.product_data[3])) # category
            self.lineEditPrice.setText(str(self.product_data[4])) # price
            self.lineEditSku.setText(str(self.product_data[5])) # sku
            self.lineEditQuantity.setText(str(self.product_data[6])) # quantity


    def get_product_data(self):
        """ Get data from the form fields after validation """
        try:
            name = self.lineEditName.text().strip()
            brand = self.lineEditBrand.text().strip()
            category = self.lineEditCategory.text().strip()
            price_str = self.lineEditPrice.text().strip()
            sku = self.lineEditSku.text().strip()
            quantity_str = self.lineEditQuantity.text().strip()

            if not name or not price_str or not sku:
                 QMessageBox.warning(self, "Lỗi nhập liệu", "Tên sản phẩm, Giá và Mã SKU không được để trống.")
                 return None # Return None to indicate validation failure

            price = float(price_str)

            # Quantity is only required and used for adding new product initially
            if not self.is_edit_mode:
                 if not quantity_str:
                      QMessageBox.warning(self, "Lỗi nhập liệu", "Số lượng tồn kho ban đầu không được để trống khi thêm sản phẩm.")
                      return None
                 quantity = int(quantity_str)
                 if quantity < 0:
                      QMessageBox.warning(self, "Lỗi nhập liệu", "Số lượng tồn kho không thể là số âm.")
                      return None
            else:
                 # In edit mode, quantity field is disabled, so just pass the original one or ignore
                 quantity = int(quantity_str) if quantity_str else 0 # Or get from self.product_data

            # Return data including the original ID if in edit mode
            if self.is_edit_mode:
                 if self.product_data and len(self.product_data) > 0:
                     product_id = self.product_data[0] # Original product ID from loaded data
                     return {
                         'id': product_id,
                         'name': name,
                         'brand': brand,
                         'category': category,
                         'price': price,
                         'sku': sku # Note: SKU is disabled in UI edit mode
                     }
                 else:
                     QMessageBox.critical(self, "Lỗi", "Không có dữ liệu sản phẩm gốc để cập nhật.")
                     return None

            else: # Add mode
                return {
                    'name': name,
                    'brand': brand,
                    'category': category,
                    'price': price,
                    'sku': sku,
                    'initial_quantity': quantity # Use this for initial stock
                }
        except ValueError:
             QMessageBox.warning(self, "Lỗi nhập liệu", "Giá và Số lượng tồn kho phải là số hợp lệ.")
             return None # Return None to indicate validation failure


# --- UI Logic for Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        """ Khởi tạo MainWindow bằng cách load UI từ file .ui """
        super().__init__()
        # Load UI từ file .ui
        # Đảm bảo file 'ui/main_window.ui' tồn tại
        try:
            loadUi("ui/main_window.ui", self)
        except FileNotFoundError:
            QMessageBox.critical(self, "Lỗi UI", "Không tìm thấy file ui/main_window.ui. Vui lòng kiểm tra lại đường dẫn.")
            sys.exit(1) # Thoát ứng dụng nếu không load được UI

        self.data_manager = DataManager() # Khởi tạo DataManager

        self.setWindowTitle("Ứng dụng Quản lý Mỹ phẩm")

        # Setup Table View Model
        self.product_model = QStandardItemModel()
        self.tableViewProducts.setModel(self.product_model)
        self._set_table_headers()
        # Fit columns to content/view and stretch Name
        self.tableViewProducts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Find index of Name column dynamically if headers change order
        try:
             name_col_index = self.product_model.horizontalHeaderLabels().index("Tên Sản phẩm")
             self.tableViewProducts.horizontalHeader().setSectionResizeMode(name_col_index, QHeaderView.ResizeMode.Stretch)
        except ValueError:
             print("Warning: 'Tên Sản phẩm' column not found for stretching.")
             # Default to stretching the first column if not found
             self.tableViewProducts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)


        # Make the table view selectable by row
        self.tableViewProducts.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tableViewProducts.setSelectionMode(QTableView.SelectionMode.SingleSelection) # Allow only single selection

        self.setup_ui_logic() # Kết nối tín hiệu/slot

        # Load initial data
        self.load_products_data()


    def setup_ui_logic(self):
        """ Connect signals to slots (Assuming object names from .ui file) """
        # Menu Actions (assuming actionManageProducts exists in your .ui menu bar)
        if hasattr(self, 'actionManageProducts'):
             self.actionManageProducts.triggered.connect(self.show_product_management_screen)

        # Buttons (assuming object names from .ui file)
        if hasattr(self, 'btnAddProduct'):
            self.btnAddProduct.clicked.connect(self.open_add_product_dialog)
        if hasattr(self, 'btnEditProduct'):
            self.btnEditProduct.clicked.connect(self.open_edit_product_dialog)
        if hasattr(self, 'btnDeleteProduct'):
            self.btnDeleteProduct.clicked.connect(self.delete_selected_product)

        # TODO: Connect other menu actions and buttons for other features


    def show_product_management_screen(self):
        """ Handle showing the product management view """
        # If using QStackedWidget, switch index here.
        # In this single-window example, this function is just a placeholder.
        print("Attempting to show Product Management Screen...")
        # QMessageBox.information(self, "Thông báo", "Đây là màn hình Quản lý Sản phẩm.")


    def _set_table_headers(self):
        """ Set headers for the product table model """
        # Ensure headers match the order of columns fetched by get_all_products
        headers = ["ID", "Tên Sản phẩm", "Thương hiệu", "Loại", "Giá", "Mã SKU", "Tồn kho"]
        self.product_model.setHorizontalHeaderLabels(headers)

    def load_products_data(self):
        """ Load product data from DB and display in QTableView """
        self.product_model.removeRows(0, self.product_model.rowCount()) # Clear existing data

        products = self.data_manager.get_all_products()

        for product in products:
            # product is a tuple/list: (id, name, brand, category, price, sku, quantity)
            items = [QStandardItem(str(col) if col is not None else '') for col in product]

            # Make all items non-editable directly in the table view
            for item in items:
                 item.setEditable(False)

            self.product_model.appendRow(items)

        print(f"Loaded {len(products)} products.")


    def open_add_product_dialog(self):
        """ Open dialog to add a new product """
        dialog = ProductDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted: # Check if dialog was accepted (OK clicked)
            product_data = dialog.get_product_data()
            if product_data: # Check if get_product_data returned data (validation passed)
                # Call data manager to add product
                success = self.data_manager.add_product(
                    product_data['name'],
                    product_data['brand'],
                    product_data['category'],
                    product_data['price'],
                    product_data['sku'],
                    product_data['initial_quantity'] # Use initial_quantity key
                )
                if success:
                    QMessageBox.information(self, "Thành công", "Đã thêm sản phẩm mới.")
                    self.load_products_data() # Reload table data to show the new product
                else:
                     # Error message handled in DataManager, but we can show a generic one or refine
                     QMessageBox.warning(self, "Lỗi", "Không thể thêm sản phẩm. Mã SKU có thể đã tồn tại hoặc lỗi khác.")


    def open_edit_product_dialog(self):
        """ Open dialog to edit selected product """
        selected_indexes = self.tableViewProducts.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Chọn sản phẩm", "Vui lòng chọn sản phẩm muốn sửa.")
            return

        # Get data of the first selected row (assuming single selection is enforced)
        selected_row = selected_indexes[0].row()

        # Get the full product data from the model for the selected row
        # This data format should match what DataManager.get_all_products returns
        product_data = []
        for col in range(self.product_model.columnCount()):
            item = self.product_model.item(selected_row, col)
            product_data.append(item.text() if item else '')

        # Convert numeric data types from string representation in model
        try:
             # Assuming order from _set_table_headers and get_all_products:
             # ID, Name, Brand, Category, Price, SKU, Quantity
             product_id = int(product_data[0])
             price = float(product_data[4])
             quantity = int(product_data[6]) # Pass original quantity for dialog load

             # Create a list/tuple in the format expected by ProductDialog init
             # (id, name, brand, category, price, sku, quantity) - used for loading dialog
             product_info_for_dialog = (product_id, product_data[1], product_data[2],
                                        product_data[3], price, product_data[5], quantity)

        except (ValueError, IndexError) as e:
             QMessageBox.critical(self, "Lỗi dữ liệu", f"Không thể đọc dữ liệu sản phẩm từ bảng: {e}")
             return

        # Open dialog with existing data
        dialog = ProductDialog(product_data=product_info_for_dialog)
        if dialog.exec() == QDialog.DialogCode.Accepted: # Check if dialog was accepted
            updated_data = dialog.get_product_data()
            if updated_data and 'id' in updated_data: # Ensure get_product_data returned valid update data
                 # Call data manager to update product
                 success = self.data_manager.update_product(
                     updated_data['id'],
                     updated_data['name'],
                     updated_data['brand'],
                     updated_data['category'],
                     updated_data['price'],
                     updated_data['sku'] # This sku is from dialog, but disabled in edit mode
                 )
                 # Quantity update is NOT handled here; should be separate stock adjustment

                 if success:
                     QMessageBox.information(self, "Thành công", "Đã cập nhật sản phẩm.")
                     self.load_products_data() # Reload table data
                 else:
                      # Error handled in DataManager, often SKU conflict
                      QMessageBox.warning(self, "Lỗi", "Không thể cập nhật sản phẩm. Mã SKU có thể đã tồn tại hoặc lỗi khác.")


    def delete_selected_product(self):
        """ Delete the selected product """
        selected_indexes = self.tableViewProducts.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Chọn sản phẩm", "Vui lòng chọn sản phẩm muốn xóa.")
            return

        # Get ID and Name of the first selected row
        selected_row = selected_indexes[0].row()
        product_id_item = self.product_model.item(selected_row, 0) # Assuming ID is in column 0
        product_name_item = self.product_model.item(selected_row, 1) # Assuming Name is in column 1


        if product_id_item and product_name_item:
             try:
                 product_id = int(product_id_item.text())
                 product_name = product_name_item.text()
             except ValueError:
                 QMessageBox.critical(self, "Lỗi dữ liệu", "Không thể đọc ID sản phẩm.")
                 return

             # Confirmation dialog
             reply = QMessageBox.question(self, 'Xác nhận xóa',
                                          f"Bạn có chắc chắn muốn xóa sản phẩm '{product_name}'?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

             if reply == QMessageBox.StandardButton.Yes:
                 # Call data manager to delete product
                 success = self.data_manager.delete_product(product_id)
                 if success:
                     QMessageBox.information(self, "Thành công", "Đã xóa sản phẩm.")
                     self.load_products_data() # Reload table data
                 else:
                      # Error handled in DataManager
                      QMessageBox.warning(self, "Lỗi", "Không thể xóa sản phẩm. Có thể do ràng buộc dữ liệu (ví dụ: sản phẩm đã có trong đơn hàng).")

        else:
             QMessageBox.critical(self, "Lỗi dữ liệu", "Không thể lấy thông tin sản phẩm để xóa.")


    # TODO: Implement other screens and their logic (Sales, Customers, Inventory, Reports)


# --- Main Application Entry Point ---

if __name__ == "__main__":
    # Kiểm tra xem file database đã tồn tại chưa để chỉ thêm dữ liệu ban đầu 1 lần
    db_exists = os.path.exists(DATABASE_NAME)

    # 1. Khởi tạo CSDL và thêm dữ liệu ban đầu
    create_tables()
    if not db_exists:
         add_initial_data()
    else:
        print("Database already exists. Skipping initial data addition.")


    # 2. Khởi tạo ứng dụng PyQt
    app = QApplication(sys.argv)

    # 3. Tạo và hiển thị cửa sổ chính
    main_window = MainWindow()
    main_window.show()

    # 4. Chạy vòng lặp sự kiện của ứng dụng
    sys.exit(app.exec())