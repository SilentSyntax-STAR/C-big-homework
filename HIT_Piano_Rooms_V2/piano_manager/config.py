"""Rules extracted from the original 2024 C homework; use Beijing time."""
from datetime import datetime, timedelta, timezone

ROOM_COUNT = 20
MAX_STUDENTS = 2000
OPEN_HOUR = 7
CLOSE_HOUR = 22
SLOT_HOURS = tuple(range(OPEN_HOUR, CLOSE_HOUR))
HALF_HOUR_CUTOFF = 30
BEIJING_TZ = timezone(timedelta(hours=8), '北京时间')

ANNOUNCEMENT = '''琴房使用公告：

尊敬的各位使用者：

为了维护琴房的良好秩序与环境，确保每位使用者都能享受到高质量的练习时间，特此发布以下使用规定，请大家共同遵守：

1.预约制度：琴房实行预约使用制度，请提前通过指定渠道（如学校官网、微信公众号等）进行预约，并按时到场使用。未预约者不得进入琴房。
2.使用时间：琴房每日开放时间为早7:00至晚22:00，请合理安排练习时间，避免超时占用。
3.爱护设施：请爱护琴房内的各项设施，如钢琴、座椅、节拍器等，使用完毕后请归还原位，并保持整洁。如有损坏，需按价赔偿。
4.禁止饮食：琴房内禁止食用任何食物或饮料，以保持环境清洁与卫生。
5.个人物品：请妥善保管好个人物品，如有遗失，责任自负。
6.遵守规定：请严格遵守琴房的各项规定，如有违反，将视情节轻重给予警告、取消使用资格等处罚。

感谢大家的理解与配合！让我们共同营造一个和谐、有序、高效的琴房环境。

琴房管理办公室
发布日期：2024年12月1日'''


def china_now():
    return datetime.now(BEIJING_TZ)


def normalize_now(value=None):
    """All date/time policy decisions use the campus's UTC+8 clock."""
    value = value or china_now()
    return value.replace(tzinfo=BEIJING_TZ) if value.tzinfo is None else value.astimezone(BEIJING_TZ)


def bookable_hours(now=None):
    """A slot stops being bookable at HH:30, matching the original code."""
    now = normalize_now(now)
    first = max(OPEN_HOUR, now.hour + (now.minute >= HALF_HOUR_CUTOFF))
    return tuple(h for h in SLOT_HOURS if h >= first)


def slot_label(hour):
    return f'{hour:02d}:00 – {hour + 1:02d}:00'
