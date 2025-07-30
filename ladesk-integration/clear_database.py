#!/usr/bin/env python3
"""
Script để xóa dữ liệu trong database
"""

import sqlite3
import os
from config import Config

def clear_database():
    """Xóa tất cả dữ liệu trong database"""
    db_path = Config.DB_PATH
    
    if not os.path.exists(db_path):
        print(f"❌ Database file không tồn tại: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Xóa dữ liệu trong bảng conversation_mappings
            cursor.execute("DELETE FROM conversation_mappings")
            mappings_deleted = cursor.rowcount
            
            # Xóa dữ liệu trong bảng webhook_logs
            cursor.execute("DELETE FROM webhook_logs")
            logs_deleted = cursor.rowcount
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='conversation_mappings'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='webhook_logs'")
            
            conn.commit()
            
            print(f"✅ Đã xóa thành công:")
            print(f"   - {mappings_deleted} mappings")
            print(f"   - {logs_deleted} webhook logs")
            print(f"   - Reset auto-increment counters")
            
    except Exception as e:
        print(f"❌ Lỗi khi xóa database: {e}")

if __name__ == "__main__":
    print("🗑️ Xóa dữ liệu trong database...")
    clear_database()
    print("✅ Hoàn thành!") 