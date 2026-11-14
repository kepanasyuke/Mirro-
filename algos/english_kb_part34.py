# -*- coding: utf-8 -*-
"""English KB part 34: writing and its instruments (batch)."""

TOPICS = {
    "quill": (
        "Quill is the hollow barrel of a great feather cut and trimmed to a point and dipped in ink, "
        "the light and living pen which the hand holds upright between the fingers, and the ancient "
        "instrument by whose nib the letters of a page are laid down; and it is the quill of the clerk "
        "who saws a new nib at morning, of the scholar whose elbow is stained with ink, and of the "
        "lover who writes a line that must not be spoken, being the light and living pen of the feather; "
        "and it differs from parchment, which is the skin upon which the hand writes, in being the hand's "
        "own cutting tool and not the surface which receives its trace, being the feathered and pointed "
        "instrument, and it differs from a tablet, which bears its signs upon a harder and more stubborn "
        "face, in being supple and quick and made to follow the smallest turn of the thought, being the "
        "light and obedient pen; and it is the quill which, cut fresh and taken in a steady hand, is at "
        "once the humblest tool of the writing room and the instrument of the fairest letters, being the "
        "feather and the pen in one; and a person shows the use of the quill when he shapes a nib to his "
        "own purpose and draws the letters that answer his will, being the patient and skilful scribe; and "
        "quill is thus the hollow feather trimmed to a point, the light pen of the old writing, and the "
        "instrument by which the hand lays its signs upon the page."
    ),
    "parchment": (
        "Parchment is the fine and supple skin of a beast prepared for writing, scraped smooth and "
        "stretched upon a frame until it will take the pen, the pale and lasting surface upon which the "
        "letters of an old book are laid, and the material which outlasts the paper of a later age; and it "
        "is the parchment of a great book whose leaves are turned with care, of a charter folded small, and "
        "of a page that has kept its letters through long ages, being the smooth and lasting skin of the "
        "scribe; and it differs from a quill, which is the feather that makes the letters, in being the "
        "surface that receives them and keeps them, being the stretched and enduring skin, and it differs "
        "from a tablet, which is a stiff and small face of clay or wax, in being soft, wide and made to be "
        "folded and bound, being the supple and continuous surface; and it is the parchment which, once "
        "scraped and smoothed and ruled with faint lines, is at once the plainest sheet and the fairest "
        "ground of the illuminated page, being the prepared and yielding skin; and a thing shows the nature "
        "of parchment when it takes the ink without blot and holds the mark for many years, being the smooth "
        "and lasting surface; and parchment is thus the beast's skin prepared for writing, the pale and "
        "enduring surface of the old book, and the material that keeps its letters longer than paper."
    ),
    "seal": (
        "Seal is the impression of a sign pressed into soft wax or clay, the fixed and private mark which "
        "closes a writing and declares it true, and the little image cut in a hard stone or a ring by which "
        "that mark is given; and it is the seal of a letter whose fold must not be opened, of a deed made "
        "lawful by its sign, and of a grave mark set beside a name, being the pressed and private sign of "
        "truth; and it differs from a quill, which is the hand's instrument for making letters, in being "
        "the sign set down at the end, being the closing and the private mark, and it differs from a scroll, "
        "which is a writing rolled and tied, in being the wax and the emblem that hold it fast and show "
        "whose it is, being the binding and the witness, and it differs from the beast that bears the same "
        "name, which is a creature of the sea, in being no living thing at all but a mark pressed into wax, "
        "being the sign and the image alone; and it is the seal which, once pressed in hot wax and left to "
        "cool, is at once the close of a writing and the promise of him who sent it, being the pressed and "
        "private sign; and a person sets his seal when he is bound by the mark that bears his own sign, "
        "being the faithful and the bound one; and seal is thus the impression of a sign in soft wax, the "
        "private mark that closes a writing and makes it true, and the stone or ring from which that mark "
        "is taken."
    ),
    "scroll": (
        "Scroll is a writing rolled upon itself, a long and narrow sheet wound about a rod or merely "
        "closed in a cylinder and tied, the ancient and open-ended form of the book before the folded leaf, "
        "and the roll which is unwound by degrees as the reader goes down it; and it is the scroll of a "
        "prophet whose words are read aloud from the high place, of a long and solemn list that hangs from "
        "the hand and falls to the ground, and of a message tied and sealed and carried far, being the "
        "rolled and continuous writing; and it differs from a tablet, which is a flat and stiff face "
        "written and turned over in the hand, in being a long sheet wound and unwound, being the continuous "
        "and rolled form, and it differs from parchment, which is the skin itself before it is cut and "
        "rolled, in being the writing as it is formed, wound and kept, being the rolled and finished "
        "writing; and it is the scroll which, once proper to the old law and the old prophecy, is at once "
        "a book and an unfolding act, being the wound and the revealed word; and a person unrolls a scroll "
        "when he opens a writing that is long and continuous to read it from the first line to the last, "
        "being the patient and unfolding reader; and scroll is thus a writing rolled upon itself, the long "
        "sheet wound and tied, and the old form of the book before the folded leaf."
    ),
    "tablet": (
        "Tablet is a small and flat face of clay, wax or stone on which signs are cut or pressed, the "
        "stiff and heavy leaf that is held in the hand and written upon with a hard point, and the oldest "
        "and plainest of all the surfaces of writing; and it is the tablet of a schoolboy who smooths the wax "
        "and begins again, of a mason who cuts his reckoning into the stone, and of a keeper of the old law "
        "who presses his marks into the clay and bakes them hard, being the stiff and small face of signs; "
        "and it differs from parchment, which is a soft skin stretched and folded into a book, in being hard, "
        "small and single, being the stubborn and hand-held face, and it differs from a scroll, which is a "
        "long sheet rolled and unrolled, in being a flat leaf that is neither wound nor unfolded, being the "
        "fixed and single surface; and it is the tablet which, once smoothed and marked, is at once the "
        "plainest of all writings and the most enduring of them, being the hard and lasting face; and a "
        "person writes upon a tablet when he cuts or presses his signs into a face that will not be bent or "
        "folded but must be held and smoothed again, being the patient and the hard-handed writer; and "
        "tablet is thus a small flat face of clay or wax for signs, the stiff leaf held in the hand, and "
        "the oldest and plainest of all the surfaces of writing."
    ),
}

TOPIC_TEST = [
    ("quill", ("quill", "feather pen", "what is a quill", "pen from a feather", "hollow feather", "quill pen")),
    ("parchment", ("parchment", "what is parchment", "skin for writing", "animal skin page", "parchment sheet", "old book page")),
    ("seal", ("wax seal", "what is a seal", "seal on a letter", "pressed sign", "seal in wax", "sealing mark")),
    ("scroll", ("scroll", "what is a scroll", "rolled writing", "rolled up page", "ancient scroll", "scroll of paper")),
    ("tablet", ("tablet", "what is a tablet", "clay tablet", "wax tablet", "tablet for writing", "flat writing face")),
]
