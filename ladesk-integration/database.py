import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import Config

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và tạo các bảng cần thiết"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tạo bảng ticket_mapping
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ticket_mapping (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ladesk_conversation_id TEXT UNIQUE NOT NULL,
                        onpremise_ticket_id TEXT UNIQUE NOT NULL,
                        customer_info TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tạo bảng webhook_logs
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS webhook_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        webhook_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        status TEXT DEFAULT 'received',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logging.info("Database initialized successfully")
                
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    def create_ticket_mapping(self, ladesk_conversation_id: str, onpremise_ticket_id: str, 
                            customer_info: Dict) -> bool:
        """Tạo mapping giữa Ladesk conversation ID và On-premise ticket ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ticket_mapping 
                    (ladesk_conversation_id, onpremise_ticket_id, customer_info, status)
                    VALUES (?, ?, ?, ?)
                ''', (
                    ladesk_conversation_id,
                    onpremise_ticket_id,
                    json.dumps(customer_info),
                    'open'
                ))
                conn.commit()
                logging.info(f"Ticket mapping created: {ladesk_conversation_id} -> {onpremise_ticket_id}")
                return True
        except sqlite3.IntegrityError:
            logging.warning(f"Ticket mapping already exists: {ladesk_conversation_id}")
            return False
        except Exception as e:
            logging.error(f"Error creating ticket mapping: {e}")
            return False
    
    def get_ticket_mapping(self, ticket_id: str = None, conversation_id: str = None) -> Optional[Dict]:
        """Lấy thông tin mapping theo ticket_id hoặc conversation_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if ticket_id:
                    cursor.execute('''
                        SELECT * FROM ticket_mapping WHERE onpremise_ticket_id = ?
                    ''', (ticket_id,))
                elif conversation_id:
                    cursor.execute('''
                        SELECT * FROM ticket_mapping WHERE ladesk_conversation_id = ?
                    ''', (conversation_id,))
                else:
                    return None
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'ladesk_conversation_id': row[1],
                        'onpremise_ticket_id': row[2],
                        'customer_info': json.loads(row[3]) if row[3] else {},
                        'status': row[4],
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting ticket mapping: {e}")
            return None
    
    def get_all_mappings(self) -> List[Dict]:
        """Lấy tất cả ticket mappings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ticket_mapping ORDER BY created_at DESC')
                rows = cursor.fetchall()
                
                return [{
                    'id': row[0],
                    'ladesk_conversation_id': row[1],
                    'onpremise_ticket_id': row[2],
                    'customer_info': json.loads(row[3]) if row[3] else {},
                    'status': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                } for row in rows]
        except Exception as e:
            logging.error(f"Error getting all mappings: {e}")
            return []
    
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Cập nhật trạng thái ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ticket_mapping 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE onpremise_ticket_id = ?
                ''', (status, ticket_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating ticket status: {e}")
            return False
    
    def log_webhook(self, webhook_type: str, data: Dict, status: str = 'received') -> bool:
        """Log webhook data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhook_logs (webhook_type, data, status)
                    VALUES (?, ?, ?)
                ''', (webhook_type, json.dumps(data), status))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error logging webhook: {e}")
            return False
    
    def get_webhook_logs(self, limit: int = 50) -> List[Dict]:
        """Lấy webhook logs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM webhook_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                
                return [{
                    'id': row[0],
                    'webhook_type': row[1],
                    'data': json.loads(row[2]) if row[2] else {},
                    'status': row[3],
                    'created_at': row[4]
                } for row in rows]
        except Exception as e:
            logging.error(f"Error getting webhook logs: {e}")
            return []

# Global database instance
db = DatabaseManager() 
