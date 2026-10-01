"""
Data Generator page — generates test datasets from local lists or real public APIs.
Expanded: 100+ names per locale, real API data from randomuser.me / dummyjson / reqres.in
         + restcountries / quotable / dicebear, presets, seed, Luhn/INN/SNILS, FK.
"""

import json, random, string, uuid, ipaddress, html as html_mod, csv, io, os, hashlib, time
from datetime import datetime, timedelta
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import ACCENT
from automat.ui.page_base import PageWidget
from automat.core.activity_log import log, EVENT_DATAGEN, STATUS_OK
from automat.core.worker import run_in_background

CACHE_TTL = 24 * 3600  # 24h


def _cache_dir():
    # QStandardPaths if available, fallback to APPDATA / ~/.cache
    try:
        from PyQt5.QtCore import QStandardPaths
        d = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        if d:
            p = Path(d) / "datagen"
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass
    base = os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / "Automat" / "cache" / "datagen"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cache_path(key):
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    safe = "".join(c if c.isalnum() else "_" for c in key)[:24]
    return _cache_dir() / f"{safe}_{h}.json"


def _save_cache(key, data):
    try:
        _cache_path(key).write_text(json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _load_cache(key, max_age=CACHE_TTL):
    try:
        p = _cache_path(key)
        if not p.exists():
            return None
        obj = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - obj.get("ts", 0) > max_age:
            return None
        return obj.get("data")
    except Exception:
        return None


def _load_cache_any_age(key):
    try:
        p = _cache_path(key)
        if not p.exists():
            return None
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj.get("data")
    except Exception:
        return None

try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
try:
    import yaml as _yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
try:
    import openpyxl as _openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ── LOCAL DATA ───────────────────────────────────────────────────────────────

FIRST_NAMES_RU_M = [
    "Александр","Алексей","Андрей","Антон","Артём","Борис","Вадим","Валентин","Валерий","Виктор",
    "Виталий","Владимир","Владислав","Глеб","Григорий","Даниил","Денис","Дмитрий","Евгений","Егор",
    "Иван","Ильяс","Кирилл","Константин","Лев","Леонид","Максим","Матвей","Михаил","Никита",
    "Николай","Олег","Павел","Пётр","Роман","Руслан","Рустам","Сергей","Станислав","Тимур",
    "Фёдор","Филипп","Эдуард","Юрий","Ярослав","Аркадий","Богдан","Василий","Геннадий","Георгий",
    "Давид","Данил","Захар","Игорь","Карл","Клеменс","Марк","Мирон","Платон","Радислав",
    "Роберт","Святослав","Семён","Тарас","Устин","Феликс","Харитон","Эльдар","Ян",
]

FIRST_NAMES_RU_F = [
    "Алина","Алиса","Анастасия","Ангелина","Анна","Валентина","Валерия","Варвара","Вера","Виктория",
    "Галина","Дарья","Евгения","Елена","Елизавета","Жанна","Зинаида","Злата","Ирина","Кира",
    "Клавдия","Кристина","Лариса","Лена","Лидия","Лилия","Любовь","Людмила","Маргарита","Марина",
    "Мария","Надежда","Наталья","Нелли","Нина","Оксана","Ольга","Полина","Раиса","Регина",
    "Светлана","София","Тамара","Татьяна","Ульяна","Фаина","Элеонора","Юлия","Яна","Ярослава",
    "Агата","Аглая","Аделаида","Акана","Амалия","Амина","Антонина","Белла","Василиса","Вероника",
    "Виолетта","Виталина","Глафира","Дамира","Диана","Ева","Жасмин","Зарина","Зоя","Инга",
    "Искра","Камилла","Карина","Каролина","Ксения","Лайма","Лера","Мирослава","Ника","Пелагея",
    "Рената","Рита","Снежана","Соня","Сьяна","Таисия","Фрида","Хлоя","Эвелина","Эрика",
    "Юлиана","Анфиса","Венера","Габриэлла",
]

LAST_NAMES_RU_M = [
    "Иванов","Петров","Сидоров","Смирнов","Кузнецов","Попов","Васильев","Зайцев","Павлов","Соколов",
    "Михайлов","Новиков","Морозов","Волков","Соловьёв","Лебедев","Козлов","Ильин","Степанов","Николаев",
    "Орлов","Андреев","Макаров","Никитин","Захаров","Зуров","Борисов","Яковлев","Григорьев","Романов",
    "Воробьёв","Сергеев","Кузьмин","Фролов","Алексеев","Давыдов","Белов","Комаров","Матвеев","Поляков",
    "Тихонов","Гусев","Киселёв","Игнатов","Лазарев","Тарасов","Богданов","Власов","Мельников","Денисов",
    "Китаев","Наумов","Шестаков","Афанасьев","Завьялов","Лукин","Баранов","Колычев","Егоров","Маслов",
    "Третьяков","Чернов","Авдеев","Жуков","Белозёров","Кочетков","Савельев","Львов","Горбунов","Пономарёв",
    "Графов","Калачёв","Ершов","Баженов","Кадыров","Столяров","Кравцов","Понкратов","Горшков","Голубев",
    "Пореченков","Кулешов",
]

LAST_NAMES_RU_F = [
    "Иванова","Петрова","Сидорова","Смирнова","Кузнецова","Попова","Васильева","Зайцева","Павлова","Соколова",
    "Михайлова","Новикова","Морозова","Волкова","Соловьёва","Лебедева","Козлова","Ильина","Степанова","Николаева",
    "Орлова","Андреева","Макарова","Никитина","Захарова","Борисова","Яковлева","Григорьева","Романова","Воробьёва",
    "Сергеева","Кузьмина","Фролова","Алексеева","Давыдова","Белова","Комарова","Матвеева","Полякова","Тихонова",
    "Гусева","Киселёва","Игнатова","Лазарева","Тарасова","Богданова","Власова","Мельникова","Денисова","Китаева",
    "Наумова","Шестакова","Афанасьева","Завьялова","Лукина","Баранова","Егорова","Маслова","Третьякова","Чернова",
    "Авдеева","Жукова","Белозёрова","Кочеткова","Савельева","Львова","Горбунова","Пономарёва","Графова","Калачёва",
    "Ершова","Баженова","Кадырова","Столярова","Кравцова","Понкратова","Горшкова","Голубева","Кулешова","Седова",
    "Рябова","Бобылева",
]

CITIES_RU = [
    "Москва","Санкт-Петербург","Новосибирск","Екатеринбург","Казань","Красноярск","Нижний Новгород","Челябинск","Самара","Уфа",
    "Ростов-на-Дону","Омск","Краснодар","Воронеж","Пермь","Волгоград","Тюмень","Саратов","Тольятти","Ижевск",
    "Барнаул","Иркутск","Хабаровск","Владивосток","Махачкала","Томск","Оренбург","Кемерово","Новокузнецк","Рязань",
    "Астрахань","Набережные Челны","Пенза","Липецк","Калининград","Тула","Киров","Сочи","Муром","Петрозаводск",
    "Нижний Тагил","Магнитогорск","Курган","Сургут","Тверь","Ставрополь","Брянск","Севастополь","Ярославль","Майкоп",
    "Владимир","Чита","Смоленск","Саранск","Великий Новгород","Кострома","Курск","Ульяновск","Грозный","Южно-Сахалинск",
    "Чебоксары","Тамбов","Стерлитамак","Комсомольск-на-Амуре","Кызыл","Архангельск","Псков","Нижневартовск","Бийск","Якутск",
    "Мурманск","Горно-Алтайск","Назрань","Элиста","Черкесск","Петропавловск-Камчатский","Магадан","Калуга","Дзержинск","Нальчик",
    "Мытищи","Подольск","Королёв","Балашиха","Химки","Люберцы","Одинцово","Красногорск","Домодедово",
]

FIRST_NAMES_EN = [
    "James","John","Robert","Michael","David","William","Richard","Joseph","Thomas","Charles",
    "Christopher","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua",
    "Kenneth","Kevin","Brian","George","Timothy","Ronald","Edward","Jason","Jeffrey","Ryan",
    "Jacob","Gary","Nicholas","Eric","Jonathan","Stephen","Larry","Justin","Scott","Brandon",
    "Benjamin","Samuel","Raymond","Gregory","Frank","Alexander","Patrick","Jack","Dennis","Jerry",
    "Tyler","Aaron","Jose","Adam","Nathan","Henry","Douglas","Zachary","Peter","Noah",
    "Harold","Kyle","Ethan","Jeremy","Walter","Christian","Keith","Roger","Terry","Austin",
    "Sean","Gerald","Carl","Arthur","Lawrence","Jesse","Dylan","Bryan","Joe","Jordan",
    "Billy","Bruce","Gabriel","Vincent","Russell","Sylvia","Philip","Bobby","Harry","Eugene",
    "Logan","Aiden","Lucas","Mason","Liam","Oliver","Elijah",
]

LAST_NAMES_EN = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts",
    "Gomez","Phillips","Evans","Turner","Diaz","Parker","Cruz","Edwards","Collins","Reyes",
    "Stewart","Morris","Morales","Murphy","Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper",
    "Peterson","Bailey","Reed","Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson",
    "Watson","Brooks","Chavez","Wood","James","Bennett","Gray","Mendoza","Ruiz","Hughes",
    "Price","Alvarez","Castillo","Sanders","Patel","Myers","Long","Ross","Foster","Jimenez",
]

