from django.shortcuts import render
import requests
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from .models import UserData
from .forms import ImageForm,UserForm
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core import serializers
import json
import os
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

def addFacetoList_old(image):
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    try:
        image_url = image
        params = urllib.parse.urlencode({
            'userData': image_url
        })
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largefacelists/facedetectionlist_new/persistedFaces?%s" % params, '{"url": "'+image_url+'"}', headers)
        response = conn.getresponse()
        data = response.read()
        responseObject = json.loads(data)
        conn.close()
        return responseObject;
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

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






@csrf_exempt
def model_form_upload(request):
    output=[]
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():

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
                                userDetail = UserData.objects.get(PersistedFaceId=sm['persistedFaceId'])
                                userDetail = {"PersistedFaceId":userDetail.PersistedFaceId,"FirstName":userDetail.FirstName,"LastName":userDetail.LastName,"Email":userDetail.Email,"image":request.build_absolute_uri(userDetail.image.url),"UserId":userDetail.id,"old":"yes"}
                                record = {"statusCode":200, "message":'similar face found !',"data":userDetail}
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
            saved = form.save()
            added_face = addFacetoList(request.FILES["image"])
            added_face = added_face.json()
    		
            for face in added_face:
                if face=='error':
                    UserData.objects.filter(id=saved.id).delete()
                    os.unlink(saved.image.path)
                    error_msg = json.dumps(added_face['error']['message'])
                    record = {"statusCode":400, "message":error_msg}
                    output.append(record)
                    return JsonResponse(record, safe=False)
                else:
                    if added_face['persistedFaceId']!='':
                        TrainFaceList(request)
                        t = UserData.objects.get(id=saved.id)
                        t.PersistedFaceId = added_face['persistedFaceId']
                        t.save()
                        record = {"statusCode":200, "message":'saved user data successfully!'}
                        output.append(record)
                        return JsonResponse(record, safe=False)
            UserData.objects.filter(id=saved.id).delete()
            os.unlink(saved.image.path)
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
def model_form_upload_test(request):
    output=[]
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            saved = form.save()
            face_detection = facedetect(request.build_absolute_uri(saved.image.url))
            faces = face_detection.json()
            if not faces:
                UserData.objects.filter(id=saved.id).delete()
                record = {"statusCode":400, "message":'Image Not Correct !'}
                return JsonResponse(record, safe=False)

            if len(faces)>1:
                UserData.objects.filter(id=saved.id).delete()
                record = {"statusCode":400, "message":'Image Contains Multiple Faces !'}
                return JsonResponse(record, safe=False)

            for face in faces:
                if face=='error':
                    UserData.objects.filter(id=saved.id).delete()
                    error_msg = json.dumps(faces['error']['message'])
                    record = {"statusCode":400, "message":error_msg}
                    output.append(record)
                else:
                    face_id = face['faceId']
                    list_id = "facedetectionlist_new"

                    for i in [0,1,2,3,4,5,6,7,8,9,10]:
                        if i==0:
                            list_id = "facedetectionlist_new"
                        else:
                            list_id = "facedetectionlist_new"+str(i)

                        print(str(i) + list_id)
                        check_face_list = getFaceList_test(request,list_id)
                        if len(check_face_list) == 0:
                            createFaceList_test(request,list_id)
                            added_face = addFacetoList_test(request.build_absolute_uri(saved.image.url),list_id)
                            #for added_f in added_face:
                            added_f='error'
                            if added_f=='error':
                                continue
                            if added_face['persistedFaceId']!='':
                                TrainFaceList_test(request,list_id)
                                t = UserData.objects.get(id=saved.id)
                                t.PersistedFaceId = added_face['persistedFaceId']
                                t.save()
                                record = {"statusCode":200, "message":'similar face not found !',"data":{"UserId":saved.id}}
                                output.append(record)
                                return JsonResponse(record, safe=False)
                        TrainFaceList_test(request,list_id)
                        similars = (FindSimilarinFaceList_test(request,face_id))
                        return HttpResponse(similars)
                        #print(similars)
                        for sm in similars:
                            if sm=='error':
                                error_msg = json.dumps(sm['error']['message'])
                                record = {"statusCode":400, "message":error_msg}
                                output.append(record)
                                return JsonResponse(record, safe=False)
                            if(sm['persistedFaceId']!='' and sm['confidence'] >= 0.50):

                                try:
                                    userDetail = UserData.objects.get(PersistedFaceId=sm['persistedFaceId'])
                                    userDetail = {"PersistedFaceId":userDetail.PersistedFaceId,"FirstName":userDetail.FirstName,"LastName":userDetail.LastName,"Email":userDetail.Email,"image":request.build_absolute_uri(userDetail.image.url),"UserId":userDetail.id,"old":"yes"}
                                except UserData.DoesNotExist:
                                    userDetail = {"FirstName":"","LastName":"","Email":"", "PersistedFaceId":sm['persistedFaceId'],"image":saved.image.url,"UserId":saved.id,"old":"no"}

                                if userDetail['old'] == "yes":
                                    UserData.objects.filter(id=saved.id).delete()
                                    os.unlink(saved.image.path)
                                else:
                                    t = UserData.objects.get(id=saved.id)
                                    t.PersistedFaceId = sm['persistedFaceId']
                                    t.save()

                                record = {"statusCode":200, "message":'similar face found !',"data":userDetail}
                                output.append(record)
                                return JsonResponse(record, safe=False)
                            else:
                                added_face = addFacetoList_test(request.build_absolute_uri(saved.image.url),list_id)
                                #for added_f in added_face:
                                added_f = 'error'
                                if added_f=='error':
                                    continue
                                if added_face['persistedFaceId']!='':
                                    TrainFaceList_test(request,list_id)
                                    t = UserData.objects.get(id=saved.id)
                                    t.PersistedFaceId = added_face['persistedFaceId']
                                    t.save()
                                    record = {"statusCode":200, "message":'similar face not found !',"data":{"UserId":saved.id}}
                                    output.append(record)
                                    return JsonResponse(record, safe=False)
                                record = {"statusCode":400, "message":'face could not be added !'}
                                output.append(record)
                                return JsonResponse(record, safe=False)
                        added_face = addFacetoList_test(request.build_absolute_uri(saved.image.url),list_id)
                        #for added_f in added_face:
                        added_f = 'error'
                        if added_f=='error':
                            continue
                        if added_face['persistedFaceId']!='':
                            TrainFaceList_test(request,list_id)
                            t = UserData.objects.get(id=saved.id)
                            t.PersistedFaceId = added_face['persistedFaceId']
                            t.save()
                            record = {"statusCode":200, "message":'similar face not found !',"data":{"UserId":saved.id}}
                            output.append(record)
                            return JsonResponse(record, safe=False)
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

