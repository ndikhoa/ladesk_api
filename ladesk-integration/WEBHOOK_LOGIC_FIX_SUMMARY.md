# Tóm tắt Logic Webhook Hiện Tại

## **Tổng quan Logic Webhook**

Hệ thống tích hợp Ladesk Cloud ↔ On-Premise sử dụng 2 webhook chính:

### **1. Cloud Webhook (`/webhook/ladesk-cloud`)**
- **Mục đích:** Nhận tin nhắn từ Facebook qua Ladesk Cloud
- **Xử lý:** Tạo contact và ticket mới trên On-Premise
- **Events:** Chỉ xử lý `event_type: "message_added"`

### **2. On-Premise Webhook (`/webhook/ladesk-onpremise`)**
- **Mục đích:** Nhận reply của agent từ On-Premise
- **Xử lý:** Gửi reply về Facebook qua Cloud
- **Events:** Chỉ xử lý `event_type: "agent_reply"`

## **Logic Phân Loại Events**

### **✅ Events được xử lý:**

#### **Cloud Webhook - message_added**
```json
{
    "event_type": "message_added",
    "message_type": "M",
    "status": "C",  // C=Open, A=Answered, R=Resolved
    "conversation_id": "conv_123",
    "contact_id": "contact_456",
    "message": "Tin nhắn từ khách hàng"
}
```
**Xử lý:**
1. Tạo contact mới trên On-Premise (hoặc lấy ID nếu đã tồn tại)
2. Tạo ticket mới cho tin nhắn
3. Lưu mapping `cloud_conversation_id` ↔ `onpremise_ticket_id`

#### **On-Premise Webhook - agent_reply (có agent_id hợp lệ)**
```json
{
    "event_type": "agent_reply",
    "agent_id": "k6citev3",        // ✅ Có agent_id hợp lệ
    "contactid": "k6citev3",       // ✅ Hoặc contactid hợp lệ
    "userid": "k6citev3",          // ✅ Hoặc userid hợp lệ
    "agent_name": "Keith Nguyen",  // ✅ Tên agent thật
    "ticket_id": "TICKET-123",
    "conversation_id": "TICKET-123",
    "message": "Reply từ agent",
    "customer_email": "customer@example.com"
}
```
**Xử lý:**
1. Tìm mapping bằng `ticket_id` hoặc `customer_email`
2. Gửi reply đến Cloud với `conversation_id` gốc
3. Sử dụng `agent_id` hợp lệ để map với `useridentifier` của Cloud

### **⏭️ Events bị bỏ qua:**

#### **On-Premise Webhook - agent_reply (không có agent_id hợp lệ)**
```json
{
    "event_type": "agent_reply",
    "agent_id": "",                // ❌ Empty
    "contactid": "",               // ❌ Empty
    "userid": "",                  // ❌ Empty
    "agent_name": "",              // ❌ Empty hoặc template
    "ticket_id": "TICKET-123",
    "message": "Reply từ agent"
}
```
**Xử lý:** ⏭️ Bỏ qua với log `"⚠️ No valid agent_id found, skipping agent_reply event"`

#### **On-Premise Webhook - message_added**
```json
{
    "event_type": "message_added",  // ❌ Không phải agent_reply
    "agent_id": "k6citev3",
    "message": "Tin nhắn từ khách hàng"
}
```
**Xử lý:** ⏭️ Bỏ qua với log `"⏭️ Skipping non-agent-reply event: message_added"`

## **Logic Kiểm Tra Agent ID**

### **Các nguồn agent_id được kiểm tra (theo thứ tự ưu tiên):**

1. **`agent_id`** - ID chính của agent
2. **`contactid`** - Contact ID của agent  
3. **`userid`** - User ID của agent

### **Điều kiện hợp lệ:**
```python
# Agent ID hợp lệ phải:
- Không rỗng (not empty)
- Không chứa template variables (không có '{')
- Không phải là placeholder ('{$user_id}')
- Có giá trị thực sự
```

### **Ví dụ:**
```python
# ✅ Hợp lệ
agent_id = "k6citev3"
contactid = "agent123"
userid = "user456"

# ❌ Không hợp lệ
agent_id = ""
agent_id = "{$user_id}"
agent_id = "{template_var}"
agent_id = None
```

