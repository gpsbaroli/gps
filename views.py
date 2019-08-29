import requests
from django.template import Context,loader
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from .models import UserData,Branch,LoyaltyPoint,Purchase,LoyaltyManager,BranchStaffCode,Coupon,UsersCoupon,Setting,Company,CompanyEmailTemplate,UserProfile,Useragree
from django.contrib.auth.models import User
from .forms import ImageForm,UserForm,ManagerLoginForm,CustomerStatusForm,PurchaseForm,RedeemForm,CustomerListForm,LoyaltyBenefitListForm,CheckStaffCodeForm,CouponForm,CustomerDeleteForm,updateNetworkAdminProfile,CompanyLogoForm,updateCompanyProfile,CompanyAgreeForm
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

def facedetect(imagedata):
    #return image

    headers = { 'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY, 'Content-Type':'application/octet-stream' }
    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise',
    }

    face_api_url = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/detect/'
    response = requests.post(face_api_url,  headers=headers, data = imagedata, params=params )
    return response


def createFaceList(request):
    headers = { 'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY }
    params = urllib.parse.urlencode({
	})
    try:
	    conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
	    conn.request("PUT", "/face/v1.0/largefacelists/facedetectionlist_new?%s" % params, '{"name": "sample_list","userData": "User-provided data attached to the face list."}', headers)
	    response = conn.getresponse()
	    data = response.read()
	    conn.close()
	    return HttpResponse(data);

    except Exception as e:
	    print("[Errno {0}] {1}".format(e.errno, e.strerror))

def addFacetoList(imagedata):
    #return image

    headers = { 'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY, 'Content-Type':'application/octet-stream' }
    params = {
        'userData': ''
    }

    face_api_url = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists/facedetectionlist_new/persistedFaces/'
    response = requests.post(face_api_url,  headers=headers, data = imagedata, params=params )
    return response

def getFaceList(request):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
        'start': '1',
        'top': '1000',
    })

    try:
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("GET", "/face/v1.0/largefacelists/facedetectionlist_new/persistedfaces?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def TrainFaceList(request):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largefacelists/facedetectionlist_new/train?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return HttpResponse(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def FindSimilarinFaceList(face_id):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
    })

    conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')

    #return HttpResponse('yes')

    conn.request("POST", "/face/v1.0/findsimilars?%s" % params, '{"faceId": "'+face_id+'","largeFaceListId": "facedetectionlist_new","maxNumOfCandidatesReturned": 50,"mode": "matchPerson"}', headers)
    response = conn.getresponse()
    #return HttpResponse(response)
    data = response.read()
    responseObject = json.loads(data.decode('utf-8'))
    #print(data)
    conn.close()
    return responseObject;

def DeleteFaceFromlist(face_id):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
    })

    conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')

    #return HttpResponse("/face/v1.0/largefacelists/facedetectionlist_new/persistedfaces/"+face_id+"?")

    conn.request("DELETE", "/face/v1.0/largefacelists/facedetectionlist_new/persistedfaces/"+face_id+"?%s" % params, '', headers)
    response = conn.getresponse()
    #return HttpResponse(response)
    data = response.read()
    #responseObject = json.loads(data)
    #print(data)
    conn.close()
    return data;

@csrf_exempt
def delete_customer(request):
    output = []
    if request.method == 'POST':
        form = CustomerDeleteForm(request.POST)
        if form.is_valid():
            userdata_id = request.POST['id']
            try:
                UserDetail = UserData.objects.get(pk=userdata_id,is_deleted='N')

                UserDetail.is_deleted = 'Y'  # change field
                UserDetail.save() # this will update only

                # if UserDetail.PersistedFaceId:
                #     data = DeleteFaceFromlist(UserDetail.PersistedFaceId)

                # os.unlink(UserDetail.image.path)
                # UserData.objects.filter(pk=userdata_id).delete()
                record = {"statusCode":200, "message":"Customer deleted successfully"}
                output.append(record)
            except UserData.DoesNotExist:
                record = {"statusCode":400, "message":'Customer id doesn\'t exists !'}
                return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output[0], safe=False)

@csrf_exempt
def agree_tc(request):
    output = []
    if request.method == 'POST':
        form = CompanyAgreeForm(request.POST)
        if form.is_valid():
            userdata_id = request.POST['userdata_id']
            company_id = request.POST['company_id']
            try:
                userComDetail = Useragree.objects.get(company_id=company_id,userdata_id=userdata_id)
                record = {"statusCode":400, "message":"Company terms & conditions agreed already!"}
                output.append(record)
            except Useragree.DoesNotExist:
                saved1 = form.save(commit=False)
                saved1.company_id = company_id
                saved1.userdata_id = userdata_id
                saved=saved1.save()

                record = {"statusCode":200, "message":'Company terms & conditions agreed successfully!!'}
                return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output[0], safe=False)

