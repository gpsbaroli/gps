from django.shortcuts import render
import requests
from django.contrib import auth
from django.template import Context,loader
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from face_detection.models import UserData,Branch,LoyaltyPoint,Purchase,LoyaltyManager,BranchStaffCode,Coupon,UsersCoupon,Setting,Company,CompanyEmailTemplate,UserProfile,Useragree,CompanySettings,EmailTemplate,UsersSelectedCoupon, Allergy, CustomerAllergy
from django.contrib.auth.models import User
from face_detection.forms import ImageForm,UserForm,ManagerLoginForm,CustomerStatusForm,PurchaseForm,RedeemForm,CustomerListForm,LoyaltyBenefitListForm,CheckStaffCodeForm,CouponForm,CustomerDeleteForm,updateNetworkAdminProfile,CompanyLogoForm,updateCompanyProfile,CompanyAgreeForm,updateCompany,AllDeleteForm,InvisibleForm,EmailLoginForm,CompanyRegisteredAgreeForm
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
from django.contrib.auth.hashers import check_password

#Set invisible
@csrf_exempt
def set_visible(request):
    output = []
    if request.method == 'POST':
        form = InvisibleForm(request.POST)
        if form.is_valid():
            company_id = request.POST['company_id']
            userdata_id = request.POST['userdata_id']

            try:
                review_company = Useragree.objects.filter(company_id = company_id, userdata_id = userdata_id).get()
                review_company.is_visible = 'Y'
                review_company.save()

                record = {"statusCode":200, "message":"You have set customer account as visible successfully!"}
                output.append(record)

            except:
                record = {"statusCode":400, "message":"Couldn't make customer visible, Please try again!"}
                output.append(record)
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
            userdata_id = request.POST['userdata_id']
            company_id = request.POST['company_id']

            try:
                all_company_coupons = Coupon.objects.filter(company_id = company_id).values('id')
                if all_company_coupons is not None :
                    for x in all_company_coupons:
                        #print(x['id'])
                        UsersCoupon.objects.filter(coupon_id=x['id'],userdata_id=userdata_id).delete()
                #UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
            except:
                pass


            try:
                User_agree = Useragree.objects.filter(userdata_id=userdata_id,company_id=company_id).delete()

                UserDetail = UserData.objects.get(pk=userdata_id)
                company = Company.objects.get(pk=company_id)

                first_name = UserDetail.FirstName
                last_name = UserDetail.LastName
                greeting_name = UserDetail.greeting_name
                email = UserDetail.Email
                if greeting_name is None:
                    name = first_name+' '+last_name
                else:
                    name = greeting_name

                templates = EmailTemplate.objects.get(pk=4)
                html_content = templates.body
                from_email   = settings.DEFAULT_FROM_EMAIL
                html_content = html_content.replace("{greeting_name}",name)
                html_content = html_content.replace("{retailer}",company.name)
                message      = EmailMessage(str(templates.subject), html_content, from_email, [email])
                message.content_subtype = "html"
                message.send()
                #added in 24/10/2018 for update company brach using company id and userdata id
                branches = Branch.objects.filter(company_id = company_id).values('id','company_id')
                for branch in branches:
                    purchases = Purchase.objects.filter(branch_id = branch['id'], userdata_id = userdata_id)
                    if purchases:
                        for purchase in purchases:
                            Purchase.objects.filter(id=purchase.id).update(userdata_id=getattr(settings, "ANNOTATE_USER_ID", None) , removed_from=purchase.userdata_id)
                #end

                record = {"statusCode":200, "message":"Customer deleted successfully"}
                output.append(record)
            except Useragree.DoesNotExist:
                record = {"statusCode":400, "message":'record doesn\'t exists !'}
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

# @csrf_exempt
# def delete_all_customer(request):
#     output = []
#     if request.method == 'POST':
#         form = AllDeleteForm(request.POST)
#         if form.is_valid():
#             userdata_id = request.POST['userdata_id']
#             try:
#                 all_agreed = Useragree.objects.filter(userdata_id=userdata_id).all()
#                 if all_agreed:
#                     for agree in all_agreed:
#                         try:
#                             User_agree = Useragree.objects.filter(userdata_id=userdata_id,company_id=agree.company_id).delete()

