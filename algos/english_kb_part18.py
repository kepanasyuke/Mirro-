# -*- coding: utf-8 -*-
"""English KB part 18: sounds and noises (batch)."""

TOPICS = {
    "clamour": (
        "Clamour is the loud and importunate outcry of many voices together, the confused and swelling noise of a multitude that "
        "shouts and demands, and the urgent and unruly din by which a crowd presses its will upon the ear; and it is the clamour of "
        "the marketplace at noon, of the mob before the magistrate's door, and of a people that will not be denied, being the "
        "multitudinous and urgent outcry, and it differs from hiss, which is the sharp and sibilant breath of contempt, in being the "
        "mingled and unceasing cry of many, and from murmur, which is a low and continuous mutter, in being loud and importunate, and "
        "from roar, which is the heavy bellow of one beast or of the sea, in being the many and disordered voice, and from shriek, "
        "which is the shrill cry of one throat in terror, in being the sustained demand of a people, being the urgent and confused "
        "outcry of a multitude; and it is the clamour which, whether of petition or of protest, is at once a demand of the many and a "
        "sound without form, being the loud and importunate outcry; and a person raises a clamour when he cries aloud and repeats his "
        "cry among others who cry likewise, being the loud and importunate crier; and clamour is thus the loud and importunate outcry "
        "of many voices together, the confused and swelling noise of a multitude that demands, and the urgent din upon the ear."
    ),
    "hiss": (
        "Hiss is the sharp and prolonged sibilant sound made by the forcing of breath or of steam through a narrow passage, the thin "
        "and contemptuous sound of a serpent or of an angry audience, and the act of uttering that sound in derision or in warning; and "
        "it is the hiss of the kettle upon the fire, of the serpent roused in the grass, and of the gallery that condemns a player to "
        "silence, being the sharp and sibilant sound, and it differs from shriek, which is the shrill and piercing cry of pain or of "
        "terror, in being the cold and deliberate sound of derision, and from roar, which is the deep and heavy volume of a beast or a "
        "multitude, in being thin and brief, and from clamour, which is the confused outcry of many voices, in being the single and "
        "edged breath, and from murmur, which is the soft and even utterance of many, in being cut short, being the sharp and "
        "contemptuous sibilant; and it is the hiss which, whether of steam, of serpent or of scorn, is at once a sound of "
        "the body and a judgment of the will, being the sharp and sibilant sound; and a person hisses when he utters that sibilant "
        "sound to show contempt, being the contemptuous and sibilant one; and hiss is thus the sharp and prolonged "
        "sibilant sound of breath or of steam, the thin and contemptuous sound of the serpent or of the angry audience, and the act of "
        "uttering it in derision."
    ),
    "roar": (
        "Roar is the deep and heavy and prolonged sound that issues from the throat of a great beast, from the throat of a man in "
        "fury or in pain, and from the rushing of waters or of a great engine in motion; and it is the roar of the lion in the "
        "wilderness, of the crowd in the amphitheatre, and of the sea upon a rocky shore, being the deep and sustained volume of "
        "sound, and it differs from shriek, which is a shrill and piercing cry of terror, in being deep and sustained and heavy, and "
        "from hiss, which is the thin and sibilant breath of contempt, in being full and bodily, and from clamour, which is the "
        "confused and importunate voice of many, in being one and continuous, and from murmur, which is a low and gentle undertone, in "
        "being vast and overwhelming, being the deep and continuous bellow; and it is the roar which, whether of beast, of crowd or "
        "of waters, is at once a sound of power and a terror to the hearer, being the deep and heavy volume of sound; and a thing "
        "roars when it gives forth a deep and prolonged and heavy sound, being the deep and bellowing one; and roar is thus the deep "
        "and heavy and prolonged sound of a great beast or of a man in fury, the vast and continuous voice of waters and of engines, "
        "and the dreadful and measureless noise of power in motion."
    ),
    "murmur": (
        "Murmur is the low and continuous and subdued sound of voices or of waters that makes no distinct word, the soft and "
        "indistinct issuing of speech below the breath, and the gentle plashing of a stream or the stirring of a crowd in a "
        "hall; and it is the murmur of a congregation at prayer, of a brook that runs among the stones, and of an audience that talks "
        "and will not be stilled, being the low and continuous undertone, and it differs from clamour, which is a loud and "
        "importunate outcry, in being soft and even and subdued, and from hiss, which is a sharp and sibilant sound, in being low and "
        "unbroken and without edge, and from roar, which is deep and heavy and vast, in being gentle and small, and from shriek, "
        "which is the piercing cry of one throat, in being the many and quiet voices, and from silence, which is the absence of "
        "sound, in being sound that is all but no sound, being the low and gentle and continuous undertone; and it is the murmur "
        "which, whether of men or of waters, is at once a sound and a degree of silence, being the low and gentle undertone; and a "
        "person murmurs when he speaks in a low and half-heard voice, and a stream murmurs when it runs, "
        "being the low and gentle speaker; and murmur is thus the low and continuous and subdued sound of voices or of waters, the "
        "soft and indistinct issuing of speech beneath the breath, and the gentle running of a stream."
    ),
    "shriek": (
        "Shriek is the sharp and shrill and piercing cry wrung from the throat by sudden pain or terror or joy, the loud and "
        "shuddering scream of a woman or of a bird that is startled or seized, and the wild and piercing sound of a thing that is rent "
        "or breaks; and it is the shriek of the drowning man who sinks beneath the wave, of the owl beneath the moon, and of the harp "
        "that cries out as the tempest tears it, being the sharp and shrill and piercing cry, and it differs from roar, which is deep "
        "and heavy and continuous, in being acute and brief and high, and from hiss, which is a thin and deliberate sound of scorn, in "
        "being the sudden and involuntary cry of the body, and from clamour, which is the mingled outcry of many, in being the single "
        "and piercing voice, and from murmur, which is the low and even undertone, in being sharp and loud and torn from the breast, "
        "being the acute and involuntary cry; "
        "and it is the shriek which, whether of woman, of bird or of harp string, is at once a cry and a tearing of the air, being the "
        "sharp and piercing cry; and a person shrieks when he utters a shrill and piercing cry in the grip of a sudden passion, being "
        "the acute and piercing one; and shriek is thus the sharp and shrill and piercing cry of sudden pain or terror, the loud and "
        "shuddering scream of man or bird, and the wild and piercing sound of a thing that is rent."
    ),
}

TOPIC_TEST = [
    ("clamour", ("clamour", "loud outcry", "uproar of many", "noisy multitude", "din of voices", "what is clamour")),
    ("hiss", ("hiss", "sibilant sound", "sound of a snake", "boo of a crowd", "sound of steam", "what is hiss")),
    ("roar", ("roar", "roar of a lion", "roaring noise", "sound of a crowd", "what is roar", "roar of the sea")),
    ("murmur", ("murmur", "low murmur", "murmur of a crowd", "murmur of water", "low indistinct voice", "what is murmur")),
    ("shriek", ("shriek", "shriek of terror", "piercing cry", "shrill scream", "what is shriek", "cry of pain")),
]