@csrf_exempt
def model_form_upload(request):
    output=[]
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():

            try:
                listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=request.POST['staff_code'])
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Incorrect Staff code !'}
                return JsonResponse(record, safe=False)

            face_detection = facedetect(request.FILES["image"])
            faces = face_detection.json()

            if not faces:
                record = {"statusCode":400, "message":'Image Not Correct !'}
                return JsonResponse(record, safe=False)

            if len(faces)>1:
                record = {"statusCode":400, "message":'Image Contains Multiple Faces !'}
                return JsonResponse(record, safe=False)

            for face in faces:
                if face=='error':
                    error_msg = json.dumps(faces['error']['message'])
                    record = {"statusCode":400, "message":error_msg}
                    output.append(record)
                else:
                    face_id = face['faceId']
                    check_face_list = getFaceList(request)

                    if len(check_face_list) == 0:
                        createFaceList(request)

                    TrainFaceList(request)
                    similars = (FindSimilarinFaceList(face_id))
                    for sm in similars:
                        if(sm['persistedFaceId']!='' and sm['confidence'] >= 0.50):
                            try:
                                userDetail = UserData.objects.get(PersistedFaceId=sm['persistedFaceId'],is_deleted='N')

                                try:
                                    LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userDetail.id).latest('id')
                                    pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                                except LoyaltyPoint.DoesNotExist:
                                    pre_loyalty_balance = 0

                                if userDetail.greeting_name is None:
                                    greeting_name =''
                                else:
                                    greeting_name = userDetail.greeting_name

                                if userDetail.phone_number is None:
                                    phone_number =''
                                else:
                                    phone_number = userDetail.phone_number

                                if userDetail.date_of_birth is None:
                                    date_of_birth =''
                                else:
                                    date_of_birth = userDetail.date_of_birth


                                userDetails = {"greeting_name":greeting_name,"phone_number":phone_number,"date_of_birth":date_of_birth,"PersistedFaceId":userDetail.PersistedFaceId,"FirstName":userDetail.FirstName,"LastName":userDetail.LastName,"Email":userDetail.Email,"image":request.build_absolute_uri(userDetail.image.url),"id":userDetail.id,"created_at":datetime.strptime(str(userDetail.created_at), '%Y-%m-%d').strftime('%d %b, %Y'),"old":"yes","loyalty_balance":pre_loyalty_balance}

                                UserData.objects.filter(staff_code=request.POST['staff_code']).update(is_active='N')
                                UserData.objects.filter(id=userDetail.id).update(staff_code=request.POST['staff_code'],updated_staffcode_at = datetime.now(),is_active='Y')

                                try:
                                    userDetails['is_agree'] = 'Y'
                                    userComDetail = Useragree.objects.get(company_id=request.POST['company_id'],userdata_id=userDetail.id)

                                    record = {"statusCode":200, "message":'similar face found !',"data":userDetails}
                                except:
                                    userDetails['is_agree'] = 'N'
                                    record = {"statusCode":200, "message":'similar face found !',"data":userDetails}

                            except UserData.DoesNotExist:
                                record = {"statusCode":200, "message":'similar face not found !'}

                            output.append(record)
                            return JsonResponse(record, safe=False)
                        else:
                            record = {"statusCode":200, "message":'similar face not found !'}
                            output.append(record)
                            return JsonResponse(record, safe=False)
                    record = {"statusCode":200, "message":'similar face not found !'}
                    output.append(record)
                    return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output[0], safe=False)

@csrf_exempt
def send_image(request):
    return render(request, 'core/model_form_upload.html')


