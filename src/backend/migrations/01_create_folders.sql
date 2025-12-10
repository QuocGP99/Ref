-- folders
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL
);

-- photo_folder (N-1)
CREATE TABLE IF NOT EXISTS photo_folder (
    photo_id INTEGER NOT NULL,
    folder_id INTEGER NOT NULL,
    PRIMARY KEY(photo_id),
    FOREIGN KEY(photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);
