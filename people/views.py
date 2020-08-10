from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Student, Contact
from django.shortcuts import render, get_object_or_404

import csv
from django.http import HttpResponse

from io import BytesIO
from xlsxwriter.workbook import Workbook

@login_required
def index(request):
    return render(request, 'students.html', 
        {'students': Student.objects.all() })

@login_required
def studentcoversheet(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'studentcoversheet.html', 
        {'student': student })

@login_required
def list_excel(request):
	output = BytesIO()
	book = Workbook(output)
	sheet = book.add_worksheet("Adressliste")

	format_normal = book.add_format({"font_size": 8, "bold": False, "num_format": "dd.mm.yyyy"})
	format_normal_gray = book.add_format({"font_size": 8, "bold": False, "num_format": "dd.mm.yyyy", "bg_color":"#CCCCCC"})
	format_bold = book.add_format({"font_size": 8, "bold": True, "num_format": "dd.mm.yyyy"})
	format_bold_gray = book.add_format({"font_size": 8, "bold": True, "num_format": "dd.mm.yyyy", "bg_color":"#CCCCCC"})

	printed = []
	row = 1
	gray = False

	sheet.set_column(0,1,15)
	sheet.set_column(2,1,7)
	sheet.set_column(3,10,15)

	for student in Student.objects.all().filter(status="active"):

		if not student.id in printed:
			gray = not gray

			# get this student's guardians
			guardians = student.guardians.all()

			# actually print the first guardians's students
			for child in guardians[0].students.all().filter(status="active"):
				sheet.write(row, 0, child.name)
				sheet.write(row, 1, child.short_name if child.short_name else child.first_name )
				sheet.write_datetime(row, 2, child.dob)
				sheet.set_row(row, 10, format_bold_gray if gray else format_bold)
				printed.append(child.id)
				row += 1


			# print all guardians
			for guardian in guardians.filter(on_address_list=True):
				sheet.write(row, 0, guardian.name)
				sheet.write(row, 1, guardian.first_name)
				sheet.write(row, 2, "")
				sheet.write(row, 3, guardian.address.street)
				sheet.write(row, 4, guardian.address.postal_code+" "+guardian.address.city)
				sheet.write(row, 5, guardian.phone_number)
				sheet.write(row, 6, guardian.cellphone_number)
				sheet.write(row, 7, guardian.email_address)
				sheet.set_row(row, 10, format_normal_gray if gray else format_normal)
				row += 1

	row += 1
	for person in Contact.objects.all().filter(is_teammember=True):
				sheet.write(row, 0, person.name)
				sheet.write(row, 1, person.first_name)
				sheet.write(row, 2, "")
				sheet.write(row, 3, person.address.street)
				sheet.write(row, 4, person.address.postal_code+" "+person.address.city)
				sheet.write(row, 5, person.phone_number)
				sheet.write(row, 6, person.cellphone_number)
				sheet.write(row, 7, person.team_email_address)
				sheet.set_row(row, 10, format_normal)
				row += 1


	book.close()

	output.seek(0)
	response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	response['Content-Disposition'] = "attachment; filename=adressliste.xlsx"

	return response

@login_required
def students_csv(request, status="active"):
	response = HttpResponse(content_type="text/csv")
	response["Content-Disposition"] = "attachment;filename=list.csv"

	writer = csv.writer(response)

	writer.writerow(["SchülerInnen mit Status '"+status+"'"]);
	writer.writerow(["Name", "Vorname", "Geburtsdatum", "Klassenstufe", "Strasse", "Ort", "Erziehungsberechtigte"])

	for student in Student.objects.all().filter(status=status):
		guardian_names = [];
		first_guardian_name = ""
		for guardian in student.guardians.all():
			if first_guardian_name == guardian.name:
				guardian_names.append(guardian.first_name);
			else:
				first_guardian_name = guardian.name;
				guardian_names.append(guardian.first_name + " " + guardian.name);

		guardian_names.reverse()


		writer.writerow([student.name, student.first_name, student.dob.strftime("%d.%m.%Y"), calc_level(student,date.today()),
			student.address.street, student.address.postal_code+" "+student.address.city,
			" und ".join(guardian_names)])

	return response;


