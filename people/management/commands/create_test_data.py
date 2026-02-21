import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from people.models import Address, Contact, Student, Payment, Note


STREETS = [
    "Evergreen Terrace", "Maple Street", "Oak Avenue", "Elm Street",
    "Walnut Street", "Cherry Lane", "Spruce Drive", "Pine Road",
]

CITIES = [
    ("20251", "Springfield"),
    ("20253", "Springfield"),
    ("22303", "Springfield"),
    ("22769", "Shelbyville"),
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


def make_address(street=None, plz=None, city=None):
    if not plz:
        plz, city = random.choice(CITIES)
    if not street:
        street = f"{random.choice(STREETS)} {random.randint(1, 120)}"
    return Address.objects.create(street=street, postal_code=plz, city=city)


def make_contact(first, last, addr, **kwargs):
    defaults = dict(
        name=last, first_name=first, kind="prs", address=addr,
        phone_number=random_phone(), cellphone_number=random_mobile(),
        email_address=random_email(first, last),
    )
    defaults.update(kwargs)
    return Contact.objects.create(**defaults)


def make_student(first, last, gender, addr, status, mentor, **kwargs):
    age_days = random.randint(5 * 365, 16 * 365)
    dob = date.today() - timedelta(days=age_days)
    enrollment_year = dob.year + 6

    first_day = None
    last_day = None
    if status == "active":
        first_day = date(enrollment_year, 8, random.randint(1, 28))
    elif status == "alumnus":
        first_day = date(enrollment_year, 8, random.randint(1, 28))
        last_day = first_day + timedelta(days=random.randint(365, 2000))

    return Student.objects.create(
        name=last, first_name=first, short_name=first[:3],
        status=status, dob=dob, pob="Springfield", gender=gender,
        language="Deutsch", address=addr,
        mentor=mentor if status == "active" else None,
        first_day=first_day, last_day=last_day,
        first_enrollment=enrollment_year, level_ofs=1, level_ref=enrollment_year,
        planned_enrollment_year=str(date.today().year) if status == "in_admission_procedure" else None,
        planned_enrollment_age="6" if status == "in_admission_procedure" else None,
        **kwargs,
    )


class Command(BaseCommand):
    help = "Generate synthetic test data using Springfield characters"

    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")

        # --- Addresses ---
        addr_simpson = make_address("Evergreen Terrace 742", "20251", "Springfield")
        addr_flanders = make_address("Evergreen Terrace 744", "20251", "Springfield")
        addr_van_houten = make_address("Cherry Lane 316", "20253", "Springfield")
        addr_kirk = make_address("Maple Street 12b", "20253", "Springfield")
        addr_muntz = make_address("Elm Street 55", "22303", "Springfield")
        addr_wiggum = make_address("Oak Avenue 88", "20251", "Springfield")
        addr_riviera = make_address("Walnut Street 7", "20253", "Springfield")
        addr_bouvier = make_address("Maple Street 430", "22769", "Shelbyville")
        addr_carlson = make_address("Spruce Drive 19", "20253", "Springfield")
        addr_prince = make_address("Pine Road 3", "22303", "Springfield")
        addr_spuckler = make_address("Route 9", "22769", "Shelbyville")
        extra_addresses = [make_address() for _ in range(4)]

        all_addresses = [
            addr_simpson, addr_flanders, addr_van_houten, addr_kirk,
            addr_muntz, addr_wiggum, addr_riviera, addr_bouvier,
            addr_carlson, addr_prince, addr_spuckler,
        ] + extra_addresses
        self.stdout.write(f"  {len(all_addresses)} addresses")

        # --- Team members / mentors ---
        edna = make_contact("Edna", "Krabappel", random.choice(extra_addresses),
                            is_teammember=True,
                            team_email_address="edna@springfield-elementary.example")
        elizabeth = make_contact("Elizabeth", "Hoover", random.choice(extra_addresses),
                                 is_teammember=True,
                                 team_email_address="hoover@springfield-elementary.example")
        dewey = make_contact("Dewey", "Largo", random.choice(extra_addresses),
                             is_teammember=True,
                             team_email_address="largo@springfield-elementary.example")
        mentors = [edna, elizabeth, dewey]
        self.stdout.write(f"  {len(mentors)} mentors (Krabappel, Hoover, Largo)")

        # --- Bufdis ---
        make_contact("Üter", "Zörker", random.choice(extra_addresses), kind="buf",
                     note="Bufdi seit September " + str(date.today().year))
        make_contact("Allison", "Taylor", random.choice(extra_addresses), kind="buf",
                     note="Bufdi seit Oktober " + str(date.today().year))
        self.stdout.write("  2 Bufdis (Üter, Allison)")

        # --- Interns ---
        make_contact("Artie", "Ziff", random.choice(extra_addresses), kind="int",
                     note="Praktikum 3 Wochen")
        make_contact("Frank", "Grimes", random.choice(extra_addresses), kind="int",
                     note="Praktikum 6 Wochen")
        self.stdout.write("  2 interns (Ziff, Grimes)")

        # --- Org/company contacts ---
        Contact.objects.create(
            name="Springfield Nuclear Power Plant", first_name="", kind="com",
            address=random.choice(extra_addresses), phone_number=random_phone(),
            email_address="info@snpp.example",
        )
        Contact.objects.create(
            name="Springfield Board of Education", first_name="", kind="org",
            address=random.choice(extra_addresses), phone_number=random_phone(),
            email_address="info@sbe.example",
        )
        self.stdout.write("  2 org/company contacts")

        # --- Society member (not team, not guardian) ---
        Contact.objects.create(
            name="Burns", first_name="Charles Montgomery", kind="prs",
            address=random.choice(extra_addresses), phone_number=random_phone(),
            email_address="burns@snpp.example", is_societymember=True,
            note="Sponsor",
        )
        self.stdout.write("  1 society member (Burns)")

        all_students = []
        all_guardians = []

        # === FAMILY STRUCTURES ===

        # --- Simpson family: classic two-parent, 3 kids ---
        homer = make_contact("Homer", "Simpson", addr_simpson,
                             email_address="homer@snpp.example",
                             note="Arbeitet im Kernkraftwerk")
        marge = make_contact("Marge", "Simpson", addr_simpson,
                             email_address="marge.simpson@gmail.com")
        all_guardians.extend([homer, marge])

        bart = make_student("Bart", "Simpson", "m", addr_simpson, "active", edna,
                            emergency_notes="Kein Ritalin! Nur im Notfall Rektor Skinner anrufen.")
        bart.guardians.add(homer, marge)
        lisa = make_student("Lisa", "Simpson", "f", addr_simpson, "active", elizabeth,
                            emergency_notes="Vegetarierin, kein Fleisch beim Mittagessen")
        lisa.guardians.add(homer, marge)
        maggie = make_student("Maggie", "Simpson", "f", addr_simpson, "active", elizabeth)
        maggie.guardians.add(homer, marge)
        all_students.extend([bart, lisa, maggie])

        # --- Flanders family: classic two-parent, 2 kids ---
        ned = make_contact("Ned", "Flanders", addr_flanders,
                           email_address="ned.flanders@mailbox.org")
        maude = make_contact("Maude", "Flanders", addr_flanders,
                             email_address="maude.flanders@posteo.de")
        all_guardians.extend([ned, maude])

        rod = make_student("Rod", "Flanders", "m", addr_flanders, "active", dewey)
        rod.guardians.add(ned, maude)
        todd = make_student("Todd", "Flanders", "m", addr_flanders, "active", dewey)
        todd.guardians.add(ned, maude)
        all_students.extend([rod, todd])

        # --- Van Houten: patchwork/separated ---
        # Kirk and Luann divorced. Milhouse lives with Luann.
        # Kirk has different address. Both are guardians.
        luann = make_contact("Luann", "Van Houten", addr_van_houten,
                             email_address="luann.vanhouten@web.de")
        kirk = make_contact("Kirk", "Van Houten", addr_kirk,
                            email_address="kirk.vanhouten@gmx.de",
                            note="Abholung nur nach Absprache")
        all_guardians.extend([luann, kirk])

        milhouse = make_student("Milhouse", "Van Houten", "m", addr_van_houten, "active", edna)
        milhouse.guardians.add(luann, kirk)
        all_students.append(milhouse)

        # --- Muntz family: single parent ---
        # Nelson lives with his mom, no father listed
        mrs_muntz = make_contact("Mrs.", "Muntz", addr_muntz,
                                 email_address="muntz@web.de")
        all_guardians.append(mrs_muntz)

        nelson = make_student("Nelson", "Muntz", "m", addr_muntz, "active", edna,
                              emergency_notes="Bei Rauferei: Nelson ist meistens nicht der Anfänger (lt. Mutter)")
        nelson.guardians.add(mrs_muntz)
        all_students.append(nelson)

        # --- Wiggum family: classic one-child ---
        sarah = make_contact("Sarah", "Wiggum", addr_wiggum,
                             email_address="sarah.wiggum@gmail.com")
        clancy = make_contact("Clancy", "Wiggum", addr_wiggum,
                              email_address="chief@springfield-pd.example",
                              note="Polizeichef")
        all_guardians.extend([sarah, clancy])

        ralph = make_student("Ralph", "Wiggum", "m", addr_wiggum, "active", elizabeth,
                             emergency_notes="Isst gelegentlich Kleber")
        ralph.guardians.add(sarah, clancy)
        all_students.append(ralph)

        # --- Patchwork: Riviera/Bouvier/Simpson ---
        # Dr. Riviera married Selma Bouvier. Selma's daughter Ling has
        # only Selma as guardian. Riviera's son from previous marriage
        # has only Riviera. Their common child has both.
        selma = make_contact("Selma", "Bouvier", addr_riviera,
                             email_address="selma.bouvier@gmail.com")
        riviera = make_contact("Nick", "Riviera", addr_riviera,
                               email_address="dr.nick@riviera.example",
                               note="Hi everybody!")
        all_guardians.extend([selma, riviera])

        ling = make_student("Ling", "Bouvier", "f", addr_riviera, "active", elizabeth)
        ling.guardians.add(selma)  # only Selma
        all_students.append(ling)

        nick_jr = make_student("Nick Jr.", "Riviera", "m", addr_riviera, "active", dewey)
        nick_jr.guardians.add(riviera)  # only Riviera
        all_students.append(nick_jr)

        sophia = make_student("Sophia", "Bouvier-Riviera", "f", addr_riviera, "active", elizabeth)
        sophia.guardians.add(selma, riviera)  # both
        all_students.append(sophia)

        # --- Carlson family: single parent, 2 kids ---
        carl_sr = make_contact("Carl", "Carlson", addr_carlson,
                               email_address="carl@snpp.example")
        all_guardians.append(carl_sr)

        carl_jr = make_student("Carl Jr.", "Carlson", "m", addr_carlson, "active", edna)
        carl_jr.guardians.add(carl_sr)
        daisy = make_student("Daisy", "Carlson", "f", addr_carlson, "active", elizabeth)
        daisy.guardians.add(carl_sr)
        all_students.extend([carl_jr, daisy])

        # --- Prince family: separated, kids have mom's name, dad different name ---
        brandine = make_contact("Brandine", "Spuckler", addr_spuckler,
                                email_address="brandine@web.de")
        cletus = make_contact("Cletus", "Spuckler", addr_spuckler,
                              email_address="cletus@web.de")
        all_guardians.extend([brandine, cletus])

        # Spuckler kids (3 active)
        for name in ["Whitney", "Jitney", "Dubya"]:
            g = "f" if name in ["Whitney", "Jitney"] else "m"
            s = make_student(name, "Spuckler", g, addr_spuckler, "active", dewey)
            s.guardians.add(brandine, cletus)
            all_students.append(s)

        # --- Alumni ---
        # Jimbo Jones - graduated
        carol = make_contact("Carol", "Jones", random.choice(extra_addresses),
                             email_address="carol.jones@web.de")
        all_guardians.append(carol)
        jimbo = make_student("Jimbo", "Jones", "m", random.choice(extra_addresses), "alumnus", None)
        jimbo.guardians.add(carol)
        all_students.append(jimbo)

        # Database (the dog's owner, Sideshow Bob's kid)
        gino_mother = make_contact("Francesca", "Terwilliger", random.choice(extra_addresses),
                                   email_address="francesca.t@posteo.de")
        all_guardians.append(gino_mother)
        gino = make_student("Gino", "Terwilliger", "m", random.choice(extra_addresses), "alumnus", None)
        gino.guardians.add(gino_mother)
        all_students.append(gino)

        # Sherri and Terri's family - alumni
        mrs_mackleberry = make_contact("Mrs.", "Mackleberry", random.choice(extra_addresses),
                                       email_address="mackleberry@gmx.de")
        all_guardians.append(mrs_mackleberry)
        sherri = make_student("Sherri", "Mackleberry", "f", random.choice(extra_addresses), "alumnus", None)
        sherri.guardians.add(mrs_mackleberry)
        all_students.append(sherri)

        # --- In admission procedure ---
        manjula = make_contact("Manjula", "Nahasapeemapetilon", addr_prince,
                               email_address="manjula@gmail.com")
        apu = make_contact("Apu", "Nahasapeemapetilon", addr_prince,
                           email_address="apu@kwik-e-mart.example")
        all_guardians.extend([manjula, apu])

        sashi = make_student("Sashi", "Nahasapeemapetilon", "m", addr_prince,
                             "in_admission_procedure", None)
        sashi.guardians.add(manjula, apu)
        all_students.append(sashi)

        agnes = make_contact("Agnes", "Skinner", random.choice(extra_addresses),
                             email_address="agnes.skinner@web.de")
        all_guardians.append(agnes)
        armin = make_student("Armin", "Tamzarian", "m", random.choice(extra_addresses),
                             "in_admission_procedure", None)
        armin.guardians.add(agnes)
        all_students.append(armin)

        # --- Orphaned contacts (simulate deleted students' guardians) ---
        make_contact("Lucius", "Sweet", random.choice(all_addresses))
        make_contact("Lurleen", "Lumpkin", random.choice(all_addresses))
        make_contact("Patty", "Bouvier", addr_bouvier)
        make_contact("Lionel", "Hutz", random.choice(all_addresses))
        self.stdout.write("  4 orphaned contacts (Sweet, Lumpkin, Bouvier, Hutz)")

        self.stdout.write(f"  {len(all_students)} students")
        self.stdout.write(f"  {len(all_guardians)} guardians")

        # --- Payments (for active students, last 6 months) ---
        payments = []
        active_students = [s for s in all_students if s.status == "active"]
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
                    student=s, date=payment_date,
                    amount=random.choice([150.0, 180.0, 200.0, 220.0, 250.0]),
                    kind="tuition",
                )
                payments.append(p)
        self.stdout.write(f"  {len(payments)} payments")

        # --- Notes ---
        Note.objects.create(student=bart, date=today - timedelta(days=5),
                            content="Wurde beim Sprayen erwischt. Elterngespräch vereinbart.")
        Note.objects.create(student=bart, date=today - timedelta(days=30),
                            content="Skateboard-Verbot auf dem Schulhof nochmal besprochen.")
        Note.objects.create(student=lisa, date=today - timedelta(days=10),
                            content="Sehr engagiert im Projektunterricht Umwelt.")
        Note.objects.create(student=nelson, date=today - timedelta(days=15),
                            content="Konflikt mit Mitschüler, Gespräch geführt.")
        Note.objects.create(student=ralph, date=today - timedelta(days=3),
                            content="Hat wieder Kleber gegessen. Eltern informiert.")

        self.stdout.write(self.style.SUCCESS("Done."))
