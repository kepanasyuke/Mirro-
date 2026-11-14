# -*- coding: utf-8 -*-
"""English KB part 11: writing, syllables and hand (batch)."""

TOPICS = {
    "abbreviation": (
        "An abbreviation is the shortening of a word or of a phrase by the cutting away of its letters, "
        "the contracted and diminished form which stands in the place of the whole, and the sign or the "
        "group of signs which gives back the hidden word; and it is the abbreviation "
        "of a title that is written after a name, of a measure set down as a single letter upon a "
        "page, and of the long and familiar name that men shorten for speed, being the shortened and "
        "standing form of a word; and it differs from an alphabet, which is the whole and ordered set of "
        "letters, in taking a part of the word for the whole, being the diminished and substituted form, "
        "and it differs from a syllable, which is a piece of the spoken word, in being a piece cut from the "
        "written word for the sake of haste, being the written and contracted sign; and it is the "
        "abbreviation which, permitted by the custom of a trade or a science, is at once a convenience to "
        "the hand and a danger to the reader who knows not the custom, being the short and standing form; "
        "and a writing shows abbreviations when it shortens the words that are oftenest used and takes its "
        "sense from the agreement of those who read it, being the contracted and current one; and an "
        "abbreviation is thus the shortening of a word by the cutting away of letters, the contracted form "
        "that stands for the whole, and the sign which returns that word to him who reads it."
    ),
    "alphabet": (
        "An alphabet is the whole and ordered set of letters with which a language is written, the "
        "complete company of signs each standing for a sound, and the fixed and received order in which "
        "those signs are learned and set down; and it is the alphabet of a tongue that is sung over by "
        "children in the schoolroom, of a people who owe their letters to a distant nation, and of a "
        "script that carries its own order into printing, indexing and the naming of things, being the "
        "ordered and complete set of letters; and it differs from a syllable, which is a unit of the "
        "spoken word, in being the unit of the written word, being the store of signs from which all "
        "writing is drawn, and it differs from handwriting, which is the manner of forming those signs, in "
        "being the signs themselves and their order, being the received and numbered letters; and it is "
        "the alphabet which, once fixed and taught, is at once a whole instrument of utterance and the "
        "first key to every book, being the ordered and public set of signs; and a language has an "
        "alphabet when its speech can be written down letter by letter and read back again by any who "
        "know the order, being the written and lettered tongue; and an alphabet is thus the ordered set of "
        "letters for writing a language, the complete company of signs for its sounds, and the fixed order "
        "in which they are learned and set down."
    ),
    "syllable": (
        "A syllable is a single and complete sound of the voice uttered in one breath, the unit of spoken "
        "speech into which a word is divided and which may be held or struck as one, and the least part of "
        "a word that the ear can take by itself; and it is the syllable of a name that is counted by the "
        "poet, of a word that is broken across the line of a page, and of a cry that the child utters "
        "before it can speak at all, being the single and sounded unit of speech; and it differs from an "
        "alphabet, which is the written sign of a sound, in being the sound itself as spoken and heard, "
        "being the unit of the voice, and it differs from grammar, which orders whole words and sentences, "
        "in ordering only the breath and the beat within the single word, being the smallest and sounded "
        "measure of speech; and it is the syllable which, once marked for its length and its stress, is at "
        "once the ground of verse and the measure of the plainest speaking, being the single and complete "
        "sound; and a word has many syllables when it must be spoken in several breaths and broken into "
        "several beats, being the sounded and divided one; and a syllable is thus a single sound of the "
        "voice in one breath, the unit into which speech is divided, and the least part of a word that the "
        "ear can take by itself."
    ),
    "grammar": (
        "Grammar is the whole body of rules by which the words of a language are formed, joined and "
        "ordered into speech, the art of speaking and writing according to the custom of a tongue, and the "
        "study which sets down that art in its parts and its laws; and it is the grammar of a language that "
        "the child learns at school, of a scholar who sets it down in a book, and of a people whose speech "
        "keeps its order without knowing the name of it, being the ordered law of the tongue; and it "
        "differs from a syllable, which is a single sound within a word, in governing whole words and "
        "sentences in their place and their dependence, being the law of the whole construction, and it "
        "differs from handwriting, which is the shape of the letters upon the page, in being the shape of "
        "the thought in the sentence, being the ordered and lawful joining of words; and it is the grammar "
        "which, whether in speech or in writing, is at once the discipline of the careless and the "
        "unnoticed custom of the learned, being the law of the tongue; and a person shows grammar when he "
        "so orders his words that each takes the form and the place which his language demands, being the "
        "lawful and ordered speaker; and grammar is thus the body of rules by which words are formed and "
        "joined into speech, the art of speaking according to the custom of a tongue, and the study which "
        "sets that art down in its parts and laws."
    ),
    "handwriting": (
        "Handwriting is the manner in which a person forms the letters of his script with the hand, the "
        "particular and personal character of his written signs, and the writing itself as it comes from "
        "the pen and is known by its trace; and it is the handwriting of the clerk whose fair "
        "letters fill the page, of the scholar whose hand is hasty, and of the friend whose "
        "note is known from across the room before a word of it is read, being the personal and formal "
        "trace of the hand; and it differs from an alphabet, which is the common and public set of "
        "letters, in being the private manner of forming them, being the personal and customary hand, and "
        "it differs from an abbreviation, which shortens a word to save the hand's labour, in being the "
        "full and unshortened working of the hand, being the personal and formal trace; and it is the "
        "handwriting which, taught in the copybook and thereafter turned to the haste of life, is at once "
        "the outward sign of a person and the plainest witness of his care, being the personal and formal "
        "trace; and a person shows handwriting when the letters of his page bear a character that is "
        "recognized as his own and no other's, being the personal and formal writer; and handwriting is "
        "thus the manner of forming letters with the hand, the personal character of a person's written "
        "signs, and the writing itself as it comes from the pen and is known by its trace."
    ),
}

TOPIC_TEST = [
    ("abbreviation", ("abbreviation", "what is an abbreviation", "shortened word", "abbreviated form", "short form of word", "abbreviation meaning")),
    ("alphabet", ("alphabet", "what is an alphabet", "set of letters", "letters of a language", "alphabetical order", "abc")),
    ("syllable", ("syllable", "what is a syllable", "part of a word", "syllables in a word", "unstressed syllable", "syllable meaning")),
    ("grammar", ("grammar", "what is grammar", "rules of a language", "english grammar", "grammatical rules", "grammar meaning")),
    ("handwriting", ("handwriting", "what is handwriting", "one's hand", "writing of a person", "bad handwriting", "handwriting meaning")),
]
