# -*- coding: utf-8 -*-
"""English KB part 12: boundary, verge and limit (batch)."""

TOPICS = {
    "boundary": (
        "Boundary is the line which passes along the edge of a thing and marks where it ceases to be, "
        "the fixed and declared limit which parts one holding from another, and the visible seam at "
        "which the rule of a place or a right ends; and it is the boundary of a field and of a parish, "
        "of a forest at the mountain's foot, and of a kingdom at the river's crossing, being the agreed "
        "and marking line, and it differs from a threshold, which is the sill of an entrance, in being "
        "the long and running line that parts one region from another rather than the point of passing, "
        "being the continuous and dividing border, and it differs from a margin, which is the spare "
        "strip left about a thing, in being the line where a thing is ended and not the room yielded "
        "round it, being the strict and declared edge, and it differs from a verge, which is the last "
        "strip before a change, in being set and settled and not merely about to be passed, being the "
        "firm and surveyed line; and it is the boundary which, whether of land, of law or of custom, is "
        "at once the end of the one and the beginning of the other, being the parting and settled line; "
        "and a place has a boundary when a line is run beyond which its own ceased, being the "
        "delimited and acknowledged one; and boundary is thus the line along the edge of a thing, the "
        "fixed limit parting one holding from another, and the seam at which a rule ends."
    ),
    "margin": (
        "Margin is the spare strip of white or of empty ground left about the body of a thing, the "
        "unoccupied breadth which borders a written page or a printed field, and the room that is "
        "withheld from use for safety or for ease; and it is the margin of a book about its text, of a "
        "page about its picture, and of a coin about its device, being the spared and bordering strip, "
        "and it differs from a boundary, which is the line where a thing is ended, in being the breadth "
        "that lies within the edge and is given up to quiet, being the spared and unclaimed breadth, "
        "and it differs from a verge, which is the outermost brink of an approach, in being set round a "
        "thing on every hand and not only reached before a change, being the bordering strip, and it "
        "differs from a recess, which is a hollow set back, in being the flat ground about a body "
        "rather than the withdrawn space within it, being the open and surrounding border; and it is "
        "the margin which, whether of paper, of coin or of land, is at once the empty border and the "
        "room for the hand, being the spared and welcoming breadth; and a page has a margin when a "
        "strip is left empty about it, being the spared and bordering one; and margin is thus the spare "
        "strip left about the body of a thing, the unoccupied breadth which borders a written page, and "
        "the room withheld from use for ease."
    ),
    "verge": (
        "Verge is the very brink and outer edge of a thing, the last narrow strip of ground upon which "
        "a man stands before the world changes beneath him, and the extreme border at which one state "
        "of things is ended and another is about to begin; and it is the verge of a cliff before the "
        "fall, of a wood before the open field, and of a man's temper before the outbreak, being the "
        "brink and last strip, and it differs from a boundary, which is the settled line dividing two "
        "holdings, in being the approaching edge rather than the agreed and surveyed one, being the "
        "near and impending brink, and it differs from a threshold, which is the sill passed in going "
        "in, in being the last ground before a change and not the point of entry, being the outermost "
        "and imminent edge, and it differs from a margin, which is a spare strip yielded about a thing, "
        "in being the edge itself which stands next to what lies beyond, being the lean and narrow "
        "brink; and it is the verge which, whether of land, of temper or of fortune, is at once the "
        "edge of the one and the first step toward the other, being the extreme and imminent border; "
        "and a man comes to the verge when he stands upon the last strip before a change, being the "
        "poised and outermost one; and verge is thus the very brink and outer edge of a thing, the last "
        "narrow strip before the world changes, and the extreme border where one state ends and another "
        "begins."
    ),
    "threshold": (
        "Threshold is the sill or the plank that is laid across the foot of a doorway, the raised and "
        "worn member of wood or stone over which a man steps when he passes from without into a house, "
        "and the very point of passage at which the outside ceases and the inside begins; and it is the "
        "threshold of a church door worn hollow by many feet, of the gate of a court, and of a chamber "
        "long shut, being the crossing sill of entry, and it differs from an aperture, which is the "
        "opening itself, in being the solid member on which the foot is set, being the low and crossed "
        "sill, and it differs from a verge, which is the brink before a change, in being the known gate "
        "of setting foot across and not the approach to one, being the entered sill, and it differs "
        "from a boundary, which is the line that parts two holdings, in being a single point of passage "
        "that a person crosses rather than a line that runs, being the narrow crossing; and it is the "
        "threshold which, whether of house or of a man's patience, is at once the end of the way "
        "without and the first step into the within, being the crossed and crossing point; and a house "
        "has a threshold when a sill is set and worn where entry is made, being the crossing one; and "
        "threshold is thus the sill across the foot of a doorway, the worn member over which a man "
        "steps, and the point where the outside ends and the inside begins."
    ),
    "frontier": (
        "Frontier is the foremost and outward march of a thing, the further edge of a settled order "
        "beyond which the land lies as yet unmeasured or but half known, and the shifting edge of what "
        "is held before the wilderness begins; and it is the frontier of a realm beyond its last town, "
        "of a settlement before the deep wood, and of knowledge at the edge of what has been proved, "
        "being the outward and doubtful march, and it differs from a boundary, which is a line run and "
        "settled between two that know one another, in being the loose and uncertain outermost part, "
        "being the open and half-known march, and it differs from a verge, which is the brink of a "
        "single thing, in being the wide and outward band of a whole order, being the extended edge, "
        "and it differs from a threshold, which is crossed on entering, in being the outermost extent "
        "reached and not the point of entry, being the far march; and it is the frontier which, whether "
        "of a realm or of a science, is at once the end of what is tilled and the beginning of what is "
        "wild, being the outward and advancing march; and a people has a frontier when its works reach "
        "an outermost edge beyond which order is not yet carried, being the advancing one; and frontier "
        "is thus the foremost and outward march of a thing, the further edge of a settled order beyond "
        "which the land lies unmeasured, and the shifting edge of what is held before the wild."
    ),
}

TOPIC_TEST = [
    ("boundary", ("boundary", "what is a boundary", "fixed boundary line", "dividing line", "border line between fields", "edge of an estate")),
    ("margin", ("margin", "margin of a page", "what is a margin", "spare strip", "empty border", "room about the text")),
    ("verge", ("verge", "on the verge", "what is a verge", "brink of a cliff", "edge before the fall", "very edge")),
    ("threshold", ("threshold", "what is a threshold", "door sill", "threshold of a door", "point of entering", "sill of a doorway")),
    ("frontier", ("frontier", "what is a frontier", "outermost march", "edge of settled land", "wild edge", "further edge")),
]
