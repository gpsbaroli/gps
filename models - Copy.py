from django.db import models
from django.utils.safestring import mark_safe
import uuid
from django.core.mail import EmailMessage
from datetime import datetime
#import os.path
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.models import User
User._meta.get_field('email').blank = False
User._meta.get_field('email')._unique  = True
User._meta.get_field('first_name').blank = False
User._meta.get_field('last_name').blank = False
User._meta.get_field('groups').blank = False
from django.core.validators import MaxValueValidator, MinValueValidator,URLValidator,RegexValidator,EmailValidator
from django.utils import timezone
from ckeditor.fields import RichTextField
from datetime import datetime
from django.forms.fields import CheckboxInput
from smart_selects.db_fields import ChainedForeignKey
from django.dispatch import receiver
from django.db.models.signals import post_save
import json as simplejson
import urllib
from django.core.validators import ValidationError
from enumfields import EnumField, Enum
# Create your models here.
class Setting(models.Model):
    logo = models.ImageField(upload_to='settings/',default="")
    email = models.CharField(max_length=255,validators=[EmailValidator()])
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True) # validators should be a list
    address = models.TextField()
    facebook = models.CharField(max_length=255,validators=[URLValidator()])
    twitter = models.CharField(max_length=255,validators=[URLValidator()])

    def image_tag(self):
        if self.logo:
            if default_storage.exists(self.logo.path):
                return mark_safe('<img src="{}" width="100" height="100" />'.format(self.logo.url))
            else:
                return mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        else:
            return 'No image'
    image_tag.short_description = 'Logo'

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__ (self):
        return self.email

class EmailTemplate(models.Model):
    subject = models.CharField(max_length=255)
    body = RichTextField()
    template_type = models.CharField(max_length=255, default="")

    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"

    def __str__ (self):
        return self.subject

class CompanyEmailTemplate(models.Model):
    subject = models.CharField(max_length=255)
    body = RichTextField()
    TEMPLATE_TYPE = (
        ( 'purchase','Purchase Complete'),
        ('extra','extra')
    )
    template_type = models.CharField(
        max_length=8,
        choices=TEMPLATE_TYPE,
        default='purchase',)
    #template_type = models.CharField(max_length=255, default="purchase")
    company = models.ForeignKey('Company', on_delete=models.CASCADE, default=uuid.uuid1)

    class Meta:
        db_table = "company_email_templates"
        #unique_together = ('template_type', 'company',)

    def __str__ (self):
        return self.subject

class UserData(models.Model):

    PersistedFaceId = models.TextField()
    FirstName = models.CharField(max_length=50)
    LastName = models.CharField(max_length=50)
    greeting_name = models.CharField(max_length=50,blank=True,null=True,default=None)
    phone_number = models.CharField(max_length=50,blank=True,null=True,default=None)
    date_of_birth = models.DateField(("Date of birth"),blank=True,null=True,default=None)
    Email = models.CharField(max_length=255,unique=True)
    image = models.ImageField(upload_to='')
    created_at = models.DateField(("Created at"), default=datetime.now)
    #branch = models.ForeignKey('Branch', on_delete=models.CASCADE, related_name='users')
    staff_code = models.CharField(max_length=255, default="")
    STATUS_TYPE = (
        ( 'Y','Y'),
        ( 'N','N')
    )
    is_active = models.CharField(
        max_length=1,
        choices=STATUS_TYPE,
        default='Y',)
    AGREE = (
        ( 'Y','Y'),
        ( 'N','N')
    )
    is_agree = models.CharField(
        max_length=1,
        choices=AGREE,
        default='N',)
    DELETED = (
        ( 'Y','Y'),
        ( 'N','N')
    )
    is_deleted = models.CharField(
        max_length=1,
        choices=DELETED,
        default='N',)

    updated_staffcode_at = models.DateTimeField(("Updated Staff code at"), default=datetime.now)

    def image_tag(self):
        if self.image:
            if default_storage.exists(self.image.path):
                return mark_safe('<img src="{}" width="100" height="100" />'.format(self.image.url))
            else:
                return mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        else:
            return 'No image'
    image_tag.short_description = 'Image'

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return '%s %s' % (self.FirstName, self.LastName)