#                             UserDetail = UserData.objects.get(pk=userdata_id)
#                             company = Company.objects.get(pk=agree.company_id)

#                             first_name = UserDetail.FirstName
#                             last_name = UserDetail.LastName
#                             greeting_name = UserDetail.greeting_name
#                             email = UserDetail.Email

#                             # if UserDetail.PersistedFaceId:
#                             #     data = DeleteFaceFromlist(UserDetail.PersistedFaceId)

#                             # os.unlink(UserDetail.image.path)
#                             # UserData.objects.filter(pk=userdata_id).delete()

#                             if greeting_name is None:
#                                 name = first_name+' '+last_name
#                             else:
#                                 name = greeting_name



#                             templates = EmailTemplate.objects.get(pk=4)
#                             html_content = templates.body
#                             from_email   = settings.DEFAULT_FROM_EMAIL
#                             html_content = html_content.replace("{greeting_name}",name)
#                             html_content = html_content.replace("{retailer}",company.name)
#                             message      = EmailMessage(str(templates.subject), html_content, from_email, [email])
#                             message.content_subtype = "html"
#                             message.send()

#                             record = {"statusCode":200, "message":"Customer deleted successfully"}
#                             output.append(record)
#                         except Useragree.DoesNotExist:
#                             record = {"statusCode":400, "message":'record doesn\'t exists !'}
#                             return JsonResponse(record, safe=False)
#                 else:
#                     record = {"statusCode":400, "message":'you are not registered to any company yet !'}
#                     return JsonResponse(record, safe=False)
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
#         record = {"statusCode":400, "message":"Not a valid request method !"}
#         output.append(record)

#     return JsonResponse(output[0], safe=False)

