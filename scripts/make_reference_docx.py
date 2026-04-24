from docx import Document
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Create a reference DOCX with preferred table style
doc = Document()
doc.add_paragraph('Reference document for pandoc to apply table styles')
# create a sample table to ensure styles are embedded
table = doc.add_table(rows=2, cols=2)
for i, row in enumerate(table.rows):
    for j, cell in enumerate(row.cells):
        cell.text = f'Sample {i},{j}'
# Use a common style and apply header shading + bold header text
try:
    table.style = 'Table Grid'
except Exception:
    pass

# format header row (first row) with bold text and light gray shading
hdr = table.rows[0]
for cell in hdr.cells:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
    # apply shading via XML (w:shd)
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'D9D9D9')
    tcPr.append(shd)

doc.save('docs/reference.docx')
print('Wrote docs/reference.docx')
