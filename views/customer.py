from django.http import JsonResponse, HttpResponse
from face_detection.models import Useragree, Company,Branch, Purchase, LoyaltyManager, Coupon, CouponDetail,CompanyRating, FavouriteCompany,UserData,LoyaltyPoint,UsersSelectedCoupon,UsersCoupon,EmailTemplate, Allergy,CustomerAllergy
from face_detection.forms import getCompaniesForm, getBranchesForm,getCustomerCouponForm, getPurchasesForm,CompanyRatingForm,CompanyFavouriteForm,CustomerImageForm,CustomerForm,UpdateCustomerForm,CompanyReviewForm,InvisibleForm,getLoyaltyForm,SelectCouponsForm,SelectCouponDetailForm,SelectNonRegisteredCouponsForm,getcompanylocrevloyalityForm,getBranchesNonRegisteredForm,increaseCouponCountForm,GetNonRegisteredCouponsForm,getCompanyReviewsForm,AllDeleteForm,WpRegisterationForm,selectallergyForm
import http.client, urllib.request, urllib.parse, urllib.error, base64
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import json
import os # added on 11_13_2018
from datetime import datetime
from datetime import datetime
from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.db.models import Sum
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal
from django.core.mail import EmailMessage
from datetime import timedelta
from django.contrib.auth.models import User, AbstractBaseUser
from django.contrib.auth.models import Group
from django.utils import timezone

def addFacetoList(imagedata):
	#return image

	headers = { 'Ocp-Apim-Subscription-Key': settings.SUBSCRIPTION_KEY, 'Content-Type':'application/octet-stream' }
	params = {
		'userData': ''
	}

	face_api_url = 'https://northeurope.api.cognitive.microsoft.com/face/v1.0/largefacelists/facedetectionlist_new/persistedFaces/'
	response = requests.post(face_api_url,  headers=headers, data = imagedata, params=params )
	return response
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

#login customer
@csrf_exempt
def customer_image_upload(request):
	output=[]
	if request.method == 'POST':
		form = CustomerImageForm(request.POST, request.FILES)
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
					for sm in similars:
						if(sm['persistedFaceId']!='' and sm['confidence'] >= 0.50):
							try:
								userDetail = UserData.objects.get(PersistedFaceId=sm['persistedFaceId'],is_deleted='N')

								# try:
								#     LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userDetail.id).latest('id')
								#     pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
								# except LoyaltyPoint.DoesNotExist:
								#     pre_loyalty_balance = 0

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


								userDetails = {"greeting_name":greeting_name,"phone_number":phone_number,"date_of_birth":date_of_birth,"PersistedFaceId":userDetail.PersistedFaceId,"FirstName":userDetail.FirstName,"LastName":userDetail.LastName,"Email":userDetail.Email,"image":request.build_absolute_uri(userDetail.image.url),"id":userDetail.id,"created_at":datetime.strptime(str(userDetail.created_at), '%Y-%m-%d').strftime('%d %b, %Y'),"old":"yes"}
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

#API to use when customer is not found
@csrf_exempt
def save_customer_data(request):
	output=[]
	if request.method == 'POST':
		form = CustomerForm(request.POST, request.FILES)
		if form.is_valid():

			saved1 = form.save(commit=False)
			# saved1.branch_id = False
			saved=saved1.save()

			data_saved = UserData.objects.latest('id')

			# UserData.objects.filter(staff_code=request.POST['staff_code']).update(is_active='N')
			# UserData.objects.filter(id=data_saved.id).update(staff_code=request.POST['staff_code'],updated_staffcode_at = datetime.now(),is_active='Y')

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
						#t.updated_staffcode_at = datetime.now()
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

						#BranchDetails = Branch.objects.get(pk = request.POST['branch_id'])
						#print(BranchDetails)
						# try:
						#     userComDetail = Useragree.objects.get(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
						# except Useragree.DoesNotExist:
						#     save_user_agreement = Useragree(company_id=BranchDetails.company_id,userdata_id=data_saved.id)
						#     save_user_agreement.save()


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

#API for update customer
@csrf_exempt
def update_customer_data(request):
	output=[]
	if request.method == 'POST':
		form = UpdateCustomerForm(request.POST)
		if form.is_valid():

			id = request.POST['userdata_id']
			FirstName = request.POST['FirstName']
			LastName = request.POST['LastName']
			Email = request.POST['Email']
			greeting_name = request.POST.get('greeting_name', None)
			phone_number = request.POST.get('phone_number', None)
			date_of_birth = request.POST.get('date_of_birth', None)

			t = UserData.objects.get(pk=id)
			#return HttpResponse(t)

			t.FirstName = FirstName  # change field
			t.LastName = LastName  # change field
			t.Email = Email  # change field
			t.greeting_name = greeting_name  # change field
			t.phone_number = phone_number  # change field
			t.date_of_birth = date_of_birth  # change field
			t.save() # this will update only
			#return HttpResponse(t)
			data_saved = UserData.objects.get(pk=id)

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

			userDetails = {"greeting_name":greeting_name,"phone_number":phone_number,"date_of_birth":date_of_birth,"PersistedFaceId":data_saved.PersistedFaceId,"FirstName":data_saved.FirstName,"LastName":data_saved.LastName,"Email":data_saved.Email,"image":request.build_absolute_uri(data_saved.image.url),"id":data_saved.id,"created_at":datetime.strptime(str(data_saved.created_at), '%Y-%m-%d').strftime('%d %b, %Y'),"old":"no"}


			record = {"statusCode":200, "message":'saved user data successfully!',"data":userDetails}
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


