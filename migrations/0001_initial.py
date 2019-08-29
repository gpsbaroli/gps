# Generated by Django 2.0.2 on 2019-02-08 10:14

import ckeditor.fields
import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import face_detection.models
import tinymce.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Allergy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('retailer_id', models.IntegerField(default=0, max_length=10)),
                ('date', models.DateField(auto_now_add=True, verbose_name='Created')),
            ],
        ),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('address', models.TextField(default='', validators=[face_detection.models.check_address])),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('is_deleted', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
            ],
            options={
                'verbose_name_plural': 'Branches',
                'db_table': 'branches',
            },
        ),
        migrations.CreateModel(
            name='BranchStaffCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('staff_code', models.CharField(default='', max_length=255)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Branch')),
            ],
            options={
                'verbose_name_plural': 'Branch Staff Codes',
                'db_table': 'branch_staff_codes',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.ImageField(default='', upload_to='company/')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Company Name')),
                ('contact_name', models.CharField(default='', max_length=50, verbose_name='Name')),
                ('phone_number', models.CharField(default='', help_text="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", max_length=17, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
                ('email', models.CharField(default='', max_length=255, unique=True, validators=[django.core.validators.EmailValidator()])),
                ('address', models.TextField(default='')),
                ('status', models.CharField(choices=[('a', 'Active'), ('s', 'Suspend')], default='a', max_length=15)),
                ('address_line2', models.TextField(blank=True, default='')),
                ('town', models.CharField(blank=True, default='', max_length=100)),
                ('county', models.CharField(blank=True, default='', max_length=100)),
                ('post_code', models.CharField(blank=True, default='', max_length=100)),
                ('company_website', models.CharField(blank=True, default='', help_text='https://www.example.com/', max_length=300)),
                ('company_phone_number', models.CharField(default=None, help_text="Contact Tel No must be entered in the format: '+999999999'. Up to 15 digits allowed.", max_length=17, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9, null=True)),
                ('user', models.OneToOneField(default=uuid.uuid1, limit_choices_to={'groups__name': 'Network Admin'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Network Admin')),
            ],
            options={
                'verbose_name_plural': 'Companies',
                'db_table': 'companies',
            },
        ),
        migrations.CreateModel(
            name='CompanyEmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', ckeditor.fields.RichTextField()),
                ('template_type', models.CharField(choices=[('purchase', 'Purchase Complete')], default='purchase', max_length=8)),
                ('company', models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'db_table': 'company_email_templates',
            },
        ),
        migrations.CreateModel(
            name='CompanyRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True, default='', null=True)),
                ('rating', models.IntegerField(blank=True, default=0, null=True)),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'verbose_name': 'Rating',
                'verbose_name_plural': 'Ratings',
                'db_table': 'company_ratings',
            },
        ),
        migrations.CreateModel(
            name='CompanySettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loyalty_on', models.BooleanField(default=False, help_text='Activate Loyalty Points', verbose_name='On')),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'db_table': 'company_settings',
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default='', upload_to='coupon/')),
                ('coupon_code', models.CharField(max_length=255, unique=True, verbose_name='Coupon Code')),
                ('description', models.TextField()),
                ('discount_type', models.CharField(choices=[('PERCENT', 'Percent Discount'), ('FIXED_CART', 'Fixed Cart Discount'), ('FIXED_PRODUCT', 'Fixed Product Discount')], max_length=13)),
                ('amount', models.FloatField(help_text='Please enter coupon amount', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Coupon Amount')),
                ('bid', models.FloatField(default=0, help_text='Please enter bid amount', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Coupon Bid')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('expiry_date', models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(2019, 2, 9))], verbose_name='Coupon expiry date')),
                ('minimum_spend', models.IntegerField(blank=True, help_text='Minimum cart value allowed to use this coupon, Leave blank for No Minimum', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Minimum cart value')),
                ('maximum_spend', models.IntegerField(blank=True, help_text='Maximum cart value allowed to use this coupon, Leave blank for No Maximum', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Maximum cart value')),
                ('coupon_count', models.IntegerField(blank=True, default=0, null=True)),
                ('user_type', models.CharField(choices=[('registered', 'registered'), ('non-registered', 'non-registered')], default='registered', max_length=14)),
                ('company', models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'db_table': 'coupons',
            },
        ),
        migrations.CreateModel(
            name='CouponDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(max_length=255)),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Coupon')),
            ],
            options={
                'db_table': 'coupondetail',
            },
        ),
        migrations.CreateModel(
            name='CustomerAllergy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Created')),
                ('allergy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Allergy')),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', tinymce.models.HTMLField(default='')),
                ('template_type', models.CharField(default='', max_length=254)),
            ],
            options={
                'verbose_name': 'Email Template',
                'verbose_name_plural': 'Email Templates',
            },
        ),
        migrations.CreateModel(
            name='FavouriteCompany',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True, default='', null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'verbose_name': 'Favourite Company',
                'verbose_name_plural': 'Favourite Companies',
                'db_table': 'favourite_companies',
            },
        ),
        migrations.CreateModel(
            name='LoyaltyManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loyalty_points', models.IntegerField()),
                ('loyalty_value', models.IntegerField(default=0, verbose_name='Loyalty Value (in €)')),
                ('benefit', models.TextField()),
                ('created_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created at')),
                ('company', models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'verbose_name_plural': 'Loyalty Manager',
                'db_table': 'loyalty_manager',
            },
        ),
        migrations.CreateModel(
            name='LoyaltyPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loyalty_points', models.IntegerField()),
                ('loyalty_balance', models.IntegerField()),
                ('loyalty_value', models.IntegerField(default=0)),
                ('tot_loyalty_value', models.IntegerField(default=0)),
                ('tx_type', models.CharField(choices=[('REDEEM', 'REDEEM'), ('PURCHASE', 'PURCHASE')], default='PURCHASE', max_length=1)),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('branch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_loyalty_points', to='face_detection.Branch')),
                ('company', models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
                ('loyalty_manager', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='face_detection.LoyaltyManager')),
            ],
            options={
                'verbose_name_plural': 'Loyalty Points',
                'db_table': 'loyalty_points',
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('purchase_summary', models.TextField(blank=True, default='')),
                ('coupon_code', models.CharField(blank=True, max_length=255, null=True, verbose_name='Coupon Code')),
                ('discount_type', models.CharField(blank=True, max_length=13, null=True)),
                ('discount_amount', models.IntegerField(default=0)),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('created_datetime_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created at')),
                ('removed_from', models.IntegerField(default=0)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tot_users', to='face_detection.Branch')),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Coupon')),
            ],
            options={
                'verbose_name_plural': 'Purchases',
                'db_table': 'purchases',
            },
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo', models.ImageField(default='', upload_to='settings/')),
                ('email', models.CharField(max_length=255, validators=[django.core.validators.EmailValidator()])),
                ('phone_number', models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+9999 99999'. Up to 20 digits allowed.", regex='^\\+?1?\\S\\d')])),
                ('address', models.TextField()),
                ('facebook', models.CharField(max_length=255, validators=[django.core.validators.URLValidator()])),
                ('twitter', models.CharField(max_length=255, validators=[django.core.validators.URLValidator()])),
            ],
            options={
                'verbose_name': 'Site Settings',
                'verbose_name_plural': 'Site Settings',
            },
        ),
        migrations.CreateModel(
            name='Useragree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_visible', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=1)),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('company', models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
            ],
            options={
                'db_table': 'useragree',
            },
        ),
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('PersistedFaceId', models.TextField()),
                ('FirstName', models.CharField(max_length=50)),
                ('LastName', models.CharField(max_length=50)),
                ('greeting_name', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('date_of_birth', models.DateField(blank=True, default=None, null=True, verbose_name='Date of birth')),
                ('Email', models.CharField(max_length=255, unique=True)),
                ('image', models.ImageField(upload_to='')),
                ('created_at', models.DateField(default=datetime.datetime.now, verbose_name='Created at')),
                ('user_pass', models.CharField(blank=True, max_length=255)),
                ('staff_code', models.CharField(default='', max_length=255)),
                ('is_active', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=1)),
                ('is_agree', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('is_deleted', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('updated_staffcode_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='Updated Staff code at')),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='user_images/')),
                ('added_by', models.CharField(choices=[('A', 'A'), ('NA', 'NA')], default='A', help_text='A -> Admin, NA -> Network Admin', max_length=2)),
                ('company', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_profile',
            },
        ),
        migrations.CreateModel(
            name='UsersSelectedCoupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.Coupon')),
                ('userdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData')),
            ],
            options={
                'verbose_name_plural': 'Selected Coupons',
                'db_table': 'selected_coupons',
            },
        ),
        migrations.AddField(
            model_name='useragree',
            name='userdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='purchase',
            name='userdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='loyaltypoint',
            name='purchase',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchase_loyalty_points', to='face_detection.Purchase'),
        ),
        migrations.AddField(
            model_name='loyaltypoint',
            name='userdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='favouritecompany',
            name='userdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='customerallergy',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='coupon',
            name='users',
            field=models.ManyToManyField(to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='companyrating',
            name='userdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='face_detection.UserData'),
        ),
        migrations.AddField(
            model_name='branch',
            name='company',
            field=models.ForeignKey(default=uuid.uuid1, on_delete=django.db.models.deletion.CASCADE, to='face_detection.Company'),
        ),
        migrations.AddField(
            model_name='branch',
            name='user',
            field=models.OneToOneField(default=uuid.uuid1, limit_choices_to={'groups__name': 'Store Manager'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Branch Manager'),
        ),
        migrations.AlterUniqueTogether(
            name='branch',
            unique_together={('name', 'company')},
        ),
    ]
