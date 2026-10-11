"""Unit tests for Stage 1 (regex extraction)."""

import pytest

from src.core.extraction import ContactInfo, ContentExtractor, RawProfile

SAMPLE_CV = """\
# Jane Doe
jane.doe@example.com | +57 300 123 4567

## Summary
Backend engineer who loves clean APIs.

## Technical Skills
Python, JS, React.js, Node.js, PostgreSQL, sklearn, Git, R

## Experience
- Senior Developer at ACME (2019 - 2022)
- Built REST APIs with Django and Docker on AWS

## Education
B.Sc. Computer Science, Universidad del Valle, 2018

## Certifications
* AWS Certified Cloud Practitioner
* Scrum Master
"""


@pytest.fixture
def extractor() -> ContentExtractor:
    return ContentExtractor()


# ------------------------------------------------------------ find_section

class TestFindSection:
    def test_returns_body_until_next_header(self, extractor):
        body = extractor.find_section("Education", SAMPLE_CV)
        assert body == "B.Sc. Computer Science, Universidad del Valle, 2018"

    @pytest.mark.parametrize("header", ["education", "EDUCATION", "Education"])
    def test_case_insensitive(self, extractor, header):
        assert "Universidad del Valle" in extractor.find_section(header, SAMPLE_CV)

    @pytest.mark.parametrize("cv", [
        "Education:\nMIT",
        "EDUCATION\nMIT",
        "## Education\nMIT",
        "**Education**\nMIT",
        "**Education:**\nMIT",
    ])
    def test_header_decorations(self, extractor, cv):
        assert extractor.find_section("Education", cv) == "MIT"

    def test_inline_content_after_colon(self, extractor):
        assert extractor.find_section("Skills", "Skills: Python, SQL\n") == "Python, SQL"

    def test_missing_section_returns_empty(self, extractor):
        assert extractor.find_section("Experience", "Education\nMIT") == ""

    def test_empty_text_and_header(self, extractor):
        assert extractor.find_section("Education", "") == ""
        assert extractor.find_section("", SAMPLE_CV) == ""

    def test_header_word_inside_sentence_is_not_a_header(self, extractor):
        text = "Experience with Python\nEducation\nMIT"
        assert extractor.find_section("Experience", text) == ""

    def test_windows_line_endings(self, extractor):
        assert extractor.find_section("Education", "Education\r\nMIT\r\n") == "MIT"

    def test_unknown_header_is_supported(self, extractor):
        text = "Hobbies\nChess\nEducation\nMIT"
        assert extractor.find_section("Hobbies", text) == "Chess"

    def test_spanish_headers(self, extractor):
        text = "Educación\nUniversidad Nacional\nExperiencia\nDev"
        assert extractor.extract_education(text) == ("Universidad Nacional",)
        assert extractor.extract_experience(text) == ("Dev",)


# ----------------------------------------------------------------- contact

class TestContact:
    def test_full_contact(self, extractor):
        assert extractor.extract_contact(SAMPLE_CV) == ContactInfo(
            name="Jane Doe", email="jane.doe@example.com", phone="+57 300 123 4567"
        )

    @pytest.mark.parametrize("phone", [
        "+57 300 123 4567", "(300) 123-4567", "300-123-4567",
        "+1 (415) 555-2671", "3001234567", "300.123.4567",
    ])
    def test_phone_formats(self, extractor, phone):
        assert extractor.extract_contact(f"John Smith\nTel: {phone}\n").phone == phone

    def test_date_range_is_not_a_phone(self, extractor):
        assert extractor.extract_contact("John Smith\n2018 - 2021\n").phone == ""

    def test_labelled_name(self, extractor):
        assert extractor.extract_contact("Name: María Pérez\n").name == "María Pérez"

    def test_accented_name(self, extractor):
        assert extractor.extract_contact("José Núñez\njose@x.co\n").name == "José Núñez"

    def test_name_skips_resume_title_and_headers(self, extractor):
        assert extractor.extract_contact("Resume\nSummary\nAda Lovelace\n").name == "Ada Lovelace"

    def test_missing_fields_are_empty_strings(self, extractor):
        assert extractor.extract_contact("") == ContactInfo(name="", email="", phone="")

    def test_email_variants(self, extractor):
        assert extractor.extract_contact("a+b.c@sub.dom-ain.org").email == "a+b.c@sub.dom-ain.org"


# ------------------------------------------------------ list-like sections

class TestEntries:
    def test_education(self, extractor):
        assert extractor.extract_education(SAMPLE_CV) == (
            "B.Sc. Computer Science, Universidad del Valle, 2018",
        )

    def test_experience_strips_bullets(self, extractor):
        assert extractor.extract_experience(SAMPLE_CV) == (
            "Senior Developer at ACME (2019 - 2022)",
            "Built REST APIs with Django and Docker on AWS",
        )

    def test_certifications(self, extractor):
        assert extractor.extract_certifications(SAMPLE_CV) == (
            "AWS Certified Cloud Practitioner",
            "Scrum Master",
        )

    def test_rule_lines_and_blanks_are_dropped(self, extractor):
        text = "Experience\n----------\n\n- Dev\n\n"
        assert extractor.extract_experience(text) == ("Dev",)

    def test_missing_sections_give_empty_tuples(self, extractor):
        assert extractor.extract_experience("nothing here") == ()
        assert extractor.extract_certifications("nothing here") == ()