@csrf_exempt
def save_user_data(request):
    output=[]
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():

            try:
                listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=request.POST['staff_code'])
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Incorrect Staff code !'}
                return JsonResponse(record, safe=False)

            saved1 = form.save(commit=False)
            saved1.branch_id = request.POST['branch_id']
            saved=saved1.save()

            data_saved = UserData.objects.latest('id')

            UserData.objects.filter(staff_code=request.POST['staff_code']).update(is_active='N')
            UserData.objects.filter(id=data_saved.id).update(staff_code=request.POST['staff_code'],updated_staffcode_at = datetime.now(),is_active='Y')

            added_face = addFacetoList(request.FILES["image"])
            added_face = added_face.json()
            for face in added_face:
                if face=='error':
                    UserData.objects.filter(id=data_saved.id).delete()
                    os.unlink(data_saved.image.path)
                    error_msg = json.dumps(added_face['error']['message'])
                    record = {"statusCode":400, "message":error_msg}
                    output.append(record)
                    return JsonResponse(record, safe=False)
                else:
                    if added_face['persistedFaceId']!='':
                        TrainFaceList(request)
                        t = UserData.objects.get(id=data_saved.id)
                        t.PersistedFaceId = added_face['persistedFaceId']
                        t.updated_staffcode_at = datetime.now()
                        t.save()

                        try:
                            LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = data_saved.id).latest('id')
                            pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                        except LoyaltyPoint.DoesNotExist:
                            pre_loyalty_balance = 0

                        if data_saved.greeting_name is None:
                            greeting_name =''
                        else:
                            greeting_name = data_saved.greeting_name

                        if data_saved.phone_number is None:
                            phone_number =''
                        else:
                            phone_number = data_saved.phone_number

                        if data_saved.date_of_birth is None:
                            date_of_birth =''
                        else:
                            date_of_birth = data_saved.date_of_birth

                        userDetails = {"greeting_name":greeting_name,"phone_number":phone_number,"date_of_birth":date_of_birth,"PersistedFaceId":added_face['persistedFaceId'],"FirstName":data_saved.FirstName,"LastName":data_saved.LastName,"Email":data_saved.Email,"image":request.build_absolute_uri(data_saved.image.url),"id":data_saved.id,"created_at":datetime.strptime(str(data_saved.created_at), '%Y-%m-%d').strftime('%d %b, %Y'),"old":"no","loyalty_points":pre_loyalty_balance}

                        BranchDetails = Branch.objects.get(pk = request.POST['branch_id'])
                        #print(BranchDetails)
                        try:
                            userComDetail = Useragree.objects.get(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
                        except Useragree.DoesNotExist:
                            save_user_agreement = Useragree(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
                            save_user_agreement.save()


                        record = {"statusCode":200, "message":'saved user data successfully!',"data":userDetails}
                        output.append(record)
                        return JsonResponse(record, safe=False)
            UserData.objects.filter(id=data_saved.id).delete()
            os.unlink(data_saved.image.path)
            record = {"statusCode":400, "message":'face could not be added !'}
            output.append(record)
            return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output[0], safe=False)

@csrf_exempt
def loyalty_benefits(request):
    output=[]
    if request.method == 'POST':
        form = LoyaltyBenefitListForm(request.POST)
        if form.is_valid():
            try:
                company_id = request.POST['company_id']
                loyalty_benefits_data = LoyaltyManager.objects.filter(company_id = company_id).order_by('-id')

                loyalty_benefits = []
                for loyalty_benefit in loyalty_benefits_data:
                    loyalty_benefit_record = {"loyalty_manager_id":loyalty_benefit.id,"loyalty_points":loyalty_benefit.loyalty_points,"benefit":loyalty_benefit.benefit}
                    loyalty_benefits.append(loyalty_benefit_record)

                record = {"statusCode":200, "message":'Loyalty Benefits !',"data":loyalty_benefits}
            except LoyaltyManager.DoesNotExist:
                record = {"statusCode":200, "message":'No Loyalty Benefits found !'}
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

@csrf_exempt
def active_customers(request):
    output=[]
    if request.method == 'POST':
        form = CustomerListForm(request.POST)
        if form.is_valid():
            try:
                branch_id = request.POST['branch_id']
                company_id = request.POST['company_id']
                staff_code = request.POST['staff_code']
                try:
                    selected_userdata_id = request.POST['userdata_id']
                except:
                    selected_userdata_id =0

                try:
                    listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=staff_code)
                except BranchStaffCode.DoesNotExist:
                    record = {"statusCode":400, "message":'Incorrect Staff code !'}
                    return JsonResponse(record, safe=False)

                current_customer = []
                # user_data = UserData.objects.get(staff_code=staff_code, is_deleted='N',is_active='Y')

                try:
                    user_data = UserData.objects.get(staff_code=staff_code, is_deleted='N',is_active='Y')
                    #return HttpResponse(user_data)
                    try:
                        user_agree = Useragree.objects.get(userdata_id =user_data.id, company_id=company_id)

                        pre_loyalty_balance = 0

                        try:
                            LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = user_data.id,company_id=company_id).latest('id')
                            pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                        except LoyaltyPoint.DoesNotExist:
                            pre_loyalty_balance = 0

                        if user_data.greeting_name is None:
                            greeting_name =''
                        else:
                            greeting_name = user_data.greeting_name

                        current_customer_record = {"userdata_id":user_data.id,"greeting_name":greeting_name,"FirstName":user_data.FirstName,"LastName":user_data.LastName,"Email":user_data.Email,"image":request.build_absolute_uri(user_data.image.url),"loyalty_points":pre_loyalty_balance}
                        current_customer.append(current_customer_record)
                    except Useragree.DoesNotExist:
                        current_customer = []
                except UserData.DoesNotExist:
                    current_customer = []

                # for user in user_data:
                #     if not current_customer:
                #         if not selected_userdata_id:
                #             pre_loyalty_balance = 0

                #             try:
                #                 LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = user.id,company_id=company_id).latest('id')
                #                 pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                #             except LoyaltyPoint.DoesNotExist:
                #                 pre_loyalty_balance = 0

                #             current_customer_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url),"loyalty_points":pre_loyalty_balance}
                #             current_customer.append(current_customer_record)
                #         else:
                #             UserDetail = UserData.objects.get(pk=selected_userdata_id)
                #             pre_loyalty_balance = 0

                #             try:
                #                 LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = selected_userdata_id,company_id=company_id).latest('id')
                #                 pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                #             except LoyaltyPoint.DoesNotExist:
                #                 pre_loyalty_balance = 0

                #             current_customer_record = {"userdata_id":UserDetail.id,"FirstName":UserDetail.FirstName,"LastName":UserDetail.LastName,"Email":UserDetail.Email,"image":request.build_absolute_uri(UserDetail.image.url),"loyalty_points":pre_loyalty_balance}
                #             current_customer.append(current_customer_record)
                #     else:
                #         user_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url)}
                #         previous_customers.append(user_record)

                if not current_customer:
                    loyalty_benefits = []
                else:
                    loyalty_benefits = []
                    for customer in current_customer:
                        already_redeemed = LoyaltyPoint.objects.filter(tx_type='REDEEM', userdata_id = customer['userdata_id'], created_at = datetime.now()).values('loyalty_manager_id').distinct()

                        current_customer_loyalty = customer['loyalty_points']
                        loyalty_benefits_data = LoyaltyManager.objects.filter(company_id = company_id, loyalty_points__lte = current_customer_loyalty).exclude(id__in=already_redeemed).order_by('-id')[:3]

                        for loyalty_benefit in loyalty_benefits_data:
                            loyalty_benefit_record = {"loyalty_manager_id":loyalty_benefit.id,"loyalty_points":loyalty_benefit.loyalty_points,"benefit":loyalty_benefit.benefit}
                            loyalty_benefits.append(loyalty_benefit_record)

                coupons = []
                if not current_customer:
                    coupons = []
                else:
                    for customer in current_customer:
                        used_coupons = Purchase.objects.filter(userdata_id = customer['userdata_id']).values('coupon_id')
                        #print([o['coupon_id'] for o in used_coupons])
                        exclude_ids = []
                        for o in used_coupons:
                            if o['coupon_id'] != None:
                                exclude_ids.append(o['coupon_id'])

                        #print(exclude_ids)

                        coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).exclude(id__in=exclude_ids).order_by('-id')[:4]
                        #print(customer['userdata_id'])
                        #print(company_id)
                        #coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).order_by('-id')[:4]

                        for coupon in coupon_data:
                            coun = UsersCoupon.objects.get(coupon_id=coupon.id,userdata_id=customer['userdata_id'])
                            coupon_record = {"id":coupon.id,"coupon":coupon.coupon_code,"description":coupon.description,"discount_type":coupon.discount_type,"amount":coupon.amount,"amount":coupon.amount,'minimum_spend':coupon.minimum_spend,'maximum_spend':coupon.maximum_spend,'expiry_date':coupon.expiry_date,"image":request.build_absolute_uri(format(coupon.image.url))}
                            coupons.append(coupon_record)

                record = {"statusCode":200, "message":'Cutomers list !',"data":{'current_customer':current_customer,'loyalty_benefits':loyalty_benefits,'coupons':coupons}}
            except UserData.DoesNotExist:
                record = {"statusCode":200, "message":'No customer found !'}
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}

    output.append(record)
    return JsonResponse(record, safe=False)

# @csrf_exempt
# def active_customers_old(request):
#     output=[]
#     if request.method == 'POST':
#         form = CustomerListForm(request.POST)
#         if form.is_valid():
#             try:
#                 branch_id = request.POST['branch_id']
#                 company_id = request.POST['company_id']
#                 staff_code = request.POST['staff_code']
#                 try:
#                     selected_userdata_id = request.POST['userdata_id']
#                 except:
#                     selected_userdata_id =0

#                 try:
#                     listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=staff_code)
#                 except BranchStaffCode.DoesNotExist:
#                     record = {"statusCode":400, "message":'Incorrect Staff code !'}
#                     return JsonResponse(record, safe=False)

#                 user_data = UserData.objects.filter(staff_code=staff_code, is_deleted='N').order_by('-updated_staffcode_at')[:settings.LIMIT_ACTIVE_CUSTOMERS]
#                 previous_customers = []
#                 current_customer = []
#                 for user in user_data:
#                     if not current_customer:
#                         if not selected_userdata_id:
#                             pre_loyalty_balance = 0

#                             try:
#                                 LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = user.id,company_id=company_id).latest('id')
#                                 pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
#                             except LoyaltyPoint.DoesNotExist:
#                                 pre_loyalty_balance = 0

#                             current_customer_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url),"loyalty_points":pre_loyalty_balance}
#                             current_customer.append(current_customer_record)
#                         else:
#                             UserDetail = UserData.objects.get(pk=selected_userdata_id)
#                             pre_loyalty_balance = 0