@csrf_exempt
def agree_tc1(request):
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

                UserDetail = UserData.objects.get(pk=userdata_id)
                CompanyDetail = Company.objects.get(pk=company_id)

                first_name = UserDetail.FirstName
                last_name = UserDetail.LastName
                greeting_name = UserDetail.greeting_name

                templates = EmailTemplate.objects.get(pk=5)
                html_content = templates.body
                from_email   = settings.DEFAULT_FROM_EMAIL

                if greeting_name is None:
                    name = first_name+' '+last_name
                else:
                    name = greeting_name

                html_content = html_content.replace("{greeting_name}",name)
                html_content = html_content.replace("{retailer}",CompanyDetail.name)

                message      = EmailMessage(str(templates.subject), html_content, from_email, [UserDetail.Email])
                message.content_subtype = "html"
                message.send()

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
def agree_tc(request):
    output = []
    if request.method == 'POST':
        form = CompanyAgreeForm(request.POST)
        if form.is_valid():
            userdata_id = request.POST['userdata_id']
            company_id = request.POST['company_id']

            try:
                coupon_id = request.POST['coupon_id']
            except KeyError:
                coupon_id = ""


            useragreedata = []
            userCoupons= []
            try:
                userComDetail = Useragree.objects.get(company_id=company_id,userdata_id=userdata_id)
                usercomarr = {"statusCode":400, "message":"Company terms & conditions agreed already!"}
                useragreedata.append(usercomarr)


                if coupon_id !="":

                    try:
                        usercoupon = UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
                        usersCoupanDetail = {"statusCode":400, "message":"This Coupon is assigned already to this user!"}
                        userCoupons.append(usersCoupanDetail)
                    except UsersCoupon.DoesNotExist:
                        users_coupon = UsersCoupon(userdata_id = userdata_id, coupon_id = coupon_id)
                        users_coupon.save()
                        usersCoupanDetail = {"statusCode":200, "message":"UsersCoupon selected successfully !"}
                        userCoupons.append(usersCoupanDetail)

            except Useragree.DoesNotExist:
                saved1 = form.save(commit=False)
                saved1.company_id = company_id
                saved1.userdata_id = userdata_id
                saved=saved1.save()

                UserDetail = UserData.objects.get(pk=userdata_id)
                CompanyDetail = Company.objects.get(pk=company_id)

                first_name = UserDetail.FirstName
                last_name = UserDetail.LastName
                greeting_name = UserDetail.greeting_name

                templates = EmailTemplate.objects.get(pk=5)
                html_content = templates.body
                from_email   = settings.DEFAULT_FROM_EMAIL

                if greeting_name is None:
                    name = first_name+' '+last_name
                else:
                    name = greeting_name

                html_content = html_content.replace("{greeting_name}",name)
                html_content = html_content.replace("{retailer}",CompanyDetail.name)

                message      = EmailMessage(str(templates.subject), html_content, from_email, [UserDetail.Email])
                message.content_subtype = "html"
                message.send()
                useragreedata = {"statusCode":200, "message":'Company terms & conditions agreed successfully!!'}

                if coupon_id !="":
                    try:
                        usercoupon = UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
                        usersCoupanDetail = {"statusCode":400, "message":"This Coupon is assigned already to this user!"}
                        userCoupons.append(usersCoupanDetail)
                    except UsersCoupon.DoesNotExist:
                        users_coupon = UsersCoupon(userdata_id = userdata_id, coupon_id = coupon_id)
                        users_coupon.save()
                        usersCoupanDetail = {"statusCode":200, "message":"UsersCoupon selected successfully !"}
                        userCoupons.append(usersCoupanDetail)

            required_data = {"userCoupons":userCoupons,"useragreedata":useragreedata}
            record = {"statusCode":200, "message":'Company terms & conditions agreed successfully!!',"data":required_data}
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

        try:
            company_det = Company.objects.get(id=request.POST['company_id'],status='s')
            if company_det.status:
                site_settings = Setting.objects.get(id = 1)
                record = {"statusCode":500, "message":'Your company account has been suspended.  Please contact '+site_settings.phone_number+' for help'}
                return JsonResponse(record, safe=False)
        except:
            pass

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
                                    LoyaltyPointDetail = LoyaltyPoint.objects.filter(company_id=request.POST['company_id'],userdata_id = userDetail.id).latest('id')
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

                                #UserData.objects.filter(staff_code=request.POST['staff_code']).update(is_active='N')
                                UserData.objects.filter(id=userDetail.id).update(staff_code=request.POST['staff_code'],updated_staffcode_at = datetime.now(),is_active='Y')



                                try:
                                    userDetails['is_visible'] = 'Y'
                                    userComDetail = Useragree.objects.get(company_id=request.POST['company_id'],userdata_id=userDetail.id,is_visible='Y')
                                except:
                                    userDetails['is_visible'] = 'N'

                                try:
                                    userDetails['is_agree'] = 'Y'
                                    userComDetail = Useragree.objects.get(company_id=request.POST['company_id'],userdata_id=userDetail.id)
                                except:
                                    userDetails['is_agree'] = 'N'
                                    userDetails['is_visible'] = 'N'


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

# @csrf_exempt
# def send_image(request):
#     return render(request, 'core/model_form_upload.html')

