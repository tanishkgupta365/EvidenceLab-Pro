import os, io, json, hashlib, sqlite3, mimetypes, subprocess, shutil
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
import streamlit as st
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
REPORT_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "evidencelab.db"
for p in (DATA_DIR, EVIDENCE_DIR, REPORT_DIR): p.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="FSL EvidenceLab Pro", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY, title TEXT NOT NULL, examiner TEXT, notes TEXT, created_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, original_name TEXT NOT NULL,
            stored_path TEXT NOT NULL, mime_type TEXT, size_bytes INTEGER, sha256 TEXT NOT NULL,
            registered_at TEXT NOT NULL, description TEXT, FOREIGN KEY(case_id) REFERENCES cases(case_id))""")
        con.execute("""CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_time TEXT NOT NULL, case_id TEXT,
            evidence_id TEXT, action TEXT NOT NULL, details TEXT)""")
        con.execute("PRAGMA foreign_keys=ON")

def audit(action, case_id=None, evidence_id=None, details=""):
    with connect() as con:
        con.execute("INSERT INTO audit(event_time,case_id,evidence_id,action,details) VALUES(?,?,?,?,?)",
                    (now(), case_id, evidence_id, action, details[:2000]))

def sha256_bytes(data):
    h=hashlib.sha256()
    for i in range(0,len(data),1024*1024): h.update(data[i:i+1024*1024])
    return h.hexdigest()

def get_cases():
    with connect() as con: return con.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()

def get_evidence(case_id=None):
    with connect() as con:
        if case_id:
            return con.execute("SELECT * FROM evidence WHERE case_id=? ORDER BY registered_at DESC",(case_id,)).fetchall()
        return con.execute("SELECT * FROM evidence ORDER BY registered_at DESC").fetchall()

def get_audit(case_id=None):
    with connect() as con:
        if case_id:
            return con.execute("SELECT * FROM audit WHERE case_id=? ORDER BY id DESC",(case_id,)).fetchall()
        return con.execute("SELECT * FROM audit ORDER BY id DESC").fetchall()

init_db()

st.markdown("""
<style>
:root { --ink:#173b39; --teal:#16796f; --mint:#dff3ee; --paper:#f5f8f7; --line:#dbe6e2; }
.stApp {background:linear-gradient(180deg,#f5f8f7 0%,#eef4f1 100%);color:#1d302f;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#123f3c 0%,#0c302f 100%);border-right:1px solid #245b55;}
[data-testid="stSidebar"] * {color:#f0fbf8 !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#c5ded8 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:7px 10px;border-radius:9px;margin:2px 0;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#245750;}
.block-container {padding-top:1.6rem;padding-bottom:2.5rem;max-width:1450px;}
.hero {padding:27px 30px;background:linear-gradient(120deg,#ffffff 0%,#e8f7f2 100%);border:1px solid #d6e8e2;border-left:6px solid #168577;border-radius:18px;margin-bottom:24px;box-shadow:0 8px 26px rgba(17,65,58,.06);}
.hero-kicker {color:#16796f;font-size:.75rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;}
.metric-card {background:#ffffff;border:1px solid var(--line);padding:19px;border-radius:15px;box-shadow:0 5px 18px rgba(16,57,51,.045);min-height:116px;}
.small-muted {color:#667b76;font-size:.88rem;}
div[data-testid="stMetric"] {background:#ffffff;border:1px solid var(--line);padding:15px 17px;border-radius:15px;box-shadow:0 5px 18px rgba(16,57,51,.045);}
div[data-testid="stMetricLabel"] {color:#607872;font-weight:600;}
div[data-testid="stMetricValue"] {color:#173b39;font-weight:750;}
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] button {border-radius:10px;font-weight:700;border:1px solid #c5dcd5;min-height:2.7rem;transition:all .15s ease;}
.stButton>button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {background:#16796f;color:white;border-color:#16796f;}
.stButton>button:hover, .stDownloadButton>button:hover {border-color:#16796f;color:#116b62;box-shadow:0 4px 12px rgba(22,121,111,.12);}
div[data-testid="stDataFrame"] {border:1px solid var(--line);border-radius:12px;overflow:hidden;}
[data-testid="stExpander"] {background:#fff;border:1px solid var(--line);border-radius:12px;}
[data-testid="stAlert"] {border-radius:12px;}
h1,h2,h3,h4 {color:#173b39;letter-spacing:-.02em;}
hr {border-color:#dbe6e2;}
</style>
""", unsafe_allow_html=True)

PAGES = ["Overview", "Case Management", "Evidence Intake", "Integrity Verification", "Audio Lab", "Video Lab", "Chain of Custody", "Reports & Audit", "About / Viva"]
def nav_to(destination):
    st.session_state["page_selector"] = destination

with st.sidebar:
    st.markdown("<div style='font-size:1.65rem;font-weight:850;letter-spacing:-.04em'>◈ EvidenceLab</div>", unsafe_allow_html=True)
    st.caption("DIGITAL EVIDENCE WORKBENCH")
    st.markdown("<div style='padding:8px 10px;background:#1c514b;border-radius:10px;margin:10px 0 14px;font-size:.77rem'>● LOCAL WORKSPACE &nbsp; · &nbsp; OFFLINE DATA</div>", unsafe_allow_html=True)
    page = st.radio("NAVIGATION", PAGES, key="page_selector", label_visibility="visible")
    st.divider()
    st.caption("ACADEMIC PROTOTYPE • SQLITE • SHA-256")
    st.caption("Use only authorized or synthetic sample evidence.")

cases = get_cases()
evidence = get_evidence()
audits = get_audit()
total_size = sum(int(e["size_bytes"] or 0) for e in evidence)
case_ids = [c["case_id"] for c in cases]

def case_select(label="Select case"):
    if not case_ids:
        st.warning("Create a case first in Case Management.")
        return None
    return st.selectbox(label, case_ids, format_func=lambda x: f"{x} — {next((c['title'] for c in cases if c['case_id']==x), '')}")

def evidence_select(case_id=None, label="Select evidence"):
    rows = get_evidence(case_id)
    if not rows:
        st.info("No evidence registered for this selection yet.")
        return None
    ids = [r["evidence_id"] for r in rows]
    return st.selectbox(label, ids, format_func=lambda x: f"{x} — {next(r['original_name'] for r in rows if r['evidence_id']==x)}")

def row_for_evidence(eid):
    with connect() as con:
        return con.execute("SELECT * FROM evidence WHERE evidence_id=?",(eid,)).fetchone()

def file_bytes(row):
    p=Path(row["stored_path"])
    if not p.exists(): raise FileNotFoundError("Stored evidence file is missing.")
    return p.read_bytes()

def probe_media(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe: return None, "FFprobe is not installed; showing available basic file information."
    cmd=[ffprobe,"-v","error","-show_format","-show_streams","-of","json",str(path)]
    try:
        out=subprocess.run(cmd,capture_output=True,text=True,timeout=20,check=True)
        return json.loads(out.stdout), None
    except Exception as ex: return None, f"FFprobe could not inspect this file: {ex}"

def register_uploaded(upload, case_id, description):
    data=upload.getvalue()
    digest=sha256_bytes(data)
    eid="EVD-"+datetime.now().strftime("%y%m%d%H%M%S")+"-"+digest[:6].upper()
    safe_name=Path(upload.name).name.replace("..","_")
    dest=EVIDENCE_DIR/f"{eid}_{safe_name}"
    dest.write_bytes(data)
    mime=mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    with connect() as con:
        con.execute("""INSERT INTO evidence(evidence_id,case_id,original_name,stored_path,mime_type,size_bytes,sha256,registered_at,description)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (eid,case_id,safe_name,str(dest),mime,len(data),digest,now(),description))
    audit("EVIDENCE_REGISTERED",case_id,eid,f"Registered {safe_name}; SHA-256={digest}; size={len(data)} bytes")
    return eid,digest

st.markdown('<div class="hero"><div class="hero-kicker">Digital multimedia examination · Academic prototype</div><h1 style="margin:8px 0 0;color:#173b39;font-size:2.15rem">Digital Evidence Examination Workbench</h1><p style="margin:8px 0 0;color:#49645e;font-size:1.05rem">A structured workspace for case records, media review and file-integrity checks.</p><div class="small-muted" style="margin-top:9px">Student-built local application · Not official FSL software or a certified forensic tool</div></div>', unsafe_allow_html=True)

if page=="Overview":
    st.markdown("## Workspace overview")
    st.caption("Live totals are calculated from this computer's local SQLite database.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Registered cases",len(cases),help="Cases saved in the local database")
    c2.metric("Evidence items",len(evidence),help="Files registered into this prototype")
    c3.metric("Audit events",len(audits),help="Application actions logged")
    c4.metric("Evidence storage",f"{total_size/1024/1024:.2f} MB",help="Size of registered evidence copies")
    st.markdown("## Start an examination")
    st.caption("Use the quick actions below to open a working page. Create the synthetic demo first if you want immediate sample output.")
    q1,q2,q3=st.columns([1.15,1,1])
    with q1:
        st.markdown('<div class="metric-card"><div class="hero-kicker">01 · Best first step</div><h3>Create a demo case</h3><p class="small-muted">Generate a clearly labelled sample case and 3-second synthetic WAV file.</p></div>',unsafe_allow_html=True)
        if st.button("Create demo data",type="primary",use_container_width=True):
            try:
                import wave, math, struct
                stamp=datetime.now().strftime("%y%m%d%H%M%S%f")
                demo_case=f"DEMO-{stamp}"
                wav_name="synthetic_test_tone.wav"
                wav_path=EVIDENCE_DIR/f"{demo_case}_{wav_name}"
                sample_rate=16000
                with wave.open(str(wav_path), "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
                    frames=[]
                    for i in range(sample_rate*3):
                        t=i/sample_rate
                        amp=int(9000*math.sin(2*math.pi*(440 if t<1.5 else 660)*t))
                        frames.append(struct.pack("<h", amp))
                    wf.writeframes(b"".join(frames))
                digest=sha256_bytes(wav_path.read_bytes())
                ev_id=f"EVD-{stamp}"
                with connect() as con:
                    con.execute("INSERT INTO cases VALUES(?,?,?,?,?)", (demo_case,"Synthetic audio test — generated sample","Student demo","Generated locally for software demonstration; not real evidence.",now()))
                    con.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?)", (ev_id,demo_case,wav_name,str(wav_path),"audio/wav",wav_path.stat().st_size,digest,now(),"Synthetic 3-second tone generated by this app for testing."))
                audit("DEMO_CASE_CREATED",demo_case,None,"Created synthetic demonstration case and WAV sample.")
                audit("EVIDENCE_REGISTERED",demo_case,ev_id,f"Synthetic sample registered; SHA-256={digest}")
                st.session_state["demo_created_message"] = f"Demo case {demo_case} and sample WAV created successfully."
                st.rerun()
            except Exception as ex:
                st.error(f"Could not create demo sample: {ex}")
    with q2:
        st.markdown('<div class="metric-card"><div class="hero-kicker">02 · Register files</div><h3>Evidence intake</h3><p class="small-muted">Save an authorized sample file and calculate its SHA-256 digest.</p></div>',unsafe_allow_html=True)
        st.button("Open evidence intake",use_container_width=True,on_click=nav_to,args=("Evidence Intake",))
    with q3:
        st.markdown('<div class="metric-card"><div class="hero-kicker">03 · Export results</div><h3>Reports & audit</h3><p class="small-muted">Review case records and export JSON, PDF and CSV summaries.</p></div>',unsafe_allow_html=True)
        st.button("Open reports",use_container_width=True,on_click=nav_to,args=("Reports & Audit",))
    if st.session_state.get("demo_created_message"):
        st.success(st.session_state.pop("demo_created_message"))
    st.markdown("## Examination workflow")
    cols=st.columns(5)
    for col,num,title,desc,dest in zip(cols,["01","02","03","04","05"],["Create case","Register file","Verify hash","Inspect media","Export report"],["Case metadata","Local evidence copy","SHA-256 comparison","Audio / video tools","PDF + JSON records"],["Case Management","Evidence Intake","Integrity Verification","Audio Lab","Reports & Audit"]):
        with col:
            st.markdown(f'<div class="metric-card"><div class="hero-kicker">STEP {num}</div><h4 style="margin:9px 0">{title}</h4><div class="small-muted">{desc}</div></div>',unsafe_allow_html=True)
            st.button(f"Open {title.lower()}",key=f"workflow_{num}",use_container_width=True,on_click=nav_to,args=(dest,))
    st.markdown("## Recent evidence")
    if evidence:
        st.dataframe(pd.DataFrame([dict(r) for r in evidence[:8]])[["evidence_id","case_id","original_name","size_bytes","sha256","registered_at"]],use_container_width=True,hide_index=True)
    else:
        st.info("No evidence registered yet. Click **Create demo data** above to generate real sample output immediately.")
    st.markdown("### Recent evidence")
    if evidence:
        st.dataframe(pd.DataFrame([dict(r) for r in evidence[:8]])[["evidence_id","case_id","original_name","size_bytes","sha256","registered_at"]],use_container_width=True,hide_index=True)
    else:
        st.caption("No evidence yet. Start in Case Management.")

elif page=="Case Management":
    st.subheader("Case management")
    with st.form("case_form",clear_on_submit=True):
        c1,c2=st.columns(2)
        case_id=c1.text_input("Case ID *",placeholder="FSL-DEMO-001")
        title=c2.text_input("Case title *",placeholder="Audio-video examination demo")
        examiner=c1.text_input("Examiner / student name",placeholder="Tanishk Gupta")
        notes=c2.text_area("Case notes",placeholder="Academic demonstration using authorized sample media.")
        submitted=st.form_submit_button("＋ Create case",use_container_width=True)
    if submitted:
        if not case_id.strip() or not title.strip():
            st.error("Case ID and title are required.")
        else:
            try:
                with connect() as con: con.execute("INSERT INTO cases VALUES(?,?,?,?,?)",(case_id.strip(),title.strip(),examiner.strip(),notes.strip(),now()))
                audit("CASE_CREATED",case_id.strip(),None,f"Created case: {title.strip()}")
                st.success("Case created successfully.")
                st.rerun()
            except sqlite3.IntegrityError: st.error("That Case ID already exists. Choose a unique ID.")
    st.markdown("### Case register")
    if cases:
        st.dataframe(pd.DataFrame([dict(c) for c in cases]),use_container_width=True,hide_index=True)
        selected=st.selectbox("View case details",case_ids)
        c=next(c for c in cases if c["case_id"]==selected)
        st.write(f"**Title:** {c['title']}  \n**Examiner:** {c['examiner'] or 'Not specified'}  \n**Created:** {c['created_at']}  \n**Notes:** {c['notes'] or '—'}")
    else: st.caption("No cases registered.")

elif page=="Evidence Intake":
    st.subheader("Evidence intake")
    cid=case_select()
    if cid:
        with st.form("evidence_form"):
            up=st.file_uploader("Choose evidence file",type=None,help="Use a public, synthetic, or otherwise authorized sample. Original bytes are copied into this app's local data/evidence folder.")
            desc=st.text_area("Description / source")
            ok=st.form_submit_button("Register evidence & calculate hash",use_container_width=True)
        if ok:
            if up is None: st.error("Choose a file first.")
            else:
                try:
                    eid,digest=register_uploaded(up,cid,desc)
                    st.success(f"Registered {eid}")
                    st.code(digest,language="text")
                    st.caption("This hash identifies the bytes ingested by this prototype; it does not prove who created the file or whether it was authentic before intake.")
                    st.rerun()
                except Exception as ex: st.error(f"Could not register file: {ex}")
    st.markdown("### Registered evidence")
    rows=get_evidence(cid) if cid else []
    if rows:
        st.dataframe(pd.DataFrame([dict(r) for r in rows])[["evidence_id","original_name","mime_type","size_bytes","sha256","registered_at","description"]],use_container_width=True,hide_index=True)

elif page=="Integrity Verification":
    st.subheader("Integrity verification")
    cid=case_select()
    if cid:
        eid=evidence_select(cid)
        if eid:
            row=row_for_evidence(eid)
            st.write(f"**File:** {row['original_name']}  ·  **Registered:** {row['registered_at']}")
            st.code(row["sha256"],language="text")
            c1,c2=st.columns(2)
            with c1:
                if st.button("Recalculate stored-file hash",use_container_width=True):
                    try:
                        actual=sha256_bytes(file_bytes(row))
                        match=actual==row["sha256"]
                        audit("HASH_RECHECK",cid,eid,f"Stored-file hash {'MATCH' if match else 'MISMATCH'}; calculated={actual}")
                        if match: st.success("MATCH — stored bytes match the registered SHA-256.")
                        else: st.error("MISMATCH — stored bytes differ from the registered SHA-256.")
                        st.write("Calculated SHA-256"); st.code(actual)
                    except Exception as ex: st.error(str(ex))
            with c2:
                ref=st.text_input("Optional reference SHA-256",placeholder="Paste a 64-character hash")
                if st.button("Compare reference hash",use_container_width=True):
                    if len(ref.strip())!=64 or any(ch not in "0123456789abcdefABCDEF" for ch in ref.strip()):
                        st.error("Enter a valid 64-character hexadecimal SHA-256 value.")
                    else:
                        match=ref.strip().lower()==row["sha256"].lower()
                        audit("REFERENCE_HASH_COMPARE",cid,eid,f"Reference comparison {'MATCH' if match else 'MISMATCH'}")
                        st.success("MATCH: reference hash equals registered hash.") if match else st.error("MISMATCH: reference hash differs.")
            st.warning("A matching hash demonstrates byte-level equality against the selected reference only. It does not establish authenticity, source, or truthfulness of content.")

elif page=="Audio Lab":
    st.subheader("Audio examination")
    cid=case_select()
    if cid:
        rows=get_evidence(cid)
        aud=[r for r in rows if (r["mime_type"] or "").startswith("audio/") or Path(r["original_name"]).suffix.lower() in [".wav",".mp3",".m4a",".aac",".flac",".ogg",".wma"]]
        if not aud: st.info("Register an audio file in Evidence Intake first.")
        else:
            eid=st.selectbox("Audio evidence", [r["evidence_id"] for r in aud],format_func=lambda x: f"{x} — {next(r['original_name'] for r in aud if r['evidence_id']==x)}")
            row=row_for_evidence(eid); path=Path(row["stored_path"])
            st.write(f"**SHA-256:** `{row['sha256']}`")
            st.audio(path.read_bytes())
            result,err=probe_media(path)
            if result:
                fmt=result.get("format",{}); streams=result.get("streams",[])
                st.markdown("### File metadata")
                a,b,c=st.columns(3)
                a.metric("Duration",f"{float(fmt.get('duration',0)):.2f} sec" if fmt.get("duration") else "N/A")
                a.metric("File size",f"{int(fmt.get('size',row['size_bytes']))/1024:.1f} KB")
                audio_stream=next((s for s in streams if s.get("codec_type")=="audio"),{})
                b.metric("Codec",audio_stream.get("codec_name","N/A"))
                b.metric("Sample rate",f"{audio_stream.get('sample_rate','N/A')} Hz")
                c.metric("Channels",audio_stream.get("channels","N/A"))
                st.json({"format":fmt,"audio_streams":[s for s in streams if s.get("codec_type")=="audio"]})
            else:
                st.info(err)
                st.write({"File name":row["original_name"],"Size (bytes)":row["size_bytes"],"MIME type":row["mime_type"]})
            try:
                import numpy as np
                import soundfile as sf
                audio_data,sr=sf.read(str(path),always_2d=True)
                st.markdown("### Waveform preview")
                max_points=5000
                mono=audio_data.mean(axis=1)
                stride=max(1,len(mono)//max_points)
                st.line_chart(pd.DataFrame({"Amplitude":mono[::stride]}),height=220)
                st.caption(f"Waveform plotted from decoded samples; sample rate {sr} Hz. This visualization is descriptive, not an authenticity verdict.")
            except Exception:
                st.caption("Waveform preview requires a supported audio decoder (soundfile). WAV/FLAC files are best for the offline demo.")
            audit("AUDIO_EXAMINATION_VIEWED",cid,eid,"Audio metadata / playback view opened.")

elif page=="Video Lab":
    st.subheader("Video examination")
    cid=case_select()
    if cid:
        rows=get_evidence(cid)
        vids=[r for r in rows if (r["mime_type"] or "").startswith("video/") or Path(r["original_name"]).suffix.lower() in [".mp4",".mov",".avi",".mkv",".webm",".m4v"]]
        if not vids: st.info("Register a video file in Evidence Intake first.")
        else:
            eid=st.selectbox("Video evidence",[r["evidence_id"] for r in vids],format_func=lambda x: f"{x} — {next(r['original_name'] for r in vids if r['evidence_id']==x)}")
            row=row_for_evidence(eid); path=Path(row["stored_path"])
            st.write(f"**SHA-256:** `{row['sha256']}`")
            st.video(path.read_bytes())
            result,err=probe_media(path)
            if result:
                fmt=result.get("format",{}); streams=result.get("streams",[])
                vs=next((s for s in streams if s.get("codec_type")=="video"),{})
                a,b,c=st.columns(3)
                a.metric("Duration",f"{float(fmt.get('duration',0)):.2f} sec" if fmt.get("duration") else "N/A")
                b.metric("Resolution",f"{vs.get('width','?')} × {vs.get('height','?')}")
                c.metric("Frame rate",vs.get("r_frame_rate","N/A"))
                st.json({"format":fmt,"video_streams":[s for s in streams if s.get("codec_type")=="video"]})
            else: st.info(err)
            st.caption("Metadata can be missing or altered. Frame rate fields such as 30000/1001 are rational values and should not be mistaken for a verified recording time.")
            if st.button("Extract preview frame (requires FFmpeg)",use_container_width=True):
                ffmpeg=shutil.which("ffmpeg")
                if not ffmpeg: st.error("FFmpeg is not installed. Install it and ensure ffmpeg is on PATH.")
                else:
                    target=REPORT_DIR/f"{eid}_preview.jpg"
                    try:
                        subprocess.run([ffmpeg,"-y","-ss","1","-i",str(path),"-frames:v","1",str(target)],capture_output=True,timeout=30,check=True)
                        st.image(str(target),caption="Preview frame at approximately 1 second; not a complete forensic frame examination.")
                        audit("VIDEO_FRAME_EXTRACTED",cid,eid,"Preview frame extracted near 1 second.")
                    except Exception as ex: st.error(f"Frame extraction failed: {ex}")

elif page=="Chain of Custody":
    st.subheader("Chain-of-custody activity log")
    st.caption("This is an application activity log for academic demonstration, not a tamper-proof or legally certified chain-of-custody record.")
    cid=case_select()
    if cid:
        c=next(c for c in cases if c["case_id"]==cid)
        rows=get_evidence(cid)
        logs=get_audit(cid)
        st.markdown(f"### {c['case_id']} — {c['title']}")
        st.write(f"Evidence items: **{len(rows)}** · Logged actions: **{len(logs)}**")
        if rows:
            for r in rows:
                with st.expander(f"{r['evidence_id']} · {r['original_name']}", expanded=False):
                    st.write(f"**Registered:** {r['registered_at']}")
                    st.write(f"**Size:** {r['size_bytes']} bytes")
                    st.code(r['sha256'])
                    st.write(f"**Description:** {r['description'] or 'Not provided'}")
                    try:
                        data=file_bytes(r)
                        st.download_button("Download stored evidence copy", data=data, file_name=r['original_name'], mime=r['mime_type'] or "application/octet-stream", key=f"download_{r['evidence_id']}")
                    except Exception as ex:
                        st.error(f"Stored copy unavailable: {ex}")
        st.markdown("### Activity timeline")
        if logs:
            df=pd.DataFrame([dict(a) for a in logs])
            st.dataframe(df[["event_time","action","evidence_id","details"]], use_container_width=True, hide_index=True)
            st.download_button("Export activity log (CSV)", df.to_csv(index=False).encode("utf-8"), file_name=f"{cid}_activity_log.csv", mime="text/csv")
        else:
            st.info("No actions logged for this case yet.")

elif page=="Reports & Audit":
    st.subheader("Reports & audit trail")
    cid=case_select()
    if cid:
        c=next(c for c in cases if c["case_id"]==cid)
        rows=get_evidence(cid); logs=get_audit(cid)
        report={"report_type":"Academic Digital Multimedia Forensics Examination Summary","generated_at":now(),"case":dict(c),
                "evidence":[dict(r) for r in rows],"audit_events":[dict(a) for a in logs],
                "limitations":["This is an academic prototype, not a certified forensic tool.","Hash equality confirms byte-level equality only against a reference.","Metadata may be incomplete or altered; no automated authenticity conclusion is made."]}
        st.markdown("### Report preview")
        st.write(f"**Case:** {c['case_id']} — {c['title']}")
        st.write(f"**Evidence items:** {len(rows)} · **Audit events:** {len(logs)}")
        if rows:
            st.dataframe(pd.DataFrame([dict(r) for r in rows])[["evidence_id","original_name","size_bytes","sha256","registered_at"]],use_container_width=True,hide_index=True)
        st.download_button("⬇ Download JSON examination report",json.dumps(report,indent=2,ensure_ascii=False).encode(),file_name=f"{cid}_examination_report.json",mime="application/json",use_container_width=True)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=16*mm,bottomMargin=16*mm)
            styles=getSampleStyleSheet(); story=[Paragraph("EvidenceLab Pro — Academic Prototype",styles["Title"]),Paragraph("Digital Multimedia Examination Summary",styles["Heading2"]),Spacer(1,8)]
            story += [Paragraph(f"<b>Case ID:</b> {xml_escape(str(c['case_id']))}",styles["BodyText"]),Paragraph(f"<b>Case title:</b> {xml_escape(str(c['title']))}",styles["BodyText"]),Paragraph(f"<b>Examiner:</b> {xml_escape(str(c['examiner'] or 'Not specified'))}",styles["BodyText"]),Paragraph(f"<b>Generated:</b> {report['generated_at']}",styles["BodyText"]),Spacer(1,10)]
            data=[["Evidence ID","Filename","Size (bytes)","SHA-256"]]
            for r in rows: data.append([r["evidence_id"],r["original_name"][:30],str(r["size_bytes"]),r["sha256"][:20]+"…"])
            t=Table(data,repeatRows=1,colWidths=[27*mm,48*mm,25*mm,55*mm])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#15304b")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#eef3f8")])]))
            story += [Paragraph("Registered evidence",styles["Heading2"]),t,Spacer(1,12),Paragraph("Interpretation & limitations",styles["Heading2"])]
            for item in report["limitations"]: story.append(Paragraph("• "+item,styles["BodyText"]))
            story += [Spacer(1,12),Paragraph("Audit trail",styles["Heading2"])]
            for a in logs[:30]: story.append(Paragraph(xml_escape(f"{a['event_time']} — {a['action']} — {a['details'] or ''}"),styles["BodyText"]))
            doc.build(story)
            st.download_button("⬇ Download PDF examination report",buf.getvalue(),file_name=f"{cid}_examination_report.pdf",mime="application/pdf",use_container_width=True)
        except Exception as ex: st.warning(f"PDF export unavailable: {ex}. JSON export is available.")
        st.markdown("### Audit trail")
        if logs: st.dataframe(pd.DataFrame([dict(a) for a in logs]),use_container_width=True,hide_index=True)
        else: st.caption("No audit events for this case yet.")

elif page=="About / Viva":
    st.subheader("Project documentation & viva guide")
    st.markdown("""
### Problem statement
Digital audio/video evidence needs organized intake, integrity checking, metadata inspection and traceable examination records. Manual workflows can make it difficult to present a consistent, repeatable demonstration.

### Proposed solution
FSL EvidenceLab Pro is a local academic prototype that combines case registration, file intake, SHA-256 hashing, available media metadata inspection, descriptive waveform/frame previews, an SQLite audit trail and downloadable examination summaries.

### Architecture
**Streamlit UI → Python processing layer → SQLite case/evidence/audit database → local evidence store → PDF/JSON report output.**

### Viva-ready explanation
- **Why SHA-256?** It creates a fixed-length digest used to compare file bytes. If the bytes change, the digest will normally change.
- **Does a matching hash prove authenticity?** No. It proves equality to the compared reference, not the identity of the creator or whether the original content was genuine.
- **What is chain of custody?** A documented record of evidence handling and related actions. This prototype logs selected app actions, but is not tamper-proof or a certified chain-of-custody system.
- **Why SQLite?** It is lightweight and suitable for an offline single-machine prototype.
- **Why FFprobe?** It reads container and stream properties when FFmpeg tools are installed.
- **Can the app detect deepfakes?** No. It does not claim to determine manipulation or authenticity automatically.
- **What are the limitations?** It is an academic prototype; it does not replace write blockers, validated forensic acquisition, secure signing, access control or laboratory SOPs.

### Demonstration safety
Use only self-created, synthetic, public-domain or explicitly authorized sample media. Do not upload confidential case evidence or personal files without permission.
""")
    st.info("Be precise in the viva: describe features that you can demonstrate live, and distinguish implemented functions from optional FFmpeg-dependent features.")

st.markdown("---")
st.caption("Digital Evidence Examination Workbench • Student-built academic prototype • Not official FSL software")