@login_required
def society_csv(request):
	response = HttpResponse(content_type="text/csv")
	response["Content-Disposition"] = "attachment;filename=list.csv"

	writer = csv.writer(response)

	writer.writerow(["Name", "Vorname", "Strasse", "Ort", "Land", "E-Mail"])

	for person in Contact.objects.all().filter(is_societymember=True):
		writer.writerow([person.name, person.first_name, 
			person.address.street, person.address.postal_code+" "+person.address.city,
			])

	return response;


from datetime import date, datetime
import math
from django.db.models import Q

def calc_level(student, cutoff_date):
	if not student.level_ref or not student.level_ofs:
		return "N/A"
	current_year = cutoff_date.year-1 if cutoff_date.month < 8 else cutoff_date.year
	level =  current_year - (int(student.level_ref) - int(student.level_ofs))
	return(level)


@login_required
def level_report(request):
		response = HttpResponse(content_type="text/plain; charset=utf-8")
#		response["Content-Disposition"] = "attachment;filename=list.csv"


		# we want to group into two levels (primary 1-4/secondary 5-9)
		groups = [ range(1,5), range(5,10) ]

		# iterate a school year, produce a list of dates, one for each month
		year = settings.GLOBAL_SETTINGS['LEVEL_REPORT_FIRST_YEAR']
		report_duration = settings.GLOBAL_SETTINGS['LEVEL_REPORT_YEARS']
		first_month_of_schoolyear = 6
		dates = list(map(
					lambda month: date(year + math.floor(month/12), (month%12)+1, 1), 
					range(first_month_of_schoolyear-1, first_month_of_schoolyear+(12*report_duration))))

		response.write("Bericht Klassenstufen (%r - %r)\n\n" % (year, year+report_duration));

		enrollment_at_date = ()

		last_students = []

		# now for each of those dates
		for cutoff_date in dates:
			enrolled_at_level = {}
			response.write("%s:\n" % cutoff_date.strftime("%m/%Y"))

			came = []
			left = []

			# and each active student
			for student in Student.objects.all().filter(Q(status="active") | Q(status="alumnus")):
				# if the student doesnt have a first_day, construct it from first_enrollment
				if not student.first_day:
					student.first_day = date(student.first_enrollment, 8, 1)
					#maybe: student.save();

				# see if the student was enrolled
				enrolled_before = not student.first_day or student.first_day <= cutoff_date
				enrolled_after = not student.last_day or student.last_day >= cutoff_date
				enrolled = enrolled_before and enrolled_after

				if enrolled:
					# calculate the students class level at that date
					level = calc_level(student, cutoff_date)

					# create a list at that level if it doesnt exist
					if not level in enrolled_at_level: enrolled_at_level[level] = []

					# add the student to its level
					enrolled_at_level[level].append(student)

					# if she's not in last_students, she "came"
					if not student in last_students:
						came.append(student)
						last_students.append(student)

				else:
					# if she's in last_students, she "left"
					if student in last_students:
						left.append(student)
						last_students.remove(student)

				# just print that info
#				response.write("\t%s %r %r\n" % ("✓" if enrolled else "✗", level, student) );

			# print those that came or left
			if came:
				response.write("\tZugegangen:\n")
				for student in came:
					response.write("\t\t%s, %s (%s)\n" % (student.name, student.first_name, student.first_day.strftime("%d.%m.%Y")))
					
			if left:
				response.write("\tAbgegangen:\n")
				for student in left:
					response.write("\t\t%s, %s (%s)\n" % (student.name, student.first_name, student.last_day.strftime("%d.%m.%Y")))

			# now, for this date, we group
			for group in groups:
				count = 0
				for level in group:
					if level in enrolled_at_level:
						count += len(enrolled_at_level[level])

				response.write("  %i-%i : %r\n" % (group.start, group.stop-1, count))
					

#			response.write("%r\n" % enrolled_at_level)
			response.write("\n")

			# no


		# iterate students
#		for student in Student.objects.all().filter(status="active"):
#			response.write( student.name+", "+student.first_name+" "+calc_level(student)+"\n");


		return response;


