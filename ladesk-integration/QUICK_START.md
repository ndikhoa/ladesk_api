# 🚀 Quick Start Guide - Contact Management

## Vấn đề đã được giải quyết

### ❌ Trước đây:
- Tất cả ticket đều có `useridentifier: "agent@ladesk.com"`
- Khó phân biệt khách hàng
- Không có thông tin khách hàng trong ticket

### ✅ Bây giờ:
- Mỗi khách hàng có contact riêng
- Sử dụng tên khách hàng làm useridentifier (ví dụ: `Nguyễn Duy Khoa`, `Trần Thị A`)
- Thông tin khách hàng đầy đủ trong nội dung ticket
- Dễ dàng phân biệt và quản lý khách hàng

## Cách hoạt động mới

### 1. Khi có tin nhắn từ Facebook:
```
Facebook → Ladesk Cloud → Webhook → Integration API
                                    ↓
                              Tìm/Tạo Contact
                                    ↓
                              Tạo Ticket với Contact ID
                                    ↓
                              Ladesk On-Premise
```

### 2. Thông tin trong ticket:
```
[Nội dung tin nhắn từ khách hàng]
```
*Tên khách hàng sẽ hiển thị ở useridentifier, không cần thêm thông tin trong nội dung*

## Test nhanh

### 1. Khởi động API:
```bash
python run.py
```

### 2. Test health check:
```bash
curl http://localhost:3000/health
```

### 3. Test tạo contact:
```bash
curl -X POST http://localhost:3000/test/create-contact \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Nguyễn Văn Test",
    "customer_email": "nguyenvantest@facebook.com",
    "facebook_id": "123456789",
    "message": "Xin chào, tôi cần hỗ trợ",
    "subject": "Yêu cầu hỗ trợ"
  }'
```

### 4. Chạy script test đầy đủ:
```bash
python test_contact.py
```

## Kiểm tra kết quả

### 1. Trong Ladesk On-Premise:
- Vào phần **Contacts** - sẽ thấy contact mới được tạo
- Vào phần **Tickets** - sẽ thấy ticket với email khách hàng (ví dụ: `90f8q9h4@facebook.com`) thay vì email cố định
- Nội dung ticket chỉ có message gốc từ Facebook

### 2. Trong logs:
```bash
tail -f logs/app.log
```

### 3. Trong database:
```bash
sqlite3 ladesk_integration.db
SELECT * FROM ticket_mapping ORDER BY created_at DESC LIMIT 5;
```

## Cấu hình webhook

### Ladesk Cloud Webhook:
```
URL: http://your-server:3000/webhook/ladesk-cloud
Method: POST
Content-Type: application/json
```

### Ladesk On-Premise Webhook:
```
URL: http://your-server:3000/webhook/ladesk-onpremise
Method: POST
Content-Type: application/json
```

## Troubleshooting

### Contact không được tạo:
- Kiểm tra API key On-Premise
- Kiểm tra URL On-Premise
- Xem logs: `logs/app.log`

### Ticket không được tạo:
- Kiểm tra department ID
- Kiểm tra quyền API
- Kiểm tra contact ID

### Mapping không tìm thấy:
- Kiểm tra database connection
- Kiểm tra conversation_id/ticket_id

## Lợi ích

1. **Phân biệt khách hàng**: Mỗi khách hàng có contact riêng
2. **Thông tin đầy đủ**: Tên, email, Facebook ID trong ticket
3. **Quản lý dễ dàng**: Có thể xem lịch sử contact
4. **Tìm kiếm nhanh**: Tìm theo contact ID hoặc email
5. **Báo cáo chính xác**: Thống kê theo từng khách hàng

## Next Steps

1. Test với webhook thực từ Ladesk Cloud
2. Cấu hình webhook trong On-Premise
3. Monitor logs để đảm bảo hoạt động ổn định
4. Tùy chỉnh thông tin khách hàng theo nhu cầu 