## **Cải Thiện JSON Parsing**

### **Vấn đề:**
- Webhook data chứa control characters gây lỗi `JSON parsing failed: Invalid control character`

### **Giải pháp:**
```python
def parse_webhook_data(request):
    try:
        raw_data = request.get_data(as_text=True)
        
        # Làm sạch control characters
        import re
        cleaned_data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', raw_data)
        
        # Parse JSON
        data = json.loads(cleaned_data)
        return data
        
    except json.JSONDecodeError:
        # Fallback với json5
        try:
            import json5
            data = json5.loads(raw_data)
            return data
        except:
            return None
```

### **Dependency mới:**
```txt
# requirements.txt
json5==0.9.14
```

## **Logs Chi Tiết**

### **Logs thành công:**
```
✅ agent_reply with valid agent_id: "🔄 Processing agent reply: conv_123, agent: Keith Nguyen, valid_agent_id: k6citev3"
✅ Found mapping by ticket_id: "TICKET-123"
✅ Reply sent successfully to Cloud: conv_123
```

### **Logs bỏ qua:**
```
⏭️ Skipping non-agent-reply event: message_added
⚠️ No valid agent_id found, skipping agent_reply event
⚠️ agent_id='', contactid='', userid=''
```

### **Logs lỗi:**
```
❌ No mapping found for ticket_id: TICKET-123
❌ JSON parsing failed: Invalid control character
❌ Failed to send reply: API error message
```

## **Test Cases**

### **Test 1: Valid agent_reply**
```bash
curl -X POST http://localhost:3000/webhook/ladesk-onpremise \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "agent_reply",
    "agent_id": "k6citev3",
    "agent_name": "Keith Nguyen",
    "ticket_id": "TICKET-123",
    "message": "Test reply"
  }'
```
**Kết quả:** ✅ Xử lý và gửi reply

### **Test 2: agent_reply với empty agent_id**
```bash
curl -X POST http://localhost:3000/webhook/ladesk-onpremise \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "agent_reply",
    "agent_id": "",
    "ticket_id": "TICKET-123",
    "message": "Test reply"
  }'
```
**Kết quả:** ⏭️ Bỏ qua (no_valid_agent_id)

### **Test 3: message_added event**
```bash
curl -X POST http://localhost:3000/webhook/ladesk-onpremise \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "message_added",
    "agent_id": "k6citev3",
    "message": "Customer message"
  }'
```
**Kết quả:** ⏭️ Bỏ qua (non_agent_reply_event)

## **Monitoring & Debug**

### **Kiểm tra logs:**
```bash
# Xem logs real-time
tail -f logs/app.log

# Filter webhook logs
grep "OnPremise webhook" logs/app.log

# Filter agent reply processing
grep "Processing agent reply" logs/app.log
```

### **Kiểm tra database:**
```bash
# Xem mappings
python -c "from database_simple import db; print('Mappings:', len(db.get_all_mappings()))"

# Xem webhook logs
python -c "from database_simple import db; print('Webhook logs:', len(db.get_webhook_logs()))"
```

## **Lưu Ý Quan Trọng**

### **✅ Logic hiện tại đã ổn định:**
- Phân biệt đúng `message_added` và `agent_reply`
- Chỉ xử lý agent_reply có agent_id hợp lệ
- JSON parsing robust với fallback
- Logs chi tiết để debug

### **⚠️ Cần lưu ý:**
- Agent mapping phải được cấu hình trước khi agent có thể reply
- Sử dụng `manage_agent_mapping.py` để quản lý agent mappings
- Monitor logs thường xuyên để phát hiện issues sớm

### **🔄 Quy trình thêm agent mới:**
1. Agent được tạo trên On-Premise
2. Sử dụng `manage_agent_mapping.py add` để thêm mapping
3. Test reply để đảm bảo hoạt động
4. Monitor logs để confirm

## **Files liên quan:**
- `app.py` - Logic webhook chính
- `agent_mapping_config.py` - Quản lý agent mappings
- `manage_agent_mapping.py` - CLI tool quản lý
- `requirements.txt` - Dependencies (bao gồm json5)
- `logs/app.log` - Logs chi tiết 