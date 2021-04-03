from  reportlab.lib.styles import ParagraphStyle as PS
from  reportlab.platypus import PageBreak
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from  reportlab.platypus.tableofcontents import TableOfContents
from  reportlab.platypus.frames import Frame
from  reportlab.lib.units import cm

from  reportlab.platypus import SimpleDocTemplate, Image
#import glPdf.VoissNumberToLetter


class GLPDF(BaseDocTemplate):

   def __init__(self, filename, **kw):
      self.image=""
      self.barcode=""
      self.header=[]
      self.footer=[]
      self.vouchers=[]
      self.vouchersf=[]
      self.station=""
      self.date=""
      self.dispatcher=""
      self.driver=""
      self.pump=""
      self.amount=""
      self.price=""
      self.volume=""
      self.saleId=""
      self.customer=""
      self.customerId=""
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

   def setBarcode(self, barcode):
      self.barcode= barcode

   def setHeader(self, header):
      self.header= header

   def setFooter(self, footer):
      self.footer=footer

   def setVouchers(self, vouchers):
      self.vouchers=vouchers

   def setVouchersF(self, vouchersf):
      self.vouchersf=vouchersf

   def setStation(self, station):
      self.station= station

   def setDate(self, date):
      self.date= date

   def setDispatcher(self, dispatcher):
      self.dispatcher = dispatcher

   def setDriver(self, driver):
      self.driver = driver

   def setCustomer(self,customer):
      self.customer= customer

   def setCustomerId(self,customerId):
      self.customerId= customerId

   def setPump(self, pump):
      self.pump= pump

   def setAmount(self, amount):
      self.amount= amount

   def setPrice(self, price):
      self.price= price

   def setVolume(self, volume):
      self.volume= volume

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
      if self.dispatcher:
         self.ticketContent.append(Paragraph('Despachador : ' + self.dispatcher, self.h2))
      if self.driver:
         self.ticketContent.append(Paragraph('Conductor   : ' + self.driver, self.h2))
      self.ticketContent.append(Paragraph('Cliente     : (' + str(self.customerId) + ')' + self.customer, self.h2))
      self.ticketContent.append(Paragraph('Bomba       : ' + self.pump, self.h2))
      self.ticketContent.append(Paragraph('Precio x L  : $'+ self.price, self.h2))
      self.ticketContent.append(Paragraph('Volumen     : ' + self.volume, self.h2))
      self.ticketContent.append(Paragraph('Venta       : ' + self.saleId, self.h2))
      self.ticketContent.append(Paragraph('Producto    : ' + self.product, self.h2))
      self.ticketContent.append(Paragraph('Turno       : ' + self.shift, self.h2))
      self.ticketContent.append(Paragraph('Total       : $'+ self.amount, self.h2))
      self.ticketContent.append(Paragraph(' ', self.space))
      self.ticketContent.append(Paragraph(VoissNumberToLetter.to_word(float(self.amount)), self.h2))
      self.ticketContent.append(Paragraph(' ', self.space))

      self.ticketContent.append(Paragraph('------------------------------', self.centered))

      if self.vouchers:
         self.ticketContent.append(Paragraph('Vales Usados', self.centered))
         self.ticketContent.append(Paragraph(' ', self.space))
         
         vouchersSeparated= self.vouchers.split(',')
         for currentVoucher in vouchersSeparated:
            if currentVoucher:
               self.ticketContent.append(Paragraph('<b>Fol: '+ currentVoucher.split('@')[0] + ' , SE: ' + currentVoucher.split('@')[1]  + ' , SD: ' + currentVoucher.split('@')[2]  + '</b>', self.h2))

         self.ticketContent.append(Paragraph(' ', self.space))

      if self.vouchersf:
         self.ticketContent.append(Paragraph('Vales Libres', self.centered))
         self.ticketContent.append(Paragraph(' ', self.space))

         vouchersSeparated= self.vouchersf.split(',')
         for currentVoucher in vouchersSeparated:
            if currentVoucher:
               self.ticketContent.append(Paragraph('<b>Folio : '+ currentVoucher.split('@')[0] + ' , Serie : ' + currentVoucher.split('@')[1]  + ' , SD: ' + currentVoucher.split('@')[2]  + '</b>', self.h2))

         self.ticketContent.append(Paragraph(' ', self.space))

      self.ticketContent.append(Paragraph('------------------------------', self.centered))
      self.ticketContent.append(Paragraph(' ', self.space))

      self.ticketContent.append(Image(self.barcode))

      for currentFooter in self.footer:
         self.ticketContent.append(Paragraph('<b>'+ currentFooter +'</b>', self.centered))

      self.multiBuild(self.ticketContent)

