from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm
from  reportlab.platypus import SimpleDocTemplate, Image
from reportlab.platypus import NextPageTemplate
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch

class GLReportAsPDF(BaseDocTemplate):

   def addPageNumber(self,canvas, doc):
       """
       Add the page number
       """
       page_num = canvas.getPageNumber()
       text = "Page #%s" % page_num
       canvas.drawRightString(200*mm, 20*mm, text)

   def make_portrait(self,canvas,doc):
      canvas.setPageSize(letter)

   def make_landscape(self,canvas,doc):
      canvas.setPageSize(landscape(letter))

   def __init__(self, filename, **kw):#{{{#

      self.ticketContent= []

      self.allowSplitting = 0
      apply(BaseDocTemplate.__init__, (self, filename), kw)
      template = PageTemplate('normal', [Frame(0.5*cm, 1*cm, 20*cm, 28*cm, id='F1')] )
      self.addPageTemplates(template)
      
      self.styles = getSampleStyleSheet()
      self.styles.add(ParagraphStyle(name='normal', fontSize=6, leading = 7, alignment=TA_LEFT))

      frame1 = Frame(100, 0,
                self.width, self.height,
                leftPadding = 140, rightPadding = 0,
                topPadding = 120, bottomPadding = 0,
                id='frame1')

      ltemplate = PageTemplate(id='landscape',frames =[frame1], onPage=self.make_landscape)
      self.addPageTemplates(ltemplate)

      self.centered = PS(name = 'centered',
          fontSize = 12,
          leading = 16,
          alignment = 1,
          spaceAfter = 1)

      self.ccRecord = PS(name = 'ccRecord',
          fontSize = 6,
          leading = 15,
          alignment = 0,
          spaceAfter = 0)

      self.normalRecord = PS(name = 'normalRecord',
          fontSize = 8,
          leading = 15,
          alignment = 0,
          spaceShrinkage = 0.1,
          spaceAfter = 2)

      self.normalRecordBalance = PS(name = 'normalRecord',
          fontSize = 6,
          leading = 15,
          alignment = 0,
          spaceAfter = 2)

      self.newline = PS(name = 'newline',
          fontSize = 12,
          leading = 16,
          alignment = 0,
          spaceAfter = 8)

      self.h2 = PS(name = 'Heading2',
          fontSize = 10,
          alignment = 0,
          textcolor= 'blue',
          color= 'blue',
          fontcolor= 'blue',
          leading = 9,
          spaceAfter=4)

      self.black = PS(name = 'black',
          fontSize = 6,
          alignment = 0,
          leading = 14,
          spaceAfter=0)

      self.lineblack = PS(name = 'lineblack',
          fontSize = 6,
          alignment = 0,
          leading = 14,
          spaceAfter=8)
   #}}}#



   def afterFlowable(self, flowable):#{{{#
      "Registers TOC entries."
      if flowable.__class__.__name__ == 'Paragraph':
          text = flowable.getPlainText()
          style = flowable.style.name
          if style == 'Heading1':
              self.notify('TOCEntry', (0, text, self.page))
          if style == 'Heading2':
              self.notify('TOCEntry', (1, text, self.page))
   #}}}#

   def addRightSpaces(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(noSpaces + (noSpaces)):
         finalString+='&nbsp;'
      return finalString
   #}}}#


   def rightSpaces(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(int((noSpaces-len(finalString)))):
         finalString+='&nbsp;'
      return finalString
   #}}}#

   def rightSpacesVehi(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(int((noSpaces-len(finalString))*2.2 )):
         finalString+='&nbsp;'
      return finalString
   #}}}#

   def rightSpacesTable(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(int((noSpaces-len(finalString)) )):
         finalString+=' '
      return finalString
   #}}}#

   def rightSpacesBalance(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(int((noSpaces-len(finalString)) )):
         finalString+='<b>_</b>'
      return finalString
   #}}}#

   def rightSpacesF(self, fullString, noSpaces):#{{{#
      finalString= fullString
      for i in range(noSpaces-len(finalString)):
         finalString+='_'
      return finalString
   #}}}#

   def leftSpaces(self, fullString, noSpaces):#{{{#
      finalString=""
      for i in range(noSpaces-len(fullString)):
         finalString+='&nbsp;'
      finalString+= fullString
      return finalString
   #}}}#

   def leftSpacesVehi(self, fullString, noSpaces):#{{{#
      finalString=""
      for i in range(noSpaces):
         finalString+='&nbsp;'
      finalString+= fullString
      return finalString
   #}}}#

   def leftSpacesF(self, fullString, noSpaces):#{{{#
      finalString=""
      for i in range(noSpaces-len(fullString)):
         finalString+='&nbsp;'
      finalString+= fullString
      return finalString
   #}}}#
      
   def generateReport(self,reportId,request):#{{{#
      pass

   #}}}#