#                             try:
#                                 LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = selected_userdata_id,company_id=company_id).latest('id')
#                                 pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
#                             except LoyaltyPoint.DoesNotExist:
#                                 pre_loyalty_balance = 0

#                             current_customer_record = {"userdata_id":UserDetail.id,"FirstName":UserDetail.FirstName,"LastName":UserDetail.LastName,"Email":UserDetail.Email,"image":request.build_absolute_uri(UserDetail.image.url),"loyalty_points":pre_loyalty_balance}
#                             current_customer.append(current_customer_record)
#                     else:
#                         user_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url)}
#                         previous_customers.append(user_record)

#                 if not current_customer:
#                     loyalty_benefits = []
#                 else:
#                     loyalty_benefits = []
#                     for customer in current_customer:
#                         already_redeemed = LoyaltyPoint.objects.filter(tx_type='REDEEM', userdata_id = customer['userdata_id'], created_at = datetime.now()).values('loyalty_manager_id').distinct()

#                         current_customer_loyalty = customer['loyalty_points']
#                         loyalty_benefits_data = LoyaltyManager.objects.filter(company_id = company_id, loyalty_points__lte = current_customer_loyalty).exclude(id__in=already_redeemed).order_by('-id')[:3]

#                         for loyalty_benefit in loyalty_benefits_data:
#                             loyalty_benefit_record = {"loyalty_manager_id":loyalty_benefit.id,"loyalty_points":loyalty_benefit.loyalty_points,"benefit":loyalty_benefit.benefit}
#                             loyalty_benefits.append(loyalty_benefit_record)

#                 coupons = []
#                 if not current_customer:
#                     coupons = []
#                 else:
#                     for customer in current_customer:
#                         used_coupons = Purchase.objects.filter(userdata_id = customer['userdata_id']).values('coupon_id')
#                         #print(used_coupons)
#                         coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).exclude(id__in=used_coupons).order_by('-id')[:4]

#                         #coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).order_by('-id')[:4]

#                         for coupon in coupon_data:
#                             coun = UsersCoupon.objects.get(coupon_id=coupon.id,userdata_id=customer['userdata_id'])
#                             coupon_record = {"id":coupon.id,"coupon":coupon.coupon_code,"description":coupon.description,"discount_type":coupon.discount_type,"amount":coupon.amount,"amount":coupon.amount,'minimum_spend':coupon.minimum_spend,'maximum_spend':coupon.maximum_spend,'expiry_date':coupon.expiry_date,"image":request.build_absolute_uri(format(coupon.image.url))}
#                             coupons.append(coupon_record)

#                 record = {"statusCode":200, "message":'Cutomers list !',"data":{'current_customer':current_customer,'previous_customers':previous_customers,'loyalty_benefits':loyalty_benefits,'coupons':coupons}}
#             except UserData.DoesNotExist:
#                 record = {"statusCode":200, "message":'No customer found !'}
#         else:
#             errors = form.errors
#             errors3 =''
#             errors4 =''
#             for i in errors:
#                 errors2 = ','.join(errors[i])
#                 errors3 += errors4+i+': '+errors2
#                 errors4 =', '

