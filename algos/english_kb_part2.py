# -*- coding: utf-8 -*-
"""English KB part 2: slopes, levels and steepness (batch)."""

TOPICS = {
    "ascent": (
        "Ascent is the act or the state of rising upward, the mounting of a thing "
        "toward a higher place, and the upward course and the climbing motion by which "
        "a body gains a greater height than that from which it set out; and "
        "it is the ascent of a pilgrim upon a stony height, of a smoke and a vapour into "
        "the roof of the sky, and of a soul toward the things that are above it, being "
        "the rising and the climbing course, and it differs from a descent, which is the "
        "going down, in being the mounting upward against the weight and the "
        "pull of the earth, being the rising and the uplifted course, and it differs also "
        "from an elevation, which is the height itself, and from an inclination and a "
        "steepness, which are the slant of the ground and the sharpness of that slant, in "
        "being the motion that climbs rather than the measure or the quality of the slope, "
        "being the mounting and upward going, and it is the ascent which, taken in hand "
        "with patience, is at once the labour of the limbs and the lifting of the spirit, "
        "being the slow and upward winning of height; and a person makes an ascent when he "
        "climbs a steep way and comes at last to a higher place, being "
        "the climbing and upward laboring one; and ascent is thus the act or the state of "
        "rising upward, the mounting of a thing toward a higher place, and the upward course "
        "and climbing motion by which height is gained."
    ),
    "descent": (
        "Descent is the act or the state of going down, the passage of a thing from a higher "
        "place to a lower one, and the downward course and the falling motion by which a body "
        "comes to a lesser height than that whereon it stood; and it is the descent "
        "of a traveller from a mountain into the valley, of a stone that is loosed from the "
        "hand toward the earth, and of a house or a family from its former honour, being the "
        "going down and downward course, and it differs from an ascent, which is the mounting "
        "upward against the weight of the body, in being the yielding to the pull of the earth "
        "and the passing from the greater to the lesser height, being the downward and lowered "
        "course, and it differs also from an elevation, the height itself, and from an "
        "inclination and a steepness, the slant and its sharpness, in being the moving downward rather than the slope itself, being the going down and the lowering passage, and it is the descent which, "
        "once begun upon a steep way, is at once the swift and the fearful thing to the walker "
        "thereon, being the downward and perilous going; and a person makes a descent when he "
        "goes down a steep way and comes at last to a lower place, being "
        "the going down and downward moving one; and descent is thus the act or the state of "
        "going down, the passage of a thing from a higher place to a lower, and the falling "
        "course and falling motion by which a lesser height is reached."
    ),
    "elevation": (
        "Elevation is the height to which a thing is raised above a given level, the measured "
        "loftiness of a place, a point or a body above the ground or the sea, and the raising "
        "up of a thing to a higher station by which it stands above that which lies beneath it; "
        "and it is the elevation of a tower above the roofs of a city, of a village upon a "
        "gentle rise, and of a mind above the common cares of the day, being the loftiness and "
        "the height measure, and it differs from an ascent, which is the act of climbing, and "
        "from a descent, which is the act of going down, in being the height itself that remains "
        "when the climbing is done, being the standing and measured loftiness, and it differs "
        "also from an inclination and a steepness, which are the slant of the ground and the "
        "sharpness of that slant, in being the standing height rather than the pitch of the "
        "side, being the level and the lifted measure, and it is the elevation which, spoken of "
        "a place or a person alike, is at once a matter of the earth and of the inward station, "
        "being the lifted and measured height; and a place or a person is of a notable elevation "
        "when it stands high above the common level of things about it, being the high and "
        "lifted one; and elevation is thus the height to which a thing is raised above a given "
        "level, the measured loftiness of a place or a point above the ground, and the raising "
        "up of a thing to a higher station."
    ),
    "inclination": (
        "Inclination is the slant of a thing from the upright or the level, the bending aside "
        "of a surface or a line toward the horizon, and the gentle or the great leaning by "
        "which a thing that should stand straight is set aslant; and it is the inclination of a "
        "roof toward the rain, of a meadow that falls away toward the river, and of a head that "
        "is bowed in sorrow or attention, being the leaning and the slanted set, and it differs "
        "from an ascent, which is the act of climbing upward, and from a descent, which is the "
        "act of going down, in being the fixed slant of the thing itself rather than the journey "
        "taken upon it, being the settled and leaning posture, and it differs also from an "
        "elevation, which is the height itself, and from a steepness, which is the sharpness of "
        "the rise, in being the angle of the leaning rather than the height attained or the "
        "degree of its violence, being the slanted and the leaning cast, and it is the "
        "inclination which, whether of a surface or of a temper, is at once a matter of the "
        "earth and of the mind, being the leaning and the disposed set; and a thing has an "
        "inclination when it is set aslant from the upright or the level, being the leaning and "
        "aslant one; and inclination is thus the slant of a thing from the upright or the level, "
        "the bending aside of a surface or a line toward the horizon, and the leaning by which "
        "a thing is set aslant."
    ),
    "steepness": (
        "Steepness is the quality or the state of being steep, the sharp and sudden rise of a "
        "way, a wall or a shore in which a small going forward gains a great deal of height, "
        "and the violence of the slope by which the foot is strained and the eye is daunted; "
        "and it is the steepness of a cliff above the sea, of a mountain stair cut in the rock, "
        "and of a roof that lifts against the sky, being the sharp and sudden rise, and it "
        "differs from an ascent, which is the act of climbing, and from a descent, which is the "
        "act of going down, in being the quality of the ground over which the going is made "
        "rather than the going itself, being the sharp and severe rise, and it differs also from "
        "an elevation, which is the height itself, and from an inclination, which is the bare "
        "slant from the level, in being the degree of that slant carried to its sharp and trying "
        "extreme, being the severe and forbidding pitch thereof, and it is the steepness which, "
        "in a way or in a matter of the spirit, is at once an obstacle to the body and a trial of "
        "the will, being the sharp and the arduous rise; and a way or a place has steepness when "
        "it rises so sharply that the going thereon is hard and the footing is unsure, being the "
        "sharp and arduous one; and steepness is thus the quality of being steep, the sharp and "
        "sudden rise of a way or a shore, and the violence of the slope by which the going is "
        "made hard."
    ),
}

TOPIC_TEST = [
    ("ascent", ("ascent", "what is an ascent", "act of climbing up", "going up a hill", "upward climb", "rise to a height")),
    ("descent", ("descent", "what is a descent", "act of going down", "coming down a hill", "downward course", "lowering passage")),
    ("elevation", ("elevation", "what is an elevation", "height above the ground", "height above sea level", "loftiness of a place", "raised height")),
    ("inclination", ("inclination", "what is an inclination", "slant from the level", "leaning of a surface", "angle of a slope", "aslant set")),
    ("steepness", ("steepness", "what is steepness", "sharpness of a slope", "how steep a hill is", "sudden sharp rise", "degree of the slant")),
]
