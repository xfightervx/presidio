import unittest
from core import get_analyzer

class TestEntities(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer = get_analyzer()

    def assert_detected(self, text, expected_entity):
        results = self.analyzer.analyze(text=text, language="en")
        self.assertTrue(
            any(r.entity_type == expected_entity for r in results),
            f"Expected {expected_entity} not found in: '{text}'"
        )

    def test_cin(self):
        self.assert_detected("My CIN is AB123456", "CIN")
    def test_passport(self):
        self.assert_detected("His passport number is X1234567", "PASSPORT")
    def test_carte_de_sejour(self):
        self.assert_detected("Carte de séjour: 1234567890", "CARTE_DE_SEJOUR")
    def test_driver_license(self):
        self.assert_detected("Driving licence: 01/9876543", "DRIVER_LICENSE")
    def test_insurance_number(self):
        self.assert_detected("Policy number: CNOPS-88220", "INSURANCE_NUMBER")
    def test_income(self):
        self.assert_detected("She earns 15,000 MAD per month.", "INCOME_AMOUNT")
    def test_postal_code(self):
        self.assert_detected("He lives in postal code 20250", "POSTAL_CODE")
    def test_blood_type(self):
        self.assert_detected("Blood type: AB+", "BLOOD_TYPE")
    def test_tin(self):
        self.assert_detected("TIN: 123456789012345", "TIN")
    def test_internal_id(self):
        self.assert_detected("Internal ID: EMP-002345", "INTERNAL_ID")
    def test_job_title(self):
        self.assert_detected("He works as a software engineer.", "JOB_TITLE")
    def test_medical_condition(self):
        test_cases = [
            ("Patient has chronic kidney disease.", "MEDICAL_CONDITION"),
            ("He was diagnosed with type 2 diabetes.", "MEDICAL_CONDITION"),
            ("She suffers from asthma.", "MEDICAL_CONDITION"),
            ("The tumor was malignant.", "MEDICAL_CONDITION"),
            ("Symptoms include hypertension and fatigue.", "MEDICAL_CONDITION"),
        ]   
        for text, expected in test_cases:
            with self.subTest(text=text):
                self.assert_detected(text, expected)
    def test_gender_declared(self):
        self.assert_detected("Sex: Female", "GENDER_DECLARED")
    def test_implied_gender(self):
        self.assert_detected("She went to the market.", "IMPLIED_GENDER")
    def test_email_address(self):
        self.assert_detected("Contact me at someone@example.com", "EMAIL_ADDRESS")
    def test_phone_number(self):
        self.assert_detected("My number is +212 661-234567", "PHONE_NUMBER")
    def test_credit_card(self):
        self.assert_detected("Card number: 4111 1111 1111 1111", "CREDIT_CARD")
    def test_iban_code(self):
        self.assert_detected("IBAN: MA64011519000001205000534921", "MIBAN_CODE")
    def test_ip_address(self):
        self.assert_detected("Connect to 192.168.1.1", "IP_ADDRESS")
    def test_person(self):
        self.assert_detected("My name is Ahmed Benali", "PERSON")
    def test_location(self):
        self.assert_detected("I live in Casablanca", "LOCATION")
    def test_nrp(self):
        self.assert_detected("She is Moroccan", "NRP")
    def test_date_time(self):
        self.assert_detected("He was born on 12/06/1995", "DATE_TIME")
