# db_helper.py
import pyodbc

def search_food_names(keyword):
    try:
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=DESKTOP-XXXXXXX\\SQLEXPRESS;"   
            "Database=DOAN;"                         
            "Trusted_Connection=yes;"
        )
        cursor = conn.cursor()
        query = "SELECT TenMonAn FROM MonAn WHERE TenMonAn LIKE ?"
        cursor.execute(query, ('%' + keyword + '%',))
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        return result
    except Exception as e:
        print("Lỗi kết nối hoặc truy vấn:", e)
        return []
