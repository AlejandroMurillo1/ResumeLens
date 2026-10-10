from pathlib import Path
from src.core.dsl.validator import DSLValidator
from src.core.models.models import DSLError

GRAMMAR_PATH = Path(__file__).parent / "candidate.tx"  # ajusta la ruta real en tu repo

validator = DSLValidator(
    grammar_path=GRAMMAR_PATH,
    valid_profile_names=("Cloud Engineer", "Full Stack Developer"),
)

text = '''
candidate {
    contact { name: "Ana Perez" email: ana@mail.com phone: +573001234567 }
    education { "BSc Computer Science" }
    experience { "Backend intern, 6 months" }
    certifications { }
    skills { GIT, REACT, AWS }
    profiles {
        "Cloud Engineer" ACCEPTED evaluated [AWS]
        "Full Stack Developer" ACCEPTED evaluated [GIT, REACT]
    }
}
'''

try:
    model = validator.validate(text)
    print("OK, modelo parseado.")
    print("Nombre del contacto:", model.contact.name)
    print("Skills:", [s.name for s in model.skills])
except DSLError as e:
    print(f"[{e.kind.name}] {e.message} (línea {e.line}, columna {e.column})")