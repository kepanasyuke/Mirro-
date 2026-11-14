# -*- coding: utf-8 -*-
"""English KB part 35: mist, dew and thaw (batch)."""

TOPICS = {
    "mist": (
        "Mist is the fine and clouded film of suspended water which hangs in the lower air and "
        "steeps the near world in a pale and quiet dimness, the soft and floating veil which blots "
        "the far hedge and the further hill while the hand before the face is still plain, and the "
        "gentle dullness which makes a familiar road strange and the far unknown close; and "
        "it is the mist of a valley at daybreak, of a lake upon an autumn evening, and of a warm "
        "room breaking into a cold morning, being the low and clinging veil, and it differs from dew, "
        "which is water already fallen and laid as beads upon the grass, in being water still aloft "
        "and never resting, being the floating and unhoused dampness, and it differs from haze, which "
        "is a thin and golden drift of the upper air that softens the sun, in being low, thick and "
        "close about the ground, being the nearer and the denser veil; and it is the mist which, "
        "rising from wet ground or drawn from warm water in the cold, is at once a hiding of the land "
        "and a moistening of it, being the veiling and yielding breath; and a person walks in mist "
        "when the air about him is white and uncertain and every distance is guessed rather than "
        "seen, being the veiled and cautious one; and mist is thus the low film of suspended water "
        "that hangs in the air, the soft veil which dims the near world, and the gentle dullness that "
        "hides the distance and wets the cheek."
    ),
    "dew": (
        "Dew is the small and clear moisture which the cool of night gathers out of the air upon the "
        "grass, the leaf, the stone and the spider's thread, the bright and beaded sweat of a world "
        "that has breathed out its warmth and is repaid in drops, and the gentle and freshly fallen "
        "wetness which the first sun finds and slowly takes again; and it is the dew of a summer "
        "meadow at dawn, of a pane of glass upon a chilly morning, and of a garden path where the "
        "runner leaves his print, being the resting and beaded moisture, and it differs from mist, "
        "which is moisture still floating and veiling the air, in being that moisture brought down "
        "and set upon the surfaces of things, being the settled and shining deposit, and it differs "
        "from thaw, which is a softening of the air that loosens what is frozen, in being a small and "
        "quiet moisture laid down without noise, being the gentle and silent gathering; and it is the "
        "dew which, shed upon a land by a clear and cooling night, is at once a blessing to the dry "
        "herb and a sign of the morning, being the refreshing and the quiet sign; and a field is wet "
        "with dew when the grass at daybreak is heavy with clear and separate drops, being the cool "
        "and beaded one; and dew is thus the small clear moisture gathered by the night air upon "
        "grass and leaf, the beaded sweat of a cooling world, and the gentle wetness which the dawn "
        "finds and the sun takes away."
    ),
    "thaw": (
        "Thaw is the softening and yielding of the frozen world when a milder air comes over it, the "
        "slow and dripping change in which the ice gives up its hardness, the snow loses its stiffness "
        "and the river finds its voice again, and the gentle loosening which turns the hard white "
        "ground to a black and sighing one; and it is the thaw of a late February "
        "wind, of a frozen pond breaking into water at noon, and of a road once ringing under the "
        "foot and now silent with mud, being the yielding of the cold, and it differs from dew, which "
        "is a fresh and quiet moisture laid by night upon living grass, in being the undoing of an "
        "older and harder cold, being the melting and releasing change, and it differs from sleet, "
        "which is a mean and stinging fall of half-frozen water, in being the giving up of the frost "
        "rather than a new and mixed descent from the sky, being the softened and dripping release; "
        "and it is the thaw which, coming upon a land locked hard for a season, is at once a promise "
        "of the earth's return and a muddy and uncertain hour, being the yielding and hopeful change; "
        "and a day is one of thaw when the air is mild and dripping and the ice gives way underfoot, "
        "being the mild and releasing one; and thaw is thus the slow softening of the frozen world "
        "under a milder air, the dripping change in which ice and snow yield, and the release that "
        "turns the hard white ground to soft and black."
    ),
    "sleet": (
        "Sleet is the mean and stinging fall of half-frozen water which is neither rain nor snow, the "
        "sharp and mixed descent of cold water that strikes the cheek and whitens upon the roof, and "
        "the raw and grudging weather which lashes the hillside and leaves nothing plainly one kind "
        "or the other; and it is the sleet of a March evening in a narrow street, of a mountain pass "
        "in early spring, and of a sea wind driving inland upon a fishing town, being the sharp and "
        "mixed fall, and it differs from thaw, which is the old cold giving way in mildness and drip, "
        "in being a new and hostile descent of water still half frozen, being the falling and stinging "
        "change, and it differs from mist, which is moisture hanging still and soft without weight, "
        "in being moisture that falls with an edge and a sting, being the driving and cutting "
        "precipitation; and it is the sleet which, falling between the freezing and the mild hour, is "
        "at once a rain to soak and a snow to chill, being the half-frozen and grudging descent; and a "
        "traveler meets sleet when the air stings his face and the ground grows greasy and uncertain "
        "beneath his feet, being the raw and stinging one; and sleet is thus the half-frozen fall that "
        "is neither rain nor snow, the sharp and mixed descent that whitens and soaks at once, and "
        "the raw weather of the dividing season."
    ),
    "haze": (
        "Haze is the thin and luminous dimness of the upper air, the faint and golden opacity in "
        "which distant things are seen softly yet remain unconfused, and the dry and delicate film "
        "which heat or dust draws over the sky so that the sun is pale and the far hills are "
        "tender and blue; and it is the haze of a hot afternoon over a wide plain, of a harvest "
        "field in late summer, and of a city seen from a hill beyond its smoke, being the thin and "
        "luminous dimness, and it differs from mist, which is a thick and low veil of water close "
        "about the ground, in being thin, high and luminous, allowing the eye to pass and only "
        "softening what it sees, being the delicate and aerial dimness, and it differs from dew and "
        "from sleet, which are water come down to be touched, in being neither fallen nor falling "
        "water but a light and dry suffusion of the air itself, being the suffused and untouching "
        "veil; and it is the haze which, by softening every outline without hiding it, is at once a "
        "beauty of distance and a lassitude of the hour, being the tender and enervating dimness; and "
        "a landscape lies in haze when its far shapes are veiled in a pale and golden air, being the "
        "softened and luminous one; and haze is thus the thin luminous dimness of the upper air, the "
        "golden film that softens distance without concealing it, and the dry and tender veil which "
        "heat or dust lays upon the far view."
    ),
}

TOPIC_TEST = [
    ("mist", ("mist", "low cloud", "thin fog", "what is mist", "misty air", "white vapour near ground")),
    ("dew", ("dew", "drops on grass", "morning dew", "what is dew", "dew on leaves", "beads of moisture")),
    ("thaw", ("thaw", "melting of ice", "what is a thaw", "snow melting", "spring thaw", "ice giving way")),
    ("sleet", ("sleet", "half frozen rain", "what is sleet", "rain and snow", "freezing rain", "wet snow falling")),
    ("haze", ("haze", "what is haze", "summer haze", "hazy air", "thin dim air", "dusty air far off")),
]