CITIES_EN = [
    "New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","San Jose",
    "Austin","Jacksonville","Fort Worth","Columbus","Charlotte","Indianapolis","San Francisco","Seattle","Denver","Washington",
    "Nashville","Oklahoma City","El Paso","Boston","Portland","Las Vegas","Memphis","Louisville","Baltimore","Milwaukee",
    "Albuquerque","Tucson","Fresno","Mesa","Sacramento","Atlanta","Kansas City","Colorado Springs","Omaha","Raleigh",
    "Long Beach","Virginia Beach","Miami","Oakland","Minneapolis","Tulsa","Tampa","Arlington","New Orleans","Wichita",
    "Cleveland","Bakersfield","Aurora","Anaheim","Honolulu","Santa Ana","Riverside","Corpus Christi","Lexington","Stockton",
    "St. Louis","Pittsburgh","Cincinnati","Anchorage","Greensboro","Toledo","Newark","Plano","Henderson","Lincoln",
    "Orlando","Jersey City","Chandler","Madison","Lubbock","Scottsdale","Reno","Buffalo","Gilbert","Glendale",
    "North Las Vegas","Chesapeake","Fremont","Irvine","Baton Rouge","Garland","Hialeah","Rochester","San Bernardino","Boise",
    "Spokane","Missoula","Tallahassee","Montgomery",
]

COMPANIES = [
    "TechCorp","InnoSoft","DataFlow","CloudNine","PixelWorks","QuantumCore","ByteForge","CyberLink","NovaTech","StarNet",
    "AlphaBit","BlueShift","RedRock","GreenLeaf","SilverLine","GoldenGate","Ironclad","CrystalView","FireStorm","IceBreaker",
    "DeepSea","SkyHigh","EarthBound","WindRider","SunBurst","MoonLight","StarDust","CosmicRay","NebulaNet","GalaxyTech",
    "OrbitSoft","PulsarIT","VortexAI","PrismData","EchoLabs","NexusCore","ZenithDev","ApexSystems","SummitTech","ForgeWorks",
    "NebulaSoft","QuantumLeap","HyperLoop","TurboCode","MegaByte","GigaWatt","TeraFlop","PetaScale","NanoTech","MicroChip",
    "MiliScope","PicoScale","FemtoLab","AttoWorks","KiloNet","MegaDrive",
]

