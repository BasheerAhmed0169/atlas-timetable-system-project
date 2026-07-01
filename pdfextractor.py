from datetime import datetime
import pdfplumber
import re


#patterng matching

RE_TITLE = re.compile(
    r"\b("
    r"(?:Prof\.?\s*Dr\.?|Prof\.?|Dr\.?|Engr\.?|Mr\.?|Ms\.?|Mrs\.?)"
    r"(?:\s+[A-Za-z]{2,}){1,3}"
    r")\b",
    re.I
)


RE_CODE = re.compile(r"\b([A-Z]{2,4}\d{3,4})\b")

RE_TIME = re.compile(
    r"(\d{1,2}:\d{2})\s*(AM|PM)?\s*[-–]\s*(\d{1,2}:\d{2})\s*(AM|PM)?",
    re.I
)




def clean(text):   # reoving unnecessary space
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text):   # removig html signs and spaces
    text = str(text or "")
    text = text.replace("&amp;amp;", "&amp;")
    text = text.replace("&amp;gt;", "&gt;")
    text = text.replace("&amp;lt;", "&lt;")
    text = re.sub(r"(Lab)([A-Z])", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# clean the whole text remove unwanted data
def clean_garbage(text):
    text = re.sub(r"[+]+", " ", text)
    text = re.sub(r"[^\w\s\-/()&amp;]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def to_24h(time_str, ampm):    
    h, m = map(int, time_str.split(":"))   # convert the time into sql format
    if ampm:
        ampm = ampm.upper()
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
    return f"{h:02d}:{m:02d}:00"


def build_col_time_map(table):
    col_map = {}    #slot maaping time 
    for row in table[:5]:
        for i, cell in enumerate(row or []):
            m = RE_TIME.search(clean(cell))
            if m:
                s_h, s_ap, e_h, e_ap = m.group(1), m.group(2), m.group(3), m.group(4)
                s_ap = s_ap or e_ap
                e_ap = e_ap or s_ap
                col_map[i] = (to_24h(s_h, s_ap), to_24h(e_h, e_ap))
        if col_map:
            break
    return col_map



def extract_building_room(text):
    text = normalize(text)    

    m = re.search(r"(B\d+)\s*-\s*(.+)", text, re.I)    # room extracting
    if m:
        return clean(m.group(1)), clean(m.group(2))

    patterns = [
        r"(LR\s*\d+)",
        r"(SR\s*\d+(?:\s*\([^)]*\))?)",
        r"(Computer\s+Lab\s*[IVXLC0-9]*)",
        r"(Physics\s+Lab)",
        r"(Library)",
        r"(Training\s+Hall)",
        r"(Seminar\s+Hall)",
        r"(Auditorium)",
        r"(Museum)",
        r"(Studio\s*\([^)]*\))",
        r"(Lab\s*[IVXLC0-9]*)",
    ]

    for pat in patterns:
        m2 = re.search(pat, text, re.I)
        if m2:
            return "", clean(m2.group(1))

    return "", ""

 

def extract_timetable(pdf_file):
    records = []                             # whole pdf extracting

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:

            tables = page.extract_tables()
            page_text = page.extract_text() or ""

            batch = program = semester = ""
            m = re.search(
                r"Timetable[:\s]+(.+?)\((\d+\w+\s+Semester)\)",
                page_text,
                re.I
            )
            if m:
                left = clean(m.group(1))
                semester = clean(m.group(2))
                batches = re.findall(r"[FS]-\d{2}", left)
                batch = " &amp; ".join(batches)
                parts = re.split(r"[FS]-\d{2}[\s&amp;]*", left)
                program = clean(parts[-1]).strip(" -")

            if not tables:
                continue

            table = max(tables, key=len)
            col_time_map = build_col_time_map(table)
            lecture_cols = sorted(col_time_map.keys())

            prev_cell_content = {}

            for row in table:
                if not row:
                    continue

                day_text = clean(row[0]).lower()
                day = None
                for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
                    if day_text in (d.lower(), d[::-1].lower()):
                        day = d
                        break
                if not day:
                    continue

                for col_idx in lecture_cols:

                    cell = row[col_idx]
                    cell_text = clean(cell) if cell else ""

                    
                    if not cell_text:
                        if col_idx - 1 in prev_cell_content:
                            cell_text = prev_cell_content[col_idx - 1]
                        else:
                            continue
                    else:
                        prev_cell_content[col_idx] = cell_text

                    text = normalize(cell_text)

                    if re.search(r"\b(break|kaerb)\b", text, re.I):
                        continue
                    #print(text)

                 
                    
                    code_match = RE_CODE.search(text)

                    if code_match:
                                  
                        teacher_part = text[:code_match.start()]
                    else:
   
                        teacher_part = text


                    teacher = " ".join(teacher_part.split()[:3])
                    teacher = clean(teacher)
                    print(teacher)


                    

                    # room class extrating
                    building, room = extract_building_room(text)

                    if room:
                        text = re.sub(re.escape(room), "", text, flags=re.I)
                    if building:
                        text = re.sub(re.escape(building), "", text, flags=re.I)
                    #print(room)

                   
                    subjects = re.split(r"\)\s*", text) # subject matching

                    start_t, end_t = col_time_map[col_idx]
                    slot_num = lecture_cols.index(col_idx) + 1

                    for sub in subjects:
                        sub = sub.strip()
                        if not sub:
                            continue

                        if "(" in sub and not sub.endswith(")"):
                            sub += ")"

                        code_m = RE_CODE.search(sub)
                        subject_code = code_m.group(1) if code_m else "N/A"

                        if code_m:
                            sub = sub.replace(subject_code, "").strip()

                        subject_name = re.sub(r"\(\d+\+\d+\)", "", sub)
                        subject_name = clean(subject_name)
                        
                        subject_name = re.sub(rf"^{re.escape(teacher)}\s*", "", subject_name, flags=re.I)
                        subject_name = clean(subject_name)


                        if len(subject_name) < 3:
                            continue

                        records.append({
                            "batch": batch,
                            "program": program,
                            "semester": semester,
                            "day": day,
                            "lecture_slot": slot_num,
                            "time_start": start_t,
                            "time_end": end_t,
                            "subject_code": subject_code,
                            "subject_name": subject_name,
                            "teacher": teacher,
                            "building": building,
                            "room": room,
                        })

    return records




if __name__ == "__main__":
    PDF = "D:/my_timetable/proj2/Program Wise (Spring 26).pdf"
    data = extract_timetable(PDF)

    print(f"Total Records: {len(data)}")
    print("-" * 100)

    for r in data:
        print(r)