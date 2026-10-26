# EvidenceLab Pro — Digital Evidence Examination Workbench

**Academic prototype only. This is not official FSL software and is not a certified forensic tool.** Use synthetic, public-domain, or explicitly authorized sample files only.

## What's included

- Dashboard with live counts from the local database
- Case registration (SQLite)
- Evidence intake with local copy storage and SHA-256 hash
- Stored-file hash recheck and optional reference-hash comparison
- Synthetic demo generator: creates a test case and 3-second WAV tone
- Audio playback and waveform for supported formats
- Video playback and optional FFmpeg frame extraction
- Activity log / chain-of-custody-style view and CSV export
- PDF and JSON report export
- Local data folders; no cloud account required

## Run on Windows 10/11

1. Extract the ZIP to a writable folder.
2. Double-click `run_windows.bat`.
3. First launch installs packages and needs internet access. Keep the terminal open.
4. When Streamlit starts, open `http://localhost:8501` if the browser does not open automatically.
5. On the dashboard, click **Create demo data**. This creates a synthetic case and a generated WAV file, so the dashboard will show non-zero counts and other pages will have sample output.
6. Try **Integrity Verification** and click **Recalculate stored-file hash**; the expected result for the untouched sample is `MATCH`.
7. Try **Audio Lab**, **Chain of Custody**, and **Reports & Audit** to see playback/waveform, activity, and report downloads.

## If you already have Python in `D:\Python`

The included launcher checks an existing `.venv`, the Windows `py` launcher, the `python` command, and finally `D:\Python\python.exe`. If you prefer manual commands, open Command Prompt inside this folder and run:

```bat
D:\Python\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

If `.venv` already exists, do not create it again; use the last two commands.

## Project architecture

```text
Streamlit UI (frontend)
        |
Python processing layer
  |        |           |
SHA-256  Media tools  Report generation
  |        |           |
SQLite case/evidence/audit database + local evidence files
        |
PDF / JSON / CSV exports
```

## Technical limitations

- A SHA-256 match means the compared bytes match; it does not prove authenticity, authorship, or truthfulness.
- The audit log is not tamper-proof or a legally certified chain-of-custody record.
- FFmpeg/FFprobe are optional and are required for some advanced video/media metadata features.
- Waveform decoding depends on supported file formats and installed packages.
- This prototype does not detect deepfakes or automatically determine whether media has been manipulated.
- Do not use confidential case material or real evidence without explicit authorization.

## Viva walkthrough

1. Create demo data.
2. Show the case and evidence totals on the dashboard.
3. Recalculate the stored file hash and show `MATCH`.
4. Open Audio Lab and play the generated synthetic tone / show waveform.
5. Open Chain of Custody and explain logged application actions.
6. Open Reports & Audit and download JSON/PDF; export activity CSV.
7. Explain the limitations honestly.