#             record = {"statusCode":400, "message":errors3.replace(".","") }
#             output.append(record)
#     else:
#         record = {"statusCode":400, "message":'invalid request method'}

#     output.append(record)
#     return JsonResponse(record, safe=False)

@csrf_exempt
def manager_login(request):
    output=[]
    if request.method == 'POST':
        form = ManagerLoginForm(request.POST, request.FILES)
        if form.is_valid():
            user_type = request.POST['user_type'] # Customer / Staff
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    try:
                        login(request, user)
                        userDetail = User.objects.filter(groups__name=settings.STORE_MANAGER_GROUP,id=user.id).values()
                        if not userDetail:
                            record = {"statusCode":400, "message":'User is not a manager!'}
                        else:
                            try:
                                BranchDetails = Branch.objects.filter(is_deleted = 'N').get(user_id=user)
                                company_det = Company.objects.get(pk=BranchDetails.company_id)
                                if user_type == 'Staff':
                                    staff_code = get_random_string(length=8,allowed_chars='ABCDEFGHIJKLMNPQRSTUVWXYZ123456789')
                                    branch_staff_code = BranchStaffCode(branch=BranchDetails,staff_code=staff_code)
                                    branch_staff_code.save()

                                if user_type == 'Staff':
                                    record = {"statusCode":200, "message":'successfully login!', 'data' : {
                                        'first_name' : user.first_name,
                                        'last_name' : user.last_name,
                                        'email' : user.email,
                                        'username' : user.username,
                                        'branch_id' : BranchDetails.id,
                                        'company_id' : BranchDetails.company_id,
                                        'company_name' : company_det.name,
                                        'staff_code' : staff_code
                                    }}
                                else:
                                    record = {"statusCode":200, "message":'successfully login!', 'data' : {
                                        'first_name' : user.first_name,
                                        'last_name' : user.last_name,
                                        'email' : user.email,
                                        'username' : user.username,
                                        'branch_id' : BranchDetails.id,
                                        'company_name' : company_det.name,
                                        'company_id' : BranchDetails.company_id
                                    }}

                            except Branch.DoesNotExist:
                                record = {"statusCode":400, "message":"Manager not assigned to any branch !"}
                    except User.DoesNotExist:
                        record = {"statusCode":400, "message":'Invalid username or password!'}
                else:
                    record = {"statusCode":400, "message":'You\'re account is disabled.'}
            else:
	            record = {"statusCode":400, "message":'invalid login details'}
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

# @csrf_exempt
# def change_customer_status(request):
#     output=[]
#     if request.method == 'POST':
#         form = CustomerStatusForm(request.POST, request.FILES)
#         if form.is_valid():
#             id = request.POST['id']
#             is_active = request.POST['is_active']
#             try:
#                 UserData.objects.filter(id=id).update(is_active=is_active)
#                 record = {"statusCode":200, "message":'Customer status updated successfully!'}
#             except UserData.DoesNotExist:
#                 record = {"statusCode":400, "message":'Couldn\'t update status!'}
#         else:
#             errors = form.errors
#             record = {"statusCode":400, "message":"validation Errors","data":errors}
#     else:
#         record = {"statusCode":400, "message":'invalid request method'}

#     output.append(record)
#     return JsonResponse(record, safe=False)


@csrf_exempt
def check_customer_status(request):
    output=[]
    if request.method == 'POST':
        form = CustomerStatusForm(request.POST, request.FILES)
        if form.is_valid():
            id = request.POST['id']
            try:
                UserData.objects.filter(pk=id,is_active='Y').get()
                record = {"statusCode":200, "message":'Customer is active!', 'data' : {'is_active' : 'Y'}}
            except UserData.DoesNotExist:
                record = {"statusCode":200, "message":'Customer is inactive!', 'data' : {'is_active' : 'N'}}
        else:
            errors = form.errors
            record = {"statusCode":400, "message":"validation Errors","data":errors}
    else:
        record = {"statusCode":400, "message":'invalid request method'}

    output.append(record)
    return JsonResponse(record, safe=False)