#get companies based on customer id(userdata_id)
@csrf_exempt
def get_companies(request):
	output = []
	if request.method == 'POST':
		form = getCompaniesForm(request.POST)
		if form.is_valid():
			userdata_id = request.POST['userdata_id']
			company_type = request.POST['company_type']
			latitude = request.POST['latitude']
			longitude = request.POST['longitude']


			try:
				registered_companies = Useragree.objects.filter(userdata_id=userdata_id).values('company_id')
			except Useragree.DoesNotExist:
				registered_companies = []

			if company_type == 'R':
				try:
					CompanyData = Company.objects.filter(id__in = registered_companies,status='a').all()
				except Company.DoesNotExist:
					CompanyData = []


				required_data = []
				if CompanyData:
					for company in CompanyData:

						#get average rating
						r_stars_average = 0
						try:
							r_stars_average1 = CompanyRating.objects.filter(company_id = company.id).aggregate(avg_rating=Avg('rating'))
							r_stars_average = r_stars_average1['avg_rating']

							if not r_stars_average1['avg_rating']:
								r_stars_average = 0
							else:
								r_stars_average = r_stars_average1['avg_rating']


						except:
							r_stars_average = 0


						#check if company is favourite or not
						is_favourite = 'N'
						favourite_message = ''

						if company.latitude and company.latitude:
							# approximate radius of earth in km
							R = 6373.0

							lat1 = radians(company.latitude)
							lon1 = radians(company.longitude)
							lat2 = radians(Decimal(latitude))
							lon2 = radians(Decimal(longitude))


							dlon = lon2 - lon1
							dlat = lat2 - lat1

							a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
							c = 2 * atan2(sqrt(a), sqrt(1 - a))

							distance = R * c
						else:
							distance = 0

						try:
							fav = FavouriteCompany.objects.filter(userdata_id = userdata_id, company_id = company.id).get()
							is_favourite = 'Y'
							favourite_message = fav.message
						except:
							pass

						logopath = ''
						try:
							logopath = request.build_absolute_uri(format(company.logo.url));
						except:
							pass

						company_record = {"distance":round(distance,2),"favourite_message":favourite_message,"is_favourite":is_favourite,"avg_rating":r_stars_average, "id":company.id,"name":company.name,"address":company.address,"logo":logopath,"phone_number":company.phone_number,"contact_name":company.contact_name}

						required_data.append(company_record)
						required_data = sorted(required_data, key=lambda x:x['distance'])

				record = {"statusCode":200, "message":'Registered Company list !',"data":required_data}
			else:
				try:
					CompanyData = Company.objects.filter(status='a').exclude(id__in=registered_companies).all()
				except Company.DoesNotExist:
					CompanyData = []

				required_data = []
				if CompanyData:
					for company in CompanyData:
						stars_average = 0
						try:
							stars_average1 = CompanyRating.objects.filter(company_id = company.id).aggregate(avg_rating=Avg('rating'))
							if not stars_average1['avg_rating']:
								stars_average = 0
							else:
								stars_average = stars_average1['avg_rating']
						except:
							stars_average = 0

						#check if company is favourite or not
						is_favourite = 'N'
						favourite_message = ''

						if company.latitude and company.longitude:
							# approximate radius of earth in km
							R = 6373.0

							lat1 = radians(company.latitude)
							lon1 = radians(company.longitude)
							lat2 = radians(Decimal(latitude))
							lon2 = radians(Decimal(longitude))

							dlon = lon2 - lon1
							dlat = lat2 - lat1

							a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
							c = 2 * atan2(sqrt(a), sqrt(1 - a))

							distance = R * c
						else:
							distance = 0

						try:
							fav = FavouriteCompany.objects.filter(userdata_id = userdata_id, company_id = company.id).get()
							is_favourite = 'Y'
							favourite_message = fav.message
						except:
							pass

						logopath = ''
						try:
							logopath = request.build_absolute_uri(format(company.logo.url));
						except:
							pass

						company_record = {"distance":round(distance,2),"favourite_message":favourite_message,"is_favourite":is_favourite,"avg_rating":stars_average,"id":company.id,"name":company.name,"address":company.address,"image":logopath,"phone_number":company.phone_number,"contact_name":company.contact_name}

						required_data.append(company_record)
						required_data = sorted(required_data, key=lambda x:x['distance'])

				record = {"statusCode":200, "message":'Not Registered Company list !',"data":required_data}


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

