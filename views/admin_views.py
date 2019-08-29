from django.shortcuts import render
import requests
from django.contrib import auth
from django.template import Context,loader
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from face_detection.models import UserData,Branch,LoyaltyPoint,Purchase,LoyaltyManager,BranchStaffCode,Coupon,UsersCoupon,Setting,Company,CompanyEmailTemplate,UserProfile,Useragree,CompanySettings
from django.contrib.auth.models import User
from face_detection.forms import ImageForm,UserForm,ManagerLoginForm,CustomerStatusForm,PurchaseForm,RedeemForm,CustomerListForm,LoyaltyBenefitListForm,CheckStaffCodeForm,CouponForm,CustomerDeleteForm,updateNetworkAdminProfile,CompanyLogoForm,updateCompanyProfile,CompanyAgreeForm,updateCompany,CompanySettingsForm
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe
import json
import os
from django.db.models.functions import Coalesce
from django.db.models import Sum
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.utils.crypto import get_random_string
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models import Q
import operator
from functools import reduce
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.text import normalize_newlines
import math
# Create your views here.
from django.contrib.auth.signals import user_logged_in


# This function is to check if user is assigned to group and if assigned to a group, is it assigned to a company or branch after login.
def check_after_login(sender, user, request, **kwargs):

    if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
        try:
            getCompany = Company.objects.get(user_id = request.user.id,status='a')
            pass
        except:
            messages.error(request, 'You are not assigned to any Company, Please contact Administrator')
            auth.logout(request)
    elif request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():
        try:
            getBranch = Branch.objects.get(user_id = request.user.id)
            pass
        except:
            messages.error(request, 'You are not assigned to any Branch, Please contact your Network Administrator')
            auth.logout(request)
    elif request.user.groups.filter(name=settings.ADMIN_GROUP).exists():
        pass
    else:
        if request.user.is_superuser:
            pass
        else:
            messages.error(request, 'You are not assigned to any group, Please contact Administrator')
            auth.logout(request)

user_logged_in.connect(check_after_login)


def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False

    return user_passes_test(in_groups, login_url='/admin/login')

#Manager reports
@group_required(settings.STORE_MANAGER_GROUP)
def my_model_list_view_manager(request):

    from_date_search = ''
    to_date_search = ''
    from_date = request.GET.get('from_date')
    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    #get logged in user
    current_user = request.user

    #get logged in user's company
    branch = Branch.objects.get(user_id =current_user )
    company = Company.objects.get(id =branch.company_id )
    q_list = [Q(branch=branch.id), ]
    if from_date_search != '':
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        q_list.append(Q(created_at__lte=to_date_search))

    #get total customers based on purchases
    total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()

    #get new customers based on purchases
    total_previous_new_customers = []
    prev_q_list = [Q(id__gte=0),]
    if from_date_search != '':
        prev_q_list.append(Q(created_at__lt=from_date_search))
        prev_q_list.append(Q(branch=branch.id),)

        previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
        if previous_new_customers is not None :
            for x in previous_new_customers:
                total_previous_new_customers.append(x['userdata_id'])

    new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()

    #get new customers based on registrations
    #new_customers = UserData.objects.filter(reduce(operator.and_, q_list)).count()

    #get total purchase by company users
    total_purchase = Purchase.objects.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))

    if total_customers > 0:
        avg_spend_per_cus = total_purchase['tot_amount']/float(total_customers)
    else:
        avg_spend_per_cus = 0

    if new_customers > 0:
        average_spend_per_new_cus = total_purchase['tot_amount']/float(new_customers)
    else:
        average_spend_per_new_cus = 0

    ql_list = [Q(branch=branch.id),Q(tx_type='REDEEM'), ]
    if from_date_search != '':
        ql_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        ql_list.append(Q(created_at__lte=to_date_search))

    total_loyalty_points_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_points=Coalesce(Sum('loyalty_points'),0))

    total_loyalty_value_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_value=Coalesce(Sum('loyalty_value'),0))

    total_users_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).values('userdata_id').distinct().count()

    context = {'manager_name':current_user.first_name+' '+current_user.last_name,'company_name':company.name,'company_address':company.address,'branch_address':branch.address, 'total_customers': total_customers,'new_customers':new_customers,'avg_spend_per_cus':avg_spend_per_cus,'average_spend_per_new_cus':average_spend_per_new_cus,'total_users_reclaimed':total_users_reclaimed,'total_loyalty_points_reclaimed':total_loyalty_points_reclaimed['loyalty_points'],'total_loyalty_value_reclaimed':total_loyalty_value_reclaimed['loyalty_value'],'from_date':from_date,'to_date':to_date,'branch':branch.id}
    r = render(request, 'admin/reports/reports_manager.html', context)
    return HttpResponse(r)

