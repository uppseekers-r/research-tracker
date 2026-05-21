import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- DATABASE SETUP ---
DB_FILE = "research_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    password TEXT, 
                    role TEXT)''')
    
    # Batches Table
    c.execute('''CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY, 
                    batch_name TEXT, 
                    researcher_email TEXT,
                    submission_link TEXT)''')
    
    # Sessions Table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT, 
                    session_number INTEGER, 
                    session_date TEXT)''')
    
    # Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY, 
                    batch_id TEXT, 
                    student_name TEXT, 
                    student_email TEXT,
                    student_phone TEXT)''')
    
    # Attendance & Metric Evaluations Table
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (
                    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT, 
                    session_number INTEGER,
                    status TEXT,
                    participation INTEGER,
                    curiosity INTEGER,
                    communication INTEGER,
                    research_depth INTEGER,
                    preparedness INTEGER,
                    understanding INTEGER,
                    work_completion INTEGER,
                    comments TEXT)''')
    
    # Submissions Table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
                    sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    batch_id TEXT,
                    session_number INTEGER,
                    submission_type TEXT,
                    file_name TEXT,
                    file_data BLOB,
                    submitted_at TEXT,
                    score TEXT,
                    suggestions TEXT,
                    status TEXT DEFAULT 'Pending')''')
    
    # Publications Table
    c.execute('''CREATE TABLE IF NOT EXISTS publications (
                    pub_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    task_name TEXT,
                    target_date TEXT,
                    status TEXT)''')

    # Seed an admin user if table is empty (Password: admin123)
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin@uppseekers.com", hashed_pw, "Admin"))
        
    conn.commit()
    conn.close()

init_db()

# --- DATABASE UTILITY FUNCTIONS ---
def run_query(query, params=(), fetch="all"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    if fetch == "all":
        data = c.fetchall()
    elif fetch == "one":
        data = c.fetchone()
    else:
        data = None
    conn.commit()
    conn.close()
    return data

def get_df(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- HELPER FUNCTIONS ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# --- WHATSAPP SIMULATOR (API Stub) ---
def send_whatsapp_alert(phone, message_type, details):
    """
    Mock function for WhatsApp Integration.
    To make this live, integrate APIs like Twilio, Waati, or Interakt here.
    """
    st.info(f"📱 [WhatsApp API Triggered] Target: {phone} | Type: {message_type}")

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Research Batch Portal", layout="wide", page_icon="🎓")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = ""
    st.session_state['user_role'] = ""

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.title("🎓 Research Batch Management Portal")
    st.subheader("Internal Team Login")
    
    with st.form("login_form"):
        email = st.text_input("Email Address").strip().lower()
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Login")
        
        if submit_login:
            user_data = run_query("SELECT password, role FROM users WHERE email = ?", (email,), fetch="one")
            if user_data and check_hashes(password, user_data[0]):
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = email
                st.session_state['user_role'] = user_data[1]
                st.success(f"Welcome back, {email}!")
                st.rerun()
            else:
                st.error("Invalid Email or Password. Please contact your system administrator.")
    st.stop()

# --- POST-LOGIN NAVIGATION ---
st.sidebar.title("Navigation")
st.sidebar.write(f"**Logged in as:** {st.session_state['user_email']}")
st.sidebar.info(f"Access Level: {st.session_state['user_role']}")

if st.sidebar.button("Log Out"):
    st.session_state['logged_in'] = False
    st.rerun()

# Determine navigation options based on role
if st.session_state['user_role'] == "Admin":
    menu = ["Dashboard & Analytics", "Manage Teams & Users", "Batch Architecture", "Researcher Workspace", "Student Submissions Portal"]
else:
    menu = ["Researcher Workspace", "Student Submissions Portal"]

choice = st.sidebar.radio("Go to", menu)

# --- VIEW 1: ADMIN USER MANAGEMENT ---
if choice == "Manage Teams & Users":
    st.header("👥 System Access & User Management")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Add Team Member")
        new_email = st.text_input("User Email").strip().lower()
        new_pw = st.text_input("Temporary Password", type="password")
        new_role = st.selectbox("Assign Access Level", ["Researcher", "Admin"])
        
        if st.button("Create Account"):
            if new_email and new_pw:
                try:
                    hashed = make_hashes(new_pw)
                    run_query("INSERT INTO users VALUES (?, ?, ?)", (new_email, hashed, new_role), fetch="none")
                    st.success(f"Successfully added {new_email} as {new_role}!")
                except sqlite3.IntegrityError:
                    st.error("This user account email already exists.")
            else:
                st.error("Please fill out all fields.")
                
    with col2:
        st.subheader("Current Accounts")
        users_df = get_df("SELECT email, role FROM users")
        st.dataframe(users_df, use_container_width=True)


# --- VIEW 2: BATCH ARCHITECTURE ---
elif choice == "Batch Architecture":
    st.header("🏗️ Batch Setup & Architecture")
    
    tab1, tab2, tab3 = st.tabs(["Create New Batch", "Add Students", "Schedule Sessions"])
    
    with tab1:
        st.subheader("Initialize a Research Batch")
        b_id = st.text_input("Unique Batch ID (e.g., BATCH-2026-A)")
        b_name = st.text_input("Batch Display Name")
        
        # Pull available researchers
        researchers = [r[0] for r in run_query("SELECT email FROM users WHERE role = 'Researcher'")]
        assigned_res = st.selectbox("Assign Initial Researcher", ["None"] + researchers)
        unique_link = st.text_input("Unique Assignment Drop Box Drive Link (Optional)")
        
        if st.button("Deploy Batch"):
            if b_id and b_name:
                run_query("INSERT OR REPLACE INTO batches VALUES (?, ?, ?, ?)", (b_id, b_name, assigned_res, unique_link), fetch="none")
                st.success(f"Batch {b_id} successfully synchronized.")
            else:
                st.error("Batch ID and Name are non-negotiable requirements.")
                
        st.subheader("Modify Existing Batches")
        batches_df = get_df("SELECT * FROM batches")
        st.dataframe(batches_df, use_container_width=True)
        
    with tab2:
        st.subheader("Enroll Students in Batch")
        target_b = st.selectbox("Select Target Batch", get_df("SELECT batch_id FROM batches")['batch_id'].tolist() if not get_df("SELECT batch_id FROM batches").empty else ["None"])
        
        s_id = st.text_input("Student Roll/ID")
        s_name = st.text_input("Full Name")
        s_email = st.text_input("Email")
        s_phone = st.text_input("WhatsApp Number (with country code, e.g., +91...)")
        
        if st.button("Enroll Student"):
            if target_b != "None" and s_id and s_name:
                run_query("INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?, ?)", (s_id, target_b, s_name, s_email, s_phone), fetch="none")
                st.success(f"Enrolled {s_name} into {target_b} successfully.")
            else:
                st.error("Ensure all fields are structured completely.")
                
        st.subheader("Roster Review")
        if target_b != "None":
            st.dataframe(get_df("SELECT * FROM students WHERE batch_id = ?", (target_b,)), use_container_width=True)

    with tab3:
        st.subheader("Map Class Sessions")
        target_b_sess = st.selectbox("Choose Batch", get_df("SELECT batch_id FROM batches")['batch_id'].tolist() if not get_df("SELECT batch_id FROM batches").empty else ["None"], key="sess_b")
        sess_num = st.number_input("Session Number", min_value=1, value=1, step=1)
        sess_date = st.date_input("Session Date Execution")
        
        if st.button("Log Planned Session"):
            run_query("INSERT INTO sessions (batch_id, session_number, session_date) VALUES (?, ?, ?)", (target_b_sess, sess_num, str(sess_date)), fetch="none")
            st.success(f"Session {sess_num} added to timeline for {target_b_sess}.")


# --- VIEW 3: RESEARCHER WORKSPACE ---
elif choice == "Researcher Workspace":
    st.header("📝 Researcher Evaluation Engine")
    
    # Filter batches based on assigned researcher role restrictions
    if st.session_state['user_role'] == "Researcher":
        my_batches = get_df("SELECT batch_id FROM batches WHERE researcher_email = ?", (st.session_state['user_email'],))['batch_id'].tolist()
    else:
        my_batches = get_df("SELECT batch_id FROM batches")['batch_id'].tolist() if not get_df("SELECT batch_id FROM batches").empty else []
        
    if not my_batches:
        st.warning("No active assigned cohorts found.")
    else:
        active_b = st.selectbox("Select Active Cohort", my_batches)
        
        task_tab, eval_tab = st.tabs(["📊 Publication & Milestone Tracker", "📈 Daily Class Evaluations"])
        
        with task_tab:
            st.subheader("Publication Progression Tasks")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                p_task = st.text_input("Milestone Name (e.g., Literature Review Draft)")
                p_date = st.date_input("Target Completion Goal Date")
                p_status = st.selectbox("Initial Status", ["Not Started", "In Progress", "Under Review", "Completed"])
                if st.button("Append Task Milestone"):
                    run_query("INSERT INTO publications (batch_id, task_name, target_date, status) VALUES (?,?,?,?)", (active_b, p_task, str(p_date), p_status), fetch="none")
            
            with col_t2:
                st.markdown("**Update Progress Track**")
                pub_records = get_df("SELECT * FROM publications WHERE batch_id = ?", (active_b,))
                if not pub_records.empty:
                    for idx, row in pub_records.iterrows():
                        new_stat = st.selectbox(f"Task: {row['task_name']} (Due: {row['target_date']})", ["Not Started", "In Progress", "Under Review", "Completed"], index=["Not Started", "In Progress", "Under Review", "Completed"].index(row['status']), key=f"pub_{row['pub_id']}")
                        if new_stat != row['status']:
                            run_query("UPDATE publications SET status = ? WHERE pub_id = ?", (new_stat, row['pub_id']), fetch="none")
                            st.rerun()
                else:
                    st.info("No current programmatic publication milestones logged.")

        with eval_tab:
            st.subheader("Session Metric Entry & Attendance")
            sessions_avail = get_df("SELECT DISTINCT session_number FROM sessions WHERE batch_id = ?", (active_b,))['session_number'].tolist()
            
            if not sessions_avail:
                st.error("No sessions mapped for this cohort yet. Inform your operations administrator.")
            else:
                target_s = st.selectbox("Target Session Execution Number", sessions_avail)
                students_in_b = get_df("SELECT student_id, student_name, student_phone FROM students WHERE batch_id = ?", (active_b,))
                
                if students_in_b.empty:
                    st.info("No students currently rostered in this cohort.")
                else:
                    st.markdown("---")
                    for _, s_row in students_in_b.iterrows():
                        with st.expander(f"Student: {s_row['student_name']} ({s_row['student_id']})"):
                            # Check if historical rating exists
                            hist = run_query("SELECT * FROM evaluations WHERE student_id = ? AND session_number = ?", (s_row['student_id'], target_s), fetch="one")
                            
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                att_status = st.selectbox("Attendance Status", ["Present", "Absent"], index=0 if not hist else ["Present", "Absent"].index(hist[3]), key=f"att_{s_row['student_id']}")
                                part = sk = st.slider("Class Participation", 1, 5, 3 if not hist else hist[4], key=f"p_{s_row['student_id']}")
                                cur = st.slider("Curiosity Matrix", 1, 5, 3 if not hist else hist[5], key=f"c_{s_row['student_id']}")
                            with c2:
                                comm = st.slider("Communication Skills", 1, 5, 3 if not hist else hist[6], key=f"cm_{s_row['student_id']}")
                                r_dpth = st.slider("Research Depth Execution", 1, 5, 3 if not hist else hist[7], key=f"rd_{s_row['student_id']}")
                                prep = st.slider("Preparedness Assessment", 1, 5, 3 if not hist else hist[8], key=f"pr_{s_row['student_id']}")
                            with c3:
                                und = st.slider("Core Understanding Metrics", 1, 5, 3 if not hist else hist[9], key=f"un_{s_row['student_id']}")
                                comp = st.slider("Work Completion Standards", 1, 5, 3 if not hist else hist[10], key=f"wc_{s_row['student_id']}")
                                comms = st.text_area("Qualitative Insights", value="" if not hist else hist[11], key=f"txt_{s_row['student_id']}")
                            
                            if st.button("Commit Performance Profile Record", key=f"btn_{s_row['student_id']}"):
                                if hist:
                                    run_query('''UPDATE evaluations SET status=?, participation=?, curiosity=?, communication=?, research_depth=?, preparedness=?, understanding=?, work_completion=?, comments=? WHERE eval_id=?''',
                                              (att_status, part, cur, comm, r_dpth, prep, und, comp, comms, hist[0]), fetch="none")
                                else:
                                    run_query('''INSERT INTO evaluations (student_id, session_number, status, participation, curiosity, communication, research_depth, preparedness, understanding, work_completion, comments) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                                              (s_row['student_id'], target_s, att_status, part, cur, comm, r_dpth, prep, und, comp, comms), fetch="none")
                                st.success("Record permanently committed.")
                                
                                # Automated WhatsApp Actions
                                if att_status == "Absent":
                                    send_whatsapp_alert(s_row['student_phone'], "Absenteeism Notification", f"Missed Session {target_s} for batch {active_b}")


