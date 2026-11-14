# -*- coding: utf-8 -*-
"""English KB part 33: catching and gear (batch)."""

TOPICS = {
    "net": (
        "A net is the woven and knotted snare of cord spread across an opening, the meshed"
        " fabric whose narrow gaps are made to close about the creature and hold it, and the"
        " wide and yielding trap which, being cast over water or over ground, is drawn in"
        " again with its catch; and it is the net of the fisher who spreads his mesh over the"
        " shallows, of the fowler who closes the snare upon the wing, and of the hunter who"
        " casts the spreading web over the thicket, being the woven and yielding snare; and"
        " it differs from a hook, which is a single point that holds one, and from a bait,"
        " which is the temptation laid in the way, and from a seine, which is a net drawn"
        " through the water about the shoal, in being the wide and patient snare which takes"
        " by encompassing rather than by striking, and from a haven or a harbour, which are"
        " the places of rest and shelter, in being the trap that no creature puts into"
        " willingly, being the encompassing and holding snare; and it is the net which, having"
        " no point and no tooth, is at once gentle and inescapable, being the soft and closing"
        " trap; and a person finds himself in a net when he is so enclosed that his going out"
        " is cut off, being the entangled and held one; and a net is thus the woven snare"
        " spread to encompass and hold, the meshed instrument of the fisher and the fowler,"
        " and the patient and yielding trap whose strength is in wrapping."
    ),
    "hook": (
        "A hook is the bent and pointed piece of metal upon which a bait is set and by which"
        " the creature is caught, the single and grasping instrument which, once taken into"
        " the mouth or the flesh, holds by its own curve and may not be got out again, and the"
        " small and cruel hold that is hidden in the midst of a sweet thing; and it is the"
        " hook of the fisher who sets the worm in the stream, of the angler whose line runs"
        " out and whose barb takes hold, and of the hawk whose talons fasten as a hook upon"
        " the dove, being the single and grasping hold; and it differs from a net, which"
        " ensnares the whole body by encompassing it, and from a bait, which is the allurement"
        " laid upon it, and from a seine, which sweeps many at once and keeps them by its mesh,"
        " in being the one sharp point that seizes but one and holds it by pain, being the"
        " single and piercing hold; and it is the hook which, being baited and hidden, is at"
        " once the gift and the wound, being the concealed and grasping steel; and a person"
        " swallows the hook when he takes what is offered and finds that the offering had a"
        " barb within it, being the taken and held one; and a hook is thus the bent and"
        " pointed thing baited to seize and hold, the single instrument of the fisher, and the"
        " small and piercing hold which, being hidden, keeps what it has once bitten."
    ),
    "bait": (
        "A bait is the tempting morsel laid upon a hook or within a net to draw the creature"
        " to its taking, the allurement set out by the fisher that the fish may come willingly"
        " to the place of its capture, and the sweet and offered thing whose purpose is not"
        " itself but the snare it serves; and it is the bait of the fisher who sets the worm"
        " upon the water, of the fowler who scatters grain before the spreading net, and of"
        " the angler whose lure glitters in the stream, being the tempting and offered morsel;"
        " and it differs from a hook, which is the steel that holds and hurts, and from a net,"
        " which is the mesh that encloses, and from a seine, which is the mesh drawn about the"
        " many, in being the gift set before the hidden snare, being the offered and ensnaring"
        " gift, and it differs from a lure, which is the brightness that draws the eye, in"
        " being the food that draws the appetite; and it is the bait which, being itself eaten,"
        " is at once the food and the snare, being the palatable and fatal morsel; and a"
        " person takes the bait when he seizes upon an easy profit or a sweet offer and finds"
        " the price afterwards, being the taken and deceived one; and a bait is thus the"
        " tempting morsel laid to draw the creature to the snare, the offered gift of the"
        " fisher and the fowler, and the allurement whose whole sweetness is the promise of"
        " the thing that lies beneath it."
    ),
    "angler": (
        "An angler is the person who takes fish with the hook and the line, the patient fisher"
        " who waits by the water and plies his craft by artifice rather than by force, and the"
        " man of the slender tackle whose whole strength is in his patience and his skill at"
        " setting the bait; and it is the angler of the quiet river who waits the livelong day,"
        " of the sea-rock who casts into the surf at dusk, and of any man who angles after his"
        " advantage by slow and cunning means, being the patient and artful fisher; and it"
        " differs from a hook, which is his own instrument, and from a bait, which is the"
        " morsel he sets, and from a net, which takes by encompassing many, and from a seine,"
        " which is the drawn mesh of the many-handed fisher, in being the man himself who waits"
        " and works by line and morsel, being the waiting and skilful fisher, and he has no"
        " fellowship with the haven, which is a place of rest, but with the open water where"
        " the taking is done; and it is the angler who, being slow and still, is at once the"
        " hunter and the waiter, being the patient and cunning one; and a person is an angler"
        " after some thing when he seeks it not by open force but by long waiting and the"
        " setting of a bait for another, being the waiting and artful seeker; and an angler is"
        " thus the man who takes fish with hook and line, the patient fisher whose craft is in"
        " the bait and the waiting.
    ),
    "seine": (
        "A seine is the long and deep net hung with weights below and floats above, which is"
        " drawn through the water about a shoal and closes upon it from both sides, the swept"
        " and enclosing mesh of the fisher who takes the many at once, and the wide curtain of"
        " cord whose two ends are hauled away and whose belly gathers up what it has"
        " encircled; and it is the seine of the fishers upon the beach who drag it ashore, of"
        " the boat that lets it out in a ring about the moving multitude, and of the market"
        " carried off in one taking, being the swept and enclosing mesh; and it differs from a"
        " net, which is cast and held, and from a hook, which takes but one, and from a bait,"
        " which draws to its taking, and from an angler, who waits with line and morsel, in"
        " being the net that moves through the water and takes the many by one wide enclosing"
        " sweep, being the drawn and gathering mesh; and it is the seine which, being drawn"
        " about the shoal, is at once the wall and the purse, being the enclosing and gathering"
        " sweep; and fishers draw a seine when they let the long mesh out about a multitude and"
        " haul it in, being the hauling and enclosing many; and a person is taken in a seine"
        " when the many about him are swept up together, being the swept and gathered one; and"
        " a seine is thus the long weighted net drawn through the water about a shoal, the"
        " enclosing instrument of the many-handed fisher, and the wide and moving curtain whose"
        " closing gathers all into one taking."
    ),
}

TOPIC_TEST = [
    ("net", ("net", "meshed snare", "woven trap", "what is a net", "casting net", "fish net")),
    ("hook", ("hook", "barbed hook", "fish hook", "what is a hook", "bent point", "hook and line")),
    ("bait", ("bait", "fish bait", "what is a bait", "tempting morsel", "bait on a hook", "take the bait")),
    ("angler", ("angler", "who is an angler", "patient fisher", "man with a rod", "what is an angler", "angling")),
    ("seine", ("seine", "seine net", "what is a seine", "drawn net", "hauling net", "drag net")),
]
