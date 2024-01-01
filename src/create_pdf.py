from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.image("/home/vishvaa/projects/Quiz-App/src/VEC-logo.png",10,6,25)
        self.set_font("helvetica",'B',15)
        self.cell(80)
        self.cell(30,10,"VELAMMAL ENGINEERING COLLEGE",border=False,align="C",new_x="LMARGIN",
            new_y="NEXT",)
        self.cell(80)
        self.cell(30,10,"Velammal Newgen Park, Ambattur - Red Hills Road",border=False,align="C",new_x="LMARGIN",
            new_y="NEXT",)

        self.cell(0,10,"COURSE WISE MARK LIST",border=False,align="C")
        self.write_html(f"""""")

        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica","I",8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


pdf = PDF()
pdf.add_page()
pdf.set_font("Times", size=12)



pdf.write_html(
    f"""
    <table style="border-top: 1px solid black; ">
        <thead>
            <tr>
                <th width="10%" style="border-bottom: 1px solid black;">S.NO</th>
                <th width="25%" style="border-bottom: 1px solid black;">Reg.NO</th>
                <th width="30%" style="border-bottom: 1px solid black;">Name</th>
                <th width="25%" style="border-bottom: 1px solid black;">Obtained Mark</th>
            </tr>
        </thead>
        <tbody>
            <tr width="25%">
                <td>1</td>
                <td>23VEC-734</td>
                <td>VISHVAA K</td>        
                <td>10/10</td>        
            </tr>
            <tr width="25%">
                <td>1</td>
                <td>23VEC-734</td>
                <td>VISHVAA K</td>        
                <td>10/10</td>        
            </tr>
        </tbody>
    </table>
    """,
    table_line_separators=True,
)

pdf.output("example.pdf")