# --- VIEW 4: STUDENT SUBMISSIONS PORTAL ---
elif choice == "Student Submissions Portal":
    st.header("📥 Global Assignments Repository")
    
    st.markdown("*(Note: For live workflows, students interact with this portal module directly via their own access layers or a public form counterpart).*")
    
    sub_tab, review_tab = st.tabs(["Upload New Artifact", "Evaluations & Correction Module"])
    
    with sub_tab:
        st.subheader("Asset Upload")
        all_b = get_df("SELECT batch_id FROM batches")['batch_id'].tolist() if not get_df("SELECT batch_id FROM batches").empty else ["None"]
        sel_b = st.selectbox("Target Pipeline Batch", all_b, key="sub_b")
        
        if sel_b != "None":
            students_avail = get_df("SELECT student_id, student_name FROM students WHERE batch_id = ?", (sel_b,))
            student_mapping = dict(zip(students_avail['student_name'], students_avail['student_id']))
            
            sel_student = st.selectbox("Identify Student Submitting", list(student_mapping.keys()) if not students_avail.empty else ["None"])
            sess_target = st.number_input("Session Reference Number", min_value=1, step=1)
            sub_type = st.selectbox("Artifact Stage Category", ["Standard Assignment/HW", "Draft Progression Project", "Final Research Masterwork"])
            
            uploaded_file = st.file_uploader("Attach Target Deliverable Asset", type=["pdf", "docx", "xlsx", "csv"])
            
            if st.button("Submit Asset Packet"):
                if sel_student != "None" and uploaded_file is not None:
                    file_bytes = uploaded_file.read()
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_query('''INSERT INTO submissions (student_id, batch_id, session_number, submission_type, file_name, file_data, submitted_at, status) VALUES (?,?,?,?,?,?,?, 'Pending')''',
                              (student_mapping[sel_student], sel_b, sess_target, sub_type, uploaded_file.name, file_bytes, now_str), fetch="none")
                    st.success("Asset logged in immutable repository framework successfully.")
                else:
                    st.error("Please explicitly provide target file buffers and data parameters.")

    with review_tab:
        st.subheader("Pending Evaluations Dashboard")
        pending_df = get_df("SELECT sub_id, student_id, batch_id, session_number, submission_type, file_name, status FROM submissions WHERE status = 'Pending'")
        
        if pending_df.empty:
            st.info("Excellent! Repository contains zero unrated deliverables.")
        else:
            st.dataframe(pending_df, use_container_width=True)
            sel_sub_id = st.selectbox("Choose Target Item ID to Evaluate", pending_df['sub_id'].tolist())
            
            if sel_sub_id:
                score_val = st.text_input("Enter Score Matrix (e.g., 90/100 or Grade A)")
                suggest = st.text_area("Correction Comments & Strategic Recommendations")
                
                if st.button("Finalize Grading Assessment Matrix"):
                    run_query("UPDATE submissions SET score = ?, suggestions = ?, status = 'Graded' WHERE sub_id = ?", (score_val, suggest, sel_sub_id), fetch="none")
                    st.success("Grading assessment architecture updated.")
                    st.rerun()


