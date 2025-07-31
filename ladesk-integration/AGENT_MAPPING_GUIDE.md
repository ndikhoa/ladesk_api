# Hướng dẫn quản lý Agent Mapping

## **Vấn đề ban đầu:**
Khi thêm agent mới trên Ladesk On-Premise, bạn phải sửa code và restart service để agent có thể reply được.

## **Giải pháp mới:**
Sử dụng file config riêng để quản lý mapping, không cần sửa code hay restart service.

---

## **📋 Cách sử dụng:**

### **1. Xem danh sách mapping hiện tại:**
```bash
python manage_agent_mapping.py list
```

### **2. Thêm agent mapping mới:**
```bash
python manage_agent_mapping.py add --onpremise-id "agent123" --cloud-id "cloud456"
```

### **3. Xóa mapping:**
```bash
python manage_agent_mapping.py remove --onpremise-id "agent123"
```

### **4. Test mapping:**
```bash
python manage_agent_mapping.py test --onpremise-id "agent123"
```

### **5. Reload mapping (nếu sửa file trực tiếp):**
```bash
python manage_agent_mapping.py reload
```

---

## **📁 File cấu hình:**

### **`agent_mapping.json`** (tự động tạo):
```json
{
  "k6citev3": "1pkaew79",
  "agent123": "cloud456",
  "agent789": "cloud999"
}
```

### **Cấu trúc:**
- **Key**: Agent ID từ On-Premise
- **Value**: User Identifier từ Cloud

---

## **🔄 Quy trình thêm agent mới:**

### **Bước 1: Lấy thông tin agent**
1. **On-Premise Agent ID**: Lấy từ webhook hoặc API On-Premise
2. **Cloud User Identifier**: Lấy từ Cloud admin panel hoặc API

### **Bước 2: Thêm mapping**
```bash
python manage_agent_mapping.py add --onpremise-id "new_agent_id" --cloud-id "cloud_user_id"
```

### **Bước 3: Test**
```bash
python manage_agent_mapping.py test --onpremise-id "new_agent_id"
```

### **Bước 4: Kiểm tra**
- Agent có thể reply từ On-Premise
- Reply hiển thị như message thật (không phải note)
- Không cần restart service

---

## **🔧 Các file liên quan:**

### **`agent_mapping_config.py`**
- Class quản lý mapping
- Load/save từ file JSON
- Tự động tạo file mặc định

### **`manage_agent_mapping.py`**
- Script CLI để quản lý mapping
- Các lệnh: list, add, remove, test, reload

### **`app.py`**
- Sử dụng mapping config thay vì hardcode
- Tự động reload mapping khi cần

---

## **⚠️ Lưu ý quan trọng:**

### **1. Backup mapping:**
```bash
cp agent_mapping.json agent_mapping_backup.json
```

### **2. Kiểm tra format:**
- On-Premise ID: thường là string ngắn
- Cloud ID: thường là string dài hơn

### **3. Test trước khi deploy:**
```bash
python test_useridentifier_fix.py
```

### **4. Monitor logs:**
```bash
tail -f logs/app.log | grep "Mapped agent_id"
```

---

## **🚀 Ưu điểm của giải pháp mới:**

✅ **Không cần sửa code**  
✅ **Không cần restart service**  
✅ **Dễ quản lý nhiều agent**  
✅ **Backup/restore dễ dàng**  
✅ **Test mapping trước khi dùng**  
✅ **Logs chi tiết**  

---

## **📞 Hỗ trợ:**

Nếu gặp vấn đề:
1. Kiểm tra logs: `tail -f logs/app.log`
2. Test mapping: `python manage_agent_mapping.py test --onpremise-id "agent_id"`
3. Reload config: `python manage_agent_mapping.py reload`
4. Kiểm tra file JSON có đúng format không 