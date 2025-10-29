#!/usr/bin/env python3
"""
Cleanup script for PythonAnywhere scheduled tasks
Run this daily to remove old media files and free up disk space
"""

import os
import sqlite3
from datetime import datetime, timedelta

# Configuration
UPLOAD_FOLDER = 'static/uploads'
SUBTITLE_FOLDER = 'static/subtitles'
DATABASE = 'mediafusion.db'
CLEANUP_HOURS = 24  # Delete files older than this many hours

def cleanup_old_files(hours=CLEANUP_HOURS):
    """Remove files older than specified hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Find old files
    old_files = c.execute(
        'SELECT * FROM media WHERE upload_date < ?',
        (cutoff,)
    ).fetchall()
    
    deleted_count = 0
    freed_space = 0
    
    for media in old_files:
        # Delete media file
        filepath = os.path.join(UPLOAD_FOLDER, media['filename'])
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            os.remove(filepath)
            freed_space += file_size
            deleted_count += 1
            print(f"Deleted: {media['filename']} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Delete associated subtitles
        subtitles = c.execute(
            'SELECT * FROM subtitles WHERE media_id = ?',
            (media['id'],)
        ).fetchall()
        
        for subtitle in subtitles:
            sub_path = os.path.join(SUBTITLE_FOLDER, subtitle['filename'])
            if os.path.exists(sub_path):
                os.remove(sub_path)
        
        # Delete from database
        c.execute('DELETE FROM subtitles WHERE media_id = ?', (media['id'],))
        c.execute('DELETE FROM analytics WHERE media_id = ?', (media['id'],))
        c.execute('DELETE FROM media WHERE id = ?', (media['id'],))
    
    conn.commit()
    conn.close()
    
    print(f"\nCleanup Summary:")
    print(f"Files deleted: {deleted_count}")
    print(f"Space freed: {freed_space / 1024 / 1024:.2f} MB")
    print(f"Cutoff date: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return deleted_count, freed_space

if __name__ == '__main__':
    print(f"Starting cleanup of files older than {CLEANUP_HOURS} hours...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        deleted, freed = cleanup_old_files()
        print("\n✓ Cleanup completed successfully")
    except Exception as e:
        print(f"\n✗ Error during cleanup: {str(e)}")
        raise
