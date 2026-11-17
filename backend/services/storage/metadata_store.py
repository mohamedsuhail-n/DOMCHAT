import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

class MetadataStore:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations TEXT,
                model TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        """)
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """)
        
        # Websites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                page_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                last_crawled TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """)
        
        # Settings key-value table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        
        # Ensure default project exists
        cursor.execute("SELECT id FROM projects WHERE id = 'default'")
        if not cursor.fetchone():
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("default", "Default Workspace", "Primary workspace for DOMCHAT", now, now)
            )
            conn.commit()
            
        conn.close()

    # --- Project Methods ---
    def list_projects(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        projects = [dict(r) for r in rows]
        conn.close()
        return projects

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        project_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, description, now, now)
        )
        conn.commit()
        conn.close()
        return {"id": project_id, "name": name, "description": description, "created_at": now, "updated_at": now}

    def update_project(self, project_id: str, name: str, description: Optional[str] = None) -> bool:
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        if description is not None:
            conn.execute(
                "UPDATE projects SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                (name, description, now, project_id)
            )
        else:
            conn.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
                (name, now, project_id)
            )
        changed = conn.total_changes > 0
        conn.commit()
        conn.close()
        return changed

    def delete_project(self, project_id: str) -> bool:
        if project_id == "default":
            return False  # Protect default project
        conn = get_db_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        changed = conn.total_changes > 0
        conn.commit()
        conn.close()
        return changed

    # --- Conversation Methods ---
    def list_conversations(self, project_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM conversations WHERE project_id = ? ORDER BY updated_at DESC",
            (project_id,)
        ).fetchall()
        convs = [dict(r) for r in rows]
        conn.close()
        return convs

    def create_conversation(self, project_id: str, title: str = "New Conversation") -> Dict[str, Any]:
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO conversations (id, project_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, project_id, title, now, now)
        )
        conn.commit()
        conn.close()
        return {"id": conv_id, "project_id": project_id, "title": title, "created_at": now, "updated_at": now}

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?", (title, now, conversation_id))
        changed = conn.total_changes > 0
        conn.commit()
        conn.close()
        return changed

    def delete_conversation(self, conversation_id: str) -> bool:
        conn = get_db_connection()
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        changed = conn.total_changes > 0
        conn.commit()
        conn.close()
        return changed

    # --- Message Methods ---
    def list_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,)
        ).fetchall()
        msgs = []
        for r in rows:
            d = dict(r)
            if d.get("citations"):
                try:
                    d["citations"] = json.loads(d["citations"])
                except Exception:
                    d["citations"] = []
            else:
                d["citations"] = []
            msgs.append(d)
        conn.close()
        return msgs

    def add_message(self, conversation_id: str, role: str, content: str, citations: Optional[List[Dict[str, Any]]] = None, model: str = "") -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        citations_json = json.dumps(citations or [])
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, citations, model, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, citations_json, model, now)
        )
        # Update conversation updated_at
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        conn.commit()
        conn.close()
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "citations": citations or [],
            "model": model,
            "created_at": now
        }

    # --- Document Methods ---
    def add_document(self, project_id: str, filename: str, file_type: str, file_size: int, file_path: str) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO documents 
               (id, project_id, filename, file_type, file_size, file_path, chunk_count, status, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, project_id, filename, file_type, file_size, file_path, 0, "uploaded", now, now)
        )
        conn.commit()
        conn.close()
        return {
            "id": doc_id, "project_id": project_id, "filename": filename,
            "file_type": file_type, "file_size": file_size, "file_path": file_path,
            "chunk_count": 0, "status": "uploaded", "created_at": now, "updated_at": now
        }

    def update_document_status(self, doc_id: str, status: str, chunk_count: Optional[int] = None, error_message: Optional[str] = None):
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        if chunk_count is not None:
            conn.execute(
                "UPDATE documents SET status = ?, chunk_count = ?, error_message = ?, updated_at = ? WHERE id = ?",
                (status, chunk_count, error_message, now, doc_id)
            )
        else:
            conn.execute(
                "UPDATE documents SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                (status, error_message, now, doc_id)
            )
        conn.commit()
        conn.close()

    def list_documents(self, project_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM documents WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
        docs = [dict(r) for r in rows]
        conn.close()
        return docs

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.get_document(doc_id)
        if not doc:
            return None
        conn = get_db_connection()
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        return doc

    # --- Website Methods ---
    def add_website(self, project_id: str, url: str) -> Dict[str, Any]:
        site_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO websites 
               (id, project_id, url, title, page_count, chunk_count, status, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (site_id, project_id, url, url, 0, 0, "pending", now, now)
        )
        conn.commit()
        conn.close()
        return {
            "id": site_id, "project_id": project_id, "url": url, "title": url,
            "page_count": 0, "chunk_count": 0, "status": "pending",
            "created_at": now, "updated_at": now
        }

    def update_website_status(self, site_id: str, status: str, title: Optional[str] = None, page_count: Optional[int] = None, chunk_count: Optional[int] = None, error_message: Optional[str] = None):
        now = datetime.utcnow().isoformat()
        conn = get_db_connection()
        conn.execute(
            """UPDATE websites 
               SET status = ?, title = COALESCE(?, title), 
                   page_count = COALESCE(?, page_count), 
                   chunk_count = COALESCE(?, chunk_count), 
                   error_message = ?, last_crawled = ?, updated_at = ? 
               WHERE id = ?""",
            (status, title, page_count, chunk_count, error_message, now, now, site_id)
        )
        conn.commit()
        conn.close()

    def list_websites(self, project_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM websites WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
        sites = [dict(r) for r in rows]
        conn.close()
        return sites

    def get_website(self, site_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM websites WHERE id = ?", (site_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_website(self, site_id: str) -> Optional[Dict[str, Any]]:
        site = self.get_website(site_id)
        if not site:
            return None
        conn = get_db_connection()
        conn.execute("DELETE FROM websites WHERE id = ?", (site_id,))
        conn.commit()
        conn.close()
        return site

    # --- Settings Methods ---
    def get_setting(self, key: str, default: Any = None) -> Any:
        conn = get_db_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        if row:
            try:
                return json.loads(row["value"])
            except Exception:
                return row["value"]
        return default

    def set_setting(self, key: str, value: Any):
        now = datetime.utcnow().isoformat()
        val_str = json.dumps(value)
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?",
            (key, val_str, now, val_str, now)
        )
        conn.commit()
        conn.close()

    def get_all_settings(self) -> Dict[str, Any]:
        conn = get_db_connection()
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        conn.close()
        res = {}
        for r in rows:
            try:
                res[r["key"]] = json.loads(r["value"])
            except Exception:
                res[r["key"]] = r["value"]
        return res

db = MetadataStore()
