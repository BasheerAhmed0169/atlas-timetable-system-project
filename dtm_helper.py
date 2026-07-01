# time and dat  functins


from datetime import datetime

DEPT_MAP = {
    "ai": "Artificial Intelligence", "artificial": "Artificial Intelligence",
    "civil": "Civil Engineering",
    "fashion": "Fashion Design",
    "textile": "Textile Design",
    "architecture": "Architecture", "arch": "Architecture",
    "environmental": "Environmental", "env": "Environmental",
    "visual": "Visual Arts", "arts": "Visual Arts",
    "multimedia": "Multimedia", "gaming": "Multimedia",
    "cyber": "Cyber Security", "security": "Cyber Security",
    "history": "History",
    "pakistan": "Pakistan Studies", "pks": "Pakistan Studies",
    "archaeology": "Archaeology",
    "digital": "Digital Art",
}


def get_now():
    now = datetime.now()
    day = now.strftime("%A")
    time = now.strftime("%H:%M:%S")   # ✅ FIXED
    return day, time
   # print(time) for cecking purpose

def fmt_time(t):
    if t is None:
        return ""

    if hasattr(t, "total_seconds"):  # timedelta
        total = int(t.total_seconds())
        h = total // 3600
        m = (total % 3600) // 60
    else:  # time
        h = t.hour
        m = t.minute

    am_pm = "AM" if h < 12 else "PM"
    h = h % 12 or 12

    return f"{h:02d}:{m:02d} {am_pm}"
def to_keyword(user_input):
    return DEPT_MAP.get(user_input.strip().lower(), user_input.strip())


print(get_now())
day,time=get_now()
print(day,time)