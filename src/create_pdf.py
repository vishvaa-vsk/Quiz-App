from fpdf import FPDF

pdf = FPDF(orientation='P',unit='mm',format='A4')

pdf.add_page()
pdf.set_font("helvetica",size=18)
pdf.cell(100,15,"Communicative English Lab Report",new_x="LMARGIN",new_y="NEXT",align='C')
pdf.output("example.pdf")