def check_address(location):
    googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'
    query = location.encode('utf-8')
    params = {
        'address': query,
        'sensor': "false"
    }
    url = googleGeocodeUrl + urllib.parse.urlencode(params)
    json_response = urllib.request.urlopen(url)
    response = simplejson.loads(json_response.read())
    if response['results']:
        pass
    else:
        print(response)
        raise ValidationError("Please enter a valid address.")

class Branch(models.Model):
    name = models.CharField(max_length=50)
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=uuid.uuid1, limit_choices_to={'groups__name': settings.STORE_MANAGER_GROUP},verbose_name="Branch Manager")
    company = models.ForeignKey('Company', on_delete=models.CASCADE, default=uuid.uuid1)
    address = models.TextField(default="",validators=[check_address])
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    DELETED = (
        ( 'Y','Y'),
        ( 'N','N')
    )
    is_deleted = models.CharField(
        max_length=1,
        choices=DELETED,
        default='N',)


    def save(self):
        location = "%s" % (self.address)

        #if not self.latitude or not self.longitude:
        latlng = self.geocode(location)
        latlng = latlng.split(',')
        self.latitude = latlng[0]
        self.longitude = latlng[1]

        super(Branch, self).save()

    def geocode(self, location):
        googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'
        query = location.encode('utf-8')
        params = {
            'address': query,
            'sensor': "false"
        }
        url = googleGeocodeUrl + urllib.parse.urlencode(params)
        json_response = urllib.request.urlopen(url)
        response = simplejson.loads(json_response.read())
        if response['results']:
            location = response['results'][0]['geometry']['location']
            latitude, longitude = location['lat'], location['lng']
            return "%s,%s" % (latitude, longitude)
        else:
            print(response)
            return "%s,%s" % (0.00, 0.00)
            #return ','

    def __str__(self):
        return self.name

    class Meta:
        db_table = "branches"
        verbose_name_plural = "Branches"
        unique_together = ('name', 'company',)

class BranchStaffCode(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    staff_code = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.staff_code

    class Meta:
        db_table = "branch_staff_codes"
        verbose_name_plural = "Branch Staff Codes"

class Statuscom(Enum):
    Active = 'a'
    Inactive = 'i'
    Suspend = 's'

class Company(models.Model):
    logo = models.ImageField(upload_to='company/',default="")
    name = models.CharField(max_length=50,unique=True,verbose_name="Company Name")
    contact_name = models.CharField(max_length=50,verbose_name="Name",default="")
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex],unique=True, max_length=17, blank=False,default="",help_text="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.") # validators should be a list
    email = models.CharField(max_length=255,unique=True,validators=[EmailValidator()],default="")
    address = models.TextField(default="")
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=uuid.uuid1, limit_choices_to={'groups__name': settings.NETWORK_GROUP},verbose_name="Network Admin")
    status = EnumField(Statuscom, max_length=1,default="a")

    def image_tag(self):
        if self.logo:
            if default_storage.exists(self.logo.path):
                return mark_safe('<img src="{}" width="100" height="100" />'.format(self.logo.url))
            else:
                return mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        else:
            return 'No image'
    image_tag.short_description = 'Logo'

    def __str__(self):
        return self.name

    class Meta:
        db_table = "companies"
        verbose_name_plural = "Companies"



class Coupon(models.Model):
    list_per_page = 20
    COUPON_TYPE = (
        ( 'PERCENT','Percent Discount'),
        ( 'FIXED_CART','Fixed Cart Discount'),
        ( 'FIXED_PRODUCT','Fixed Product Discount')
    )
    image = models.ImageField(upload_to='coupon/',default="")
    coupon_code = models.CharField(("Coupon Code"), unique=True, blank=False, null=False,max_length=255)
    description = models.TextField()
    discount_type = models.CharField(max_length=13,choices=COUPON_TYPE)
    amount = models.FloatField(("Coupon Amount"),help_text=("Please enter coupon amount"),validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(("Created at"), auto_now_add=True)
    expiry_date = models.DateField(("Coupon expiry date"), blank=False, null=False,validators=[MinValueValidator(timezone.now().date()+ timezone.timedelta(days=1))])
    minimum_spend = models.IntegerField(("Minimum cart value"), blank=True,null=True, help_text=("Minimum cart value allowed to use this coupon, Leave blank for No Minimum"),validators=[MinValueValidator(1)])
    maximum_spend = models.IntegerField(("Maximum cart value"), blank=True, null=True, help_text=("Maximum cart value allowed to use this coupon, Leave blank for No Maximum"),validators=[MinValueValidator(1)])
    users = models.ManyToManyField('UserData', through='UsersCoupon')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=uuid.uuid1)


    def image_tag(self):
        if self.image:
            if default_storage.exists(self.image.path):
                return mark_safe('<img src="{}" width="100" height="100" />'.format(self.image.url))
            else:
                return mark_safe('<img src="'+settings.STATIC_URL+'face_detection/no-image.jpg" width="100" height="100" />')
        else:
            return 'No image'
    image_tag.short_description = 'Image'

    def display_users(self):
        return self.users.all().count()
    display_users.short_description = 'Customers'
    display_users.allow_tags = True

    class Meta:
        db_table = "coupons"
    def __str__(self):
        return self.coupon_code