#Network admin Reports
@group_required(settings.NETWORK_GROUP)
def my_model_list_view(request):

    from_date_search = ''
    to_date_search = ''
    from_date = request.GET.get('from_date')
    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    #get logged in user
    current_user = request.user

    #get logged in user's company
    company = Company.objects.get(user_id =current_user )

    q_list = [Q(branch__company_id=company.id), ]
    if from_date_search != '':
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        q_list.append(Q(created_at__lte=to_date_search))

    #get total customers based on purchases
    total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()
    #get new customers based on purchases
    total_previous_new_customers = []
    prev_q_list = [Q(id__gte=0),]
    if from_date_search != '':
        prev_q_list.append(Q(created_at__lt=from_date_search))
        prev_q_list.append(Q(branch__company_id=company.id),)

        previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
        if previous_new_customers is not None :
            for x in previous_new_customers:
                total_previous_new_customers.append(x['userdata_id'])

    new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()
    #new_customers = UserData.objects.filter(reduce(operator.and_, q_list)).count()

    #get total purchase by company users
    total_purchase = Purchase.objects.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))

    if total_customers > 0:
        avg_spend_per_cus = total_purchase['tot_amount']/float(total_customers)
    else:
        avg_spend_per_cus = 0

    if new_customers > 0:
        average_spend_per_new_cus = total_purchase['tot_amount']/float(new_customers)
    else:
        average_spend_per_new_cus = 0

    ql_list = [Q(company=company.id),Q(tx_type='REDEEM'), ]
    if from_date_search != '':
        ql_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        ql_list.append(Q(created_at__lte=to_date_search))

    total_loyalty_points_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_points=Coalesce(Sum('loyalty_points'),0))

    total_loyalty_value_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_value=Coalesce(Sum('loyalty_value'),0))

    total_users_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).values('userdata_id').distinct().count()

    context = {'total_customers': total_customers,'new_customers':new_customers,'avg_spend_per_cus':avg_spend_per_cus,'average_spend_per_new_cus':average_spend_per_new_cus,'total_users_reclaimed':total_users_reclaimed,'total_loyalty_points_reclaimed':total_loyalty_points_reclaimed['loyalty_points'],'total_loyalty_value_reclaimed':total_loyalty_value_reclaimed['loyalty_value'],'from_date':from_date,'to_date':to_date,'selected_company':int(company.id)}
    r = render(request, 'admin/reports/reports.html', context)
    return HttpResponse(r)


#Admin group
@group_required(settings.ADMIN_GROUP)
def my_model_list_view_admin(request):

    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')

    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')
    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    #get logged in user
    current_user = request.user

    #get logged in user's company
    #company = Company.objects.get(user_id =current_user )

    #q_list = [Q(branch__company_id=company.id), ]
    q_list = [Q(id__gte=0),]

    if selected_company is not None and selected_company != '':
        q_list.append(Q(branch__company_id=selected_company),)

    if from_date_search != '':
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        q_list.append(Q(created_at__lte=to_date_search))



    #get total customers based on purchases
    total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()

    total_previous_new_customers = []
    prev_q_list = [Q(id__gte=0),]
    if from_date_search != '':
        prev_q_list.append(Q(created_at__lt=from_date_search))
        if selected_company is not None and selected_company != '':
            prev_q_list.append(Q(branch__company_id=selected_company),)

        previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
        if previous_new_customers is not None :
            for x in previous_new_customers:
                total_previous_new_customers.append(x['userdata_id'])

    #get new customers based on purchases
    new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()

    #new_customers = UserData.objects.filter(reduce(operator.and_, q_list)).count()

    #get total purchase by company users
    total_purchase = Purchase.objects.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))

    if total_customers > 0:
        avg_spend_per_cus = total_purchase['tot_amount']/float(total_customers)
    else:
        avg_spend_per_cus = 0

    if new_customers > 0:
        average_spend_per_new_cus = total_purchase['tot_amount']/float(new_customers)
    else:
        average_spend_per_new_cus = 0

    #ql_list = [Q(userdata__branch__company=company.id),Q(tx_type='REDEEM'), ]



    ql_list = [Q(tx_type='REDEEM'), ]

    if selected_company is not None and selected_company != '':
        ql_list.append(Q(company=selected_company),)

    if from_date_search != '':
        ql_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        ql_list.append(Q(created_at__lte=to_date_search))


    total_loyalty_points_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_points=Coalesce(Sum('loyalty_points'),0))

    total_loyalty_value_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_value=Coalesce(Sum('loyalty_value'),0))

    total_users_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).values('userdata_id').distinct().count()

    if selected_company is None or selected_company == '':
        selected_company = 0

    context = {'total_customers': total_customers,'new_customers':new_customers,'avg_spend_per_cus':avg_spend_per_cus,'average_spend_per_new_cus':average_spend_per_new_cus,'total_users_reclaimed':total_users_reclaimed,'total_loyalty_points_reclaimed':total_loyalty_points_reclaimed['loyalty_points'],'total_loyalty_value_reclaimed':total_loyalty_value_reclaimed['loyalty_value'],'from_date':from_date,'to_date':to_date,'companies': companies,'selected_company':int(selected_company)}
    r = render(request, 'admin/reports/reports_admin.html', context)
    return HttpResponse(r)

	
