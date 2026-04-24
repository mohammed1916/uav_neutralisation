import shutil, os, datetime, zipfile

cwd = os.path.dirname(__file__)
os.chdir(cwd)
now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
src = 'pneumatic_launcher_analysis_complete.docx'
if not os.path.exists(src):
    raise SystemExit('Source complete doc not found: ' + src)
dst = f'pneumatic_launcher_analysis_dump_{now}.docx'
shutil.copy2(src, dst)

# Gather files to include
include_ext = ('.docx', '.png', '.csv', '.json')
files = [f for f in os.listdir(cwd) if f.lower().endswith(include_ext)]
zipname = f'pneumatic_launcher_analysis_dump_{now}.zip'
with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f)

print(dst)
print(zipname)
