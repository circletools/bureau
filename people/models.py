from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _

from django import forms

class Address(models.Model):
    class Meta:
        verbose_name = _("Postal Address")
        verbose_name_plural = _("Postal Addresses")
        ordering = ["city", "street"]

    street = models.CharField(_("Street Address"), max_length=200, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=200, blank=True)
    city = models.CharField(_("City"), max_length=200, blank=True)

    alternative = models.CharField(_("Alternative"), max_length=1000, blank=True)

    country = models.CharField(_("Country"), max_length=200, blank=True)

    def __str__(self):
        return self.postal_code + " " + self.city + (", " + self.street) if self.street else "";


class Contact(models.Model):
    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")
        ordering = ["name", "first_name"]

    KIND_CHOICES = (
            ("oth",_("Other")),
            ("prs",_("Person")),
            ("com",_("Company")),
            ("org",_("Organization")),
        )

    name = models.CharField(_("Name"), max_length=200)
    first_name = models.CharField(_("First Name"), max_length=200, blank=True)
    kind = models.CharField(_("Kind"), max_length=3, choices=KIND_CHOICES)

    address = models.ForeignKey(Address, verbose_name=_("Postal Address"), null=True, on_delete=models.CASCADE)
    phone_number = models.CharField(_("Phone"), max_length=64, blank=True)
    cellphone_number = models.CharField(_("Mobile"), max_length=64, blank=True)
    email_address = models.CharField(_("EMail"), max_length=128, blank=True)

    on_address_list = models.BooleanField(_("Appears on Adress List"), default=True)

    is_teammember = models.BooleanField(_("Team Member"), default=False)
    is_societymember = models.BooleanField(_("Society Member"), default=False)
    team_email_address = models.CharField(_("Team-EMail"), max_length=128, blank=True)

    note = models.TextField(_("Note"), blank=True)

    def __str__(self):
        if self.first_name:
            return self.name + ", " + self.first_name
        return self.name


# Platzhalter Elterngespraech,Anmerkung,
# Alter Einschulung,Warteliste,Klassenstufe 13/14,Klassenstufe 16/17,
# Zusatz,Frei 1,


class Student(models.Model):
    class Meta:
        verbose_name = _("Student")
        verbose_name_plural = _("Students")
        ordering = ["name", "first_name"]

    GENDER_CHOICES = (
        ("m", _("male")),
        ("f", _("female")),
        ("__", _("other/unspecified"))
        )

    STATUS_CHOICES = (
        ("active", _("active")),
        ("in_admission_procedure", _("in admission procedure")),
        ("waitlisted", _("waitlisted")),
        ("intent_declared", _("intent declared")),
        ("cancelled", _("rejected/expired")),
        ("alumnus", _("alumn")),
        ("special", _("special")),
        )

    def get_new_entry_nr():
        existing = Student.objects.all().order_by("-entry_nr");
        if len(existing)>0:
            return existing[0].entry_nr+1;
        return 1;

    entry_nr = models.IntegerField(_("Entry #"), blank=True, null=True, unique=True, default=get_new_entry_nr)
    status = models.CharField(_("Status"), max_length=32, blank=True, null=True, choices=STATUS_CHOICES)

    name = models.CharField(_("Last Name"), max_length=200)
    first_name = models.CharField(_("First Name"), max_length=200)
    short_name = models.CharField( _("Short Name"), max_length=100, blank=True)

    def short_or_first_name(self):
        return self.short_name or self.first_name

    remark = models.CharField(_("Remark"), max_length=500, blank=True, null=True)

    dob = models.DateField(_("Date of Birth"), blank=True, null=True)
    pob = models.CharField(_("Place of Birth"), max_length=200, blank=True, null=True)

    gender = models.CharField(_("Gender"), max_length=2, blank=True, null=True, choices=GENDER_CHOICES)

    def gender_verbose(self):
        return dict(self.GENDER_CHOICES)[self.gender]

    denomination = models.CharField(_("Religious Denomination"), max_length=200, blank=True, null=True)
    citizenship = models.CharField(_("Citizenship"), max_length=200, blank=True, null=True)
    language = models.CharField(_("Household Language"), max_length=200, blank=True, default="Deutsch")

    first_day = models.DateField(_("First day at this School"), blank=True, null=True)
    last_day = models.DateField(_("Last day at this School"), blank=True, null=True)

    first_enrollment = models.IntegerField(_("First Enrollment (at any School)"), blank=True, null=True)
    level_ofs = models.IntegerField(_("Class Level (at Reference)"), blank=True, null=True)
    level_ref = models.IntegerField(_("Class Level Reference"), blank=True, null=True)

    address = models.ForeignKey(Address, verbose_name=_("Postal Address"), null=True, blank=True, on_delete=models.CASCADE)
    guardians = models.ManyToManyField(Contact, verbose_name=_("Guardians"), limit_choices_to={"kind":"prs"}, blank=True, related_name="students")

    district_school = models.CharField(_("District School"), max_length=200, blank=True, null=True)

    after_school_care = models.BooleanField(_("in After-school Care"), default=False)
    privacy_policy_agreement = models.NullBooleanField(_("Privacy Policy Agreement"))
    vaccination_policy_agreement = models.NullBooleanField(_("Vaccination Policy Agreement"))
    is_sibling = models.NullBooleanField(_("Sibling"))

# Bewerbungsverfahren:
    planned_enrollment_year = models.CharField(_("Enrollment Year"), max_length=32, blank=True, null=True)
    planned_enrollment_age = models.CharField(_("Enrollment Age"), max_length=32, blank=True, null=True)
    waitlist_position = models.IntegerField(_("Waitlist Position"), blank=True, null=True)

    application_received = models.NullBooleanField(_("Application received"))
    obligatory_conference = models.NullBooleanField(_("was present at obligatory parent conference"))
    parent_dialog = models.CharField(_("Parent Dialog"), max_length=32, blank=True, null=True)
    confirmation_status = models.CharField(_("Confirmation"), max_length=32, blank=True, null=True)
    sitting = models.CharField(_("Sitting In"), max_length=32, blank=True, null=True)

    def __str__(self):
        return self.name + ", " + self.first_name


class Note(models.Model):
    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")

    content = models.TextField(_("Content"))
    date = models.DateField(_("Date"), blank=True, null=True)
    archived = models.BooleanField(_("Archived"), blank=True, default=False)
    student = models.ForeignKey(Student, verbose_name=_("Student"), null=True, blank=True, on_delete=models.CASCADE)
#    user = ForeignKey
