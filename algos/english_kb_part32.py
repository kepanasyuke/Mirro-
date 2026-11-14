# -*- coding: utf-8 -*-
"""English KB part 32: stuffs of the loom and their finishing (batch)."""

TOPICS = {
    "linen": (
        "Linen is the state or the condition of being of the flax, the plain and wholesome cloth woven from the fibre of that plant, "
        "and the smooth and serviceable stuff which is got out of the stalk and made decent by the bleaching of the sun; "
        "and it is the linen of a farmer in the summer heat, of a table spread for guests, and of a bride made white for her day, "
        "being the plain and sun-whitened cloth, and it differs from woollen, which is the stuff of the fleece, warm and of a rough and hairy nap, "
        "in being the cool and the smooth cloth of the stalk, being the plain and cleanly stuff, "
        "and it differs from satin and from brocade, which are the lustrous and figured stuffs of show, in being the homely cloth of use and of the plainest decency, "
        "being the simple and wholesome stuff, and it is the linen which, laid upon the board or worn against the skin, "
        "is at once the cloth of the household and the cloth of the person, being the plain and serviceable stuff; "
        "and a thing is of linen when it is made of that smooth and sun-bleached thread which keeps its whiteness and its freshness under the hand, "
        "being the woven and noble stuff of the stalk; and linen is thus the plain and wholesome cloth got from the flax, "
        "the smooth and cool stuff of household and of person, and the clean and modest array of woven thread."
    ),
    "satin": (
        "Satin is the state or the condition of being of the shining face, the smooth and glossy cloth whose surface is left with its threads lying long and close "
        "so that the light plays upon it, and the soft and lustrous stuff which falls in the falling fold and shows the sheen "
        "of a polished surface; and it is the satin of a wedding gown, of a cushion upon a lady's chair, and of the pale sleeve of a dancer, "
        "being the smooth and gleaming cloth, and it differs from velvet, which is the stuff of the standing nap and the soft and deep-piled face, "
        "in being the flat and unrisen surface that catches the light with a hard and brilliant shine, being the smooth and lustrous stuff, "
        "and it differs from linen and from brocade, which are the plain cloth of use and the figured cloth of picture, "
        "in being the stuff of a single gleaming face and of no figure at all, being the plain and shining stuff, "
        "and it is the satin which, turning and turning in the light, is at once a deep and a light cloth, being the sleek and deceptive stuff; "
        "and a thing is of satin when it is woven of so long a lying thread that its face catches the light in one smooth and unbroken gleam, "
        "being the shining and falling stuff; and satin is thus the smooth and glossy cloth of the gleaming face, the soft and lustrous stuff of the falling fold, "
        "and the sleek and brilliant array that turns the light upon itself."
    ),
    "velvet": (
        "Velvet is the state or the condition of being of the standing nap, the rich and heavy cloth whose surface is raised into a dense and even pile "
        "so that it takes the print of the hand and holds it, and the soft and deep-faced stuff which swallows the light instead of giving it back; "
        "and it is the velvet of a king's mantle, of a curtain drawn in the dark room, and of a jeweller's little tray, "
        "being the piled and shifting cloth, and it differs from satin, which is the flat and smooth stuff of the hard and brilliant shine, "
        "in being the soft and unrisen-faced one that drinks the light, being the deep and thick-piled stuff, "
        "and it differs from brocade, which is the figured cloth whose picture is wrought into the ground, "
        "in being the same rich ground throughout, figured only by the very nap of it, being the plain and sumptuous stuff, "
        "and it is the velvet which, pressed one way and another, is at once one cloth and two colours, being the changes and the deep-faced stuff; "
        "and a thing is of velvet when its face is so thickly piled that the stroke of the hand leaves a darker path upon it, "
        "being the piled and stroked stuff; and velvet is thus the rich cloth of the standing nap and the deep and even pile, "
        "the soft and light-drinking stuff of the heavy fold, and the sumptuous array whose colour shifts under the hand."
    ),
    "woollen": (
        "Woollen is the state or the condition of being of the fleece, the thick and hairy cloth woven from the carded and twisted yarn of the sheep, "
        "and the warm and serviceable stuff whose nap is left upon it and whose body holds the heat against the cold; "
        "and it is the woollen of a shepherd's coat in the rain, of a blanket upon a winter bed, and of the cloak of a young man upon the hill, "
        "being the warm and thick cloth, and it differs from linen, which is the smooth and cool cloth of the stalk, "
        "in being the warm and hairy stuff of the beast, being the thick and comforting cloth, "
        "and it differs from velvet, which is the piled cloth of ornament cut to a standing nap, in being the coarse and honest stuff of warmth and wear, "
        "being the plain and enduring stuff, and it is the woollen which, breathed for its warmth and worn for its roughness, "
        "is at once a poor man's comfort and a rich man's riding-cloak, being the warm and homely cloth; "
        "and a thing is of woollen when it is made of such a hairy and compacted thread as keeps the heat and stands the weather, "
        "being the stout and warming stuff; and woollen is thus the thick and hairy cloth got from the fleece, "
        "the warm and enduring stuff of the cold season, and the honest array that holds the heat of the body against the wind."
    ),
    "brocade": (
        "Brocade is the state or the condition of being of the figured stuff, the rich cloth upon whose ground another thread is woven in raised and shining figures "
        "so that the stuff carries a picture of its own, and the sumptuous fabric in which flowers and beasts and scrolls are wrought into the very body of the web; "
        "and it is the brocade of a priest's vestment, of the cushion of a throne, and of the long coat of a merchant's daughter, "
        "being the figured and sumptuous cloth, and it differs from satin, which is the plain and gleaming stuff of the single smooth face, "
        "in being the stuff where the gleam is broken and set about into shapes, being the figured and pictured stuff, "
        "and it differs from velvet, which is the deep-piled stuff plain throughout, in being the ornament wrought by the treadle and not by the pile, "
        "being the wrought and patterned stuff, and it is the brocade which, chained upon the loom with many shuttles, is at once a cloth and a picture, "
        "being the figured and gleaming stuff; and a thing is of brocade when its face bears figures raised and shining out of the ground, "
        "being the worked and ornate stuff; and brocade is thus the rich and figured cloth of the raised and shining pattern, "
        "the sumptuous stuff whose picture is woven into its body, and the gorgeous array that is at once a garment and an ornament."
    ),
}

TOPIC_TEST = [
    ("linen", ("linen", "flax cloth", "what is linen", "plain white cloth", "linen stuff", "cool table cloth")),
    ("satin", ("satin", "glossy cloth", "what is satin", "smooth shining cloth", "satin stuff", "lustrous fabric")),
    ("velvet", ("velvet", "piled cloth", "what is velvet", "soft nap cloth", "velvet stuff", "deep pile fabric")),
    ("woollen", ("woollen", "woolen cloth", "what is woollen", "sheep fleece cloth", "woollen stuff", "warm thick cloth")),
    ("brocade", ("brocade", "figured cloth", "what is brocade", "woven picture cloth", "brocade stuff", "ornate figured fabric")),
]
