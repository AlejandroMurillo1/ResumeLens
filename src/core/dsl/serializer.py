from src.core.models.models import CandidateReport


def to_dsl(report: CandidateReport) -> str:
    def q(s: str) -> str:
        return '"' + s.replace('"', '\\"') + '"'

    lines = ["candidate {", "    contact {", f"        name: {q(report.contact.name)}",
             f"        email: {report.contact.email}", f"        phone: {report.contact.phone}", "    }",
             "    education { " + " ".join(q(e) for e in report.education) + " }",
             "    experience { " + " ".join(q(e) for e in report.experience) + " }",
             "    certifications { " + " ".join(q(c) for c in report.certifications) + " }",
             "    skills { " + ", ".join(report.skills) + " }", "    profiles {"]
    for c in report.classifications:
        status = "ACCEPTED" if c.accepted else "REJECTED"
        lines.append(f"        {q(c.profile_name)} {status} evaluated [{', '.join(c.sequence)}]")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines)