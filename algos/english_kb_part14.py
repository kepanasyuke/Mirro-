# -*- coding: utf-8 -*-
"""English KB part 14: air, moisture and cold (batch)."""

TOPICS = {
    "atmosphere": (
        "Atmosphere is the whole and encircling body of air that wraps a world about, the "
        "gaseous sea in which every living thing is steeped, and the soft and pressing envelope "
        "which the vapours and the exhalations of a place gather into a single airy garment; and "
        "it is the atmosphere of a warm and fruitful valley, of a city heavy with smoke, and of a "
        "high and windy hill, being the all-embracing and tempered air, and it differs from vapour, "
        "which is that moist and escaping breath one substance yields, in being the great and "
        "collected body of every such breath together, being the whole and gathered air, and it "
        "differs from humidity, which is the measure of the water held in the air, in being the air "
        "itself and not the reckoning of what it carries, being the containing and encircling body; "
        "and it is the atmosphere which, wherever men breathe and things grow, is at once the common "
        "air of all and the weather of each, being the enclosing and tempered air; and a place has "
        "an atmosphere when its air is of a settled temper and quality, being the tempered and "
        "surrounding one; and atmosphere is thus the encircling body of air about a world, the "
        "gaseous sea in which all things are steeped, and the airy envelope which vapours and "
        "exhalations build about a place."
    ),
    "vapour": (
        "Vapour is the thin and wandering moisture that has been raised from a body by heat, the "
        "air-borne and unshapen substance which rises from the warm water, the breathing earth or "
        "the heated pot, and the faint and fleeting body which the cold of night turns back to "
        "drops again; and it is the vapour of a kettle above the fire, of a marsh in the evening "
        "sun, and of the warm breath of a beast in winter, being the rising and unshapen moisture, "
        "and it differs from humidity, which is the dampness held within the air at large, in being "
        "the particular and escaping breath of a body, being the risen and wandering moisture, and "
        "it differs from drizzle, which is that moisture fallen again as fine and even rain, in "
        "being the moisture not yet gathered and come down, being the rising and disembodied one; "
        "and it is the vapour which, once the air is cooled about it, is at once a mist and a "
        "deposit of dew, being the yielding and changing moisture; and a thing yields vapour when "
        "it gives off a thin and rising moisture under warmth, being the warm and breathing one; "
        "and vapour is thus the thin moisture raised from a body by heat, the air-borne and "
        "unshapen substance that rises from warm water or breathing earth, and the faint body "
        "which the cold of night gathers back into drops."
    ),
    "humidity": (
        "Humidity is the dampness of the air, the state of a place in which moisture is held "
        "suspended and unseen in the common air, and the soft and clinging heaviness which water "
        "gives to the breath when it is diffused throughout it; and it is the humidity of a summer "
        "night before a storm, of a cellar beneath a house, and of a land that lies near the sea, "
        "being the unseen and pervasive dampness, and it differs from vapour, which is the visible "
        "and rising breath of a single heated body, in being the whole damp temper of the "
        "surrounding air, being the diffused and pervasive dampness, and it differs from "
        "atmosphere, which is the entire body of air itself, in being the water held within that "
        "air and not the air that holds it, being the contained and unseen dampness; and it is the "
        "humidity which, whether of a room, of a season or of a climate, is at once the unseen water "
        "of the air and the heaviness that men feel upon the skin, being the diffused and oppressive "
        "dampness; and a place is of great humidity when its air is warm and heavy with unseen "
        "moisture, being the damp and clinging one; and humidity is thus the dampness of the air, "
        "the state of a place in which moisture is held unseen in the common air, and the soft and "
        "clinging heaviness which water gives to the breath."
    ),
    "frost": (
        "Frost is the thin and whitened crust of ice which the cold of a clear night lays upon "
        "the ground, the leaves, the stones and the window, and the sharp and biting chill of the "
        "air which hardens the soil and stills the growing of things; and it is the frost of a "
        "winter morning upon the grass, of a pane breathed upon and then frozen, and of an orchard "
        "left white at dawn, being the cold and whitening rime, and it differs from drizzle, which "
        "is a fine and even rain that wets, in being the moisture of the air fixed to ice and laid "
        "down as a crust, being the frozen and whitening deposit, and it differs from humidity, "
        "which is the dampness held in the air, in being that dampness brought out of the air and "
        "turned to a hard and shining skin, being the settled and crystalline cold; and it is the "
        "frost which, seizing on the moisture of the air and of the ground, is at once a beauty to "
        "the eye and a bane to the garden, being the biting and whitening cold; and a land suffers "
        "frost when a cold and clear night brings the white crust upon it and stiffens the soil, "
        "being the chilled and whitened one; and frost is thus the morning crust of ice laid by "
        "cold upon ground and leaf, the biting chill of the sharp air, and the white rime that "
        "hardens the earth and checks the growing of things."
    ),
    "drizzle": (
        "Drizzle is the fine and even rain of very small drops that falls close and quiet from a "
        "low and heavy sky, the thin and steady wetting which fills the air without haste or noise, "
        "and the soft and grey precipitation which makes all things wet and none the fresher; and "
        "it is the drizzle of a November afternoon, of a mountain pass in mist, and of a harbour on "
        "a windless day, being the fine and steady wetting, and it differs from frost, which is "
        "moisture fixed into a white and biting crust, in being the moisture still falling and "
        "falling as water, being the soft and liquid wetting, and it differs from vapour, which is "
        "moisture risen and still aloft, in being that moisture already gathered and come down "
        "again, being the descended and falling moisture; and it is the drizzle which, though it "
        "never pours and never thunders, at last soaks the cloth and the road and the open field, "
        "being at once a gentle rain and a thorough wetting; and a day is one of drizzle when a "
        "small and steady rain falls without ceasing and the air is grey and damp, being the small "
        "and steady one; and drizzle is thus the fine and even rain of very small drops from a low "
        "and heavy sky, the thin and steady wetting that fills the air quietly, and the soft and "
        "grey falling which wets all things evenly."
    ),
}

TOPIC_TEST = [
    ("atmosphere", ("atmosphere", "layer of air", "air around earth", "gases around planet", "the air about us", "what is atmosphere")),
    ("vapour", ("vapour", "vapor", "mist from heat", "steam rising", "water gas", "breath of kettle")),
    ("humidity", ("humidity", "moisture in air", "damp air", "air moisture", "wet in the air", "water in the air")),
    ("frost", ("frost", "white ice", "rime on grass", "freezing crust", "ice on leaves", "morning ice")),
    ("drizzle", ("drizzle", "fine rain", "light rain", "small drops", "mizzle", "thin rain")),
]
