import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('foodie.db')
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables():
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Bảng người dùng
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE NOT NULL,
                          password TEXT NOT NULL,
                          ho TEXT NOT NULL,
                          ten TEXT NOT NULL,
                          sdt TEXT NOT NULL)''')
            
            # Bảng món ăn
            c.execute('''CREATE TABLE IF NOT EXISTS mon_an
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          ten_mon TEXT NOT NULL,
                          gia INTEGER NOT NULL,
                          hinh_anh TEXT NOT NULL)''')
            
            # Bảng giỏ hàng
            c.execute('''CREATE TABLE IF NOT EXISTS gio_hang
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER NOT NULL,
                          mon_an_id INTEGER NOT NULL,
                          so_luong INTEGER DEFAULT 1,
                          FOREIGN KEY (user_id) REFERENCES users (id),
                          FOREIGN KEY (mon_an_id) REFERENCES mon_an (id))''')
            
            conn.commit()
            
            # Thêm dữ liệu mẫu nếu bảng món ăn trống
            c.execute("SELECT COUNT(*) FROM mon_an")
            if c.fetchone()[0] == 0:
                mon_an_data = [
                    ("Phở bò", 40000, ":/pic/pho_bo.jpg"),
                    ("Cơm tấm", 40000, ":/pic/com_tam.jpg"),
                    ("Cơm chiên", 30000, ":/pic/com_chien.jpg"),
                    ("Hủ tiếu", 35000, ":/pic/hu_tieuu.jpg"),
                    ("Hủ tiếu bò kho", 40000, ":/pic/hu_tieu_bo_kho.jpg"),
                    ("Bánh canh", 35000, ":/pic/banh_canh.jpg"),
                    ("Hoành thánh", 30000, ":/pic/hoanh_thanh.jpg"),
                    ("Bún mọc", 30000, ":/pic/bun_moc.jpg"),
                    ("Súp cua", 25000, ":/pic/sup_cua.jpg"),
                    ("Bánh mì thịt", 25000, ":/pic/banh_mi.jpg"),
                    ("Bánh canh cua", 45000, ":/pic/banh_canh_cua.jpg"),
                    ("Cơm bò xào", 40000, ":/pic/com_bo_xao.jpg"),
                    ("Bún bò Huế", 40000, ":/pic/bun_bo_hue.jpg"),
                    ("Cơm gà chiên", 40000, ":/pic/com_ga_chien.jpg"),
                    ("Cháo thịt bằm", 25000, ":/pic/chao_thit_bam.jpg")
                ]
                c.executemany("INSERT INTO mon_an (ten_mon, gia, hinh_anh) VALUES (?, ?, ?)", mon_an_data)
                conn.commit()
                
        except Error as e:
            print(e)
        finally:
            conn.close()

def register_user(username, password, ho, ten, sdt):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, ho, ten, sdt) VALUES (?, ?, ?, ?, ?)",
                      (username, password, ho, ten, sdt))
            conn.commit()
            return True
        except Error as e:
            print(e)
            return False
        finally:
            conn.close()
    return False

def login_user(username, password):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT id, ho, ten FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            return user if user else None
        except Error as e:
            print(e)
            return None
        finally:
            conn.close()
    return None

def get_mon_an(page=1, items_per_page=8):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            offset = (page - 1) * items_per_page
            c.execute("SELECT * FROM mon_an LIMIT ? OFFSET ?", (items_per_page, offset))
            return c.fetchall()
        except Error as e:
            print(e)
            return []
        finally:
            conn.close()
    return []

def add_to_cart(user_id, mon_an_id):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            # Kiểm tra xem món đã có trong giỏ hàng chưa
            c.execute("SELECT id, so_luong FROM gio_hang WHERE user_id=? AND mon_an_id=?", (user_id, mon_an_id))
            item = c.fetchone()
            
            if item:
                # Nếu có rồi thì tăng số lượng lên 1
                new_quantity = item[1] + 1
                c.execute("UPDATE gio_hang SET so_luong=? WHERE id=?", (new_quantity, item[0]))
            else:
                # Nếu chưa có thì thêm mới
                c.execute("INSERT INTO gio_hang (user_id, mon_an_id) VALUES (?, ?)", (user_id, mon_an_id))
            
            conn.commit()
            return True
        except Error as e:
            print(e)
            return False
        finally:
            conn.close()
    return False

def get_cart_items(user_id):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute('''SELECT m.id, m.ten_mon, m.gia, g.so_luong, m.gia * g.so_luong as thanh_tien 
                         FROM gio_hang g 
                         JOIN mon_an m ON g.mon_an_id = m.id 
                         WHERE g.user_id=?''', (user_id,))
            return c.fetchall()
        except Error as e:
            print(e)
            return []
        finally:
            conn.close()
    return []

def clear_cart(user_id):
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("DELETE FROM gio_hang WHERE user_id=?", (user_id,))
            conn.commit()
            return True
        except Error as e:
            print(e)
            return False
        finally:
            conn.close()
    return False

# Khởi tạo database khi import module
create_tables()