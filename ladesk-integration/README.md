# Ladesk Integration API

## 📋 Tổng quan hệ thống

Hệ thống tích hợp giữa **Ladesk Cloud** (Facebook) và **Ladesk On-Premise** để đồng bộ tin nhắn hai chiều:

- **Facebook → Cloud → On-Premise**: Tin nhắn khách hàng từ Facebook được tạo thành ticket mới trên On-Premise
- **On-Premise → Cloud → Facebook**: Reply của agent từ On-Premise được gửi về Facebook qua Cloud

## 🔄 Logic xử lý chính

### 1. Flow Facebook → On-Premise
```
Facebook → Ladesk Cloud → Webhook → Tạo Contact → Tạo Ticket → Mapping
```

**Chi tiết:**
1. Khách hàng gửi tin nhắn trên Facebook
2. Ladesk Cloud nhận và gửi webhook đến `/webhook/ladesk-cloud`
3. Hệ thống lấy thông tin contact từ Cloud API
4. Tạo contact trong On-Premise (hoặc lấy ID nếu đã tồn tại)
5. Tạo ticket mới cho mỗi tin nhắn (vì LiveAgent không cho phép update message)
6. Lưu mapping `cloud_conversation_id` ↔ `onpremise_ticket_code`

### 2. Flow On-Premise → Facebook
```
Agent Reply → On-Premise Webhook → Tìm Mapping → Gửi Reply → Cloud → Facebook
```

**Chi tiết:**
1. Agent reply tin nhắn trên On-Premise
2. On-Premise gửi webhook đến `/webhook/ladesk-onpremise`
3. Hệ thống tìm mapping bằng ticket_id hoặc email
4. Gửi reply đến Cloud API với conversation_id gốc
5. Cloud gửi tin nhắn về Facebook

## 🗄️ Database Mapping

### Bảng `conversation_mappings`
```sql
CREATE TABLE conversation_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cloud_conversation_id TEXT NOT NULL,      -- ID conversation từ Cloud
    onpremise_ticket_id TEXT NOT NULL,        -- Code ticket từ On-Premise
    onpremise_contact_id TEXT,                -- ID contact trong On-Premise
    customer_name TEXT,                       -- Tên khách hàng
    customer_email TEXT,                      -- Email khách hàng
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_agent_reply TEXT,                    -- Reply cuối cùng của agent
    last_agent_name TEXT,                     -- Tên agent cuối cùng
    last_reply_time TIMESTAMP                 -- Thời gian reply cuối
);
```

### Bảng `webhook_logs`
```sql
CREATE TABLE webhook_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,                     -- 'cloud_incoming' hoặc 'onpremise_incoming'
    data TEXT NOT NULL,                       -- JSON data từ webhook
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 API Endpoints

### 1. Health Check
```
GET /health
```
Kiểm tra trạng thái hệ thống

### 2. Cloud Webhook
```
POST /webhook/ladesk-cloud
```
Nhận webhook từ Ladesk Cloud khi có tin nhắn Facebook

**Xử lý:**
- Chỉ xử lý `event_type: "message_added"` và `message_type: "M"`
- Kiểm tra status conversation (C=Open, A=Answered, R=Resolved)
- Tạo contact và ticket mới trên On-Premise
- Lưu mapping conversation

### 3. On-Premise Webhook
```
POST /webhook/ladesk-onpremise
```
Nhận webhook từ Ladesk On-Premise khi agent reply

**Xử lý:**
- Chỉ xử lý `event_type: "agent_reply"`
- Tìm mapping bằng ticket_id hoặc email
- Gửi reply về Cloud với conversation_id gốc

## 🔧 API Versions & Endpoints

### Ladesk Cloud API

#### API v3 (Contacts)
```
GET /api/v3/contacts/{contact_id}
```
- **Headers:** `apikey: {API_KEY_V3}`
- **Content-Type:** `application/json`
- **Dùng cho:** Lấy thông tin contact chi tiết

#### API v1 (Conversations)
```
GET /api/conversations/{conversation_id}
POST /api/conversations/{conversation_id}/messages
```
- **Headers:** `apikey: {API_KEY_V1}`
- **Content-Type:** `application/x-www-form-urlencoded` (POST)
- **Dùng cho:** Lấy thông tin conversation và gửi reply

### Ladesk On-Premise API

#### API v3 (Tickets & Contacts)
```
POST /api/v3/contacts
POST /api/v3/tickets
```
- **Headers:** `apikey: {API_KEY_V3}`
- **Content-Type:** `application/json`
- **Dùng cho:** Tạo contact và ticket mới

#### API v1 (Messages - không dùng)
```
POST /api/conversations/{conversation_id}/messages
```
- **Lưu ý:** Không sử dụng vì LiveAgent không cho phép update message

## 📝 Cấu hình

### File `config.py`
```python
class Config:
    # Server
    HOST = '0.0.0.0'
    PORT = 3000
    DEBUG = True
    
    # Ladesk Cloud
    LADESK_CLOUD_BASE_URL_V3 = 'https://social.ladesk.com/api/v3'
    LADESK_CLOUD_API_KEY_V3 = 'your_v3_api_key'
    LADESK_CLOUD_BASE_URL_V1 = 'https://social.ladesk.com/api'
    LADESK_CLOUD_API_KEY_V1 = 'your_v1_api_key'
    LADESK_CLOUD_USER_IDENTIFIER = 'agent_id'
    
    # Ladesk On-Premise
    LADESK_ONPREMISE_BASE_URL_V3 = 'https://social-on-premise.ladesk.com/api/v3'
    LADESK_ONPREMISE_API_KEY_V3 = 'your_onpremise_v3_api_key'
    LADESK_ONPREMISE_BASE_URL_V1 = 'https://social-on-premise.ladesk.com/api'
    LADESK_ONPREMISE_API_KEY_V1 = 'your_onpremise_v1_api_key'
    LADESK_ONPREMISE_DEPARTMENT_ID = 'department_id'
    LADESK_ONPREMISE_RECIPIENT_EMAIL = 'recipient@example.com'