#get branches based on company id
@csrf_exempt
def get_company_branches(request):
	output = []
	if request.method == 'POST':
		form = getBranchesForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			userdata_id = request.POST['userdata_id']
			latitude = request.POST['latitude']
			longitude = request.POST['longitude']

			#Get branches of company
			try:
				branches = Branch.objects.filter(company_id=company_id, is_deleted = 'N').all()
			except Branch.DoesNotExist:
				branches = []

			branches_data = []
			branch_spendings = []
			tot_spending_amount = 0
			tot_visits = 0
			if branches:
				for branch in branches:

					try:
						tot_spending = Purchase.objects.filter(branch_id=branch.id, userdata_id = userdata_id).aggregate(spending=Coalesce(Sum('amount'),0))
						visits = Purchase.objects.filter(branch_id=branch.id, userdata_id = userdata_id).all().count()
						spendings = tot_spending['spending']
						tot_spending_amount = tot_spending_amount+spendings
						tot_visits = tot_visits+visits
					except Purchase.DoesNotExist:
						spendings = 0

					b_spending = {"id":branch.id,"branch" : branch.name , "spending" : spendings}
					branch_spendings.append(b_spending)

					if branch.latitude and branch.latitude:
						# approximate radius of earth in km
						R = 6373.0

						lat1 = radians(branch.latitude)
						lon1 = radians(branch.longitude)
						lat2 = radians(Decimal(latitude))
						lon2 = radians(Decimal(longitude))

						dlon = lon2 - lon1
						dlat = lat2 - lat1

						a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
						c = 2 * atan2(sqrt(a), sqrt(1 - a))

						distance = R * c
					else:
						distance = 0

					branch_record = {"distance":round(distance,2),"id":branch.id,"name":branch.name,"address":branch.address,"latitude":branch.latitude,"longitude":branch.longitude}
					branches_data.append(branch_record)
					branches_data = sorted(branches_data, key=lambda x:x['distance'])

			#Get coupons of company
			try:
				used_coupons = Purchase.objects.filter(userdata_id = userdata_id).values('coupon_id')
				exclude_ids = []
				for o in used_coupons:
					if o['coupon_id'] != None:
						exclude_ids.append(o['coupon_id'])

				selected_coupons = UsersSelectedCoupon.objects.filter(userdata_id = userdata_id).values('coupon_id')
				include_ids = []
				for o2 in selected_coupons:
					if o2['coupon_id'] != None:
						include_ids.append(o2['coupon_id'])

				coupons = Coupon.objects.filter(users__id=userdata_id,company_id=company_id).exclude(id__in=exclude_ids).order_by('-id').all()
			except Coupon.DoesNotExist:
				coupons = []

			coupons_data = []
			if coupons:
				for coupon in coupons:
					is_selected = 'N'

					if coupon.id in include_ids:
						is_selected = 'Y'

					coupon_record = {"is_selected":is_selected,"id":coupon.id,"coupon_code":coupon.coupon_code,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)), "expiry_date":coupon.expiry_date}
					coupons_data.append(coupon_record)

			pre_loyalty_balance = 0
			try:
				LoyaltyPointDetail = LoyaltyPoint.objects.filter(userdata_id = userdata_id,company_id=company_id).latest('id')
				pre_loyalty_balance = LoyaltyPointDetail.loyalty_balance
			except LoyaltyPoint.DoesNotExist:
				pre_loyalty_balance = 0

			#Get non registered coupons of company
			try:
				coupons_non = Coupon.objects.filter(company_id=company_id,user_type="non-registered")
			except Coupon.DoesNotExist:
				coupons_non = []

			coupons_non_data = []
			if coupons_non:
				for coupon1 in coupons_non:
					coupon_record_non = {"id":coupon1.id,"coupon_code":coupon1.coupon_code,"description":coupon1.description,"image":request.build_absolute_uri(format(coupon1.image.url)), "expiry_date":coupon1.expiry_date}
					coupons_non_data.append(coupon_record_non)

			required_data = {"branches":branches_data,"coupons":coupons_data,"spendings":{"loyalty_balance":pre_loyalty_balance, "tot_spending_amount" : tot_spending_amount,"tot_visits" : tot_visits,"branch_spendings":branch_spendings},"coupons_non_registered":coupons_non_data}

			record = {"statusCode":200, "message":'Branch list !',"data":required_data}

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

#Get purchases based on branch id and customer id(userdata_id)
@csrf_exempt
def get_customer_purchases(request):
	output = []
	if request.method == 'POST':
		form = getPurchasesForm(request.POST)
		if form.is_valid():
			branch_id = request.POST['branch_id']
			userdata_id = request.POST['userdata_id']
			try:
				purchases = Purchase.objects.filter(branch_id=branch_id, userdata_id = userdata_id).all()
			except Purchase.DoesNotExist:
				purchases = []

			required_data = []
			if purchases:
				for purchase in purchases:
					purchase_record = {"id":purchase.id,"amount":purchase.amount,"purchase_summary":purchase.purchase_summary,"coupon_code":purchase.coupon_code if purchase.coupon_code else '' ,"discount_amount":purchase.discount_amount,"discount_type": purchase.discount_type if purchase.discount_type else '' ,"created":datetime.strptime(str(purchase.created_at), '%Y-%m-%d').strftime('%d %b, %Y')}
					required_data.append(purchase_record)

			record = {"statusCode":200, "message":'Purchase list !',"data":required_data}

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

#Get reviews and ratings based on company id(company_id)
@csrf_exempt
def get_company_reviews(request):
	output = []
	if request.method == 'POST':
		form = getCompanyReviewsForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']

			try:
				ratings = CompanyRating.objects.filter(company_id=company_id).all().order_by('-created_at')
			except CompanyRating.DoesNotExist:
				ratings = []

			rating_data = []

			stars_average = 0
			try:
				stars_average1 = CompanyRating.objects.filter(company_id = company_id).aggregate(avg_rating=Avg('rating'))
				if not stars_average1['avg_rating']:
					stars_average = 0
				else:
					stars_average = stars_average1['avg_rating']
			except:
				stars_average = 0

			if ratings:
				for rating in ratings:
					userDetail = UserData.objects.get(pk=rating.userdata_id)
					rating_record = {"customer_name":userDetail.FirstName+' '+userDetail.LastName,"rating":rating.rating,"review":rating.message,"created_at":datetime.strptime(str(rating.created_at), '%Y-%m-%d').strftime('%d %b, %Y')}
					rating_data.append(rating_record)



			required_data = {"average_rating":stars_average, "reviews" : rating_data}

			record = {"statusCode":200, "message":'Reviews list !',"data":required_data}

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