@login_required
def student_report(request):
	today = date.today();
	year = today.year

	if today.month <= 1:
		period_start = date(year-1, 7, 31)
	elif today.month < 8:
		period_start = date(year, 1, 31) 
	else:
		period_start = date(year, 7, 31)

	period_end = today;

	students_that_left = []
	students_that_came = []
	students  = []

	for student in Student.objects.all().filter(Q(status="active") | Q(status="alumnus")):
		came = False
		left = False
		alumnus = False

		if student.first_day:
			came = student.first_day >= period_start and student.first_day <= period_end

		if student.last_day:
			left = student.last_day >= period_start and student.last_day <= period_end
			alumnus = student.last_day < period_start


		# calculate the students class level at that date
		student.tmp_level = calc_level(student, period_end)

		if left:
			students_that_left.append(student)
		elif came:
			students_that_came.append(student)
		elif not alumnus:
			students.append(student)

#				response.write("\t%s %r %r\n" % ("✓" if enrolled else "✗", level, student) );


	output = BytesIO()
	book = Workbook(output)
	sheet = book.add_worksheet("SchülerInnen")

	format_normal = book.add_format({"font_size": 10, "bold": False, "num_format": "dd.mm.yyyy"})
	format_bold = book.add_format({"font_size": 10, "bold": True, "num_format": "dd.mm.yyyy"})

	row = 0

	sheet.set_column(0,0,10)
	sheet.set_column(1,1,20)
	sheet.set_column(2,5,15)
	sheet.set_column(5,7,30)
	sheet.set_column(8,8,5)
	sheet.set_column(9,12,15)

	sheet.write(row, 0, "Stand")
	sheet.write(row, 2, period_end)
	sheet.set_row(row, 12, format_normal)
	row += 1
	sheet.write(row, 0, "Zu-/Abgänge berücksichtigt ab")
	sheet.write(row, 2, period_start)
	sheet.set_row(row, 12, format_normal)
	row += 1
	row += 1

	sheet.write(row, 0, "Name")
	sheet.write(row, 1, "Vorname")
	sheet.write(row, 2, "Geburtsdatum")
	sheet.write(row, 3, "Geburtsort")
	sheet.write(row, 4, "Strasse")
	sheet.write(row, 5, "Ort")
	sheet.write(row, 6, "Erziehungsberechtigte")
	sheet.write(row, 7, "Anschrift Erziehungsberechtigte (falls abweichend)")
	sheet.write(row, 8, "Klassenstufe")
	sheet.write(row, 9, "Tag des Eintritts")
	sheet.write(row, 10, "Tag der Entlassung")
	sheet.set_row(row, 12, format_bold)
	row += 1

	for student in sorted(students, key=lambda student: student.tmp_level):
		student_report_row(sheet, student, row)
		sheet.set_row(row, 12, format_normal)
		row += 1

	row += 1
	sheet.write(row, 0, "Zugegangen")
	sheet.set_row(row, 12, format_bold)
	row += 1

	for student in sorted(students_that_came, key=lambda student: student.tmp_level):
		student_report_row(sheet, student, row)
		sheet.set_row(row, 12, format_normal)
		row += 1

	row += 1
	sheet.write(row, 0, "Abgegangen")
	sheet.set_row(row, 12, format_bold)
	row += 1

	for student in sorted(students_that_left, key=lambda student: student.tmp_level):
		student_report_row(sheet, student, row)
		sheet.set_row(row, 12, format_normal)
		row += 1

	book.close()

	output.seek(0)

	response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	response['Content-Disposition'] = "attachment; filename=zugaenge_abgaenge.xlsx"

	return response;	


def student_report_row(sheet, student, row):
	guardian_names = [];
	first_guardian_name = ""
	other_address = ""
	for guardian in student.guardians.all():
		if first_guardian_name == guardian.name:
			guardian_names.append(guardian.first_name);
		else:
			first_guardian_name = guardian.name;
			guardian_names.append(guardian.first_name + " " + guardian.name);

		if guardian.address != student.address:
			other_address = "%s %s, %s, %s %s  " % (guardian.first_name, guardian.name, 
				guardian.address.street, guardian.address.postal_code, guardian.address.city)

	guardian_names.reverse()

	sheet.write(row, 0, student.name)
	sheet.write(row, 1, student.first_name)
	sheet.write(row, 2, student.dob)
	sheet.write(row, 3, student.pob)
	sheet.write(row, 4, student.address.street)
	sheet.write(row, 5, student.address.postal_code+" "+student.address.city)
	sheet.write(row, 6, " und ".join(guardian_names))
	sheet.write(row, 7, other_address)
	sheet.write(row, 8, "%r" % student.tmp_level)
	sheet.write(row, 9, student.first_day)
	sheet.write(row, 10, student.last_day)
