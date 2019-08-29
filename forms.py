from django import forms
from .models import UserData,Branch,Coupon,UsersCoupon,Purchase,LoyaltyPoint,LoyaltyManager,BranchStaffCode,Company,UserProfile,Useragree, CompanySettings,CustomerAllergy
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib import admin
from django.contrib.auth.models import User

from ckeditor.fields import RichTextFormField


class CkEditorForm(forms.Form):
    content = RichTextFormField()

class CompanyLogoForm(forms.Form):
    id = forms.IntegerField()
    class Meta:
        model = Company

class ManagerLoginForm(forms.Form):
    user_type = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)
    class Meta:
        model = User
        fields = ('username','password')

class CheckStaffCodeForm(forms.Form):
    staff_code = forms.CharField(max_length=50,required=True)
    class Meta:
        model = BranchStaffCode
        fields = ('staff_code',)

class CustomerListForm(forms.Form):
    staff_code = forms.CharField(max_length=50,required=True)
    branch_id = forms.IntegerField(required=True)
    company_id = forms.IntegerField(required=True)
    #userdata_id = forms.IntegerField(required=True)
    class Meta:
        model = UserData
        fields = ('branch_id','staff_code','company_id')

class CustomerDeleteForm(forms.Form):
    userdata_id = forms.IntegerField(required=True)
    company_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('userdata_id','company_id')

class AllDeleteForm(forms.Form):
    userdata_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('userdata_id',)

class LoyaltyBenefitListForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    class Meta:
        model = LoyaltyManager
        fields = ('company_id',)

class PurchaseForm(forms.ModelForm):
    branch_id = forms.IntegerField(required=True)
    purchase_summary = forms.CharField(widget=forms.Textarea,required=False)
    userdata_id = forms.IntegerField(required=True)
    amount = forms.FloatField(required=True)
    coupon_id = forms.IntegerField(required=False)

    class Meta:
        model = Purchase
        fields = ('branch_id','userdata_id','amount','purchase_summary','coupon_id')

class RedeemForm(forms.ModelForm):
    branch_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    loyalty_manager_id = forms.IntegerField(required=True)

    class Meta:
        model = LoyaltyPoint
        fields = ('branch_id','userdata_id','loyalty_manager_id')

class CompanyAgreeForm(forms.ModelForm):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)

    class Meta:
        model = Useragree
        fields = ('company_id','userdata_id')

class InvisibleForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('company_id','userdata_id')

class CouponForm(forms.ModelForm):
    userdata_id = forms.IntegerField(required=True)
    coupon_id = forms.IntegerField(required=True)

    class Meta:
        model = UsersCoupon
        fields = ('userdata_id','coupon_id')

class CustomerStatusForm(forms.ModelForm):
    id = forms.IntegerField()
    class Meta:
        model = UserData
        fields = ('id',)

class ImageForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    staff_code = forms.CharField(max_length=50,required=True)
    image = forms.ImageField(required=True)
    class Meta:
        #model = UserData
        fields = ('image','staff_code','company_id')

class CustomerImageForm(forms.Form):
    image = forms.ImageField(required=True)
    class Meta:
        #model = UserData
        fields = ('image',)

class BranchStaffCodeForm(forms.ModelForm):
    staff_code = forms.CharField(max_length=50,required=True)
    branch_id = forms.ModelChoiceField(queryset=Branch.objects.all())
    class Meta:
        model = BranchStaffCode
        fields = ('staff_code','branch_id')

class CompanySettingsForm(forms.ModelForm):
    loyalty_on = forms.BooleanField(required=False, initial=False,label='Activate Loyalty Points')
    class Meta:
        model = CompanySettings
        fields = ('loyalty_on',)

