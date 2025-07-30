#!/usr/bin/env python3
"""
Ladesk Integration API - Clean Version
Logic cốt lõi: Facebook → Cloud → On-Premise → Cloud → Facebook
"""

import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from config import Config
from database_simple import db

# Cấu hình logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

class LadeskCloudAPI:
    """API cho Ladesk Cloud"""
    
    def __init__(self):
        self.api_key_v3 = Config.LADESK_CLOUD_API_KEY_V3
        self.base_url_v3 = Config.LADESK_CLOUD_BASE_URL_V3
        self.api_key_v1 = Config.LADESK_CLOUD_API_KEY_V1
        self.base_url_v1 = Config.LADESK_CLOUD_BASE_URL_V1
        self.user_identifier = Config.LADESK_CLOUD_USER_IDENTIFIER
    
    def get_conversation_details(self, conversation_id: str) -> dict:
        """Lấy chi tiết conversation từ Cloud"""
        try:
            url = f"{self.base_url_v1}/conversations/{conversation_id}"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            logger.info(f"Cloud conversation details response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Cloud conversation details error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_contact_details(self, contact_id: str) -> dict:
        """Lấy chi tiết contact từ Cloud"""
        try:
            url = f"{self.base_url_v3}/contacts/{contact_id}"
            headers = {
                'apikey': self.api_key_v3,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            logger.info(f"Cloud contact details response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Cloud contact details error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_reply(self, conversation_id: str, message: str, agent_id: str = None) -> dict:
        """Gửi reply đến Cloud"""
        try:
            url = f"{self.base_url_v1}/conversations/{conversation_id}/messages"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Sử dụng agent_id nếu có, không thì dùng user_identifier mặc định
            useridentifier = agent_id if agent_id else self.user_identifier
            
            # Strip HTML tags và entities từ message
            import re
            import html
            
            # Strip HTML tags trước
            clean_message = re.sub(r'<[^>]+>', '', message)
            # Decode HTML entities (như &nbsp;, &amp;, etc.)
            clean_message = html.unescape(clean_message)
            # Strip whitespace thừa
            clean_message = clean_message.strip()
            
            data = {
                'message': clean_message,
                'useridentifier': useridentifier,
                'type': 'M'  # Đảm bảo hiển thị như message thay vì system note
            }
            
            logger.info(f"🔄 Sending reply to Cloud: {conversation_id}, agent: {useridentifier}")
            logger.info(f"🔄 Original message: {message}")
            logger.info(f"🔄 Clean message: {clean_message}")
            logger.info(f"🔄 Reply data: {data}")
            
            # Gửi dưới dạng form data thay vì JSON
            response = requests.post(url, headers=headers, data=data)
            logger.info(f"Cloud reply response: {response.status_code}")
            logger.info(f"Cloud reply response body: {response.text}")
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Cloud reply error: {e}")
            return {'success': False, 'error': str(e)}

class LadeskOnPremiseAPI:
    """API cho Ladesk On-Premise"""
    
    def __init__(self):
        self.api_key = Config.LADESK_ONPREMISE_API_KEY_V3
        self.base_url = Config.LADESK_ONPREMISE_BASE_URL_V3
    
    def create_contact(self, contact_data: dict) -> dict:
        """Tạo contact trong On-Premise"""
        try:
            url = f"{self.base_url}/contacts"
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=contact_data)
            logger.info(f"Contact creation response: {response.status_code}")
            logger.info(f"Contact creation response body: {response.text}")
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            elif response.status_code == 400 and "already exist" in response.text:
                # Contact đã tồn tại, trích xuất ID từ response
                try:
                    error_data = response.json()
                    # Tìm ID trong message text
                    import re
                    id_match = re.search(r'Id: ([a-zA-Z0-9]+)', response.text)
                    if id_match:
                        contact_id = id_match.group(1)
                        logger.info(f"✅ Extracted existing contact ID: {contact_id}")
                        return {'success': True, 'contact_id': contact_id, 'exists': True}
                    else:
                        # Thử parse JSON
                        contact_id = error_data.get('contact_id') or error_data.get('id')
                        if contact_id:
                            logger.info(f"✅ Found existing contact ID in JSON: {contact_id}")
                            return {'success': True, 'contact_id': contact_id, 'exists': True}
                        else:
                            logger.error(f"❌ Cannot extract contact ID from response: {response.text}")
                            return {'success': False, 'error': 'Contact exists but cannot extract ID'}
                except Exception as e:
                    logger.error(f"❌ Error parsing contact creation response: {e}")
                    return {'success': False, 'error': 'Contact exists but cannot extract ID'}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Contact creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_ticket(self, ticket_data: dict) -> dict:
        """Tạo ticket trong On-Premise"""
        try:
            url = f"{self.base_url}/tickets"
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=ticket_data)
            logger.info(f"Ticket creation response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Ticket creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_ticket_message(self, message_data: dict) -> dict:
        """Cập nhật message vào ticket hiện tại"""
        try:
            # Sử dụng API v1 cho message update (conversation messages)
            url = f"{Config.LADESK_ONPREMISE_BASE_URL_V1}/conversations/{message_data['ticketid']}/messages"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Format đúng cho API v1 - sử dụng form data với apikey trong data
            data = {
                'message': message_data['message'],  # Message body (mandatory)
                'apikey': Config.LADESK_ONPREMISE_API_KEY_V1,  # API key (mandatory)
                'type': 'M',  # Message type (optional) - để hiển thị đúng message của khách hàng
                'useridentifier': message_data['useridentifier']  # Customer identifier (optional) - để hiển thị như customer message
            }
            
            logger.info(f"🔄 Updating ticket message at URL: {url}")
            logger.info(f"🔄 Message data: {data}")
            
            # Gửi dưới dạng form data thay vì JSON
            response = requests.post(url, headers=headers, data=data)
            logger.info(f"Ticket message update response: {response.status_code}")
            logger.info(f"Ticket message update response body: {response.text}")
            
            if response.status_code == 200:
                # Kiểm tra xem response có body không
                if response.text.strip():
                    try:
                        return {'success': True, 'data': response.json()}
                    except json.JSONDecodeError:
                        return {'success': True, 'data': {'message': 'Message updated successfully'}}
                else:
                    return {'success': True, 'data': {'message': 'Message updated successfully'}}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Ticket message update error: {e}")
            return {'success': False, 'error': str(e)}

def parse_webhook_data(request):
    """Parse webhook data từ request"""
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw webhook data: {raw_data}")
        
        # Parse JSON đơn giản
        data = json.loads(raw_data)
        logger.info("✅ JSON parsed successfully")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Webhook parsing error: {e}")
        return None

# Khởi tạo API instances
cloud_api = LadeskCloudAPI()
onpremise_api = LadeskOnPremiseAPI()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Ladesk Integration API"
    })

