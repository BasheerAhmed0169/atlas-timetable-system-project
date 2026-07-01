# database.py
# All MySQL database operations

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Basheer@339",   # apna MySQL password
    "database": "uni_timetabl",
}


def conn():
    return mysql.connector.connect(**DB_CONFIG)


def create_database_and_tables():
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    c = mysql.connector.connect(**cfg)
    cur = c.cursor()

    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cur.execute(f"USE {DB_CONFIG['database']}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            batch        VARCHAR(60),
            program      VARCHAR(160),
            semester     VARCHAR(30),
            day          VARCHAR(15),
            lecture_slot VARCHAR(5),
            time_start   TIME,
            time_end     TIME,
            subject_code VARCHAR(20),
            subject_name VARCHAR(255),
            teacher      VARCHAR(120),
            building     VARCHAR(60),
            room         VARCHAR(100)
        )
    """)

    c.commit()
    cur.close()
    c.close()


def clear_timetable():
    c = conn()
    cur = c.cursor()
    cur.execute("DELETE FROM timetable")
    c.commit()
    cur.close()
    c.close()


def insert_rows(rows):
    if not rows:
        return

    cleaned = []
    seen = set()

    for r in rows:
        key = (
            r["day"],
            r["time_start"],
            r["time_end"],
            r["building"],
            r["room"]
        )

        # ✅ same room + same slot duplicate skip
        if r["room"] and key in seen:
            continue

        seen.add(key)
        cleaned.append(r)

    c = conn()
    cur = c.cursor()

    sql = """
        INSERT INTO timetable
        (batch, program, semester, day, lecture_slot, time_start, time_end,
         subject_code, subject_name, teacher, building, room)
        VALUES
        (%(batch)s, %(program)s, %(semester)s, %(day)s, %(lecture_slot)s,
         %(time_start)s, %(time_end)s, %(subject_code)s, %(subject_name)s,
         %(teacher)s, %(building)s, %(room)s)
    """

    cur.executemany(sql, cleaned)
    c.commit()
    cur.close()
    c.close()



def get_active_classes(day):
    c = conn()
    cur = c.cursor(dictionary=True)

    cur.execute("""
        SELECT batch, program, semester, subject_code, subject_name,
               teacher, building, room, time_start, time_end
        FROM timetable
        WHERE day = %s
          AND time_start <= CURTIME()
          AND time_end  >  CURTIME()
        ORDER BY building, room
    """, (day,))

    rows = cur.fetchall()
    cur.close()
    c.close()
    return rows


def get_all_buildings():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT DISTINCT building
        FROM timetable
        WHERE building != ''
        ORDER BY building
    """)

    result = [r[0] for r in cur.fetchall()]
    cur.close()
    c.close()
    return result


def get_free_rooms(day, time, building):
    c = conn()
    cur = c.cursor(dictionary=True)

    # all rooms in this building
    cur.execute("""
        SELECT DISTINCT building, room
        FROM timetable
        WHERE building = %s AND room != ''
        ORDER BY room
    """, (building,))
    all_rooms = cur.fetchall()

    # occupied right now
    cur.execute("""
        SELECT DISTINCT building, room
        FROM timetable
        WHERE building = %s
          AND day = %s
          AND time_start <= %s
          AND time_end > %s
    """, (building, day, time, time))
    occupied = {(r["building"], r["room"]) for r in cur.fetchall()}

    cur.close()
    c.close()

    return [r for r in all_rooms if (r["building"], r["room"]) not in occupied]


def get_free_teachers(day, time, keyword):
    c = conn()
    cur = c.cursor()

    # teachers of selected department/program
    cur.execute("""
        SELECT DISTINCT teacher
        FROM timetable
        WHERE program LIKE %s
          AND teacher != ''
          AND teacher != 'Unknown'
    """, (f"%{keyword}%",))
    dept_teachers = {r[0] for r in cur.fetchall()}

    # busy right now
    cur.execute("""
        SELECT DISTINCT teacher
        FROM timetable
        WHERE day = %s
          AND time_start <= %s
          AND time_end > %s
          AND teacher != ''
          AND teacher != 'Unknown'
    """, (day, time, time))
    busy_teachers = {r[0] for r in cur.fetchall()}

    cur.close()
    c.close()

    return sorted(dept_teachers - busy_teachers)


def get_all_programs():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT DISTINCT program
        FROM timetable
        WHERE program != ''
        ORDER BY program
    """)

    result = [r[0] for r in cur.fetchall()]
    cur.close()
    c.close()
    return result


def get_stats():
    c = conn()
    cur = c.cursor()

    cur.execute("SELECT COUNT(*) FROM timetable")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT teacher)
        FROM timetable
        WHERE teacher != '' AND teacher != 'Unknown'
    """)
    teachers = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT CONCAT(building, '-', room))
        FROM timetable
        WHERE building != '' AND room != ''
    """)
    rooms = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT program)
        FROM timetable
        WHERE program != ''
    """)
    programs = cur.fetchone()[0]

    cur.close()
    c.close()

    return {
        "total": total,
        "teachers": teachers,
        "rooms": rooms,
        "programs": programs,
    }