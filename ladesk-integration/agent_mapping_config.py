#!/usr/bin/env python3
"""
Agent Mapping Configuration
Quản lý mapping giữa agent ID On-Premise và user identifier Cloud
"""

import json
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AgentMappingConfig:
    """Quản lý mapping agent từ file config"""
    
    def __init__(self, config_file: str = "agent_mapping.json"):
        self.config_file = config_file
        self.mapping = self._load_mapping()
    
    def _load_mapping(self) -> Dict[str, str]:
        """Load mapping từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    logger.info(f"✅ Loaded {len(mapping)} agent mappings from {self.config_file}")
                    return mapping
            else:
                # Tạo file mặc định nếu chưa có
                default_mapping = {
                    "k6citev3": "1pkaew79",  # Keith Nguyen: On-Premise -> Cloud
                    # Thêm các mapping khác ở đây
                }
                self._save_mapping(default_mapping)
                logger.info(f"✅ Created default mapping file: {self.config_file}")
                return default_mapping
        except Exception as e:
            logger.error(f"❌ Error loading mapping: {e}")
            return {}
    
    def _save_mapping(self, mapping: Dict[str, str]):
        """Lưu mapping vào file JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved mapping to {self.config_file}")
        except Exception as e:
            logger.error(f"❌ Error saving mapping: {e}")
    
    def get_cloud_userid(self, onpremise_agent_id: str) -> Optional[str]:
        """Lấy Cloud user identifier từ On-Premise agent ID"""
        return self.mapping.get(onpremise_agent_id)
    
    def add_mapping(self, onpremise_agent_id: str, cloud_userid: str) -> bool:
        """Thêm mapping mới"""
        try:
            self.mapping[onpremise_agent_id] = cloud_userid
            self._save_mapping(self.mapping)
            logger.info(f"✅ Added mapping: {onpremise_agent_id} -> {cloud_userid}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding mapping: {e}")
            return False
    
    def remove_mapping(self, onpremise_agent_id: str) -> bool:
        """Xóa mapping"""
        try:
            if onpremise_agent_id in self.mapping:
                del self.mapping[onpremise_agent_id]
                self._save_mapping(self.mapping)
                logger.info(f"✅ Removed mapping: {onpremise_agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error removing mapping: {e}")
            return False
    
    def list_mappings(self) -> Dict[str, str]:
        """Liệt kê tất cả mappings"""
        return self.mapping.copy()
    
    def reload_mapping(self):
        """Reload mapping từ file"""
        self.mapping = self._load_mapping()

# Instance toàn cục
agent_mapping = AgentMappingConfig() 