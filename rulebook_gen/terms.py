"""Terms and conditions of an offer: its class template (classes/<class>.terms.md)
filled with the provider's [provider.terms] values, overridden by the offer's
[offer.terms]. The result is published as the offering's "License" term; the
front matter names the class and the rulebook commit (rulebook R5.2).
"""

import pathlib
import string

CLASSES_DIR = pathlib.Path(__file__).resolve().parent.parent / "classes"
REPO_URL = "https://github.com/CitComAI-Hub/citcom-ds-rulebook"


def template(cls):
    return string.Template((CLASSES_DIR / f"{cls}.terms.md").read_text())


def missing(provider, offer):
    """Template variables with no value, for validation."""
    values = provider.get("terms", {}) | offer.get("terms", {})
    return sorted(set(template(offer["class"]).get_identifiers()) - values.keys())


def text(provider, offer):
    values = provider.get("terms", {}) | offer.get("terms", {})
    return template(offer["class"]).substitute(values)


def document(provider, offer, ref):
    cls = offer["class"]
    return (
        "---\n"
        f"class: {cls}\n"
        f"class_url: {REPO_URL}/blob/{ref}/classes/{cls}.md\n"
        f"rulebook: {ref}\n"
        "generated: citcom-ds-rulebook rulebook_gen, do not edit\n"
        "---\n\n"
        + text(provider, offer)
    )


def body(doc):
    """The terms without the front matter (what is published as the License)."""
    return doc.split("\n---\n", 1)[1].lstrip("\n")
