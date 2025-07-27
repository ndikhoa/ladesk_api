# Ladesk Integration API

API tích hợp giữa Ladesk Cloud (có liên kết Facebook) và Ladesk On-Premise để đồng bộ ticket và message.

## Tính năng chính

### 1. Webhook từ Ladesk Cloud
- Nhận webhook khi có ticket mới từ Facebook (message hoặc comment)
- Tự động tạo contact cho khách hàng Facebook
- **Xử lý đặc biệt cho comment**: Logic đã được cải thiện để lấy thông tin khách hàng thực
- Tạo ticket trong On-Premise với thông tin khách hàng đầy đủ
- Đồng bộ conversation giữa Cloud và On-Premise

### 4. Xử lý Comment Facebook (CẬP NHẬT)
- **Logic mới**: Tìm message cuối cùng từ khách hàng thực (không phải system/bot)
- **Ưu tiên tên thật**: Sử dụng `commenter_name`, `author_name` từ webhook nếu có
- **Fallback**: Tạo tên "Facebook User {userid}" nếu không có tên thật
- **Vấn đề hiện tại**: Webhook thực tế từ Ladesk Cloud không gửi `commenter_name`/`author_name`
- **Cần cấu hình**: Webhook rules trong Ladesk Cloud để gửi thêm thông tin tên thật

### 2. Webhook từ Ladesk On-Premise  
- Nhận webhook khi agent reply trong On-Premise
- Gửi reply về Ladesk Cloud để khách hàng nhận được

### 3. Quản lý Contact
- Tự động tạo contact mới cho mỗi khách hàng Facebook
- Tìm và sử dụng contact hiện có nếu đã tồn tại
- Sử dụng email khách hàng làm useridentifier để phân biệt khách hàng

## Vấn đề hiện tại và Giải pháp

### Vấn đề: Comment hiển thị "Facebook User {userid}" thay vì tên thật

**Nguyên nhân:**
- Webhook thực tế từ Ladesk Cloud không gửi trường `commenter_name` hoặc `author_name`
- Logic đã hoạt động đúng, nhưng không có dữ liệu tên thật để sử dụng

**Giải pháp cần thực hiện:**
1. **Cấu hình Webhook Rules trong Ladesk Cloud**:
   - Vào Settings > Webhook Rules
   - Thêm trường `commenter_name`, `author_name` vào webhook payload
   - Đảm bảo webhook gửi thông tin tên thật của người comment

2. **Test lại**:
   - Tạo comment mới trên Facebook
   - Kiểm tra webhook có gửi `commenter_name` không
   - Xác nhận ticket hiển thị tên thật

**Trạng thái hiện tại:**
- ✅ Logic xử lý comment đã hoạt động
- ✅ Tìm được userid chính xác từ message cuối cùng
- ✅ Tạo ticket thành công với email khách hàng
- ❌ Thiếu thông tin tên thật từ webhook

## Cấu hình

### Environment Variables
```env
# Ladesk Cloud Configuration
LADESK_CLOUD_API_KEY_V1=your_cloud_api_key_v1
LADESK_CLOUD_API_KEY_V3=your_cloud_api_key_v3
LADESK_CLOUD_BASE_URL_V1=https://social.ladesk.com/api
LADESK_CLOUD_BASE_URL_V3=https://social.ladesk.com/api/v3
LADESK_CLOUD_USER_IDENTIFIER=your_user_identifier
FACEBOOK_DEPARTMENT_CLOUD=your_facebook_department_id

# Ladesk On-Premise Configuration
LADESK_ONPREMISE_API_KEY_V1=your_onpremise_api_key_v1
LADESK_ONPREMISE_API_KEY_V3=your_onpremise_api_key_v3
LADESK_ONPREMISE_BASE_URL_V1=https://your-onpremise.ladesk.com/api
LADESK_ONPREMISE_BASE_URL_V3=https://your-onpremise.ladesk.com/api/v3
LADESK_ONPREMISE_USER_IDENTIFIER=your_user_identifier
FACEBOOK_DEPARTMENT_ONPREMISE=your_facebook_department_id
```

## API Endpoints