#Get company loyalty points based on company_id
@csrf_exempt
def get_company_loyalty_points(request):
	output = []
	if request.method == 'POST':
		form = getLoyaltyForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			try:
				loyalties = LoyaltyManager.objects.filter(company_id=company_id).all()
			except LoyaltyManager.DoesNotExist:
				loyalties = []

			required_data = []
			if loyalties:
				for loyalty in loyalties:
					loyalty_record = {"id":loyalty.id,"loyalty_points":loyalty.loyalty_points,"benefit":loyalty.benefit,"loyalty_value":loyalty.loyalty_value}
					required_data.append(loyalty_record)

			record = {"statusCode":200, "message":'Loyalty Points list !',"data":required_data}

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

#Get company coupons based on company_id
# @csrf_exempt
# def get_company_coupons(request):
#     output = []
#     if request.method == 'POST':
#         form = getCustomerCouponForm(request.POST)
#         if form.is_valid():
#             company_id = request.POST['company_id']
#             userdata_id = request.POST['userdata_id']
#             try:

#                 used_coupons = Purchase.objects.filter(userdata_id = userdata_id).values('coupon_id')
#                 exclude_ids = []
#                 for o in used_coupons:
#                     if o['coupon_id'] != None:
#                         exclude_ids.append(o['coupon_id'])

#                 coupons = Coupon.objects.filter(users__id=userdata_id,company_id=company_id).exclude(id__in=exclude_ids).order_by('-id').all()
#             except Coupon.DoesNotExist:
#                 coupons = []

#             required_data = []
#             if coupons:
#                 for coupon in coupons:
#                     coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)), "expiry_date":coupon.expiry_date}
#                     required_data.append(coupon_record)

#             record = {"statusCode":200, "message":'Coupons list !',"data":required_data}

#             return JsonResponse(record, safe=False)
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

#Rate company
@csrf_exempt
def rate_company(request):
	output = []
	if request.method == 'POST':
		form = CompanyRatingForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			userdata_id = request.POST['userdata_id']

			rating = request.POST['rating']
			try:
				t = CompanyRating.objects.get(company_id = company_id, userdata_id = userdata_id)

				if t:
					if t.rating:
						record = {"statusCode":400, "message":"You have already rated this company!"}
						output.append(record)
						return JsonResponse(output[0], safe=False)
					else:
						t.rating = rating
						t.save()
						record = {"statusCode":200, "message":"Your ratings has been submitted successfully"}
						output.append(record)
						return JsonResponse(output[0], safe=False)
			except CompanyRating.DoesNotExist:
				pass

			try:
				submit_rating = CompanyRating(company_id = company_id, userdata_id = userdata_id, rating = rating)
				submit_rating.save()

				record = {"statusCode":200, "message":"Your ratings has been submitted successfully"}
				output.append(record)

			except:
				record = {"statusCode":400, "message":"Couldn't submit ratings, Please try again!"}
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

#Favourite company
@csrf_exempt
def make_favourite_company(request):
	output = []
	if request.method == 'POST':
		form = CompanyFavouriteForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			userdata_id = request.POST['userdata_id']
			if 'message' in request.POST:
				message = request.POST['message']
			else:
				message = None

			try:
				favourite_company = FavouriteCompany.objects.get(company_id = company_id, userdata_id = userdata_id)

				if favourite_company:
					fav =  FavouriteCompany.objects.get(pk=favourite_company.id)
					fav.message  = message
					fav.save()
					record = {"statusCode":200, "message":"Updated favourite!"}
					output.append(record)
					return JsonResponse(output[0], safe=False)
			except FavouriteCompany.DoesNotExist:
				pass

			try:
				submit_favourite = FavouriteCompany(company_id = company_id, userdata_id = userdata_id,message=message)
				submit_favourite.save()

				record = {"statusCode":200, "message":"Company has been marked as favourite"}
				output.append(record)

			except:
				record = {"statusCode":400, "message":"Couldn't mark company as favourite, Please try again!"}
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

#Review company
@csrf_exempt
def review_company(request):
	output = []
	if request.method == 'POST':
		form = CompanyReviewForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			userdata_id = request.POST['userdata_id']
			message = request.POST['review']

			try:
				review_company = CompanyRating.objects.get(company_id = company_id, userdata_id = userdata_id)

				if review_company:
					if review_company.message:
						record = {"statusCode":400, "message":"You have already reviewed this company!"}
						output.append(record)
						return JsonResponse(output[0], safe=False)
					else:
						review_company.message = message
						review_company.save()
						record = {"statusCode":200, "message":"Your review has been submitted successfully!"}
						output.append(record)
						return JsonResponse(output[0], safe=False)

			except CompanyRating.DoesNotExist:
				pass

			try:
				review_company = CompanyRating(company_id = company_id, userdata_id = userdata_id,message=message)
				review_company.save()

				record = {"statusCode":200, "message":"Your review has been submitted successfully!"}
				output.append(record)

			except:
				record = {"statusCode":400, "message":"Couldn't submit your review, Please try again!"}
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