#Admin group
@group_required(settings.ADMIN_GROUP)
def my_model_list_view_admin_coupon(request):

    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')    
    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')
    
    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')         

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d') 

    current_user = request.user
       
    q_list = [Q(id__gte=0),]
	
    q_list.append(Q(user_type = 'non-registered'))
	
    if selected_company is not None and selected_company != '':
        q_list.append(Q(company_id=selected_company),)
        
    if from_date_search != '':
        q_list.append(Q(coupondetail__created_at__gte=from_date_search))       

    if to_date_search != '':
        q_list.append(Q(coupondetail__created_at__lte=to_date_search))        
	
    if from_date_search != '' and to_date_search != '':
        q_list.append(Q(coupondetail__created_at__range=[from_date_search,to_date_search]))

    #get all coupons based on purchases      
    coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company','CouponDetail').values('company_id','coupon_code','bid','amount','coupon_count','company__name').annotate(dcount=Count('coupondetail__coupon_id')) 
   
    if selected_company is None or selected_company == '':
        selected_company = 0

    context = {'coupons': coupons,'companies': companies,'selected_company':int(selected_company),'from_date':from_date,'to_date':to_date}

    r = render(request, 'admin/reports/reports_coupon_admin.html', context)
    return HttpResponse(r)
	
#export reports
@staff_member_required
def my_model_export_coupon(request): #show list of all objects.

    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')
    
    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')

    date_text = 'All Dates'

    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')  
        #from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S.%f')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        #to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d 23:59:59.%f')
       

    if from_date == '' and to_date == '':
        date_text = 'All Dates'
    else:
        if from_date == '' and to_date != '':
            date_text = 'To '+to_date

        if from_date != '' and to_date == '':
            date_text = 'From '+from_date

        if from_date != '' and to_date != '':
            date_text = 'From '+from_date+' To '+to_date

    #get logged in user
    current_user = request.user   

    if selected_company is None or selected_company == '' or selected_company == '0':
        company_name = "All Companies"
        selected_company = 0
    else:
        company = Company.objects.get(pk=selected_company)        
        company_name = company.name
    
    csv_data = [
        ['EYE-D-Solutions','','','',''],
        ['Coupon Clicks Report','','','',''],
        ['Company : '+company_name,'','','',''],
        ['Date : '+date_text,'','','',''],
        ['Company','Voucher','Bid Value', 'Views', 'Cost'],
    ]
   

    q_list = [Q(id__gte=0),]
	
    q_list.append(Q(user_type = 'non-registered'))
	
    if selected_company is not None and selected_company != '' and selected_company != str(0) and selected_company != 0:
        q_list.append(Q(company_id=selected_company),)            
    
    if from_date_search != '':            
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':            
        q_list.append(Q(created_at__lte=to_date_search))

    if from_date_search != '' and to_date_search != '':
        q_list.append(Q(coupondetail__created_at__range=[from_date_search,to_date_search]))  
   		
            
    #coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company').values('company_id','coupon_code','bid','amount','coupon_count','company__name') 
    coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company','coupondetail').values('company_id','coupon_code','bid','amount','coupon_count','company__name').annotate(dcount=Count('coupondetail__coupon_id'))
	
	
    if not coupons:
        #context = [company.name,'-',0.00,0,0.00]            
        context =['No record found']
        csv_data.append(context)
    else:
        for coupon in coupons:                                                    
            context = [coupon['company__name'],coupon['coupon_code'],coupon['bid'],coupon['dcount'],coupon['bid']*coupon['dcount'] ]         
            csv_data.append(context)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_model_export_coupon.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response


	
	
#update profile
@group_required(settings.NETWORK_GROUP,settings.STORE_MANAGER_GROUP,settings.ADMIN_GROUP)
def form_handle(request):
    #get logged in user
    current_user = request.user
    form = updateNetworkAdminProfile(initial={'first_name':current_user.first_name,'last_name':current_user.last_name})
    #get logged in user's profile
    already_found = ''
    try:
        profile = UserProfile.objects.get(user_id =current_user)
        already_found ='yes'
        if profile.image:
            if default_storage.exists(profile.image.path):
                image = mark_safe('<img src="{}" width="100" height="100" />'.format(profile.image.url))
            else:
                image = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        else:
            image = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
    except UserProfile.DoesNotExist:
        image = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')

    if request.method == 'POST':

        form = updateNetworkAdminProfile(request.POST,request.FILES)
        if form.is_valid():
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            user = User.objects.get(pk = current_user.id)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            if request.FILES:
                image_uploaded = request.FILES["image"]

                if already_found == 'yes':
                    if profile.image:
                        os.unlink(profile.image.path)
                    profile.image = image_uploaded
                    profile.save()
                else:
                    profile = UserProfile(image=image_uploaded,user_id=current_user.id)
                    profile.save()
            messages.success(request, 'Your profile updated successfully')
            return HttpResponseRedirect("/admin/change_profile")
    context = {'form': form,'image':image}
    r = render(request, 'admin/change_profile.html', context)
    return HttpResponse(r)

