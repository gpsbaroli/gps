from django.shortcuts import render
import requests
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from .models import FaceDetection,FaceImages
from .forms import ImageForm
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
# Create your views here.

def facedetect(image):
    #return image

    headers = { 'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY }
    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise',
    }

    face_api_url = 'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect/'
    image_url = 'http://111.93.41.194:5779'+image
    response = requests.post(face_api_url, params=params, headers=headers, json={"url": image_url})
    #faces = dict()
    #faces = response.json()
    #for group in faces:
    	#face = FaceDetection.objects.get(faceId=group['faceId'])
       # FaceDetection.objects.create(faceId=group['faceId'],faceTop=group['faceRectangle']['top'],faceLeft=group['faceRectangle']['left'],faceWidth=group['faceRectangle']['width'],faceHeight=group['faceRectangle']['height'],attrGender=group['faceAttributes']['gender'],attrAge=group['faceAttributes']['age'])

    return response


def createFaceList(request):
    headers = { 'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY }
    params = urllib.parse.urlencode({
	})
    try:
	    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	    conn.request("PUT", "/face/v1.0/largefacelists/facedetectionlist_new?%s" % params, '{"name": "sample_list","userData": "User-provided data attached to the face list."}', headers)
	    response = conn.getresponse()
	    data = response.read()
	    conn.close()
	    return HttpResponse(data);

    except Exception as e:
	    print("[Errno {0}] {1}".format(e.errno, e.strerror))

def addFacetoList(request):
	headers = {
	    'Content-Type': 'application/json',
	    'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
	}

	params = urllib.parse.urlencode({
	    # 'userData': '{string}',
	    # 'targetFace': '{string}',
	})

	try:
	    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	    conn.request("POST", "/face/v1.0/largefacelists/facedetectionlist_new/persistedFaces?%s" % params, '{"url": "http://111.93.41.194:5779/documents/_3af44508-acd4-11e7-b6fd-382ae8cf2ee4.jpg"}', headers)
	    response = conn.getresponse()
	    data = response.read()
	    print(data)
	    conn.close()
	    return HttpResponse(data);
	except Exception as e:
	    print("[Errno {0}] {1}".format(e.errno, e.strerror))

def getFaceList(request):
	headers = {
	    # Request headers
	    'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY,
	}

	params = urllib.parse.urlencode({
	})

	try:
	    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	    conn.request("GET", "/face/v1.0/largefacelists/facedetectionlist_new?%s" % params, "{body}", headers)
	    response = conn.getresponse()
	    data = response.read()
	    print(data)
	    conn.close()
	    return HttpResponse(data)
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
	    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
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

	try:
	    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
	    conn.request("POST", "/face/v1.0/findsimilars?%s" % params, '{"faceId": "'+face_id+'","largeFaceListId": "facedetectionlist_new","maxNumOfCandidatesReturned": 1,"mode": "matchPerson"}', headers)
	    response = conn.getresponse()
	    data = response.read()
	    #print(data)
	    conn.close()
	    return data;
	except Exception as e:
	    print("[Errno {0}] {1}".format(e.errno, e.strerror))

@csrf_exempt
def model_form_upload(request):
    output=[]
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            saved = form.save()
            face_detection = facedetect(settings.MEDIA_URL+str(saved.image))
            #faces = dict()
            faces = face_detection.json()
            #return HttpResponse(faces)

            if faces:
                for face in faces:
                    face_id = face['faceId']
                    similar = FindSimilarinFaceList(face_id)
                    similars = similar.json()
                    if similar[0]:
                        record = {"statusCode":200, "message":'similar face found !',"data":{'persistedFaceId':similars['persistedFaceId']}}
                        output.append(record)
                    else:
                        record = {"statusCode":200, "message":'similar face not found !'}
                        output.append(record)
            else:
                if 'error' in faces:
                    error_msg = json.dumps(faces['error']['message'])
                    record = {"statusCode":400, "message":error_msg}
                    output.append(record)
        else:
            record = {"statusCode":400, "message":"validation error"}
            output.append(record)
    else:
        record = {"statusCode":400, "message":"Not a valid request method !"}
        output.append(record)

    return JsonResponse(output, safe=False)
