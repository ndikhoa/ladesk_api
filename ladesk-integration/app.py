import os
import json
import logging
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from config import Config
from database import db

# Tạo thư mục logs với đường dẫn tuyệt đối
LOG_DIR = r'D:\ladesk-integration-api\ladesk-integration\logs'
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Tạo thư mục logs nếu chưa tồn tại
os.makedirs(LOG_DIR, exist_ok=True)

# Xóa tất cả handlers hiện tại để tránh duplicate logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Cấu hình logging với đường dẫn cụ thể
logging.basicConfig(
    level=getattr(logging, getattr(Config, 'LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Tạo logger cho module này
logger = logging.getLogger(__name__)

# Test log để kiểm tra
logger.info(f"Logger initialized. Log file: {LOG_FILE}")
logger.info(f"Log directory created: {LOG_DIR}")

app = Flask(__name__)
app.config.from_object(Config)

class LadeskCloudAPI:
    """Class để tương tác với Ladesk Cloud (có liên kết Facebook)"""
    
    def __init__(self):
        # API v3 cho tạo ticket và lấy thông tin
        self.api_key_v3 = Config.LADESK_CLOUD_API_KEY_V3
        self.base_url_v3 = Config.LADESK_CLOUD_BASE_URL_V3
        
        # API v1 cho gửi reply
        self.api_key_v1 = Config.LADESK_CLOUD_API_KEY_V1
        self.base_url_v1 = Config.LADESK_CLOUD_BASE_URL_V1
        
        self.user_identifier = Config.LADESK_CLOUD_USER_IDENTIFIER
    
    def get_conversation_details(self, conversation_id: str) -> dict:
        """Lấy chi tiết conversation từ Ladesk Cloud - API v1"""
        try:
            url = f"{self.base_url_v1}/conversations/{conversation_id}"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Retrieved conversation details from Cloud API v1 for {conversation_id}")
            return {
                "status": "success",
                "data": response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting conversation details from Cloud API v1: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_conversation_messages(self, conversation_id: str) -> dict:
        """Lấy messages của conversation từ Ladesk Cloud - API v1"""
        try:
            url = f"{self.base_url_v1}/conversations/{conversation_id}/messages"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Retrieved messages from Cloud API v1 for {conversation_id}")
            return {
                "status": "success",
                "data": response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting messages from Cloud API v1: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_reply(self, conversation_id: str, message: str, user_identifier: str = None) -> dict:
        """Gửi reply message đến Ladesk Cloud - API v1 (endpoint đúng cho Facebook)"""
        try:
            # Sử dụng API v1 với endpoint đúng cho reply
            url = f"{self.base_url_v1}/conversations/{conversation_id}/messages"
            
            # Sử dụng form data thay vì JSON
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'message': message,
                'type': 'M',  # M cho message
                'useridentifier': user_identifier or self.user_identifier
            }
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            # Xử lý response - có thể rỗng
            try:
                if response.text.strip():
                    result = response.json()
                    if result.get('response', {}).get('status') == 'OK':
                        logger.info(f"Reply sent successfully to Cloud API v1 conversation {conversation_id}")
                        return {
                            "status": "success",
                            "data": result
                        }
                    else:
                        logger.error(f"API returned error: {result}")
                        return {
                            "status": "error",
                            "message": f"API error: {result}"
                        }
                else:
                    # Response rỗng - coi như thành công
                    logger.info(f"Empty response from Cloud API v1, treating as success")
                    return {
                        "status": "success",
                        "data": {
                            "message": "Reply sent successfully",
                            "response_status": response.status_code
                        }
                    }
            except Exception as e:
                logger.warning(f"Response parsing failed: {e}")
                # Vẫn coi là thành công nếu status code là 200
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "data": {
                            "message": "Reply sent successfully",
                            "parsing_error": str(e)
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Response parsing failed: {e}"
                    }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending reply to Cloud API v1: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

class LadeskOnPremiseAPI:
    """Class để tương tác với Ladesk On-Premise (nơi Agent làm việc)"""
    
    def __init__(self):
        # API v3 cho tạo ticket và lấy thông tin
        self.api_key_v3 = Config.LADESK_ONPREMISE_API_KEY_V3
        self.base_url_v3 = Config.LADESK_ONPREMISE_BASE_URL_V3
        
        # API v1 cho gửi reply
        self.api_key_v1 = Config.LADESK_ONPREMISE_API_KEY_V1
        self.base_url_v1 = Config.LADESK_ONPREMISE_BASE_URL_V1
    
    def create_contact(self, contact_data: dict) -> dict:
        """Tạo contact mới trong On-Premise system sử dụng API v3"""
        try:
            url = f"{self.base_url_v3}/contacts"
            
            headers = {
                'apikey': self.api_key_v3,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Creating contact in On-Premise with URL: {url}")
            logger.info(f"Contact data: {contact_data}")
            
            response = requests.post(url, headers=headers, json=contact_data, timeout=30)
            
            logger.info(f"Contact creation response status: {response.status_code}")
            logger.info(f"Contact creation response text: {response.text}")
            
            # Nếu thành công (200, 201, 202)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Contact created successfully in On-Premise with API v3")
                
                # Xử lý response
                try:
                    if response.text.strip():
                        response_data = response.json()
                        return {
                            "status": "success",
                            "data": response_data
                        }
                    else:
                        # Response rỗng - vẫn coi là thành công
                        logger.info(f"Empty response for contact creation, treating as success")
                        return {
                            "status": "success",
                            "data": {
                                "message": "Contact created successfully",
                                "response_status": response.status_code
                            }
                        }
                except Exception as e:
                    logger.warning(f"Contact creation response parsing failed: {e}")
                    return {
                        "status": "success",
                        "data": {
                            "message": "Contact created successfully",
                            "parsing_error": str(e)
                        }
                    }
            
            # Nếu lỗi
            else:
                logger.error(f"Failed to create contact. Status: {response.status_code}, Response: {response.text}")
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
            
        except Exception as e:
            logger.error(f"Error creating contact in On-Premise: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_contact_by_email(self, email: str) -> dict:
        """Tìm contact theo email trong On-Premise system"""
        try:
            url = f"{self.base_url_v3}/contacts"
            
            headers = {
                'apikey': self.api_key_v3,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            contacts = response.json()
            
            # Tìm contact có email trùng khớp
            for contact in contacts:
                if contact.get('emails') and email in contact['emails']:
                    logger.info(f"Found existing contact with email {email}: {contact['id']}")
                    return {
                        "status": "success",
                        "data": contact
                    }
            
            logger.info(f"No existing contact found with email {email}")
            return {
                "status": "not_found",
                "message": f"No contact found with email {email}"
            }
            
        except Exception as e:
            logger.error(f"Error getting contact by email: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_ticket(self, ticket_data: dict) -> dict:
        """Tạo ticket trong On-Premise system sử dụng API v3"""
        try:
            # Sử dụng API v3 cho tạo ticket
            url = f"{self.base_url_v3}/tickets"
            
            headers = {
                'apikey': self.api_key_v3,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Creating ticket in On-Premise with URL: {url}")
            logger.info(f"API Key: {self.api_key_v3[:10]}...")
            logger.info(f"Ticket data: {ticket_data}")
            
            response = requests.post(url, headers=headers, json=ticket_data, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response text: {response.text}")
            
            # Nếu thành công (200, 201, 202)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Ticket created successfully in On-Premise with API v3")
                
                # Xử lý response
                try:
                    if response.text.strip():
                        response_data = response.json()
                        return {
                            "status": "success",
                            "data": response_data
                        }
                    else:
                        # Response rỗng - vẫn coi là thành công
                        logger.info(f"Empty response, treating as success")
                        return {
                            "status": "success",
                            "data": {
                                "message": "Ticket created successfully",
                                "response_status": response.status_code
                            }
                        }
                except Exception as e:
                    logger.warning(f"Response parsing failed: {e}")
                    return {
                        "status": "success",
                        "data": {
                            "message": "Ticket created successfully",
                            "parsing_error": str(e)
                        }
                    }
            
            # Nếu lỗi
            else:
                logger.error(f"Failed to create ticket. Status: {response.status_code}, Response: {response.text}")
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
            
        except Exception as e:
            logger.error(f"Error creating ticket in On-Premise: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_reply(self, ticket_id: str, message: str, agent_id: str = None) -> dict:
        """Gửi reply trong On-Premise system sử dụng API v1"""
        try:
            # Sử dụng API v1 cho reply
            url = f"{self.base_url_v1}/conversations/{ticket_id}/messages"
            payload = {
                "message": message,
                "agent_id": agent_id
            }
            
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Reply sent successfully in On-Premise ticket {ticket_id}")
            return {
                "status": "success",
                "data": response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending reply in On-Premise: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_ticket_details(self, ticket_id: str) -> dict:
        """Lấy chi tiết ticket từ On-Premise - API v3"""
        try:
            url = f"{self.base_url_v3}/tickets/{ticket_id}"
            headers = {
                'apikey': self.api_key_v3,
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "data": response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting ticket details from On-Premise: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# Khởi tạo API clients
cloud_api = LadeskCloudAPI()
onpremise_api = LadeskOnPremiseAPI()

def parse_webhook_data(request):
    """Parse webhook data từ nhiều format khác nhau"""
    raw_data = request.get_data(as_text=True)
    logger.info(f"Raw webhook data: {raw_data}")
    logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
    
    # Try JSON first
    try:
        data = request.get_json()
        if data:
            logger.info(f"Successfully parsed as JSON: {data}")
            return data
    except Exception as e:
        logger.info(f"JSON parsing failed: {e}")
    
    # Try to fix escaped JSON and parse manually
    try:
        if raw_data and raw_data.strip().startswith('{'):
            # Fix double escaped quotes - replace "" with "
            fixed_data = raw_data.replace('""', '"')
            # Also fix escaped quotes in the middle of strings
            fixed_data = fixed_data.replace('" "', ' ')
            # Remove outer quotes if present
            if fixed_data.startswith('"') and fixed_data.endswith('"'):
                fixed_data = fixed_data[1:-1]
            # Parse the fixed JSON
            import json
            data = json.loads(fixed_data)
            logger.info(f"Successfully parsed fixed JSON: {data}")
            return data
    except Exception as e:
        logger.info(f"Fixed JSON parsing failed: {e}")
        
        # Try more aggressive fixing
        try:
            if raw_data and raw_data.strip().startswith('{'):
                # More aggressive quote fixing
                fixed_data = raw_data
                # Replace all double quotes with single quotes
                fixed_data = fixed_data.replace('""', '"')
                # Fix spaces between quotes
                fixed_data = fixed_data.replace('" "', ' ')
                # Remove any remaining problematic patterns
                fixed_data = fixed_data.replace('""', '"')
                
                # Try to parse
                import json
                data = json.loads(fixed_data)
                logger.info(f"Successfully parsed with aggressive fixing: {data}")
                return data
        except Exception as e2:
            logger.info(f"Aggressive JSON fixing also failed: {e2}")
    
    # Try form data
    try:
        form_data = request.form.to_dict()
        if form_data:
            logger.info(f"Successfully parsed as form data: {form_data}")
            return form_data
    except Exception as e:
        logger.info(f"Form data parsing failed: {e}")
    
    # Try URL-encoded data
    try:
        if raw_data and '=' in raw_data:
            pairs = raw_data.split('&')
            parsed_data = {}
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed_data[key] = value
            if parsed_data:
                logger.info(f"Successfully parsed as URL-encoded: {parsed_data}")
                return parsed_data
    except Exception as e:
        logger.info(f"URL-encoded parsing failed: {e}")
    
    # If all parsing methods fail, return raw data as string
    logger.warning(f"All parsing methods failed, returning raw data: {raw_data}")
    return {"raw_data": raw_data}

def generate_ticket_id() -> str:
    """Tạo ticket ID duy nhất"""
    return f"TICKET-{uuid.uuid4().hex[:8].upper()}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Kiểm tra database connection
        mappings = db.get_all_mappings()
        logger.info("Health check performed successfully")
        return jsonify({
            "status": "OK",
            "message": "Service is running",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_mappings": len(mappings),
            "cloud_api": "configured",
            "onpremise_api": "configured",
            "log_file": LOG_FILE
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route('/webhook/ladesk-cloud', methods=['POST'])
def ladesk_cloud_webhook():
    """Webhook endpoint để nhận data từ Ladesk Cloud (có liên kết Facebook)"""
    try:
        # Parse webhook data
        data = parse_webhook_data(request)
        logger.info(f"Parsed webhook data from Cloud: {data}")
        
        # Log webhook
        db.log_webhook('cloud_incoming', data)
        
        # Validate required fields
        required_fields = ['conversation_id']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({
                    "status": "ERROR",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Kiểm tra message_type để tránh loop
        message_type = data.get('message_type', 'unknown')
        if message_type == 'agent_reply':
            logger.info(f"Ignoring agent reply from Cloud to avoid loop")
            return jsonify({
                "status": "OK",
                "message": "Agent reply ignored to avoid loop"
            }), 200
        
        conversation_id = data['conversation_id']
        event_type = data.get('event_type', 'ticket_created')
        message = data.get('message', '')
        customer_info = data.get('customer_info', {})
        
        # Nếu không có customer_info, tạo từ data gốc
        if not customer_info:
            customer_info = {
                'name': data.get('customer_name', ''),
                'email': data.get('customer_email', ''),
                'phone': data.get('customer_phone', ''),
                'contact_id': data.get('contact_id', ''),
                'ticket_id': data.get('ticket_id', ''),
                'status': data.get('status', ''),
                'channel_type': data.get('channel_type', ''),
                'created_at': data.get('created_time', ''),
                'department': data.get('department', ''),
                'subject': data.get('subject', '')
            }
        
        # Xử lý đặc biệt cho comment - lấy thông tin khách hàng từ conversation details
        event_type = data.get('event_type', 'ticket_created')
        message_type = data.get('message_type', '')
        channel_type = data.get('channel_type', '')
        
        # Phát hiện comment dựa trên nhiều tiêu chí
        is_comment = (
            event_type in ['comment_added', 'post_comment'] or 
            'comment' in event_type.lower() or
            message_type == 'C' or  # C = Comment
            (customer_info.get('name') and 'fanpage' in customer_info.get('name', '').lower()) or
            (customer_info.get('name') and customer_info.get('name').lower() in ['demo ladesk', 'facebook fanpage', 'page'])
        )
        
        if is_comment:
            logger.info(f"Detected comment event: {event_type}, message_type: {message_type}, customer_name: {customer_info.get('name')}")
            # Với comment, customer_name có thể là tên fanpage, cần lấy từ conversation details
            if customer_info.get('name') and ('fanpage' in customer_info.get('name', '').lower() or 
                                            customer_info.get('name').lower() in ['demo ladesk', 'facebook fanpage', 'page']):
                logger.info(f"Customer name appears to be fanpage name: {customer_info.get('name')}")
                # Sẽ cập nhật customer_info sau khi lấy conversation details
        
        # BƯỚC 1: Lấy chi tiết conversation từ Ladesk Cloud
        conversation_details = cloud_api.get_conversation_details(conversation_id)
        if conversation_details['status'] == 'success':
            # Cập nhật customer_info với data từ Cloud
            cloud_data = conversation_details['data'].get('response', {})
            if cloud_data:
                # Log toàn bộ conversation details để debug
                logger.info(f"Conversation details data: {cloud_data}")
                
                customer_info.update({
                    'ladesk_cloud_ticket_id': cloud_data.get('code'),
                    'status': cloud_data.get('status'),
                    'channel_type': cloud_data.get('channel_type'),
                    'created_at': cloud_data.get('datecreated'),
                    'department': cloud_data.get('departmentname'),
                    'subject': cloud_data.get('subject'),
                    'preview': cloud_data.get('preview'),
                    'source': 'facebook'
                })
                
                # Xử lý đặc biệt cho comment - lấy thông tin khách hàng thực
                if is_comment:
                    # Lưu ý: ownername trong conversation details thường là tên fanpage, không phải tên khách hàng
                    # Thông tin khách hàng thực sẽ được lấy từ messages
                    logger.info(f"Comment detected - ownername from conversation: {cloud_data.get('ownername')}")
                    
                    # Lấy contact_id từ conversation nếu có
                    conversation_contact_id = cloud_data.get('contact_id')
                    if conversation_contact_id and conversation_contact_id != customer_info.get('contact_id'):
                        customer_info['contact_id'] = conversation_contact_id
                        logger.info(f"Updated contact ID from conversation: {conversation_contact_id}")
                
                logger.info(f"Retrieved conversation details from Cloud for {conversation_id}")
        else:
            logger.warning(f"Failed to get conversation details from Cloud: {conversation_details.get('message', 'Unknown error')}")
        
        # BƯỚC 1.5: Lấy messages để có thông tin chi tiết
        messages_details = cloud_api.get_conversation_messages(conversation_id)
        if messages_details['status'] == 'success':
            messages_data = messages_details['data'].get('response', {}).get('groups', [])
            # Log toàn bộ messages data để debug
            logger.info(f"Messages data: {messages_details['data'].get('response', {})}")
            if messages_data:
                # Lấy message cuối cùng
                latest_message = None
                for group in messages_data:
                    if group.get('messages'):
                        latest_message = group['messages'][-1]
                        break
                
                if latest_message:
                    customer_info.update({
                        'latest_message': latest_message.get('message'),
                        'latest_message_id': latest_message.get('messageid'),
                        'latest_message_type': latest_message.get('rtype'),
                        'latest_message_date': latest_message.get('datecreated')
                    })
                    
                    # Xử lý đặc biệt cho comment - lấy thông tin khách hàng từ message
                    if is_comment:
                        # Tìm message của người comment thực sự (không phải system message)
                        comment_message = None
                        comment_userid = None
                        
                        # Duyệt qua tất cả messages để tìm message comment thực sự (từ cuối lên)
                        for group in reversed(messages_data):
                            if group.get('messages'):
                                for msg in reversed(group['messages']):
                                    # Tìm message có rtype = 'M' (message) và không phải system
                                    if (msg.get('rtype') == 'M' and 
                                        msg.get('userid') and 
                                        msg.get('userid') != 'system00' and
                                        msg.get('userid') != 'bl3krpc4' and  # Bot ID
                                        msg.get('userid') != '4aldh82o' and  # Bot ID
                                        msg.get('userid') != 'l5agmqlp'):    # Bot ID
                                        
                                        comment_message = msg
                                        comment_userid = msg.get('userid')
                                        logger.info(f"Found comment message from userid: {comment_userid}")
                                        break
                                if comment_message:
                                    break
                        
                        # Nếu không tìm thấy, lấy message cuối cùng không phải system
                        if not comment_message:
                            for group in reversed(messages_data):
                                if group.get('messages'):
                                    for msg in reversed(group['messages']):
                                        if (msg.get('userid') and 
                                            msg.get('userid') != 'system00' and
                                            msg.get('userid') != 'bl3krpc4' and
                                            msg.get('userid') != '4aldh82o'):
                                            
                                            comment_message = msg
                                            comment_userid = msg.get('userid')
                                            logger.info(f"Found fallback comment message from userid: {comment_userid}")
                                            break
                                    if comment_message:
                                        break
                        
                        # Cập nhật thông tin từ message comment thực sự
                        if comment_userid:
                            # Cập nhật contact_id từ userid
                            if comment_userid != customer_info.get('contact_id'):
                                customer_info['contact_id'] = comment_userid
                                logger.info(f"Updated contact ID from comment userid: {comment_userid}")
                            
                            # Ưu tiên sử dụng tên thật từ webhook data (giống logic direct messages)
                            real_customer_name = (
                                data.get('commenter_name') or 
                                data.get('author_name') or 
                                data.get('customer_name') or
                                customer_info.get('commenter_name') or
                                customer_info.get('author_name')
                            )
                            
                            # Nếu có tên thật và không phải tên fanpage, sử dụng tên thật
                            if (real_customer_name and 
                                real_customer_name.lower() not in ['demo ladesk', 'facebook fanpage', 'page'] and
                                real_customer_name != customer_info.get('name')):
                                
                                customer_info['name'] = real_customer_name
                                logger.info(f"Using real customer name from webhook: {real_customer_name}")
                            # Fallback: tạo tên từ userid nếu không có tên thật
                            elif not customer_info.get('name') or customer_info.get('name').lower() in ['demo ladesk', 'facebook fanpage', 'page']:
                                customer_info['name'] = f"Facebook User {comment_userid}"
                                logger.info(f"Generated customer name from comment userid: {customer_info['name']}")
                        
                        # Fallback: thử lấy từ các trường khác nếu có
                        if not customer_info.get('name') or customer_info.get('name').lower() in ['demo ladesk', 'facebook fanpage', 'page']:
                            message_author = (
                                latest_message.get('author_name') or 
                                latest_message.get('user_name') or 
                                latest_message.get('contact_name') or
                                latest_message.get('from_name') or
                                latest_message.get('sender_name')
                            )
                            message_author_id = (
                                latest_message.get('author_id') or 
                                latest_message.get('user_id') or 
                                latest_message.get('contact_id') or
                                latest_message.get('from_id') or
                                latest_message.get('sender_id')
                            )
                            
                            if message_author and message_author != customer_info.get('name'):
                                customer_info['name'] = message_author
                                logger.info(f"Updated customer name from message: {message_author}")
                            
                            if message_author_id and message_author_id != customer_info.get('contact_id'):
                                customer_info['contact_id'] = message_author_id
                                logger.info(f"Updated contact ID from message: {message_author_id}")
                            
                            # Nếu vẫn không có tên khách hàng, tạo từ contact_id
                            if not message_author and customer_info.get('contact_id'):
                                contact_id = customer_info.get('contact_id')
                                if contact_id and contact_id != customer_info.get('name'):
                                    customer_info['name'] = f"Facebook User {contact_id}"
                                    logger.info(f"Generated customer name from contact ID in message: {customer_info['name']}")
        else:
            logger.warning(f"Failed to get messages from Cloud: {messages_details.get('message', 'Unknown error')}")
        
        # BƯỚC 2: Tạo ticket ID nội bộ
        ticket_id = generate_ticket_id()
        
        # BƯỚC 2.5: Xử lý contact - tạo hoặc tìm contact hiện có
        contact_id = None
        customer_email = customer_info.get('email', '')
        customer_name = customer_info.get('name', 'Facebook Customer')
        
        # Tạo email từ Facebook ID nếu không có email
        if not customer_email:
            facebook_id = customer_info.get('contact_id', '')
            if facebook_id:
                customer_email = f"{facebook_id}@facebook.com"
                logger.info(f"Generated email from Facebook ID: {customer_email}")
            else:
                customer_email = f"facebook_customer_{uuid.uuid4().hex[:8]}@facebook.com"
                logger.info(f"Generated random email: {customer_email}")
        
        # Log thông tin khách hàng cuối cùng
        logger.info(f"Final customer info - Name: {customer_name}, Email: {customer_email}, Contact ID: {customer_info.get('contact_id', 'N/A')}")
        
        # Fallback cuối cùng: nếu vẫn là tên fanpage, tạo tên từ contact_id
        if is_comment and customer_name.lower() in ['demo ladesk', 'facebook fanpage', 'page'] and customer_info.get('contact_id'):
            contact_id = customer_info.get('contact_id')
            customer_name = f"Facebook User {contact_id}"
            logger.info(f"Final fallback - Generated customer name: {customer_name}")
        
        # Fallback cuối cùng: nếu vẫn là tên fanpage, tạo tên từ contact_id
        if is_comment and customer_name.lower() in ['demo ladesk', 'facebook fanpage', 'page'] and customer_info.get('contact_id'):
            contact_id = customer_info.get('contact_id')
            customer_name = f"Facebook User {contact_id}"
            logger.info(f"Final fallback - Generated customer name: {customer_name}")
        
        # Tìm contact hiện có
        existing_contact = onpremise_api.get_contact_by_email(customer_email)
        
        if existing_contact['status'] == 'success':
            # Sử dụng contact hiện có
            contact_id = existing_contact['data']['id']
            logger.info(f"Using existing contact: {contact_id}")
        else:
            # Tạo contact mới
            contact_data = {
                "firstname": customer_name.split()[0] if customer_name else "Facebook",
                "lastname": " ".join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else "Customer",
                "emails": [customer_email],
                "description": f"Facebook Customer - {customer_name}",
                "type": "V"  # V = Visitor
            }
            
            contact_result = onpremise_api.create_contact(contact_data)
            if contact_result['status'] == 'success':
                contact_id = contact_result['data'].get('id')
                logger.info(f"Created new contact: {contact_id}")
            else:
                logger.warning(f"Failed to create contact: {contact_result['message']}")
                # Fallback: sử dụng email thay vì contact ID
                contact_id = None
        
        # BƯỚC 3: Tạo nội dung ticket với thông tin khách hàng
        # customer_info_text = f"""
        # === THÔNG TIN KHÁCH HÀNG ===
        # Tên: {customer_name}
        # Email: {customer_email}
        # Facebook ID: {customer_info.get('contact_id', 'N/A')}
        # Nguồn: Facebook Fanpage
        # Thời gian tạo: {customer_info.get('created_at', 'N/A')}
        # ========================
        # 
        # """
        
        # full_message = customer_info_text + message
        full_message = message  # Chỉ sử dụng message gốc, không thêm thông tin khách hàng
        
        # BƯỚC 4: Tạo ticket trong On-Premise system
        # Sử dụng API v3 format với email khách hàng làm useridentifier
        onpremise_ticket_data = {
            "departmentid": Config.FACEBOOK_DEPARTMENT_ONPREMISE,  # Sử dụng department ID từ config
            "subject": customer_info.get('subject', 'Facebook Message'),
            "message": full_message,
            "contactemail": customer_email,
            "contactname": customer_name,
            "useridentifier": customer_email,  # Sử dụng email khách hàng làm useridentifier
            "recipient": "support@mail.social-on-premise.ladesk.com",  # Email support của On-Premise
            "status": "N",  # N = New
            "channel_type": "E"  # E = Email (thay vì F = Facebook)
        }
        
        logger.info(f"Creating ticket with API v3 format: {onpremise_ticket_data}")
        
        onpremise_result = onpremise_api.create_ticket(onpremise_ticket_data)
        logger.info(f"On-Premise API v3 response: {onpremise_result}")
        
        if onpremise_result['status'] == 'success':
            # API v3 trả về ticket ID trong response
            response_data = onpremise_result['data']
            onpremise_ticket_id = response_data.get('id') or response_data.get('code')
            
            # Nếu không có ticket ID từ API, sử dụng ticket ID nội bộ
            if not onpremise_ticket_id:
                logger.warning(f"On-Premise API returned success but no ticket ID. Using internal ticket ID: {ticket_id}")
                onpremise_ticket_id = ticket_id
            
            onpremise_success = True
            logger.info(f"Ticket created successfully in On-Premise with ID: {onpremise_ticket_id}")
        else:
            logger.error(f"Failed to create ticket in On-Premise: {onpremise_result['message']}")
            onpremise_success = False
            onpremise_ticket_id = None
        
        # BƯỚC 4: Lưu mapping vào database
        success = db.create_ticket_mapping(
            ladesk_conversation_id=conversation_id,
            onpremise_ticket_id=ticket_id,
            customer_info=customer_info
        )
        
        if not success:
            logger.warning(f"Failed to create ticket mapping for conversation {conversation_id}")
        
        logger.info(f"Cloud webhook processed successfully. Ticket ID: {ticket_id}, Contact ID: {contact_id}")
        
        return jsonify({
            "status": "OK",
            "message": "Cloud webhook received and processed",
            "ticket_id": ticket_id,
            "conversation_id": conversation_id,
            "onpremise_ticket_id": onpremise_ticket_id,
            "onpremise_success": onpremise_success,
            "contact_id": contact_id,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "cloud_details": conversation_details.get('data', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Cloud webhook processing error: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route('/webhook/ladesk-onpremise', methods=['POST'])
def ladesk_onpremise_webhook():
    """Webhook endpoint để nhận data từ Ladesk On-Premise (Agent reply)"""
    try:
        # Parse webhook data
        data = parse_webhook_data(request)
        logger.info(f"Parsed webhook data from On-Premise: {data}")
        
        # Log webhook
        db.log_webhook('onpremise_reply', data)
        
        # Validate required fields
        required_fields = ['ticket_id', 'message']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({
                    "status": "ERROR",
                    "message": f"Missing required field: {field}"
                }), 400
        
        onpremise_ticket_id = data['ticket_id']
        message = data['message']
        event_type = data.get('event_type', 'agent_reply')
        
        # Lấy agent info từ data
        agent_info = data.get('agent_info', {})
        user_identifier = agent_info.get('agent_id') or data.get('agent_id')
        
        # BƯỚC 1: Lấy mapping từ database - thử tìm bằng conversation_id trước
        mapping = None
        conversation_id = data.get('conversation_id')
        
        if conversation_id:
            # Thử tìm bằng conversation_id (vì 78swamro là conversation ID)
            mapping = db.get_ticket_mapping(conversation_id=conversation_id)
            logger.info(f"Looking for mapping with conversation_id: {conversation_id}")
        
        if not mapping:
            # Nếu không tìm thấy, thử tìm bằng ticket_id
            mapping = db.get_ticket_mapping(ticket_id=onpremise_ticket_id)
            logger.info(f"Looking for mapping with ticket_id: {onpremise_ticket_id}")
        
        if not mapping:
            logger.error(f"Mapping not found for conversation_id: {conversation_id} or ticket_id: {onpremise_ticket_id}")
            return jsonify({
                "status": "ERROR",
                "message": f"Mapping not found for conversation_id: {conversation_id} or ticket_id: {onpremise_ticket_id}"
            }), 404
        
        cloud_conversation_id = mapping['ladesk_conversation_id']
        
        # BƯỚC 2: Gửi reply đến Ladesk Cloud
        result = cloud_api.send_reply(cloud_conversation_id, message, user_identifier)
        
        if result['status'] == 'success':
            # Cập nhật trạng thái ticket
            db.update_ticket_status(onpremise_ticket_id, 'replied')
            
            logger.info(f"Reply sent successfully from On-Premise to Cloud")
            
            return jsonify({
                "status": "OK",
                "message": "Reply sent successfully to Cloud",
                "ticket_id": onpremise_ticket_id,
                "cloud_conversation_id": cloud_conversation_id
            }), 200
        else:
            logger.error(f"Failed to send reply to Cloud: {result['message']}")
            return jsonify({
                "status": "ERROR",
                "message": f"Failed to send reply to Cloud: {result['message']}"
            }), 500
        
    except Exception as e:
        logger.error(f"On-Premise webhook processing error: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route('/test/create-contact', methods=['POST'])
def test_create_contact():
    """Test endpoint để tạo contact và ticket với thông tin khách hàng"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "ERROR",
                    "message": f"Missing required field: {field}"
                }), 400
        
        customer_name = data['customer_name']
        customer_email = data['customer_email']
        message = data['message']
        facebook_id = data.get('facebook_id', '')
        
        # Tạo email từ Facebook ID nếu không có email
        if not customer_email and facebook_id:
            customer_email = f"{facebook_id}@facebook.com"
        
        # Tìm contact hiện có
        existing_contact = onpremise_api.get_contact_by_email(customer_email)
        
        if existing_contact['status'] == 'success':
            # Sử dụng contact hiện có
            contact_id = existing_contact['data']['id']
            logger.info(f"Using existing contact: {contact_id}")
        else:
            # Tạo contact mới
            contact_data = {
                "firstname": customer_name.split()[0] if customer_name else "Facebook",
                "lastname": " ".join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else "Customer",
                "emails": [customer_email],
                "description": f"Facebook Customer - {customer_name}",
                "type": "V"  # V = Visitor
            }
            
            contact_result = onpremise_api.create_contact(contact_data)
            if contact_result['status'] == 'success':
                contact_id = contact_result['data'].get('id')
                logger.info(f"Created new contact: {contact_id}")
            else:
                logger.warning(f"Failed to create contact: {contact_result['message']}")
                # Fallback: sử dụng email thay vì contact ID
                contact_id = None
        
        # Tạo nội dung ticket với thông tin khách hàng
        # customer_info_text = f"""
        # === THÔNG TIN KHÁCH HÀNG ===
        # Tên: {customer_name}
        # Email: {customer_email}
        # Facebook ID: {facebook_id or 'N/A'}
        # Nguồn: Facebook Fanpage
        # Thời gian tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        # ========================
        # 
        # """
        
        # full_message = customer_info_text + message
        full_message = message  # Chỉ sử dụng message gốc, không thêm thông tin khách hàng
        
        # Tạo ticket với email khách hàng làm useridentifier
        ticket_data = {
            "departmentid": Config.FACEBOOK_DEPARTMENT_ONPREMISE,
            "subject": data.get('subject', 'Facebook Message'),
            "message": full_message,
            "contactemail": customer_email,
            "contactname": customer_name,
            "useridentifier": customer_email,  # Sử dụng email khách hàng làm useridentifier
            "recipient": "support@mail.social-on-premise.ladesk.com",
            "status": "N",
            "channel_type": "E"
        }
        
        ticket_result = onpremise_api.create_ticket(ticket_data)
        
        return jsonify({
            "status": "OK",
            "message": "Test completed",
            "contact_id": contact_id,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "ticket_result": ticket_result
        }), 200
        
    except Exception as e:
        logger.error(f"Test create contact error: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route('/test/comment-webhook', methods=['POST'])
def test_comment_webhook():
    """Test endpoint để mô phỏng webhook comment từ Facebook"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['conversation_id', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "ERROR",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Mô phỏng data comment từ Facebook
        comment_data = {
            "event_type": "comment_added",
            "conversation_id": data['conversation_id'],
            "ticket_id": data.get('ticket_id', f"TICKET-{uuid.uuid4().hex[:8].upper()}"),
            "subject": data.get('subject', 'Facebook Comment'),
            "customer_name": data.get('customer_name', 'Demo Ladesk'),  # Tên fanpage
            "customer_email": data.get('customer_email', ''),
            "department": "Facebook Fanpage",
            "department_id": "dw51dt2g",
            "created_time": data.get('created_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "channel_type": "A",
            "message": data['message'],
            "message_type": "C",  # C = Comment
            "status": "C",
            "contact_id": data.get('contact_id', ''),
            "contact_system_name": data.get('contact_system_name', 'Contact1'),
            # Thêm thông tin khách hàng thực
            "commenter_name": data.get('commenter_name', 'Nguyễn Văn Comment'),
            "commenter_id": data.get('commenter_id', '123456789'),
            "author_name": data.get('author_name', 'Nguyễn Văn Comment'),
            "author_id": data.get('author_id', '123456789')
        }
        
        # Gọi webhook chính
        response = requests.post(
            f"http://localhost:{getattr(Config, 'PORT', 3000)}/webhook/ladesk-cloud",
            json=comment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        return jsonify({
            "status": "OK",
            "message": "Comment webhook test completed",
            "test_data": comment_data,
            "webhook_response": response.json() if response.status_code == 200 else response.text
        }), 200
        
    except Exception as e:
        logger.error(f"Test comment webhook error: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.route('/test/conversation-details/<conversation_id>', methods=['GET'])
def test_conversation_details(conversation_id):
    """Test endpoint để kiểm tra conversation details API"""
    try:
        cloud_api = LadeskCloudAPI()
        
        # Lấy conversation details
        conversation_details = cloud_api.get_conversation_details(conversation_id)
        
        # Lấy messages
        messages_details = cloud_api.get_conversation_messages(conversation_id)
        
        return jsonify({
            "status": "OK",
            "conversation_id": conversation_id,
            "conversation_details": conversation_details,
            "messages_details": messages_details
        }), 200
        
    except Exception as e:
        logger.error(f"Test conversation details error: {e}")
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        "status": "ERROR",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({
        "status": "ERROR",
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    logger.info("Starting Ladesk Integration API...")
    logger.info(f"Database path: {getattr(Config, 'DB_PATH', 'Not configured')}")
    logger.info(f"Ladesk Cloud URL: {getattr(Config, 'LADESK_CLOUD_BASE_URL', 'Not configured')}")
    logger.info(f"Ladesk On-Premise URL: {getattr(Config, 'LADESK_ONPREMISE_BASE_URL', 'Not configured')}")
    logger.info(f"Log file location: {LOG_FILE}")
    
    app.run(
        host=getattr(Config, 'HOST', '0.0.0.0'),
        port=getattr(Config, 'PORT', 5000),
        debug=getattr(Config, 'DEBUG', False)
    )