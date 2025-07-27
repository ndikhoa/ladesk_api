#!/usr/bin/env python3
"""
Script test để kiểm tra tính năng tạo contact và ticket với thông tin khách hàng
"""

import requests
import json
import time
from datetime import datetime

# Cấu hình
API_BASE_URL = "http://localhost:3000"

def test_health():
    """Test health endpoint"""
    print("=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_contact():
    """Test tạo contact và ticket"""
    print("\n=== Testing Create Contact ===")
    
    # Test data
    test_data = {
        "customer_name": "Nguyễn Văn Test",
        "customer_email": "nguyenvantest@facebook.com",
        "facebook_id": "123456789",
        "message": "Xin chào, tôi cần hỗ trợ về sản phẩm của bạn. Có thể tư vấn thêm không?",
        "subject": "Yêu cầu tư vấn sản phẩm"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/test/create-contact",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Request Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_webhook_cloud():
    """Test webhook từ Ladesk Cloud"""
    print("\n=== Testing Cloud Webhook ===")
    
    # Test data mô phỏng webhook từ Cloud
    webhook_data = {
        "conversation_id": f"test_conv_{int(time.time())}",
        "message": "Xin chào, tôi có câu hỏi về dịch vụ của bạn",
        "customer_info": {
            "name": "Trần Thị Khách",
            "email": "tranthikhach@facebook.com",
            "contact_id": "987654321",
            "subject": "Hỏi về dịch vụ"
        },
        "event_type": "ticket_created"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/webhook/ladesk-cloud",
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Webhook Data: {json.dumps(webhook_data, indent=2, ensure_ascii=False)}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_multiple_contacts():
    """Test tạo nhiều contact khác nhau"""
    print("\n=== Testing Multiple Contacts ===")
    
    customers = [
        {
            "name": "Lê Văn A",
            "email": "levana@facebook.com",
            "facebook_id": "111111111",
            "message": "Tôi muốn mua sản phẩm A"
        },
        {
            "name": "Phạm Thị B",
            "email": "phamthib@facebook.com", 
            "facebook_id": "222222222",
            "message": "Có thể giao hàng tận nơi không?"
        },
        {
            "name": "Hoàng Văn C",
            "email": "hoangvanc@facebook.com",
            "facebook_id": "333333333", 
            "message": "Giá sản phẩm có giảm không?"
        }
    ]
    
    success_count = 0
    
    for i, customer in enumerate(customers, 1):
        print(f"\n--- Test Customer {i}: {customer['name']} ---")
        
        test_data = {
            "customer_name": customer["name"],
            "customer_email": customer["email"],
            "facebook_id": customer["facebook_id"],
            "message": customer["message"],
            "subject": f"Yêu cầu từ {customer['name']}"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/test/create-contact",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Contact ID: {result.get('contact_id', 'N/A')}")
                print(f"Customer Email: {result.get('customer_email', 'N/A')}")
                success_count += 1
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        # Delay giữa các request
        time.sleep(1)
    
    print(f"\nSuccess: {success_count}/{len(customers)} customers")
    return success_count == len(customers)

def main():
    """Main test function"""
    print("🚀 Starting Ladesk Integration API Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test health
    health_ok = test_health()
    if not health_ok:
        print("❌ Health check failed. Please check if the API is running.")
        return
    
    # Test create contact
    contact_ok = test_create_contact()
    
    # Test webhook
    webhook_ok = test_webhook_cloud()
    
    # Test multiple contacts
    multiple_ok = test_multiple_contacts()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Create Contact: {'✅ PASS' if contact_ok else '❌ FAIL'}")
    print(f"Cloud Webhook: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    print(f"Multiple Contacts: {'✅ PASS' if multiple_ok else '❌ FAIL'}")
    
    if all([health_ok, contact_ok, webhook_ok, multiple_ok]):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check the logs.")

if __name__ == "__main__":
    main() 