class UsersCoupon(models.Model):
    coupon = models.ForeignKey('Coupon', on_delete=models.CASCADE)
    userdata = models.ForeignKey('UserData', on_delete=models.CASCADE)
    # SELECTED = (
    # 	('Y','Y'),
    # 	('N','N')
    # 	)
    # is_selected = models.CharField(max_length=2, choices=SELECTED, default='N')
    # REDEEMED = (
    #     ('Y', 'Y'),
    #     ('N', 'N')
    # )
    # is_redeemed = models.CharField(max_length=1,choices=REDEEMED,default='N')
    class Meta:
        verbose_name_plural = "Customers"
        auto_created = True

class UsersSelectedCoupon(models.Model):
    coupon = models.ForeignKey('Coupon', on_delete=models.CASCADE)
    userdata = models.ForeignKey('UserData', on_delete=models.CASCADE)

    class Meta:
        db_table = "selected_coupons"
        verbose_name_plural = "Selected Coupons"

def get_first_name(self):
    return '%s %s (%s)' % (self.first_name, self.last_name, self.username)

User.add_to_class("__str__", get_first_name)

class Purchase(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='tot_users')
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    amount = models.FloatField(blank=False)
    purchase_summary = models.TextField(blank=True,default="")
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank=True, null=True)
    coupon_code = models.CharField(("Coupon Code"), blank=True, null=True,max_length=255)
    discount_type = models.CharField(max_length=13, blank=True, null=True)
    discount_amount = models.IntegerField( default=0)
    created_at = models.DateField(("Created at"), default=datetime.now)
    created_datetime_at = models.DateTimeField(("Created at"), default=datetime.now)
    class Meta:
        db_table = "purchases"
        verbose_name_plural = "Purchases"

class Useragree(models.Model):
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=uuid.uuid1)
    VISIBILITY = (
        ('Y', 'Y'),
        ('N', 'N')
    )
    is_visible = models.CharField(max_length=1,choices=VISIBILITY,default='Y')
    created_at = models.DateField(("Created at"), default=datetime.now)
    class Meta:
        db_table = "useragree"

class CompanySettings(models.Model):
    company   = models.OneToOneField(Company, on_delete=models.CASCADE)
    loyalty_on = models.BooleanField(('On'), default=False,
            help_text=('Decide whether or not loyalty points will be on'))
    class Meta:
        db_table = "company_settings"

class LoyaltyManager(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=uuid.uuid1)
    loyalty_points = models.IntegerField(blank=False)
    loyalty_value = models.IntegerField(blank=False, default=0, verbose_name='Loyalty Value (in '+settings.CURRENCY_SYMBOL+')',)
    benefit = models.TextField(blank=False)
    created_at = models.DateTimeField(("Created at"), default=datetime.now)

    def __str__(self):
        return '%s (%s points)' % (self.benefit, self.loyalty_points)

    class Meta:
        db_table = "loyalty_manager"
        verbose_name_plural = "Loyalty Manager"

class CompanyRating(models.Model):
	userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
	company = models.ForeignKey(Company, on_delete=models.CASCADE)
	message = models.TextField(blank=True,default="", null=True )
	rating = models.IntegerField(blank=True,default=0, null=True)
	created_at = models.DateField(("Created at"), default=datetime.now)

	class Meta:
		db_table = "company_ratings"
		verbose_name = "Rating"
		verbose_name_plural = "Ratings"

class FavouriteCompany(models.Model):
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    message = models.TextField(blank=True,default="", null=True )

    class Meta:
        db_table = "favourite_companies"
        verbose_name = "Favourite Company"
        verbose_name_plural = "Favourite Companies"