#Set invisible
@csrf_exempt
def set_invisible(request):
	output = []
	if request.method == 'POST':
		form = InvisibleForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']
			userdata_id = request.POST['userdata_id']

			try:
				review_company = Useragree.objects.filter(company_id = company_id, userdata_id = userdata_id).get()
				review_company.is_visible = 'N'
				review_company.save()

				record = {"statusCode":200, "message":"You have set your account as invisible successfully!"}
				output.append(record)

			except:
				record = {"statusCode":400, "message":"Couldn't make you invisible, Please try again!"}
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

#Select coupons so that it can be seen in company branch manager app
@csrf_exempt
def select_coupons(request):
	output = []
	if request.method == 'POST':
		form = SelectCouponsForm(request.POST)
		if form.is_valid():
			userdata_id = request.POST['userdata_id']
			coupon_id = request.POST['coupon_id']
			try:
				check_coupon = UsersCoupon.objects.get(userdata_id = userdata_id, coupon_id = coupon_id)
				try:
					get_selected_coupon = UsersSelectedCoupon.objects.get(userdata_id = userdata_id, coupon_id = coupon_id)
					record = {"statusCode":200, "message":"Coupon is already selected!"}
					output.append(record)
				except UsersSelectedCoupon.DoesNotExist:
					select_coupon = UsersSelectedCoupon(userdata_id = userdata_id, coupon_id = coupon_id)
					select_coupon.save()

				record = {"statusCode":200, "message":"Coupon has been selected successfully!"}
				output.append(record)
			except UsersCoupon.DoesNotExist:
				record = {"statusCode":200, "message":"This coupon doesn't exists!"}
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


#Select coupons so that it can be seen in company branch manager app
@csrf_exempt
def select_coupon_detail_bk(request):
	output = []
	if request.method == 'POST':
		form = SelectCouponDetailForm(request.POST)
		if form.is_valid():
			#userdata_id = request.POST['userdata_id']
			coupon_id = request.POST['coupon_id']


			try:
				check_coupon=[]
				check_coupon = Coupon.objects.filter( pk = coupon_id)

				coupons = []
				coupon_arr=[]
				coupons = Coupon.objects.filter(pk = coupon_id)
				if coupons:
					for coupon in coupons:
						company = Company.objects.get(pk=coupon.company_id)

						coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)),"discount_type":coupon.discount_type,"company_id":str(coupon.company_id),"amount":coupon.amount,"minimum_spend":coupon.minimum_spend,"maximum_spend":coupon.maximum_spend,"user_type":coupon.user_type,"created_at":coupon.created_at,"expiry_date":coupon.expiry_date,"name":company.name}
						coupon_arr.append(coupon_record)

						record = {"statusCode":200, "message":'success',"data":coupon_arr}
						return JsonResponse(record, safe=False)

			except Coupon.DoesNotExist:
				record = {"statusCode":200, "message":"This coupon doesn't exists!"}
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


#Select coupons so that it can be seen in company branch manager app
@csrf_exempt
def select_coupon_detail(request):
	output = []
	if request.method == 'POST':
		form = SelectCouponDetailForm(request.POST)
		if form.is_valid():
			userdata_id = request.POST['userdata_id']
			coupon_id = request.POST['coupon_id']
			company_id = request.POST['company_id']

			try:
				check_coupon=[]
				check_coupon = Coupon.objects.filter( pk = coupon_id)

				coupons = []
				coupon_arr=[]
				coupons = Coupon.objects.filter(pk = coupon_id)

				if coupons:
					for coupon in coupons:
						company = Company.objects.get(pk=coupon.company_id)

						try:
							usercoupon = UsersCoupon.objects.get(coupon_id=coupon_id,userdata_id=userdata_id)
							coupon_status="registered"
						except UsersCoupon.DoesNotExist:
							coupon_status="non-registered"

						try:
							agreed = Useragree.objects.get(userdata_id=userdata_id,company_id=coupon.company_id)
							company_status="registered"
						except Useragree.DoesNotExist:
							company_status="non-registered"

						coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"coupon_id":coupon_id,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)),"discount_type":coupon.discount_type,"company_id":str(coupon.company_id),"amount":coupon.amount,"minimum_spend":coupon.minimum_spend,"maximum_spend":coupon.maximum_spend,"user_type":coupon.user_type,"created_at":coupon.created_at,"expiry_date":coupon.expiry_date,"name":company.name,'coupon_status':str(coupon_status),'company_status':company_status}
						coupon_arr.append(coupon_record)

						record = {"statusCode":200, "message":'success',"data":coupon_arr}
						return JsonResponse(record, safe=False)

			except Coupon.DoesNotExist:
				record = {"statusCode":200, "message":"This coupon doesn't exists!"}
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


@csrf_exempt
def delete_from_all_companies(request):
    output = []
    if request.method == 'POST':
        form = AllDeleteForm(request.POST)
        if form.is_valid():
            userdata_id = request.POST['userdata_id']
            try:
                all_agreed = Useragree.objects.filter(userdata_id=userdata_id).all()
                if all_agreed:
                    for agree in all_agreed:
                        try:
                            User_agree = Useragree.objects.filter(userdata_id=userdata_id,company_id=agree.company_id).delete()

                            UserDetail = UserData.objects.get(pk=userdata_id)
                            company = Company.objects.get(pk=agree.company_id)

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

                        except Useragree.DoesNotExist:
                            pass

                    record = {"statusCode":200, "message":"Customer deleted from all companies successfully"}
                    output.append(record)
                    return JsonResponse(record, safe=False)
                else:
                    record = {"statusCode":400, "message":'you are not registered to any company yet !'}
                    return JsonResponse(record, safe=False)
            except:
                record = {"statusCode":400, "message":'There is some problem, Please try again !'}
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