@csrf_exempt
def save_user_data(request):
    output=[]
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            BranchDetails = Branch.objects.get(pk = request.POST['branch_id'])
            try:
                listing = BranchStaffCode.objects.filter(branch__is_deleted = 'N').get(staff_code=request.POST['staff_code'])
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Incorrect Staff code !'}
                return JsonResponse(record, safe=False)

            saved1 = form.save(commit=False)
            #saved1.branch_id = request.POST['branch_id']
            saved=saved1.save()

            data_saved = UserData.objects.latest('id')

            #UserData.objects.filter(staff_code=request.POST['staff_code']).update(is_active='N')
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
                            LoyaltyPointDetail = LoyaltyPoint.objects.filter(company_id=BranchDetails.company_id,userdata_id = data_saved.id).latest('id')
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


                        #print(BranchDetails)
                        try:
                            userComDetail = Useragree.objects.get(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
                        except Useragree.DoesNotExist:
                            save_user_agreement = Useragree(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
                            save_user_agreement.save()

                        #UserDetail = UserData.objects.get(pk=data_saved.id)
                        CompanyDetail = Company.objects.get(pk=BranchDetails.company_id)

                        first_name = data_saved.FirstName
                        last_name = data_saved.LastName
                        greeting_name = data_saved.greeting_name

                        templates = EmailTemplate.objects.get(pk=5)
                        html_content = templates.body
                        from_email   = settings.DEFAULT_FROM_EMAIL

                        if greeting_name is None:
                            name = first_name+' '+last_name
                        else:
                            name = greeting_name

                        html_content = html_content.replace("{greeting_name}",name)
                        html_content = html_content.replace("{retailer}",CompanyDetail.name)

                        message      = EmailMessage(str(templates.subject), html_content, from_email, [data_saved.Email])
                        message.content_subtype = "html"
                        message.send()

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
                    company_det = Company.objects.get(id=company_id,status='a')

                except Company.DoesNotExist:
                    site_settings = Setting.objects.get(id = 1)
                    record = {"statusCode":500, "message":'Your company account has been suspended.  Please contact '+site_settings.phone_number+' for help'}
                    return JsonResponse(record, safe=False)

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

                if selected_userdata_id == 0:
                    try:
                        user_data1 = UserData.objects.filter(staff_code=staff_code, is_deleted='N',is_active='Y').order_by('updated_staffcode_at').all()

                        try:
                            if user_data1:
                                user_data = user_data1[0]
                                user_agree = Useragree.objects.get(userdata_id =user_data.id, company_id=company_id)

                                pre_loyalty_balance = 0

                                try:
									#Allergy = Allergies.objects.all().select_related("customerallergy").values('allergy_id')
                        			#Allergy = Allergies.objects.all().select_related("CustomerAllergy__id__allergy_id").values('allergy_id')
                                    Allergy = Allergy.objects.filter(customerallergy__customer_id=user_data.id).all()
                                except Allergy.DoesNotExist:
                                    Allergy = []

                                allerg = []

                                if len(Allergy) > 0:
                                    for allergyitem in Allergy:
                                        Allergy_record = {"id":allergyitem.id,"name":allergyitem.name}
                                        allerg.append(Allergy_record)


                                try:
                                    LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = user_data.id,company_id=company_id).latest('id')
                                    pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                                except LoyaltyPoint.DoesNotExist:
                                    pre_loyalty_balance = 0

                                if user_data.greeting_name is None:
                                    greeting_name =''
                                else:
                                    greeting_name = user_data.greeting_name

                                current_customer_record = {"userdata_id":user_data.id,"greeting_name":greeting_name,"FirstName":user_data.FirstName,"LastName":user_data.LastName,"Email":user_data.Email,"image":request.build_absolute_uri(user_data.image.url),"loyalty_points":pre_loyalty_balance, "allergy":allerg}
                                current_customer.append(current_customer_record)
                            else:
                                current_customer = []
                        except Useragree.DoesNotExist:
                            current_customer = []
                    except UserData.DoesNotExist:
                        current_customer = []
                else:
                    try:
                        user_data = UserData.objects.get(id =selected_userdata_id,staff_code=staff_code, is_deleted='N',is_active='Y')
                        #return HttpResponse(user_data)
                        try:
                            user_agree = Useragree.objects.get(userdata_id =user_data.id, company_id=company_id)

                            pre_loyalty_balance = 0

                            try:
                                Allergy = Allergy.objects.filter(customerallergy__customer_id=user_data.id).all()
                            except Allergy.DoesNotExist:
                                Allergy = []

                            allerg = []

                            if len(Allergy) > 0:
                                for allergyitem in Allergy:
                                    Allergy_record = {"id":allergyitem.id,"name":allergyitem.name}
                                    allerg.append(Allergy_record)


                            if user_data.greeting_name is None:
                                greeting_name =''
                            else:
                                greeting_name = user_data.greeting_name

                            current_customer_record = {"userdata_id":user_data.id,"greeting_name":greeting_name,"FirstName":user_data.FirstName,"LastName":user_data.LastName,"Email":user_data.Email,"image":request.build_absolute_uri(user_data.image.url),"loyalty_points":pre_loyalty_balance, "allergy":allerg}
                            current_customer.append(current_customer_record)
                        except Useragree.DoesNotExist:
                            current_customer = []
                    except UserData.DoesNotExist:
                        current_customer = []



                if not current_customer:
                    prev_user_data = UserData.objects.filter(staff_code=staff_code, is_deleted='N',is_active='Y').all()
                else:
                    prev_user_data = UserData.objects.filter( staff_code=staff_code, is_deleted='N',is_active='Y').exclude(id=current_customer[0]['userdata_id']).all()

                previous_customers = []
                if prev_user_data:
                    for user in prev_user_data:
                        user_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url)}
                        previous_customers.append(user_record)

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
                        selected_coupons = UsersSelectedCoupon.objects.filter(userdata_id = customer['userdata_id']).values('coupon_id')
                        include_ids = []
                        for o2 in selected_coupons:
                            if o2['coupon_id'] != None:
                                include_ids.append(o2['coupon_id'])

                        coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).exclude(id__in=exclude_ids).order_by('-id')[:4]
                        #print(customer['userdata_id'])
                        #print(company_id)
                        #coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).order_by('-id')[:4]

                        for coupon in coupon_data:
                            coun = UsersCoupon.objects.get(coupon_id=coupon.id,userdata_id=customer['userdata_id'])

                            is_selected = 'N'

                            if coupon.id in include_ids:
                                is_selected = 'Y'

                            coupon_record = {"id":coupon.id,"is_selected":is_selected,"coupon":coupon.coupon_code,"description":coupon.description,"discount_type":coupon.discount_type,"amount":coupon.amount,"amount":coupon.amount,'minimum_spend':coupon.minimum_spend if coupon.minimum_spend else '','maximum_spend':coupon.maximum_spend if coupon.maximum_spend else '','expiry_date':coupon.expiry_date,"image":request.build_absolute_uri(format(coupon.image.url))}
                            coupons.append(coupon_record)

                record = {"statusCode":200, "message":'Cutomers list !',"data":{'current_customer':current_customer,'loyalty_benefits':loyalty_benefits,'coupons':coupons,'previous_customers':previous_customers}}
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

            try:
                company_det = Company.objects.get(branch__user_id=user.id,status='s')
                if company_det.status:
                    site_settings = Setting.objects.get(id = 1)
                    record = {"statusCode":500, "message":'Your company account has been suspended.  Please contact '+site_settings.phone_number+' for help'}
                    return JsonResponse(record, safe=False)
            except:
                pass

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
                    record = {"statusCode":400, "message":'Your account is disabled.'}
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
            is_loyalty_on = 0

            try:
                company_settings = CompanySettings.objects.get(company_id = branch.company_id)
                if company_settings.loyalty_on == 1:
                    is_loyalty_on = 1
                else:
                    pass
            except:
                pass

            if is_loyalty_on == 1:
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

                loyalty_instance = LoyaltyPoint(branch_id =branch_id , loyalty_manager=LoyaltyManagerDetail, tx_type='REDEEM',userdata=userdata, purchase_id=None,loyalty_points=int(req_loyalty_points),loyalty_balance=pre_loyalty_balance-int(req_loyalty_points),loyalty_value=int(req_loyalty_value),tot_loyalty_value=pre_loyalty_value+int(req_loyalty_value),company=company)
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

	# On coupon select, if coupon is registered call below function
