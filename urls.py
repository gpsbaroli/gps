from django.conf.urls import url
from . import views
from django.conf.urls import include

urlpatterns = [
    url(r'^facedetect/$', views.facedetect, name="facedetect"),
    url(r'^createFaceList/$', views.createFaceList, name="createFaceList"),
    url(r'^addFacetoList/$', views.addFacetoList, name="addFacetoList"),
    url(r'^getFaceList/$', views.getFaceList, name="getFaceList"),
    url(r'^FindSimilarinFaceList/$', views.FindSimilarinFaceList, name="FindSimilarinFaceList"),
    url(r'^TrainFaceList/$', views.TrainFaceList, name="TrainFaceList"),
    url(r'^model_form_upload/$', views.model_form_upload, name="model_form_upload"),
    # url(r'^send_image/$', views.send_image, name="send_image"),
    url(r'^save_user_data/$', views.save_user_data, name="save_user_data"),
    url(r'^active_customers/$', views.active_customers, name="active_customers"),
    url(r'^manager_login/$', views.manager_login, name="manager_login"),
    # url(r'^change_customer_status/$', views.change_customer_status, name="change_customer_status"),
    url(r'^purchase/$', views.purchase, name="purchase"),
    url(r'^redeem/$', views.redeem, name="redeem"),
    url(r'^loyalty_benefits/$', views.loyalty_benefits, name="loyalty_benefits"),
    url(r'^validate_staff_code/$', views.validate_staff_code, name="validate_staff_code"),
    # url(r'^apply_coupon/$', views.apply_coupon, name="apply_coupon"),
    url(r'^delete_customer/$', views.delete_customer, name="delete_customer"),
    url(r'^agree_tc/$', views.agree_tc, name="agree_tc"),
    url(r'^check_customer_status/$', views.check_customer_status, name="check_customer_status"),
    url(r'^company_logo/$', views.company_logo, name="company_logo"),
    url(r'^change_company/$', views.change_company, name="change_company"),
    url(r'^get_companies/$', views.get_companies, name="get_companies"),
    url(r'^get_company_branches/$', views.get_company_branches, name="get_company_branches"),
    url(r'^get_customer_purchases/$', views.get_customer_purchases, name="get_customer_purchases"),
    url(r'^get_company_loyalty_points/$', views.get_company_loyalty_points, name="get_company_loyalty_points"),
    #url(r'^get_company_coupons/$', views.get_company_coupons, name="get_company_coupons"),
    url(r'^rate_company/$', views.rate_company, name="rate_company"),
    url(r'^make_favourite_company/$', views.make_favourite_company, name="make_favourite_company"),
    url(r'^customer_image_upload/$', views.customer_image_upload, name="customer_image_upload"),
    url(r'^save_customer_data/$', views.save_customer_data, name="save_customer_data"),
    url(r'^update_customer_data/$', views.update_customer_data, name="update_customer_data"),
    url(r'^review_company/$', views.review_company, name="review_company"),
    url(r'^set_invisible/$', views.set_invisible, name="set_invisible"),
    url(r'^get_branch_managers/$', views.get_branch_managers, name="get_branch_managers"),
    url(r'^select_coupons/$', views.select_coupons, name="select_coupons"),
    url(r'^get_company_reviews/$', views.get_company_reviews, name="get_company_reviews"),
    url(r'^delete_from_all_companies/$', views.delete_from_all_companies, name="delete_from_all_companies"),
    url(r'^select_nonregistered_coupons/$', views.select_nonregistered_coupons, name="select_nonregistered_coupons"),
    url(r'^get_company_branches_nonregistered/$', views.get_company_branches_nonregistered, name="get_company_branches_nonregistered"),
    url(r'^get_nonregistered_coupons/$', views.get_nonregistered_coupons, name="get_nonregistered_coupons"),
    url(r'^increaseCouponCount/$', views.increaseCouponCount, name="increaseCouponCount"),
    url(r'^get_company_loc_rev_loyality/$', views.get_company_loc_rev_loyality, name="get_company_loc_rev_loyality"),
    url(r'^select_coupon_detail/$', views.select_coupon_detail, name="select_coupon_detail"),
    url(r'^set_visible/$', views.set_visible, name="set_visible"),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^email_login/$', views.email_login, name="email_login"),
    url(r'^save_wpregisteration_data/$', views.save_wpregisteration_data, name="save_wpregisteration_data"),
    url(r'^coupon_is_registered/$', views.coupon_is_registered, name="coupon_is_registered"),
    url(r'^get_reviews_reply/$', views.get_reviews_reply, name="get_reviews_reply"),
    url(r'^get_allergy_item/$', views.get_allergy_item, name="get_allergy_item"),
    url(r'^update_allergy_item/$', views.update_allergy_item, name="update_allergy_item"),
    url(r'^get_allergy/$', views.get_allergy, name="get_allergy"),
    #url(r'^cadmin/', include('cadmin.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
]
