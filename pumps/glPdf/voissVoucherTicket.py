from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm

from  reportlab.platypus import SimpleDocTemplate, Image


class VoissPDF(BaseDocTemplate):

   def __init__(self, filename, **kw):
      self.image=""
      self.header=[]
      self.footer=[]
      self.station=""
      self.date=""
      self.dispatcher=""
      self.driver=""
      self.pump=""
      self.amount=""
      self.saleId=""
      self.product=""
      self.shift=""
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

   def setHeader(self, header):
      self.header= header

   def setFooter(self, footer):
      self.footer=footer

   def setStation(self, station):
      self.station= station

   def setDate(self, date):
      self.date= date

   def setDispatcher(self, dispatcher):
      self.dispatcher = dispatcher

   def setDriver(self, driver):
      self.driver = driver

   def setPump(self, pump):
      self.pump= pump

   def setAmount(self, amount):
      self.amount= amount

   def setSale(self, saleId):
      self.saleId= saleId

   def setProduct(self, product):
      self.product= product

   def setShift(self, shift):
      self.shift= shift

   def setDocumentName(self, documentName):
      self.documentName= documentName

   def generateTicket(self):

      self.ticketContent.append(Image(self.image))
      
      for currentHeader in self.header:
         self.ticketContent.append(Paragraph('<b>'+ currentHeader +'</b>', self.centered))

      self.ticketContent.append(Paragraph(' ', self.space))
      self.ticketContent.append(Paragraph('Estacion    : ' + self.station, self.h2))
      self.ticketContent.append(Paragraph('Fecha       : ' + self.date, self.h2))
      self.ticketContent.append(Paragraph('Despachador : ' + self.dispatcher, self.h2))
      self.ticketContent.append(Paragraph('Conductor   : ' + self.driver, self.h2))
      self.ticketContent.append(Paragraph('Bomba       : ' + self.pump, self.h2))
      self.ticketContent.append(Paragraph('Monto       : $' +  self.amount, self.h2))
      self.ticketContent.append(Paragraph('Venta       : ' + self.saleId, self.h2))
      self.ticketContent.append(Paragraph('Producto    : ' + self.product, self.h2))
      self.ticketContent.append(Paragraph('Turno       : ' + self.shift, self.h2))
      self.ticketContent.append(Paragraph(' ', self.space))

      for currentFooter in self.footer:
         self.ticketContent.append(Paragraph('<b>'+ currentFooter +'</b>', self.centered))

      self.multiBuild(self.ticketContent)



#currentTicket = VoissPDF('ticket.pdf')
#currentTicket.setImage('logo.jpg')

#header=[]
#footer=[]

#header.append('Estacion de Servicio EST 3315')
#header.append('RFC: EST121212I92')
#header.append('Jalisco 9, Cuernavaca Morelos, Mexico 62384')

#footer.append('Gracias por su preferencia')
#footer.append('Visite www.sistemental.voiss.com.mx')

#currentTicket.setHeader(header)
#currentTicket.setFooter(footer)
#currentTicket.setStation('EST 3315')
#currentTicket.setDate('Sept. 17, 2015, 1:40 a.m.')
#currentTicket.setDispatcher('Gerardo Hernandez Ballesteros')
#currentTicket.setDriver('Luis Alberto Ramirez Albino')
#currentTicket.setPump('2')
#currentTicket.setAmount('101.12')
#currentTicket.setSale('000000012322')
#currentTicket.setProduct('DIESEL')
#currentTicket.setShift('2015010101')
#currentTicket.generateTicket()