# ------------------------------------------------------------------ skills

class TestSkills:
    @pytest.mark.parametrize("text, expected", [
        ("I know JS", "JS"),
        ("I know JavaScript", "JavaScript"),
        ("I know java script", "java script"),
        ("I know React.js", "React.js"),
        ("I know ReactJS", "ReactJS"),
        ("I know Node.js", "Node.js"),
        ("I know NodeJS", "NodeJS"),
        ("I know sklearn", "sklearn"),
        ("I know scikit-learn", "scikit-learn"),
        ("I know Scikit Learn", "Scikit Learn"),
        ("I know Spring Boot", "Spring Boot"),
        ("I know PostgreSQL", "PostgreSQL"),
        ("I know Postgres", "Postgres"),
        ("I know Power BI", "Power BI"),
        ("I know PowerBI", "PowerBI"),
        ("I know Amazon Web Services", "Amazon Web Services"),
        ("I know GitHub Actions", "GitHub Actions"),
        ("I know k8s", "k8s"),
        ("I know CloudFormation", "CloudFormation"),
        ("I know TensorFlow", "TensorFlow"),
        ("I know PyTorch", "PyTorch"),
        ("I know RESTful APIs", "RESTful APIs"),
        ("I know MS Excel", "MS Excel"),
        ("I know Excel", "Excel"),
        ("I know EXCEL", "EXCEL"),
        ("I know TypeScript", "TypeScript"),
        ("I know Vue.js", "Vue.js"),
        ("I know Python3", "Python3"),
        ("I know Redis", "Redis"),
        ("I know Cassandra", "Cassandra"),
        ("I know Casandra", "Casandra"),
    ])
    def test_single_variant_is_returned_as_written(self, extractor, text, expected):
        assert extractor.extract_skills(text) == (expected,)

    def test_case_insensitive(self, extractor):
        assert extractor.extract_skills("docker and DOCKER and Docker") == ("docker",)

    def test_sql_not_matched_inside_other_databases(self, extractor):
        assert extractor.extract_skills("PostgreSQL MySQL NoSQL") == (
            "PostgreSQL", "MySQL", "NoSQL",
        )

    def test_plain_sql_is_matched(self, extractor):
        assert extractor.extract_skills("Strong SQL skills") == ("SQL",)

    def test_git_not_matched_inside_github_or_gitlab(self, extractor):
        assert extractor.extract_skills("GitHub and GitLab") == ("GitLab",)
        assert extractor.extract_skills("Git and GitHub") == ("Git",)

    def test_js_not_matched_inside_framework_names(self, extractor):
        assert extractor.extract_skills("Node.js") == ("Node.js",)
        assert extractor.extract_skills("React.js") == ("React.js",)

    def test_excel_verb_and_excellent_are_not_matched(self, extractor):
        assert extractor.extract_skills("Students excel at math") == ()
        assert extractor.extract_skills("EXCELLENT communicator") == ()

    def test_single_letter_r_only_in_skills_section(self, extractor):
        assert extractor.extract_skills("Skills\nPython, R, SQL\n") == ("Python", "SQL", "R")
        assert extractor.extract_skills("Worked on R&D and plan R") == ()

    def test_order_of_first_appearance_and_deduplication(self, extractor):
        assert extractor.extract_skills("Docker, Python, docker, PYTHON, Git") == (
            "Docker", "Python", "Git",
        )

    def test_dedup_ignores_dots_and_spaces(self, extractor):
        # Same spelling up to '.', '-' and spaces collapses to one entry...
        assert extractor.extract_skills("React.js and ReactJS and React js") == ("React.js",)
        # ...but distinct variants (React vs React.js) are left to the Stage 2 FST.
        assert extractor.extract_skills("React and React.js") == ("React", "React.js")

    def test_skills_found_in_experience_text(self, extractor):
        assert "Django" in extractor.extract_skills(SAMPLE_CV)

    def test_no_skills(self, extractor):
        assert extractor.extract_skills("") == ()
        assert extractor.extract_skills("I like cooking") == ()


# ----------------------------------------------------------------- extract

class TestExtract:
    def test_full_cv(self, extractor):
        raw = extractor.extract(SAMPLE_CV)
        assert isinstance(raw, RawProfile)
        assert raw.contact.name == "Jane Doe"
        assert raw.contact.email == "jane.doe@example.com"
        assert len(raw.experience) == 2
        assert len(raw.certifications) == 2
        assert raw.education == ("B.Sc. Computer Science, Universidad del Valle, 2018",)
        for expected in ("Python", "JS", "React.js", "Node.js", "PostgreSQL",
                         "sklearn", "Git", "R", "Django", "Docker", "AWS"):
            assert expected in raw.raw_skills
        assert "SQL" not in raw.raw_skills  # only inside PostgreSQL

    def test_empty_text_gives_empty_profile(self, extractor):
        raw = extractor.extract("")
        assert raw == RawProfile(
            contact=ContactInfo("", "", ""),
            education=(), experience=(), certifications=(), raw_skills=(),
        )

    def test_is_idempotent(self, extractor):
        assert extractor.extract(SAMPLE_CV) == extractor.extract(SAMPLE_CV)
