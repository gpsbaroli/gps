from django.shortcuts import render
import requests
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from .models import UserData,Branch,LoyaltyPoint,Purchase,LoyaltyManager,BranchStaffCode,Coupon,UsersCoupon,Setting,Company
from django.contrib.auth.models import User
from .forms import ImageForm,UserForm,ManagerLoginForm,CustomerStatusForm,PurchaseForm,RedeemForm,CustomerListForm,LoyaltyBenefitListForm,CheckStaffCodeForm,CouponForm,CustomerDeleteForm
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core import serializers
import json
import os
from django.contrib.auth import authenticate, login, logout
from django.utils.crypto import get_random_string
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import loader
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
            record = {"statusCode":400, "message":"validation error","data":errors}
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
                listing = BranchStaffCode.objects.get(staff_code=request.POST['staff_code'])
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
                    #return HttpResponse(similars)
                    for sm in similars:
                        if(sm['persistedFaceId']!='' and sm['confidence'] >= 0.50):
                            try:
                                userDetail = UserData.objects.get(PersistedFaceId=sm['persistedFaceId'],is_deleted='N')

                                try:
                                    LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userDetail.id).latest('id')
                                    pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                                except LoyaltyPoint.DoesNotExist:
                                    pre_loyalty_balance = 0

                                userDetails = {"PersistedFaceId":userDetail.PersistedFaceId,"FirstName":userDetail.FirstName,"LastName":userDetail.LastName,"Email":userDetail.Email,"image":request.build_absolute_uri(userDetail.image.url),"id":userDetail.id,"created_at":userDetail.created_at,"old":"yes","loyalty_balance":pre_loyalty_balance}

                                #Update user status
                                UserData.objects.filter(id=userDetail.id).update(staff_code=request.POST['staff_code'])

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
            record = {"statusCode":400, "message":"validation error","data":errors}
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output, safe=False)

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
                listing = BranchStaffCode.objects.get(staff_code=request.POST['staff_code'])
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Incorrect Staff code !'}
                return JsonResponse(record, safe=False)

            saved1 = form.save(commit=False)
            saved1.branch_id = request.POST['branch_id']
            saved=saved1.save()
            data_saved = UserData.objects.latest('id')
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
                        # t.is_active = 'Y'
                        t.save()

                        try:
                            LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = data_saved.id).latest('id')
                            pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                        except LoyaltyPoint.DoesNotExist:
                            pre_loyalty_balance = 0

                        userDetails = {"PersistedFaceId":added_face['persistedFaceId'],"FirstName":data_saved.FirstName,"LastName":data_saved.LastName,"Email":data_saved.Email,"image":request.build_absolute_uri(data_saved.image.url),"id":data_saved.id,"created_at":data_saved.created_at,"old":"no","loyalty_points":pre_loyalty_balance}

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
            record = {"statusCode":400, "message":"validation error","data":errors}
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output, safe=False)

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
            record = {"statusCode":400, "message":"validation Errors","data":errors}
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
                    listing = BranchStaffCode.objects.get(staff_code=staff_code)
                except BranchStaffCode.DoesNotExist:
                    record = {"statusCode":400, "message":'Incorrect Staff code !'}
                    return JsonResponse(record, safe=False)



                # user_data = UserData.objects.filter(staff_code=staff_code, branch_id= branch_id,is_deleted='N').order_by('-id')[:settings.LIMIT_ACTIVE_CUSTOMERS]
                user_data = UserData.objects.filter(staff_code=staff_code, is_deleted='N').order_by('-id')[:settings.LIMIT_ACTIVE_CUSTOMERS]
                previous_customers = []
                current_customer = []
                for user in user_data:
                    if not current_customer:
                        if not selected_userdata_id:
                            pre_loyalty_balance = 0

                            try:
                                LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = user.id,company_id=company_id).latest('id')
                                pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                            except LoyaltyPoint.DoesNotExist:
                                pre_loyalty_balance = 0

                            current_customer_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url),"loyalty_points":pre_loyalty_balance}
                            current_customer.append(current_customer_record)
                        else:
                            UserDetail = UserData.objects.get(pk=selected_userdata_id)
                            pre_loyalty_balance = 0

                            try:
                                LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = selected_userdata_id,company_id=company_id).latest('id')
                                pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
                            except LoyaltyPoint.DoesNotExist:
                                pre_loyalty_balance = 0

                            current_customer_record = {"userdata_id":UserDetail.id,"FirstName":UserDetail.FirstName,"LastName":UserDetail.LastName,"Email":UserDetail.Email,"image":request.build_absolute_uri(UserDetail.image.url),"loyalty_points":pre_loyalty_balance}
                            current_customer.append(current_customer_record)
                    else:
                        user_record = {"userdata_id":user.id,"FirstName":user.FirstName,"LastName":user.LastName,"Email":user.Email,"image":request.build_absolute_uri(user.image.url)}
                        previous_customers.append(user_record)

                if not current_customer:
                    loyalty_benefits = []
                else:
                    loyalty_benefits = []
                    for customer in current_customer:
                        current_customer_loyalty = customer['loyalty_points']
                        loyalty_benefits_data = LoyaltyManager.objects.filter(company_id = company_id, loyalty_points__lte = current_customer_loyalty).order_by('-id')[:3]

                        for loyalty_benefit in loyalty_benefits_data:
                            loyalty_benefit_record = {"loyalty_manager_id":loyalty_benefit.id,"loyalty_points":loyalty_benefit.loyalty_points,"benefit":loyalty_benefit.benefit}
                            loyalty_benefits.append(loyalty_benefit_record)

                coupons = []
                if not current_customer:
                    coupons = []
                else:
                    for customer in current_customer:
                        used_coupons = Purchase.objects.filter(userdata_id = customer['userdata_id']).values('coupon_id')
                        #print(used_coupons)
                        coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).exclude(id__in=used_coupons).order_by('-id')[:4]

                        #coupon_data = Coupon.objects.filter(users__id=customer['userdata_id'],company_id=company_id).order_by('-id')[:4]

                        for coupon in coupon_data:
                            coun = UsersCoupon.objects.get(coupon_id=coupon.id,userdata_id=customer['userdata_id'])
                            coupon_record = {"id":coupon.id,"coupon":coupon.coupon_code,"description":coupon.description,"discount_type":coupon.discount_type,"amount":coupon.amount,"amount":coupon.amount,'minimum_spend':coupon.minimum_spend,'maximum_spend':coupon.maximum_spend,'expiry_date':coupon.expiry_date,"image":request.build_absolute_uri(format(coupon.image.url))}
                            coupons.append(coupon_record)

                record = {"statusCode":200, "message":'Cutomers list !',"data":{'current_customer':current_customer,'previous_customers':previous_customers,'loyalty_benefits':loyalty_benefits,'coupons':coupons}}
            except UserData.DoesNotExist:
                record = {"statusCode":200, "message":'No customer found !'}
        else:
            errors = form.errors
            record = {"statusCode":400, "message":"validation Errors","data":errors}
    else:
        record = {"statusCode":400, "message":'invalid request method'}

    output.append(record)
    return JsonResponse(record, safe=False)

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
                        userDetail = User.objects.filter(groups__name='Store Manager',id=user.id).values()
                        if not userDetail:
                            record = {"statusCode":400, "message":'User is not a manager!'}
                        else:
                            try:
                                BranchDetails = Branch.objects.get(user_id=user)
                                if user_type == 'Staff':
                                    staff_code = get_random_string(length=10)
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
                                        'staff_code' : staff_code
                                    }}
                                else:
                                    record = {"statusCode":200, "message":'successfully login!', 'data' : {
                                        'first_name' : user.first_name,
                                        'last_name' : user.last_name,
                                        'email' : user.email,
                                        'username' : user.username,
                                        'branch_id' : BranchDetails.id,
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
            record = {"statusCode":400, "message":"validation Errors","data":errors}
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

            branch = Branch.objects.get(id=branch_id)
            userdata = UserData.objects.get(id=userdata_id)

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
                loyalty_instance = LoyaltyPoint(tx_type='PURCHASE',userdata=userdata, purchase=purchase_saved,loyalty_points=int(request.POST['amount']),loyalty_balance=pre_loyalty_balance+int(request.POST['amount']),company=company)
                loyalty_instance.save()

            record = {"statusCode":200, "message":"Purchase data added successfully"}
        else:
            errors = form.errors
            record = {"statusCode":400, "message":"validation Errors","data":errors}
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
            branch = Branch.objects.get(id=branch_id)

            company = Company.objects.get(id = branch.company_id)
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

                loyalty_instance = LoyaltyPoint(tx_type='REDEEM',userdata=userdata, purchase_id=None,loyalty_points=int(req_loyalty_points),loyalty_balance=pre_loyalty_balance-int(req_loyalty_points),loyalty_value=int(req_loyalty_value),tot_loyalty_value=pre_loyalty_value+int(req_loyalty_value),company=company)
                loyalty_instance.save()

                record = {"statusCode":200, "message":"Loyalty Points redeemed successfully"}
            else:
                record = {"statusCode":400, "message":"Customer doesn\'t have enough loyalty points."}
        else:
            errors = form.errors
            record = {"statusCode":400, "message":"validation Errors","data":errors}
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
                listing = BranchStaffCode.objects.get(staff_code=staff_code)
                record = {"statusCode":200, "message":'Staff code is valid !'}
            except BranchStaffCode.DoesNotExist:
                record = {"statusCode":400, "message":'Invalid Staff code !'}
                return JsonResponse(record, safe=False)
        else:
            errors = form.errors
            record = {"statusCode":400, "message":"validation Errors","data":errors}
    else:
        record = {"statusCode":400, "message":'invalid request method'}
    output.append(record)
    return JsonResponse(record, safe=False)

# def reports(request):
#     return HttpResponse('yes');

@staff_member_required
def my_model_list_view(request): #show list of all objects.
    context = {'foo': 'bar'}
    r = render(request, 'admin/reports/reports.html', context)
    return HttpResponse(r)

@staff_member_required
def my_model_export(request): #show list of all objects.
    context = {'foo': 'bar'}
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    # The data is hard-coded here, but you could load it from a database or
    # some other source.
    csv_data = (
        ('First row', 'Foo', 'Bar', 'Baz','fr','ht'),
        ('Second row', 'A', 'B', 'C', '"Testing"', 'Heres a quote'),
    )

    t = loader.get_template('my_template_name.txt')
    c = {'data': csv_data}

    response.write(t.render(c))
    return response
    r = render(request, 'admin/reports/reports.html', context)
    return HttpResponse(r)

@staff_member_required
def my_model_detail_view(request, row_id):
    context = {'foo': 'bar'}
    r = render(request, 'admin/reports/reports.html', context)
    return HttpResponse(r)