### Health Check
```
GET /health
```

### Webhook từ Ladesk Cloud
```
POST /webhook/ladesk-cloud
```

**Request Body:**
```json
{
  "conversation_id": "conversation_id_from_cloud",
  "message": "Nội dung tin nhắn",
  "customer_info": {
    "name": "Tên khách hàng",
    "email": "email@example.com",
    "contact_id": "facebook_id"
  }
}
```

### Webhook từ Ladesk On-Premise
```
POST /webhook/ladesk-onpremise
```

**Request Body:**
```json
{
  "ticket_id": "ticket_id_from_onpremise",
  "message": "Reply từ agent",
  "agent_info": {
    "agent_id": "agent_identifier"
  }
}
```

### Test Endpoints

#### Test tạo Contact và Ticket
```
POST /test/create-contact
```

**Request Body:**
```json
{
  "customer_name": "Nguyễn Văn A",
  "customer_email": "nguyenvana@facebook.com",
  "facebook_id": "123456789",
  "message": "Xin chào, tôi cần hỗ trợ",
  "subject": "Yêu cầu hỗ trợ"
}
```

#### Test Comment Webhook (với tên thật)
```
POST /test/comment-webhook
```

**Request Body:**
```json
{
  "conversation_id": "k6nko1eq",
  "message": "test comment với tên thật",
  "commenter_name": "Nguyễn Văn Comment",
  "author_name": "Nguyễn Văn Comment"
}
```

#### Test Conversation Details
```
GET /test/conversation-details/<conversation_id>
```

**Response:** Chi tiết conversation và messages từ Ladesk Cloud API

### Test Comment Webhook
```
POST /test/comment-webhook
```

**Request Body:**
```json
{
  "conversation_id": "test_comment_123",
  "message": "Bình luận thì sao nữa",
  "commenter_name": "Nguyễn Văn Comment",
  "commenter_id": "123456789",
  "subject": "Facebook Comment"
}
```

## Cách hoạt động

### 1. Khi có tin nhắn mới từ Facebook:
1. Webhook từ Ladesk Cloud được gọi
2. API lấy thông tin chi tiết conversation từ Cloud
3. Tìm hoặc tạo contact mới cho khách hàng
4. Tạo ticket trong On-Premise với:
   - Email khách hàng làm useridentifier
   - Message gốc từ Facebook (không thêm thông tin khách hàng)
   - Subject và message từ Facebook
5. Lưu mapping giữa conversation ID và ticket ID

### 2. Khi agent reply trong On-Premise:
1. Webhook từ On-Premise được gọi
2. Tìm mapping bằng ticket ID hoặc conversation ID
3. Gửi reply về Ladesk Cloud
4. Khách hàng nhận được tin nhắn trên Facebook

## Lợi ích của việc sử dụng Contact

### Trước đây:
- Tất cả ticket đều có `useridentifier: "agent@ladesk.com"`
- Khó phân biệt khách hàng
- Không có thông tin khách hàng trong ticket

### Bây giờ:
- Mỗi khách hàng có contact riêng
- Sử dụng email khách hàng làm useridentifier (ví dụ: `90f8q9h4@facebook.com`, `contact1@facebook.com`)
- Message gốc từ Facebook (không thêm thông tin khách hàng)
- Dễ dàng phân biệt và quản lý khách hàng

## Cài đặt và chạy

1. Clone repository
2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Cấu hình environment variables trong file `.env`

4. Chạy ứng dụng:
```bash
python run.py
```

## Logs

Logs được lưu trong thư mục `logs/app.log` với các thông tin:
- Webhook requests
- Contact creation/tìm kiếm
- Ticket creation
- Error handling

## Troubleshooting

### Vấn đề thường gặp:
1. **Contact không được tạo**: Kiểm tra API key và URL On-Premise
2. **Ticket không được tạo**: Kiểm tra department ID và quyền API
3. **Mapping không tìm thấy**: Kiểm tra database connection

### Debug:
- Sử dụng endpoint `/health` để kiểm tra trạng thái
- Xem logs trong `logs/app.log`
- Test với endpoint `/test/create-contact` 