@csrf_exempt
def coupon_is_registered(request):
    output=[]
    if request.method == 'POST':
        form = CompanyRegisteredAgreeForm(request.POST)
        if form.is_valid():
            coupon_id = request.POST['coupon_id']
            userdata_id = request.POST['userdata_id']
            userCoupons=[]
            if coupon_id !="":
                try:
                    usercoupon = UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
                    usersCoupanDetail = {"statusCode":400, "message":"This Coupon is assigned already to this user!"}
                    userCoupons.append(usersCoupanDetail)
                except UsersCoupon.DoesNotExist:
                    users_coupon = UsersCoupon(userdata_id = userdata_id, coupon_id = coupon_id)
                    users_coupon.save()
                    usersCoupanDetail = {"statusCode":200, "message":"UsersCoupon selected successfully !"}
                    userCoupons.append(usersCoupanDetail)

                record = {"statusCode":200, "message":'Coupon registration detail!!',"data":userCoupons}
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
def email_login(request):
    output=[]
    if request.method == 'POST':
        form = EmailLoginForm(request.POST, request.FILES)
        if form.is_valid():
            Email = request.POST['Email']
            userpass = request.POST['password']
            try:
                '''user_list = User.objects.all()
                userdata = UserFilter(Email=Email, queryset=user_list)'''
                #userdata = UserData.objects.filter(Email=Email).values_list( * UserData.objects.get_all_field_names(), flat=True)
                userdata = UserData.objects.get(Email=Email)
                #print(userdata.is_active)
                #print(userpass)
                # and userdata.user_pass==userpass

                if userdata is not None:

                        if (userdata.is_active == 'Y' and userdata.user_pass==userpass):
                            try:
                                #login(request, userdata)
                                userdataDetail = UserData.objects.filter(Email=Email,id=userdata.id).values()
                                #print(userdataDetail)
                                #return HttpResponse(userdataDetail)
                                if not userdataDetail:
                                    record = {"statusCode":400, "message":'User is not available!'}
                                else:
                                    userfirstname = ''
                                    userlastname = ''
                                    useremail = ''
                                    userisactive = ''
                                    usergreeting = ''
                                    userphonenumber = ''
                                    userdob = ''
                                    usercreated = ''
                                    if(userdata.FirstName!='' and userdata.FirstName):
                                        userfirstname = userdata.FirstName
                                    if(userdata.LastName!='' and userdata.LastName):
                                        userlastname = userdata.LastName
                                    if(userdata.Email!='' and userdata.Email):
                                        useremail = userdata.Email
                                    if(userdata.is_active!='' and userdata.is_active):
                                        userisactive = userdata.is_active
                                    if(userdata.greeting_name!='' and userdata.greeting_name):
                                        usergreeting = userdata.greeting_name
                                    if(userdata.date_of_birth!='' and userdata.date_of_birth):
                                        userdob = userdata.date_of_birth
                                    if(userdata.created_at!='' and userdata.created_at):
                                        usercreated = userdata.created_at

                                    record = {"statusCode":200, "message":'successfully login!', 'data' : {
                                        'FirstName' : userfirstname,
                                        'LastName' : userlastname,
                                        'Email' : useremail,
                                        'is_active' : userisactive,
                                        'greeting_name' : usergreeting,
                                        'phone_number' : userphonenumber,
                                        'date_of_birth' : userdob,
                                        'created_at' : usercreated,
                                        'id' : userdata.id,
                                    }}
                            except UserData.DoesNotExist:
                                record = {"statusCode":400, "message":'Invalid email or password!'}
                        else:
                            record = {"statusCode":400, "message":'Your account is disabled1.'}
                else:
                    record = {"statusCode":400, "message":'Invalid login details'}

            except UserData.DoesNotExist:
                record = {"statusCode":400, "message":'invalid user details'}
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

# On coupon select, if coupon is registered call below function
@csrf_exempt
def coupon_is_registered(request):
    output=[]
    if request.method == 'POST':
        form = CompanyRegisteredAgreeForm(request.POST)
        if form.is_valid():
            coupon_id = request.POST['coupon_id']
            userdata_id = request.POST['userdata_id']
            userCoupons=[]
            if coupon_id !="":
                try:
                    usercoupon = UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
                    usersCoupanDetail = {"statusCode":400, "message":"This Coupon is assigned already to this user!"}
                    userCoupons.append(usersCoupanDetail)
                except UsersCoupon.DoesNotExist:
                    users_coupon = UsersCoupon(userdata_id = userdata_id, coupon_id = coupon_id)
                    users_coupon.save()
                    usersCoupanDetail = {"statusCode":200, "message":"UsersCoupon selected successfully !"}
                    userCoupons.append(usersCoupanDetail)

                record = {"statusCode":200, "message":'Coupon registration detail!!',"data":userCoupons}
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
