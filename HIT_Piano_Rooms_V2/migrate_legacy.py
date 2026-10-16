"""One-way, explicit importer for old students.txt and reservations.txt.

Old files are NEVER modified. pianoRooms.txt is intentionally ignored because it
has no date and may contain stale state. Booking state is derived from records.
"""
import argparse
from datetime import date
from pathlib import Path
import sqlite3

from piano_manager import PianoService, PianoError
from piano_manager.database import default_database_path
from piano_manager.config import SLOT_HOURS, ROOM_COUNT


def import_old_files(directory, db_path):
    directory = Path(directory)
    student_file = directory / 'students.txt'
    reservation_file = directory / 'reservations.txt'
    if not student_file.is_file() and not reservation_file.is_file():
        raise FileNotFoundError('指定目录中没有 students.txt 或 reservations.txt。')
    service = PianoService(db_path)
    report = {'students_imported': 0, 'students_skipped': 0,
              'reservations_imported': 0, 'reservations_skipped': 0}
    try:
        if student_file.is_file():
            # The original uses whitespace-separated fields. Malformed rows are skipped,
            # rather than guessing how to reconstruct names or credentials.
            for line in student_file.read_text(encoding='utf-8-sig', errors='replace').splitlines():
                fields = line.split()
                if len(fields) != 6 or fields[-1] != '1':
                    report['students_skipped'] += 1
                    continue
                try:
                    service.register(*fields[:5])
                    report['students_imported'] += 1
                except (PianoError, sqlite3.Error):
                    report['students_skipped'] += 1
        if reservation_file.is_file():
            for line in reservation_file.read_text(encoding='utf-8-sig', errors='replace').splitlines():
                fields = line.split()
                if len(fields) != 5:
                    report['reservations_skipped'] += 1
                    continue
                sid, room_text, slot_text, start_date, end_date = fields
                try:
                    room, slot = int(room_text), int(slot_text)
                    # Original C fprintf used %d-%d-%d (no zero padding).
                    def parse_legacy_date(value):
                        parts = value.split('-')
                        if len(parts) != 3 or not all(part.isdecimal() for part in parts):
                            raise ValueError('bad date')
                        return date(*(int(part) for part in parts)).isoformat()
                    start_date = parse_legacy_date(start_date)
                    end_date = parse_legacy_date(end_date)
                    if start_date != end_date or room not in range(1, ROOM_COUNT+1) or slot-1+7 not in SLOT_HOURS:
                        raise ValueError('bad room, slot or date')
                    if service._student(sid) is None:
                        raise ValueError('unknown student')
                    # Old timeSlot was 1..15 and encoded 07:00..21:00.
                    service.db.execute('''INSERT INTO reservations
                        (student_id,room_no,reservation_date,slot_hour,status,created_at)
                        VALUES(?,?,?,?,?,?)''',
                        (sid,room,start_date,slot+6,'booked',start_date+'T00:00:00+08:00'))
                    report['reservations_imported'] += 1
                except (ValueError, sqlite3.IntegrityError):
                    report['reservations_skipped'] += 1
    finally:
        service.close()
    return report


def main():
    parser = argparse.ArgumentParser(description='导入旧版C项目TXT数据（不会修改源文件）')
    parser.add_argument('--source', required=True, help='三个旧TXT文件所在目录')
    parser.add_argument('--db', default=str(default_database_path()))
    args = parser.parse_args()
    result = import_old_files(args.source, args.db)
    print('导入完成（已导入 / 已跳过）：')
    print('学生：',result['students_imported'],'/',result['students_skipped'])
    print('预约：',result['reservations_imported'],'/',result['reservations_skipped'])
    print('注意：原版不保存签到/签退状态，无法恢复这部分历史数据。')
    print('旧文件均未被修改。')


if __name__ == '__main__':
    main()
