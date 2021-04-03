
import logging
from datetime import datetime, timedelta
import datetime
import os
from glPdf.glReportAsPDF import GLReportAsPDF 
from glPdf.VoissReportDispatcher import VoissReportDispatcher
from glPdf.VoissReportIsland import VoissReportIsland

logger = logging.getLogger(__name__)

REPORT_DESC              = "Reporte"
REPORT_PDF_EXT           = '.pdf'
REPORT_XLS_EXT           = '.xls'

class GLReportsEngine:

   def __init__(self):#{{{#
      self.reportName =""
   #}}}#

   def getReportObject(self,reportId,fileNameReport):#{{{#
      return {
          '2' : VoissReportDispatcher(fileNameReport) ,
          '1' : VoissReportIsland(fileNameReport) ,
       }[reportId]
   #}}}#

   def getReportAsPdf(self,reportId, request):#{{{#

      self.reportName = REPORT_DESC + str(datetime.datetime.now()) + REPORT_PDF_EXT
      report = self.getReportObject(reportId,os.path.dirname(os.path.abspath(__file__)) + '/static/reports/' + self.reportName)
      report.generateReport(request)

      return self.reportName
   #}}}#

   def getReportAsExcel(self,reportId, request):#{{{#

      self.reportName= REPORT_DESC + str(datetime.datetime.now()) + REPORT_PDF_EXT

      return 'report.xls'
   #}}}#

