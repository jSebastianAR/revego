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

class VoissReportVoucherBalances(GLReportAsPDF):

   def __init__(self, filename, **kw):#{{{#
      GLReportAsPDF.__init__(self,filename)
   #}}}#

   def getAmountFromTrx(self,currentTransaction):#{{{#
      try:
         vouchers= currentTransaction[1].split(',')
         currentStation= GLStation.objects.get(vStationDesc=currentTransaction[4])
         burnVoucherObj = GLBurnVouchers(vouchers,0)
         if burnVoucherObj.areAllMultiuse(currentStation):
            return currentTransaction[5]
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

         if request.GET.get('dateIni') is None:
            logger.error('dateIni not found in request, please check the client selection')
            return 

         if request.GET.get('dateEnd') is None:
            logger.error('dateEnd not found in request, please check the client selection')
            return 

         currentCustomer = GLCustomer.objects.get(vCustomerId= request.GET['customerId'])

         self.ticketContent.append(Paragraph(self.rightSpaces('Reporte Cliente Estado de Cuenta',77)+' ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S %p')) + '', self.h2))
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

         self.ticketContent.append(Paragraph(self.rightSpaces('Saldo Actual:',30) + str(currentCustomer.vBalance), self.normalRecord))
         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(self.addRightSpaces(self.leftSpaces('Id ',10),4)+
                                             self.addRightSpaces(self.rightSpaces('Fecha Registro  ',30),1)+
                                             self.addRightSpaces(self.rightSpaces('F Contable  ',15),1)+
                                             self.addRightSpaces(self.rightSpaces('Tipo  ',20),1)+
                                             self.addRightSpaces(self.rightSpaces('Referencia  ',65),1)+
                                             self.addRightSpaces(self.rightSpaces('Cargos  ',20),1)+
                                             self.addRightSpaces(self.rightSpaces('Abonos  ',24),1)+
                                             'Saldo ', self.normalRecord))
         self.ticketContent.append(Paragraph(' ', self.newline))


         currentMovement=1
         totalCharges= 0
         totalPayments=0

         customQuery=''

         customQuery+= ' select 1 kind,"vVouchers" vouchers,"vDate","vAmount",glst."vStationDesc", "vAmountVouchers"'
         customQuery+= ' from "vouchersModule_glvouchertransaction" glvt'
         customQuery+= ' join'
         customQuery+= ' "vouchersModule_glstation" glst'
         customQuery+= ' on glvt."vStationId"=glst."vStationId"'
         customQuery+= ' where "vDate">=\'' + request.GET['dateIni'] + '\''
         customQuery+= ' and "vDate"<=\'' + request.GET['dateEnd'] + '\''
         customQuery+= ' and  "vCustomerId"=' +  str(currentCustomer.vCustomerId)
         customQuery+= ' union all'
         customQuery+= ' select 2 kind,\'\'  vouchers,"vDate","vAmount",\'\' vStationId, 0'
         customQuery+= ' from "vouchersModule_glbilling"'
         customQuery+= ' where "vDate">=\'' + request.GET['dateIni'] + '\''
         customQuery+= ' and "vDate"<=\'' + request.GET['dateEnd'] + '\''
         customQuery+= ' and "vCustomerDestiny_id"=' + str(currentCustomer.vCustomerId)
         customQuery+= ' order by "vDate";'

         #Get the balances on inverse order
         balances=[]
         kinds=[]
         dates=[]
         charges=[]
         payments=[]
         
         cursor = connection.cursor()
         cursor.execute(customQuery)

         currentAmount=0
         currentPayment=0
         totalCharges=0
         totalPayments=0

         for currentRow in cursor.fetchall():

            kinds.append(currentRow[0])
            dates.append(currentRow[2])

            if 1==currentRow[0]:
               currentAmount=self.getAmountFromTrx(currentRow)
               charges.append(currentAmount)
               totalCharges+=float(currentAmount)
            else:
               currentPayment=currentRow[3]
               payments.append(str(currentPayment))
               totalPayments+=float(currentPayment)


         index=0
         indexBalances=len(balances)-1
         indexPayments=0
         indexCharges=0

         firstBalance= totalPayments-totalCharges
         balances.append(firstBalance)

         indexCharges=0
         indexPayments=0
         kinds= kinds[::-1]

         for currentBalance in kinds:
            if 1==currentBalance:
               firstBalance+=float(charges[indexCharges])
               balances.append(firstBalance)
               indexCharges+=1
            else:
               firstBalance-=float(payments[indexPayments])
               balances.append(firstBalance)
               indexPayments+=1


         indexCharges=0
         indexPayments=0

         charges= charges[::-1]
         payments= payments[::-1]
         kinds= kinds[::-1]
         balances= balances[::-1]
         index=0
         indexB=1


         try:
            for currentKind in kinds:
               
               currentDate= dates.pop(index)
               finalParagraph=""
               finalParagraph+=self.addRightSpaces(self.leftSpaces(str(currentMovement),8),4) 
               finalParagraph+=self.addRightSpaces(str(currentDate.strftime('%d/%m/%Y %H:%M:%S')),8) 
               finalParagraph+=self.addRightSpaces(self.rightSpaces(str(currentDate.strftime('%d/%m/%Y')),14),1) 
               if 1==currentKind:
                  finalParagraph+=self.addRightSpaces(self.rightSpaces('Consumo',14),1) 
               else:
                  finalParagraph+=self.addRightSpaces(self.rightSpaces('Deposito',14),1)

               if 1==currentKind:
                  finalParagraph+=self.addRightSpaces(self.rightSpaces(' ',67),1) 
               else:
                  finalParagraph+=self.addRightSpaces(self.rightSpaces(' ',67),1) 
               
               if 1==currentKind:
                  finalParagraph+=self.addRightSpaces(self.leftSpacesF(str("%0.2f" % float(charges.pop(indexCharges))) ,12),0)  
               else:
                  finalParagraph+=self.addRightSpaces(self.leftSpacesF('0.00',12),0) 

               if 1==currentKind:
                  finalParagraph+=self.addRightSpaces(self.leftSpacesF('0.00 ',23),10) 
               else:
                  finalParagraph+=self.addRightSpaces(self.leftSpacesF(str("%0.2f" %float(payments.pop(indexPayments))),23),10) 

               finalParagraph+=self.addRightSpaces(self.leftSpacesF(str(balances.pop(indexB)),15),1)

               self.ticketContent.append(Paragraph(finalParagraph, self.normalRecord))
               currentMovement+=1
               indexBalances-=1
         except Exception,e: print str(e)


         self.ticketContent.append(Paragraph(' ', self.newline))
         self.ticketContent.append(Paragraph(self.addRightSpaces(self.leftSpaces('Totales :',160),10) + 
                                             self.rightSpaces(str("%0.2f" %totalCharges),19) + 
                                             str("%0.2f" %totalPayments), self.normalRecord))

         self.multiBuild(self.ticketContent)
      except GLStation.DoesNotExist:
         logger.error('Error while trying to get the station : ' + str(request.GET['currentStation']))
      except GLCustomer.DoesNotExist:
         logger.error('Error while trying to get the customerId : ' + str(request.GET['customerId']))
      except GLVoucherTransaction.DoesNotExist:
         logger.error('Error while trying to get the voucher transactions from customer :' + str(request.GET['customerId']))


   #}}}#
