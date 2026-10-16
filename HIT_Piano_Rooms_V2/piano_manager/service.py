"""Business layer independent of tkinter; no external dependencies."""
import hashlib
import hmac
import secrets
import sqlite3

from .config import (ROOM_COUNT, MAX_STUDENTS, SLOT_HOURS, bookable_hours,
                     normalize_now, slot_label)
from .database import open_database


class PianoError(ValueError):
    """An actionable validation or state error shown to the user."""


def _clean(value, label, limit=49):
    if not isinstance(value, str) or not value.strip():
        raise PianoError(f'{label}不能为空。')
    value = value.strip()
    if len(value) > limit or any(ord(c) < 32 for c in value):
        raise PianoError(f'{label}不能超过{limit}个字符，且不得含控制字符。')
    return value


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 240_000)
    return 'pbkdf2_sha256$240000$' + salt.hex() + '$' + digest.hex()


def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not (10000 <= int(rounds) <= 1000000):
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(digest, bytes.fromhex(expected))
    except (ValueError, TypeError, AttributeError):
        return False


class PianoService:
    def __init__(self, path=':memory:', clock=None):
        self.db = open_database(path)
        self._clock = clock or (lambda: None)

    def now(self):
        return normalize_now(self._clock())

    def close(self):
        self.db.close()

    def register(self, student_id, name, class_name, instrument, password):
        student_id = _clean(student_id, '学号')
        if not student_id.isascii() or not student_id.isdecimal():
            raise PianoError('学号仅允许输入数字。')
        name = _clean(name, '姓名')
        class_name = _clean(class_name, '班级')
        instrument = _clean(instrument, '乐器')
        if not isinstance(password, str) or not (1 <= len(password) <= 128):
            raise PianoError('密码长度应为1～128个字符。')
        # Lock before counting to enforce the 2000-student cap across processes.
        self.db.execute('BEGIN IMMEDIATE')
        try:
            count = self.db.execute('SELECT COUNT(*) FROM students').fetchone()[0]
            if count >= MAX_STUDENTS:
                raise PianoError('已达到原项目2000名学生上限。')
            self.db.execute('''INSERT INTO students
                (student_id,name,class_name,instrument,password_hash,registered_at)
                VALUES(?,?,?,?,?,?)''', (student_id, name, class_name, instrument,
                hash_password(password), self.now().isoformat()))
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise PianoError('该学号已经注册，请直接使用原账号。') from exc
        except Exception:
            self.db.rollback()
            raise
        return student_id

    def _student(self, student_id):
        return self.db.execute('SELECT * FROM students WHERE student_id=?', (student_id,)).fetchone()

    def authenticate(self, student_id, password, name=None):
        student_id = _clean(student_id, '学号')
        row = self._student(student_id)
        if row is None or not verify_password(password, row['password_hash']):
            raise PianoError('学号或密码错误。')
        if name is not None and _clean(name, '姓名') != row['name']:
            raise PianoError('姓名与注册信息不一致。')
        return {'student_id': row['student_id'], 'name': row['name'],
                'class_name': row['class_name'], 'instrument': row['instrument']}

    def available_hours(self):
        return bookable_hours(self.now())

    def availability(self, hour):
        if hour not in SLOT_HOURS:
            raise PianoError('时间段必须在07:00～22:00范围内。')
        date = self.now().date().isoformat()
        occupied = {r[0] for r in self.db.execute(
            'SELECT room_no FROM reservations WHERE reservation_date=? AND slot_hour=?',
            (date, hour))}
        return [room for room in range(1, ROOM_COUNT + 1) if room not in occupied]

    def daily_summary(self):
        date = self.now().date().isoformat()
        booked = self.db.execute('SELECT COUNT(*) FROM reservations WHERE reservation_date=?', (date,)).fetchone()[0]
        signed_in = self.db.execute('''SELECT COUNT(*) FROM reservations
            WHERE reservation_date=? AND status='signed_in' ''', (date,)).fetchone()[0]
        current = self.now().hour
        current_free = len(self.availability(current)) if current in SLOT_HOURS else None
        return {'date': date, 'today_bookings': booked,
                'signed_in': signed_in, 'current_free': current_free}

    def book(self, student_id, password, hour, room_no):
        student = self.authenticate(student_id, password)
        if type(hour) is not int or hour not in SLOT_HOURS:
            raise PianoError('请选择有效的预约时间段。')
        if type(room_no) is not int or room_no not in range(1, ROOM_COUNT + 1):
            raise PianoError('请选择1～20号琴房。')
        now = self.now()
        if hour not in bookable_hours(now):
            raise PianoError('已过该时段预约截止时间（整点后30分钟），请选择其他时段。')
        try:
            # Guard read/insert in one database writer transaction.
            self.db.execute('BEGIN IMMEDIATE')
            if hour not in bookable_hours(self.now()):
                raise PianoError('操作期间已过预约截止时间，请重新选择。')
            cursor = self.db.execute('''INSERT INTO reservations
                (student_id,room_no,reservation_date,slot_hour,status,created_at)
                VALUES(?,?,?,?,?,?)''', (student['student_id'], room_no,
                now.date().isoformat(), hour, 'booked', now.isoformat()))
            self.db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            exists = self.db.execute('''SELECT 1 FROM reservations
                WHERE student_id=? AND reservation_date=? AND slot_hour=?''',
                (student['student_id'], now.date().isoformat(), hour)).fetchone()
            if exists:
                raise PianoError('您在该时间段已有预约，不能重复预约其他琴房。') from exc
            raise PianoError('该琴房刚被其他用户预约，请刷新后重新选择。') from exc
        except Exception:
            self.db.rollback()
            raise

    def reservations_for(self, student_id, password):
        self.authenticate(student_id, password)
        rows = self.db.execute('''SELECT id,room_no,reservation_date,slot_hour,status,
                       checked_in_at,checked_out_at FROM reservations
                   WHERE student_id=? ORDER BY reservation_date DESC,slot_hour DESC,id DESC''',
                   (student_id.strip(),)).fetchall()
        return [dict(row) for row in rows]

    def _reservation(self, reservation_id):
        if type(reservation_id) is not int or reservation_id <= 0:
            raise PianoError('请选择一条预约记录。')
        row = self.db.execute('SELECT * FROM reservations WHERE id=?', (reservation_id,)).fetchone()
        if row is None:
            raise PianoError('未找到预约记录。')
        return row

    def _assert_today(self, row):
        if row['reservation_date'] != self.now().date().isoformat():
            raise PianoError('仅允许操作当天预约的签到或签退。')

    def sign_in(self, reservation_id, student_id, name, password):
        self.authenticate(student_id, password, name)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self._reservation(reservation_id)
            if row['student_id'] != student_id.strip():
                raise PianoError('只能签到自己的预约。')
            self._assert_today(row)
            if row['status'] != 'booked':
                raise PianoError('该预约已经签到或签退，不能重复签到。')
            self.db.execute('''UPDATE reservations SET status='signed_in',checked_in_at=?
                WHERE id=?''', (self.now().isoformat(), reservation_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return f'签到成功！{row["room_no"]}号琴房，{slot_label(row["slot_hour"])}。请勿提前进入琴房。'

    def sign_out(self, reservation_id, student_id, name, password):
        self.authenticate(student_id, password, name)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self._reservation(reservation_id)
            if row['student_id'] != student_id.strip():
                raise PianoError('只能签退自己的预约。')
            self._assert_today(row)
            if row['status'] != 'signed_in':
                raise PianoError('只有已签到且尚未签退的预约才能签退。')
            now = self.now()
            scheduled_end = now.replace(hour=row['slot_hour'] + 1, minute=0, second=0, microsecond=0)
            # Inclusive minute count for use-time warning; later than planned end is overdue.
            overdue_seconds = max(0, (now - scheduled_end).total_seconds())
            overdue_minutes = int((overdue_seconds + 59) // 60)
            self.db.execute('''UPDATE reservations SET status='signed_out',checked_out_at=?
                WHERE id=?''', (now.isoformat(), reservation_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ('签退成功，未超时。请带好随身物品！' if not overdue_minutes else
                f'签退成功，超过预约结束时间约{overdue_minutes}分钟。请带好随身物品！')
