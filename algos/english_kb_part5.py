# -*- coding: utf-8 -*-
"""English KB part 5: qualities of speech and expression (batch)."""

TOPICS = {
    "hyperbole": (
        "Hyperbole is the quality of speech which overstates a thing beyond the measure of its truth, "
        "the bold and deliberate heightening of a statement past the bounds of the literal, and the "
        "figurative magnitude which a speaker lends to a matter that its weight be felt rather "
        "than counted; and it is the hyperbole of the man who declares that he has told a thing a thousand "
        "times, of the lover who swears that his beloved outshines the sun, and of the orator who calls a "
        "single hour of reckoning an age of darkness, being the figurative heightening of speech; "
        "and it differs from verbosity, which is the swelling of words beyond the need, "
        "in being the swelling of the saying itself and not of its length, and from emphasis, which is the "
        "laying of weight upon a word that is already true, in being the falsification of the measure, "
        "being the figurative and exceeding magnification; and it is the hyperbole "
        "which, spoken in jest or in passion, is at once a pleasant ornament and a perilous untruth, being "
        "the bold exaggeration; and a person shows hyperbole when he speaks of a trifle as "
        "though it were a marvel and of a hardship as though it were a ruin, being the willing and figurative "
        "exceeder of measure; and hyperbole is thus the overstating of a thing beyond the measure of its "
        "truth, the deliberate heightening of a statement, and the figurative magnitude lent to a matter "
        "that its weight be felt."
    ),
    "verbosity": (
        "Verbosity is the quality or the state of being verbose, the habit of pouring forth a multitude of "
        "words beyond what the matter requires, and the copious and unwieldy abundance of speech in which the "
        "sense is buried beneath the sound; and it is the verbosity of the counsellor who speaks an hour upon "
        "a simple point, of the letter that runs to many pages for a single request, and of the sermon that "
        "strains a brief text through a long and winding discourse, being the copious and needless multitude "
        "of words; and it differs from hyperbole, which is the overstating of the matter itself, in being the "
        "overgrowing of the words about an honest matter, and from brevity, which is the cutting away of all "
        "that may be spared, in being the withholding of nothing and the sparing of no word, being the "
        "copious and unmeasured plenty of speech; and it is the verbosity which, whether in a treatise or in "
        "a talk, is at once a fullness of language and a poverty of meaning, being the copious and needless "
        "overflow; and a person shows verbosity when he circles a plain thing with many words and comes to it "
        "at the last, being the copious and lingering speaker; and verbosity is thus the quality of being "
        "verbose, the pouring forth of words beyond the need of the matter, and the copious abundance in "
        "which the sense is buried beneath the sound."
    ),
    "ambiguity": (
        "Ambiguity is the quality or the state of being ambiguous, the doubleness of sense in a word, a "
        "phrase or a writing whereby more than one meaning may honestly be taken from it, and the uncertain "
        "and divided signification which leaves the hearer in doubt as to which of the senses was meant; "
        "and it is the ambiguity of the oracle that may be read in two ways, of the compact that binds the "
        "parties to different readings, and of the sentence whose grammar will bear either of two "
        "constructions, being the divided and uncertain signification; and it differs from hyperbole, which "
        "is the overstating of a single sense, in being the doubting between two senses, and from emphasis, "
        "which is the fixing of attention upon one sense, in being the leaving of the sense unfixed, being "
        "the doubtful and double signification; and it is the ambiguity which, whether in a riddle, an "
        "agreement or a prophecy, is at once a richness for the poet and a snare for the judge, being the "
        "doubtful and divided sense; and a writing shows ambiguity when a plain and careful reader cannot "
        "tell whether the one thing or the other was intended, being the doubtful and double one; and "
        "ambiguity is thus the doubleness of sense in a word or a writing, the uncertain and divided "
        "signification, and the doubt which leaves the hearer to choose between two honest meanings."
    ),
    "brevity": (
        "Brevity is the quality of speech that is short and to the purpose, the noble cutting away of all "
        "words that the matter does not require, and the compactness of a saying in which nothing is lacking "
        "and nothing superfluous; and it is the brevity of the dispatch that settles a great affair in few "
        "lines, of the order given in a word upon a field of battle, and of the proverb that carries a whole "
        "counsel within a single sentence, being the short and sufficient saying; and it differs from "
        "verbosity, which is the needless plenty of words, in being the just and sufficient fewness of them, "
        "and from hyperbole, which takes its effect from the excess of the measure, in taking its effect "
        "from the restraint of it, being the short and sufficient compression; and it is the brevity which, "
        "where the matter is grave, is at once a courtesy to the hearer and a discipline of the speaker, "
        "being the short and sufficient saying; and a person shows brevity when he says in a sentence what "
        "others say in a page and loses nothing of the matter thereby, being the short and sufficient "
        "speaker; and brevity is thus the quality of speech that is short and to the purpose, the cutting "
        "away of all words the matter does not require, and the compactness in which nothing is lacking and "
        "nothing superfluous."
    ),
    "emphasis": (
        "Emphasis is the quality or the act of speech whereby weight is laid upon a word, a phrase or a "
        "thing, the stress of voice or of writing that marks it out as of chief moment, and the particular "
        "and deliberate force by which one part of a saying is made to stand above the rest; and it is the "
        "emphasis of the voice that pauses upon a name, of the page that sets a single line apart from all "
        "the others, and of the argument in which one conclusion is pressed home with all the force of the "
        "reasoning, being the marked and deliberate force; and it differs from hyperbole, which heightens "
        "the measure of the thing itself, in being the heightening of the regard paid to it, and from "
        "brevity, which shortens a saying, in being the marking of its chief word, being the marked and "
        "deliberate force of regard; and it is the emphasis which, spoken or written, is at once a guide to "
        "the sense and a warning to the careless hearer, being the marked and deliberate force; and a person "
        "shows emphasis when he so speaks or writes that the hearer cannot mistake which word bears the "
        "weight of the matter, being the deliberate and marking speaker; and emphasis is thus the laying of "
        "weight upon a word or a thing, the stress that marks it out as of chief moment, and the particular "
        "and deliberate force by which one part of a saying is made to stand above the rest."
    ),
}

TOPIC_TEST = [
    ("hyperbole", ("hyperbole", "exaggerated statement", "overstatement", "what is hyperbole", "wild exaggeration", "rhetorical exaggeration")),
    ("verbosity", ("verbosity", "too many words", "wordiness", "what is verbosity", "needless words", "longwinded speech")),
    ("ambiguity", ("ambiguity", "double meaning", "what is ambiguity", "unclear meaning", "ambiguous sense", "two readings")),
    ("brevity", ("brevity", "shortness of speech", "what is brevity", "few words", "brief statements", "saying little")),
    ("emphasis", ("emphasis", "what is emphasis", "stress on a word", "marked stress", "laying weight", "emphatic speech")),
]
