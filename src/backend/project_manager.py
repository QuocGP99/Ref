import os
from src.backend.database_manager import init_db, get_session, get_engine_url
from src.backend.database_manager import Folder

_current_project_path = None


def set_current_project_path(path: str):
    global _current_project_path
    _current_project_path = path


def get_current_project_path() -> str:
    global _current_project_path
    return _current_project_path


def init_or_load_project(project_folder: str):
    """Tạo mới hoặc tải project MySQL."""
    db_url = get_engine_url()
    print(f"🔗 Using MySQL Database for project: {project_folder}")
    init_db(db_url)

    session = get_session()
    folder_name = os.path.basename(project_folder)
    existing = session.query(Folder).filter_by(name=folder_name).first()

    if not existing:
        new_folder = Folder(name=folder_name, path=project_folder)
        session.add(new_folder)
        session.commit()
        print(f"✅ Folder added: {folder_name}")
    else:
        print(f"📂 Folder already exists: {folder_name}")

    set_current_project_path(project_folder)
    return project_folder, "MySQL database active"


def load_project(project_folder: str):
    """Khi mở project đã có."""
    db_url = get_engine_url()
    print(f"📂 Loading MySQL project: {project_folder}")
    init_db(db_url)
    set_current_project_path(project_folder)
    return project_folder, "MySQL Database Active"
