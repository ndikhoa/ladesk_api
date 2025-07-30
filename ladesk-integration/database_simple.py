import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

class SimpleDatabaseManager:
    """Database manager đơn giản: 1 conversation = 1 mapping"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self.create_tables()
    
    def create_tables(self):
        """Tạo bảng đơn giản cho logic mới"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Bảng chính: conversation_mappings (hỗ trợ nhiều ticket cho 1 conversation)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_mappings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cloud_conversation_id TEXT NOT NULL,
                        onpremise_ticket_id TEXT NOT NULL,
                        onpremise_contact_id TEXT NOT NULL,
                        customer_name TEXT,
                        customer_email TEXT NOT NULL,
                        last_agent_reply TEXT,
                        last_agent_name TEXT,
                        last_reply_time TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Index cho performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversation_mappings_cloud_id 
                    ON conversation_mappings(cloud_conversation_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversation_mappings_ticket_id 
                    ON conversation_mappings(onpremise_ticket_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversation_mappings_email 
                    ON conversation_mappings(customer_email)
                ''')
                
                # Bảng webhook logs (giữ nguyên)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS webhook_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        webhook_type TEXT NOT NULL,
                        conversation_id TEXT,
                        ticket_id TEXT,
                        contact_id TEXT,
                        event_type TEXT,
                        raw_data TEXT,
                        processed_data TEXT,
                        status TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("✅ Simple database tables created successfully")
                
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise

    def create_mapping(self, cloud_conversation_id: str, onpremise_ticket_id: str, 
                      onpremise_contact_id: str, customer_name: str = None, 
                      customer_email: str = None) -> bool:
        """Tạo mapping mới: 1 conversation = 1 mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversation_mappings 
                    (cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id, customer_name, customer_email)
                    VALUES (?, ?, ?, ?, ?)
                ''', (cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id, customer_name, customer_email))
                
                conn.commit()
                logger.info(f"✅ Created mapping: {cloud_conversation_id} -> {onpremise_ticket_id}")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Mapping already exists for conversation: {cloud_conversation_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error creating mapping: {e}")
            return False

    def get_mapping_by_conversation(self, cloud_conversation_id: str) -> Optional[Dict]:
        """Lấy mapping theo conversation_id (ticket gần nhất)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id,
                           customer_name, customer_email, created_at, updated_at
                    FROM conversation_mappings 
                    WHERE cloud_conversation_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (cloud_conversation_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'cloud_conversation_id': result[1],
                        'onpremise_ticket_id': result[2],
                        'onpremise_contact_id': result[3],
                        'customer_name': result[4],
                        'customer_email': result[5],
                        'created_at': result[6],
                        'updated_at': result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting mapping by conversation: {e}")
            return None

    def get_mapping_by_ticket(self, onpremise_ticket_id: str) -> Optional[Dict]:
        """Lấy mapping theo ticket_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id,
                           customer_name, customer_email, created_at, updated_at
                    FROM conversation_mappings 
                    WHERE onpremise_ticket_id = ?
                ''', (onpremise_ticket_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'cloud_conversation_id': result[1],
                        'onpremise_ticket_id': result[2],
                        'onpremise_contact_id': result[3],
                        'customer_name': result[4],
                        'customer_email': result[5],
                        'created_at': result[6],
                        'updated_at': result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting mapping by ticket: {e}")
            return None

    def get_mapping_by_email(self, customer_email: str) -> Optional[Dict]:
        """Lấy mapping theo email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id,
                           customer_name, customer_email, created_at, updated_at
                    FROM conversation_mappings 
                    WHERE customer_email = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (customer_email,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'cloud_conversation_id': result[1],
                        'onpremise_ticket_id': result[2],
                        'onpremise_contact_id': result[3],
                        'customer_name': result[4],
                        'customer_email': result[5],
                        'created_at': result[6],
                        'updated_at': result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting mapping by email: {e}")
            return None

    def get_mapping_by_ticket_pattern(self, ticket_pattern: str) -> Optional[Dict]:
        """Lấy mapping theo pattern của ticket ID (ví dụ: QQX-DGGBS-%)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id,
                           customer_name, customer_email, created_at, updated_at
                    FROM conversation_mappings 
                    WHERE onpremise_ticket_id LIKE ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (ticket_pattern,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'cloud_conversation_id': result[1],
                        'onpremise_ticket_id': result[2],
                        'onpremise_contact_id': result[3],
                        'customer_name': result[4],
                        'customer_email': result[5],
                        'created_at': result[6],
                        'updated_at': result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting mapping by ticket pattern: {e}")
            return None

    def get_all_mappings(self, limit: int = 100) -> List[Dict]:
        """Lấy tất cả mappings (có giới hạn)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, cloud_conversation_id, onpremise_ticket_id, onpremise_contact_id,
                           customer_name, customer_email, created_at, updated_at
                    FROM conversation_mappings 
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                mappings = []
                
                for result in results:
                    mappings.append({
                        'id': result[0],
                        'cloud_conversation_id': result[1],
                        'onpremise_ticket_id': result[2],
                        'onpremise_contact_id': result[3],
                        'customer_name': result[4],
                        'customer_email': result[5],
                        'created_at': result[6],
                        'updated_at': result[7]
                    })
                
                return mappings
                
        except Exception as e:
            logger.error(f"❌ Error getting all mappings: {e}")
            return []

    def update_mapping(self, cloud_conversation_id: str, **kwargs) -> bool:
        """Cập nhật mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Xây dựng query update động
                update_fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['onpremise_ticket_id', 'onpremise_contact_id', 'customer_name', 'customer_email', 
                              'last_agent_reply', 'last_agent_name', 'last_reply_time']:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                if not update_fields:
                    return False
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(cloud_conversation_id)
                
                query = f'''
                    UPDATE conversation_mappings 
                    SET {', '.join(update_fields)}
                    WHERE cloud_conversation_id = ?
                '''
                
                cursor.execute(query, values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Updated mapping for conversation: {cloud_conversation_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No mapping found to update for conversation: {cloud_conversation_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error updating mapping: {e}")
            return False

    def delete_mapping(self, cloud_conversation_id: str) -> bool:
        """Xóa mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM conversation_mappings 
                    WHERE cloud_conversation_id = ?
                ''', (cloud_conversation_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Deleted mapping for conversation: {cloud_conversation_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No mapping found to delete for conversation: {cloud_conversation_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error deleting mapping: {e}")
            return False

    def log_webhook(self, webhook_type: str, data: Dict, status: str = 'received', 
                   error_message: str = None) -> bool:
        """Log webhook (giữ nguyên)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhook_logs 
                    (webhook_type, conversation_id, ticket_id, contact_id, event_type, 
                     raw_data, processed_data, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    webhook_type,
                    data.get('conversation_id'),
                    data.get('ticket_id'),
                    data.get('contact_id'),
                    data.get('event_type'),
                    json.dumps(data),
                    json.dumps(data),  # processed_data = raw_data cho đơn giản
                    status,
                    error_message
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error logging webhook: {e}")
            return False

    def get_webhook_logs(self, limit: int = 50) -> List[Dict]:
        """Lấy webhook logs (giữ nguyên)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, webhook_type, conversation_id, ticket_id, contact_id, 
                           event_type, raw_data, processed_data, status, error_message, created_at
                    FROM webhook_logs 
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                logs = []
                
                for result in results:
                    logs.append({
                        'id': result[0],
                        'webhook_type': result[1],
                        'conversation_id': result[2],
                        'ticket_id': result[3],
                        'contact_id': result[4],
                        'event_type': result[5],
                        'raw_data': result[6],
                        'processed_data': result[7],
                        'status': result[8],
                        'error_message': result[9],
                        'created_at': result[10]
                    })
                
                return logs
                
        except Exception as e:
            logger.error(f"❌ Error getting webhook logs: {e}")
            return []

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Cập nhật trạng thái ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE conversation_mappings 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE onpremise_ticket_id = ?
                ''', (ticket_id,))
                
                conn.commit()
                logger.info(f"✅ Updated ticket status: {ticket_id} -> {status}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error updating ticket status: {e}")
            return False

    def get_stats(self) -> Dict:
        """Lấy thống kê database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tổng số mappings
                cursor.execute('SELECT COUNT(*) FROM conversation_mappings')
                total_mappings = cursor.fetchone()[0]
                
                # Mappings hôm nay
                cursor.execute('''
                    SELECT COUNT(*) FROM conversation_mappings 
                    WHERE DATE(created_at) = DATE('now')
                ''')
                today_mappings = cursor.fetchone()[0]
                
                # Tổng số webhook logs
                cursor.execute('SELECT COUNT(*) FROM webhook_logs')
                total_logs = cursor.fetchone()[0]
                
                # Logs hôm nay
                cursor.execute('''
                    SELECT COUNT(*) FROM webhook_logs 
                    WHERE DATE(created_at) = DATE('now')
                ''')
                today_logs = cursor.fetchone()[0]
                
                return {
                    'total_mappings': total_mappings,
                    'today_mappings': today_mappings,
                    'total_logs': total_logs,
                    'today_logs': today_logs
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

# Tạo instance global
db = SimpleDatabaseManager() 