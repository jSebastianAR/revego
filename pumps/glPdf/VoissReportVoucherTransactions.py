from glReportAsPDF import GLReportAsPDF
from  reportlab.platypus.paragraph import Paragraph
import datetime
import logging
from django.db import connection

from vouchersModule.models import GLStation
from vouchersModule.models import GLCustomer
from vouchersModule.models import GLBilling
from vouchersModule.models import GLSerie
from vouchersModule.models import GLVoucher
from vouchersModule.models import GLVoucherTransaction
from vouchersModule.VoissBurnVouchers import  GLBurnVouchers

logger = logging.getLogger(__name__)

class VoissReportVoucherTransactions(GLReportAsPDF):

   def __init__(self, filename, **kw):#{{{#
      GLReportAsPDF.__init__(self,filename)
   #}}}#

   def getAmountFromTrx(self,currentTransaction):#{{{#
      try:
         vouchers= currentTransaction[1].split(',')
         currentStation= GLStation.objects.get(vStationDesc=currentTransaction[4])
         burnVoucherObj = GLBurnVouchers(vouchers,0)
         if burnVoucherObj.areAllMultiuse(currentStation):
            return currentTransaction[3]
         else:
            vouchersTotal=0
            for voucherAndSerie in vouchers:
               if len(voucherAndSerie.strip())>0:
                  voucher= voucherAndSerie.split("@")[0]
                  serie= voucherAndSerie.split("@")[1]
                  serieObj = GLSerie.objects.get(vSerie=serie, vStationId=currentStation) 
                  if '-' in voucher:
                     currentVoucher= GLVoucher.objects.get(vFolio=voucher,vStationId=currentStation,vSerie=serieObj)
                  else:
                     currentVoucher= GLVoucher.objects.get(vFolio=voucher.lstrip('0'),vStationId=currentStation,vSerie=serieObj)
                  vouchersTotal+= float(currentVoucher.vAmount.vAmount)
            return vouchersTotal
      except GLStation.DoesNotExist:
         return 0

      #}}}#

   def generateReport(self,request):#{{{#

      try:
         currentStation = GLStation.objects.get(vStationDesc= request.GET['currentStation'])
         if request.GET.get('customerId') is None:
            logger.error('customerId not found in request, please check the client selection')
            return 

         if "null" in request.GET.get('customerId'):
            logger.error('customerId not found in request, please check the client selection')
            return 

         if request.GET.get('dateIni') is None:
            logger.error('dateIni not found in request, please check the client selection')
            return 

         if request.GET.get('dateEnd') is None:
            logger.error('dateEnd not found in request, please check the client selection')
            return 



         currentCustomer = GLCustomer.objects.get(vCustomerId= request.GET['customerId'])

         self.ticketContent.append(Paragraph(self.rightSpaces('Reporte Cliente Transacciones',77)+' ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S %p')) + '', self.h2))
         self.ticketContent.append(Paragraph(self.rightSpaces(' ',16) +'' + str(currentStation.vStationDesc) , self.h2))
         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(' ', self.newline))

         self.ticketContent.append(Paragraph(self.rightSpaces('Id Cliente',40) +  
                                             self.rightSpaces(str(currentCustomer.vCustomerId),5) + 
                                             self.rightSpaces('Razon Social',20) +  
                                             self.rightSpaces(currentCustomer.vName,30), self.normalRecord))

         self.ticketContent.append(Paragraph(self.rightSpaces('Fecha Inicio:',30) + 
                                             self.rightSpaces(request.GET['dateIni'],44) +  
                                             self.rightSpaces('Fecha Fin: ' + request.GET['dateEnd'] + '',30), self.normalRecord))

         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(self.addRightSpaces(self.rightSpaces('Fecha',30),6)+
                                             self.addRightSpaces(self.rightSpaces('F Contable  ',15),1)+
                                             self.addRightSpaces(self.rightSpaces('Cliente',20),13)+
                                             self.addRightSpaces(self.rightSpaces('Turno',15),3)+
                                             self.addRightSpaces(self.rightSpaces('Id Venta',15),1)+
                                             self.addRightSpaces(self.rightSpaces('Producto',10),3)+
                                             self.addRightSpaces(self.rightSpaces('Importe',10),1)+
                                             self.addRightSpaces(self.rightSpaces('Vales',15),1)
                                             ,self.normalRecord))
         self.ticketContent.append(Paragraph(' ', self.newline))



         customQuery=''
         customQuery+=' select "vDate", cust."vName","vShift","vSaleId", prod."vProduct","vVouchers","vAmount"'
         customQuery+=' from "vouchersModule_glvouchertransaction" vtra'
         customQuery+=' join "vouchersModule_glcustomer" cust'
         customQuery+=' on cust."vCustomerId"=vtra."vCustomerId"'
         customQuery+=' join "vouchersModule_glproducts" prod '
         customQuery+=' on prod."vProductId"=vtra."vProducts_id"  '
         customQuery+=' where "vDate">=\'' + request.GET['dateIni'] + '\''
         customQuery+=' and "vDate"<=\'' + request.GET['dateEnd'] + '\''
         customQuery+=' and  cust."vCustomerId"=' +  str(currentCustomer.vCustomerId)
         customQuery+=' ;'

         cursor = connection.cursor()
         cursor.execute(customQuery)

         currentMovement=0
         totalCustomer=0
         for currentRow in cursor.fetchall():

            finalParagraph=""

            finalParagraph+=self.addRightSpaces(str(currentRow[0].strftime('%d/%m/%Y %H:%M:%S')),8) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str(currentRow[0].strftime('%d/%m/%Y')),14),1) 
            
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[1][:20]) if len(str(currentRow[1])) > 20 else currentRow[1]),20),3) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[2][:10]) if len(str(currentRow[2])) > 10 else currentRow[2]),10),3) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[3][:15]) if len(str(currentRow[3])) > 15 else currentRow[3]),15),3) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[4][:10]) if len(str(currentRow[4])) > 10 else currentRow[4]),10),3) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[6][:10]) if len(str(currentRow[6])) > 10 else currentRow[6]),10),3) 
            finalParagraph+=self.addRightSpaces(self.rightSpaces(str((currentRow[5][:20]) if len(str(currentRow[5])) > 20 else currentRow[5]),20),3) 

            currentMovement+=1
            totalCustomer+=float(currentRow[6])

            self.ticketContent.append(Paragraph(finalParagraph, self.normalRecord))


         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(self.addRightSpaces(self.leftSpaces('Total Trx: ',110),6) + 
                                    str(currentMovement) + self.leftSpacesF('Total Cliente:  $',35)  + str(totalCustomer), self.normalRecord) )
         self.multiBuild(self.ticketContent)
      except GLStation.DoesNotExist:
         logger.error('Error while trying to get the station : ' + str(request.GET['currentStation']))
      except GLCustomer.DoesNotExist:
         logger.error('Error while trying to get the customerId : ' + str(request.GET['customerId']))
      except GLVoucherTransaction.DoesNotExist:
         logger.error('Error while trying to get the voucher transactions from customer :' + str(request.GET['customerId']))


   #}}}#
