
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
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


logger = logging.getLogger(__name__)

class VoissReportIsland(GLReportAsPDF):

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
         self.header.append(Paragraph('<b>'+self.rightSpaces('Despachador : ',16) + 'TODOS</b>' , self.h2))
         self.header.append(Paragraph(' ', self.newline))

         self.header.append(Paragraph(' ', self.newline))
         self.header.append(Paragraph(' ', self.newline))
         self.header.append(Paragraph('----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------', self.lineblack))

         self.ticketContent.append(Paragraph('----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------', self.lineblack))

         customQuery=''
         customQuery+='select "vIsland" "island", '
         customQuery+='       SUM(cast(CASE WHEN "vCashAmount" = \'\' THEN \'0\' ELSE "vCashAmount" END as float)) "totalCash", '
         customQuery+='       SUM(cast(CASE WHEN "vVoucherAmountC" = \'\' THEN \'0\' ELSE "vVoucherAmountC" END as float)) "totalCredit", '
         customQuery+='       SUM(cast(CASE WHEN "vVoucherAmountD" = \'\' THEN \'0\' ELSE "vVoucherAmountD" END as float)) "totalDebit", '
         customQuery+='       SUM(cast(CASE WHEN "vOthersAmount" = \'\' THEN \'0\' ELSE "vOthersAmount" END as float)) "totalOthers", '
         customQuery+='       "use"."vName" || \' \' || "use"."vLastname" "dispatcher" '
         customQuery+='from "pumpsModule_glpartialdelivery" as pde '
         customQuery+='join "pumpsModule_glshift" as gls '
         customQuery+='   on "pde"."vShiftId"="gls"."vShiftId"  '
         customQuery+='join "pumpsModule_gluser" use '
         customQuery+='   on "use"."vUserId"="pde"."vUserId"  '
         customQuery+='where "gls"."vShift"=\'' + request.GET['shift'] + '\' '
         customQuery+='group by "vIsland", '
         customQuery+='         "use"."vName", '
         customQuery+='         "use"."vLastname" '
         customQuery+='order by "vIsland";'


         cursor = connection.cursor()
         cursor.execute(customQuery)


         elements = []
         data = []
         currentIndex=0
         data.append([])
         data[currentIndex].append(self.rightSpacesTable('Isla',10))
         data[currentIndex].append(self.rightSpacesTable('Despachador',20))
         data[currentIndex].append(self.rightSpacesTable('Total Efectivo',16))
         data[currentIndex].append(self.rightSpacesTable('Total Crédito',16))
         data[currentIndex].append(self.rightSpacesTable('Total Débito',16))
         data[currentIndex].append(self.rightSpacesTable('Total Otros',16))
         data[currentIndex].append(self.rightSpacesTable('Total Final',16))

         totalCash=0
         totalCredit=0
         totalDebit=0
         totalOthers=0
         totalFinal=0

         for currentRow in cursor.fetchall():
            currentIndex+=1
            data.append([])
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[0]),10))
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[5]),20))
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[1]),16))
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[2]),16))
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[3]),16))
            data[currentIndex].append(self.rightSpacesTable(str(currentRow[4]),16))
            totalFinal= float(currentRow[1]) + float(currentRow[2]) + float(currentRow[3]) + float(currentRow[4])
            data[currentIndex].append(self.rightSpacesTable(str(totalFinal),16))

            if currentRow[1]:
               totalCash+= float(currentRow[1])
            if currentRow[2]:
               totalCredit+= float(currentRow[2])
            if currentRow[3]:
               totalDebit+= float(currentRow[3])
            if currentRow[4]:
               totalOthers+= float(currentRow[4])

         currentIndex+=1
         data.append([])
         data[currentIndex].append(self.rightSpacesTable(str(""),10))

         currentIndex+=1
         data.append([])
         data[currentIndex].append(self.rightSpacesTable(str(""),10))
         data[currentIndex].append(self.rightSpacesTable(str("Totales"),20))
         data[currentIndex].append(self.rightSpacesTable(str(totalCash),16))
         data[currentIndex].append(self.rightSpacesTable(str(totalCredit),16))
         data[currentIndex].append(self.rightSpacesTable(str(totalDebit),16))
         data[currentIndex].append(self.rightSpacesTable(str(totalOthers),16))
         totalFinal = float(totalCash) + float(totalCredit) + float(totalDebit) +  float(totalOthers)
         data[currentIndex].append(self.rightSpacesTable(str(totalFinal),16))

         t=Table(data)

         t.setStyle(TableStyle([ ('TEXTCOLOR',(0,0),(6,0),colors.blue),
                                 ('FONTSIZE',(0,0),(6,currentIndex),8),
                                 ('FONTNAME',(0,0),(6,0),'Times-Bold'),
                                 ('FONTSIZE',(0,0),(6,0),9)
                                 ])) 


         elements.append(t)
         self.build(self.header + elements )

      except GLStation.DoesNotExist:
         logger.error('Error while trying to get the station : ' + str(request.GET['currentStation']))
      except GLCustomer.DoesNotExist:
         logger.error('Error while trying to get the customerId : ' + str(request.GET['customerId']))


   #}}}#

