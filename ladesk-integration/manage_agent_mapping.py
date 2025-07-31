#!/usr/bin/env python3
"""
Agent Mapping Management Script
Script để quản lý mapping giữa agent ID On-Premise và user identifier Cloud
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agent_mapping_config import agent_mapping
import argparse
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_mappings():
    """Liệt kê tất cả mappings"""
    mappings = agent_mapping.list_mappings()
    if not mappings:
        print("❌ Không có mapping nào")
        return
    
    print("📋 Danh sách Agent Mappings:")
    print("-" * 50)
    for onpremise_id, cloud_id in mappings.items():
        print(f"  {onpremise_id} -> {cloud_id}")
    print("-" * 50)
    print(f"Tổng cộng: {len(mappings)} mappings")

def add_mapping(onpremise_id: str, cloud_id: str):
    """Thêm mapping mới"""
    print(f"➕ Thêm mapping: {onpremise_id} -> {cloud_id}")
    
    if agent_mapping.add_mapping(onpremise_id, cloud_id):
        print("✅ Thêm mapping thành công!")
    else:
        print("❌ Thêm mapping thất bại!")

def remove_mapping(onpremise_id: str):
    """Xóa mapping"""
    print(f"🗑️ Xóa mapping: {onpremise_id}")
    
    if agent_mapping.remove_mapping(onpremise_id):
        print("✅ Xóa mapping thành công!")
    else:
        print("❌ Xóa mapping thất bại hoặc mapping không tồn tại!")

def test_mapping(onpremise_id: str):
    """Test mapping"""
    cloud_id = agent_mapping.get_cloud_userid(onpremise_id)
    if cloud_id:
        print(f"✅ Mapping tìm thấy: {onpremise_id} -> {cloud_id}")
    else:
        print(f"❌ Không tìm thấy mapping cho: {onpremise_id}")

def reload_mapping():
    """Reload mapping từ file"""
    print("🔄 Reloading mapping...")
    agent_mapping.reload_mapping()
    print("✅ Reload mapping thành công!")

def main():
    parser = argparse.ArgumentParser(description="Quản lý Agent Mapping")
    parser.add_argument('action', choices=['list', 'add', 'remove', 'test', 'reload'], 
                       help='Hành động cần thực hiện')
    parser.add_argument('--onpremise-id', '-o', help='On-Premise Agent ID')
    parser.add_argument('--cloud-id', '-c', help='Cloud User Identifier')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_mappings()
    
    elif args.action == 'add':
        if not args.onpremise_id or not args.cloud_id:
            print("❌ Cần cung cấp cả --onpremise-id và --cloud-id")
            sys.exit(1)
        add_mapping(args.onpremise_id, args.cloud_id)
    
    elif args.action == 'remove':
        if not args.onpremise_id:
            print("❌ Cần cung cấp --onpremise-id")
            sys.exit(1)
        remove_mapping(args.onpremise_id)
    
    elif args.action == 'test':
        if not args.onpremise_id:
            print("❌ Cần cung cấp --onpremise-id")
            sys.exit(1)
        test_mapping(args.onpremise_id)
    
    elif args.action == 'reload':
        reload_mapping()

if __name__ == '__main__':
    main() 