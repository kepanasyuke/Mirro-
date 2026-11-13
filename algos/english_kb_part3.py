# -*- coding: utf-8 -*-
"""English KB part 3: qualities of matter (batch)."""

TOPICS = {
    "viscosity": (
        "Viscosity is the state of being viscous, the thick and clinging and slow-flowing "
        "character of a substance, the tenacious and resisting hold which the parts of a "
        "thing keep one upon another, and the sluggishness with which a liquid or a soft "
        "body yields to the pressure that would stir it; and it is the viscosity of tar "
        "and of thick oil, of honey and of warm resin, and of heavy pitch in the heat of "
        "the day, being the thick and slow-flowing and tenacious quality, and it differs "
        "from fluidity, which is the ready and willing yielding of matter to every form, "
        "in being the stubborn and reluctant yielding, being the clinging and sluggish "
        "state; and it is the viscosity which, the colder or the thicker the body, the "
        "less it will run and the more it will cling, being at once a sluggishness and a "
        "tenacity; and a thing shows viscosity when it pours heavy and slow and adheres "
        "to the vessel that holds it, being the thick and slow one; and viscosity is thus "
        "the state of being viscous, the thick and clinging and slow-flowing character of "
        "a substance, and the sluggish resistance with which matter yields to stirring."
    ),
    "fluidity": (
        "Fluidity is the state of being fluid, the ready and yielding and untroubled "
        "character of a substance that takes the shape of its vessel, the perfect ease and "
        "promptness with which the parts of a body slide over one another, and the free "
        "and wandering motion which belongs to that which will not keep a form of its own; "
        "and it is the fluidity of water poured from a jug, of milk in a cup, and of air "
        "that fills any room it enters, being the yielding and wandering and shapeless "
        "quality, and it differs from viscosity, which is the thick and clinging hold of "
        "parts upon one another, in being the light and unresisting motion, being the "
        "yielding and shapeless state, and it differs from elasticity, which is the spring "
        "of a body into its former shape, in being the absence of any form to return to, "
        "being the shapeless and wandering state; and it is the fluidity which, once the "
        "form that contains it is changed, is at once a readiness to take the new form and "
        "a patience under every shape, being the yielding and prompt motion; and a thing "
        "shows fluidity when it runs at a touch and takes the figure of the vessel that "
        "holds it, being the ready and shapeless one; and fluidity is thus the state of "
        "being fluid, the ready and yielding and untroubled character of a substance that "
        "takes the shape of its vessel, and the easy sliding of its parts one over another."
    ),
    "ductility": (
        "Ductility is the quality of being ductile, the capacity of a metal or a soft body "
        "to be drawn out into wire or into fine thread without breach, the patient and "
        "obedient stretching of a substance under a long and steady pull, and the "
        "pliant and unbroken yielding of matter to the drawing hand; and it is the "
        "ductility of gold beaten into leaf and drawn into the finest wire, of silver "
        "stretched into threads, and of copper pulled by the smith into a long and even "
        "cord, being the drawn-out and unbroken and obedient quality, and it differs from "
        "malleability, which is the yielding of a body under the hammer, in being the "
        "yielding under the long and drawing pull, being the stretched and unbroken state, "
        "and it differs from brittleness, which is the breaking of a body at a blow, in "
        "being the unbroken and patient stretching, being the yielding and unbroken "
        "quality; and it is the ductility which, under a long and even strain, is at once "
        "a yielding and an endurance, being the pliant and unbroken quality; and a thing "
        "shows ductility when it can be drawn into a long and fine thread without "
        "breaking, being the drawn and unbroken one; and ductility is thus the quality of "
        "being ductile, the capacity of a body to be drawn out into wire or thread without "
        "breach, and the patient and unbroken stretching of a substance under a pull."
    ),
    "brittleness": (
        "Brittleness is the quality of being brittle, the hard and unyielding character of "
        "a substance which, though firm to the touch and stiff against all bending, will "
        "break suddenly at a blow and without warning, the stiffness of matter which gives "
        "way only in a single and final shattering, and the sharp and sudden fracture which "
        "befalls the hard and rigid thing; and it is the brittleness of glass struck upon "
        "the table, of dry and seasoned timber in the frost, and of old iron in the winter "
        "cold, being the hard and sudden and shattering quality, and it differs from "
        "ductility, which is the patient drawing out of a body into wire without breach, "
        "in being the sudden and total breaking instead of the yielding, being the hard "
        "and shattering state, and it differs from elasticity, which is the springing back "
        "of a body into its former figure, in being the unhappy end of all bending, being "
        "the rigid and unreturning state; and it is the brittleness which, the harder and "
        "the stiffer the substance, the more suddenly it fails, being at once a hard "
        "firmness and a fatal weakness; and a thing shows brittleness when it stands stiff "
        "and unyielding until it breaks all at once under a light blow, being the hard and "
        "unforgiving one; and brittleness is thus the quality of being brittle, the hard "
        "and unyielding character of a substance which breaks suddenly at a blow, and the "
        "fracture of the rigid thing."
    ),
    "elasticity": (
        "Elasticity is the quality or the state of being elastic, the spring of a body "
        "which, being stretched or pressed and then released, returns of itself into its "
        "former figure and measure, the lively and recovering force with which matter "
        "resists and then undoes a strain, and the resilience by which a thing remembers "
        "its own shape; and it is the elasticity of a bow bent and then loosed, of a "
        "rubber ball thrown against a wall, and of steel drawn back into its own form "
        "again, being the recovering and springing and undoing quality, and it differs "
        "from fluidity, which is the yielding of a body to every shape without any "
        "return, in being the yielding that is followed by a return, being the springing "
        "and recovering state, and it differs from brittleness, which is a sudden and "
        "unforgiving break under strain, in being the patient bending and the comely "
        "return, being the springing and unbroken state; and it is the elasticity which, "
        "whether of a bent bow or of a pressed spring, is at once a yielding and a "
        "recovering, being the springing and returning quality; and a thing shows "
        "elasticity when it bends under a light force and springs back "
        "when the force is gone, being the springing and returning one; and elasticity is "
        "thus the quality of being elastic, the spring of a body which returns into its "
        "former figure after a strain, and the recovering force which undoes the"
        " bend and the press."
    ),
}

TOPIC_TEST = [
    ("viscosity", ("viscosity", "thick and slow", "slow-flowing", "thick liquid", "sticky and thick", "viscous fluid")),
    ("fluidity", ("fluidity", "ready flowing", "takes the shape", "flows freely", "fluid state", "shapeless flowing")),
    ("ductility", ("ductility", "drawn into wire", "stretched into thread", "ductile metal", "drawn out thin", "yielding under pull")),
    ("brittleness", ("brittleness", "breaks suddenly", "brittle glass", "snaps at a blow", "hard and brittle", "sudden break")),
    ("elasticity", ("elasticity", "springs back", "returns to shape", "elastic body", "bends and recovers", "springing back")),
]