#change company logo by network admin
@group_required(settings.NETWORK_GROUP)
def form_handle_company(request):
    #get logged in user
    current_user = request.user
    form = updateCompanyProfile()
    #get logged in user's profile
    company = Company.objects.get(user_id =current_user)

    if default_storage.exists(company.logo.path):
        logo = mark_safe('<img src="{}" width="100" height="100" />'.format(company.logo.url))
    else:
        logo = mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')

    if request.method == 'POST':
        form = updateCompanyProfile(request.POST,request.FILES)
        if form.is_valid():
            logo = request.FILES["logo"]
            os.unlink(company.logo.path)
            company.logo = logo
            company.save()
            messages.success(request, 'Company logo updated successfully')
            return HttpResponseRedirect("/admin/change_company_profile")
    context = {'form': form,'logo':logo}
    r = render(request, 'admin/change_company_profile.html', context)
    return HttpResponse(r)


#for change company drop down in admin for users (Branch managers)
@csrf_exempt
@group_required(settings.ADMIN_GROUP)
def change_company(request):
    #get logged in user
    current_user = request.user
    form = updateCompany()
    record = {}
    if request.method == 'POST':
        form = updateCompany(request.POST)
        if form.is_valid():
            user_id = request.POST['user_id']
            user_data = User.objects.get(pk = user_id)
            company_id = request.POST['company_id']
            already = ''
            try:
                profile = UserProfile.objects.get(user_id=user_id)
                already = 'yes'
            except:
                pass

            if already == 'yes':
                profile.company_id = company_id
                profile.save()
            else:
                save_user_profile = UserProfile(company_id=company_id,user_id=user_id,added_by='A')
                save_user_profile.save()
            messages.success(request, user_data.first_name+" "+user_data.last_name+"'s company changed successfully!")
            record = {"success":1, "message":user_data.first_name+" "+user_data.last_name+"'s company changed successfully!" }
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"success":0, "message":errors3.replace(".","") }

    return JsonResponse(record, safe=False)

#to get branch managers of company
@csrf_exempt
def get_branch_managers(request):

    if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
        CompanyDetails = Company.objects.get(user_id=request.user)
        company_id = CompanyDetails.id
    else:
        if 'company_id' in request.POST:
            company_id = request.POST['company_id']

    selected_user_id = request.POST['selected_user_id']

    try:
        users = UserProfile.objects.filter(company_id=company_id).all()
    except:
        users = []

    user_html = ''
    if users:
        for user in users:
            user_detail = User.objects.get(pk = user.user_id)
            selected = ''
            if selected_user_id == str(user.user_id):
                selected = 'selected'

            user_html += '<option value="'+str(user.user_id)+'" '+selected+'>'+user_detail.first_name+' '+user_detail.last_name+' ('+user_detail.username+')</option>'
    else:
        pass

    return HttpResponse(user_html)


#export reports
@staff_member_required
def my_model_export(request): #show list of all objects.


    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')

    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')

    date_text = 'All Dates'

    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    if from_date == '' and to_date == '':
        date_text = 'All Dates'
    else:
        if from_date == '' and to_date != '':
            date_text = 'To '+to_date

        if from_date != '' and to_date == '':
            date_text = 'From '+from_date

        if from_date != '' and to_date != '':
            date_text = 'From '+from_date+' To '+to_date


    #get logged in user
    current_user = request.user

    #get logged in user's company
    #company = Company.objects.get(user_id =current_user )

    #q_list = [Q(branch__company_id=company.id), ]

    if selected_company is None or selected_company == '' or selected_company == '0':
        company_name = "All Companies"
        selected_company = 0
    else:
        company = Company.objects.get(pk=selected_company)
        #print(company)
        company_name = company.name

    csv_data = [
        ['', '', '', '', 'EYE-D-Solutions','','','',''],
        ['', '', '', '', 'Company : '+company_name,'','','',''],
        ['', '', '', '', 'Date : '+date_text,'','','',''],
        ['Company','Branch','Total Customers', 'New Customers', 'Average spend per customer', 'Average spend per new customer','Total loyalty points reclaimed','Total users reclaimed loyalty points','Total loyalty value reclaimed'],
    ]

    admin_companies = []
    if selected_company is not None and selected_company != '' and selected_company != str(0) and selected_company != 0:
        admin_companies = Company.objects.filter(pk=selected_company)
    else:
        admin_companies = Company.objects.filter().order_by('name')



    for company in admin_companies:

        branches = Branch.objects.filter(company_id = company.id)
        #print(branches)
        if not branches:
            context = [company.name,'-',0,0,0.00,0.00,0,0,0]
            #print(context)
            csv_data.append(context)
        else:
            for branch in branches:
                q_list = [Q(id__gte=0),]

                q_list.append(Q(branch=branch),)


                if from_date_search != '':
                    q_list.append(Q(created_at__gte=from_date_search))

                if to_date_search != '':
                    q_list.append(Q(created_at__lte=to_date_search))

                #get total customers based on purchases
                total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()

                total_previous_new_customers = []
                prev_q_list = [Q(id__gte=0),]
                if from_date_search != '':
                    prev_q_list.append(Q(created_at__lt=from_date_search))
                    #if selected_company is not None and selected_company != '':
                    prev_q_list.append(Q(branch=branch),)

                    previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
                    if previous_new_customers is not None :
                        for x in previous_new_customers:
                            total_previous_new_customers.append(x['userdata_id'])

                    #get new customers based on purchases
                new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()

                #get new customers based on registrations
                #new_customers = UserData.objects.filter(reduce(operator.and_, q_list)).count()

                #get total purchase by company users
                total_purchase = Purchase.objects.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))

                if total_customers > 0:
                    avg_spend_per_cus = total_purchase['tot_amount']/float(total_customers)
                else:
                    avg_spend_per_cus = 0

                if new_customers > 0:
                    average_spend_per_new_cus = total_purchase['tot_amount']/float(new_customers)
                else:
                    average_spend_per_new_cus = 0

                #ql_list = [Q(userdata__branch__company=company.id),Q(tx_type='REDEEM'), ]



                ql_list = [Q(tx_type='REDEEM'), ]

                #if selected_company is not None and selected_company != '' and selected_company != str(0):
                ql_list.append(Q(branch=branch),)

                if from_date_search != '':
                    ql_list.append(Q(created_at__gte=from_date_search))

                if to_date_search != '':
                    ql_list.append(Q(created_at__lte=to_date_search))


                total_loyalty_points_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_points=Coalesce(Sum('loyalty_points'),0))

                total_loyalty_value_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_value=Coalesce(Sum('loyalty_value'),0))

                total_users_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).values('userdata_id').distinct().count()

                context = [company.name,branch.name,total_customers,new_customers,round(avg_spend_per_cus,2),round(average_spend_per_new_cus,2),total_loyalty_points_reclaimed['loyalty_points'],total_users_reclaimed,total_loyalty_value_reclaimed['loyalty_value']]

                csv_data.append(context)


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_model_export.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response

