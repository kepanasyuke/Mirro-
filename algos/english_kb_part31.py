# -*- coding: utf-8 -*-
"""English KB part 31: metals - brass, copper, lead, tin, steel (batch)."""

TOPICS = {
    "brass": (
        "Brass is the yellow and shining metal of common use, the bright and golden-hued substance "
        "that is beaten into candlesticks and lockplates and rings with a clear high note when it is "
        "struck, and the well-known workable metal which takes and keeps a polish and answers sweetly "
        "under the tool; and it is the brass of the door-knocker upon the street door, of the telescope "
        "tube and the ship's fittings, and of the trumpet whose voice is heard afar, being the shining "
        "and serviceable metal; and it differs from copper, which is the red and native metal from which "
        "it is made, and from steel, which is the hard and grey metal of the blade, in being the bright "
        "and easy and gilded metal of ornament and of common ware, being the yellow and tractable metal; "
        "and it is the brass which, being rubbed and kept, is at once the metal of the household and the "
        "metal of the music, being the shining and obedient substance; and a thing shows brass when it is "
        "made of that yellow metal which gleams like pale gold and rings like a small bell when it is "
        "struck, being the sign of a common and honest and polished make; and brass is thus the yellow "
        "and shining metal, the bright substance of ware and ornament which takes a polish and gives a "
        "clear note, the workable metal of the household. "
    ),
    "copper": (
        "Copper is the red and native metal, the soft and ruddy substance that is found already formed "
        "in the earth and is beaten into vessels and drawn into wire and rolled into thin sheets, and the "
        "warm and yielding metal which the smith bends and the roofer lays and the kettle-maker hammers "
        "into shape; and it is the copper of the kitchen pot that grows green in damp and weather, of the "
        "roof of the old church that is stained with a living green, and of the long wire that carries a "
        "message across the land, being the ruddy and yielding and enduring metal; and it differs from "
        "brass, which is the yellow metal made from it, from tin, which is the pale and white and softer "
        "metal, and from steel, which is the hard and grey metal of the tool, in being the red and native "
        "metal of first and simple use, being the warm and ductile substance; and it is the copper which, "
        "being soft and easily wrought and patient under the long drawing, is at once the metal of the "
        "humble vessel and the metal of the long journey of a message, being the yielding and widely used "
        "substance; and a thing shows copper when it is made of that red metal which takes a dull glow "
        "and turns green under the rain, being the warm and honest and ancient make; and copper is thus "
        "the red and native metal, the soft and yielding substance of vessel and wire and roofing, the "
        "metal of first and simple use. "
    ),
    "lead": (
        "Lead is the heavy and dull grey metal, the soft and sombre substance that hangs in the plumb "
        "line and weighs down the net and closes the seam of the pane, and the dark and sluggish metal "
        "that yields to the knife and takes the impression of the die and stops the ball and the ray; "
        "and it is the lead of the plumb-bob that finds the upright of the wall, of the coffin lid that "
        "shuts in the dead, and of the roof of the old cathedral that lies heavy and grey against the "
        "sky, being the heavy and dull and yielding metal; and it differs from tin, which is the pale and "
        "white and lighter metal, from copper, which is the red and lively metal, and from brass and "
        "steel, which are the bright and hard metals of use and of war, in being the weighty and sombre "
        "and inert metal, being the dull and ponderous substance; and it is the lead which, being soft "
        "and weighty and deaf to the spark, is at once the metal of the measure and the metal of the "
        "shroud, being the heavy and dull and still substance; and a thing shows lead when it is made of "
        "that grey metal which is heavy in the hand and soft to the tool and dim to the eye, being the "
        "sombre and weighty make; and lead is thus the heavy and dull grey metal, the soft and ponderous "
        "substance that plums the line and seals the seam and roofs the church, the metal of weight and "
        "of quiet."
    ),
    "tin": (
        "Tin is the white and pale metal, the soft and bright and light metal which is poured into the "
        "mould and beaten into thin sheet and drawn into the cup and the plate, and the easy and clean "
        "and silent metal which rusts not and keeps its whiteness in the damp; and it is the tin of the "
        "pewter plate upon the farmhouse table, of the can that holds the preserved fruit, and of the "
        "poor man's spoon and tankard, being the white and clean and yielding metal; and it differs from "
        "lead, which is the heavy and dull and dark metal, and from brass and copper and steel, which are "
        "the bright and hard metals of weight and edge, in being the pale and light and harmless metal of "
        "the table and the kitchen, being the white and soft and clean substance; and it is the tin "
        "which, being light and soft and slow to tarnish, is at once the metal of the ever and the metal "
        "of the platter, being the white and serviceable and clean substance; and a thing shows tin when "
        "it is made of that pale white metal which is light in the hand and dull to the edge and bright "
        "in the damp, being the clean and humble make; and tin is thus the white and pale metal, the soft "
        "and bright metal of the cup and the can and the platter, the light and clean substance of the "
        "kitchen and the table."
    ),
    "steel": (
        "Steel is the hard and grey metal, the tempered and powerful substance that is heated and quenched "
        "and beaten upon the anvil until it takes an edge and holds it, and the stubborn and faithful "
        "metal which bends in the spring and stands in the blade and rings under the hammer; and it is "
        "the steel of the sword and the ploughshare, of the great bridge that carries the road across the "
        "water, and of the chisel and the pen that are trusted to the hand of the workman, being the hard "
        "and tempered and lasting metal; and it differs from brass, which is the yellow and tractable "
        "metal of ornament, from copper, which is the red and yielding metal of the vessel, from lead, "
        "which is the heavy and dull metal, and from tin, which is the white and soft metal of the table, "
        "in being the metal wrought to a high hardness that will not yield without force, being the "
        "tempered and formidable substance; and it is the steel which, being heated and "
        "quenched and beaten upon the anvil, is at once the edge of the tool and the spring of the "
        "machine, being the hard and elastic and lasting substance; and a craftsman shows steel when he "
        "draws his blade from the fire and cools it in the water and grinds it to a keen and lasting "
        "edge, being the patient and tempered workman; and steel is thus the hard and grey metal, the "
        "tempered substance that holds an edge and bears a strain, the metal of the tool and the blade."
    ),
}

TOPIC_TEST = [
    ("brass", ("brass", "what is brass", "yellow metal", "brass ornament", "polished brass", "brass lock")),
    ("copper", ("copper", "what is copper", "red metal", "copper pot", "copper wire", "copper roof")),
    ("lead", ("lead", "what is lead", "heavy metal", "plumb line", "lead roof", "lead weight")),
    ("tin", ("tin", "what is tin", "white metal", "pewter and tin", "tin cup", "tin can")),
    ("steel", ("steel", "what is steel", "hard metal", "steel blade", "tempered steel", "steel bridge")),
]