class UserForm(forms.ModelForm):
    FirstName = forms.CharField(max_length=50,required=True)
    LastName = forms.CharField(max_length=50,required=True)
    staff_code = forms.CharField(max_length=50,required=True)
    Email = forms.CharField(max_length=255,required=True)
    is_agree = forms.CharField(max_length=255,required=True)
    greeting_name = forms.CharField(max_length=50,required=False)
    phone_number = forms.CharField(max_length=50,required=False)
    date_of_birth = forms.DateField(required=False)
    branch_id = forms.ModelChoiceField(queryset=Branch.objects.all())
    user_pass = forms.CharField(required=False)

    def clean_Email(self):
        """ Verifies that this email is not already in use """
        email = self.cleaned_data['Email'].lower() # Oh hey, this is important.
        try:
            UserData.objects.get(Email=email)
            raise forms.ValidationError('User data with this Email already exists.')
        except UserData.DoesNotExist:
            return email

    class Meta:
        model = UserData
        fields = ('FirstName','LastName','Email','image','staff_code','is_agree','greeting_name','phone_number','date_of_birth','user_pass')

class CustomerForm(forms.ModelForm):
    FirstName = forms.CharField(max_length=50,required=True)
    LastName = forms.CharField(max_length=50,required=True)
    Email = forms.CharField(max_length=255,required=True)
    greeting_name = forms.CharField(max_length=50,required=False)
    phone_number = forms.CharField(max_length=50,required=False)
    date_of_birth = forms.DateField(required=False)

    def clean_Email(self):
        """ Verifies that this email is not already in use """
        email = self.cleaned_data['Email'].lower() # Oh hey, this is important.

        try:
            UserData.objects.get(Email=email)
            raise forms.ValidationError('User data with this Email already exists.')
        except UserData.DoesNotExist:
            return email

    class Meta:
        model = UserData
        fields = ('FirstName','LastName','Email','image','greeting_name','phone_number','date_of_birth')

class UpdateCustomerForm(forms.Form):
    userdata_id = forms.IntegerField(required=True)
    FirstName = forms.CharField(max_length=50,required=True)
    LastName = forms.CharField(max_length=50,required=True)
    Email = forms.CharField(max_length=255,required=True)
    greeting_name = forms.CharField(max_length=50,required=False)
    phone_number = forms.CharField(max_length=50,required=False)
    date_of_birth = forms.DateField(required=False)

    def clean_Email(self):
        """ Verifies that this email is not already in use """
        email = self.cleaned_data['Email'].lower() # Oh hey, this is important.
        userdata_id = 0
        if 'userdata_id' in self.data:
            userdata_id = self.data['userdata_id']

        try:
            if userdata_id == 0:
                return email
            else:
                xyz = UserData.objects.filter(Email=email).exclude(id=userdata_id).count()

            if xyz > 0:
                raise forms.ValidationError('Customer with this Email already exists.')
            else:
                return email
        except UserData.DoesNotExist:
            return email

    class Meta:
        fields = ('FirstName','LastName','Email','greeting_name','phone_number','date_of_birth','userdata_id')

class CouponAdminForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset= UserData.objects.all(),
        widget=FilteredSelectMultiple(('users'), False, attrs={'rows':'10'}))

    class Meta:
        model = UsersCoupon
        fields = '__all__'

    #class Media:
    # Adding this javascript is crucial
        #js = ['admin/js/SelectFilter2.js','/admin/js/SelectFilter2.js']

class CouponAdmin(admin.ModelAdmin):
    form = CouponAdminForm

class updateNetworkAdminProfile(forms.Form):
    first_name = forms.CharField(max_length=50,required=True)
    last_name = forms.CharField(max_length=50,required=True)
    image = forms.ImageField(required=False)

    class Meta:
        fields = ('first_name','last_name','image')

class updateCompanyProfile(forms.Form):
    logo = forms.ImageField(required=True)

    class Meta:
        fields = ('logo')

class updateCompany(forms.Form):
    company_id = forms.IntegerField(required=True)
    user_id = forms.IntegerField(required=True)

    class Meta:
        fields = ('company_id','user_id')

class getCompaniesForm(forms.Form):
    userdata_id = forms.IntegerField(required=True)
    company_type = forms.CharField(max_length=2,required=True)

    class Meta:
        fields = ('userdata_id','company_type')

class getBranchesForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    latitude = forms.DecimalField(max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6)
    class Meta:
        fields = ('company_id','userdata_id')

class getLoyaltyForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('company_id',)

class getCompanyReviewsForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('company_id',)

class getCustomerCouponForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('company_id','userdata_id')

class getPurchasesForm(forms.Form):
    branch_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)

    class Meta:
        fields = ('branch_id','userdata_id')

class CompanyRatingForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    #message = forms.CharField(widget=forms.Textarea,required=False)
    rating = forms.IntegerField(required=True)

    class Meta:
        fields = ('company_id','userdata_id','rating')

class CompanyFavouriteForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    message = forms.CharField(widget=forms.Textarea,required=False)

    class Meta:
        fields = ('company_id','userdata_id','message')

class CompanyReviewForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    review = forms.CharField(widget=forms.Textarea,required=True)

    class Meta:
        fields = ('company_id','userdata_id','review')

class SelectCouponsForm(forms.Form):
    userdata_id = forms.IntegerField(required=True)
    coupon_id = forms.IntegerField(required=True)

    class Meta:
        fields = ('userdata_id','coupon_id')

class SelectNonRegisteredCouponsForm(forms.Form):
    user_type = forms.CharField(max_length=16,required=False)
    class Meta:
        #fields = ('id','coupon_code','description','discount_type','amount','created_at','expiry_date','minimum_spend','maximum_spend','company','image','user_type')
        fields = ('user_type')

class getBranchesNonRegisteredForm(forms.Form):
    latitude = forms.DecimalField(max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6)
    class Meta:
        fields = ('company_id','userdata_id')

class increaseCouponCountForm(forms.Form):
    coupon_id = forms.IntegerField(required=True)
    device_id = forms.CharField(required=True)
    created_at = forms.DateField(required=False)
    class Meta:
        fields = ('coupon_id','device_id','created_at')

class getcompanylocrevloyalityForm(forms.Form):
    company_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('company_id')

class GetNonRegisteredCouponsForm(forms.Form):
    user_type = forms.CharField(max_length=16,required=False)
    #company_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('user_type')

class SelectCouponDetailForm(forms.Form):
    coupon_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    class Meta:
        fields = ('coupon_id','userdata_id')

class EmailLoginForm(forms.Form):
    Email = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)
    class Meta:
        model = UserData
        fields = ('Email','password')


class WpRegisterationForm(forms.ModelForm):
    #logo = forms.ImageField(required=False)
    name = forms.CharField(max_length=50)
    contact_name = forms.CharField(max_length=50,required=False)
    phone_number = forms.CharField(max_length=17,required=False)
    email = forms.CharField(max_length=255,required=True)
    address = forms.CharField(required=False)
    #user_id = forms.IntegerField(required=True)
    status = forms.CharField( max_length=1,required=False)
    #address_line1 = forms.CharField(max_length=255,required=False)
    address_line2 = forms.CharField(max_length=255,required=False)
    town = forms.CharField(max_length=50,required=False)
    county = forms.CharField(max_length=50,required=False)
    post_code = forms.CharField(max_length=50,required=False)
    company_phone_number = forms.CharField(max_length=17,required=False)
    company_website = forms.CharField(max_length=300,required=False)
    #latitude = forms.DecimalField(max_digits=9, decimal_places=6)
    #longitude = forms.DecimalField(max_digits=9, decimal_places=6)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)

    class Meta:
        model = Company
        fields = ('name','contact_name','phone_number','email','address','status','address_line2','town','county','post_code','company_website','company_phone_number','username','password')


class CompanyRegisteredAgreeForm(forms.ModelForm):
    coupon_id = forms.IntegerField(required=True)
    userdata_id = forms.IntegerField(required=True)
    class Meta:
        model = UsersCoupon
        fields = ('coupon_id','userdata_id')

class selectallergyForm(forms.ModelForm):
    allergy_id = forms.IntegerField(required=True)
    customer_id = forms.IntegerField(required=True)
    class Meta:
        model = CustomerAllergy
        fields = ('allergy_id','customer_id')
