import shutil, os, datetime, zipfile

BASE_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(BASE_DIR, '..'))
DOCS_DIR = os.path.join(REPO_ROOT, 'docs')
OUTPUTS_DIR = os.path.join(REPO_ROOT, 'outputs')

now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
src = os.path.join(DOCS_DIR, 'pneumatic_launcher_analysis_complete.docx')
if not os.path.exists(src):
    raise SystemExit('Source complete doc not found: ' + src)

dst_name = f'pneumatic_launcher_analysis_dump_{now}.docx'
dst = os.path.join(REPO_ROOT, dst_name)
shutil.copy2(src, dst)

# Gather files to include from outputs and docs
include_ext = ('.docx', '.png', '.csv', '.json')
files = []
for d in (OUTPUTS_DIR, DOCS_DIR):
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.lower().endswith(include_ext):
                files.append(os.path.join(d, f))

zipname = os.path.join(REPO_ROOT, f'pneumatic_launcher_analysis_dump_{now}.zip')
with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, arcname=os.path.relpath(f, REPO_ROOT))

print(dst)
print(zipname)
