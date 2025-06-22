import pyodbc

def get_all_subscribers(conn: pyodbc.Connection):
    rows = []
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Subscribers")
        for row in cursor.fetchall():
            print(row)
            rows.append(f"{row.ID}, {row.EMAIL}, {row.POSTCODE}")
    return rows