# class ReviewCompany(models.Model):
# 	userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
# 	company = models.ForeignKey(Company, on_delete=models.CASCADE)
# 	review = models.TextField(blank=True,default="", null=True )

# 	class Meta:
# 		db_table = "review_companies"
# 		verbose_name = "Review Company"
# 		verbose_name_plural = "Review Companies"


class LoyaltyPoint(models.Model):

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,null=True,related_name='branch_loyalty_points')
    userdata = models.ForeignKey(UserData, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE,null=True,related_name='purchase_loyalty_points')
    loyalty_manager = models.ForeignKey(LoyaltyManager, on_delete=models.CASCADE,null=True)
    loyalty_points = models.IntegerField(blank=False)
    loyalty_balance = models.IntegerField(blank=False)
    loyalty_value = models.IntegerField(blank=False,default=0)
    tot_loyalty_value = models.IntegerField(blank=False,default=0)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=uuid.uuid1)

    REDEEMED = (
        ('REDEEM', 'REDEEM'),
        ('PURCHASE', 'PURCHASE')
    )

    tx_type = models.CharField(
        max_length=1,
        choices=REDEEMED,
        default='PURCHASE',)

    #created_at = models.DateTimeField(("Created at"), default=datetime.now)
    created_at = models.DateField(("Created at"), default=datetime.now)

    class Meta:
        db_table = "loyalty_points"
        verbose_name_plural = "Loyalty Points"



class UserProfile(models.Model):
    user   = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='user_images/')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=None, blank=True, null=True)
    ADDED_BY = (
        ( 'A','A'),
        ( 'NA','NA')
    )
    added_by = models.CharField(
        max_length=2,
        choices=ADDED_BY,
        default='A',help_text=("A -> Admin, NA -> Network Admin"))

    class Meta:
        db_table = "user_profile"

@receiver(post_save, sender = User)
def my_callback1(sender, instance, created, **kwargs):
    if created:
        import inspect
        records =[]
        for frame_record in inspect.stack():
            records.append(frame_record[3])
            if frame_record[3]=='get_response':
                request = frame_record[0].f_locals['request']
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                username = request.POST.get('username')
                email = request.POST.get('email')
                password1 =  'sss'
                password2 = request.POST.get('password2')

                if email != None:
                    templates = EmailTemplate.objects.get(pk=3)
                    html_content = templates.body
                    from_email   = settings.DEFAULT_FROM_EMAIL

                    html_content = html_content.replace("{name}",first_name+' '+last_name)
                    html_content = html_content.replace("{username}",username)
                    html_content = html_content.replace("{password}",password1)


                    message      = EmailMessage(str(templates.subject), html_content, from_email, [email])
                    message.content_subtype = "html"
                    message.send()
                break

@receiver(post_save, sender = Coupon)
def my_callback(sender, instance, created, **kwargs):
    import inspect
    if created:
        records =[]
        for frame_record in inspect.stack():
            records.append(frame_record[3])
            if frame_record[3]=='get_response':
                request = frame_record[0].f_locals['request']
                coupon_code = request.POST.get('coupon_code')
                description = request.POST.get('description')
                expiry_date = request.POST.get('expiry_date')
                users = request.POST.get('users')
                if users != None:
                    user_detail = UserData.objects.get(pk=int(users))
                    email = user_detail.Email
                    first_name = user_detail.FirstName
                    last_name = user_detail.LastName
                    greeting_name = user_detail.greeting_name
                    templates = EmailTemplate.objects.get(pk=2)
                    html_content = templates.body
                    from_email   = settings.DEFAULT_FROM_EMAIL

                    if greeting_name is None:
                        name = first_name+' '+last_name
                    else:
                        name = greeting_name

                    current_user = request.user
                    company = Company.objects.get(user_id =current_user)

                    html_content = html_content.replace("{greeting_name}",name)
                    html_content = html_content.replace("{retailer}",company.name)
                    html_content = html_content.replace("{coupon_code}",coupon_code)
                    html_content = html_content.replace("{description}",description)
                    html_content = html_content.replace("{expiry_date}",datetime.strptime(str(expiry_date), '%Y-%m-%d').strftime('%d %b, %Y'))

                    message      = EmailMessage(str(templates.subject), html_content, from_email, [email])
                    message.content_subtype = "html"
                    message.send()
                break
