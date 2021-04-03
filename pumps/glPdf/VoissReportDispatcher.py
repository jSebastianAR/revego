
# coding=utf-8
from glPdf.glReportAsPDF import GLReportAsPDF
from  reportlab.platypus.paragraph import Paragraph
from  reportlab.platypus import PageBreak
import datetime
import logging
import calendar
import time
from django.db import connection

from pumpsModule.models import GLStation
from pumpsModule.models import GLCustomer
from pumpsModule.models import GLUser
from pumpsModule.models import GLShift
from pumpsModule.models import GLPartialDelivery
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


logger = logging.getLogger(__name__)

class VoissReportDispatcher(GLReportAsPDF):

   def __init__(self, filename, **kw):#{{{#
      GLReportAsPDF.__init__(self,filename)
   #}}}#


   def generateReport(self,request):#{{{#

      def addPageNumber(canvas, doc):
          """
          Add the page number
          """
          page_num = canvas.getPageNumber()
          text = "Page #%s" % page_num
          canvas.drawRightString(200*mm, 20*mm, text)

      try:
         userId = GLUser.objects.get(vUserId= request.GET['userId'])
         currentShift = GLShift.objects.get(vShift=request.GET['shift'])
         currentStation = GLStation.objects.get(vStationDesc= request.GET['currentStation'])
         if request.GET.get('shift') is None:
            logger.error('shift not found in request, please check the client selection')
            return 

         if "null" in request.GET.get('userId'):
            logger.error('userId not found in request, please check the client selection')
            return 

         self.header=[]

         self.header.append(Paragraph('<b>'+ self.rightSpaces('Reporte Entregas Islas',127)+' ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S %p')) + '</b>' , self.h2))
         self.header.append(Paragraph('<b>'+self.rightSpaces('Estacion    : ',16) +'' + str(currentStation.vStationDesc) +'</b>' , self.h2))
         self.header.append(Paragraph('<b>'+self.rightSpaces('Turno       : ',16) +'' + request.GET.get('shift') +'</b>' , self.h2))
         self.header.append(Paragraph('<b>'+self.rightSpaces('Despachador : ',16) +  userId.vName + ' '  + userId.vLastname + '</b>' , self.h2))
         self.header.append(Paragraph(' ', self.newline))

         self.header.append(Paragraph(' ', self.newline))
         self.header.append(Paragraph(' ', self.newline))
         self.header.append(Paragraph('----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------', self.lineblack))

         self.ticketContent.append(Paragraph('----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------', self.lineblack))

         
         allDeliveries = GLPartialDelivery.objects.filter(vShiftId=currentShift, vUserId=userId).order_by("vPartialDeliveryId")

         elements = []
         data = []
         currentIndex=0
         data.append([])
         data[currentIndex].append(self.rightSpacesTable('Isla',4))
         data[currentIndex].append(self.rightSpacesTable('Fecha',22))
         data[currentIndex].append(self.rightSpacesTable('Total Efectivo',14))
         data[currentIndex].append(self.rightSpacesTable('Total Crédito',14))
         data[currentIndex].append(self.rightSpacesTable('Total Débito',14))
         data[currentIndex].append(self.rightSpacesTable('Total Otros',14))
         data[currentIndex].append(self.rightSpacesTable('Descripción Otros',40))
         data[currentIndex].append(self.rightSpacesTable('Total Final',10))

         totalCash=0
         totalCredit=0
         totalDebit=0
         totalOthers=0
         totalFinal=0

         for currentDelivery in allDeliveries:
            currentIndex+=1
            data.append([])
            data[currentIndex].append(self.rightSpacesTable(str(currentDelivery.vIsland),4))
            data[currentIndex].append(self.rightSpacesTable(str(currentDelivery.vDate.strftime('%Y/%m/%d %H:%M:%S')),22))
            if currentDelivery.vCashAmount:
               totalCash += float(currentDelivery.vCashAmount)
               data[currentIndex].append(self.rightSpacesTable("$"+str(currentDelivery.vCashAmount),14))
            else:
               data[currentIndex].append(self.rightSpacesTable("$"+str("0"),14))
            if currentDelivery.vVoucherAmountC:
               totalCredit += float(currentDelivery.vVoucherAmountC)
               data[currentIndex].append(self.rightSpacesTable("$"+str(currentDelivery.vVoucherAmountC),14))
            else:
               data[currentIndex].append(self.rightSpacesTable("$"+str("0"),14))
            if currentDelivery.vVoucherAmountD:
               totalDebit += float(currentDelivery.vVoucherAmountD)
               data[currentIndex].append(self.rightSpacesTable("$"+str(currentDelivery.vVoucherAmountD),14))
            else:
               data[currentIndex].append(self.rightSpacesTable("$"+str("0"),14))
            if currentDelivery.vOthersAmount:
               totalOthers += float(currentDelivery.vOthersAmount)
               data[currentIndex].append(self.rightSpacesTable("$"+str(currentDelivery.vOthersAmount),14))
            else:
               data[currentIndex].append(self.rightSpacesTable("$"+str("0"),14))

            data[currentIndex].append(self.rightSpacesTable(str(currentDelivery.vOthersDesc[:40]),40))
            
            totalFinal=0
            if currentDelivery.vCashAmount:
               totalFinal+= float(currentDelivery.vCashAmount)

            if currentDelivery.vVoucherAmountC:
               totalFinal+= float(currentDelivery.vVoucherAmountC)

            if currentDelivery.vVoucherAmountD:
               totalFinal+= float(currentDelivery.vVoucherAmountD)

            if currentDelivery.vOthersAmount:
               totalFinal+= float(currentDelivery.vOthersAmount)

            data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalFinal)),10))


         currentIndex+=1
         data.append([])
         data[currentIndex].append(self.rightSpacesTable(str(""),4))


         currentIndex+=1
         data.append([])
         data[currentIndex].append(self.rightSpacesTable(str(""),4))
         data[currentIndex].append(self.rightSpacesTable(str("Totales"),22))

         data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalCash)),14))
         data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalCredit)),14))
         data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalDebit)),14))
         data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalOthers)),14))
         data[currentIndex].append(self.rightSpacesTable(str(""),40))

         totalFinal= float(totalCash) + float(totalCredit) + float(totalDebit) + float(totalOthers)
         data[currentIndex].append(self.rightSpacesTable(str("$"+str(totalFinal)),10))



         t=Table(data)

         t.setStyle(TableStyle([ ('TEXTCOLOR',(0,0),(7,0),colors.blue),
                                 ('FONTSIZE',(0,0),(7,currentIndex),7),
                                 ('FONTNAME',(0,0),(7,0),'Times-Bold'),
                                 ('FONTSIZE',(0,0),(7,0),9)
                                 ])) 


         elements.append(t)
         self.build(self.header + elements )

      except GLStation.DoesNotExist:
         logger.error('Error while trying to get the station : ' + str(request.GET['currentStation']))
      except GLCustomer.DoesNotExist:
         logger.error('Error while trying to get the customerId : ' + str(request.GET['customerId']))


   #}}}#