#Get purchases based on branch id and customer id(userdata_id)
#Get non-registered coupons  17/10/2018
@csrf_exempt
def select_nonregistered_coupons(request):
	output = []
	if request.method == 'POST':
		form = SelectNonRegisteredCouponsForm(request.POST)
		if form.is_valid():
			user_type = request.POST['user_type']
			if user_type == 'non-registered':
				try:
					current_date = datetime.today()
					coupons = Coupon.objects.filter(user_type=user_type,expiry_date__gte=current_date).order_by('-bid')
				except Coupon.DoesNotExist:
					coupons = []

				required_data = []
				if coupons:
					for coupon in coupons:
						coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)),"discount_type":coupon.discount_type,"company_id":coupon.company_id,"amount":coupon.amount,"minimum_spend":coupon.minimum_spend,"maximum_spend":coupon.maximum_spend,"user_type":coupon.user_type,"created_at":coupon.created_at,"expiry_date":coupon.expiry_date}
						required_data.append(coupon_record)


				record = {"statusCode":200, "message":'Coupon list !',"data":required_data}
				return JsonResponse(record, safe=False)
			else:
				record = {"statusCode":400, "message":'User type is not non-registered !'}
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



#get branches based on company id
# Add user type status non-registered  17/10/2018
@csrf_exempt
def get_company_branches_nonregistered(request):
	output = []
	if request.method == 'POST':
		form = getBranchesNonRegisteredForm(request.POST)
		if form.is_valid():
			latitude = request.POST['latitude']
			longitude = request.POST['longitude']
			userdata_id = request.POST['userdata_id']

			#Get branches of company
			try:
				branches = Branch.objects.filter( is_deleted = 'N').all()
			except Branch.DoesNotExist:
				branches = []

			branches_data = []
			branch_spendings = []
			tot_spending_amount = 0
			tot_visits = 0
			if branches:
				for branch in branches:
					#print(branch.company_id)
					try:
						tot_spending = Purchase.objects.filter(branch_id=branch.id, userdata_id = userdata_id).aggregate(spending=Coalesce(Sum('amount'),0))
						visits = Purchase.objects.filter(branch_id=branch.id, userdata_id = userdata_id).all().count()
						spendings = tot_spending['spending']
						tot_spending_amount = tot_spending_amount+spendings
						tot_visits = tot_visits+visits
					except Purchase.DoesNotExist:
						spendings = 0

					b_spending = {"id":branch.id,"branch" : branch.name , "spending" : spendings}
					branch_spendings.append(b_spending)

					"""useragrees = Useragree.objects.filter(company_id = branch.company_id, userdata_id = userdata_id).all()
					if not useragrees:
						user_type="non-registered"
					else:
						user_type="registered """

					if branch.latitude and branch.latitude:
						# approximate radius of earth in km
						R = 6373.0

						lat1 = radians(branch.latitude)
						lon1 = radians(branch.longitude)
						lat2 = radians(Decimal(latitude))
						lon2 = radians(Decimal(longitude))

						dlon = lon2 - lon1
						dlat = lat2 - lat1

						a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
						c = 2 * atan2(sqrt(a), sqrt(1 - a))

						distance = R * c
					else:
						distance = 0


					branch_record = {"distance":round(distance,2),"id":branch.id,"name":branch.name,"address":branch.address,"latitude":branch.latitude,"longitude":branch.longitude}
					branches_data.append(branch_record)



			required_data = {"branches":branches_data}

			record = {"statusCode":200, "message":'Branch list !',"data":required_data}

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


#Select coupons so that it can be seen in company branch manager app
#Save coupon id with device id into coupon detail table and increase coupon counter into coupon table 18/10/2018
@csrf_exempt
def increaseCouponCount(request):
	output = []
	inserted_data = []
	if request.method == 'POST':
		form = increaseCouponCountForm(request.POST)
		if form.is_valid():
			coupon_id = request.POST['coupon_id']
			device_id = request.POST['device_id']
			#return HttpResponse(device_id)
			try:
				# check_coupon = Coupon.objects.filter(id = coupon_id).values('coupon_code','coupon_count')
				# try:
					# get_coupondetail = CouponDetail.objects.get(device_id = device_id, coupon_id = coupon_id)
					# record = {"statusCode":200, "message":"Coupon is already available!"}
					# output.append(record)
				# except CouponDetail.DoesNotExist:
				select_coupon = CouponDetail(device_id = device_id, coupon_id = coupon_id)
				select_coupon.save()

				couponCount = Coupon.objects.get(id = coupon_id)
				couponCount.coupon_count += 1
				couponCount.save()

				coupon_record = {"Device Id":device_id,"Coupon Id":coupon_id}
				inserted_data.append(coupon_record)

				record = {"statusCode":200, "message":"Coupon has been inserted successfully!","Inserted Data":inserted_data}
				output.append(record)

			except Coupon.DoesNotExist:
				record = {"statusCode":200, "message":"This coupon doesn't exists!"}
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
		record = {"statusCode":600, "message":"Not a valid request method !"}
		output.append(record)

	return JsonResponse(output[0], safe=False)