#export report in branch manager
@staff_member_required
def my_model_export_branch(request): #show list of all objects.


    from_date_search = ''
    to_date_search = ''
    branch = request.GET.get('branch')

    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')

    date_text = 'All Dates'

    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    if from_date == '' and to_date == '':
        date_text = 'All Dates'
    else:
        if from_date == '' and to_date != '':
            date_text = 'To '+to_date

        if from_date != '' and to_date == '':
            date_text = 'From '+from_date

        if from_date != '' and to_date != '':
            date_text = 'From '+from_date+' To '+to_date


    #get logged in user
    current_user = request.user

    #get logged in user's company
    #company = Company.objects.get(user_id =current_user )

    #q_list = [Q(branch__company_id=company.id), ]
    q_list = [Q(id__gte=0),]

    # if branch is not None and branch != '' and branch != str(0):
    q_list.append(Q(branch=branch),)

    if from_date_search != '':
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        q_list.append(Q(created_at__lte=to_date_search))

    #get total customers based on purchases
    total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()

    total_previous_new_customers = []
    prev_q_list = [Q(id__gte=0),]
    if from_date_search != '':
        prev_q_list.append(Q(created_at__lt=from_date_search))
        prev_q_list.append(Q(branch=branch),)

        previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
        if previous_new_customers is not None :
            for x in previous_new_customers:
                total_previous_new_customers.append(x['userdata_id'])

    #get new customers based on purchases
    new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()

    #get new customers based on registrations
    #new_customers = UserData.objects.filter(reduce(operator.and_, q_list)).count()

    #get total purchase by company users
    total_purchase = Purchase.objects.filter(reduce(operator.and_, q_list)).aggregate(tot_amount=Coalesce(Sum('amount'),0))

    if total_customers > 0:
        avg_spend_per_cus = total_purchase['tot_amount']/float(total_customers)
    else:
        avg_spend_per_cus = 0

    if new_customers > 0:
        average_spend_per_new_cus = total_purchase['tot_amount']/float(new_customers)
    else:
        average_spend_per_new_cus = 0

    #ql_list = [Q(userdata__branch__company=company.id),Q(tx_type='REDEEM'), ]



    ql_list = [Q(tx_type='REDEEM'), ]

    #if selected_company is not None and selected_company != '' and selected_company != str(0):
    ql_list.append(Q(branch=branch),)

    if from_date_search != '':
        ql_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        ql_list.append(Q(created_at__lte=to_date_search))


    total_loyalty_points_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_points=Coalesce(Sum('loyalty_points'),0))

    total_loyalty_value_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).aggregate(loyalty_value=Coalesce(Sum('loyalty_value'),0))

    total_users_reclaimed = LoyaltyPoint.objects.filter(reduce(operator.and_, ql_list)).values('userdata_id').distinct().count()

    branch_det = Branch.objects.get(pk=branch)
    branch_name = branch_det.name

    company_det = Company.objects.get(pk=branch_det.company_id)
    company_name = company_det.name

    csv_data = [
        ['', '', '', 'EYE-D-Solutions','','',''],
        ['', '', '', 'Company : '+company_name,'','',''],
        ['', '', '', 'Branch : '+branch_name,'','',''],
        ['', '', '', 'Date : '+date_text,'','',''],
        ['Total Customers', 'New Customers', 'Average spend per customer', 'Average spend per new customer','Total loyalty points reclaimed','Total users reclaimed loyalty points','Total loyalty value reclaimed'],
    ]

    context = [total_customers,new_customers,round(avg_spend_per_cus,2),round(average_spend_per_new_cus,2),total_loyalty_points_reclaimed['loyalty_points'],total_users_reclaimed,total_loyalty_value_reclaimed['loyalty_value']]

    csv_data.append(context)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_template_name.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response


