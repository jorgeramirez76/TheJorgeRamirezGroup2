#!/usr/bin/env python3
"""Replace unsupported numeric authority claims in blog and social copy.

The approved stable experience fact lives in data/site-facts.json. This script
does not touch references to the age of a house, appliance, roof, HVAC system,
or household belongings.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Callable, Match, Union


ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "data" / "site-facts.json").read_text(encoding="utf-8"))
SINCE = FACTS["business"]["fullTimeSince"]

Replacement = Union[str, Callable[[Match[str]], str]]


def same_case_experience(match: Match[str]) -> str:
    text = f"full-time NJ real estate work since {SINCE}"
    return text.capitalize() if match.group(0)[0].isupper() else text


COUNTY_TAIL = r"(?:\s+(?:across|in)\s+[^<\n.:]{0,160}?\s+count(?:y|ies))?"
VOLUME_NOUN = (
    r"(?:(?:NJ|New Jersey)\s+)?(?:homes?(?:\s+(?:sold|listed|closed))?|home\s+sales?|"
    r"closed\s+transactions?|transactions?|closings?|sales?|families|homeowners?|clients?|"
    r"sellers?|buyers?)"
)
YEAR = r"(?:15|fifteen)\+?\s+years?"


RULES: list[tuple[str, Replacement]] = [
    # Hyphenated tenure claims used in metadata and index summaries.
    (
        r"\bA\s+(?:15|fifteen)-year\s+NJ\s+agent's\s+honest\s+take\b",
        f"An honest take from a full-time NJ agent since {SINCE}",
    ),
    (
        r"\b(?:a|an)\s+(?:15|fifteen)-year\s+(?:NJ\s+)?(?:real estate\s+)?agent\b",
        f"a full-time NJ real estate agent since {SINCE}",
    ),
    # Attribution and metadata formulations.
    (
        rf"\b(?:a|an)\s+(?:local\s+)?(?:NJ\s+)?(?:real estate\s+)?agent\s+"
        rf"(?:with|who(?:'s| has))\s+(?:{YEAR}\s+(?:and|,)\s+)?(?:sold\s+|closed\s+)?"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}",
        f"a full-time NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bfrom\s+(?:a\s+)?(?:local\s+)?expert\s+with\s+500\+\s+{VOLUME_NOUN}",
        f"from a full-time local NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bsomeone\s+who(?:'s| has)\s+closed\s+500\+\s+homes?(?:\s+in\s+NJ)?",
        f"a full-time NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bwritten\s+from\s+the\s+perspective\s+of\s+an\s+active\s+NJ\s+listing\s+agent\s+"
        rf"with\s+500\+\s+sales{COUNTY_TAIL}",
        f"written from the perspective of a full-time NJ listing agent since {SINCE}",
    ),
    # Combined years-and-volume introductions.
    (
        rf"\bHere(?:'s| is)\s+what\s+(?:I\s+know\s+from\s+)?{YEAR}\s+(?:and|,)\s+"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s+(?:has\s+taught\s+me)?\s*:",
        f"Here's what my full-time NJ real estate work since {SINCE} has taught me:",
    ),
    (
        rf"\bHere\s+is\s+what\s+I(?:'ve| have)\s+learned\s+after\s+{YEAR}\s+(?:and|,)\s+"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s*:",
        f"Here is what I have learned through full-time NJ real estate work since {SINCE}:",
    ),
    (
        rf"\b{YEAR}\s+(?:and|,)\s+500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s+"
        rf"(?:has|have)\s+(given|taught)\s+me",
        lambda match: f"My full-time NJ real estate work since {SINCE} has {match.group(1).lower()} me",
    ),
    (
        rf"\b{YEAR}\s+(?:and|,)\s+500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s+"
        rf"gives\s+you\s+a\s+solid\s+eye",
        f"My full-time NJ real estate work since {SINCE} has sharpened my eye",
    ),
    (
        rf"\bAfter\s+{YEAR}\s+(?:and|,)\s+(?:over\s+)?500\+\s+{VOLUME_NOUN}"
        rf"{COUNTY_TAIL}\s*,",
        f"As a full-time NJ real estate agent since {SINCE},",
    ),
    (
        rf"\bIn\s+{YEAR}\s+(?:and|,)\s+(?:over\s+)?500\+\s+{VOLUME_NOUN}"
        rf"{COUNTY_TAIL}\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bAcross\s+500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bAs\s+a\s+NJ\s+real estate agent\s+with\s+{YEAR}\s+(?:and|,)\s+"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s*,",
        f"As a full-time NJ real estate agent since {SINCE},",
    ),
    (
        rf"\b(?:B|b)ut\s+as\s+a\s+NJ\s+real estate agent\s+who(?:'s| has)\s+closed\s+"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s*,",
        f"But as a full-time NJ real estate agent since {SINCE},",
    ),
    (
        rf"\b(?:based\s+on|from)\s+{YEAR}\s+(?:and|,)\s+500\+\s+{VOLUME_NOUN}"
        rf"{COUNTY_TAIL}",
        f"based on full-time NJ real estate work since {SINCE}",
    ),
    # Remaining combined credential fragments.
    (
        rf"\b{YEAR}\s*(?:of\s+NJ\s+real estate\s*)?(?:and|,)\s*(?:over\s+)?"
        rf"500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}",
        same_case_experience,
    ),
    (
        rf"\b500\+\s+{VOLUME_NOUN}\s*,\s*{YEAR}\s+in\s+NJ\s+real estate",
        same_case_experience,
    ),
    # First-person volume formulations.
    (
        rf"\bI(?:'ve| have)\s+helped\s+500\+\s+"
        rf"(?:(?:NJ|New Jersey)\s+)?(?:families|homeowners?|clients?|sellers?)"
        rf"(?:\s+(?:sell|list)(?:\s+their)?\s+homes?)?{COUNTY_TAIL}",
        f"I've helped NJ clients as a full-time real estate agent since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+(?:sold|listed|closed|done|handled)\s+500\+\s+{VOLUME_NOUN}"
        rf"{COUNTY_TAIL}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+(?:sold|listed|closed|handled)\s+(?:over|more\s+than)\s+"
        rf"500\s+{VOLUME_NOUN}{COUNTY_TAIL}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bsomeone\s+who\s+has\s+(?:sold|listed|closed|handled)\s+(?:over|more\s+than)\s+"
        rf"500\s+{VOLUME_NOUN}{COUNTY_TAIL}",
        f"a full-time New Jersey real estate agent since {SINCE}",
    ),
    (
        rf"\bsomeone\s+who\s+has\s+(?:sold|listed|closed|handled)\s+500\+\s+"
        rf"{VOLUME_NOUN}{COUNTY_TAIL}",
        f"a full-time New Jersey real estate agent since {SINCE}",
    ),
    (
        rf"\bIn\s+my\s+experience\s+(?:selling|listing|closing|handling)\s+"
        rf"(?:over|more\s+than)\s+500\s+{VOLUME_NOUN}{COUNTY_TAIL}",
        f"In my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\b(?:a|an)\s+(?:practicing\s+)?(?:NJ\s+)?real estate agent\s+who\s+has\s+"
        rf"(?:sold|listed|closed|handled)\s+(?:over|more\s+than)\s+500\s+"
        rf"{VOLUME_NOUN}{COUNTY_TAIL}",
        f"a full-time NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+done\s+this\s+for\s+500\+\s+homes?{COUNTY_TAIL}",
        f"I've done this in my full-time New Jersey real estate work since {SINCE}",
    ),
    (
        rf"\b(?:After|Across|In)\s+500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bafter\s+500\+\s+{VOLUME_NOUN}",
        f"through my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\bPro\s+tip\s+from\s+500\+\s+sales\s*:",
        "A practical seller tip:",
    ),
    (
        rf"\bfrom\s+500\+\s+sales",
        f"from my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\b(?:Over|More\s+than)\s+500\s+homes?\s+(?:sold|listed|closed)"
        rf"{COUNTY_TAIL}\s*\.",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}.",
    ),
    (
        rf"\b(?:Over|More\s+than)\s+500\s+families\s+have\s+trusted\s+me\s+"
        rf"with\s+their\s+biggest\s+investment\s*\.",
        f"I've worked full time in New Jersey real estate since {SINCE}.",
    ),
    (
        rf"\b500\+\s+{VOLUME_NOUN}\s*\.\s*{YEAR}\s*\.",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}.",
    ),
    (
        rf"\b{YEAR}\s*\.\s*500\+\s+{VOLUME_NOUN}\s*(?:sold)?\s*\.",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}.",
    ),
    # Standalone volume fragments, after grammar-specific cases above.
    (rf"\b500\+\s+{VOLUME_NOUN}{COUNTY_TAIL}", same_case_experience),
    # Years-only first-person and attribution formulations.
    (
        rf"\bI(?:'ve| have)\s+been\s+(?=[^.!?<\n]{{0,130}}\b"
        rf"(?:selling|listing|helping|working|doing|in\s+this\s+business)\b)"
        rf"[^.!?<\n]{{0,160}}?\s+for\s+(?:over\s+)?{YEAR}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+(?:walked|worked|helped|managed|reviewed|sold|listed)"
        rf"(?=[^.!?<\n]{{0,150}}\b(?:buyers?|sellers?|homes?|houses?|listings?|showings?|real estate)\b)"
        rf"[^.!?<\n]{{0,170}}?\s+(?:for|over)\s+{YEAR}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+spent\s+{YEAR}\s+helping\s+NJ\s+sellers",
        f"I've helped NJ sellers as a full-time real estate agent since {SINCE}",
    ),
    (
        rf"\b(?:After|In)\s+{YEAR}\s+(?:of\s+)?"
        rf"(?:selling|listing|showing|walking|guiding|doing|preparing|working|real estate|transactions?|"
        rf"pre-listing\s+consultations?)[^<\n.:]{{0,170}}?\s*,",
        f"In my full-time New Jersey real estate work since {SINCE},",
    ),
    (
        rf"\b(?:After|In)\s+{YEAR}\s+"
        rf"(?:selling|listing|showing|walking|guiding|helping|working)[^<\n.:]{{0,170}}?\s*,",
        f"In my full-time New Jersey real estate work since {SINCE},",
    ),
    (
        rf"\bBased\s+on\s+{YEAR}\s+of\s+"
        rf"(?:showing|listing|selling|real estate|transaction|pre-listing\s+consultation)"
        rf"[^:<\n]{{0,150}}\s*:",
        f"Based on my full-time New Jersey real estate work since {SINCE}:",
    ),
    (
        rf"\bWhat\s+I\s+know\s+from\s+{YEAR}\s+of\s+transactions\s*:",
        f"What I know from my full-time New Jersey real estate work since {SINCE}:",
    ),
    (
        rf"\bIn\s+my\s+{YEAR}\s+in\s+NJ\s+real estate",
        f"In my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+worked\s+both\s+sides\s+of\s+this\s+in\s+{YEAR}\s+across\s+NJ",
        f"I've worked both sides of this as a full-time NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+been\s+doing\s+this\s+for\s+{YEAR}(?:\s+across\s+[^.!?<\n]+)?",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bany\s+buyer\s+pool\s+I(?:'ve| have)\s+dealt\s+with\s+in\s+{YEAR}",
        f"the buyers I have worked with during my full-time NJ real estate career since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+dealt\s+with[^.!?<\n]{{0,120}}?\bin\s+{YEAR}",
        f"I've worked with buyers throughout my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\bIn\s+my\s+experience\s+(?:selling|listing|showing|helping)\s+"
        rf"[^.!?<\n]{{0,150}}?\s+for\s+{YEAR}",
        f"In my full-time New Jersey real estate work since {SINCE}",
    ),
    (
        rf"\b{YEAR}\s+(?:of\s+)?(?:selling|listing|showing|walking|helping|working|NJ\s+closings|"
        rf"NJ\s+real estate|pre-listing\s+consultations?|seller\s+experience)",
        lambda _match: f"full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\b{YEAR}\s+in\s+NJ\s+real estate\b",
        lambda _match: f"full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\b{YEAR}\s+selling\s+homes",
        lambda _match: f"full-time NJ real estate work since {SINCE}",
    ),
    # Unsupported vague volume used as personal authority.
    (r"\b(?:hundreds|thousands)\s+of\s+NJ\s+homes\b", "many NJ homes"),
    (r"\b(?:hundreds|thousands)\s+of\s+homes\b", "many homes"),
    (r"\b(?:hundreds|thousands)\s+of\s+houses\b", "many houses"),
    (r"\b(?:hundreds|thousands)\s+of\s+NJ\s+kitchens\b", "many NJ kitchens"),
    (r"\bhundreds\s+of\s+buyers\b", "many buyers"),
    (r"\bhundreds\s+of\s+sellers\b", "many sellers"),
    (r"\bhundreds\s+of\s+listings\b", "many listings"),
    (r"\bhundreds\s+of\s+buyer\s+consultations\b", "buyer consultations"),
    (r"\bhundreds\s+of\s+inspection\s+reports\b", "many inspection reports"),
    (r"\bhundreds\s+of\s+home\s+inspection\s+reports\b", "many home inspection reports"),
    (r"\bhundreds\s+of\s+them\b", "many of them"),
    # Less-common phrasings found by the regression scan.
    (
        rf"\bIn\s+{YEAR}\s+(?:and|,)\s+500\+\s+NJ\s+transactions\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bI(?:'ve| have)\s+been\s+walking\s+buyers\s+through\s+homes?"
        rf"[^.!?<\n]{{0,150}}?\s+for\s+{YEAR}",
        f"I've worked with buyers as a full-time NJ real estate agent since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+been\s+through\s+many\s+homes?"
        rf"[^.!?<\n]{{0,150}}?\s+over\s+{YEAR}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bI(?:'ve| have)\s+walked\s+through\s+many\s+NJ\s+kitchens\s+over\s+{YEAR}",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    ),
    (
        rf"\bacross\s+many\s+NJ\s+listings\s+over\s+{YEAR}",
        f"through my full-time NJ real estate work since {SINCE}",
    ),
    (
        rf"\bshowing\s+I(?:'ve| have)\s+managed\s+over\s+{YEAR}",
        f"showing I've managed since becoming a full-time NJ real estate agent in {SINCE}",
    ),
    (
        rf"\b(?:After|In)\s+{YEAR}\s+in\s+NJ\s+real estate\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bIn\s+{YEAR}\s+and\s+over\s+500\s+transactions{COUNTY_TAIL}\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\bIn\s+{YEAR}\s+and\s+500\+\s+NJ\s+home\s+sales\s*,",
        f"In my full-time NJ real estate work since {SINCE},",
    ),
    (
        rf"\b(?:an?\s+)?NJ\s+real estate agent\s+with\s+{YEAR}\s+in\s+"
        rf"(?:Union|Essex|Morris|Middlesex|Hudson|Somerset)[^<\n.:]{{0,140}}?Count(?:y|ies)",
        f"a full-time NJ real estate agent since {SINCE}",
    ),
]


def normalize(source: str) -> str:
    for pattern, replacement in RULES:
        source = re.sub(pattern, replacement, source, flags=re.I)
    source = re.sub(
        rf"full-time NJ real estate work since {SINCE}\s+(?:home\s+)?sales\s+in\s+NJ\s+over\s+{YEAR}",
        f"full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"full-time NJ real estate work since {SINCE}\s+homes?\s+across\s+[^<\n.:]{{0,150}}?\s+count(?:y|ies)",
        f"full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"full-time NJ real estate work since {SINCE}\s+NJ\s+homes",
        f"Full-time NJ Realtor since {SINCE}.",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bwith\s+full-time NJ real estate work since {SINCE}",
        f"with full-time NJ real estate experience since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bsince {SINCE}\s+across\s+NJ\b",
        f"since {SINCE}",
        source,
        flags=re.I,
    )
    # Sentence and metadata starts should remain properly capitalized.
    source = re.sub(
        rf'(?P<prefix>(?:content|description|text)=["\']|[.!?]\s+|<p[^>]*>|^|\n)'
        rf"(?:a\s+)?full-time NJ real estate work since {SINCE}",
        lambda match: match.group("prefix") + f"Full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf'(?P<prefix>"(?:description|text)"\s*:\s*")a full-time NJ real estate agent since {SINCE}',
        lambda match: match.group("prefix") + f"A full-time NJ real estate agent since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"(In my full-time New Jersey real estate work since {SINCE}),\s+"
        rf"(?:Union|Essex|Morris|Middlesex|Hudson|Somerset)[^<\n.:]{{0,140}}?"
        rf"\bcount(?:y|ies)\s*([,:])",
        lambda match: match.group(1) + match.group(2),
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"(In my full-time New Jersey real estate work since {SINCE}),\s+"
        rf"(?:Westfield|Summit|Cranford|Maplewood)[^<\n.:]{{0,100}}?Maplewood\s*,",
        lambda match: match.group(1) + ",",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bIn full-time NJ real estate work since {SINCE}\b",
        f"In my full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bIn my experience doing full-time NJ real estate work since {SINCE}\b",
        f"In my full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bAfter full-time NJ real estate work since {SINCE}\b",
        f"Through my full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bHere is what I(?:'ve| have) learned after full-time NJ real estate work since {SINCE}\b",
        f"Here is what I have learned through my full-time NJ real estate work since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bHere's the truth In my full-time New Jersey real estate work since {SINCE},"
        rf"[^:<\n]{{0,100}}?counties\s*:",
        f"Here's what I have observed in my full-time New Jersey real estate work since {SINCE}:",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bFull-time NJ real estate work since {SINCE}\s+(?:home\s+)?sales\s+across\s+"
        rf"[^<\n.:]{{0,160}}?count(?:y|ies)\b",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bFull-time NJ real estate work since {SINCE}\s+(?:homes?\s+)?(?:in|across)\s+NJ\b",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bFull-time NJ real estate work since {SINCE}\s+closed\b",
        f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bI've worked full time in New Jersey real estate since {SINCE}\s+in\s+NJ\b",
        f"I've worked full time in New Jersey real estate since {SINCE}",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bI've helped NJ sellers as a full-time real estate agent since {SINCE}\s+get\s+homes\s+ready",
        f"Since becoming a full-time real estate agent in {SINCE}, I've helped NJ sellers get homes ready",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\bHere's what full-time NJ real estate work since {SINCE}\s+homes?\s+in\s+"
        rf"[^:<\n]{{0,140}}?counties\s+taught\s+me\s*:",
        f"Here's what my full-time NJ real estate work since {SINCE} has taught me:",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"\b(?:15|Fifteen) years\.\s+(?=Full-time)",
        "",
        source,
    )
    source = source.replace("And In my full-time", "And in my full-time")
    source = source.replace("In my experience In my full-time", "In my full-time")
    source = source.replace("Here's the truth In my full-time", "Here's the truth from my full-time")
    source = source.replace("Here is what I've learned Through my full-time", "Here is what I've learned through my full-time")
    source = source.replace(". a full-time NJ real estate agent", ". A full-time NJ real estate agent")
    source = source.replace("full-time local NJ real estate agent", "full-time local real estate agent")
    source = source.replace("hundreds of many houses", "many houses")
    source = source.replace(
        f"In my Full-time Realtor with Keller Williams Premier Properties since {SINCE}",
        f"In my full-time NJ real estate work since {SINCE}",
    )
    source = source.replace(
        f"I've worked full time in New Jersey real estate since {SINCE} in New Jersey",
        f"I've worked full time in New Jersey real estate since {SINCE}",
    )
    source = source.replace(
        f"a full-time New Jersey real estate agent since {SINCE} in New Jersey",
        f"a full-time New Jersey real estate agent since {SINCE}",
    )
    source = source.replace(
        f"based on full-time NJ real estate work since {SINCE} sales",
        f"based on my full-time NJ real estate work since {SINCE}",
    )
    source = source.replace(
        f"based on full-time NJ real estate work since {SINCE}",
        f"based on my full-time NJ real estate work since {SINCE}",
    )
    source = source.replace(
        f"Jorge Ramirez, full-time NJ real estate work since {SINCE}",
        f"Jorge Ramirez, a full-time NJ real estate agent since {SINCE}",
    )
    source = source.replace(
        f"real ROI data and full-time NJ real estate work since {SINCE}",
        f"real ROI data, drawing on full-time NJ real estate work since {SINCE}",
    )
    source = source.replace(
        f"I bring full-time NJ real estate work since {SINCE} to your listing",
        f"I bring experience from full-time NJ real estate work since {SINCE} to your listing",
    )
    source = source.replace(
        f"I've been walking through NJ homes before listing them for full-time NJ real estate work since {SINCE}",
        f"I've been walking through NJ homes before listing them throughout my full-time NJ real estate work since {SINCE}",
    )
    source = source.replace(
        f"from a full-time New Jersey real estate agent since {SINCE} and knows",
        f"from a full-time New Jersey real estate agent since {SINCE} who knows",
    )
    source = source.replace(
        f"Since becoming a full-time real estate agent in {SINCE}, I've helped NJ clients sell for more than they expected",
        f"Since becoming a full-time real estate agent in {SINCE}, I've helped NJ clients prepare homes for sale",
    )
    source = re.sub(
        r"I've helped many sellers across Union, Essex, Morris, and Middlesex Count(?:y|ies) "
        r"get their homes ready — and get top dollar",
        f"As a full-time NJ real estate agent since {SINCE}, I help sellers across Union, Essex, "
        "Morris, and Middlesex counties prepare their homes for market",
        source,
        flags=re.I,
    )
    source = source.replace(
        "I've walked through many inspection reports",
        f"In my full-time New Jersey real estate work since {SINCE}, I've reviewed inspection reports",
    )
    source = source.replace(
        "I've walked through many NJ homes with buyers and their inspectors",
        f"In my full-time New Jersey real estate work since {SINCE}, I've joined buyers and inspectors on home visits",
    )
    source = source.replace(
        "I've reviewed many home inspection reports across Union, Essex, Morris, and Middlesex counties. "
        "Gutters appear as a deficiency on the majority of them.",
        f"In my full-time NJ real estate work since {SINCE}, I've reviewed inspection issues across "
        "Union, Essex, Morris, and Middlesex counties. Gutter deficiencies recur in those reports.",
    )
    source = source.replace(
        "I've reviewed many inspection reports across Union, Essex, Morris, and Middlesex counties. "
        "Gutter deficiencies appear on the majority of them.",
        f"In my full-time NJ real estate work since {SINCE}, I've reviewed inspection issues across "
        "Union, Essex, Morris, and Middlesex counties. Gutter deficiencies recur in those reports.",
    )
    source = source.replace(
        "from an agent who has walked many listings in Union, Essex and Morris",
        f"from a full-time NJ real estate agent since {SINCE}",
    )
    source = source.replace(
        "a licensed NJ real estate agent who has walked many homes near these train stops",
        f"a licensed NJ real estate agent who has worked full time since {SINCE}",
    )
    source = re.sub(
        r"Most of these fixes cost \$200–\$500 each\. You don't need to do all 12\. "
        r"But if you address the ones that apply to your home — and there are usually 4–6 on "
        r"this list in any given NJ listing — you will consistently see \$5,000–\$20,000 more "
        r"at closing than comparable sellers who didn't make the effort\. That's not a staging "
        r"opinion\. That's 15 years of watching offers come in\.",
        f"You do not need to address all 12 items. Focus on the ones that apply to your home; a "
        f"cleaner, more coherent presentation makes it easier for buyers to assess its condition. "
        f"That recommendation comes from my full-time NJ real estate work since {SINCE}.",
        source,
    )
    source = source.replace(
        f"Full-time NJ Realtor since {SINCE}..",
        f"Full-time NJ Realtor since {SINCE}.",
    )
    source = source.replace(". written from the perspective", ". Written from the perspective")
    source = source.replace(
        f"I've helped NJ clients as a full-time real estate agent since {SINCE} sell",
        f"Since becoming a full-time real estate agent in {SINCE}, I've helped NJ clients sell",
    )
    source = source.replace(
        f"In my full-time New Jersey real estate work since {SINCE}, pre-listing walkthroughs, inspections, buyer tours —",
        f"Across pre-listing walkthroughs, inspections, and buyer tours during my full-time New Jersey real estate work since {SINCE},",
    )
    verified_sentence = f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}."
    source = source.replace(f"{verified_sentence} {verified_sentence}", verified_sentence)
    source = re.sub(
        r"\bthe same mistake play out hundreds of times\b",
        "the same mistake play out repeatedly",
        source,
        flags=re.I,
    )
    source = re.sub(
        rf"(?P<prefix>(?:^|\n|<p[^>]*>|[.!?]\s+))Full-time NJ real estate work since {SINCE}\.",
        lambda match: match.group("prefix")
        + f"Full-time Realtor with Keller Williams Premier Properties since {SINCE}.",
        source,
        flags=re.I,
    )
    # Collapse accidental repetition when two adjacent claims normalize to the
    # same verified sentence.
    sentence = f"Full-time NJ real estate work since {SINCE}."
    source = source.replace(f"{sentence} {sentence}", sentence)
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write changes in place")
    args = parser.parse_args()
    changed: list[Path] = []
    for path in sorted((ROOT / "blog").rglob("*")):
        if path.suffix.lower() not in {".html", ".md"}:
            continue
        before = path.read_text(encoding="utf-8", errors="ignore")
        after = normalize(before)
        if after == before:
            continue
        changed.append(path)
        if args.write:
            path.write_text(after, encoding="utf-8")
    mode = "Updated" if args.write else "Would update"
    for path in changed:
        print(f"{mode}: {path.relative_to(ROOT)}")
    print(f"{mode} {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
