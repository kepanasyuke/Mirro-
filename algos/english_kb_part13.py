# -*- coding: utf-8 -*-
"""English KB part 13: decree, edict and ordinance (batch)."""

TOPICS = {
    "decree": (
        "Decree is the act of determining and ordering by authority, the solemn resolution whereby a "
        "matter is settled and commanded to be done, and the binding sentence that stands as the rule "
        "of it; and it is the decree of a judge upon a cause, of a council upon a question of faith, "
        "and of a ruler upon the affairs of a realm, being the solemn and declared resolution, and it "
        "differs from an edict, which is that resolution cried abroad to all, in being the deciding act "
        "and not the publishing of it, and it differs from an ordinance, which is a standing rule for "
        "the governing of a place, in being the determination of one matter, and it differs from a "
        "mandate, which is a charge committed to a bearer, in being the sentence itself and not the "
        "commission that carries it, and it differs from an injunction, which restrains a party from "
        "an act, in binding the whole matter rather than staying a single hand; and it is the decree "
        "which, whether of a court, a council or a prince, is at once the end of the doubt and the "
        "beginning of the duty; and a judge makes a decree when he settles a cause by a solemn "
        "sentence; and decree is thus the act of ordering by authority, the resolution that settles a "
        "matter, and the sentence that commands its doing."
    ),
    "edict": (
        "Edict is the formal and public proclamation of a command or an intention, the solemn notice "
        "which a power causes to be published abroad that all men may know its will, and the open word "
        "of authority cried at the gate; and it is the edict of a prince concerning his succession, of "
        "a governor concerning the taxes of a province, and of a senate concerning the exiles of a "
        "city, being the published and authoritative proclamation, and it differs from a decree, which "
        "is the sentence that determines a matter, in being the making known of that sentence to the "
        "world that must obey it, and it differs from an ordinance, which is a standing rule long "
        "kept, in being a will uttered at a time and not the settled frame of order, and it differs "
        "from a mandate, which is a charge laid upon one man, in being the word uttered to all and not "
        "the burden put upon a single hand, and it differs from an injunction, which is a restraint "
        "laid upon a party, in being proclaimed to a whole people and not addressed to one; and it is "
        "the edict which, whether of a king, a magistrate or a council, is at once the utterance of the "
        "will and the law of those who hear; and a prince issues an edict when he causes his will to "
        "be cried abroad where all may read it; and edict is thus the public proclamation of a "
        "command, the solemn notice published abroad by authority, and the obeyed word of the power "
        "that utters it."
    ),
    "ordinance": (
        "Ordinance is the act of disposing and ordering in due form, the settled rule made by lawful "
        "authority for the governing of a place, and the prescribed rule that a common life may be "
        "kept in peace; and it is the ordinance of a city touching the keeping of the market, of a "
        "guild touching the admission of its members, and of a household touching its hours of "
        "labour, being the standing rule, and it differs from a decree, which is the sentence of a "
        "particular cause, in being the general frame of order and not the closing word in one matter, "
        "and it differs from an edict, which is a word cried once to all, in being the rule that is in "
        "use and long kept, and it differs from a mandate, which is a charge committed to a person, in "
        "being the rule appointed for all within the place and not the burden laid upon one bearer, "
        "and it differs from an injunction, which forbids an act to a party, in being the positive "
        "ordering of a manner of life and not the staying of a hand; and it is the ordinance which, "
        "whether of a city, a guild or a household, is at once the rule set forth and the order thereby "
        "kept; and a body has an ordinance when it appoints by authority the manner in which its common "
        "life is to be ordered; and ordinance is thus the settled rule of a governing authority, the "
        "standing appointment for the ordering of a place, and the prescribed manner in which a "
        "common life is kept."
    ),
    "mandate": (
        "Mandate is the act of committing a charge to another, the commission by which power is given "
        "to one man to act in the name of the giver, and the conveyed authority under which the "
        "charged one must do a prescribed thing; and it is the mandate of a prince to his envoy, of a "
        "court to its officer, and of a trusting man to his steward, being the committed charge, and "
        "it differs from a decree, which is the sentence that settles a matter, in being the charge "
        "that carries the sentence into other hands and not the word that determines it, and it "
        "differs from an edict, which is the proclamation made to the world, in being a charge given "
        "to one named bearer and not a voice cried to all, and it differs from an ordinance, which is "
        "a rule standing for all within a place, in being the particular commission laid upon a chosen "
        "person, and it differs from an injunction, which is a restraint laid upon a party, in being a "
        "power given and not a power withheld; and it is the mandate which, whether of a council, a "
        "court or a master, is at once the will of the giver and the duty of the bearer; and a person "
        "holds a mandate when a charge is committed to him which he must execute in the name of "
        "another; and mandate is thus the committing of a charge to another, the warrant by which "
        "power is given to act for the giver, and the conveyed authority under which a prescribed "
        "thing must be done."
    ),
    "injunction": (
        "Injunction is the act of enjoining, the authoritative charge by which one is required to do a "
        "prescribed thing or is restrained from doing what he would, and the binding word laid upon "
        "one who must hear and obey it; and it is the injunction of a parent to a child that he "
        "forbear, of a physician to one that he rest, and of a court to a party that he cease, being "
        "the charging and restraining word, and it differs from a decree, which is the sentence that "
        "determines a matter, in being the charge pressed upon a party to do or forbear within the "
        "matter, and it differs from an edict, which is a proclamation cried abroad, in being addressed "
        "to one or few and not published to all, and it differs from an ordinance, which is a rule kept "
        "by all within a place, in being the particular command laid upon a named party in a present "
        "cause, and it differs from a mandate, which is a power given to one to act, in being for the "
        "most part a command to forbear and withhold the hand; and it is the injunction which, whether "
        "of a court, a parent or a counsellor, is at once the command laid upon the will and the "
        "barrier set before the hand; and a person receives an injunction when an authority lays upon "
        "him a solemn charge to do or to forbear; and injunction is thus the act of enjoining, the "
        "charging word that requires a prescribed act, and the restraining command which binds one to "
        "forbear."
    ),
}

TOPIC_TEST = [
    ("decree", ("decree", "what is a decree", "court decree", "solemn decree", "royal decree", "decree of the council")),
    ("edict", ("edict", "what is an edict", "public edict", "edict of the prince", "royal edict", "edict proclaimed abroad")),
    ("ordinance", ("ordinance", "what is an ordinance", "city ordinance", "standing ordinance", "ordinance of the guild", "ordinance of a place")),
    ("mandate", ("mandate", "what is a mandate", "given a mandate", "mandate to act", "mandate of authority", "entrusted mandate")),
    ("injunction", ("injunction", "what is an injunction", "court injunction", "receive an injunction", "injunction to forbear", "injunction of a parent")),
]
