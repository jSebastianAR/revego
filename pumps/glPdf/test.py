from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm

from  reportlab.platypus import SimpleDocTemplate, Image

class MyDocTemplate(BaseDocTemplate):
     def __init__(self, filename, **kw):
         self.allowSplitting = 0
         apply(BaseDocTemplate.__init__, (self, filename), kw)
         template = PageTemplate('normal', [Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')])
         self.addPageTemplates(template)

# Entries to the table of contents can be done either manually by
# calling the addEntry method on the TableOfContents object or automatically
# by sending a 'TOCEntry' notification in the afterFlowable method of
# the DocTemplate you are using. The data to be passed to notify is a list
# of three or four items countaining a level number, the entry text, the page
# number and an optional destination key which the entry should point to.
# This list will usually be created in a document template's method like
# afterFlowable(), making notification calls using the notify() method
# with appropriate data.

     def afterFlowable(self, flowable):
         "Registers TOC entries."
         if flowable.__class__.__name__ == 'Paragraph':
             text = flowable.getPlainText()
             style = flowable.style.name
             if style == 'Heading1':
                 self.notify('TOCEntry', (0, text, self.page))
             if style == 'Heading2':
                 self.notify('TOCEntry', (1, text, self.page))


centered = PS(name = 'centered',
    fontSize = 12,
    leading = 16,
    alignment = 1,
    spaceAfter = 1)

space = PS(name = 'space',
    fontSize = 17,
    leading = 16,
    alignment = 1,
    spaceAfter = 15)

h2 = PS(name = 'Heading2',
    fontSize = 12,
    alignment = 1,
    leading = 14)


# Build story.
story = []

# Create an instance of TableOfContents. Override the level styles (optional)
# and add the object to the story

toc = TableOfContents()
#toc.levelStyles = [
#    PS(fontName='Times-Bold', fontSize=20, name='TOCHeading1', leftIndent=20, firstLineIndent=-20, spaceBefore=10, leading=16),
#    PS(fontSize=18, name='TOCHeading2', leftIndent=40, firstLineIndent=-20, spaceBefore=5, leading=12),
#]
#story.append(toc)

#story.append(Paragraph('<b>Table of contents</b>', centered))

story.append(Image('logo.jpg'))

story.append(Paragraph('<b>Estacion de Servicio EST 3315</b>', centered))
story.append(Paragraph('<b>RFC: EST121212I92</b>', centered))
story.append(Paragraph('<b>Jalisco 9, Cuernavaca Morelos, Mexico 62384</b>', centered))

story.append(Paragraph(' ', space))
story.append(Paragraph('Estacion    : EST 3315', h2))
story.append(Paragraph('Fecha       : Sept. 17, 2015, 1:40 a.m.', h2))
story.append(Paragraph('Despachador : Gerardo Hernandez Ballesteros', h2))
story.append(Paragraph('Conductor   : Luis Alberto Ramirez Albino', h2))
story.append(Paragraph('Bomba       : 2', h2))
story.append(Paragraph('Monto       : $101.12', h2))
story.append(Paragraph('Venta       : 000000012322', h2))
story.append(Paragraph('Producto    : DIESEL', h2))
story.append(Paragraph('Turno       : 2015010101', h2))
story.append(Paragraph(' ', space))

story.append(Paragraph('<b>Gracias por su preferencia</b>', centered))
story.append(Paragraph('<b>Visite www.sistemental.voiss.com.mx</b>', centered))

doc = MyDocTemplate('voucherTicket.pdf')
doc.multiBuild(story)
