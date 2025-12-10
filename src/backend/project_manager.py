# src/backend/project_manager.py

import os
from .db import set_db_path, init_db

def init_project_folder(project_folder: str):
    """
    Tạo cấu trúc .ref và database trong project
    """
    ref_folder = os.path.join(project_folder, ".ref")
    os.makedirs(ref_folder, exist_ok=True)

    db_path = os.path.join(ref_folder, "ref.db")

    # SET DB PATH GLOBAL
    set_db_path(db_path)

    # Tạo DB nếu chưa có
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