#get details based on company id 19/10/2018
@csrf_exempt
def get_company_loc_rev_loyality(request):
	output = []
	if request.method == 'POST':
		form = getcompanylocrevloyalityForm(request.POST)
		if form.is_valid():
			company_id = request.POST['company_id']

			#get non-registered voucher code
			user_type = 'non-registered'
			try:
				coupons = Coupon.objects.filter(user_type=user_type).all()
			except Coupon.DoesNotExist:
				coupons = []

			coupon_data = []
			coupon_record = []
			if coupons:
				for coupon in coupons:
					coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"company_id":coupon.company_id,"user_type":coupon.user_type}
					coupon_data.append(coupon_record)

			#get review of company
			try:
				ratings = CompanyRating.objects.filter(company_id=company_id).all()
			except CompanyRating.DoesNotExist:
				ratings = []

			rating_data = []
			stars_average = 0
			review_data = []
			try:
				stars_average1 = CompanyRating.objects.filter(company_id = company_id).aggregate(avg_rating=Avg('rating'))
				if not stars_average1['avg_rating']:
					stars_average = 0
				else:
					stars_average = stars_average1['avg_rating']
			except:
				stars_average = 0

			if ratings:
				for rating in ratings:
					userDetail = UserData.objects.get(pk=rating.userdata_id)
					rating_record = {"customer_name":userDetail.FirstName+' '+userDetail.LastName,"rating":rating.rating,"review":rating.message,"created_at":datetime.strptime(str(rating.created_at), '%Y-%m-%d').strftime('%d %b, %Y')}
					rating_data.append(rating_record)

			#Get locations of branches
			try:
				branches = Branch.objects.filter( is_deleted = 'N',company_id=company_id).all()
			except Branch.DoesNotExist:
				branches = []

			location_data = []
			branches_data = []
			if branches:
				for branch in branches:
					if branch.latitude and branch.latitude:
						location_data = {"id":branch.id,"name":branch.name,"address":branch.address,"latitude":branch.latitude,"longitude":branch.longitude}
						branches_data.append(location_data)

			#Get Loyalty points of LoyaltyManager
			try:
				loyalties = LoyaltyManager.objects.filter(company_id=company_id).all()

			except LoyaltyManager.DoesNotExist:
				loyalties = []

			required_data = []
			loyalty_record = []
			if loyalties:
				for loyalty in loyalties:
					required_data = {"id":loyalty.id,"loyalty_points":loyalty.loyalty_points,"benefit":loyalty.benefit,"loyalty_value":loyalty.loyalty_value}
					loyalty_record.append(required_data)

			required_data = {"Branch Data":branches_data,"Coupons Data":coupon_data,"Review Data":rating_data,"Loyalty Data":loyalty_record}

			record = {"statusCode":200, "message":'Record list based on company id !',"data":required_data}
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

#Get non-registered coupons params {company_id}  19/10/2018
@csrf_exempt
def get_nonregistered_coupons(request):
	output = []
	if request.method == 'POST':
		form = GetNonRegisteredCouponsForm(request.POST)
		if form.is_valid():
			user_type = 'non-registered'
			#company_id = request.POST['company_id']

			if user_type == 'non-registered':
				try:
					#coupons = Coupon.objects.filter(user_type=user_type,company_id=company_id).all()
					current_date = datetime.today()
					coupons = Coupon.objects.filter(user_type=user_type,expiry_date__gte=current_date).order_by('-bid')
				except Coupon.DoesNotExist:
					coupons = []

				required_data = []
				if coupons:
					for coupon in coupons:
						coupon_record = {"id":coupon.id,"coupon_code":coupon.coupon_code,"description":coupon.description,"image":request.build_absolute_uri(format(coupon.image.url)),"discount_type":coupon.discount_type,"company_id":coupon.company_id,"amount":coupon.amount,"minimum_spend":coupon.minimum_spend,"maximum_spend":coupon.maximum_spend,"user_type":coupon.user_type,"created_at":coupon.created_at,"expiry_date":coupon.expiry_date}
						required_data.append(coupon_record)

					record = {"statusCode":200, "message":'Coupon list !',"data":required_data}
					return JsonResponse(record, safe=False)

				else:
					record = {"statusCode":400, "message":'Coupon Not Available !'}
					return JsonResponse(record, safe=False)

			else:
				record = {"statusCode":400, "message":'User type is not non-registered !'}
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



#API to use when customer is not found
@csrf_exempt
def save_wpregisteration_data(request):

	output=[]
	if request.method == 'POST':
		form = WpRegisterationForm(request.POST, request.FILES)
		if form.is_valid():

			#print(request.POST['user_id'])
			#return HttpResponse(request.POST['user_id'])
			email = request.POST.get('email')
			username = request.POST.get('username')
			contact_name = request.POST.get('contact_name')

			request.POST._mutable = True
			request.POST['first_name'] = contact_name
			request.POST['last_name'] = contact_name

			try:
				check_email = User.objects.get(email = email)
				record = {"statusCode":400, "message":"email is already exist!"}
				output.append(record)
			except User.DoesNotExist:
				try:
					check_user = User.objects.get(username = username)
					record = {"statusCode":400, "message":"Username is already exist!"}
					output.append(record)
				except User.DoesNotExist:
					select_user = User(email = email, username = username,is_staff=1,is_active=1,first_name=username,last_name=username)
					password = form.cleaned_data['password']
					select_user.set_password(password)
					saved=select_user.save()
					data_saved1 = User.objects.latest('id')

					my_group = Group.objects.get(name=settings.NETWORK_GROUP)
					my_group.user_set.add(User.objects.get(pk = data_saved1.id))

					#User.objects.get(username = username)
					saved1 = form.save(commit=False)
					saved1.user_id = data_saved1.id
					saved = saved1.save()

					data_saved = Company.objects.latest('id')

					if data_saved:
						if data_saved.contact_name is None:
							contact_name =''
						else:
							contact_name = data_saved.contact_name

						if data_saved.phone_number is None:
							phone_number =''
						else:
							phone_number = data_saved.phone_number

						if data_saved.address is None:
							address =''
						else:
							address = data_saved.address

						if data_saved.address_line2 is None:
							address_line2 =''
						else:
							address_line2 = data_saved.address_line2

						if data_saved.town is None:
							town =''
						else:
							town = data_saved.town

						if data_saved.county is None:
							county =''
						else:
							county = data_saved.county

						if data_saved.post_code is None:
							post_code =''
						else:
							post_code = data_saved.post_code

						record = {"statusCode":200, "message":'saved company data successfully!'}
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

