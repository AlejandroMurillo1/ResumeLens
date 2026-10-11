def render_markdown(model) -> str:
    lines = [
        f"# {model.contact.name}",
        "",
        f"**Email:** {model.contact.email}  ", f"**Phone:** {model.contact.phone}",
        "",
        "## Education"
    ]

    lines.extend(f"- {e}" for e in model.education)
    lines.append("")

    lines.append("## Experience")
    lines.extend(f"- {e}" for e in model.experience)
    lines.append("")

    if model.certifications:
        lines.append("## Certifications")
        lines.extend(f"- {c}" for c in model.certifications)
        lines.append("")

    lines.append("## Skills")
    lines.append(", ".join(s.name for s in model.skills))
    lines.append("")

    lines.append("## Profile Matches")
    for r in model.results:
        mark = "✅" if r.status == "ACCEPTED" else "❌"
        evaluated = ", ".join(s.name for s in r.evaluated)
        lines.append(f"- {mark} **{r.name}** — evaluated: [{evaluated}]")

    return "\n".join(lines)