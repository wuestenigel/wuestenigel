"""DMCA takedown notice generator in English and German."""

from datetime import datetime
from typing import Optional

from .config import Config
from .models import Violation


def generate_dmca_english(violation: Violation, config: Config) -> str:
    """Generate a DMCA takedown notice in English."""
    return f"""DMCA TAKEDOWN NOTICE
====================

Date: {datetime.now().strftime('%B %d, %Y')}

To Whom It May Concern:

I am writing to notify you of an infringement of my copyrighted work.

1. IDENTIFICATION OF COPYRIGHTED WORK

The original copyrighted image is located at:
{violation.original_image_url}

I am the copyright owner of this work.

2. IDENTIFICATION OF INFRINGING MATERIAL

The infringing material is located at:
- Image URL: {violation.infringing_url}
- Page URL: {violation.page_url}
- Domain: {violation.domain}
- Similarity: {violation.similarity_score:.1f}%

3. CONTACT INFORMATION

Name: {config.owner_name}
Email: {config.owner_email}
Address: {config.owner_address}
Phone: {config.owner_phone}

4. GOOD FAITH STATEMENT

I have a good faith belief that the use of the copyrighted material described
above is not authorized by the copyright owner (myself), its agent, or the law.

5. ACCURACY STATEMENT

I swear, under penalty of perjury, that the information in this notification
is accurate, and that I am the copyright owner or am authorized to act on
behalf of the copyright owner of an exclusive right that is allegedly infringed.

6. REQUESTED ACTION

I request that you immediately remove or disable access to the infringing
material identified above.

Sincerely,

{config.owner_name}
{config.owner_email}
"""


def generate_dmca_german(violation: Violation, config: Config) -> str:
    """Generate a DMCA takedown notice in German (Abmahnung)."""
    return f"""ABMAHNUNG WEGEN URHEBERRECHTSVERLETZUNG
========================================

Datum: {datetime.now().strftime('%d.%m.%Y')}

Sehr geehrte Damen und Herren,

hiermit mache ich Sie auf eine Verletzung meiner Urheberrechte aufmerksam.

1. IDENTIFIKATION DES URHEBERRECHTLICH GESCHUETZTEN WERKS

Das originale urheberrechtlich geschuetzte Bild befindet sich unter:
{violation.original_image_url}

Ich bin der Urheber und Rechteinhaber dieses Werks.

2. IDENTIFIKATION DES RECHTSVERLETZENDEN MATERIALS

Das rechtsverletzende Material befindet sich unter:
- Bild-URL: {violation.infringing_url}
- Seiten-URL: {violation.page_url}
- Domain: {violation.domain}
- Uebereinstimmung: {violation.similarity_score:.1f}%

3. KONTAKTINFORMATIONEN

Name: {config.owner_name}
E-Mail: {config.owner_email}
Adresse: {config.owner_address}
Telefon: {config.owner_phone}

4. AUFFORDERUNG

Ich fordere Sie hiermit auf, das oben bezeichnete rechtsverletzende Material
unverzueglich zu entfernen oder den Zugang dazu zu sperren.

Gemaess den Bestimmungen des Urheberrechtsgesetzes (UrhG) behalte ich mir
ausdruecklich vor, weitergehende Ansprueche auf Unterlassung, Auskunft und
Schadensersatz geltend zu machen.

Ich bitte um Bestaetigung der Entfernung des Materials innerhalb von
14 Tagen nach Erhalt dieses Schreibens.

Mit freundlichen Gruessen,

{config.owner_name}
{config.owner_email}
"""


def generate_dmca_email_subject(violation: Violation, language: str = "en") -> str:
    """Generate an email subject line for the DMCA notice."""
    if language == "de":
        return f"Abmahnung: Urheberrechtsverletzung auf {violation.domain}"
    return f"DMCA Takedown Notice: Copyright Infringement on {violation.domain}"