def getFaceList_test(request,list_id):
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
        conn.request("GET", "/face/v1.0/largefacelists/"+list_id+"/persistedfaces?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def createFaceList_test(request,list_id):
    headers = { 'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY }
    params = urllib.parse.urlencode({
    })
    try:
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("PUT", "/face/v1.0/largefacelists/"+list_id+"?%s" % params, '{"name": "sample_list","userData": "User-provided data attached to the face list."}', headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return HttpResponse(data);

    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def addFacetoList_test(image,list_id):
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    try:
        image_url = image
        params = urllib.parse.urlencode({
            'userData': image_url
        })
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largefacelists/"+list_id+"/persistedFaces?%s" % params, '{"url": "'+image_url+'"}', headers)
        response = conn.getresponse()
        data = response.read()
        responseObject = json.loads(data)
        conn.close()
        return responseObject;
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def TrainFaceList_test(request,list_id):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
    })

    try:
        conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/largefacelists/"+list_id+"/train?%s" % params, "", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return HttpResponse(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


def FindSimilarinFaceList_test(request,face_id):
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
    }

    params = urllib.parse.urlencode({
    })

    for i in [0,1,2,3,4,5,6,7,8,9,10]:
        if i==0:
            list_id = "facedetectionlist_new"
        else:
            list_id = "facedetectionlist_new"+str(i)
       	print(list_id)
        check_face_list = getFaceList_test(request,list_id)
        if len(check_face_list) != 0:
            try:
                conn = http.client.HTTPSConnection('northeurope.api.cognitive.microsoft.com')
                conn.request("POST", "/face/v1.0/findsimilars?%s" % params, '{"faceId": "'+face_id+'","largeFaceListId": "'+list_id+'","maxNumOfCandidatesReturned": 50,"mode": "matchPerson"}', headers)
                response = conn.getresponse()
                data = response.read()
                responseObject = json.loads(data)
                #print(data)
                conn.close()
                if len(responseObject)==0 and i<10:
                	continue
                return responseObject;
            except Exception as e:
                print("[Errno {0}] {1}".format(e.errno, e.strerror))
