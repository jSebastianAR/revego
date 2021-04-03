

import os
import glPdf
import qrcode
import logging
from glEmail.src.glemail import GLEmail
logger = logging.getLogger(__name__)

class GLSendQR():

   def __init__(self, rfc):
      self.mail=""
      self.businessName =""
      self.rfc=rfc

   def setBusinessName(self, businessName):
      self.businessName=businessName

   def setMail(self, mail):
      self.mail=mail

   def sendMail(self):

      logger.info('Sending QR to mail')

      qrFileName = "QR_" + unicode(self.businessName) 
      logger.info("Generating pdf file : " + unicode(qrFileName) + '.pdf' )

      currentTicket = glPdf.glQRCustomer.GLQRCustomer('glPdf/' + unicode(qrFileName) + '.pdf')

      qrcodes = qrcode.QRCode(
                  version=1,
                  error_correction=qrcode.constants.ERROR_CORRECT_L,
                  box_size=10,
                  border=4,
               )
      qrcodes.add_data(self.rfc) 
      qrcodes.make(fit=True)

      imagec = qrcodes.make_image()
      imagec.save('glQr/' + self.rfc + '.jpg')
      currentTicket.setImage( 'glQr/' + self.rfc + '.jpg')
      currentTicket.setBusinessName(self.businessName)

      currentTicket.generateTicket()

      if self.mail:
         email = GLEmail()
         response = email.send(
            "Codigo Qr para Facturar ",
            self.mail,
            "Estimado cliente, le enviamos su codigo QR con el cual podra facturar sus ventas en nuestras estaciones de servicio",
            os.path.dirname(os.path.abspath(__file__)) + "/../glPdf/" + qrFileName + ".pdf")
         logger.info( 'Mail has been sent to customer mail:'  + str(response))
         return response
      return False

