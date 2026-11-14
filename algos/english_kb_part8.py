# -*- coding: utf-8 -*-
"""English KB part 8: payment, debt and ransom (batch)."""

TOPICS = {
    "bribe": (
        "Bribe is the secret and unlawful gift of money, of goods or of favor which is offered "
        "to a man in office, to a judge, to a witness or to a servant of the public, in order to "
        "persuade him to act against his duty, the corrupting price of a service that ought to be "
        "given freely or denied altogether, and the payment which buys a silence, a verdict or a "
        "favor that the giver has no right to buy; and it is the bribe of a purse slid beneath a "
        "desk, of a gift dressed up as a courtesy, and of a promise whispered in a corridor, being "
        "the covert and corrupting price, and it differs from a fee, which is the lawful charge for "
        "a service rendered, in being the unlawful price paid for a service betrayed, being the "
        "surreptitious and corrupting payment, and it differs also from a tribute, which is the "
        "acknowledged payment of submission, and from a ransom, which is the purchase of a prisoner, "
        "in being the purchase of a man's partiality, being the private and guilty bargain; and it is "
        "the bribe which, offered or taken, is at once a sin and a crime, being the double guilt of "
        "the giver and the taker; and a man takes a bribe when he sells his office for a secret "
        "consideration, being the corrupted and unfaithful servant; and bribe is thus the secret and "
        "unlawful gift offered to turn a man from his duty, the corrupting price of a betrayed "
        "trust, and the payment which buys what may not lawfully be sold."
    ),
    "ransom": (
        "Ransom is the price which is demanded and paid for the release of a captive, the sum of "
        "money or of goods given to a captor, a raider or a pirate that he may restore a person to "
        "liberty, and the purchase of a life out of bondage; and it is the ransom of a prisoner of "
        "war, of a traveler taken upon the road, and of a child seized for the sake of gain, being "
        "the paid and coercive price of liberty, and it differs from a bribe, which buys a man's "
        "partiality, in being the price of a man's body and freedom, being the purchased release "
        "from captivity, and it differs also from a debt, which is an obligation of honor between "
        "free men, and from a tribute, which is the regular payment of a subject people, in being "
        "the sudden and forcible demand of an armed hand, being the extorted and liberating price; "
        "and it is the ransom which, however willingly paid, is at once a mercy and a surrender, "
        "being the price of a life bought from power; and a family pays a ransom when it gives what "
        "is demanded for the return of one who is held, being the anxious and the constrained; and "
        "ransom is thus the price demanded for the release of a captive, the sum given to a captor "
        "that a person may go free, and the purchase of a life out of bondage."
    ),
    "debt": (
        "Debt is the state of being under obligation to pay or to return what has been received, "
        "the sum which one owes to another and is bound in honor and in law to restore, and the "
        "mutual dependence which a past kindness or a borrowed good creates between two persons; "
        "and it is the debt of a sum lent upon a promise, of a harvest shared in the lean season, "
        "and of a service rendered which calls for a service again, being the owed and acknowledged "
        "bond, and it differs from a ransom, which is an extorted price for liberty, in being the "
        "voluntary and honorable return of what was freely given, being the free and binding "
        "obligation, and it differs also from a fee, which is paid as the price of a service here "
        "and now, and from a tribute, which is paid to a master, in being the return owed to a "
        "benefactor or a creditor, being the remembered and the answerable; and it is the debt "
        "which, faithfully remembered, is at once a burden and a bond, being the tie that binds the "
        "grateful and the just; and a man is in debt when he owes what he has received and cannot "
        "yet restore, being the bound and the answerable one; and debt is thus the state of being "
        "bound to pay or to return what one has received, the sum which one owes, and the mutual "
        "dependence which a past good creates between persons."
    ),
    "fee": (
        "Fee is the price which is paid for a professional service, the settled charge which a "
        "counselor, a physician, a master or an officer receives for the exercise of his art or his "
        "office, and the lawful consideration given for work that is done by skill and by "
        "knowledge rather than by the hand of a laborer; and it is the fee of a physician called to "
        "the sick, of a counselor whose counsel is sought in a cause, and of a master who teaches "
        "the young, being the lawful and appointed price, and it differs from a bribe, "
        "which is a secret and corrupting gift, in being the open and lawful charge for honest "
        "work, being the public and the earned price, and it differs also from a debt, which is the "
        "return of what was borrowed, in being the payment for what was done and not returned, "
        "being the hired and the earned consideration, and it differs also from a tribute, which is "
        "the payment of a subject people, in being the charge of a single service freely sought, "
        "being the personal and the voluntary price; and it is the fee which, openly named, is at "
        "once a wage and a dignity, being the price that honors both the taker and the giver; and a "
        "man takes a fee when he receives the appointed reward for his skill and his office, being "
        "the lawfully hired servant; and fee is thus the price paid for a professional service, the "
        "settled charge of a counselor, and the lawful price for work done by skill."
    ),
    "tribute": (
        "Tribute is the payment which a subject people, a weaker state or a conquered province "
        "renders to its lord or its conqueror in token of submission, the regular and acknowledged "
        "offering of goods, of money or of labor which is laid upon the vanquished as the price of "
        "peace, and the dues which a ruler exacts from those beneath his hand; and it is the tribute "
        "of a province to its governor, of a weaker realm to a mightier, and of a people to the "
        "prince who has spared it, being the acknowledged and the regular submission, and it differs "
        "from a ransom, which is a single and sudden price for a captive's life, in being the "
        "continuing and the recognized payment of subjection, being the periodic and the consented "
        "price, and it differs also from a bribe, which is secret and corrupting, and from a fee, "
        "which is earned by service, in being the public token of a people's subjection, being the "
        "open and the humbling due; and it is the tribute which, faithfully rendered, is at once a "
        "peace and a servitude, being the purchased and the degrading quiet; and a people pays "
        "tribute when it renders its goods to a foreign lord rather than to arms, being the "
        "subjected and the spared; and tribute is thus the payment which a subject people renders "
        "to its lord in token of submission, the regular offering laid upon the vanquished, and the "
        "dues exacted by a conqueror from those beneath his hand."
    ),
}

TOPIC_TEST = [
    ("bribe", ("bribe", "a bribe", "offer a bribe", "take a bribe", "what is a bribe", "paid to corrupt")),
    ("ransom", ("ransom", "pay a ransom", "a ransom note", "price for a captive", "what is a ransom", "buy a man free")),
    ("debt", ("debt", "in debt", "a debt", "what is a debt", "owe a debt", "be in debt to")),
    ("fee", ("fee", "a fee", "pay a fee", "charge a fee", "what is a fee", "professional fee")),
    ("tribute", ("tribute", "pay tribute", "a tribute", "what is tribute", "render tribute", "tribute to a lord")),
]
