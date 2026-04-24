from docx import Document
import os

DOC = os.path.normpath(os.path.join(os.path.dirname(
    __file__), '..', 'docs', 'pneumatic_launcher_analysis_complete.docx'))
doc = Document(DOC)
text = '\n'.join([p.text for p in doc.paragraphs])

checks = [
    ('Isothermal work', 'Isothermal work'),
    ('Transient', 'Transient 1D'),
    ('Parametric Sweep', 'Parametric Sweep'),
    ('Flange', 'Flange'),
    ('Engineering Drawing', 'Engineering Drawing'),
    ('launcher_drawing.svg', 'launcher_drawing.svg'),
    ('launcher_drawing.png', 'launcher_drawing.png'),
    ('Appendix: Generated Files', 'Appendix: Generated Files')
]

for label, key in checks:
    print(f"{label}:", 'FOUND' if key in text else 'MISSING')

# print first 40 chars of document start for basic verification
print('\nDocument start preview:')
print(text[:400])