STREETS = [
    "ул. Ленина","ул. Пушкина","ул. Гагарина","ул. Мира","ул. Советская","ул. Центральная","ул. Молодёжная","ул. Садовая","ул. Парковая","ул. Речная",
    "ул. Лесная","ул. Полевая","ул. Школьная","ул. Заводская","ул. Новая","ул. Старая","ул. Озёрная","ул. Горная","Main St","Oak St",
    "Pine St","Maple St","Cedar St","Elm St","Walnut St","2nd Ave","3rd Ave","4th Ave","5th Ave","6th Ave",
    "7th Ave","8th Ave","Park Ave","Broadway","Highland Ave","Lake Ave","Hill St","Spring St","Summer St","Winter St",
    "River Rd","Mountain Rd","Forest Dr","Valley Blvd","Sunset Blvd","Pacific Hwy","Ocean Ave",
]

JOB_TITLES = [
    "Software Engineer","Data Scientist","Product Manager","UX Designer","DevOps Engineer","Backend Developer","Frontend Developer","Full Stack Developer","ML Engineer","QA Engineer",
    "System Administrator","Database Administrator","Security Analyst","Cloud Architect","Mobile Developer","Game Developer","Technical Writer","Scrum Master","Tech Lead","CTO",
    "VP of Engineering","Director of IT","Solutions Architect","Site Reliability Engineer","Data Analyst","Business Analyst","Network Engineer","Hardware Engineer","Embedded Systems Engineer","AI Researcher",
    "Blockchain Developer","AR/VR Developer","IoT Engineer","Firmware Engineer",
]

COLORS = [
    "Red","Blue","Green","Yellow","Orange","Purple","Pink","Brown","Black","White",
    "Gray","Cyan","Magenta","Lime","Teal","Indigo","Violet","Gold","Silver","Bronze",
    "Coral","Salmon","Turquoise","Mauve","Lavender","Mint","Ivory","Jade","Onyx","Ruby",
]

COUNTRIES = [
    "Russia","USA","UK","Germany","France","Japan","China","India","Brazil","Canada",
    "Australia","Italy","Spain","Netherlands","Sweden","Norway","Finland","Poland","Czech Republic","Austria",
    "Switzerland","Belgium","Portugal","Greece","Turkey","South Korea","Thailand","Vietnam","Indonesia","Mexico",
    "Argentina","Colombia","Chile","Peru","Egypt","Nigeria","South Africa","Kenya","Morocco","UAE",
    "Saudi Arabia","Israel","Singapore","Malaysia","Philippines","New Zealand","Iceland","Ireland","Denmark","Hungary",
    "Romania","Ukraine",
]

PRODUCTS = [
    "Laptop","Smartphone","Headphones","Keyboard","Mouse","Monitor","Tablet","Camera","Speaker","Router",
    "SSD 1TB","HDD 2TB","RAM 16GB","GPU RTX 4080","CPU i9-14900","Motherboard","Power Supply","Webcam","Microphone","Chair",
    "Desk","Backpack","Smart Watch","E-Reader","Drone","Console","Gamepad","VR Headset","Projector","Printer",
]

CURRENCIES = ["RUB","USD","EUR","GBP","JPY","CNY","KZT","BYN","UAH","TRY"]

FIELD_TYPES = [
    "id","name","first_name","last_name","email","phone","age","gender","birthdate",
    "city","address","lat","lng","company","job_title","salary","uuid","ipv4","ipv6","mac",
    "active","date","text","website","credit_card","inn","snils","passport","iban",
    "color","country","currency","avatar","description","amount","product",
]

PRESETS = {
    "custom": None,
    "hr": ["id","name","email","phone","age","gender","birthdate","city","company","job_title","salary","active"],
    "ecommerce": ["id","name","email","city","product","amount","currency","date","active"],
    "crm": ["id","name","email","phone","company","city","country","website","description","active"],
    "finance": ["id","name","inn","snils","passport","iban","credit_card","amount","currency","date"],
    "geo": ["id","name","city","address","lat","lng","country","phone"],
}

SQL_TYPES = {
    "id": "INTEGER PRIMARY KEY",
    "age": "INTEGER",
    "salary": "INTEGER",
    "amount": "REAL",
    "lat": "REAL",
    "lng": "REAL",
    "active": "BOOLEAN",
    "date": "DATE",
    "birthdate": "DATE",
    "uuid": "TEXT",
    "ipv4": "TEXT",
    "ipv6": "TEXT",
    "mac": "TEXT",
    "credit_card": "TEXT",
    "inn": "TEXT",
    "snils": "TEXT",
    "passport": "TEXT",
    "iban": "TEXT",
}

# ── LUHN / INN / SNILS helpers ─────────────────────────────────────────────

def _luhn_checksum(num_str):
    s = 0
    alt = False
    for c in reversed(num_str):
        d = int(c)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return s % 10


def _gen_luhn(rng, prefix, length):
    """Generate card number with given prefix and total length, valid Luhn."""
    need = length - len(prefix) - 1
    body = prefix + "".join(str(rng.randint(0, 9)) for _ in range(need))
    check = (10 - _luhn_checksum(body + "0")) % 10
    return body + str(check)


def _gen_inn_10(rng):
    """INN 10 digits (legal entity) with checksum."""
    base = [rng.randint(0, 9) for _ in range(9)]
    coeff = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    s = sum(a * b for a, b in zip(base, coeff)) % 11 % 10
    return "".join(str(x) for x in base) + str(s)


def _gen_inn_12(rng):
    """INN 12 digits (individual) with 2 checksums."""
    base = [rng.randint(0, 9) for _ in range(10)]
    c1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    n11 = sum(a * b for a, b in zip(base, c1)) % 11 % 10
    c2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    n12 = sum(a * b for a, b in zip(base + [n11], c2)) % 11 % 10
    return "".join(str(x) for x in base) + str(n11) + str(n12)


