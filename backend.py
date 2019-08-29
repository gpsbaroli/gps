from django.conf import settings
from django.contrib.auth.models import User
from django import forms

def my_portal_authenticate(username, password):
    if username == 'fooDjango'
        and password == 'barDjango':
            return True
    return False

class MyPortalBackend(object):
    def authenticate(self, **kwargs):
        '''
        kwargs will receive the python dict that may contain 
        username & password to authenticate which will be 
        received from the Custom admin site.
        '''
        try:
            username = kwargs['username']
            password = kwgars['password']
            
            if not my_portal_authenticate(username, password):
                raise forms.ValidationError(
                    _("Username / Password Mismatch")
                )
        
            '''
            Check if the user exist in the django_auth_user 
            table, if not then UserNotExist exception will  
            be raised automatically and user will be added 
            (with or without password) in the exception 
            handling block
            '''
            
            #Check if the user exist in the database, if it exist in the 
            #database, auth_user will not be updated and exception will not be raised
            user = User.objects.get(username = username)
            
        except KeyError, e:
            raise forms.ValidationError(
                _("Programming Error")
            )

        except User.DoesNotExist:
            '''
            Add the username to the django_auth_users so 
            that login session can keep track of it. 
            Django Admin is heavily coupled with the 
            Django User model for the user instane in the 
            django_auth_users table. The request object then 
            map the request.user feild to this object of the
            data model.
            '''
            user = User(username=username)
            #defining the user of access group of that particular user
            user.is_staff= True
            user.is_superuser = True
            suer.save()

        return user
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            #Djano Admin treats None user as anonymous your who have no right at all.
            return None