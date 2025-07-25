"""
in this file, we define the laws that we should adhere to and then implement it into patterns 
and then add them to the analysis engine.

the laws to be implemented are:

personal Identity:
- full name (already exists under PERSON)
- first name / family name  (already exists under PERSON)
- sex (to be added using language models)
- birth date   (already exists under DATE_TIME)
- birth place (already exists under LOCATION)
- nationality (already exists under NRP)

- CIN (or any national ID) (to be added using language models)
- Passeport (to be added using language models)
- carte de séjour (to be added using language models)
- driving license (to be added using language models)


- email Adresse (to be added using language models)
- phone number (already exists under PHONE_NUMBER)
- postal address
- postal code



- RIB / IBAN (already exists under IBAN_CODE)
- bank account number 
- credit card number (already exists under CREDIT_CARD)
- income


-ilness/ medical history
- blood type
- biometric data


-job
-company name
-insurance number
-internal ID


-usernames
-ip Adresse (already exists under IP_ADDRESS)
Cookies, Device ID
Geolocation data (already exists under LOCATION)

-political views (NRP)
-religious beliefs (NRP)
-union membership (NRP)
-sexual orientation (shouwld i mention it? because of muslim culture)
-genetic data 



"""

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult, EntityRecognizer, AnalyzerEngine
import spacy, re
#CIN
CIN_PATTERN = Pattern(
    name="CIN",
    regex=r"\b[A-Z]{1,2}[0-9]{5,7}\b",
    score=0.8)
#PASSPORT
PASSPORT_PATTERN = Pattern(
    name="PASSPORT",
    regex=r"\b[A-Z]{1}[0-9]{7}\b", # this is just for moroccan passports, it can be generalized with context later since most passport numbers deffer
    score=0.8)


# Carte de séjour
CARTE_DE_SEJOUR_PATTERN = Pattern(
    name="Carte de séjour",
    regex=r"\b[0-9]{9,10}\b",  # This is just the frensh carte de séjour format, it can be generalized with context later
    score=0.5)

# Driving License in morocco don t have a specific format, so we will use context to detect it

DRIVER_LICENSE_PATTERN = Pattern(
    name="DRIVER_LICENSE_PATTERN",
    regex=r"\b(?=\S*\d)\S{6,20}\b",  # let the context decide if it is a driving license or not
    score=0.4 # Moderate confidence
)

DRIVER_LICENSE_RECOGNIZER = PatternRecognizer(
    supported_entity="DRIVER_LICENSE",
    patterns=[DRIVER_LICENSE_PATTERN],
    context=[
        "driver's license",
        "driving licence",
        "license number",
        "driver's license number",
        "DLN",
        "permit ID",
        "license no."
    ],
    supported_language="en",
    name="driver_license_contextual"
)


#Postal Code
POSTAL_CODE_PATTERN = Pattern(
    name="Postal Code",
    regex=r"\b[0-9]{5}\b",  # This is just the moroccan postal code format we can add context to assure it is a postal code
    score=0.4)

POSTAL_CODE_RECOGNIZER = PatternRecognizer(
    supported_entity="POSTAL_CODE",
    patterns=[POSTAL_CODE_PATTERN],
    context=["postal code", "zip code", "postcode", "CP", "code postal"],  
    supported_language="en",
    name="postal_code_recognizer"
)


#Blood Type
BLOOD_TYPE_PATTERN = Pattern(
    name="Blood Type",
    regex=r"\b(?:A|B|AB|O)(?:[+-]|(?:\s?(?:positive|negative|pos|neg)))|Rh(?:\s?(?:null|positive|negative|pos|neg))\b",
    score=0.85)
#IBAN custome for morocco
IBAN_PATTERN = Pattern(
    name="moroccan_iban",
    regex = r"\bMA(?:\s*\d\s*){20,28}\b",
    score=0.9
)

IBAN_RECOGNIZER = PatternRecognizer(
    supported_entity="MIBAN_CODE",
    patterns=[IBAN_PATTERN],
    context=["IBAN", "account", "bank", "moroccan", "morocco"],
    supported_language="en"
)

#Insureance Number we ll use context to detect it
INSUREANCE_PATERN = Pattern(
    name="INSURANCE_PATTERN",
    regex=r"\b(?=\S*[0-9])[\w\-]{6,20}\b",
    score=0.4  # base score; boosted by context
)

INSURANCE_RECOGNIZER = PatternRecognizer(
    supported_entity="INSURANCE_NUMBER",
    patterns=[INSUREANCE_PATERN],
    context=[
        "insurance number", "policy number", "insurance id",
        "numéro d'assurance", "CNOPS", "mutuelle","insurance",
        "policy number", "policy id", "insurance policy",
        "beneficiary id", "police d'assurance", "coverage number"
    ],
    supported_language="en",
    name="insurance_number_recognizer"
)
#TIN
TIN_PATTERN = Pattern(
    name="Tax Identification Number",
    regex=r"\b[0-9]{15}\b",
    score=0.5)

#Internal ID we ll use context
INTERNAL_ID_PATTERN = Pattern(
    name="Internal ID",
    regex=r"EMP-[0-9]{4,6}",
    score=0.5)

#Gender 
GENDER_PATTERN = Pattern(
    name="Gender",
    regex=r"\b(?:male|female)\b",
    score=0.5
)
GENDER_RECOGNIZER = PatternRecognizer(
    supported_entity="GENDER_DECLARED",
    patterns=[GENDER_PATTERN],
    name="gender_recognizer",
    context=["sex", "gender", "assigned", "identity"],
    supported_language="en"
)

