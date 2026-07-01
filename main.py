
import io 
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd

import pdfextractor as extractor   # import the pdfextracto file

import database  as db                # import the db file 
import dtm_helper as helpers          # heleper functions
st.set_page_config(page_title="Aror University", layout="wide")
st_autorefresh(interval=1000, key="refresh")

try:
    db.create_database_and_tables()
except Exception as e:
    st.error(f"MySQL error: {e}  —  Set password in part2_database.py")
    st.stop()

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

with st.sidebar:
    col1, col2 = st.columns([1, 3])  # adjust ratio if needed

    with col1:
        st.image("logo.png", width=120)

    with col2:
        st.markdown("### Aror University")
    st.divider()
    page = st.radio("", ["Dashboard","Free Teachers","Free Rooms","Admin"],
                    label_visibility="collapsed")
    st.divider()
    now = datetime.now()
    st.write(f"{now.strftime('%I:%M %p')}")
    st.write(f"{now.strftime('%A, %d %b %Y')}")
    st.divider()
    try:
        s = db.get_stats()
        st.caption(f"Records : {s['total']}")
        st.caption(f"Teachers: {s['teachers']}")
        st.caption(f"Rooms   : {s['rooms']}")
        st.markdown("#####  Developers")
        st.caption("Basheer Ahmed & Nasreen Naz ")
# or
        st.caption("Team ATLAS")
    except Exception:
        st.caption("No data — upload PDF in Admin")


def day_time_selector():
    day, t = helpers.get_now()
    with st.expander("Change day  & Time"):
        day = st.selectbox("Day", DAYS, index=DAYS.index(day) if day in DAYS else 0)
        sel = st.time_input("Time", value=datetime.now().time())
        t   = sel.strftime("%H:%M:%S")
    return day, t


#  DASHBOARD 
if page == "Dashboard":
    st.title("ATLAS(Aror Timetable and live Allocation System)")
    day, t = day_time_selector()
    st.write(f"{day}  {datetime.strptime(t,'%H:%M:%S').strftime('%I:%M %p')}")
    st.divider()

    active = db.get_active_classes(day)

    if not active:
        st.warning("No classes running at this time.")
        
    else:
        by_building = {}
        for r in active:
            by_building.setdefault(r["building"] or "Unknown", []).append(r)

        for bld in sorted(by_building):
            st.subheader(f"Building {bld}  —  {len(by_building[bld])} class(es)")
            cols = st.columns(3)
            for i, r in enumerate(by_building[bld]):
                with cols[i % 3]:
                    st.success(
                        f"{r['subject_code']}  {r['subject_name']}\n\n"
                        f"{r['teacher'] or 'N/A'}\n\n"
                    f"{r['room']}\n\n"
                        f"{r['batch']}  {r['program']}\n\n"
                    f"{helpers.fmt_time(r['time_start'])} – {helpers.fmt_time(r['time_end'])}"
                )
        st.divider()


# for he free techers
elif page == "Free Teachers":
    st.title("Search Free Teachers by Department")
    day, t = day_time_selector()
    st.write(f"{day}  {datetime.strptime(t,'%H:%M:%S').strftime('%I:%M %p')}")
    st.divider()

    dept = st.text_input("Enter department name", placeholder="e.g. AI or Civil")

    if dept.strip():
        keyword = helpers.to_keyword(dept)
        free    = db.get_free_teachers(day, t, keyword)

        if not free:
            st.warning(f"No free teachers found for {keyword} right now.")
        else:
            st.success(f"{len(free)} free teacher(s) in {keyword}")
            st.divider()
            cols = st.columns(3)
            for i, name in enumerate(free):
                with cols[i % 3]:
                    st.success(f"{name}")
    else:
        st.info("Available programs: AI, Civil, Fashion, Textile, Architecture..")


# for the free rooms
elif page == "Free Rooms":
    st.title(" Search Free Rooms by building")
    day, t = day_time_selector()
    st.write(f"{day}  {datetime.strptime(t,'%H:%M:%S').strftime('%I:%M %p')}")
    st.divider()

    buildings = db.get_all_buildings()
    if not buildings:
        st.warning("No data. Upload PDF in Admin first.")
        st.stop()

    building = st.selectbox("Select Building", buildings)

    if building:
        free = db.get_free_rooms(day, t, building)

        if not free:
            st.warning(f"No free rooms in Building {building} right now.")
        else:
            st.success(f"{len(free)} free rooms in Building {building}")
            st.divider()
            cols = st.columns(3)
            for i, r in enumerate(free):
                with cols[i % 3]:
                    st.success(f"{r['room']} (Building {r['building']})")


# admin pasge
elif page == "Admin":
    st.title("Admin ")

    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if pwd == "admin123":
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("Wrong password.")
        st.caption("Default: admin123")
        st.stop()

    st.success("Logged in")
    if st.button("Logout"):
        st.session_state.admin_ok = False
        st.rerun()

    st.divider()

    try:
        s = db.get_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records",  s["total"])
    
    except Exception:
        pass

    st.divider()
    st.subheader("Upload PDF")

    uploaded = st.file_uploader("Choose PDF", type=["pdf"])
    replace  = st.checkbox("Replace existing data", value=True)

    if uploaded:
        if st.button("Extract and Save"):
            with st.spinner("Reading PDF..."):
                try:
                    rows = extractor.extract_timetable(io.BytesIO(uploaded.read()))
                    if not rows:
                        st.error("No data extracted.")
                    else:
                        if replace:
                            db.clear_timetable()
                        db.insert_rows(rows)
                        st.success(f"{len(rows)} records saved.")
                        st.dataframe(pd.DataFrame(rows[:10]), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.warning("Delete all records from database:")
    if st.button("Clear All Data"):
        db.clear_timetable()
        st.success("Cleared.")
        st.rerun()