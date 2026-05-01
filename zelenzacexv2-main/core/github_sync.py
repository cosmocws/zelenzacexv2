# core/github_sync.py
import os
import requests
import base64
from datetime import datetime
from typing import Dict, Optional

class GitHubSync:
    """Sincroniza archivos con GitHub - Version simple."""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str, branch: str = "main"):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.sync_log = []
    
    def _get_sha(self, file_path: str) -> Optional[str]:
        try:
            url = f"{self.base_url}/contents/{file_path}"
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                return r.json().get('sha')
        except:
            pass
        return None
    
    def subir_archivo(self, local_path: str) -> bool:
        """Sube UN archivo a GitHub. Retorna True si funciono."""
        try:
            if not os.path.exists(local_path):
                return False
            
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_path = local_path.replace('\\', '/')
            sha = self._get_sha(file_path)
            
            payload = {
                "message": f"Update {os.path.basename(local_path)}",
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "branch": self.branch
            }
            if sha:
                payload["sha"] = sha
            
            url = f"{self.base_url}/contents/{file_path}"
            r = requests.put(url, headers=self.headers, json=payload)
            
            if r.status_code in [200, 201]:
                self.sync_log.append({
                    "file": file_path,
                    "time": datetime.now().isoformat()
                })
                return True
            return False
        except:
            return False
    
    def get_sync_status(self) -> Dict:
        return {
            "last_sync": self.sync_log[-1] if self.sync_log else None,
            "total_syncs": len(self.sync_log)
        }


def sync_archivo(local_path: str):
    """Sube un archivo a GitHub si el sync esta disponible."""
    import streamlit as st
    gs = st.session_state.get('github_sync')
    if gs:
        gs.subir_archivo(local_path)