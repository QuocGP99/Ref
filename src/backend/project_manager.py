# src/backend/project_manager.py

import os
from .db import set_db_path, init_db

def init_or_load_project(project_folder: str):
    """
    Tự động phát hiện project mới hoặc cũ.
    Nếu có .ref/ref.db → load; nếu chưa có → init mới.
    """
    ref_folder = os.path.join(project_folder, ".ref")
    db_path = os.path.join(ref_folder, "ref.db")

    os.makedirs(ref_folder, exist_ok=True)

    if os.path.exists(db_path):
        # Project cũ → chỉ load lại DB path
        print("Loading existing project database:", db_path)
        set_db_path(db_path)
    else:
        print("Initializing new project database:", db_path)
        set_db_path(db_path)
        init_db()

    return ref_folder, db_path

def load_project(project_folder: str):
    """
    Khi mở project có sẵn
    """
    ref_folder = os.path.join(project_folder, ".ref")
    db_path = os.path.join(ref_folder, "ref.db")

    if not os.path.exists(db_path):
        raise Exception("Project chưa được init!")

    set_db_path(db_path)
    return ref_folder, db_path