@csrf_exempt
def purchase(request):
    output=[]
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            saved = form.save(commit=False)
            branch_id = request.POST['branch_id']
            userdata_id = request.POST['userdata_id']
            if 'coupon_id' in request.POST:
                coupon_id = request.POST['coupon_id']
                if coupon_id != '':
                    try:
                        c= UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
                        coupon = Coupon.objects.get(id=coupon_id)
                    except:
                        record = {"statusCode":400, "message":'not a valid coupon!'}
                        output.append(record)
                        return JsonResponse(record, safe=False)
                    saved.coupon_code = coupon.coupon_code
                    saved.discount_amount = coupon.amount
                    saved.discount_type = coupon.discount_type
                    saved.coupon = coupon
            try:
                branch = Branch.objects.filter(is_deleted = 'N').get(id=branch_id)
                userdata = UserData.objects.get(id=userdata_id)
            except:
                record = {"statusCode":400, "message":'Branch or user has been deleted by admin!'}
                output.append(record)
                return JsonResponse(record, safe=False)

            saved.branch = branch
            saved.userdata = userdata
            saved.save()

            purchase_saved = Purchase.objects.latest('id')

            pre_loyalty_balance = 0

            setting = Setting.objects.latest('id')
            if setting.loyalty_on == 1:
                try:
                    LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userdata_id,company_id=branch.company_id).latest('id')
                    pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                except LoyaltyPoint.DoesNotExist:
                    pre_loyalty_balance = 0

                company = Company.objects.get(id=branch.company_id)
                loyalty_instance = LoyaltyPoint(tx_type='PURCHASE',userdata=userdata, purchase=purchase_saved,loyalty_points=math.floor(float(request.POST['amount'])),loyalty_balance=pre_loyalty_balance+math.floor(float(request.POST['amount'])),company=company)
                loyalty_instance.save()

            company = Company.objects.get(id=branch.company_id)
            try:
                templates = CompanyEmailTemplate.objects.filter(template_type='purchase',company=company).latest('id')
                html_content = templates.body
                from_email   = settings.DEFAULT_FROM_EMAIL
                message      = EmailMessage(str(templates.subject), html_content, from_email, [userdata.Email])
                message.content_subtype = "html"
                message.send()
            except CompanyEmailTemplate.DoesNotExist:
                message =''

            # Make user inactive after purchase
            UserData.objects.filter(pk=userdata_id).update(is_active='N')

            record = {"statusCode":200, "message":"Purchase data added successfully"}
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

@csrf_exempt
def redeem(request):
    output=[]
    if request.method == 'POST':
        form = RedeemForm(request.POST)
        if form.is_valid():
            branch_id = request.POST['branch_id']
            userdata_id = request.POST['userdata_id']
            loyalty_manager_id = request.POST['loyalty_manager_id']

            req_loyalty_points = 0
            req_loyalty_value = 0
            try:
                LoyaltyManagerDetail = LoyaltyManager.objects.get(pk=loyalty_manager_id)
                req_loyalty_points = LoyaltyManagerDetail.loyalty_points
                req_loyalty_value = LoyaltyManagerDetail.loyalty_value
            except LoyaltyManager.DoesNotExist:
                record = {"statusCode":400, "message":'Loyalty benefit doesn\'t exists' }
                output.append(record)
                return JsonResponse(record, safe=False)

            pre_loyalty_balance = 0

            try:
                branch = Branch.objects.filter(is_deleted = 'N').get(id=branch_id)
                company = Company.objects.get(id = branch.company_id)
            except:
                record = {"statusCode":400, "message":'Branch or user has been deleted by admin!'}
                output.append(record)
                return JsonResponse(record, safe=False)

            # return HttpResponse(company)
            try:
                LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userdata_id,company_id=branch.company_id).latest('id')
                pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                pre_loyalty_value = LoyaltyPointDetail.tot_loyalty_value
            except LoyaltyPoint.DoesNotExist:
                pre_loyalty_balance = 0
                pre_loyalty_value = 0

            if pre_loyalty_balance >= req_loyalty_points:

                userdata = UserData.objects.get(id=userdata_id)

                loyalty_instance = LoyaltyPoint(loyalty_manager=LoyaltyManagerDetail, tx_type='REDEEM',userdata=userdata, purchase_id=None,loyalty_points=int(req_loyalty_points),loyalty_balance=pre_loyalty_balance-int(req_loyalty_points),loyalty_value=int(req_loyalty_value),tot_loyalty_value=pre_loyalty_value+int(req_loyalty_value),company=company)
                loyalty_instance.save()

                record = {"statusCode":200, "message":"Loyalty Points redeemed successfully"}
            else:
                record = {"statusCode":400, "message":"Customer doesn\'t have enough loyalty points."}
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

# @csrf_exempt
# def apply_coupon(request):
#     output=[]
#     if request.method == 'POST':
#         form = CouponForm(request.POST)
#         if form.is_valid():
#             coupon_id = request.POST['coupon_id']
#             userdata_id = request.POST['userdata_id']
#             try:
#                 c= UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)

