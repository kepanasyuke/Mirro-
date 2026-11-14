# -*- coding: utf-8 -*-
"""English KB part 15: repast and viands (batch)."""

TOPICS = {
    "repast": (
        "Repast is the act of taking food and drink at a stated time, the settled and orderly meal which "
        "gathers a household or a company about a board, and the appointed occasion on which the body is "
        "refreshed and the day is punctuated by its intervals of rest; and it is the repast of the morning "
        "taken in haste before the labours of the day, of the evening when the household assembles, and of "
        "the traveller who halts upon the road, being the settled and orderly meal, and it differs from a "
        "banquet, which is a great and stately entertainment, in being the modest and recurrent meal of the "
        "household, being the plain and appointed occasion of sustenance; and it differs from the viands "
        "themselves, which are the things set out, in being the act of dining and the hour thereof, being "
        "the occasion and not the provision; and it is the repast which, appointed by custom and taken in "
        "common, is at once the refreshment of the body and the bond of the household, being the settled "
        "and shared occasion; and a person makes a repast when he sits down at the accustomed hour to eat "
        "and drink, being the one who dines and not the food he dines upon; and repast is thus the act of "
        "taking food at a stated time, the settled and orderly meal of the household, and the appointed "
        "occasion on which the body is refreshed. "
    ),
    "banquet": (
        "Banquet is a great and stately entertainment of many guests, the sumptuous and ceremonial repast "
        "spread for honour, festivity or the solemn reception of the great, and the ordered and abundant "
        "spread at which speech, music and formality attend the board; and it is the banquet of a coronation, "
        "of a wedding or a treaty of peace, and of the guild that feasts its officers once in the year, "
        "being the great and ceremonial entertainment, and it differs from a repast, which is the modest "
        "and recurrent meal of the household, in being the public and lavish festivity of many, being the "
        "ceremonial and abundant one; and it differs from a dainty, which is a single delicate morsel, in "
        "being the whole stately occasion, being the great and ordered entertainment; and it is the banquet "
        "which, given in honour or in festivity, is at once a provision for many and a display of magnificence, "
        "being the stately and abundant entertainment; and a person gives a banquet when he summons guests "
        "to a great and ceremonial repast and sets before them his best, being the lavish and honoured host; "
        "and banquet is thus a great and stately entertainment of many guests, the sumptuous and ceremonial "
        "repast spread for honour or festivity, and the ordered and abundant spread of the great. "
    ),
    "viands": (
        "Viands are the articles of food provided for a meal, the things set out upon the table to be eaten, "
        "and the whole provision of victual which has been gathered and made ready for the board; and they "
        "are the viands of the market, of the kitchen and of the table, and of the country feast that is "
        "laid out in many dishes, being the provided articles of food, and they differ from a repast, which "
        "is the occasion and the hour of eating, in being the provender itself and not the act of dining, "
        "being the set out and prepared food; and they differ from a banquet, which is the stately and "
        "festive occasion, in being merely the things whereof the occasion is made, being the dishes and "
        "the victual; and they differ from a dainty, which is one rare and delicate morsel, in being the "
        "plentiful and ordinary provision of the table, being the common and the solid victual; and it is "
        "the viands which, set out in use and order, are at once the substance of the meal and the visible "
        "mark of the household's state, being the prepared and provided articles; and a board has viands "
        "when there are dishes upon it to be eaten, being the set out and furnished table; and viands are "
        "thus the articles of food provided for a meal, the things set out upon the table, and the whole "
        "provision of victual made ready for the board. "
    ),
    "dainty": (
        "Dainty is a thing of delicate and exquisite excellence in the way of meat and drink, the rare and "
        "choice morsel which pleases by its fineness of flavour and its curious and costly quality, and the "
        "little delicacy prized for its daintiness rather than for the strength of the sustenance it yields; "
        "and it is the dainty of the confectioner, of the rare fruit brought from far, and of the sweet "
        "meat that is offered to the honoured guest, being the rare and choice morsel, and it differs from "
        "viands, which are the plentiful provision of the table, in being the single and exquisite morsel "
        "set apart, being the rare and delicate one; and it differs from a banquet, which is the whole "
        "stately entertainment, in being the small and chosen thing within it, being the choice and the "
        "confection; and it is the dainty which, offered to the palate for delight, is at once a thing of "
        "fineness and a mark of favour, being the delicate and prized morsel; and a person receives a "
        "dainty when he is set before a rare and delicate thing of the table, being the favoured and "
        "delighted guest; and dainty is thus a thing of delicate excellence in meat and drink, the rare "
        "and choice morsel, and the little delicacy prized for its fineness. "
    ),
    "fare": (
        "Fare is the provision of food and drink that is set before one, the kind and quality of the "
        "victual which the table affords, and the whole condition of the board as it is supplied from day "
        "to day; and it is the fare of the inn, of the ship at sea, and of the humble household that lives "
        "upon simple things, being the provision and its quality, and it differs from viands, which are "
        "the particular articles set out, in being the general and standing supply of the table, being the "
        "kind and quality of the provision; and it differs from a repast, which is one appointed meal, in "
        "being the continual tenor of the board through the days, being the standing provision; and it "
        "differs from a banquet, which is the stately festivity, in being the ordinary and the daily, "
        "being the plain and the customary supply; and it is the fare which, in house or in inn or upon "
        "the sea, is at once the supply of the body and the sign of the estate of those who are fed, "
        "being the kind and quality of the provision; and a traveller finds good fare when the table set "
        "before him is plentiful and well made, being the well supplied and contented guest; and fare is "
        "thus the provision of food and drink set before one, the kind and quality of the victual, and "
        "the condition of the board supplied from day to day. "
    ),
}

TOPIC_TEST = [
    ("repast", ("repast", "what is a repast", "a meal taken", "daily meal at noon", "sit down to repast", "appointed meal")),
    ("banquet", ("banquet", "what is a banquet", "great feast for guests", "stately entertainment", "ceremonial dinner party", "sumptuous feast")),
    ("viands", ("viands", "what are viands", "food for a meal", "articles of food", "dishes set out", "provender of the table")),
    ("dainty", ("dainty", "what is a dainty", "a delicate morsel", "rare choice food", "sweetmeat of choice", "fine delicacy")),
    ("fare", ("fare", "what is fare", "food provided for", "board of an inn", "quality of the food", "supply of victual")),
]