#Get reviews reply based on company rating review id(companyrating_id)
@csrf_exempt
def get_reviews_reply(request):
	output = []
	if request.method == 'POST':
		form = getReviewsReplyForm(request.POST)
		if form.is_valid():
			companyrating_id = request.POST['companyrating_id']

			reviewreply_data =[]
			reviewreply = CompanyReviewReply.objects.filter(review_id=companyrating_id).all()

			if reviewreply:
				try:
					companyReviewReply = CompanyReviewReply.objects.filter(review_id=companyrating_id)
					for reviewreply in companyReviewReply:
						reviewreply_record = {"id":reviewreply.id,"reply":reviewreply.reply,"created_at":datetime.strptime(str(reviewreply.created_at), '%Y-%m-%d').strftime('%d %b, %Y')}

						reviewreply_data.append(reviewreply_record)
						#required_data = { "reviewsreply" : reviewreply_data}
						record = {"statusCode":200, "message":'Reviews reply !',"data":reviewreply_data}
						return JsonResponse(record, safe=False)

				except CompanyReviewReply.DoesNotExist:
					companyReviewReply = []
					record = {"statusCode":400, "message":"Reviews reply not found !"}
					return JsonResponse(record, safe=False)
			else:
				record = {"statusCode":400, "message":"Reviews reply record not found !"}
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
def get_allergy(request):
	output = []
	if request.method == 'POST':
		customer_id = request.POST['customer_id']
		print(customer_id)
		try:
			#Allergy = Allergy.objects.all().select_related("customerallergy").values('allergy_id')
			#Allergy = Allergy.objects.all().select_related("CustomerAllergy__id__allergy_id").values('allergy_id')
			Allergy = Allergy.objects.filter(customerallergy__customer_id=customer_id).all()
		except Allergy.DoesNotExist:
			Allergy = []

		#return JsonResponse(Allergy, safe=False)
		items = []

		if len(Allergy) > 0:
			for allergyitem in Allergy:
				Allergy_record = {"id":allergyitem.id,"name":allergyitem.name}
				items.append(Allergy_record)

			record = {"statusCode":200, "message":'Purchase list !',"data":items}

			return JsonResponse(record, safe=False)
		else:
			pass

		return JsonResponse(output[0], safe=False)



@csrf_exempt
def get_allergy_item(request):
	output = []
	if request.method == 'POST':
		customer_id = request.POST['customer_id']
		try:
			#Allergy = Allergy.objects.all().select_related("customerallergy").values('allergy_id')
			#Allergy = Allergy.objects.all().select_related("CustomerAllergy__id__allergy_id").values('allergy_id')
			Allergy = Allergy.objects.filter().all()
		except Allergy.DoesNotExist:
			Allergy = []

		#return JsonResponse(Allergy, safe=False)
		items = []
		if(Allergy):
			for allergyitem in Allergy:
				Aller = CustomerAllergy.objects.filter(customer_id=customer_id, allergy_id=allergyitem.id)
				if len(Aller) > 0:
					Allergy_record = {"id":allergyitem.id,"name":allergyitem.name,'status':'selected'}
				else:
					Allergy_record = {"id":allergyitem.id,"name":allergyitem.name}

				items.append(Allergy_record)

		record = {"statusCode":200, "message":'Purchase list !',"data":items}

		return JsonResponse(record, safe=False)
	else:
		pass

	return JsonResponse(output[0], safe=False)


@csrf_exempt
def update_allergy_item(request):
	output = []
	record = []
	if request.method == 'POST':
		form = selectallergyForm(request.POST)
		if form.is_valid():
			allergy_id = request.POST['allergy_id']
			customer_id = request.POST['customer_id']
		else:
			record = {"statusCode":400, "message":"Form not valid!"}
			output.append(record)
			return JsonResponse(output[0], safe=False)


		try:
			t = CustomerAllergy.objects.filter(allergy_id = allergy_id, customer_id = customer_id)
			if len(t) > 0:
				print("asd")
				CustomerAllergy.objects.filter(allergy_id = allergy_id, customer_id = customer_id).delete()
				record = {"statusCode":200, "message":"Removed!"}
				output.append(record)
				return JsonResponse(output[0], safe=False)
			else:
				submit = CustomerAllergy(allergy_id = allergy_id, customer_id = customer_id, date = timezone.now() )
				submit.save()
				print("111111111")
				record = {"statusCode":200, "message":"Added!"}
				output.append(record)
				return JsonResponse(output[0], safe=False)

		except Exception as e:
			pass
	else:
		record = {"statusCode":400, "message":"Form is not valid!"}
		output.append(record)
		return JsonResponse(output[0], safe=False)