#             except UsersCoupon.DoesNotExist:
#                 record = {"statusCode":400, "message":'Coupon is not valid!' }
#                 output.append(record)
#                 return JsonResponse(record, safe=False)

#             c.is_redeemed = 'Y'
#             c.save()
#             record = {"statusCode":200, "message":"Coupon applied successfully!"}
#         else:
#             errors = form.errors
#             record = {"statusCode":400, "message":"validation Errors","data":errors}
#     else:
#         record = {"statusCode":400, "message":'invalid request method'}
#     output.append(record)
#     return JsonResponse(record, safe=False)

@csrf_exempt
def validate_staff_code(request):
    output=[]
    if request.method == 'POST':
        form = CheckStaffCodeForm(request.POST)
        if form.is_valid():
            staff_code = request.POST['staff_code']
            try:
                listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=staff_code)
                record = {"statusCode":200, "message":'Staff code is valid !'}
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Invalid Staff code !'}
                return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

@csrf_exempt
def company_logo(request):
    output=[]
    if request.method == 'POST':
        form = CompanyLogoForm(request.POST)
        if form.is_valid():
            id = request.POST['id']
            try:
                company = Company.objects.get(pk=id)
                company_record = {"logo":request.build_absolute_uri(format(company.logo.url))}
                record = {"statusCode":200, "message":'Company Logo !',"data":company_record}
            except Company.DoesNotExist:
                record = {"statusCode":400, "message":'Invalid Company ID !'}
                return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            errors3 =''
            errors4 =''
            for i in errors:
                errors2 = ','.join(errors[i])
                errors3 += errors4+i+': '+errors2
                errors4 =', '

            record = {"statusCode":400, "message":errors3.replace(".","") }
            output.append(record)
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False

    return user_passes_test(in_groups, login_url='/admin/login')


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

    ql_list = [Q(userdata__branch=branch.id),Q(tx_type='REDEEM'), ]
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

    ql_list = [Q(userdata__branch__company=company.id),Q(tx_type='REDEEM'), ]
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
        ql_list.append(Q(userdata__branch__company=selected_company),)

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
        if default_storage.exists(profile.image.path):
            image = mark_safe('<img src="{}" width="100" height="100" />'.format(profile.image.url))
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
                ql_list.append(Q(userdata__branch=branch),)

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

@staff_member_required
def my_model_export_purchase(request): #show list of all objects.

    from_date_search = ''
    to_date_search = ''
    branch = request.GET.get('branch')
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

    date_text = 'All Dates'

    if from_date is None and from_date == str(0) and to_date !=None:
        from_date =''

    if from_date != '' and from_date != str(0) and to_date !=None:
        from_date_search = datetime.strptime(from_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    to_date = request.GET.get('to_date')
    if to_date is None and to_date == str(0):
        to_date =''
    #return HttpResponse(to_date)
    if to_date != '' and to_date != str(0) and to_date !=None:
        to_date_search = datetime.strptime(to_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    if (from_date == '' and to_date == '') or (from_date == str(0) and to_date == str(0)) and to_date !=None:
        date_text = 'All Dates'
    else:
        if (from_date == '' or from_date == str(0)) and ( to_date != '' and to_date != str(0)) and to_date !=None:
            date_text = 'To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        if (to_date == '' or to_date == str(0)) and ( from_date != '' and from_date != str(0)) and to_date !=None:
            date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        if (from_date != '' and to_date != '' and from_date != str(0) and to_date != str(0)  and to_date !=None):
            date_text = 'From '+datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')+' To '+datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

    ql_list = [Q(id__gte=0),]

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
        ['', '', '', 'Branch : '+branch_txt,'','',''],
        ['', '', '', 'Date : '+date_text,'','',''],
        ['Customer', 'Company', 'Branch', 'Amount', 'Purchase Summary','Coupon','Created at'],
    ]
    #return JsonResponse(purchases)
    if purchases is not None :
        for pur in purchases:

            if pur.coupon is not None :
                purcoupon = pur.coupon
            else:
                purcoupon = ''
            context = [pur.userdata, pur.branch.company, pur.branch,str(pur.amount),pur.purchase_summary,purcoupon,datetime.strptime(str(pur.created_at), '%Y-%m-%d').strftime('%d/%m/%Y')]
            csv_data.append(context)
    #return HttpResponse(csv_data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EYE_D_Purchases_'+datetime.today().strftime('%d-%m-%Y')+'.csv"'
    t = loader.get_template('my_template_name.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response

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
    ql_list.append(Q(userdata__branch=branch),)

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
