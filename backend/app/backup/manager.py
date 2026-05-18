"""
FitAI - 数据备份模块
Phase 7: 数据备份机制
"""
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import json
import sqlite3
import os


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(
        self,
        db_path: str,
        name: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """创建数据库备份"""
        if name is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            name = f"backup_{timestamp}.db"
            
        backup_path = self.backup_dir / name
        
        # SQLite备份
        if os.path.exists(db_path):
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(str(backup_path))
            
            with dst_conn:
                src_conn.backup(dst_conn)
                
            src_conn.close()
            dst_conn.close()
            
            # 创建元数据
            if include_metadata:
                metadata = {
                    "name": name,
                    "created_at": datetime.utcnow().isoformat(),
                    "source_db": db_path,
                    "size_bytes": backup_path.stat().st_size
                }
                metadata_path = self.backup_dir / f"{name}.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
        return str(backup_path)
        
    def restore_backup(self, backup_name: str, target_db: str) -> bool:
        """从备份恢复"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return False
            
        # 备份现有数据库
        if os.path.exists(target_db):
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_old = f"{target_db}.pre_restore_{timestamp}"
            os.rename(target_db, backup_old)
            
        # 恢复
        src_conn = sqlite3.connect(str(backup_path))
        dst_conn = sqlite3.connect(target_db)
        
        with dst_conn:
            src_conn.backup(dst_conn)
            
        src_conn.close()
        dst_conn.close()
        
        return True
        
    def list_backups(self) -> List[dict]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            metadata_path = self.backup_dir / f"{backup_file.name}.json"
            
            backup_info = {
                "name": backup_file.name,
                "size_bytes": backup_file.stat().st_size,
                "created_at": datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
            }
            
            # 尝试读取元数据
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        backup_info.update(metadata)
                except Exception:
                    pass
                    
            backups.append(backup_info)
            
        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
        
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        backup_path = self.backup_dir / backup_name
        metadata_path = self.backup_dir / f"{backup_name}.json"
        
        deleted = False
        
        if backup_path.exists():
            backup_path.unlink()
            deleted = True
            
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True
            
        return deleted
        
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """清理旧备份"""
        backups = self.list_backups()
        deleted = 0
        
        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                self.delete_backup(backup["name"])
                deleted += 1
                
        return deleted


# 全局实例
_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """获取全局备份管理器"""
    global _manager
    if _manager is None:
        _manager = BackupManager()
    return _manager