@app.route('/webhook/ladesk-cloud', methods=['POST'])
def ladesk_cloud_webhook():
    """Webhook nhận data từ Ladesk Cloud (Facebook)"""
    try:
        # Parse webhook data
        data = parse_webhook_data(request)
        if not data:
            return jsonify({"error": "Invalid webhook data"}), 400
        
        # Log webhook
        db.log_webhook('cloud_incoming', data)
        
        # Chỉ xử lý message từ khách hàng
        event_type = data.get('event_type')
        message_type = data.get('message_type')
        status = data.get('status', '')
        
        if event_type != 'message_added' or message_type not in ['M', 'message']:
            logger.info(f"⏭️ Skipping non-customer message: {event_type} - {message_type}")
            return jsonify({"status": "skipped", "reason": "non_customer_message"}), 200
        
        # Kiểm tra status - chỉ xử lý conversation mở hoặc mới
        if status == 'C':  # Open - tiếp tục xử lý
            logger.info(f"✅ Conversation is open (status: {status}), continuing processing")
        elif status == 'A':  # Answered - có thể tiếp tục xử lý
            logger.info(f"✅ Conversation is answered (status: {status}), continuing processing")
        elif status == 'R':  # Resolved - có thể tiếp tục xử lý
            logger.info(f"✅ Conversation is resolved (status: {status}), continuing processing")
        elif status not in ['N', 'O', '']:  # New, Open, or empty
            logger.info(f"⏭️ Skipping conversation with status: {status}")
            return jsonify({"status": "skipped", "reason": f"conversation_status_{status}"}), 200
        
        # Lấy thông tin cần thiết
        conversation_id = data.get('conversation_id')
        contact_id = data.get('contact_id')  # Lấy contact_id từ webhook
        message = data.get('message', '')
        subject = data.get('subject', 'Facebook Message')
        logger.info(f"✅ Processing customer message: {conversation_id}, contact: {contact_id}")
        
        # Kiểm tra mapping hiện tại
        existing_mapping = db.get_mapping_by_conversation(conversation_id)
        
        # Lưu mapping để sử dụng sau
        should_update_existing = existing_mapping is not None
        existing_ticket_id = existing_mapping['onpremise_ticket_id'] if existing_mapping else None
        
        # Khởi tạo biến contact_data_cloud
        contact_data_cloud = {}
        contact_result = {'success': False}
        
        # Lấy thông tin contact thật từ Cloud
        customer_name = 'Facebook Customer'  # Default
        customer_email = f"facebook_{conversation_id}@facebook.com"  # Default
        
        if contact_id:
            contact_result = cloud_api.get_contact_details(contact_id)
            if contact_result['success']:
                contact_data_cloud = contact_result['data']
                customer_name = f"{contact_data_cloud.get('firstname', '')} {contact_data_cloud.get('lastname', '')}".strip()
                if not customer_name:
                    customer_name = 'Facebook Customer'
                
                customer_email = contact_data_cloud.get('emails', [])
                if customer_email:
                    customer_email = customer_email[0]  # Lấy email đầu tiên
                else:
                    customer_email = f"facebook_{conversation_id}@facebook.com"
                
                logger.info(f"✅ Retrieved contact info: {customer_name}, email: {customer_email}")
            else:
                logger.error(f"❌ Failed to get contact details: {contact_result['error']}")
        else:
            logger.warning("⚠️ No contact_id in webhook data")
        
        # Tạo contact trong On-Premise với thông tin thật
        contact_data = {
            'firstname': contact_data_cloud.get('firstname', 'Facebook') if contact_data_cloud else 'Facebook',
            'lastname': contact_data_cloud.get('lastname', 'Customer') if contact_data_cloud else 'Customer',
            'emails': [customer_email],
            'description': f'Facebook Customer - {customer_name}',
            'type': 'V'
        }
        
        contact_result = onpremise_api.create_contact(contact_data)
        if not contact_result['success']:
            logger.error(f"❌ Failed to create contact: {contact_result['error']}")
            # Nếu contact tạo thất bại, vẫn tiếp tục tạo ticket với thông tin có sẵn
            logger.warning("⚠️ Continuing with ticket creation despite contact creation failure")
            contact_id = None
        else:
            contact_id = contact_result.get('contact_id') or contact_result.get('data', {}).get('id')
            logger.info(f"✅ Contact created/retrieved successfully: {contact_id}")
        
        # Tạo ticket mới cho mỗi message (vì LiveAgent không cho phép update message)
        logger.info(f"🆕 Creating new ticket for message in conversation: {conversation_id}")
        
        # Tạo subject với conversation ID để dễ track
        message_subject = f"Facebook - {conversation_id} - {subject}"
        
        ticket_data = {
            'departmentid': Config.LADESK_ONPREMISE_DEPARTMENT_ID,
            'subject': message_subject,
            'message': message,
            'contactemail': customer_email,
            'contactname': customer_name,
            'useridentifier': customer_email,
            'recipient': Config.LADESK_ONPREMISE_RECIPIENT_EMAIL,
            'status': 'N',
            'channel_type': 'E'
        }
        
        ticket_result = onpremise_api.create_ticket(ticket_data)
        if not ticket_result['success']:
            logger.error(f"❌ Failed to create ticket: {ticket_result['error']}")
            return jsonify({"error": "Ticket creation failed"}), 500
        
        ticket_id = ticket_result['data']['id']
        ticket_code = ticket_result['data'].get('code', ticket_id)  # Sử dụng code nếu có
        
        # Tạo mapping cho message này - sử dụng ticket_code để match với webhook
        db.create_mapping(
            cloud_conversation_id=conversation_id,
            onpremise_ticket_id=ticket_code,  # Sử dụng code thay vì id
            onpremise_contact_id=contact_id,
            customer_name=customer_name,
            customer_email=customer_email
        )
        
        logger.info(f"✅ Successfully created ticket: {ticket_id} (code: {ticket_code}) for message in conversation: {conversation_id}")
        
        return jsonify({
            "status": "success",
            "message": "New ticket created for message",
            "conversation_id": conversation_id,
            "ticket_id": ticket_id,
            "ticket_code": ticket_code
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Cloud webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/ladesk-onpremise', methods=['POST'])
def ladesk_onpremise_webhook():
    """Webhook nhận data từ Ladesk On-Premise (Agent reply)"""
    try:
        # Parse webhook data
        data = parse_webhook_data(request)
        if not data:
            return jsonify({"error": "Invalid webhook data"}), 400
        
        # Log webhook
        db.log_webhook('onpremise_incoming', data)
        
        # Chỉ xử lý agent reply
        event_type = data.get('event_type')
        if event_type != 'agent_reply':
            logger.info(f"⏭️ Skipping non-agent-reply event: {event_type}")
            return jsonify({"status": "skipped", "reason": "non_agent_reply"}), 200
        
        # Lấy thông tin cần thiết
        conversation_id = data.get('conversation_id')
        ticket_id = data.get('ticket_id')
        message = data.get('message', '')
        agent_name = data.get('agent_name', 'Agent')
        customer_email = data.get('customer_email', '')
        
        # Kiểm tra nếu agent_name chứa template variables
        if '{$user_firstname}' in agent_name or '{$user_lastname}' in agent_name:
            logger.warning(f"⚠️ Agent name contains template variables: {agent_name}")
            # Thử lấy tên agent từ agent_email hoặc sử dụng tên mặc định
            if agent_name == '{$user_firstname} {$user_lastname}':
                agent_name = 'Agent'  # Sử dụng tên mặc định
                logger.info(f"🔄 Using default agent name: {agent_name}")
            else:
                # Có thể có một phần template, giữ lại phần thật
                agent_name = agent_name.replace('{$user_firstname}', '').replace('{$user_lastname}', '').strip()
                if not agent_name:
                    agent_name = 'Agent'
                logger.info(f"🔄 Cleaned agent name: {agent_name}")
        
        logger.info(f"🔄 Processing agent reply: {conversation_id}, agent: {agent_name}")
        
        logger.info(f"🔄 Processing agent reply: {conversation_id}")
        
        # Tìm mapping - webhook từ On-Premise gửi ticket_id và conversation_id của On-Premise
        mapping = None
        
        # Thử tìm bằng ticket_id trước (vì đây là ticket ID của On-Premise)
        if ticket_id:
            mapping = db.get_mapping_by_ticket(ticket_id)
            if mapping:
                logger.info(f"✅ Found mapping by ticket_id: {ticket_id}")
        
        # Nếu không tìm thấy, thử tìm bằng conversation_id (cũng có thể là ticket ID)
        if not mapping and conversation_id:
            mapping = db.get_mapping_by_ticket(conversation_id)
            if mapping:
                logger.info(f"✅ Found mapping by conversation_id (as ticket_id): {conversation_id}")
        
        # Nếu vẫn không tìm thấy, thử tìm bằng email
        if not mapping and customer_email:
            mapping = db.get_mapping_by_email(customer_email)
            if mapping:
                logger.info(f"✅ Found mapping by email: {customer_email} -> ticket: {mapping['onpremise_ticket_id']}")
        
        # Nếu vẫn không tìm thấy, thử tìm tất cả mapping và log để debug
        if not mapping:
            logger.error(f"❌ No mapping found for ticket_id: {ticket_id}, conversation_id: {conversation_id}")
            logger.error(f"❌ Customer email: {customer_email}")
            
            # Log tất cả mapping để debug
            all_mappings = db.get_all_mappings()
            logger.error(f"❌ All available mappings: {len(all_mappings)}")
            for m in all_mappings:
                logger.error(f"   - Cloud: {m['cloud_conversation_id']} -> OnPremise: {m['onpremise_ticket_id']} (Email: {m['customer_email']})")
            
            return jsonify({"error": "No mapping found"}), 404
        
        # Gửi reply đến Cloud
        cloud_conversation_id = mapping['cloud_conversation_id']
        
        # Lấy agent_id từ webhook data nếu có
        agent_id = data.get('agent_id', '')
        
        # Nếu không có agent_id, thử lấy từ agent_email hoặc sử dụng default
        if not agent_id:
            agent_email = data.get('agent_email', '')
            if agent_email and agent_email != '{$user_email}':
                # Có thể extract agent ID từ email hoặc sử dụng email làm identifier
                agent_id = agent_email
                logger.info(f"🔄 Using agent_email as identifier: {agent_id}")
            else:
                # Sử dụng user_identifier mặc định từ config
                agent_id = Config.LADESK_CLOUD_USER_IDENTIFIER
                logger.warning(f"⚠️ No agent_id in webhook data, using default: {agent_id}")
        else:
            logger.info(f"🔄 Using agent_id from webhook: {agent_id}")
        
        reply_result = cloud_api.send_reply(cloud_conversation_id, message, agent_id)
        
        if reply_result['success']:
            logger.info(f"✅ Reply sent successfully to Cloud: {cloud_conversation_id}")
            
            # Cập nhật mapping với thông tin reply
            db.update_mapping(
                cloud_conversation_id=cloud_conversation_id,
                last_agent_reply=message,
                last_agent_name=agent_name,
                last_reply_time=datetime.now().isoformat()
            )
            
            return jsonify({
                "status": "success",
                "conversation_id": cloud_conversation_id,
                "message": "Reply sent to Cloud"
            }), 200
        else:
            logger.error(f"❌ Failed to send reply: {reply_result['error']}")
            return jsonify({"error": "Failed to send reply"}), 500
        
    except Exception as e:
        logger.error(f"❌ On-Premise webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Ladesk Integration API...")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    ) 