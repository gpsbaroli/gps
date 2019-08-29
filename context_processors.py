from django.conf import settings
from face_detection.models import Company,Branch

def global_settings(request):
    # return any necessary values

    company_name = ''
    branch_name = ''

    if request.user.groups.filter(name=settings.NETWORK_GROUP).exists():
    	CompanyData = Company.objects.get(user_id =request.user)
    	company_name = CompanyData.name

    if request.user.groups.filter(name=settings.STORE_MANAGER_GROUP).exists():

    	BranchData = Branch.objects.get(user_id = request.user)
    	branch_name = BranchData.name
    	company_id = BranchData.company_id

    	CompanyData = Company.objects.get(pk = company_id)
    	company_name = CompanyData.name

    return {
        'CURRENCY_SYMBOL': settings.CURRENCY_SYMBOL,
        'SITE_TITLE': settings.SITE_TITLE,
        'ADMIN_GROUP': settings.ADMIN_GROUP,
        'NETWORK_GROUP': settings.NETWORK_GROUP,
        'STORE_MANAGER_GROUP': settings.STORE_MANAGER_GROUP,
        'COMPANY_NAME': company_name,
        'BRANCH_NAME': branch_name,
	}