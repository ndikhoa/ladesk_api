# Ladesk Integration API - Tổng Quan Dự Án

## 📋 Tổng quan hệ thống

Hệ thống tích hợp hai chiều giữa **Ladesk Cloud** (Facebook) và **Ladesk On-Premise** để đồng bộ tin nhắn:

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
5. Tạo ticket mới cho mỗi tin nhắn
6. Lưu mapping `cloud_conversation_id` ↔ `onpremise_ticket_id`

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
- Kiểm tra agent_id hợp lệ từ `agent_id`, `contactid`, hoặc `userid`
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
    LADESK_CLOUD_USER_IDENTIFIER = '1pkaew79'  # Default useridentifier
    
    # Ladesk On-Premise
    LADESK_ONPREMISE_BASE_URL_V3 = 'https://social-on-premise.ladesk.com/api/v3'
    LADESK_ONPREMISE_API_KEY_V3 = 'your_onpremise_v3_api_key'
    LADESK_ONPREMISE_DEPARTMENT_ID = 'department_id'
    LADESK_ONPREMISE_RECIPIENT_EMAIL = 'recipient@example.com'
```

## 🚀 Cài đặt & Chạy

### 1. Cài đặt dependencies
```bash
cd ladesk-integration
pip install -r requirements.txt
```

### 2. Cấu hình
- Copy `config.py.example` thành `config.py`
- Cập nhật API keys và URLs

### 3. Chạy ứng dụng
```bash
python app.py
```

### 4. Kiểm tra
```bash
curl http://localhost:3000/health
```

## 🔧 Quản lý Agent Mapping

### Sử dụng CLI tool
```bash
# Xem danh sách agent mappings
python manage_agent_mapping.py list

# Thêm agent mapping mới
python manage_agent_mapping.py add k6citev3 1pkaew79 "Keith Nguyen"

# Xóa agent mapping
python manage_agent_mapping.py remove k6citev3

# Test agent mapping
python manage_agent_mapping.py test k6citev3

# Reload config
python manage_agent_mapping.py reload
```

### File cấu hình agent mapping
```json
// agent_mapping.json
{
    "k6citev3": {
        "cloud_useridentifier": "1pkaew79",
        "agent_name": "Keith Nguyen",
        "added_at": "2024-01-01T00:00:00"
    }
}
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

## 🔍 Logic Webhook Hiện Tại

### **Cloud Webhook (`/webhook/ladesk-cloud`)**
- **Events xử lý:** `event_type: "message_added"`
- **Xử lý:** Tạo contact và ticket mới trên On-Premise
- **Mapping:** Lưu `cloud_conversation_id` ↔ `onpremise_ticket_id`

### **On-Premise Webhook (`/webhook/ladesk-onpremise`)**
- **Events xử lý:** `event_type: "agent_reply"` với agent_id hợp lệ
- **Kiểm tra agent_id:** Từ `agent_id`, `contactid`, hoặc `userid`
- **Xử lý:** Tìm mapping và gửi reply về Cloud

### **Events bị bỏ qua:**
- `message_added` events từ On-Premise
- `agent_reply` events không có agent_id hợp lệ
- Events có template variables trong agent_id

## 🛠️ Các tính năng đã implement

### ✅ 1. UserIdentifier Mapping
- **Vấn đề:** Agent reply bị hiểu là note thay vì message
- **Giải pháp:** Mapping agent_id On-Premise ↔ useridentifier Cloud
- **Kết quả:** Agent reply hiển thị đúng như message

### ✅ 2. Agent Mapping Management
- **Vấn đề:** Cần quản lý agent mappings một cách linh hoạt
- **Giải pháp:** External config file + CLI tool
- **Kết quả:** Dễ dàng thêm/xóa agent mappings

### ✅ 3. Webhook Logic Fix
- **Vấn đề:** Hệ thống tự động reply lại nội dung khách hàng
- **Giải pháp:** Phân biệt rõ `message_added` và `agent_reply`
- **Kết quả:** Chỉ xử lý agent_reply thực sự

### ✅ 4. JSON Parsing Improvement
- **Vấn đề:** Control characters gây lỗi JSON parsing
- **Giải pháp:** Clean control chars + json5 fallback
- **Kết quả:** JSON parsing robust

### ✅ 5. Agent ID Validation
- **Vấn đề:** Xử lý agent_reply không có agent_id hợp lệ
- **Giải pháp:** Kiểm tra agent_id từ nhiều nguồn
- **Kết quả:** Chỉ xử lý agent_reply có agent thật

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

### 5. Agent ID không hợp lệ
- **Lỗi:** `agent_id: ""` hoặc `agent_id: "{$user_id}"`
- **Xử lý:** Bỏ qua event với log warning
- **Kết quả:** Không gửi reply với default agent

### 6. JSON parsing errors
- **Lỗi:** `JSON parsing failed: Invalid control character`
- **Xử lý:** Clean control chars + json5 fallback
- **Kết quả:** Parse JSON thành công

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
    "agent_id": "k6citev3",
    "agent_name": "Keith Nguyen",
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

### Logs Monitoring
```bash
# Xem logs real-time
tail -f logs/app.log

# Filter webhook logs
grep "OnPremise webhook" logs/app.log

# Filter agent reply processing
grep "Processing agent reply" logs/app.log
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

## 📁 Cấu trúc file

```
ladesk-integration/
├── app.py                          # Ứng dụng chính
├── config.py                       # Cấu hình
├── requirements.txt                # Dependencies
├── database_simple.py              # Xử lý database
├── agent_mapping_config.py         # Quản lý agent mappings
├── manage_agent_mapping.py         # CLI tool
├── clear_database.py               # Utility
├── agent_mapping.json              # Agent mappings data
├── README.md                       # Tài liệu chính
├── AGENT_MAPPING_GUIDE.md          # Hướng dẫn agent mapping
├── USERIDENTIFIER_FIX_SUMMARY.md   # Tóm tắt fix useridentifier
├── WEBHOOK_LOGIC_FIX_SUMMARY.md    # Tóm tắt logic webhook
├── logs/                           # Log files
├── venv/                           # Virtual environment
└── ladesk_integration.db           # SQLite database
```

## 🎯 Trạng thái hiện tại

### ✅ Đã hoàn thành:
- Logic webhook ổn định
- Agent mapping management
- UserIdentifier resolution
- JSON parsing robust
- Error handling đầy đủ
- Logging chi tiết

### 🔄 Quy trình vận hành:
1. **Thêm agent mới:** Sử dụng `manage_agent_mapping.py add`
2. **Monitor logs:** Kiểm tra `logs/app.log` thường xuyên
3. **Test reply:** Đảm bảo agent có thể reply thành công
4. **Backup database:** Backup `ladesk_integration.db` định kỳ

### 📊 Metrics quan trọng:
- Số lượng mappings trong database
- Tỷ lệ webhook được xử lý thành công
- Thời gian response của API
- Số lượng lỗi JSON parsing 