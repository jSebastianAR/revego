# coding=utf-8

from django.contrib import admin
from django import forms
from django.contrib.admin import DateFieldListFilter
from django.http import HttpResponse
from django.contrib.admin.models import LogEntry
from django.core.exceptions import ValidationError
from django.conf import settings

from pumpsModule.models import GLStationGroup
from pumpsModule.models import GLStation

from pumpsModule.models import GLShift
from pumpsModule.models import GLWebCommand
from pumpsModule.models import GLPartialDelivery
from pumpsModule.models import GLDevice
from pumpsModule.models import GLUser
from pumpsModule.models import GLCustomer
from pumpsModule.models import GLFunctions
from pumpsModule.models import GLUserFunction

class GLStationGroupAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vStationGroupId','vStationName','vStationGroupDesc']
   list_filter   = ['vStationName']
   search_fields = ['vStationName','vStationGroupDesc']

#}}}#

class GLStationAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vStationId','vStationDesc','vStationGroupId','vRequireDispatcher','vStationWHost', 'vStationWPort','vBilling', 'vPrintTime', 'vSimulatePort', 'vUsePoints', 'vUseFleets', 'vUseTAE']
   list_filter   = ['vStationDesc','vStationGroupId__vStationName']
   search_fields = ['vStationDesc','vStationGroupId__vStationName']

#}}}#

class GLDeviceAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vDeviceId','vUserId', 'vDeviceName', 'vUserAgent','vOldUserAgent', 'vIPAddress', 'vDeviceToken','vIsActive', 'vPrintTicket', 'vStationId' , 'Tipo','vVirtualKeyboard']
   list_filter   = ['vUserId__vName','vDeviceName','vIPAddress', 'vDeviceToken']
   search_fields = ['vUserId__vName','vDeviceName','vIPAddress', 'vDeviceToken']
   def Tipo(self, obj):
      return obj.vUserId.vKind

#}}}#

class GLShiftAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vShift']
   list_filter   = ['vShift']
   search_fields = ['vShift']

#}}}#

class GLWebCommandAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vWebCommandId', 'vStationId', 'vUserId','vCommandKind','vCommandInfo','vIsActive','vCommandStatus','vStartDate','vEndDate','vStatusResponse']
   list_filter   = ['vCommandKind']
   search_fields = ['vCommandInfo']

#}}}#

class GLPartialDeliveryAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vPartialDeliveryId', 'vUserId', 'vDate', 'vShiftId', 'vCashAmount', 'vVoucherAmountC', 'vVoucherAmountD', 'vOthersAmount','vOthersDesc']
   list_filter   = ['vShiftId', 'vUserId']
   search_fields = ['vShiftId', 'vUserId']

#}}}#


class GLUserForm(forms.ModelForm):
      class Media:
            js = ('http://code.jquery.com/jquery-1.11.0.min.js', settings.STATIC_URL +'admin/js/validate.js')

class GLUserAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vUserId','vStationId','vName','vLastname','vKind','vIsAdmin','vAge', 'vMail','vPhone', 'vMobilePhone','vUserAccess','vIsKiosk']
   list_filter   = ['vKind', 'vStationId']
   search_fields = ['vName','vUserAccess', 'vPassAccess', 'vLastname', 'vAge', 'vMail']

   form          = GLUserForm

   #def has_delete_permission(self, request, obj=None):
   #   return False

   #def get_actions(self, request):
   #   actions = super(GLUserAdmin, self).get_actions(request)
   #   del actions['delete_selected']
   #   return actions

#}}}#

class GLCustomerAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vCustomerId', 'vBusinessName', 'vRFC', 'vCreationDate', 'vStatus', 'vKind', 'vMail']
   list_filter   = ['vCustomerId']
   search_fields = ['vCustomerId']

   #def has_delete_permission(self, request, obj=None):
   #   return False

   #def get_actions(self, request):
   #   actions = super(GLUserAdmin, self).get_actions(request)
   #   del actions['delete_selected']
   #   return actions

#}}}#

class GLUsersInline(admin.TabularInline):#{{{#
   model= GLUserFunction
   extra=1
   #}}}#

class GLFunctionsAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vFunctionsId', 'vFunctionName', 'vFunctionDesc','vOrder']
   list_filter   = ['vFunctionsId']
   search_fields = ['vFunctionsId']

   inlines = [GLUsersInline]

   #def has_delete_permission(self, request, obj=None):
   #   return False

   #def get_actions(self, request):
   #   actions = super(GLUserAdmin, self).get_actions(request)
   #   del actions['delete_selected']
   #   return actions

#}}}#

class GLAuditAdmin(admin.ModelAdmin):#{{{#
   list_display  = ['vAuditDescription']
   list_filter   = ['vAuditDescription']
   search_fields = ['vAuditDescription']

#}}}#

class LogEntryAdmin(admin.ModelAdmin):#{{{#

   def getActionString(self):
      switcher =  {
                  1: "CREATE",
                  2: "MODIFY",
                  3: "DELETE",
                  10: "LOGIN",
                  11: "REGISTER",
                  12: "ACTIVATE",
                  13: "QUERY_FLEETS",
                  14: "PURCHASE_FLEETS",
                  }
      return switcher[self.action_flag]

   list_display  = ['user','object_repr', getActionString ,'content_type', 'action_time']
   list_filter   = ['user','content_type', ('action_time',DateFieldListFilter),'action_flag']
   search_fields = ['object_repr']

   def has_add_permission(self, request):
      return False

   def changelist_view(self, request, extra_context=None):
      self.list_display_links = (None, )
      return super(LogEntryAdmin, self).changelist_view(request, extra_context=None)

   def has_change_permission(self, request, obj=None):
      if obj is not None :
         return False
      return super(LogEntryAdmin, self).has_change_permission(request, obj=obj)

   def get_actions(self, request):
      actions = super(LogEntryAdmin, self).get_actions(request)
      del actions['delete_selected']
      return actions
   #}}}#

admin.site.register(GLStationGroup, GLStationGroupAdmin)
admin.site.register(GLStation, GLStationAdmin)
admin.site.register(GLDevice, GLDeviceAdmin)
admin.site.register(GLShift, GLShiftAdmin)
admin.site.register(GLWebCommand, GLWebCommandAdmin)
admin.site.register(GLPartialDelivery, GLPartialDeliveryAdmin)
admin.site.register(GLUser, GLUserAdmin)
admin.site.register(GLCustomer, GLCustomerAdmin)
admin.site.register(GLFunctions, GLFunctionsAdmin)
admin.site.register(LogEntry, LogEntryAdmin)

