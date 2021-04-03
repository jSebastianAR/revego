
from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm

from  reportlab.platypus import SimpleDocTemplate, Image
#import glPdf.VoissNumberToLetter


class GLQRCustomer(BaseDocTemplate):

   def __init__(self, filename, **kw):
      self.image=""
      self.barcode=""
      self.businessName=""
      self.documentName=""
      self.ticketContent= []

      self.allowSplitting = 0
      apply(BaseDocTemplate.__init__, (self, filename), kw)
      template = PageTemplate('normal', [Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')])
      self.addPageTemplates(template)

      self.centered = PS(name = 'centered',
          fontSize = 12,
          leading = 16,
          alignment = 1,
          spaceAfter = 1)

      self.space = PS(name = 'space',
          fontSize = 17,
          leading = 16,
          alignment = 1,
          spaceAfter = 15)

      self.h2 = PS(name = 'Heading2',
          fontSize = 12,
          alignment = 1,
          leading = 14)

   def afterFlowable(self, flowable):
      "Registers TOC entries."
      if flowable.__class__.__name__ == 'Paragraph':
          text = flowable.getPlainText()
          style = flowable.style.name
          if style == 'Heading1':
              self.notify('TOCEntry', (0, text, self.page))
          if style == 'Heading2':
              self.notify('TOCEntry', (1, text, self.page))


   def setImage(self, image):
      self.image= image

   def setBusinessName(self, businessName):
      self.businessName= businessName

   def setDocumentName(self, documentName):
      self.documentName= documentName

   def generateTicket(self):

      self.ticketContent.append(Image(self.image))
      
      self.ticketContent.append(Paragraph('Cliente : ' + self.businessName, self.h2))

      self.multiBuild(self.ticketContent)