def _gen_snils(rng):
    """SNILS 11 digits: 9 digits + 2-digit checksum."""
    base = [rng.randint(0, 9) for _ in range(9)]
    # avoid 000, ensure not all zeros
    s = sum((9 - i) * v for i, v in enumerate(base))
    if s < 100:
        checksum = s
    elif s in (100, 101):
        checksum = 0
    else:
        checksum = s % 101
        if checksum in (100, 101):
            checksum = 0
    return "".join(str(x) for x in base) + f"{checksum:02d}"


def _gen_passport(rng):
    """Russian passport: 4-digit series + 6-digit number."""
    series = f"{rng.randint(10, 99)}{rng.randint(10, 99)}"
    number = f"{rng.randint(100000, 999999)}"
    return f"{series} {number}"


def _gen_iban(rng, country="RU"):
    """Simplified IBAN: country + checksum + BBAN."""
    # RU IBAN is not official but we generate plausible: RU + 2 check + 20 digits
    bban = "".join(str(rng.randint(0, 9)) for _ in range(20))
    # checksum calc: move country+00 to end, convert letters to numbers, mod 97
    tmp = bban + "272700"  # R=27 U=30
    chk = 98 - int(tmp) % 97
    return f"RU{chk:02d}{bban}"


# ── PUBLIC API SOURCES ───────────────────────────────────────────────────────

API_SOURCES = {
    "randomuser.me": "https://randomuser.me/api/?results={count}&nat=us,gb,ru,de,fr",
    "dummyjson": "https://dummyjson.com/users?limit={count}&select=firstName,lastName,email,phone,age,address,company",
    "reqres": "https://reqres.in/api/users?per_page={count}",
    "jsonplaceholder": "https://jsonplaceholder.typicode.com/users",
    "restcountries": "https://restcountries.com/v3.1/all?fields=name,capital,currencies,region,cca2",
    "quotable": "https://api.quotable.io/quotes/random?limit={count}",
}

# ── PAGE WIDGET ──────────────────────────────────────────────────────────────

class DataGenPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tr = self.app.i18n.tr
        self._api_cache = []
        self._quote_cache = []
        self._country_cache = []
        self.build()

    def build(self):
        tr = self.tr
        self.header("datagen", tr("datagen_title"), tr("datagen_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("datagen_params"))
        outer.addWidget(left)

        ll.addWidget(QLabel(tr("datagen_count")))
        self.count = QSpinBox()
        self.count.setRange(1, 10000)
        self.count.setValue(10)
        ll.addWidget(self.count)

        # Seed row
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel(tr("datagen_seed")))
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(0)
        self.seed.setSpecialValueText(tr("datagen_seed_random"))
        self.seed.setToolTip(tr("datagen_seed_tip"))
        seed_row.addWidget(self.seed, 1)
        ll.addLayout(seed_row)

        ll.addWidget(QLabel(tr("datagen_format")))
        self.fmt = QComboBox()
        self.fmt.addItems(["JSON", "CSV", "SQL", "XML", "YAML", "XLSX", "Python List"])
        ll.addWidget(self.fmt)

        ll.addWidget(QLabel(tr("datagen_locale")))
        self.locale = QComboBox()
        self.locale.addItems([
            tr("datagen_locale_ru"),
            tr("datagen_locale_en"),
            tr("datagen_locale_mixed"),
        ])
        ll.addWidget(self.locale)

        # Presets
        ll.addWidget(QLabel(tr("datagen_preset")))
        preset_row = QHBoxLayout()
        self.preset = QComboBox()
        self.preset.addItems([
            tr("datagen_preset_custom"),
            tr("datagen_preset_hr"),
            tr("datagen_preset_ecommerce"),
            tr("datagen_preset_crm"),
            tr("datagen_preset_finance"),
            tr("datagen_preset_geo"),
        ])
        preset_row.addWidget(self.preset, 1)
        apply_preset_btn = QPushButton(tr("datagen_preset_apply"))
        apply_preset_btn.clicked.connect(self._apply_preset)
        preset_row.addWidget(apply_preset_btn)
        ll.addLayout(preset_row)

        ll.addWidget(QLabel(tr("datagen_fields")))
        scroll = QScrollArea()
        scroll.setMaximumHeight(180)
        scroll.setWidgetResizable(True)
        fields_widget = QWidget()
        fields_layout = QVBoxLayout(fields_widget)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields = {}
        for f in FIELD_TYPES:
            cb = QCheckBox(f)
            cb.setChecked(f in ["id","name","email","phone","age","city","company","salary","active","date"])
            self.fields[f] = cb
            fields_layout.addWidget(cb)
        fields_layout.addStretch()
        scroll.setWidget(fields_widget)
        ll.addWidget(scroll)

        # FK checkbox
        self.fk_check = QCheckBox(tr("datagen_fk"))
        self.fk_check.setToolTip(tr("datagen_fk_tip"))
        ll.addWidget(self.fk_check)

        fk_row = QHBoxLayout()
        fk_row.addWidget(QLabel(tr("datagen_fk_count")))
        self.fk_count = QSpinBox()
        self.fk_count.setRange(1, 20)
        self.fk_count.setValue(3)
        fk_row.addWidget(self.fk_count)
        fk_row.addStretch()
        ll.addLayout(fk_row)

        source_label = QLabel(tr("datagen_source"))
        ll.addWidget(source_label)
        self.source = QComboBox()
        self.source.addItems([
            tr("datagen_source_local"),
            "randomuser.me",
            "dummyjson.com",
            "reqres.in",
            "jsonplaceholder.typicode.com",
            "restcountries.com",
            "quotable.io",
        ])
        self.source.currentIndexChanged.connect(self._on_source_changed)
        ll.addWidget(self.source)

        self.fetch_btn = QPushButton(tr("datagen_fetch_api"))
        self.fetch_btn.setObjectName("accent2")
        self.fetch_btn.clicked.connect(self._fetch_api_data)
        self.fetch_btn.setEnabled(False)
        ll.addWidget(self.fetch_btn)

        self.api_status = QLabel("")
        self.api_status.setObjectName("text_muted")
        self.api_status.setWordWrap(True)
        ll.addWidget(self.api_status)

        gen_btn = QPushButton(tr("datagen_generate"))
        gen_btn.setObjectName("accent")
        gen_btn.clicked.connect(self._generate)
        ll.addWidget(gen_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        ll.addWidget(self.progress)

        save_btn = QPushButton(tr("datagen_save"))
        save_btn.clicked.connect(self._save)
        ll.addWidget(save_btn)

        # cache hint row
        cache_row = QHBoxLayout()
        self.cache_info = QLabel("")
        self.cache_info.setObjectName("text_muted")
        self.cache_info.setWordWrap(True)
        cache_row.addWidget(self.cache_info, 1)
        clear_cache_btn = QPushButton(tr("datagen_clear_cache"))
        clear_cache_btn.setMaximumWidth(90)
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_row.addWidget(clear_cache_btn)
        ll.addLayout(cache_row)

        right, inner_right, rl = self.card(tr("datagen_result"))
        outer.addWidget(right, 1)
        self.output = QPlainTextEdit()
        self.output.setObjectName("code_output")
        self.output.setReadOnly(True)
        rl.addWidget(self.output)

    def _apply_preset(self):
        keys = ["custom","hr","ecommerce","crm","finance","geo"]
        idx = self.preset.currentIndex()
        preset_key = keys[idx] if idx < len(keys) else "custom"
        fields = PRESETS.get(preset_key)
        if fields is None:
            return
        for f, cb in self.fields.items():
            cb.setChecked(f in fields)

    def _on_source_changed(self, idx):
        is_api = idx > 0
        self.fetch_btn.setEnabled(is_api)
        if is_api:
            self.api_status.setText(self.tr("datagen_api_hint"))
            self._refresh_cache_info()
        else:
            self.api_status.setText("")
            self._api_cache = []
            self.cache_info.setText("")

    def _refresh_cache_info(self):
        source = self.source.currentText()
        key = source
        cached = _load_cache(key)
        if cached is not None:
            cnt = len(cached) if isinstance(cached, list) else len(cached.get("results", cached.get("users", cached.get("data", [])))) if isinstance(cached, dict) else 0
            # quotable cache is list of strings
            if isinstance(cached, list) and cached and isinstance(cached[0], str):
                cnt = len(cached)
            self.cache_info.setText(self.tr("datagen_cache_hit", n=cnt))
        else:
            any_cached = _load_cache_any_age(key)
            if any_cached is not None:
                self.cache_info.setText(self.tr("datagen_cache_stale"))
            else:
                self.cache_info.setText(self.tr("datagen_cache_miss"))

    def _clear_cache(self):
        try:
            for p in _cache_dir().glob("*.json"):
                p.unlink()
            self.cache_info.setText(self.tr("datagen_cache_cleared"))
            self.api_status.setText("")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ── API FETCHING ─────────────────────────────────────────────────────

    def _fetch_api_data(self):
        if not HAS_REQUESTS:
            QMessageBox.warning(self, "Error", "pip install requests")
            return
        source = self.source.currentText()
        count = min(self.count.value(), 100)
        self.fetch_btn.setEnabled(False)
        self.api_status.setText(self.tr("datagen_fetching"))
        self._api_cache = []

        if "randomuser" in source:
            url = API_SOURCES["randomuser.me"].format(count=count)
        elif "dummyjson" in source:
            url = API_SOURCES["dummyjson"].format(count=count)
        elif "reqres" in source:
            url = API_SOURCES["reqres"].format(count=count)
        elif "jsonplaceholder" in source:
            url = API_SOURCES["jsonplaceholder"]
        elif "restcountries" in source:
            url = API_SOURCES["restcountries"]
        elif "quotable" in source:
            url = API_SOURCES["quotable"].format(count=min(count, 20))
        else:
            return

        run_in_background(
            self._do_fetch, url, source,
            on_result=self._on_fetch_done,
            on_error=lambda e: self._on_fetch_error(str(e)),
        )

    def _do_fetch(self, url, source):
        r = _requests.get(url, timeout=15, headers={"User-Agent": "Automat/2.0"})
        r.raise_for_status()
        data = r.json()
        # save raw to disk cache immediately (worker thread — ok)
        _save_cache(source, data)
        return {"data": data, "source": source}

    def _on_fetch_done(self, result):
        data = result["data"]
        source = result["source"]
        users = []

        if "randomuser" in source:
            for u in data.get("results", []):
                users.append({
                    "first_name": u.get("name", {}).get("first", ""),
                    "last_name": u.get("name", {}).get("last", ""),
                    "email": u.get("email", ""),
                    "phone": u.get("phone", ""),
                    "city": u.get("location", {}).get("city", ""),
                    "country": u.get("location", {}).get("country", ""),
                    "age": u.get("dob", {}).get("age", 0),
                    "avatar": u.get("picture", {}).get("large", ""),
                    "gender": u.get("gender", ""),
                })
        elif "dummyjson" in source:
            for u in data.get("users", []):
                addr = u.get("address", {})
                users.append({
                    "first_name": u.get("firstName", ""),
                    "last_name": u.get("lastName", ""),
                    "email": u.get("email", ""),
                    "phone": u.get("phone", ""),
                    "city": addr.get("city", ""),
                    "country": addr.get("country", ""),
                    "age": u.get("age", 0),
                    "address": f"{addr.get('address', '')}, {addr.get('city', '')}",
                })
        elif "reqres" in source:
            for u in data.get("data", []):
                users.append({
                    "first_name": u.get("first_name", ""),
                    "last_name": u.get("last_name", ""),
                    "email": u.get("email", ""),
                    "avatar": u.get("avatar", ""),
                })
        elif "jsonplaceholder" in source:
            lst = data if isinstance(data, list) else data.get("users", [])
            for u in lst:
                name_parts = u.get("name", "").split()
                users.append({
                    "first_name": name_parts[0] if name_parts else "",
                    "last_name": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
                    "email": u.get("email", ""),
                    "phone": u.get("phone", ""),
                    "city": u.get("address", {}).get("city", ""),
                    "website": u.get("website", ""),
                    "company": u.get("company", {}).get("name", ""),
                })
        elif "restcountries" in source:
            for c in data if isinstance(data, list) else []:
                name = c.get("name", {}).get("common", "")
                capital = (c.get("capital") or [""])[0]
                currencies = list((c.get("currencies") or {}).keys())
                users.append({
                    "country": name,
                    "city": capital,
                    "currency": currencies[0] if currencies else "",
                })
            self._country_cache = users
            self._api_cache = users
            count = len(users)
            self.api_status.setText(self.tr("datagen_api_loaded", n=count))
            self.fetch_btn.setEnabled(True)
            log(EVENT_DATAGEN, STATUS_OK, f"API fetch: {source} ({count})", count)
            return
        elif "quotable" in source:
            quotes = data if isinstance(data, list) else data.get("results", [])
            self._quote_cache = [q.get("content", "") for q in quotes if q.get("content")]
            count = len(self._quote_cache)
            self.api_status.setText(self.tr("datagen_api_loaded", n=count))
            self.fetch_btn.setEnabled(True)
            log(EVENT_DATAGEN, STATUS_OK, f"API fetch: quotable ({count})", count)
            return

        self._api_cache = users
        count = len(users)
        self.api_status.setText(self.tr("datagen_api_loaded", n=count))
        self.fetch_btn.setEnabled(True)
        log(EVENT_DATAGEN, STATUS_OK, f"API fetch: {source} ({count})", count)

    def _on_fetch_error(self, error):
        source = self.source.currentText()
        # offline fallback — try any-age cache
        cached = _load_cache_any_age(source)
        if cached is not None:
            self.api_status.setText(self.tr("datagen_cache_offline"))
            # reuse _on_fetch_done path
            self._on_fetch_done({"data": cached, "source": source})
            # mark as offline
            self.cache_info.setText(self.tr("datagen_cache_offline_hint"))
            return
        self.api_status.setText(f"Error: {error}")
        self.fetch_btn.setEnabled(True)

    # ── VALUE GENERATION ─────────────────────────────────────────────────

    def _gen_value(self, field, i, locale_idx, rng):
        is_ru = (locale_idx == 0)
        is_en = (locale_idx == 1)
        is_mixed = (locale_idx == 2)

        def pick_ru_first():
            return rng.choice(FIRST_NAMES_RU_M + FIRST_NAMES_RU_F)

        def pick_ru_last():
            return rng.choice(LAST_NAMES_RU_M + LAST_NAMES_RU_F)

        def pick_en_first():
            return rng.choice(FIRST_NAMES_EN)

        def pick_en_last():
            return rng.choice(LAST_NAMES_EN)

        def pick_first():
            if is_mixed:
                return rng.choice([pick_ru_first(), pick_en_first()])
            return pick_ru_first() if is_ru else pick_en_first()

        def pick_last():
            if is_mixed:
                return rng.choice([pick_ru_last(), pick_en_last()])
            return pick_ru_last() if is_ru else pick_en_last()

        def pick_city():
            if is_mixed:
                return rng.choice(CITIES_RU + CITIES_EN)
            return rng.choice(CITIES_RU if is_ru else CITIES_EN)

        # API cache (random.choice still deterministic via rng if seed set — use rng.choice)
        if self._api_cache:
            api_user = rng.choice(self._api_cache)
            if field == "id": return i
            if field == "first_name": return api_user.get("first_name", pick_first())
            if field == "last_name": return api_user.get("last_name", pick_last())
            if field == "name":
                fn = api_user.get("first_name", pick_first())
                ln = api_user.get("last_name", pick_last())
                return f"{fn} {ln}"
            if field == "email":
                if api_user.get("email"):
                    return api_user["email"]
                fn = rng.choice(FIRST_NAMES_EN).lower()
                ln = rng.choice(LAST_NAMES_EN).lower()
                return f"{fn}.{ln}{rng.randint(1,999)}@example.com"
            if field == "phone": return api_user.get("phone", f"+7{rng.randint(900,999)}{rng.randint(1000000,9999999)}")
            if field == "age": return api_user.get("age", rng.randint(18, 70))
            if field == "gender": return api_user.get("gender", rng.choice(["male","female"]))
            if field == "city": return api_user.get("city", pick_city())
            if field == "country": return api_user.get("country", rng.choice(COUNTRIES))
            if field == "currency": return api_user.get("currency", rng.choice(CURRENCIES))
            if field == "address":
                if api_user.get("address"):
                    return api_user["address"]
                street = rng.choice(STREETS)
                return f"{street}, {rng.randint(1,200)}"
            if field == "avatar": return api_user.get("avatar", "")
            if field == "website": return api_user.get("website", f"https://{rng.choice(LAST_NAMES_EN).lower()}.example.com")
            if field == "company": return api_user.get("company", rng.choice(COMPANIES))

        # Local generation
        if field == "id": return i
        if field == "first_name": return pick_first()
        if field == "last_name": return pick_last()
        if field == "name": return f"{pick_first()} {pick_last()}"
        if field == "email":
            domains = ["example.com","gmail.com","mail.ru","yandex.ru","outlook.com","proton.me"]
            fn = rng.choice(FIRST_NAMES_EN).lower()
            ln = rng.choice(LAST_NAMES_EN).lower()
            return f"{fn}.{ln}{rng.randint(1,999)}@{rng.choice(domains)}"
        if field == "phone":
            use_ru = is_ru or (is_mixed and rng.random() < 0.5)
            if use_ru:
                return f"+7 ({rng.randint(900,999)}) {rng.randint(100,999)}-{rng.randint(10,99)}-{rng.randint(10,99)}"
            return f"+1 ({rng.randint(200,999)}) {rng.randint(100,999)}-{rng.randint(1000,9999)}"
        if field == "age": return rng.randint(18, 75)
        if field == "gender": return rng.choice(["male","female","other"])
        if field == "birthdate":
            d = datetime(1970, 1, 1) + timedelta(days=rng.randint(0, 18000))
            return d.strftime("%Y-%m-%d")
        if field == "city": return pick_city()
        if field == "country": return rng.choice(COUNTRIES)
        if field == "currency": return rng.choice(CURRENCIES)
        if field == "address":
            street = rng.choice(STREETS)
            return f"{street}, {rng.randint(1,200)}"
        if field == "lat": return round(rng.uniform(-90, 90), 6)
        if field == "lng": return round(rng.uniform(-180, 180), 6)
        if field == "company": return rng.choice(COMPANIES)
        if field == "job_title": return rng.choice(JOB_TITLES)
        if field == "product": return rng.choice(PRODUCTS)
        if field == "salary": return rng.randint(30000, 500000)
        if field == "uuid": return str(uuid.UUID(int=rng.getrandbits(128)))
        if field == "ipv4": return str(ipaddress.IPv4Address(rng.randint(0, 2**32 - 1)))
        if field == "ipv6": return str(ipaddress.IPv6Address(rng.getrandbits(128)))
        if field == "mac": return ":".join(f"{rng.randint(0,255):02x}" for _ in range(6))
        if field == "active": return rng.choice([True, False])
        if field == "date":
            d = datetime(2020, 1, 1) + timedelta(days=rng.randint(0, 2000))
            return d.strftime(rng.choice(["%Y-%m-%d","%d.%m.%Y","%m/%d/%Y"]))
        if field == "website":
            return f"https://{rng.choice(LAST_NAMES_EN).lower()}.example.com"
        if field == "credit_card":
            # Visa/Master/Mir prefixes with valid Luhn
            prefix = rng.choice(["4", "51", "52", "53", "54", "55", "2200", "2204"])
            length = 16
            return _gen_luhn(rng, prefix, length)
        if field == "inn":
            return _gen_inn_12(rng) if rng.random() < 0.5 else _gen_inn_10(rng)
        if field == "snils": return _gen_snils(rng)
        if field == "passport": return _gen_passport(rng)
        if field == "iban": return _gen_iban(rng)
        if field == "color": return rng.choice(COLORS)
        if field == "avatar":
            # deterministic dicebear URL
            seed = rng.choice(FIRST_NAMES_EN) + str(rng.randint(1, 9999))
            return f"https://api.dicebear.com/7.x/avataaars/svg?seed={seed}"
        if field == "description":
            words = ["experienced","skilled","creative","dedicated","passionate","motivated","innovative",
                     "analytical","detail-oriented","team-player","leader","problem-solver","fast-learner",
                     "adaptable","organized","reliable","proactive","collaborative","strategic","dynamic"]
            nouns = ["engineer","developer","manager","designer","analyst","architect","consultant",
                     "specialist","director","coordinator","lead","consultant","strategist","researcher"]
            return f"A {rng.choice(words)} {rng.choice(nouns)} with expertise in {rng.choice(['Python','JavaScript','SQL','AWS','Docker','Kubernetes','React','Go','Rust','TypeScript'])}"
        if field == "amount": return round(rng.uniform(10, 10000), 2)
        if field == "text":
            if self._quote_cache:
                return rng.choice(self._quote_cache)
            lex = ["lorem","ipsum","dolor","sit","amet","consectetur","adipiscing","elit",
                   "sed","do","eiusmod","tempor","incididunt","ut","labore","et","dolore",
                   "magna","aliqua","enim","ad","minim","veniam","quis","nostrud","exercitation",
                   "ullamco","laboris","nisi","aliquip","ex","ea","commodo","consequat"]
            return " ".join(rng.choice(lex) for _ in range(rng.randint(5, 15)))
        return None

    # ── GENERATION ───────────────────────────────────────────────────────

    def _generate(self):
        tr = self.tr
        n = self.count.value()
        locale_idx = self.locale.currentIndex()
        active_fields = [f for f, cb in self.fields.items() if cb.isChecked()]
        if not active_fields:
            QMessageBox.warning(self, tr("datagen_error"), tr("datagen_select_field"))
            return
        seed_val = self.seed.value()
        rng = random.Random(seed_val) if seed_val != 0 else random

        # FK mode: generate second table orders
        fk_enabled = self.fk_check.isChecked()
        orders_per_user = self.fk_count.value() if fk_enabled else 0

        # progress bar for large n
        show_progress = n >= 500
        if show_progress:
            self.progress.setVisible(True)
            self.progress.setRange(0, n)
            self.progress.setValue(0)
            self.progress.setFormat(f"{tr('datagen_progress')} %p%")
        else:
            self.progress.setVisible(False)
        QApplication.processEvents()

        data = []
        orders = []
        order_id = 1
        chunk = max(1, n // 100)
        for i in range(1, n + 1):
            row = {}
            for f in active_fields:
                v = self._gen_value(f, i, locale_idx, rng)
                if v is not None:
                    row[f] = v
            data.append(row)
            if fk_enabled:
                for _ in range(rng.randint(1, orders_per_user) if orders_per_user > 1 else 1):
                    orders.append({
                        "id": order_id,
                        "user_id": i,
                        "product": rng.choice(PRODUCTS),
                        "amount": round(rng.uniform(10, 5000), 2),
                        "currency": rng.choice(CURRENCIES),
                        "date": (datetime(2023, 1, 1) + timedelta(days=rng.randint(0, 900))).strftime("%Y-%m-%d"),
                    })
                    order_id += 1
            if show_progress and (i % chunk == 0 or i == n):
                self.progress.setValue(i)
                QApplication.processEvents()
        if show_progress:
            QTimer.singleShot(1200, lambda: self.progress.setVisible(False))

        fmt = self.fmt.currentText()
        if fmt == "JSON":
            if fk_enabled:
                text = json.dumps({"users": data, "orders": orders}, ensure_ascii=False, indent=2)
            else:
                text = json.dumps(data, ensure_ascii=False, indent=2)
        elif fmt == "CSV":
            output = io.StringIO()
            if fk_enabled:
                # users
                if data:
                    w = csv.DictWriter(output, fieldnames=list(data[0].keys()), quoting=csv.QUOTE_MINIMAL)
                    w.writeheader()
                    w.writerows(data)
                    output.write("\n")
                if orders:
                    w2 = csv.DictWriter(output, fieldnames=list(orders[0].keys()), quoting=csv.QUOTE_MINIMAL)
                    w2.writeheader()
                    w2.writerows(orders)
            else:
                if data:
                    w = csv.DictWriter(output, fieldnames=list(data[0].keys()), quoting=csv.QUOTE_MINIMAL)
                    w.writeheader()
                    w.writerows(data)
            text = output.getvalue()
        elif fmt == "SQL":
            lines = []
            if data:
                cols = list(data[0].keys())
                col_defs = ", ".join(f"{k} {SQL_TYPES.get(k, 'TEXT')}" for k in cols)
                lines.append(f"CREATE TABLE users ({col_defs});")
                for r in data:
                    vals = ", ".join(self._sql_val(r[k]) for k in cols)
                    lines.append(f"INSERT INTO users ({','.join(cols)}) VALUES ({vals});")
            if fk_enabled and orders:
                ocols = list(orders[0].keys())
                odefs = ", ".join(f"{k} {SQL_TYPES.get(k, 'TEXT')}" for k in ocols)
                # FK constraint
                lines.append(f"CREATE TABLE orders ({odefs}, FOREIGN KEY(user_id) REFERENCES users(id));")
                for r in orders:
                    vals = ", ".join(self._sql_val(r[k]) for k in ocols)
                    lines.append(f"INSERT INTO orders ({','.join(ocols)}) VALUES ({vals});")
            text = "\n".join(lines)
        elif fmt == "XML":
            text = "<data>\n"
            if fk_enabled:
                text += "  <users>\n"
                for r in data:
                    text += "    <record>\n"
                    for k, v in r.items():
                        escaped = html_mod.escape(str(v))
                        text += f"      <{k}>{escaped}</{k}>\n"
                    text += "    </record>\n"
                text += "  </users>\n  <orders>\n"
                for r in orders:
                    text += "    <record>\n"
                    for k, v in r.items():
                        escaped = html_mod.escape(str(v))
                        text += f"      <{k}>{escaped}</{k}>\n"
                    text += "    </record>\n"
                text += "  </orders>\n"
            else:
                for r in data:
                    text += "  <record>\n"
                    for k, v in r.items():
                        escaped = html_mod.escape(str(v))
                        text += f"    <{k}>{escaped}</{k}>\n"
                    text += "  </record>\n"
            text += "</data>"
        elif fmt == "YAML":
            if not HAS_YAML:
                text = tr("datagen_yaml_need") + "\n\n" + json.dumps(data, ensure_ascii=False, indent=2)
            else:
                payload = {"users": data, "orders": orders} if fk_enabled else data
                text = _yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        elif fmt == "XLSX":
            if not HAS_OPENPYXL:
                text = tr("datagen_xlsx_need")
            else:
                # store temp path message — actual file via Save dialog is binary, so show preview as CSV
                output = io.StringIO()
                if data:
                    w = csv.DictWriter(output, fieldnames=list(data[0].keys()))
                    w.writeheader()
                    w.writerows(data)
                text = tr("datagen_xlsx_preview") + "\n\n" + output.getvalue()
                # keep workbook for save handler
                self._xlsx_data = data
                self._xlsx_orders = orders if fk_enabled else []
        else:
            text = str({"users": data, "orders": orders} if fk_enabled else data)

        self.output.setPlainText(text)
        suffix = f" + {len(orders)} orders" if fk_enabled else ""
        log(EVENT_DATAGEN, STATUS_OK, f"{n} records{suffix}", n)

    def _sql_val(self, v):
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, (int, float)):
            return str(v)
        # escape single quotes
        s = str(v).replace("'", "''")
        return f"'{s}'"

    def _save(self):
        tr = self.tr
        fmt = self.fmt.currentText()
        if fmt == "XLSX" and HAS_OPENPYXL and hasattr(self, "_xlsx_data"):
            fp, _ = QFileDialog.getSaveFileName(self, tr("datagen_save_dialog"), "generated.xlsx", "Excel (*.xlsx)")
            if fp:
                wb = _openpyxl.Workbook()
                ws = wb.active
                ws.title = "users"
                if self._xlsx_data:
                    ws.append(list(self._xlsx_data[0].keys()))
                    for r in self._xlsx_data:
                        ws.append(list(r.values()))
                if self._xlsx_orders:
                    ws2 = wb.create_sheet("orders")
                    ws2.append(list(self._xlsx_orders[0].keys()))
                    for r in self._xlsx_orders:
                        ws2.append(list(r.values()))
                wb.save(fp)
                QMessageBox.information(self, tr("datagen_saved"), f"Saved: {fp}")
            return
        fp, _ = QFileDialog.getSaveFileName(self, tr("datagen_save_dialog"), "", tr("datagen_save_all_files"))
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.output.toPlainText())
            QMessageBox.information(self, tr("datagen_saved"), f"Saved: {fp}")