# --- VIEW 5: COMPLETE ADMIN VIEW & ANALYTICS ---
elif choice == "Dashboard & Analytics":
    st.header("🎛️ Enterprise Analytics & Cross-Cohort Telemetry")
    
    all_batches = get_df("SELECT batch_id FROM batches")['batch_id'].tolist() if not get_df("SELECT batch_id FROM batches").empty else []
    
    if not all_batches:
        st.info("System uninitialized with running batch models.")
    else:
        sel_b_an = st.selectbox("Target Core Performance Batch Focus", all_batches)
        
        # High level KPIs
        tot_students = run_query("SELECT COUNT(*) FROM students WHERE batch_id = ?", (sel_b_an,), fetch="one")[0]
        tot_sessions = run_query("SELECT COUNT(DISTINCT session_number) FROM sessions WHERE batch_id = ?", (sel_b_an,), fetch="one")[0]
        tot_subs = run_query("SELECT COUNT(*) FROM submissions WHERE batch_id = ?", (sel_b_an,), fetch="one")[0]
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Cohort Roster Count", tot_students)
        kpi2.metric("Executed Milestones Scheduled", tot_sessions)
        kpi3.metric("Artifact Submissions Cataloged", tot_subs)
        
        st.subheader("Roster Performance Analysis Index")
        evals_batch = get_df('''SELECT e.*, s.student_name FROM evaluations e JOIN students s ON e.student_id = s.student_id WHERE s.batch_id = ?''', (sel_b_an,))
        
        if not evals_batch.empty:
            # Pivot out numerical metrics to show clear progress over frames
            agg_perf = evals_batch.groupby('student_name')[['participation', 'curiosity', 'communication', 'research_depth', 'preparedness', 'understanding', 'work_completion']].mean()
            st.dataframe(agg_perf.style.background_gradient(cmap='Blues'), use_container_width=True)
            
            st.subheader("Granular Student Profile Deep Dive")
            sel_st_an = st.selectbox("Choose Student to Review", evals_batch['student_name'].unique())
            
            st.markdown(f"#### Profile Timeline: {sel_st_an}")
            st.dataframe(evals_batch[evals_batch['student_name'] == sel_st_an][['session_number', 'status', 'participation', 'curiosity', 'communication', 'research_depth', 'comments']], use_container_width=True)
        else:
            st.info("No recorded parameter evaluation metrics mapped to this batch yet.")