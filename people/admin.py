from django.contrib import admin
from django import urls
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from .models import *
from django import forms

from datetime import date

from django.utils.encoding import force_text
from django.db.models import F, ExpressionWrapper, IntegerField

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages

# set a default filter option [https://stackoverflow.com/questions/851636/default-filter-in-django-admin]
class DefaultListFilter(admin.SimpleListFilter):
    all_value = '_all'

    def default_value(self):
        raise NotImplementedError()

    def queryset(self, request, queryset):
        if self.parameter_name in request.GET and request.GET[self.parameter_name] == self.all_value:
            return queryset

        if self.parameter_name in request.GET:
            return queryset.filter(**{self.parameter_name:request.GET[self.parameter_name]})

        return queryset.filter(**{self.parameter_name:self.default_value()})

    def choices(self, cl):
        yield {
            'selected': self.value() == self.all_value,
            'query_string': cl.get_query_string({self.parameter_name: self.all_value}, []),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_text(lookup) or (self.value() == None and force_text(self.default_value()) == force_text(lookup)),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

class StudentStatusFilter(DefaultListFilter):
    title = _('Status')
    parameter_name = 'status__exact'

    def lookups(self, request, model_admin):
        return Student.STATUS_CHOICES

    def default_value(self):
        return "active"

class StudentPlannedEnrollmentFilter(DefaultListFilter):
    title = _('Enrollment Year')
    parameter_name = 'planned_enrollment_year'

    def lookups(self, request, model_admin):
        years = []
        today = date.today();
        current_year = today.year
        for i in range(0,5):
            y = "%i" % (current_year + i)
            years.append((y, _(y)));
        return years;

    def queryset(self, request, queryset):
        if self.value() and self.value() != "_all":
            return queryset.filter(planned_enrollment_year__contains=self.value())

        return queryset


    def default_value(self):
        return "_all"


class NoteForm(forms.ModelForm):
    class Meta:
        widgets = {"content": forms.Textarea(attrs={"rows": 4, "cols":50 })}

class NoteInline(admin.TabularInline):
    extra = 0
    model = Note
    form = NoteForm
    fields = ("content",)



class StudentAdmin(admin.ModelAdmin):


    model = Student
    def get_list_display(self, request, obj=None):
        status = request.GET.get("status__exact", "active")

        if status == "active":
            return ("name", "first_name", "calc_level", "first_day")
        elif status == "in_admission_procedure":
            return ("name", "first_name", "entry_nr", "get_gender_short", "is_sibling", "application_received", "obligatory_conference", "parent_dialog", "confirmation_status", "sitting", "remark")
        elif status == "intent_declared":
            return ("name", "first_name", "planned_enrollment_year", "planned_enrollment_age", "is_sibling", "remark")
        elif status == "waitlisted":
            return ("name", "first_name", "dob", "calc_level", "remark")
        elif status == "alumnus":
            return ("name", "first_name", "last_day", "remark")
        elif status == "cancelled":
            return ("name", "first_name", "planned_enrollment_year", "planned_enrollment_age", "remark")
        elif status == "special":
            return ("name", "first_name", "first_day", "last_day", "remark")

        return ("entry_nr", "name", "first_name", "status", "remark")

    def get_list_filter(self, request, obj=None): 
        status = request.GET.get("status__exact", "active")

        if status == "waitlisted" or status == "intent_declared" or status == "in_admission_procedure":
            return (StudentStatusFilter,StudentPlannedEnrollmentFilter,)

        return (StudentStatusFilter,)

    actions = ["email_list","change_status"];

    search_fields = ["entry_nr", "first_name", "name"]
    filter_horizontal = ("guardians",)
    readonly_fields = ("guardians_links","calc_level","cover_sheet_link")
    inlines = [
       NoteInline,
    ]

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
                (None, {
                    "fields": ("short_name", "name", "first_name", "status", "remark", "dob", "pob", "address", "guardians_links")
                }),)

        if not obj or (obj and (obj.status == "in_admission_procedure" or obj.status == "intent_declared" or obj.status == "cancelled")):
            fieldsets += ((_("Application"), {
                        "fields":(
                        "application_received", "obligatory_conference", "parent_dialog", "confirmation_status", "sitting",
                        "planned_enrollment_year", "planned_enrollment_age", "is_sibling"
                    )}),)


        if obj and obj.status == "waitlisted":
            fieldsets += ((_("Waitlist"), {
                        "fields":(
                        "waitlist_position", 
                        "planned_enrollment_year", "planned_enrollment_age", "is_sibling"
                    )}),)

        fieldsets += (
                (_("Class Level"), {
                    "classes":("collapse",),
                    "fields":(
                    "first_day", "last_day",
                    "first_enrollment",
                    "level_ofs", "level_ref",
                    "calc_level"
                )}),
                (_("Formalities"), {
                    "classes":("collapse",),
                    "fields":(
                    "entry_nr",
                    "gender", "language",
                    "citizenship", "denomination",
                    "after_school_care", "district_school",
                    "privacy_policy_agreement", "vaccination_policy_agreement"
                )}),
                (_("Edit Guardians"), {
                    "classes":("collapse",),
                    "fields": (
                    "guardians",
                )}),
                (None, {
                        "fields":("cover_sheet_link",)
                    }),
            )

        return fieldsets;

    def cover_sheet_link(self, obj):
        return format_html('<a class="button" href="/people/studentcoversheet/%s">%s</a>' % (obj.id, _("Print")));
    cover_sheet_link.short_description = _("Cover Sheet")
    cover_sheet_link.allow_tags = True

    def guardians_links(self, obj):
        guardians = obj.guardians.all()

        links = [];
        for guardian in guardians:
        	change_url = urls.reverse("admin:people_contact_change", args=(guardian.id,))
        	links.append('<a href="%s">%s</a>' % (change_url, guardian))
        return format_html("<br>".join(links));
    guardians_links.short_description = _("Guardians")

    def get_full_name(self, obj):
        return obj.first_name + " " + obj.name;
    get_full_name.short_description = _("Name")

    def get_gender_short(self, obj):
        return obj.gender;
    get_gender_short.short_description = _("Gender")

    def calc_level(self, obj):
    	if not obj.level_ref or not obj.level_ofs:
    		return "N/A"
    	today = date.today();
    	current_year = today.year-1 if today.month < 8 else today.year
    	level =  current_year - (int(obj.level_ref) - int(obj.level_ofs))
    	return(level)
        
    calc_level.short_description = _("Class Level")

    # to order by calculated level [https://stackoverflow.com/questions/42659741/django-admin-enable-sorting-for-calculated-fields]
    calc_level.admin_order_field = 'level'
    def get_queryset(self, request):
        qs = super(StudentAdmin, self).get_queryset(request)
        qs = qs.annotate(level=ExpressionWrapper(F("level_ref")-F("level_ofs"), output_field=IntegerField())).order_by("level")
        return qs;

    # Bulk-change status
    class ChangeStatusForm(forms.Form):
        status = forms.ChoiceField(choices=Student.STATUS_CHOICES)

    def change_status(self, request, queryset):
        if "apply" in request.POST:
            form = self.ChangeStatusForm(request.POST)
            if form.is_valid():
                status = form.cleaned_data["status"]
                status_label = dict(Student.STATUS_CHOICES)[status]
                updated = queryset.update(status=status)
                messages.success(request, _("Changed status (to '%(status)s') on %(count)s students") % {"status":status_label, "count":updated})

            return HttpResponseRedirect(request.get_full_path())

        form = self.ChangeStatusForm();
        return render(request, "admin/change_status.html", context={"students":queryset, "form":form });

    change_status.short_description = _("Change Status")

    # "export" to email address list
    def email_list(self, request, queryset):
        the_list = []
        orphans = []
        for student in queryset:
            a_guardian_has_an_email = False
            for guardian in student.guardians.all():
                if guardian.email_address:
                    a_guardian_has_an_email = True
                    if not guardian in the_list and guardian.email_address:
                        the_list.append(guardian)

            if not a_guardian_has_an_email:
                orphans.append(student)

        return render(request, "admin/bulk_email.html", context={"guardians":the_list, "orphans":orphans, "students":queryset})


    email_list.short_description = _("Export Guardian EMail addresses")


