import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from piano_manager import PianoService, PianoError
from piano_manager.config import BEIJING_TZ, bookable_hours, ANNOUNCEMENT
from migrate_legacy import import_old_files


def at(hour, minute=0, day=16):
    return datetime(2026, 10, day, hour, minute, tzinfo=BEIJING_TZ)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / 'db.sqlite3'
        self.current = at(8, 10)
        self.svc = PianoService(self.path, clock=lambda: self.current)
        self.svc.register('2024123456','张同学','计算机一班','钢琴','test-password')

    def tearDown(self):
        self.svc.close()
        self.dir.cleanup()

    def book(self, hour=9, room=1):
        return self.svc.book('2024123456','test-password',hour,room)

    def test_password_hash_and_authentication(self):
        stored = self.svc.db.execute('SELECT password_hash FROM students').fetchone()[0]
        self.assertNotIn('test-password', stored)
        self.assertEqual('张同学', self.svc.authenticate('2024123456','test-password')['name'])
        with self.assertRaises(PianoError):
            self.svc.authenticate('2024123456', 'wrong')

    def test_unique_student_and_bad_data(self):
        with self.assertRaises(PianoError):
            self.svc.register('2024123456','x','y','z','p')
        with self.assertRaises(PianoError):
            self.svc.register('abc','x','y','z','p')
        with self.assertRaises(PianoError):
            self.svc.register('2024123457','', 'y','z','p')

    def test_half_hour_boundary(self):
        self.assertIn(8, bookable_hours(at(8,29)))
        self.assertNotIn(8, bookable_hours(at(8,30)))
        self.assertEqual((), bookable_hours(at(21,30)))
        self.assertEqual(15, len(bookable_hours(at(6,45))))
        self.assertEqual((), bookable_hours(at(22,0)))

    def test_booking_slots_rooms_and_remaining_count(self):
        self.assertEqual(20, len(self.svc.availability(9)))
        rid = self.book()
        self.assertGreater(rid, 0)
        self.assertEqual(19, len(self.svc.availability(9)))
        with self.assertRaises(PianoError):
            self.book(room=21)
        with self.assertRaises(PianoError):
            self.book(hour=22)

    def test_no_double_booking_room_or_student(self):
        self.book()
        self.svc.register('2024000001','李同学','电子班','小提琴','p')
        with self.assertRaisesRegex(PianoError, '已有预约'):
            self.book(room=2)
        with self.assertRaisesRegex(PianoError, '被其他用户'):
            self.svc.book('2024000001','p',9,1)
        self.assertEqual(1, len(self.svc.reservations_for('2024123456','test-password')))

    def test_one_slot_cutoff_and_after_close(self):
        self.current = at(9,30)
        with self.assertRaises(PianoError):
            self.book(hour=9)
        self.assertGreater(self.book(hour=10), 0)
        self.current = at(21,30)
        with self.assertRaises(PianoError):
            self.book(hour=21)

    def test_signin_signout_lifecycle_and_overtime(self):
        rid = self.book()
        self.assertIn('签到成功', self.svc.sign_in(rid,'2024123456','张同学','test-password'))
        with self.assertRaisesRegex(PianoError, '重复签到'):
            self.svc.sign_in(rid,'2024123456','张同学','test-password')
        self.current = at(10,7)
        self.assertIn('7分钟', self.svc.sign_out(rid,'2024123456','张同学','test-password'))
        with self.assertRaisesRegex(PianoError, '尚未签退'):
            self.svc.sign_out(rid,'2024123456','张同学','test-password')
        rows = self.svc.reservations_for('2024123456','test-password')
        self.assertEqual('signed_out', rows[0]['status'])
        self.assertTrue(rows[0]['checked_in_at'])
        self.assertTrue(rows[0]['checked_out_at'])

    def test_no_signout_before_signin_and_no_wrong_identity(self):
        rid = self.book()
        with self.assertRaises(PianoError):
            self.svc.sign_out(rid,'2024123456','张同学','test-password')
        with self.assertRaises(PianoError):
            self.svc.sign_in(rid,'2024123456','李同学','test-password')

    def test_data_survives_restart(self):
        rid = self.book()
        self.svc.sign_in(rid,'2024123456','张同学','test-password')
        self.svc.close()
        self.svc = PianoService(self.path, clock=lambda: self.current)
        self.assertEqual('signed_in', self.svc.reservations_for('2024123456','test-password')[0]['status'])
        self.assertEqual(19, len(self.svc.availability(9)))

    def test_next_day_occupancy_independent_and_actions_blocked(self):
        rid = self.book()
        self.current = at(8,10,day=17)
        self.assertEqual(20, len(self.svc.availability(9)))
        with self.assertRaises(PianoError):
            self.svc.sign_in(rid,'2024123456','张同学','test-password')
        self.assertGreater(self.book(), 0)

    def test_announcement_kept(self):
        self.assertIn('发布日期：2024年12月1日', ANNOUNCEMENT)
        self.assertIn('禁止饮食', ANNOUNCEMENT)

    def test_legacy_import_non_destructive(self):
        folder = Path(self.dir.name) / 'legacy_files'
        folder.mkdir()
        s = folder / 'students.txt'
        r = folder / 'reservations.txt'
        s.write_text('2024999999 王同学 物理班 长笛 abc123 1\n')
        r.write_text('2024999999 3 5 2024-12-5 2024-12-5\n')
        counts = import_old_files(folder, self.path)
        self.assertEqual(1, counts['students_imported'])
        self.assertEqual(1, counts['reservations_imported'])
        self.assertEqual(11, self.svc.db.execute('SELECT slot_hour FROM reservations WHERE student_id="2024999999"').fetchone()[0])
        self.assertEqual('2024999999 王同学 物理班 长笛 abc123 1\n', s.read_text())


if __name__ == '__main__':
    unittest.main()

class MultiConnectionTests(unittest.TestCase):
    def test_conflicts_across_two_process_like_connections(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'concurrent.sqlite3'
            one = PianoService(path, clock=lambda: at(14, 12))
            two = PianoService(path, clock=lambda: at(14, 12))
            try:
                one.register('100001', '甲', '一班', '钢琴', 'p1')
                two.register('100002', '乙', '二班', '钢琴', 'p2')
                one.book('100001', 'p1', 15, 1)
                with self.assertRaises(PianoError):
                    two.book('100002', 'p2', 15, 1)
                self.assertEqual(19, len(two.availability(15)))
                two.book('100002', 'p2', 15, 2)
                self.assertEqual(18, len(one.availability(15)))
            finally:
                one.close()
                two.close()

    def test_no_second_checkout_releases_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            svc = PianoService(Path(directory) / 'test.sqlite3', clock=lambda: at(15, 5))
            try:
                svc.register('100001', '甲', '一班', '钢琴', 'p1')
                rid = svc.book('100001', 'p1', 16, 1)
                svc.sign_in(rid, '100001', '甲', 'p1')
                svc.sign_out(rid, '100001', '甲', 'p1')
                self.assertEqual(19, len(svc.availability(16)))
            finally:
                svc.close()
