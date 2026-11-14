# -*- coding: utf-8 -*-
"""English KB part 18: sounds and noises (batch)."""

TOPICS = {
    "clamour": (
        "Clamour is the loud and importunate outcry of many voices together, the confused and swelling noise of a multitude that "
        "shouts and demands, and the urgent and unruly din by which a crowd presses its will upon the ear; and it is the clamour of "
        "the marketplace at noon, of the mob before the magistrate's door, and of a people that will not be denied, being the "
        "multitudinous and urgent outcry, and it differs from hiss, which is the sharp and sibilant sound of contempt, in being the "
        "mingled and unceasing cry of many, and from murmur, which is a low and continuous mutter, in being loud and importunate, and "
        "from roar, which is the deep and prolonged bellow of a single beast or of a great mass, in being the many and disordered "
        "voice, being the urgent and confused outcry of a multitude; and it is the clamour which, whether of petition or of protest, "
        "is at once a demand of the many and a sound without form, being the loud and importunate outcry; and a person raises a "
        "clamour when he cries out with a loud and repeated voice among others who cry likewise, being the loud and importunate "
        "crier; and clamour is thus the loud and importunate outcry of many voices together, the confused and swelling noise of a "
        "multitude that demands, and the urgent and unruly din that presses upon the ear."
    ),
    "hiss": (
        "Hiss is the sharp and prolonged sibilant sound made by the forcing of breath or steam through a narrow passage, the thin "
        "and contemptuous sound of a serpent or of an angry audience, and the act of uttering such a sound in derision or warning; and "
        "it is the hiss of the kettle upon the fire, of the serpent roused in the grass, and of the gallery that condemns an actor to "
        "silence, being the sharp and sibilant sound, and it differs from shriek, which is the shrill and piercing cry of pain or "
        "terror, in being the cold and deliberate sound of derision, and from murmur, which is the soft and subdued uttering of many, "
        "in being the sharp and hissing breath, and from roar, which is the deep and heavy volume of a beast or a multitude, in being "
        "thin and sibilant and brief, being the sharp and contemptuous sibilant; and it is the hiss which, whether of steam, of "
        "serpent or of scorn, is at once a sound of the body and a judgment of the will, being the sharp and sibilant sound; and a "
        "person hisses when he utters the sibilant sound in contempt or displeasure, being the contemptuous and sibilant one; and "
        "hiss is thus the sharp and prolonged sibilant sound of breath or steam, the thin and contemptuous sound of the serpent or of "
        "the angry audience, and the act of uttering it in derision or in warning."
    ),
    "roar": (
        "Roar is the deep and heavy and prolonged sound that issues from the throat of a great beast, from the throat of a man in "
        "fury or in pain, and from the rushing of waters or of a great engine in motion; and it is the roar of the lion in the "
        "wilderness, of the crowd in the amphitheatre, and of the sea upon a rocky shore, being the deep and sustained volume of "
        "sound, and it differs from shriek, which is a shrill and piercing cry of terror, in being deep and sustained and heavy, and "
        "from hiss, which is the thin and sibilant breath of contempt, in being loud and full and bodily, and from clamour, which is "
        "the confused and importunate voice of many, in being the one and continuous and heavy sound, being the deep and continuous "
        "bellow; and it is the roar which, whether of beast, of crowd or of waters, is at once a sound of power and a fear to the "
        "hearer, being the deep and heavy volume of sound; and a thing roars when it utters or gives forth a deep and prolonged and "
        "heavy sound, being the deep and bellowing one; and roar is thus the deep and heavy and prolonged sound of a great beast or "
        "of a man in fury, the vast and continuous voice of waters or of engines, and the dreadful and measureless noise of power in "
        "motion."
    ),
    "murmur": (
        "Murmur is the low and continuous and subdued sound of voices or of water that makes no distinct word, the soft and "
        "indistinct issuing of speech below the breath, and the gentle and steady plashing of a stream or the rustling stir of a "
        "crowd in a hall; and it is the murmur of a congregation at prayer, of a brook that runs among the stones, and of the "
        "audience that talks and cannot be stilled, being the low and continuous undertone, and it differs from clamour, which is a "
        "loud and importunate outcry, in being soft and even and subdued, and from hiss, which is a sharp and sibilant sound, in being "
        "low and unbroken and without edge, and from roar, which is deep and heavy and vast, in being gentle and small and "
        "continuous, being the low and gentle and continuous undertone; and it is the murmur which, whether of men or of waters, is "
        "at once a sound and a degree of silence, being the low and continuous and gentle undertone; and a person murmurs when he "
        "speaks in a low and indistinct and half-heard voice, and a stream murmurs when it runs with a soft and steady sound, being "
        "the low and gentle speaker; and murmur is thus the low and continuous and subdued sound of voices or of waters, the soft "
        "and indistinct issuing of speech beneath the breath, and the gentle measureless running of a stream."
    ),
    "shriek": (
        "Shriek is the sharp and shrill and piercing cry wrung from the throat by sudden pain or terror or joy, the loud and "
        "shuddering scream of a woman or a bird that has been startled or seized, and the wild and piercing sound of a thing that is "
        "rent or breaks; and it is the shriek of the drowning man who sinks beneath the wave, of the owl beneath the moon, and of the "
        "harp that shrieks as it is torn by the tempest, being the sharp and shrill and piercing cry, and it differs from roar, which "
        "is deep and heavy and continuous, in being acute and brief and high, and from hiss, which is a thin and deliberate sound of "
        "scorn, in being the sudden and involuntary cry of the body, and from clamour, which is the mingled outcry of many, in being "
        "the single and piercing voice, being the acute and involuntary shriek; and it is the shriek which, whether of woman, of bird "
        "or of harp string, is at once a cry and a tearing of the air, being the sharp and piercing cry; and a person shrieks when he "
        "utters a shrill and piercing cry in the grip of a sudden passion, being the acute and piercing cryer; and shriek is thus the "
        "sharp and shrill and piercing cry of sudden pain or terror, the loud and shuddering scream of man or bird, and the wild and "
        "piercing sound of a thing that is rent."
    ),
}

TOPIC_TEST = [
    ("clamour", ("clamour", "loud outcry", "uproar of many", "noisy multitude", "din of voices", "what is clamour")),
    ("hiss", ("hiss", "sibilant sound", "sound of a snake", "boo of a crowd", "sound of steam", "what is hiss")),
    ("roar", ("roar", "roar of a lion", "roaring noise", "sound of a crowd", "what is roar", "roar of the sea")),
    ("murmur", ("murmur", "low murmur", "murmur of a crowd", "murmur of water", "low indistinct voice", "what is murmur")),
    ("shriek", ("shriek", "shriek of terror", "piercing cry", "shrill scream", "what is shriek", "cry of pain")),
]
