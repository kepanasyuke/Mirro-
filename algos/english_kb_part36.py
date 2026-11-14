# -*- coding: utf-8 -*-
"""English KB part 36: coin, mint and toll (batch)."""

TOPICS = {
    "coin": (
        "Coin is the piece of metal which is struck and stamped with the mark of an authority, "
        "the small and portable token of value that is passed from hand to hand in the market "
        "and in the street, and the hard and enduring substance in which a debt may be paid and "
        "a bargain closed; and it is the coin of the purse of a merchant, of the palm of a beggar, "
        "and of the handful that a father gives to his son going upon a journey, being the struck "
        "and circulating token of value, and it differs from a mint, which is the place and the "
        "labour by which such pieces are made, in being the thing made and issued, being the "
        "struck and the passing piece, and it differs from a toll, which is a due demanded at the "
        "gate, in being the means of payment and not the payment itself, being the portable and "
        "the reckoned piece; and it is the coin which, however small its weight, is at once an "
        "object of metal and a sign of value, being the stamped and the trusted token; and a "
        "person has coin when he holds pieces of the legal and stamped money wherewith to pay "
        "for what he needs, being the ready and the current possessor; and coin is thus the piece "
        "of stamped metal which serves as money, the portable token passed in traffic, and the "
        "hard enduring substance in which debts may be answered. "
    ),
    "mint": (
        "Mint is the place and the authority appointed for the striking of coin, the house in "
        "which metal is weighed and stamped upon the die of the sovereign with the image of a "
        "realm, and the public office whose warrant it is that every piece has the weight its "
        "legend promises; and it is the mint of a kingdom whose coin is taken in every market, "
        "of a city that guards its right in a strong place, and of a house that labours to "
        "answer the need of the realm, being the authorised and the public striking of coin, "
        "and it differs from a coin, which is the struck piece it issues, in being the "
        "institution and the craft that make it, and it differs from a purse, which is the "
        "vessel where the struck coin is kept, in being the lawful public source of it. The word "
        "likewise names a humble herb of a pungent leaf, but that herb is not confounded with the "
        "house of money, for the one is grown in a garden and the other founded by a state; and "
        "it is the mint which, lawfully chartered, is at once a workshop and a warrant, being "
        "the stamping of the public faith upon the metal; and a realm keeps a mint when its coin "
        "is struck in lawful places, being the ordered coinage; and mint is thus the seat and "
        "authority of coining, the place where metal receives the image of the state, and the "
        "craft by which the coin of a realm is made lawful. "
    ),
    "purse": (
        "Purse is the small closed vessel of leather, of cloth or of net in which a person keeps "
        "his coin, the private receptacle that is carried at the girdle or in the hand and holds "
        "the means of daily payment, and the store of money which such a vessel signifies and "
        "carries, being at once the container and the trust committed to it; and it is the purse "
        "of a traveler who guards it against the highway, of a housewife mindful of the market, "
        "and of a treasurer of a guild on the day of reckoning, being the kept and the carried "
        "store, and it differs from a coin, which is the single struck piece, in being the whole "
        "and gathered store of pieces, being the private and the holding vessel, and it differs "
        "from a mint, which is the public source of coin, in being the private place where what "
        "is made is kept, being the closed and the guarded keeping; and it is the purse which, "
        "however thin or full, is at once a protection and a temptation, being the guarded and "
        "the watched store; and a person holds the purse when he commands the disposal of the "
        "common money of a household or a company, being the keeper and the steward of the "
        "store; and purse is thus the closed vessel that holds a person's coin, the private "
        "keeping of the money in hand, and the gathered store that is carried and guarded. "
    ),
    "toll": (
        "Toll is the due which is demanded and paid for passage, the charge laid upon a "
        "traveller, a cart or a vessel at a gate, a bridge or a crossway in return for the right "
        "to pass, and the lawful public exaction by which a way is maintained and its use "
        "granted; and it is the toll of a gate in a walled town, of a bridge that must be "
        "crossed, and of a harbour bar where every bark pays for entrance, being the demanded "
        "and the passing due, and it differs from a coin, which is the means by which such a due "
        "is rendered, in being the demand itself and the right to pass, being the demanded due, "
        "and it differs from a mint, which is the public striking of the coin that pays it, in "
        "being the charge exacted for a way and not the making of money, being the passage "
        "price, and it differs from a fee, which is the charge for a service sought by one who "
        "is served, in being the price of a mere passage that no man can well avoid, being the "
        "unavoidable public due; and it is the toll which, publicly granted, is at once a "
        "compensation and an exaction, being the price of a way freely given and the price of a "
        "way withheld; and a person pays toll when he renders the appointed charge for the right "
        "to pass a gate, being the paying traveller; and toll is thus the due demanded for the "
        "privilege of passage, the charge laid at a gate or a crossing, and the public exaction "
        "by which a way is kept. "
    ),
    "usury": (
        "Usury is the taking of a hire or a gain for the lending of money, the practice of "
        "demanding back more than was lent, and the exorbitant and pitiless increase which an "
        "unjust lender exacts from a borrower in his need; and it is the usury of a hard creditor "
        "who squeezes a poor household, of a money-lender who holds a farmer's harvest by a "
        "bond, and of a cunning hand that turns another's distress into his own gain, being the "
        "hired and the pitiless increase upon a loan, and it differs from a toll, which is a "
        "public due for passage, in being a private gain demanded for the mere forbearance of "
        "time, being the taking of increase for a loan, and it differs from a mint, which is the "
        "lawful public striking of coin, in being the private and the reproved making of gain "
        "from money itself, being the undue and the censorious hire; and it is the usury which, "
        "however lawfully demanded, is at once a gain and a reproach, being the taking of "
        "increase for the lending of what lacks increase; and a person is guilty of usury when "
        "he demands for a loan more than he gave, making want itself his profit, being the hard "
        "and the pitiless lender; and usury is thus the practice of taking gain for the lending "
        "of money, the exaction of increase from a borrower in his need, and the reproved price "
        "of forbearance exacted by a hard hand. "
    ),
}

TOPIC_TEST = [
    ("coin", ("coin", "piece of money", "stamped metal", "what is a coin", "small money", "hard cash")),
    ("mint", ("mint", "place of coining", "where coin is struck", "what is a mint", "coin factory", "stamping of money")),
    ("purse", ("purse", "small money bag", "where coin is kept", "what is a purse", "keeping of money", "pocket for coin")),
    ("toll", ("toll", "charge for passage", "gate fee", "what is a toll", "bridge charge", "price of passage")),
    ("usury", ("usury", "hired money", "gain on a loan", "what is usury", "lending for gain", "hard lending")),
]