admin.site.register(Student, StudentAdmin)


class ContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = ("name","first_name","kind","phone_number","cellphone_number","email_address")
    search_fields = ["name", "first_name"]
    list_filter = ("kind","is_teammember")
    readonly_fields = ("student_links",)

    def get_fields(self, request, obj=None):
#            return ("name", "first_name", "kind", "address", "phone_number", "cellphone_number", "email_address", "on_address_list", "is_teammember", "team_email_address", "note", "student_links")
        fields = ("name", "first_name", "kind", "address", "phone_number", "cellphone_number", "email_address", "on_address_list", "is_teammember", "is_societymember")
        if obj and obj.is_teammember:
            fields += ("team_email_address",)
        fields += ("note", "student_links")
        return fields

    def student_links(self, obj):
        students = obj.students.all()

        links = [];
        for student in students:
            change_url = urls.reverse("admin:people_student_change", args=(student.id,))
            links.append('<a href="%s">%s</a>' % (change_url, student))
        return format_html("<br>".join(links));
    student_links.short_description = _("Students")

admin.site.register(Contact, ContactAdmin)


class AddressAdmin(admin.ModelAdmin):
    model = Address
#    inlines = [
#    	ContactInline,
#    	StudentAddressInline
#    ]
    list_display = ("street", "city")
    readonly_fields = ("student_links","contact_links")

    def student_links(self, obj):
        students = obj.student_set.all()
        links = [];
        for student in students:
            change_url = urls.reverse("admin:people_student_change", args=(student.id,))
            links.append('<a href="%s">%s</a>' % (change_url, student))
        return format_html("<br>".join(links));
    student_links.short_description = _("Students at this Address")

    def contact_links(self, obj):
        contacts = obj.contact_set.all()
        links = [];
        for contact in contacts:
            change_url = urls.reverse("admin:people_contact_change", args=(contact.id,))
            links.append('<a href="%s">%s</a>' % (change_url, contact))
        return format_html("<br>".join(links));
    contact_links.short_description = _("Contacts at this Address")



admin.site.register(Address, AddressAdmin)
