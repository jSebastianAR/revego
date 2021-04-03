from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm

from  reportlab.platypus import SimpleDocTemplate, Image


class GLQR(BaseDocTemplate):

   def __init__(self, filename, **kw):
      self.image=""
      self.images=[]
      self.header=[]
      self.ticketContent= []
      self.series= []
      self.amounts= []
      self.folios= []
      self.dates= []
      self.products= []

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


   def setImage(self, image):
      self.image= image

   def afterFlowable(self, flowable):
      "Registers TOC entries."
      if flowable.__class__.__name__ == 'Paragraph':
          text = flowable.getPlainText()
          style = flowable.style.name
          if style == 'Heading1':
              self.notify('TOCEntry', (0, text, self.page))
          if style == 'Heading2':
              self.notify('TOCEntry', (1, text, self.page))

   def setHeader(self, header):
      self.header= header

   def addImage(self, image):
      self.images.append(image)

   def addDate(self, date):
      self.dates.append(date)

   def addSerie(self, serie):
      self.series.append(serie)

   def addFolio(self, folio):
      self.folios.append(folio)

   def addAmount(self, amount):
      self.amounts.append(amount)

   def addProduct(self, product):
      self.products.append(product)

   def generateTicket(self):


      currentIndex=0      
      for currentImage in self.images:
         self.ticketContent.append(Image(self.image))
         for currentHeader in self.header:
            self.ticketContent.append(Paragraph('<b>'+ currentHeader +'</b>', self.centered))

         self.ticketContent.append(Image(currentImage))

         self.ticketContent.append(Paragraph('<b>Serie    :  '+ self.series[currentIndex]   +' </b>', self.centered))
         self.ticketContent.append(Paragraph('<b>Folio    :  '+ self.folios[currentIndex]   +' </b>', self.centered))
         self.ticketContent.append(Paragraph('<b>Cantidad : $'+ str(self.amounts[currentIndex])  +' </b>', self.centered))
         self.ticketContent.append(Paragraph('<b>Producto :  '+ self.products[currentIndex] +' </b>', self.centered))
         self.ticketContent.append(Paragraph('<b>Fecha Impresion :  '+ str(self.dates[currentIndex])   +' </b>', self.centered))

         self.ticketContent.append(PageBreak()) 
         currentIndex= currentIndex+1

      self.multiBuild(self.ticketContent)




