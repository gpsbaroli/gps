from django.contrib import admin
from .models import Branch,UserData,Coupon,UsersCoupon,Company,EmailTemplate,Setting,LoyaltyManager,CompanyEmailTemplate,Purchase,UserProfile,CompanyRating, Allergy ,CustomerAllergy
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as origGroupAdmin
from django.forms import CheckboxSelectMultiple
from . import models
from datetime import datetime
from django.contrib.auth.models import  Group,User
from .forms import CouponAdminForm
from django.core.mail import EmailMessage
from django.conf import settings
from django.core import serializers
import json
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe
import requests
from django.db.models import Sum
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from django.forms.fields import CheckboxInput
from django.db.models import Count
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.contrib.admin import DateFieldListFilter
# from daterange_filter.filter import DateRangeFilter
from django.db.models.functions import Coalesce
from django.utils.safestring import mark_safe
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from .filters import SingleTextInputFilter
from django.db.models import Q
import operator
from functools import reduce
from django.contrib.admin import SimpleListFilter
from datetime import timedelta
admin.site.site_url = ''


class CompanyRatingAdmin(admin.ModelAdmin):
    list_per_page = 20

    def get_list_filter(self, request):
        def custom_titled_filter(title):
            class Wrapper(admin.FieldListFilter):
                def __new__(cls, *args, **kwargs):
                    instance = admin.FieldListFilter.create(*args, **kwargs)
                    instance.title = title
                    return instance
            return Wrapper
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            return (('userdata', custom_titled_filter('Customer')),)
        else:
            return ('company',('userdata', custom_titled_filter('Customer')),)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return True
        else:
            return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return actions
        else:
            return False

    def get_list_display(self, request):
        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return ('company','get_customer','get_rating','get_review','all_actions')
        else:
            return ('company','get_customer','get_rating','get_review')

    #list_display = ('company','get_customer','get_rating','get_review','all_actions')
    #list_display_links = None

    list_display_links = ('all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

    #def all_actions(self,obj):
        #return mark_safe(u"<a href='%d/change/?type=%s'><span class='changelink'>Edit</span></a>" % (obj.id,obj.user_type))

    def get_queryset(self, request):
        qs = super(CompanyRatingAdmin, self).get_queryset(request)

        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return qs
        else:
            CompanyDetails = Company.objects.get(user_id=request.user)
            return qs.filter(company=CompanyDetails)

    def get_customer(self, obj):
        return obj.userdata

    get_customer.short_description = 'Customer'

    def get_review(self, obj):
        return obj.message

    get_review.short_description = 'Review'

    def get_rating(self, obj):
        return mark_safe('<span class="stars">'+str(obj.rating)+'</span>')

    get_rating.short_description = 'Rating'

admin.site.register(CompanyRating,CompanyRatingAdmin)

class EmailTemplateAdmin(admin.ModelAdmin):
    list_per_page = 20
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('subject','all_actions')
    search_fields = ('subject',)
    list_display_links = ('all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

admin.site.register(EmailTemplate,EmailTemplateAdmin)

class FilterCompanyEmailTemplateAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        CompanyDetails = Company.objects.get(user_id=request.user)
        obj.company = CompanyDetails
        obj.save()

class CompanyEmailTemplateAdmin(FilterCompanyEmailTemplateAdmin):
    list_per_page = 20
    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    fieldsets = (
        (None, {
           'fields': ('subject','body','template_type')
        }),
    )
   #readonly_fields = ('company',)
    def get_queryset(self, request):
        qs = super(CompanyEmailTemplateAdmin, self).get_queryset(request)

        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return qs
        else:
            CompanyDetails = Company.objects.get(user_id=request.user)
            return qs.filter(company=CompanyDetails)

    list_display = ('subject','template_type','all_actions')
    search_fields = ('subject',)
    list_display_links = ('all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

admin.site.register(CompanyEmailTemplate,CompanyEmailTemplateAdmin)

class UserDataAdmin(admin.ModelAdmin):
    list_per_page = 20
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('image_tag','FirstName', 'LastName','greeting_name')
    readonly_fields = ('image_tag','PersistedFaceId','image','Email','phone_number','date_of_birth','staff_code','updated_staffcode_at','created_at','is_active','is_deleted','is_agree')
    search_fields = ('FirstName','LastName','Email')
    list_filter = (('created_at', DateRangeFilter),'useragree__company_id')

    list_display_links = ('image_tag', 'FirstName')
    # def get_company(self, obj):
    #     return obj.branch.company

    '''def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions'''

    actions = ['delete_selected']

    def publish_selected(self, request, queryset):
        #print('sadjlskajlksaflkhslfhsa66666666666666')
        queryset.update(status='p')

    def delete_selected(self, request, queryset):
        customerid=request.POST["_selected_action"]

        #print(companyid)

        # branches = Branch.objects.filter(company_id = companyid).values('id','company_id')
        #get_purchase_list = Purchase.objects.filter(branch__company_id = companyid).update(branch_id = 19)
        Purchase.objects.filter(userdata_id=customerid).update(userdata_id=getattr(settings, "ANNOTATE_USER_ID", None) , removed_from=customerid)
        UserData.objects.filter(id=customerid).delete()
        #super(Company,self).delete()


    def get_queryset(self, request):
        qs = super(UserDataAdmin, self).get_queryset(request)
        return qs.filter(is_deleted='N')

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

    # get_company.short_description = 'Company'
    # get_company.admin_order_field = 'branch__company'

admin.site.register(UserData,UserDataAdmin)

# class IsVeryBenevolentFilter(admin.SimpleListFilter):
#     title = 'Total customer by date'
#     parameter_name = 'get_tot_cus'

#     def lookups(self, request, model_admin):
#         return (
#             ('Yes', 'Yes'),
#             ('No', 'No'),
#         )

#     def queryset(self, request, queryset):
#         value = self.value()
#         if value == 'Yes':
#             return queryset.filter(users__created_at__gt=75)
#         elif value == 'No':
#             return queryset.exclude(users__created_at__gt=75)
#         return queryset

# class MyDateTimeFilter(DateFieldListFilter):
#     def __init__(self, *args, **kwargs):
#         super(MyDateTimeFilter, self).__init__(*args, **kwargs)

#         now = timezone.now()
#         if timezone.is_aware(now):
#             now = timezone.localtime(now)

#         today = now.date()

#         self.links += ((
#             (_('Next 7 days'), {
#                 self.lookup_kwarg_since: str(today),
#                 self.lookup_kwarg_until: str(today + datetime.timedelta(days=7)),
#             }),
#         ))

class CatalogCityFilter(SingleTextInputFilter):
    title = 'Purchase Date'
    parameter_name = 'from_date'
    parameter_name2 = 'to_date'

    def queryset(self, request, queryset):
        return queryset

class BranchAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('name','user', 'company','address','get_tot_cus','get_new_cus','average_spend_per_cus','average_spend_per_new_cus','total_loyalty_points_reclaimed','total_customers_reclaimed_loyalty_points','total_loyalty_value_reclaimed','all_actions')
    search_fields = ('name','user__first_name','company__name')


    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            return [(None, {
               'fields': ('name','user','address')
            })]
        else:
            return [(None, {
           'fields': ('name','company','user','address')
        }),]
    readonly_fields = ('latitude','longitude')
    # list_filter = ('company', ('users__created_at', DateTimeRangeFilter))
    list_filter = ('company',)
    list_display_links =('name','all_actions')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit choices for 'picture' field to only your pictures."""
        if db_field.name == 'user':
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                CompanyData = Company.objects.get(user_id =request.user)
                kwargs["queryset"] = User.objects.filter(userprofile__company_id=CompanyData.id,groups__name= settings.STORE_MANAGER_GROUP)
            else:
                if 'company' in request.POST:
                    company = request.POST['company']
                    kwargs["queryset"] = User.objects.filter(userprofile__company_id=company,groups__name= settings.STORE_MANAGER_GROUP)
                else:
                    pass

        return super(BranchAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def __call__(self, request, *args, **kwargs):
        self.request = request
        return super(BranchAdmin, self).__call__(request, *args, **kwargs)

    def changelist_view(self, request, extra_context=None):
        self.request = request
        extra_context = extra_context or {}

        if request.GET.get('company__id__exact') is not None:
            extra_context['company'] = request.GET.get('company__id__exact')
        else:
            extra_context['company'] = 0

        if request.GET.get('from_date') is not None:
            extra_context['from_date'] = request.GET.get('from_date')
        else:
            extra_context['from_date'] = ''

        if request.GET.get('to_date') is not None:
            extra_context['to_date'] = request.GET.get('to_date')
        else:
            extra_context['to_date'] = ''

        return super(BranchAdmin, self).changelist_view(request, extra_context=extra_context)

    def get_list_filter(self, request):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            return (CatalogCityFilter,)
        else:
            return ('company',CatalogCityFilter)

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_add_permission(self, request):
    #     if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
    #         return False
    #     else:
    #         return ['name','all_actions']

    # def __init__(self, *args, **kwargs):
    #     super(BranchAdmin, self).__init__(*args, **kwargs)
    #     self.list_display_links = (None, )
    # def get_list_display_links(self, request, list_display):
    #     if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
    #         return None
    #     else:
    #         return True
    # def has_change_permission(self, request, obj=None):
    #     if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
    #         return False
    #     else:
    #         return True

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

    actions = ['delete_selected',]

    def delete_selected(self, request, queryset):
        queryset.update(is_deleted='Y')

    def get_form(self,request,obj=None, **kwargs):
        self.exclude = []
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            self.exclude.append('company')
            self.exclude.append('is_deleted')
        else:
            self.exclude.append('is_deleted')
        return super(BranchAdmin,self).get_form(request, obj=None, **kwargs)

    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            CompanyDetails = Company.objects.get(user_id=request.user)
            obj.company = CompanyDetails
            obj.save()
        else:
            obj.save()

    def get_queryset(self, request):
        qs = super(BranchAdmin, self).get_queryset(request)

        if request.user.groups.filter(name='admin').exists():
            return qs.filter(is_deleted='N')
        else:
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                CompanyDetails = Company.objects.get(user_id=request.user)
                return qs.filter(company=CompanyDetails,is_deleted='N')
            else:
                BranchDetails = Branch.objects.get(user_id=request.user)
                return qs.filter(id=BranchDetails.id,is_deleted='N')


    def get_tot_cus(self, obj):
        #game_id = request.GET.get('company__id', None)
        #return 3q_list = [Q(id__gte=0)]
        q_list = [Q(id__gte=0)]
        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        return obj.tot_users.filter(reduce(operator.and_, q_list)).count()
    get_tot_cus.short_description = 'Total Customers'

    def get_new_cus(self, obj):
        #return obj.users.filter(created_at__gte = '2018-06-01',created_at__lte = '2018-06-06').count()
        # request = globals['radio_grid_admin_request']
        # self.from_date = self.request.GET['from_date']
        total_previous_new_customers = []
        prev_q_list = [Q(id__gte=0),]
        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            prev_q_list.append(Q(created_at__lt=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

            previous_new_customers = obj.tot_users.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
            if previous_new_customers is not None :
                for x in previous_new_customers:
                    total_previous_new_customers.append(x['userdata_id'])


        q_list = [Q(id__gte=0)]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))


        return obj.tot_users.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()
        #return obj.users.filter().count()
    get_new_cus.short_description = 'New Customers'

    def average_spend_per_cus(self, obj):
        q_list = [Q(id__gte=0)]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        total_purchase = obj.tot_users.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))
        total_customer = obj.tot_users.filter(reduce(operator.and_, q_list)).count()
        if total_customer > 0:
            return round(total_purchase['tot_amount']/float(total_customer),2)
        else:
            return '-'
    average_spend_per_cus.short_description = 'Avg spend per customer'
    average_spend_per_cus.allow_tags = True
    def average_spend_per_new_cus(self, obj):

        total_previous_new_customers = []
        prev_q_list = [Q(id__gte=0),]
        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            prev_q_list.append(Q(created_at__lt=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

            previous_new_customers = obj.tot_users.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
            if previous_new_customers is not None :
                for x in previous_new_customers:
                    total_previous_new_customers.append(x['userdata_id'])


        q_list = [Q(id__gte=0)]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))
        total_purchase = obj.tot_users.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))
        total_new_customer = obj.tot_users.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()
        if total_new_customer > 0:
            return round(total_purchase['tot_amount']/float(total_new_customer),2)
        else:
            return '-'
    average_spend_per_new_cus.short_description = 'Avg spend per new customer'

    def total_loyalty_points_reclaimed(self,obj):
        q_list = [Q(tx_type='REDEEM')]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        total_loyalty_points_reclaimed = obj.branch_loyalty_points.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('loyalty_points'),0))
        # total_loyalty_points_reclaimed = obj.users.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('loyalty_points__loyalty_points'),0))
        return total_loyalty_points_reclaimed['tot_amount']

    def total_customers_reclaimed_loyalty_points(self,obj):
        q_list = [Q(tx_type='REDEEM')]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        total_customers_reclaimed_loyalty_points = obj.branch_loyalty_points.filter(reduce(operator.and_, q_list)).values('userdata_id').distinct().count()

        # total_loyalty_points_reclaimed = obj.tot_users.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('purchase_loyalty_points__loyalty_points'),0))

        return total_customers_reclaimed_loyalty_points


    def total_loyalty_value_reclaimed(self,obj):
        q_list = [Q(tx_type='REDEEM')]

        if self.request.GET.get('from_date') is not None and self.request.GET.get('from_date') != '':
            q_list.append(Q(created_at__gte=datetime.strptime(self.request.GET.get('from_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        if self.request.GET.get('to_date') is not None and self.request.GET.get('to_date') != '':
            q_list.append(Q(created_at__lte=datetime.strptime(self.request.GET.get('to_date'), '%d/%m/%Y').strftime('%Y-%m-%d')))

        # total_loyalty_value_reclaimed = obj.tot_users.filter(reduce(operator.and_, q_list)).aggregate(tot_value=Coalesce(Sum('purchase_loyalty_points__loyalty_value'),0))
        total_loyalty_value_reclaimed = obj.branch_loyalty_points.filter(reduce(operator.and_, q_list)).aggregate(tot_value=Coalesce(Sum('loyalty_value'),0))
        return total_loyalty_value_reclaimed['tot_value']

    total_loyalty_value_reclaimed.short_description = 'Total loyalty value reclaimed ('+settings.CURRENCY_SYMBOL+')'

admin.site.register(Branch,BranchAdmin)

class FilterLoyaltyManagerAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        CompanyDetails = Company.objects.get(user_id=request.user)
        obj.company = CompanyDetails
        obj.save()



class LoyaltyManagerAdmin(FilterLoyaltyManagerAdmin):
    list_per_page = 20
    list_display = ('loyalty_points','benefit','loyalty_value','created_at','all_actions')
    list_display_links = ('all_actions',)
    list_filter = ('loyalty_points',)
    readonly_fields = ('created_at',)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')

    def get_queryset(self, request):
        qs = super(LoyaltyManagerAdmin, self).get_queryset(request)
        if request.user.groups.filter(name='admin').exists():
            return qs
        CompanyDetails = Company.objects.get(user_id=request.user)
        return qs.filter(company=CompanyDetails)

    fieldsets = (
        (None, {
           'fields': ('loyalty_points','benefit','loyalty_value')
        }),
    )

admin.site.register(LoyaltyManager,LoyaltyManagerAdmin)

class SettingAdmin(admin.ModelAdmin):
    list_per_page = 20
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    actions = None

    # admin_views = (
    #                 ('Redirect to CNN', 'redirect_to_cnn'),
    #                 ('Go to revsys.com', 'http://www.revsys.com'),
    #     )

    # def redirect_to_cnn(self, *args, **kwargs):
    #     return redirect('http://www.cnn.com')

    fieldsets = (
        (None, {
           'fields': ('image_tag','logo','email', 'phone_number', 'address')
        }),
        ('Social Links', {
            'fields': ('facebook', 'twitter'),
        }),
    )
    list_display = ('email','image_tag','phone_number', 'address', 'facebook', 'twitter','all_actions')

    readonly_fields = ('image_tag',)

    list_display_links = ('all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')

    #search_fields = ('email','user__first_name','company__name')
    #list_filter = ('company',)

admin.site.register(Setting,SettingAdmin)

class CompanyAdmin(admin.ModelAdmin):
    list_per_page = 20
    fieldsets = (
        (None, {
           'fields': ('image_tag','logo','name','user','status')
        }),
        ('Contact Details', {
            'fields': ('contact_name', 'phone_number', 'email','address','address_line2','town','county','post_code','company_website','company_phone_number'),
        }),
    )

    list_display = ('image_tag','name','user','contact_name','phone_number','email','all_actions')
    search_fields = ('name','user__first_name')
    readonly_fields = ('image_tag',)
    list_display_links = ('image_tag', 'name','all_actions')

    actions = ['delete_selected']

    def publish_selected(self, request, queryset):
        #print('sadjlskajlksaflkhslfhsa66666666666666')
        queryset.update(status='p')

    def delete_selected(self, request, queryset):
        companyid=request.POST["_selected_action"]

        #print(companyid)

        # branches = Branch.objects.filter(company_id = companyid).values('id','company_id')
        get_purchase_list = Purchase.objects.filter(branch__company_id = companyid).update(branch_id = 19)
        Company.objects.filter(id=companyid).delete()
        #super(Company,self).delete()



    #def get_actions(self, request):
        #actions = super().get_actions(request)
        #if 'delete_selected' in actions:
            #actions = [delete_model]
            #del actions['delete_selected']
        #return actions

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')




admin.site.register(Company,CompanyAdmin)

class FilterCouponAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        CompanyDetails = Company.objects.get(user_id=request.user)
        obj.company = CompanyDetails
        obj.save()


class CouponAdmin(FilterCouponAdmin):
    list_per_page = 20
    # list_display = ('image_tag','coupon_code','discount_type','amount','expiry_date','minimum_spend','maximum_spend','display_users','all_actions')
    list_display = ('image_tag','coupon_code_1','discount_type','amount','expiry_date','display_users','coupon_count1','user_type','all_actions')
    search_fields = ('coupon_code','users__Email')
    list_filter = ('expiry_date','discount_type','users__Email','user_type')
    readonly_fields = ('image_tag',)
    #form = CouponAdminForm
    list_display_links = ('image_tag', 'coupon_code_1')

    def get_fieldsets(self, request, obj=None):

        if ('type' in request.GET and request.GET['type']=='non-registered'):
            fieldsets = ((None, {
                'fields': ('user_type','image_tag','image','coupon_code','description','discount_type','amount','bid','expiry_date','minimum_spend','maximum_spend')
            }),)
        elif ('type' in request.GET and request.GET['type']=='registered'):
            fieldsets = ((None, {
                'fields': ('user_type','users','image_tag','image','coupon_code','description','discount_type','amount','expiry_date','minimum_spend','maximum_spend')
            }),)
        elif (obj.user_type == 'non-registered'):
            fieldsets = ((None, {
                'fields': ('user_type','image_tag','image','coupon_code','description','discount_type','amount','bid','expiry_date','minimum_spend','maximum_spend')
            }),)
        elif (obj.user_type == 'registered'):
            fieldsets = ((None, {
                'fields': ('user_type','users','image_tag','image','coupon_code','description','discount_type','amount','expiry_date','minimum_spend','maximum_spend')
            }),)

        return fieldsets
        #return super(CouponAdmin, self).get_fieldsets(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    def get_queryset(self, request):
        qs = super(CouponAdmin, self).get_queryset(request)
        if request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
            return qs
        CompanyDetails = Company.objects.get(user_id=request.user)
        return qs.filter(company=CompanyDetails)

    def all_actions(self,obj):
        return mark_safe(u"<a href='%d/change/?type=%s'><span class='changelink'>Edit</span></a>" % (obj.id,obj.user_type))

    def coupon_code_1(self,obj):
        return mark_safe(u"<a href='%d/change/?type=%s'>%s</a>" % (obj.id,obj.user_type,obj.coupon_code))
    coupon_code_1.short_description = 'Coupon Code'
    coupon_code_1.allow_tags = True

    def image_tag(self,obj):
        if obj.image:
            if default_storage.exists(obj.image.path):
                img_src = '<img src="{}" width="100" height="100" />'.format(obj.image.url)
                return mark_safe(u"<a href='%d/change/?type=%s'>%s</a>" % (obj.id,obj.user_type,img_src))
            else:
                img_src = '<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />'
                return mark_safe(u"<a href='%d/change/?type=%s'>%s</a>" % (obj.id,obj.user_type,img_src))
        else:
            return 'No image'
    image_tag.short_description = "Image"

    def coupon_count1(self,obj):
        return mark_safe(u"%d" % obj.coupon_count)
    coupon_count1.short_description = 'Viewed'


    filter_horizontal = ('users',)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Limit choices for 'picture' field to only your pictures."""
        if db_field.name == 'users':
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                #UserRec = Purchase.objects.filter( branch_id = 3)
                #return HttpResponse(UserRec[0].userdata_id)
                #purchase__branch_id
                search_by_date = request.GET.get('search_by_date')
                if(search_by_date):
                    #not_purchased_yet = []
                    CompanyData = Company.objects.get(user_id =request.user)
                    company_id = CompanyData.id

                    total_company_users = []
                    all_company_users = UserData.objects.filter(useragree__company_id = company_id).values('id').distinct()
                    if all_company_users is not None :
                        for x in all_company_users:
                            total_company_users.append(x['id'])

                    #datetime_search_by_date = datetime.strptime(search_by_date, '%Y-%m-%d')
                    #six_months_back_date = datetime_search_by_date - timedelta(6*365/12)

                    get_purchased_users = Purchase.objects.filter(branch__company_id = company_id, userdata_id__in = total_company_users, created_at__gt = search_by_date).values('userdata_id').distinct()

                    total_purchased_users = []
                    if get_purchased_users is not None :
                        for x in get_purchased_users:
                            total_purchased_users.append(x['userdata_id'])

                    kwargs["queryset"] = UserData.objects.filter(useragree__company_id = company_id).exclude(id__in=total_purchased_users)
                else:
                    CompanyData = Company.objects.get(user_id =request.user)
                    company_id = CompanyData.id
                    kwargs["queryset"] = UserData.objects.filter(useragree__company_id = company_id,is_deleted='N')
            else:
                CompanyData = Company.objects.get(user_id =request.user)
                company_id = CompanyData.id
                kwargs["queryset"] = UserData.objects.filter(useragree__company_id = company_id,is_deleted='N')
            return super(CouponAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    class Media:
        css = {
             'all': ('face_detection/css/custom_coupons.css',)
        }


admin.site.register(Coupon,CouponAdmin)

class UserAdmin(BaseUserAdmin):
    list_per_page = 20
    list_display_links = ('username','all_actions',)
    list_select_related = ('userprofile', )


    def get_list_display(self, request):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            return ('username','get_image', 'email', 'first_name', 'last_name','all_actions')
        else:
            return ('username','get_image','get_groups','get_company', 'email', 'first_name', 'last_name','all_actions')

    def get_list_filter(self, request):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            return None
        else:
            return ('groups',)

    def get_fieldsets(self, request, obj=None):
        if obj:
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                return [(None, {
                    'classes': ('wide',),
                    'fields': ('first_name', 'last_name','email', 'username', 'password'),
                })]
            else:
                return [(None, {
                    'classes': ('wide',),
                    'fields': ('first_name', 'last_name','email', 'username', 'password', 'groups'),
                })]
        else:
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                return [(None, {
                    'classes': ('wide',),
                    'fields': ('first_name', 'last_name','email', 'username', 'password1', 'password2'),
                })]
            else:
                return [(None, {
                    'classes': ('wide',),
                    'fields': ('first_name', 'last_name','email', 'username', 'password1', 'password2', 'groups' ),
                })]

    def get_groups(self, obj):
        groups = obj.groups.values('name')
        grp = ''
        for group in groups:
            grp += group['name']
        return grp
    get_groups.short_description = 'Group'

    def get_image(self, instance):
        try:
            if instance.userprofile.image:
                if default_storage.exists(instance.userprofile.image.path):
                    logo = mark_safe('<img src="{}" width="100" height="100" />'.format(instance.userprofile.image.url))
                else:
                    logo = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
            else:
                logo = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        except:
            logo = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')

        return logo
    get_image.short_description = 'Image'

    def get_company(self, instance):
        selected  = 'xyz'
        if instance.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
            selected = ''
            try:
                if instance.userprofile.company_id is not None:
                    selected = instance.userprofile.company_id
            except:
                pass

            CompanyData = Company.objects.all()

            company = '<select data-id="'+str(instance.id)+'" class="change_company"><option value ="" >Select one</option>'
            if CompanyData:
                for cmpny in CompanyData:
                    if cmpny.id == selected:
                        company += '<option selected value="'+str(cmpny.id)+'">'+cmpny.name+'<option>'
                    else:
                        company += '<option value="'+str(cmpny.id)+'">'+cmpny.name+'<option>'

            company += '<select>'

            company=mark_safe(company)
        else:
            company = 'NA'

        return company
    get_company.short_description = 'Company'

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)

        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            CompanyData = Company.objects.get(user_id =request.user)
            GroupDetails = Group.objects.get(name=settings.STORE_MANAGER_GROUP)
            return qs.filter(groups=GroupDetails,userprofile__company_id = CompanyData.id)
        else:
            return qs

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.save()
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            adminOb = Group.objects.get(name=settings.STORE_MANAGER_GROUP)
            adminOb.user_set.add(obj.pk)
            adminOb.save()

            already_found = ''
            #print(obj.pk)
            CompanyData = Company.objects.get(user_id =request.user)
            try:
                profile = UserProfile.objects.get(user_id =obj.pk)
                already_found ='yes'
            except UserProfile.DoesNotExist:
                already_found = ''

            if already_found == 'yes':
                profile.company_id = CompanyData.id
                profile.save()
            else:
                profile = UserProfile(user_id =obj.pk, company_id=CompanyData.id,added_by='NA')
                profile.save()

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class GroupAdmin(origGroupAdmin):
    list_per_page = 20
    list_display = ('name', 'all_actions')
    list_display_links = ('name','all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')
    all_actions.short_description = 'actions'

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

class BranchFilter(SimpleListFilter):
    title = 'Branch'
    parameter_name = 'branch'

    def lookups(self, request, model_admin):
        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            CompanyDetails = Company.objects.get(user_id=request.user)
            branches = Branch.objects.filter(company_id = CompanyDetails.id,is_deleted='N')
            return [(c.id, c.name) for c in branches]
        else:
            branches = Branch.objects.filter(is_deleted='N')
            return [(c.id, c.name) for c in branches]

    def queryset(self,request,queryset):
        if self.value():
            return queryset.filter(branch  = self.value())

class PurchaseAdmin(admin.ModelAdmin):
    list_per_page = 20
    actions = None
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def custom_titled_filter(title):
        class Wrapper(admin.FieldListFilter):
            def __new__(cls, *args, **kwargs):
                instance = admin.FieldListFilter.create(*args, **kwargs)
                instance.title = title
                return instance
        return Wrapper

    def get_queryset(self, request):
        qs = super(PurchaseAdmin, self).get_queryset(request)

        if request.user.groups.filter(name='admin').exists():
            return qs
        else:
            if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
                CompanyDetails = Company.objects.get(user_id=request.user)
                return qs.filter(branch__company=CompanyDetails)
            else:
                BranchDetails = Branch.objects.get(user_id=request.user)
                return qs.filter(branch=BranchDetails.id)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if request.GET.get('created_at__gte') is not None:
            extra_context['from_date'] = request.GET.get('created_at__gte')
        else:
            extra_context['from_date'] = 0

        if request.GET.get('created_at__lte') is not None:
            extra_context['to_date'] = request.GET.get('created_at__lte')
        else:
            extra_context['to_date'] = 0

        if request.GET.get('branch__id__exact') is not None:
            extra_context['branch'] = request.GET.get('branch__id__exact')
        else:
            if request.GET.get('branch') is not None:
                extra_context['branch'] = request.GET.get('branch')
            else:
                if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
                    BranchDetails = Branch.objects.get(user_id=request.user)
                    extra_context['branch'] = BranchDetails.id
                else:
                    extra_context['branch'] = 0

        if request.GET.get('userdata__id__exact') is not None:
            extra_context['customer'] = request.GET.get('userdata__id__exact')
        else:
            extra_context['customer'] = 0


        if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
            CompanyDetails = Company.objects.get(user_id=request.user)
            extra_context['company'] = CompanyDetails.id
        else:
            if request.GET.get('branch__company__id__exact') is not None:
                extra_context['company'] = request.GET.get('branch__company__id__exact')
            else:
                extra_context['company'] = 0

        return super(PurchaseAdmin, self).changelist_view(request, extra_context=extra_context)

    fieldset = (
        (None, {
            'classes': ('wide',),
            'fields': ('branch', 'userdata','amount', 'purchase_summary', 'coupon_code', 'discount_type', 'discount_amount','created_at'),
        }),
    )

    readonly_fields = ('branch', 'userdata','amount', 'purchase_summary', 'coupon', 'coupon_code', 'discount_type', 'discount_amount','created_at')

    list_display = ('get_userdata','get_company', 'branch','amount','purchase_summary','coupon','created_at')
    # list_filter = (('created_at', DateRangeFilter),('userdata', custom_titled_filter('Customer')),'branch__company','branch')
    list_filter = (('created_at', DateRangeFilter),BranchFilter,)

    def get_list_filter(self, request):
        if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
            return (('created_at', DateRangeFilter),)
        else:
            return (('created_at', DateRangeFilter),BranchFilter,)

    def get_userdata(self, obj):
        return obj.userdata

    get_userdata.short_description = 'Customer'

    def get_company(self, obj):
        return obj.branch.company

    get_company.short_description = 'Company'
    get_company.admin_order_field = 'branch__company'
admin.site.register(Purchase, PurchaseAdmin)





class AllergyAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('name', 'all_actions')
    list_display_links = ('name','all_actions',)

    def all_actions(self,obj):
        return mark_safe('<span class="changelink">Edit</span>')

admin.site.register(Allergy, AllergyAdmin)
