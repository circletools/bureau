import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from people.models import Address, Contact, Student, Payment, Note


FIRST_NAMES_F = [
    "Anna", "Lena", "Marie", "Sophie", "Emma", "Mia", "Clara", "Johanna",
    "Frieda", "Ida", "Ella", "Luisa", "Nora", "Maja", "Paula",
]

FIRST_NAMES_M = [
    "Felix", "Jonas", "Leon", "Finn", "Moritz", "Emil", "Theo", "Anton",
    "Oskar", "Karl", "Henri", "Paul", "Ben", "Nico", "Liam",
]

LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
    "Wagner", "Becker", "Hoffmann", "Braun", "Richter", "Klein",
    "Wolf", "Neumann", "Schwarz", "Zimmermann", "Krüger", "Hartmann",
]

STREETS = [
    "Ahornweg", "Birkenstraße", "Eichenallee", "Lindenstraße",
    "Rosenweg", "Gartenstraße", "Schulstraße", "Bergstraße",
    "Waldweg", "Mühlenstraße", "Hafenstraße", "Deichstraße",
]

CITIES = [
    ("20251", "Hamburg"),
    ("20253", "Hamburg"),
    ("22303", "Hamburg"),
    ("22297", "Hamburg"),
    ("22769", "Hamburg"),
    ("20357", "Hamburg"),
    ("22765", "Hamburg"),
    ("20459", "Hamburg"),
    ("22087", "Hamburg"),
    ("21073", "Hamburg"),
]


def random_phone():
    return f"040 {random.randint(1000000, 9999999)}"


def random_mobile():
    prefix = random.choice(["0151", "0152", "0157", "0160", "0170", "0171", "0176", "0179"])
    return f"{prefix} {random.randint(10000000, 99999999)}"


def random_email(first, last):
    domain = random.choice(["gmail.com", "web.de", "gmx.de", "posteo.de", "mailbox.org"])
    clean_last = last.lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
    return f"{first.lower()}.{clean_last}@{domain}"


class Command(BaseCommand):
    help = "Generate synthetic test data (students, contacts, addresses, payments)"

    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")

        # Addresses
        addresses = []
        for i in range(10):
            plz, city = random.choice(CITIES)
            addr = Address.objects.create(
                street=f"{random.choice(STREETS)} {random.randint(1, 120)}",
                postal_code=plz,
                city=city,
            )
            addresses.append(addr)
        self.stdout.write(f"  {len(addresses)} addresses")

        # Team members / mentors
        mentors = []
        for i in range(3):
            gender = random.choice(["m", "f"])
            first = random.choice(FIRST_NAMES_F if gender == "f" else FIRST_NAMES_M)
            last = random.choice(LAST_NAMES)
            c = Contact.objects.create(
                name=last,
                first_name=first,
                kind="prs",
                address=random.choice(addresses),
                phone_number=random_phone(),
                email_address=random_email(first, last),
                is_teammember=True,
                team_email_address=f"{first.lower()}@springfield-elementary.example",
            )
            mentors.append(c)
        self.stdout.write(f"  {len(mentors)} mentors")

        # Students + guardians
        students = []
        guardians = []
        statuses = (
            ["active"] * 10
            + ["alumnus"] * 3
            + ["in_admission_procedure"] * 2
        )
        random.shuffle(statuses)

        for i, status in enumerate(statuses):
            gender = random.choice(["m", "f"])
            first = random.choice(FIRST_NAMES_F if gender == "f" else FIRST_NAMES_M)
            last = random.choice(LAST_NAMES)
            addr = random.choice(addresses)

            # date of birth: 5-16 years ago
            age_days = random.randint(5 * 365, 16 * 365)
            dob = date.today() - timedelta(days=age_days)

            # enrollment year for level calc
            enrollment_year = dob.year + 6
            level_ofs = 1
            level_ref = enrollment_year

            first_day = None
            last_day = None
            if status == "active":
                first_day = date(enrollment_year, 8, random.randint(1, 28))
            elif status == "alumnus":
                first_day = date(enrollment_year, 8, random.randint(1, 28))
                last_day = first_day + timedelta(days=random.randint(365, 2000))

            s = Student.objects.create(
                name=last,
                first_name=first,
                short_name=first[:3],
                status=status,
                dob=dob,
                pob="Hamburg",
                gender=gender,
                language="Deutsch",
                address=addr,
                mentor=random.choice(mentors) if status == "active" else None,
                first_day=first_day,
                last_day=last_day,
                first_enrollment=enrollment_year,
                level_ofs=level_ofs,
                level_ref=level_ref,
                planned_enrollment_year=str(date.today().year) if status == "in_admission_procedure" else None,
                planned_enrollment_age="6" if status == "in_admission_procedure" else None,
                emergency_notes=random.choice([
                    "Allergie: Nüsse", "Asthma-Spray im Ranzen",
                    "Notfall: Großeltern anrufen", "", ""
                ]),
            )
            students.append(s)

            # 1-2 guardians per student
            num_guardians = random.choice([1, 2])
            for g in range(num_guardians):
                g_first = random.choice(FIRST_NAMES_F if g == 0 else FIRST_NAMES_M)
                g_last = last  # same family name
                contact = Contact.objects.create(
                    name=g_last,
                    first_name=g_first,
                    kind="prs",
                    address=addr,
                    phone_number=random_phone(),
                    cellphone_number=random_mobile(),
                    email_address=random_email(g_first, g_last),
                )
                s.guardians.add(contact)
                guardians.append(contact)

        self.stdout.write(f"  {len(students)} students")
        self.stdout.write(f"  {len(guardians)} guardians")

        # Payments (for active students, last 6 months)
        payments = []
        active_students = [s for s in students if s.status == "active"]
        today = date.today()
        for month_offset in range(6):
            m = today.month - month_offset
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            payment_date = date(y, m, random.randint(1, 28))
            for s in active_students:
                p = Payment.objects.create(
                    student=s,
                    date=payment_date,
                    amount=random.choice([150.0, 180.0, 200.0, 220.0, 250.0]),
                    kind="tuition",
                )
                payments.append(p)
        self.stdout.write(f"  {len(payments)} payments")

        # A few notes
        for s in random.sample(active_students, min(5, len(active_students))):
            Note.objects.create(
                student=s,
                content=random.choice([
                    "Elterngespräch geführt, alles gut.",
                    "Braucht Unterstützung in Mathe.",
                    "Sehr engagiert im Projektunterricht.",
                    "Konflikt mit Mitschüler*in, Gespräch geführt.",
                ]),
                date=today - timedelta(days=random.randint(1, 90)),
            )

        self.stdout.write(self.style.SUCCESS("Done."))