class ImpliedGender(EntityRecognizer):
    def __init__(self):
        super().__init__(supported_entities=["IMPLIED_GENDER"])
        self.gender_words = {
            "he", "she", "his", "her", "him", "hers",
            "mr\\.", "mrs\\.", "miss", "ms\\.", "sir", "madam"
        }
        # Precompile regex for performance
        self.pattern = re.compile(
            r"\b(" + "|".join(self.gender_words) + r")\b", flags=re.IGNORECASE
        )

    def analyze(self, text, entities, nlp_artifacts=None):
        results = []
        for match in self.pattern.finditer(text):
            results.append(
                RecognizerResult(
                    entity_type="IMPLIED_GENDER",
                    start=match.start(),
                    end=match.end(),
                    score=0.75
                )
            )
        return results
    

# INCOME 
INCOME_PATTERN = Pattern(
    name="INCOME_PATTERN",
    regex=r"\b(?:\$|€|MAD|USD|DHS)?\s?\d{3,6}(?:[.,]?\d{3})*(?:\s?(MAD|USD|DHS|EUR|K|k|M|m))?\b",
    score=0.4  # Base score — context boosts relevance
)

INCOME_RECOGNIZER = PatternRecognizer(
    supported_entity="INCOME_AMOUNT",
    patterns=[INCOME_PATTERN],
    context=[
        "salary", "income", "monthly income", "net income",
        "revenue", "wage", "paycheck", "annual salary", "earning",
        "salaire", "revenu", "paye", "remuneration", "per month", "per year"
    ],
    supported_language="en",
    name="income_contextual"
)

#Medical records this is the most challenging one since it can vary a lot so we use a pre-trained model
_SCI_NLP = None
def _get_sci_nlp():
    global _SCI_NLP
    if _SCI_NLP is None:
        _SCI_NLP = spacy.load("en_core_sci_sm")
    return _SCI_NLP
class MedRecRecognizer(EntityRecognizer):

    DEFAULT_KEYWORDS = (
        "disease", "syndrome", "cancer", "tumor", "tumour", "diabetes",
        "asthma", "hypertension", "kidney", "renal", "hepatitis", "hiv",
        "aids", "covid", "infection", "stroke", "depression", "anxiety"
    )

    def __init__(self, accept_labels=None, extra_terms=None):
        super().__init__(supported_entities=["MEDICAL_CONDITION"])
        self.nlp = _get_sci_nlp()
        self.accept_labels = {l.lower() for l in (accept_labels or [])}
        self.extra_terms = {t.lower() for t in (extra_terms or [])}
        self.keywords = {k.lower() for k in self.DEFAULT_KEYWORDS} | self.extra_terms

    def load(self) -> bool: 
        return True

    def analyze(self, text, entities, nlp_artifacts=None):
        results = []
        lowered = text.lower()

        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_.lower() in {"disease", "condition", "disorder"}:
                label_ok = (not self.accept_labels) or (ent.label_.lower() in self.accept_labels)
                keyword_in_text = any(k in ent.text.lower() for k in self.keywords)

                if label_ok or keyword_in_text:
                    score = 0.9 if keyword_in_text else 0.75
                    results.append(
                        RecognizerResult(
                            entity_type="MEDICAL_CONDITION",
                            start=ent.start_char,
                            end=ent.end_char,
                            score=score,
                        )
                    )

        for kw in self.keywords:
            start = lowered.find(kw)
            while start != -1:
                end = start + len(kw)
                if not any(r.start == start and r.end == end for r in results):
                    results.append(
                        RecognizerResult(
                            entity_type="MEDICAL_CONDITION",
                            start=start,
                            end=end,
                            score=0.6,
                        )
                    )
                start = lowered.find(kw, start + 1)

        return results


# job title (just using a dictionary )
JOBS = set()
with open("assets/jobs.csv") as f:
    for line in f:
        splited = line.strip().split(",")
        if len(splited) > 3:
            JOBS.add(splited[2].strip().lower())


class JobTitleRecognizer(EntityRecognizer):
    def __init__(self):
        super().__init__(supported_entities=["JOB_TITLE"])
        self.job_titles = JOBS
    def analyze(self, text, entities, nlp_artifacts=None):
        results = []
        lowered = text.lower()
        for job in self.job_titles:
            job = job.lower()
            if job in lowered:
                start = lowered.find(job)
                while start >= 0:
                    results.append(
                        RecognizerResult(
                            entity_type="JOB_TITLE",
                            start=start,
                            end=start + len(job),
                            score=0.8
                        )
                    )
                    start = lowered.find(job, start + 1)
        return results
#add it to the analyzer
#package it into a function
def get_analyzer():
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(IBAN_RECOGNIZER)
    analyzer.registry.add_recognizer(DRIVER_LICENSE_RECOGNIZER)
    analyzer.registry.add_recognizer(INSURANCE_RECOGNIZER)
    analyzer.registry.add_recognizer(INCOME_RECOGNIZER)
    analyzer.registry.add_recognizer(GENDER_RECOGNIZER)
    analyzer.registry.add_recognizer(ImpliedGender())
    analyzer.registry.add_recognizer(MedRecRecognizer())
    analyzer.registry.add_recognizer(JobTitleRecognizer())

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="CIN",
        patterns=[CIN_PATTERN]
    ))

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="PASSPORT",
        patterns=[PASSPORT_PATTERN]
    ))

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="CARTE_DE_SEJOUR",
        patterns=[CARTE_DE_SEJOUR_PATTERN]
    ))

    analyzer.registry.add_recognizer(POSTAL_CODE_RECOGNIZER)

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="BLOOD_TYPE",
        patterns=[BLOOD_TYPE_PATTERN]
    ))

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="TIN",
        patterns=[TIN_PATTERN]
    ))

    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="INTERNAL_ID",
        patterns=[INTERNAL_ID_PATTERN]
    ))
    
    return analyzer