from django.conf.urls import url, include

from . import views

from .models import *

from rest_framework import routers, serializers, viewsets


class StudentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Student
        fields = (
            'id', 'entry_nr', 'status',
            'short_name', 'name', 'first_name'
        )

class StudentListViewSet(viewsets.ModelViewSet):
    serializer_class = StudentListSerializer
    def get_queryset(self):
        queryset = Student.objects.all()
        status = self.request.query_params.get("status", None)
        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset.order_by('short_name')


class StudentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Student
        depth = 2
        fields = (
            'id', 'entry_nr', 'status',
            'short_name', 'name', 'first_name', 'dob', 'pob',
            'gender', 'denomination', 'citizenship', 'language',
            'first_day', 'last_day', 'first_enrollment', 'level_ofs', 'level_ref',
            'district_school', 'after_school_care', 'privacy_policy_agreement', 'vaccination_policy_agreement',
            'is_sibling', 'planned_enrollment_year', 'planned_enrollment_age', 'application_note', 'waitlist_position',
            'application_received', 'obligatory_conference', 'parent_dialog', 'confirmation_status', 'sitting',
            'address', 
            'guardians',
        )

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    def get_queryset(self):
        queryset = Student.objects.all()
        status = self.request.query_params.get("status", None)
        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset.order_by('short_name')


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ("street", "postal_code", "city", "alternative", "country")

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "name", "first_name", "kind", 
            "address", "phone_number", "cellphone_number", "email_address",
            "on_address_list", "is_teammember", "team_email_address"
                )

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()


router = routers.DefaultRouter()
router.register(r'students', StudentListViewSet, "student")
router.register(r'student', StudentViewSet, "student")
router.register(r'address', AddressViewSet, "address")
router.register(r'contact', ContactViewSet, "contact")

urlpatterns = [
#    url(r'^$', views.index, name='index'),
    url(r'^adressliste$', views.list_excel, name='adressliste'),
#    url(r'^students$', views.students_csv, name='students'),
    url(r'^studentcoversheet/(?P<student_id>\w+)/$', views.studentcoversheet, name='studentcoversheet'),
    url(r'^students_csv/(?P<status>\w+)/$', views.students_csv),
    url(r'^society_csv/$', views.society_csv),
    url(r'^level_report/$', views.level_report),
    url(r'^student_report/$', views.student_report),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