```

## 🚀 Cài đặt & Chạy

### 1. Cài đặt dependencies
```bash
pip install flask requests
```

### 2. Cấu hình
- Copy `config.py.example` thành `config.py`
- Cập nhật API keys và URLs

### 3. Chạy ứng dụng
```bash
cd ladesk-integration
python app.py
```

### 4. Kiểm tra
```bash
curl http://localhost:3000/health
```

## 📊 Logging

Hệ thống log chi tiết vào:
- **File:** `logs/app.log`
- **Console:** Real-time logs
- **Database:** Webhook logs

### Log levels:
- `INFO`: Thông tin xử lý bình thường
- `WARNING`: Cảnh báo (template variables, missing data)
- `ERROR`: Lỗi cần xử lý

## 🔍 Xử lý lỗi thường gặp

### 1. Contact đã tồn tại
- **Lỗi:** `400 - Contact with this Contact information already exist`
- **Xử lý:** Trích xuất ID từ error message bằng regex
- **Kết quả:** Tiếp tục tạo ticket với contact_id có sẵn

### 2. Template variables trong agent_name
- **Lỗi:** `agent_name: "{$user_firstname} {$user_lastname}"`
- **Xử lý:** Sử dụng tên mặc định "Agent"
- **Kết quả:** Reply vẫn được gửi thành công

### 3. HTML entities trong message
- **Lỗi:** `message: "<p>text</p>&nbsp;"`
- **Xử lý:** Strip HTML tags + decode entities + trim whitespace
- **Kết quả:** `message: "text"`

### 4. Mapping không tìm thấy
- **Lỗi:** `No mapping found for ticket_id`
- **Xử lý:** Tìm bằng email, log tất cả mappings để debug
- **Kết quả:** Trả về 404 nếu không tìm thấy

## 🧪 Testing

### Test Cloud Webhook
```bash
curl -X POST http://localhost:3000/webhook/ladesk-cloud \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "message_added",
    "conversation_id": "test123",
    "message": "Test message",
    "message_type": "M",
    "status": "C",
    "contact_id": "contact123"
  }'
```

### Test On-Premise Webhook
```bash
curl -X POST http://localhost:3000/webhook/ladesk-onpremise \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "agent_reply",
    "ticket_id": "TEST-123",
    "message": "Agent reply",
    "customer_email": "facebook_test123@facebook.com"
  }'
```

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:3000/health
```

### Database Status
```bash
python -c "from database_simple import db; print(f'Mappings: {len(db.get_all_mappings())}')"
```

## 🔒 Bảo mật

- **API Keys:** Lưu trong config file, không commit lên git
- **Webhook Validation:** Kiểm tra event_type và message_type
- **Error Handling:** Không expose thông tin nhạy cảm trong logs
- **Rate Limiting:** Có thể thêm middleware nếu cần

## 📚 Tài liệu tham khảo

- [Ladesk Cloud API v3](https://docs.ladesk.com/)
- [Ladesk On-Premise API](https://docs.ladesk.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html) 