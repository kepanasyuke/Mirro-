# -*- coding: utf-8 -*-
"""English KB part 16: attire and raiment (batch)."""

TOPICS = {
    "attire": (
        "Attire is the state or the condition of being attired, the whole ordered and seemly "
        "covering of the person, and the array of garments which a man puts on when he goes "
        "abroad among his fellows; and it is the attire of a bride at her wedding, of a judge "
        "upon the bench, and of a mourner at the graveside, being the seemly and ordered "
        "covering of the body; and it differs from raiment, which is the bare stuff of which "
        "covering is made and the store of it that a house keeps, in being the whole array as it "
        "is ordered and put on for an occasion, being the composed and becoming dress of the "
        "person; and it differs from garb, which is the manner after which the clothes are cut "
        "and worn so that the wearer may be known thereby, in being the seemly disposition of "
        "the whole about the body rather than the fashion of it, being the ordered and becoming "
        "array; and it is the attire which, when a man takes thought for the fitness of what he "
        "wears and for the time and the place of the wearing, is at once a covering and a "
        "courtesy, being the obedient and decorous dress; and a person has attire when he is "
        "clothed in a whole and ordered fashion meet for the day and the company, being the "
        "seemly and complete one; and attire is thus the state of being attired, the whole "
        "ordered and seemly covering of the person, and the array of garments which a man puts "
        "on for the fellowship of men."
    ),
    "raiment": (
        "Raiment is the state or the condition of being arrayed, the whole of the garments "
        "wherewith a body is covered and made decent, and the store of such covering which a "
        "household keeps against the wear of the seasons; and it is the raiment of a beggar in "
        "his single cloak, of a king in his ermine and his mantle, and of a wanderer who has "
        "but what he stands in, being the whole covering of the body; and it differs from "
        "attire, which is the seemly ordering of that covering for the day and the company, in "
        "being the covering itself as it is owned and put on without regard to its ordering, "
        "being the plenteous and necessary covering of a man; and it differs from vesture, "
        "which is the broad and ample outer covering that is thrown about the person as a robe "
        "or a mantle, in being what is worn for decency and use rather than for breadth and "
        "majesty, being the whole and needful garment; and it is the raiment which, when a man "
        "is poor, is at once his covering and his comfort, being the little that shelters him; "
        "and a person has raiment when he is clothed in such garments as make him decent and "
        "keep him from the cold, being the covered and needful one; and raiment is thus the "
        "whole of the garments wherewith a body is covered, the decent covering of the person, "
        "and the store of clothing which a man owns for use and for warmth."
    ),
    "vesture": (
        "Vesture is the state or the condition of being invested, the broad and ample covering "
        "which is spread about the person as a robe, a mantle or a cloak, and the outer and "
        "comely garment which gives to the wearer his figure and his breadth; and it is the "
        "vesture of a priest before the altar, of a prophet in his coarse mantle, and of a "
        "bride in her veil and her long train, being the covering thrown about the person; and "
        "it differs from garb, which is the after-cut and the manner of wearing that mark the "
        "wearer and make him known among men, in being the broad outer envelope of the body "
        "rather than the fashion of its cutting, being the ample and enveloping garment; and it "
        "differs from costume, which is the whole dress of a country or a calling taken "
        "according to rule, in being the single ample covering thrown about the frame, being "
        "the wide and majestic investiture; and it is the vesture which, when it is cast about "
        "the shoulders, is at once a covering and a dignity, being the investiture that gives "
        "to the body its breadth; and a person has vesture when he is wrapped in an ample "
        "garment that covers him about from the shoulders down, being the invested and "
        "enveloped one; and vesture is thus the broad and ample covering spread about the "
        "person, the outer garment that gives figure and breadth, and the majestic envelope of "
        "the body."
    ),
    "garb": (
        "Garb is the state or the fashion of one's clothing, the manner after which it is cut, "
        "made and worn, and the outward appearance of the wearer by which his country, his "
        "calling or his estate may be known; and it is the garb of a sailor in his rough "
        "jacket, of a bride in her white, and of a stranger whose dress betrays the land he "
        "comes from, being the fashion of the wearer's dress; and it differs from attire, which "
        "is the seemly ordering of the whole covering for the time and the company, in being "
        "the once-fixed fashion that makes the wearer a sign to others, being the manner of the "
        "making rather than the order of the wearing; and it differs from costume, which is the "
        "whole dress of a country or a calling taken according to rule, in being the look of the "
        "clothing rather than the written custom of its wearing, being the fashion of the dress "
        "and not the rule of it; and it is the garb which, when it is "
        "true to a country or a calling, is at once a clothing and a mark, being the clothing "
        "that declares the wearer; and a person is in such garb when his dress, cut and worn "
        "after the manner of a place or a state of life, makes him known for what he is, being "
        "the recognizable and marked one; and garb is thus the fashion of one's clothing, the "
        "manner after which it is cut and worn, and the outward mark by which the wearer is "
        "known among men."
    ),
    "costume": (
        "Costume is the state or the prescribed whole of dress observed by a people, a "
        "calling, a season or a play, the complete and ordered set of garments which custom "
        "appoints for a time and an office, and the settled rule which makes one dress "
        "becoming and another unseemly; and it is the costume of a high feast, of a whole "
        "nation in its festival, and of a player upon the stage, being the whole prescribed "
        "dress of a calling or a time; and it differs from attire, which is the seemly "
        "ordering of the day taken for the person's own use, in being the whole dress enjoined "
        "by custom or by office rather than chosen by the wearer for the occasion, being the "
        "prescribed and customary whole; and it differs from vesture, which is the single "
        "ample covering thrown about the person, in being the entire set of garments worn "
        "according to rule, being the complete and prescribed dress; and it is the costume "
        "which, while it lasts in use, is at once a dress and a rule, being the dress which "
        "answers to the time and the calling; and a person is in costume when his clothing "
        "answers to the time, the country or the office appointed, being the conforming and "
        "prescribed one; and costume is thus the whole prescribed dress of a people or a "
        "calling, the complete set of garments which custom appoints for a time, and the "
        "settled rule of what is seemly to wear."
    ),
}

TOPIC_TEST = [
    ("attire", ("attire", "what is attire", "array of garments", "rich attire", "attire meaning", "dress of a person")),
    ("raiment", ("raiment", "what is raiment", "raiment meaning", "clothing for the body", "raiment and vesture", "store of garments")),
    ("vesture", ("vesture", "what is vesture", "vesture meaning", "vesture and garb", "ample robe", "vesture of a mantle")),
    ("garb", ("garb", "what is garb", "garb meaning", "garb and costume", "clerical garb", "fashion of dress")),
    ("costume", ("costume", "costume meaning", "what is costume", "national costume", "costume and attire", "costume of a calling")),
]
