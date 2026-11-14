# -*- coding: utf-8 -*-
"""English KB part 17: dwelling and shelter (batch)."""

TOPICS = {
    "dwelling": (
        "Dwelling is the place in which a person has his fixed abode and his settled life, the house or the roof under which he abides by night and by day, and the place of habitation which he calls his own; "
        "and it is the dwelling of a family in a quiet street, of a solitary man in the lonely valley, and of a people in the shared house of the common ward, being the settled and inhabited place; "
        "and it differs from a mansion, which is a house of great and lordly scale, in being the place considered merely as the seat of habitation and of daily life, being the inhabited and abiding place, and from a cottage, which is a small house in the country, and from a hut, which is a slight and rough shelter, and from a tenement, which is a house of many rented rooms, in being none of these in its own right but the general seat of living which each of them may be; "
        "and it is the dwelling which, whether humble or great, is at once the lodging of the body and the home of the affections, being the settled and cherished abode; "
        "and a person has his dwelling in a place when he abides there and returns to it as to his own, being the abiding and settled one; "
        "and dwelling is thus the place in which a person has his fixed abode and his settled life, the house or the roof under which he abides, and the place of habitation which he calls his own."
    ),
    "mansion": (
        "Mansion is the great and stately house of a lord or of a man of ample means, the spacious and lordly dwelling which shows forth the dignity of its owner, and the house of many rooms and of noble front which stands apart in its own ground; "
        "and it is the mansion of a great landowner, of a prosperous merchant, and of the seat of an ancient family, being the great and lordly house; "
        "and it differs from a dwelling, which is the mere place of habitation, in being the house of grandeur and of public dignity, being the stately and lordly house, and from a cottage, which is a small and modest house, and from a tenement, which is a house of many narrow rented rooms, and from a hut, which is a rough and slight shelter, in being the great house of a single house and of ample and noble scale; "
        "and it is the mansion which, standing in its own ground and showing its noble front, is at once the pride of its owner and the mark of his rank, being the great and dignified house; "
        "and a place is called a mansion when it is a great and stately house of many rooms and of noble aspect, being the lordly and ample one; "
        "and mansion is thus the great and stately house of a lord or of a man of ample means, the spacious dwelling which shows forth the dignity of its owner, and the house of noble front which stands apart in its own ground."
    ),
    "cottage": (
        "Cottage is the small and modest house of a countryman, the little dwelling of the husbandman or of the rustic poor, and the simple and homely house in the field or at the edge of the village; "
        "and it is the cottage of a shepherd, of a woodman, and of a poor family in the country, being the small and humble house; "
        "and it differs from a dwelling, which is the general place of habitation, in being the little and rustic house of the country, being the small and homely house, and from a mansion, which is the great and stately house, and from a tenement, which is a house of many crowded rented rooms, and from a hut, which is a rough and slight erection, in being the honest and lowly house of a single family, built of plain stuff and covered by its own low roof; "
        "and it is the cottage which, with its low roof and its little garden, is at once the dwelling of the poor and the picture of a simple life, being the small and homely house; "
        "and a place is called a cottage when it is a small and modest house of the country habited by one family, being the little and rustic one; "
        "and cottage is thus the small and modest house of a countryman, the little dwelling of the husbandman, and the simple and homely house in the field or at the edge of the village."
    ),
    "hut": (
        "Hut is the slight and rough erection in which a man shelters himself from the weather, the mean and hurried covering of boughs or of clayey earth, and the poor and lowly booth of the wanderer, the hunter or the captive; "
        "and it is the hut of a shepherd on the hill, of a hunter in the forest, and of a toiling people in a distant land, being the slight and rough shelter; "
        "and it differs from a dwelling, which is the settled place of habitation, in being the slight and hastily made covering, being the mean and temporary shelter, and from a cottage, which is a small house but a house indeed, and from a mansion, which is a great and stately house, and from a tenement, which is a house of many rented rooms, in being the rudest and most temporary of coverings, raised of boughs or of clay and abandoned at need; "
        "and it is the hut which, whether of reeds, of boughs or of earth, is at once the barest shelter and the meanest home, being the slight and lowly covering; "
        "and a person lives in a hut when he lodges in a slight and rough erection raised for shelter from the weather, being the poorly sheltered one; "
        "and hut is thus the slight and rough erection in which a man shelters himself from the weather, the mean covering of boughs or of earth, and the poor and lowly booth of the wanderer, the hunter or the captive."
    ),
    "tenement": (
        "Tenement is the house of many small and rented rooms, the common dwelling of the poor where many families crowd their many chambers, and the building which one man holds and lets out in parts to many tenants; "
        "and it is the tenement of a crowded street, of a poor and toiling quarter, and of a people who have no other roof, being the crowded and rented house; "
        "and it differs from a dwelling, which may be the settled home of a single family, in being the house of many households held in one hand for gain, being the shared and rented house, and from a mansion, which is the great house of one owner's dignity, and from a cottage, which is the little house of one family in the country, and from a hut, which is a slight and passing covering, in being the high and many-storied house whose chambers are let to many tenants; "
        "and it is the tenement which, standing in its crowded street and holding many families beneath one roof, is at once the shelter of the poor and the mark of a hard and crowded city, being the crowded and rented house; "
        "and a house is a tenement when it is raised and let out in many small chambers to many families, being the rented and shared one; "
        "and tenement is thus the house of many small and rented rooms, the common dwelling of the poor, and the building which one man holds and lets out in parts to many tenants."
    ),
}

TOPIC_TEST = [
    ("dwelling", ("dwelling", "place of living", "where one lives", "what is a dwelling", "abode", "place inhabited")),
    ("mansion", ("mansion", "great house", "stately house", "large house", "what is a mansion", "lordly house")),
    ("cottage", ("cottage", "small country house", "country house", "humble house", "what is a cottage", "rustic house")),
    ("hut", ("hut", "rough shelter", "mean shelter", "slight shelter", "what is a hut", "booth of boughs")),
    ("tenement", ("tenement", "rented rooms", "crowded house", "house of many rooms", "what is a tenement", "poor lodgings")),
]