#export purchases
@staff_member_required
def my_model_export_purchase(request): #show list of all objects.

    from_date_search = ''
    to_date_search = ''
    branch = request.GET.get('branch')
    company = request.GET.get('company')
    customer = request.GET.get('customer')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    branch_txt = 'All Branches'
    if branch is not None and branch != str(0):
        try:
            branch_det = Branch.objects.get(pk=branch)
            branch_txt = branch_det.name
        except:
            branch_txt = ''
    else:
        branch_txt = 'All Branches'

    company_txt = 'All Companies'
    if company is not None and company != str(0):
        try:
            company_det = Companies.objects.get(pk=company)
            company_txt = company_det.name
        except:
            company_txt = ''
    else:
        company_txt = 'All Companies'

    customer_txt = 'All Customers'
    if customer is not None and customer != str(0):
        try:
            customer_det = UserData.objects.get(pk=customer)
            customer_txt = customer_det.FirstName+' '+customer_det.LastName
        except:
            customer_txt = ''
    else:
        customer_txt = 'All Customers'

    date_text = 'All Dates'

    if from_date is None and from_date == str(0):
        from_date =''

    if from_date != '' and from_date != str(0):
        from_date_search = datetime.strptime(from_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None and to_date == str(0):
        to_date =''

    if to_date != '' and to_date != str(0):
        to_date_search = datetime.strptime(to_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    if (from_date == '' and to_date == '') or (from_date == str(0) and to_date == str(0)):
        date_text = 'All Dates'
    else:
        if (from_date == '' or from_date == str(0)) and ( to_date != '' and to_date != str(0)):
            date_text = 'To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        if (to_date == '' or to_date == str(0)) and ( from_date != '' and from_date != str(0)):
            date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        if (from_date != '' and to_date != '' and from_date != str(0) and to_date != str(0)):
            date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')+' To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

    ql_list = [Q(id__gte=0),]

    if company is not None and company != '' and company != str(0):
        ql_list.append(Q(branch__company_id=company),)

    if customer is not None and customer != '' and customer != str(0):
        ql_list.append(Q(userdata_id=customer),)

    if branch is not None and branch != '' and branch != str(0):
        ql_list.append(Q(branch=branch),)

    if from_date_search != '':
        ql_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':
        ql_list.append(Q(created_at__lte=to_date_search))

    purchases = Purchase.objects.filter(reduce(operator.and_, ql_list)).order_by('-id')
    #return HttpResponse(purchases)
    csv_data = [
        ['', '', '', 'EYE-D-Solutions','','',''],
        #['', '', '', 'Company : '+company_txt,'','',''],
        ['', '', '', 'Branch : '+branch_txt,'','',''],
        #['', '', '', 'Customer : '+customer_txt,'','',''],
        #['', '', '', 'Date : '+date_text,'','',''],
        ['Customer', 'Company', 'Branch', 'Amount', 'Purchase Summary','Coupon','Created at'],
    ]

    if purchases is not None :
        for pur in purchases:
            if pur.coupon is not None :
                purcoupon = pur.coupon
            else:
                purcoupon = ''
            context = [pur.userdata,pur.branch.company,pur.branch,str(pur.amount),pur.purchase_summary,purcoupon,datetime.strptime(str(pur.created_at), '%Y-%m-%d').strftime('%d/%m/%Y')]
            csv_data.append(context)
    #return HttpResponse(csv_data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Purchases_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_template_name.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response



#export branches
@staff_member_required
def export_branch_data(request): #show list of all objects.
    from_date_search = ''
    to_date_search = ''
    company = request.GET.get('company')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    # branch_txt = 'All Branches'
    # if branch is not None and branch != str(0):
    #     try:
    #         branch_det = Branch.objects.get(pk=branch)
    #         branch_txt = branch_det.name
    #     except:
    #         branch_txt = ''
    # else:
    #     branch_txt = 'All Branches'

    # date_text = 'All Dates'

    # if from_date is None and from_date == str(0):
    #     from_date =''

    if from_date != '' and from_date != str(0):
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    # to_date = request.GET.get('to_date')
    # if to_date is None and to_date == str(0):
    #     to_date =''

    if to_date != '' and to_date != str(0):
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')

    # if (from_date == '' and to_date == '') or (from_date == str(0) and to_date == str(0)):
    #     date_text = 'All Dates'
    # else:
    #     if (from_date == '' or from_date == str(0)) and ( to_date != '' and to_date != str(0)):
    #         date_text = 'To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

    #     if (to_date == '' or to_date == str(0)) and ( from_date != '' and from_date != str(0)):
    #         date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')

    #     if (from_date != '' and to_date != '' and from_date != str(0) and to_date != str(0)):
    #         date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')+' To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

    ql_list = [Q(id__gte=0),]

    if company is not None and company != '' and company != str(0):
        ql_list.append(Q(company=company),)

    # if from_date_search != '':
    #     ql_list.append(Q(created_at__gte=from_date_search))

    # if to_date_search != '':
    #     ql_list.append(Q(created_at__lte=to_date_search))

    branches = Branch.objects.filter(reduce(operator.and_, ql_list)).values('id','company__name','company__contact_name','company__email','address','name').order_by('-id')
    #return HttpResponse(purchases)
    csv_data = [
        ['Company Name', 'Contact Name', 'Contact Email', 'Branch Address','Branch Name','Total Customers','New Customers'],
    ]

    #return HttpResponse(branches)
    if branches is not None :
        for branch in branches:

            total_previous_new_customers = []
            prev_q_list = [Q(id__gte=0),]
            if from_date_search != '':
                prev_q_list.append(Q(created_at__lt=from_date_search))
                prev_q_list.append(Q(branch=branch['id']),)

                previous_new_customers = Purchase.objects.filter(reduce(operator.and_, prev_q_list)).values('userdata_id').distinct()
                if previous_new_customers is not None :
                    for x in previous_new_customers:
                        total_previous_new_customers.append(x['userdata_id'])


            q_list =[]
            total_customers =0
            new_customers =0
            q_list = [Q(id__gte=0),]
            q_list.append(Q(branch=branch['id']),)
            if from_date_search != '':
                q_list.append(Q(created_at__gte=from_date_search))

            if to_date_search != '':
                q_list.append(Q(created_at__lte=to_date_search))

            #get total customers based on purchases
            total_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).count()

            #get new customers based on purchases
            new_customers = Purchase.objects.filter(reduce(operator.and_, q_list)).exclude(userdata_id__in=total_previous_new_customers).values('userdata_id').distinct().count()

            # new_cust = Branch.objects.users.filter().count()
            context = [branch['company__name'],branch['company__contact_name'],branch['company__email'],mark_safe(normalize_newlines(branch['address']).replace('\n', ' ').replace(',', ' ')),branch['name'],total_customers,new_customers]
            csv_data.append(context)
    #return HttpResponse(csv_data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Branch_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_template_name.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response


#change company settings by network admin
@group_required(settings.NETWORK_GROUP)
def change_company_settings(request):
    #get logged in user
    current_user = request.user
    company = Company.objects.get(user_id =current_user)

    is_already = ''
    set_loyalty_on = False
    try:
        check_already = CompanySettings.objects.get(company=company)
        is_already = 'yes'

        if check_already.loyalty_on == 1:
            set_loyalty_on = True
    except:
        pass

    form = CompanySettingsForm(initial={'loyalty_on':set_loyalty_on})
    #get logged in user's profile

    if request.method == 'POST':

        form = CompanySettingsForm(request.POST)
        if form.is_valid():

            if request.POST.get('loyalty_on', False) == 'on':
                loyalty_on = True
            else:
                loyalty_on = False

            if is_already == 'yes':
                check_already = CompanySettings.objects.get(company=company)
                check_already.loyalty_on = loyalty_on
                check_already.save()
            else:
                set_settings = CompanySettings(company = company, loyalty_on = loyalty_on)
                set_settings.save()
            messages.success(request, 'Company setting updated successfully')
            return HttpResponseRedirect("/admin/change_company_settings")
    context = {'form': form}
    r = render(request, 'admin/change_company_settings.html', context)
    return HttpResponse(r)

	
#export network  reports
@staff_member_required
def my_model_export_network_coupon(request): 

    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')

    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')

    date_text = 'All Dates'

    if from_date is None:
        from_date =''

    if from_date != '':
        #from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S.%f')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        #to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S.%f')

    if from_date == '' and to_date == '':
        date_text = 'All Dates'
    else:
        if from_date == '' and to_date != '':
            date_text = 'To '+to_date

        if from_date != '' and to_date == '':
            date_text = 'From '+from_date

        if from_date != '' and to_date != '':
            date_text = 'From '+from_date+' To '+to_date

    #get logged in user
    current_user = request.user

    #get logged in user's company
    
    if selected_company is None or selected_company == '' or selected_company == '0':
        company_name = "All Companies"
        selected_company = 0
    else:
        company = Company.objects.get(pk=selected_company)
        #print(company)
        company_name = company.name

    csv_data = [
        ['EYE-D-Solutions','','','',''],
        ['Coupon Clicks Report','','','',''],
        ['Company : '+company_name,'','','',''],
        ['Date : '+date_text,'','','',''],
        ['Company','Voucher','Bid Value', 'Views', 'Cost'],
    ]

    q_list = [Q(id__gte=0),]

    if selected_company is not None and selected_company != '' and selected_company != str(0) and selected_company != 0:
        q_list.append(Q(company_id=selected_company),)            
    
    if from_date_search != '':            
        q_list.append(Q(created_at__gte=from_date_search))

    if to_date_search != '':            
        q_list.append(Q(created_at__lte=to_date_search))
    
    coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company').values('company_id','coupon_code','bid','amount','coupon_count','company__name')

    if not coupons:
        #context = [company.name,'-',0.00,0,0.00]            
        context = ['No record found']
        csv_data.append(context)
    else:
        for coupon in coupons:                                                    
            context = [coupon['company__name'],coupon['coupon_code'],coupon['bid'],coupon['coupon_count'],coupon['amount']]        
            csv_data.append(context)


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_model_export_network_coupon.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response


#Network admin Reports
@group_required(settings.NETWORK_GROUP)
def my_model_list_view_network_coupon(request):

    from_date_search = ''
    to_date_search = ''
    from_date = request.GET.get('from_date')
    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')  

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')  

    #get logged in user
    current_user = request.user

    #get logged in user's company
    company = Company.objects.get(user_id =current_user )

    q_list = [Q(company_id=company.id), ] 
	
    q_list.append(Q(user_type = 'non-registered'))
	
    if from_date_search != '':
        q_list.append(Q(coupondetail__created_at__gte=from_date_search))

    if to_date_search != '':
        q_list.append(Q(coupondetail__created_at__lte=to_date_search))
		
    if from_date_search != '' and to_date_search != '':
        q_list.append(Q(coupondetail__created_at__range=[from_date_search,to_date_search]))         

		
    #print(q_list)
    #return HttpResponse(q_list)
    #get all coupons based on         
    coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company','coupondetail').values('company_id','coupon_code','bid','amount','coupon_count','company__name').annotate(dcount=Count('coupondetail__coupon_id'))
   
    context = {'coupons': coupons,'from_date':from_date,'to_date':to_date,'selected_company':int(company.id)}    
    r = render(request, 'admin/reports/reports_coupon_network.html', context)
    return HttpResponse(r)



#export network  reports
@staff_member_required
def my_model_export_network_coupon(request): 

    from_date_search = ''
    to_date_search = ''
    selected_company = request.GET.get('selected_company')

    companies = Company.objects.filter().order_by('name')
    from_date = request.GET.get('from_date')

    date_text = 'All Dates'

    if from_date is None:
        from_date =''

    if from_date != '':
        from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        #from_date_search = datetime.strptime(from_date, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S.%f')

    to_date = request.GET.get('to_date')
    if to_date is None:
        to_date =''

    if to_date != '':
        to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        #to_date_search = datetime.strptime(to_date, '%d/%m/%Y').strftime('%Y-%m-%d 23:59:59.%f')

    if from_date == '' and to_date == '':
        date_text = 'All Dates'
    else:
        if from_date == '' and to_date != '':
            date_text = 'To '+to_date

        if from_date != '' and to_date == '':
            date_text = 'From '+from_date

        if from_date != '' and to_date != '':
            date_text = 'From '+from_date+' To '+to_date

    #get logged in user
    current_user = request.user

    #get logged in user's company    
    if selected_company is None or selected_company == '' or selected_company == '0':
        company_name = "All Companies"
        selected_company = 0
    else:
        company = Company.objects.get(pk=selected_company)
        #print(company)
        company_name = company.name

    csv_data = [
        ['EYE-D-Solutions','','','',''],
        ['Coupon Clicks Report','','','',''],
        ['Company : '+company_name,'','','',''],
        ['Date : '+date_text,'','','',''],
        ['Company','Voucher','Bid Value', 'Views', 'Cost'],
    ]

    q_list = [Q(id__gte=0),]
	
    q_list.append(Q(user_type = 'non-registered'))
	
    if selected_company is not None and selected_company != '' and selected_company != str(0) and selected_company != 0:
        q_list.append(Q(company_id=selected_company),)            
    
    if from_date_search != '':            
        q_list.append(Q(coupondetail__created_at__gte=from_date_search))

    if to_date_search != '':            
        q_list.append(Q(coupondetail__created_at__lte=to_date_search))
		
    if from_date_search != '' and to_date_search != '':
        q_list.append(Q(coupondetail__created_at__range=[from_date_search,to_date_search]))
 
    
    coupons = Coupon.objects.filter(reduce(operator.and_, q_list)).select_related('company','coupondetail').values('company_id','coupon_code','bid','amount','coupon_count','company__name').annotate(dcount=Count('coupondetail__coupon_id'))

    if not coupons:
        #context =[company.name,'-',0.00,0,0.00]            
        context = ['No record found']
        csv_data.append(context)
    else:
        for coupon in coupons:                                                    
            context = [coupon['company__name'],coupon['coupon_code'],coupon['bid'],coupon['dcount'],coupon['bid'] * coupon['dcount']]        
            csv_data.append(context)


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Report_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_model_export_network_coupon.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response
	

#to get bid calculation of a coupon
@csrf_exempt
def bid_calculation(request):
              
    bid_value = request.GET['request_data'] 
    current_date = datetime.today()	    

    if bid_value:
        bid_position = Coupon.objects.filter(bid__gt=bid_value,expiry_date__gte=current_date).count()
        bid_position = bid_position+1
    print(bid_position)
    return HttpResponse(bid_position)   
    