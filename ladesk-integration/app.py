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
    
    def get_userid_from_api(self, agent_id: str = None) -> str:
        """Lấy userid từ API khi agent_id không có sẵn"""
        try:
            # Import agent mapping config
            from agent_mapping_config import agent_mapping
            
            # Nếu có agent_id và có trong mapping, sử dụng mapping
            if agent_id:
                cloud_user_id = agent_mapping.get_cloud_userid(agent_id)
                if cloud_user_id:
                    logger.info(f"✅ Mapped agent_id {agent_id} to Cloud useridentifier: {cloud_user_id}")
                    return cloud_user_id
            
            # Nếu có agent_id và không phải default, thử lấy thông tin từ On-Premise API
            if agent_id and agent_id != 'default_agent' and agent_id != self.user_identifier:
                try:
                    # Gọi API On-Premise để lấy thông tin agent
                    onpremise_api = LadeskOnPremiseAPI()
                    agent_result = onpremise_api.get_agent_id_by_contactid(agent_id)
                    if agent_result['success']:
                        # Kiểm tra xem agent_id từ API có trong mapping không
                        api_agent_id = agent_result['agent_id']
                        cloud_user_id = agent_mapping.get_cloud_userid(api_agent_id)
                        if cloud_user_id:
                            logger.info(f"✅ Got useridentifier from API mapping: {api_agent_id} -> {cloud_user_id}")
                            return cloud_user_id
                        else:
                            logger.warning(f"⚠️ Agent ID from API not in mapping: {api_agent_id}")
                    else:
                        logger.warning(f"⚠️ API call failed for agent_id: {agent_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not get userid from API: {e}")
            
            # Nếu không lấy được hoặc agent_id là user_identifier mặc định, sử dụng user_identifier mặc định
            logger.info(f"✅ Using default useridentifier: {self.user_identifier}")
            return self.user_identifier
            
        except Exception as e:
            logger.error(f"❌ Error getting userid from API: {e}")
            return self.user_identifier
    
    def send_reply(self, conversation_id: str, message: str, agent_id: str = None) -> dict:
        """Gửi reply đến Cloud"""
        try:
            # Sử dụng endpoint đúng cho agent reply
            url = f"{self.base_url_v1}/conversations/{conversation_id}/messages"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Luôn gọi get_userid_from_api để lấy useridentifier hợp lệ cho Cloud API
            useridentifier = self.get_userid_from_api(agent_id)
            
            # useridentifier đã được xác định ở trên
            
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
                'type': 'M',  # Theo tài liệu: M = Message, N = Note
                'isagent': '1',  # Đánh dấu đây là agent reply
                'agentid': useridentifier  # ID của agent
            }
            
            logger.info(f"🔄 Sending agent reply to Cloud: {conversation_id}, agent: {useridentifier}")
            logger.info(f"🔄 Original message: {message}")
            logger.info(f"🔄 Clean message: {clean_message}")
            logger.info(f"🔄 Reply data: {data}")
            
            # Gửi dưới dạng form data thay vì JSON
            response = requests.post(url, headers=headers, data=data)
            logger.info(f"Cloud reply response: {response.status_code}")
            logger.info(f"Cloud reply response body: {response.text}")
            
            if response.status_code == 200:
                # Kiểm tra xem response có body không
                if response.text.strip():
                    try:
                        return {'success': True, 'data': response.json()}
                    except json.JSONDecodeError:
                        return {'success': True, 'data': {'message': 'Agent reply sent successfully'}}
                else:
                    return {'success': True, 'data': {'message': 'Agent reply sent successfully'}}
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
        self.api_key_v1 = Config.LADESK_ONPREMISE_API_KEY_V1
        self.base_url_v1 = Config.LADESK_ONPREMISE_BASE_URL_V1
    
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
    
    def get_agent_id_by_name(self, agent_name: str) -> dict:
        """Lấy agent_id từ agent_name bằng cách gọi API Ladesk On-Premise"""
        try:
            # Sử dụng API v1 để tìm agent theo tên
            url = f"{self.base_url_v1}/agents"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            
            params = {
                'search': agent_name
            }
            
            logger.info(f"🔍 Searching for agent by name: {agent_name}")
            logger.info(f"🔍 API URL: {url}")
            
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"Agent search response: {response.status_code}")
            logger.info(f"Agent search response body: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result and 'response' in result:
                        agent_data = result['response']
                        if isinstance(agent_data, list) and len(agent_data) > 0:
                            # Lấy agent đầu tiên tìm thấy
                            agent = agent_data[0]
                            agent_id = agent.get('contactid') or agent.get('userid')
                            if agent_id:
                                logger.info(f"✅ Found agent_id: {agent_id} for agent_name: {agent_name}")
                                return {'success': True, 'agent_id': agent_id, 'agent_data': agent}
                        elif isinstance(agent_data, dict):
                            # Nếu response là object thay vì array
                            agent_id = agent_data.get('contactid') or agent_data.get('userid')
                            if agent_id:
                                logger.info(f"✅ Found agent_id: {agent_id} for agent_name: {agent_name}")
                                return {'success': True, 'agent_id': agent_id, 'agent_data': agent_data}
                    
                    logger.warning(f"⚠️ No agent found for name: {agent_name}")
                    return {'success': False, 'error': 'Agent not found'}
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON response: {response.text}")
                    return {'success': False, 'error': 'Invalid JSON response'}
            else:
                logger.error(f"❌ Agent search failed: {response.status_code} - {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"❌ Agent search error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_agent_id_by_contactid(self, contactid: str) -> dict:
        """Lấy agent_id từ contactid bằng cách gọi API Ladesk On-Premise"""
        try:
            # Sử dụng API v1 để lấy thông tin agent theo contactid
            url = f"{self.base_url_v1}/agents/{contactid}"
            headers = {
                'apikey': self.api_key_v1,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"🔍 Getting agent info by contactid: {contactid}")
            logger.info(f"🔍 API URL: {url}")
            
            response = requests.get(url, headers=headers)
            logger.info(f"Agent info response: {response.status_code}")
            logger.info(f"Agent info response body: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result and 'response' in result:
                        agent_data = result['response']
                        agent_id = agent_data.get('contactid') or agent_data.get('userid')
                        if agent_id:
                            logger.info(f"✅ Found agent_id: {agent_id} for contactid: {contactid}")
                            return {'success': True, 'agent_id': agent_id, 'agent_data': agent_data}
                    
                    logger.warning(f"⚠️ No agent found for contactid: {contactid}")
                    return {'success': False, 'error': 'Agent not found'}
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON response: {response.text}")
                    return {'success': False, 'error': 'Invalid JSON response'}
            else:
                logger.error(f"❌ Agent info failed: {response.status_code} - {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"❌ Agent info error: {e}")
            return {'success': False, 'error': str(e)}

def parse_webhook_data(request):
    """Parse webhook data từ request"""
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"Raw webhook data: {raw_data}")
        
        # Làm sạch raw_data để tránh control characters
        import re
        # Loại bỏ control characters trừ \n, \r, \t
        cleaned_data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', raw_data)
        
        # Parse JSON với xử lý lỗi tốt hơn
        data = json.loads(cleaned_data)
        logger.info("✅ JSON parsed successfully")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        # Thử parse lại với strict=False nếu có thể
        try:
            import json5
            data = json5.loads(raw_data)
            logger.info("✅ JSON parsed successfully with json5")
            return data
        except:
            logger.error("❌ Failed to parse JSON even with json5")
            return None
    except Exception as e:
        logger.error(f"Webhook parsing error: {e}")
        return None

# Khởi tạo API instances
cloud_api = LadeskCloudAPI()
onpremise_api = LadeskOnPremiseAPI()

def get_valid_agent_id(agent_name: str, agent_id: str, contactid: str = None) -> str:
    """Lấy agent_id hợp lệ từ nhiều nguồn khác nhau"""
    try:
        # Nếu agent_id đã hợp lệ, sử dụng luôn
        if agent_id and agent_id.strip() and agent_id not in ['{$user_id}', ''] and '{' not in agent_id:
            logger.info(f"✅ Using existing valid agent_id: {agent_id}")
            return agent_id
        
        # Thử lấy từ contactid nếu có
        if contactid and contactid.strip():
            logger.info(f"🔍 Trying to get agent_id from contactid: {contactid}")
            result = onpremise_api.get_agent_id_by_contactid(contactid)
            if result['success']:
                logger.info(f"✅ Got agent_id from contactid: {result['agent_id']}")
                return result['agent_id']
        
        # Thử lấy từ agent_name nếu có
        if agent_name and agent_name.strip() and agent_name not in ['{$user_firstname} {$user_lastname}', '{$user_email}', ''] and '{' not in agent_name:
            logger.info(f"🔍 Trying to get agent_id from agent_name: {agent_name}")
            result = onpremise_api.get_agent_id_by_name(agent_name)
            if result['success']:
                logger.info(f"✅ Got agent_id from agent_name: {result['agent_id']}")
                return result['agent_id']
        
        # Nếu không lấy được, sử dụng default
        logger.warning(f"⚠️ Could not get valid agent_id, using default")
        return 'default_agent'
        
    except Exception as e:
        logger.error(f"❌ Error getting valid agent_id: {e}")
        return 'default_agent'

def process_agent_reply_from_cloud(data):
    """Xử lý agent reply từ Cloud API (tương tự như On-Premise webhook)"""
    try:
        # Lấy thông tin cần thiết
        conversation_id = data.get('conversation_id')
        ticket_id = data.get('ticket_id')
        message = data.get('message', '')
        agent_name = data.get('agent_name', 'Agent')
        customer_email = data.get('customer_email', '')
        
        logger.info(f"🔄 Processing agent reply from Cloud: {conversation_id}, agent: {agent_name}")
        
        # Tìm mapping - webhook từ Cloud gửi conversation_id của Cloud
        mapping = None
        
        # Thử tìm bằng conversation_id trước (vì đây là conversation ID của Cloud)
        if conversation_id:
            mapping = db.get_mapping_by_conversation(conversation_id)
            if mapping:
                logger.info(f"✅ Found mapping by conversation_id: {conversation_id}")
        
        # Nếu không tìm thấy, thử tìm bằng ticket_id (có thể là ticket ID của On-Premise)
        if not mapping and ticket_id:
            mapping = db.get_mapping_by_ticket(ticket_id)
            if mapping:
                logger.info(f"✅ Found mapping by ticket_id: {ticket_id}")
        
        # Nếu vẫn không tìm thấy, thử tìm bằng email
        if not mapping and customer_email:
            mapping = db.get_mapping_by_email(customer_email)
            if mapping:
                logger.info(f"✅ Found mapping by email: {customer_email} -> ticket: {mapping['onpremise_ticket_id']}")
        
        # Nếu vẫn không tìm thấy, log để debug
        if not mapping:
            logger.error(f"❌ No mapping found for conversation_id: {conversation_id}, ticket_id: {ticket_id}")
            logger.error(f"❌ Customer email: {customer_email}")
            
            # Log tất cả mapping để debug
            all_mappings = db.get_all_mappings()
            logger.error(f"❌ All available mappings: {len(all_mappings)}")
            for m in all_mappings:
                logger.error(f"   - Cloud: {m['cloud_conversation_id']} -> OnPremise: {m['onpremise_ticket_id']} (Email: {m['customer_email']})")
            
            return jsonify({"error": "No mapping found"}), 404
        
        # Gửi reply đến Cloud (không cần thiết vì đã là từ Cloud rồi)
        # Chỉ cần log và cập nhật mapping
        cloud_conversation_id = mapping['cloud_conversation_id']
        
        logger.info(f"✅ Agent reply from Cloud processed: {cloud_conversation_id}")
        
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
            "message": "Agent reply from Cloud processed"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Agent reply from Cloud error: {e}")
        return jsonify({"error": str(e)}), 500

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
        
        # Phân tích webhook để xác định loại message
        event_type = data.get('event_type')
        message_type = data.get('message_type')
        status = data.get('status', '')
        agent_name = data.get('agent_name', '')
        agent_id = data.get('agent_id', '')
        channel_type = data.get('channel_type', '')
        
        # Kiểm tra xem có phải là agent reply thực sự không
        is_real_agent_reply = (
            event_type == 'agent_reply' and
            agent_name and 
            agent_name not in ['{$user_firstname} {$user_lastname}', '{$user_email}', ''] and
            agent_id and 
            agent_id.strip() and
            agent_id not in ['{$user_id}', ''] and
            channel_type == 'E'  # Email channel thường là agent reply
        )
        
        # Kiểm tra xem có phải là customer message không
        is_customer_message = (
            (event_type == 'message_added' and message_type in ['M', 'message']) or
            (event_type == 'agent_reply' and 
             (not agent_name or 
              agent_name in ['{$user_firstname} {$user_lastname}', '{$user_email}', ''] or
              not agent_id or 
              not agent_id.strip() or
              agent_id in ['{$user_id}', ''] or
              channel_type == 'A'))  # Facebook channel thường là customer message
        )
        
        # Log chi tiết về quá trình phân loại
        logger.info(f"🔍 Webhook classification: event_type={event_type}, agent_name='{agent_name}', agent_id='{agent_id}', channel_type='{channel_type}'")
        logger.info(f"🔍 is_real_agent_reply={is_real_agent_reply}, is_customer_message={is_customer_message}")
        
        # Nếu là agent reply thực sự, chuyển sang xử lý như On-Premise webhook
        if is_real_agent_reply:
            logger.info(f"🔄 Detected real agent reply from Cloud, processing as agent reply: {agent_name}")
            return process_agent_reply_from_cloud(data)
        
        # Nếu không phải customer message, bỏ qua
        if not is_customer_message:
            logger.info(f"⏭️ Skipping non-customer message: {event_type} - {message_type} - {agent_name}")
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
        
        # Phân tích webhook để xác định loại message
        event_type = data.get('event_type')
        agent_name = data.get('agent_name', '')
        agent_id = data.get('agent_id', '')
        contactid = data.get('contactid', '')
        userid = data.get('userid', '')
        channel_type = data.get('channel_type', '')
        
        # Log chi tiết về webhook
        logger.info(f"🔍 OnPremise webhook received: event_type={event_type}, agent_name='{agent_name}', agent_id='{agent_id}', contactid='{contactid}', userid='{userid}', channel_type='{channel_type}'")
        
        # Chỉ xử lý agent_reply events
        if event_type != 'agent_reply':
            logger.info(f"⏭️ Skipping non-agent-reply event: {event_type}")
            return jsonify({"status": "skipped", "reason": "non_agent_reply_event"}), 200
        
        # Kiểm tra xem có agent_id hợp lệ không
        # Lấy agent_id từ nhiều nguồn khác nhau
        valid_agent_id = None
        if agent_id and agent_id.strip() and agent_id not in ['{$user_id}', ''] and '{' not in agent_id:
            valid_agent_id = agent_id
            logger.info(f"✅ Using agent_id from webhook: {valid_agent_id}")
        elif contactid and contactid.strip() and contactid not in ['{$user_id}', ''] and '{' not in contactid:
            valid_agent_id = contactid
            logger.info(f"✅ Using contactid as agent_id: {valid_agent_id}")
        elif userid and userid.strip() and userid not in ['{$user_id}', ''] and '{' not in userid:
            valid_agent_id = userid
            logger.info(f"✅ Using userid as agent_id: {valid_agent_id}")
        
        # Nếu không có agent_id hợp lệ, bỏ qua event này
        if not valid_agent_id:
            logger.warning(f"⚠️ No valid agent_id found, skipping agent_reply event")
            logger.warning(f"⚠️ agent_id='{agent_id}', contactid='{contactid}', userid='{userid}'")
            return jsonify({"status": "skipped", "reason": "no_valid_agent_id"}), 200
        
        # Lấy thông tin cần thiết
        conversation_id = data.get('conversation_id')
        ticket_id = data.get('ticket_id')
        message = data.get('message', '')
        customer_email = data.get('customer_email', '')
        
        # Làm sạch agent_name nếu cần
        if not agent_name or agent_name in ['{$user_firstname} {$user_lastname}', '{$user_email}', '']:
            agent_name = 'Agent'
            logger.info(f"🔄 Cleaned agent_name to default: {agent_name}")
        
        logger.info(f"🔄 Processing agent reply: {conversation_id}, agent: {agent_name}, valid_agent_id: {valid_agent_id}")
        
        logger.info(f"🔄 Processing agent reply: {conversation_id}, agent: {agent_name}")
        
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
        
        # Sử dụng valid_agent_id đã được xác định từ webhook
        logger.info(f"🔄 Sending reply with valid_agent_id: {valid_agent_id}")
        
        reply_result = cloud_api.send_reply(cloud_conversation_id, message, valid_agent_id)
        
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