# -*- coding: utf-8 -*-
"""Mirro English KB — базовый английский режим.

Распознаёт англоязычный вопрос (подавляющее большинство букв — латиница,
есть англ. стоп-слово) и отвечает из мини-справочника базовых понятий
(нейросеть, алгоритм, память, граф, ДНК и т.п.) на английском.
Если понятия нет в справочнике — отвечает нейтральной фразой-переходом.

Чистый Python, атомарные функции (одни return), по LINTER.md.
"""
import re as _re

# мини-справочник: английский вопрос -> связный английский ответ
_EN_KB = {
    "neural": ("Neural networks learn by adjusting weights through training. "
               "A simple one, a perceptron, sums weighted inputs and passes them "
               "through an activation function. Training uses the error to tune weights."),
    "algorithm": ("An algorithm is a step-by-step procedure that solves a task. "
                  "For example, sorting can be done with bubble sort or merge sort. "
                  "Algorithms differ in speed and memory use."),
    "memory": ("Memory is the ability to store and reproduce information. In a "
               "computer it is RAM and disk; in the brain it is patterns of "
               "strengthened connections between neurons."),
    "graph": ("A graph is a set of nodes connected by edges. It models networks, "
              "paths, relations. Key ideas: connectivity, centrality, shortest path."),
    "dna": ("DNA is the molecule that stores hereditary information. Genes are "
            "sections of DNA that code for traits. DNA passes from parents to children."),
    "gravity": ("Gravity is the attraction between objects with mass. Earth pulls "
                "things down; heavier objects attract more strongly. It keeps planets "
                "in orbit and shapes the universe."),
    "cell": ("A cell is the basic unit of life. It has a membrane, nucleus and "
             "cytoplasm. Cells divide to grow and repair an organism."),
    "photon": ("A photon is a quantum of light, a particle of electromagnetic "
               "radiation. It carries energy proportional to its frequency."),
    "pyramid": ("A pyramid is a structure with a square base and triangular sides. "
                "The Egyptian pyramids are ancient tombs made of stone."),
    "internet": ("The internet is a global network connecting computers. Data moves "
                 "in packets routed by protocols like TCP/IP between connected devices."),
    "energy": ("Energy is the ability to do work. It can be kinetic (motion), "
               "potential (stored), thermal, electrical. Energy is conserved — it "
               "changes form but is never lost."),
    "database": ("A database stores data in an organized way and lets you retrieve "
                 "it quickly. Tables hold records; SQL queries read and update them. "
                 "Indexes speed up searches."),
    "robot": ("A robot is a machine that follows programmed instructions to perform "
              "tasks, often in physical space. Robots combine sensors, motors and "
              "control logic. They help in industry, medicine and daily life."),
"bacteria": ("Bacteria are tiny single-celled organisms. Many are harmless or "
                 "helpful (digestion, fermentation), while some cause disease. They "
                 "reproduce by dividing."),
    "ocean": ("The ocean is the vast body of salt water covering most of Earth. "
              "It has currents, tides and layers, and hosts huge marine ecosystems "
              "from coral reefs to deep trenches."),
    "light": ("Light is electromagnetic radiation that travels in waves. It can be "
              "described as photons. Light carries energy and lets us see; its speed "
              "in vacuum is fixed."),
    "genetics": ("Genetics is the study of heredity and how traits pass from parents "
                 "to offspring through genes. DNA carries the instructions; mutations "
                 "and inheritance shape variation."),
    "stem cell": ("Stem cells are unspecialized cells that can develop into different "
                  "cell types. They help repair tissues and are studied for potential "
                  "regenerative therapies."),
    "illness": ("Illnesses are conditions that disrupt normal body function. They can "
                "be infectious (caused by pathogens) or non-infectious (like allergies). "
                "Prevention, hygiene and medicine help manage them."),
    "programming": ("Programming means writing instructions that a computer runs. "
                    "Code in languages like Python is translated so the machine can "
                    "execute it step by step to solve tasks."),
    "voting": ("Voting is how a group makes a decision by letting each member "
               "choose an option. It can be by ballot, show of hands or online; "
               "the most chosen outcome usually wins."),
    "operating system": ("An operating system (OS) manages hardware and programs. "
                         "It handles files, memory and processes. Examples are Linux "
                         "and Windows."),
    "photosynthesis": ("Photosynthesis is how green plants make food from sunlight. "
                       "They take in water and carbon dioxide and, using light energy, "
                       "produce glucose and oxygen."),
    "climate change": ("Climate change is the long-term shift in global temperatures "
                       "and weather patterns. Human activity, mainly burning fossil "
                       "fuels, adds greenhouse gases that warm the planet."),
    "wave": ("A wave is a disturbance that carries energy through a medium or space. "
             "Sound and light travel as waves; their frequency and wavelength "
             "determine pitch and color."),
    "time": ("Time is the continuous progression of events from past to future. "
             "We measure it in seconds, minutes and hours; clocks and calendars "
             "help us organize and compare durations."),
    "biology": ("Biology is the science of living things. It studies cells, "
                "organisms, genetics and ecosystems, from tiny bacteria to "
                "whole environments and how life changes over time."),
    "weather": ("Weather is the short-term state of the atmosphere: temperature, "
                "rain, wind and clouds on a given day. It changes quickly, unlike "
                "climate, which describes long-term trends."),
    "space": ("Space is the region beyond Earth's atmosphere. It holds stars, "
              "planets, galaxies and emptiness. Stars are born, live and die, "
              "and gravity shapes their motion."),
    "history": ("History is the study of the human past through records and "
                "artifacts. It examines events, civilizations and change over "
                "time to understand how societies developed."),
    "literature": ("Literature is written artistic work such as novels, poetry "
                   "and plays. It uses language to express ideas, emotions and "
                   "stories, reflecting culture and imagination."),
    "trade": ("Trade is the exchange of goods and services between people or "
              "countries. It relies on money, transport and markets, and lets "
              "regions specialize in what they produce best."),
    "art": ("Art is the expression of ideas and emotions through visual or "
            "performing forms like painting, sculpture and music. It reflects "
            "culture, creativity and the human experience."),
    "music": ("Music is organized sound made with voice or instruments. Melody, "
              "harmony and rhythm come together in songs and pieces that express "
              "emotion across cultures."),
    "election": ("An election is the process by which people choose a leader or "
                 "representative. Voters cast ballots, results are counted, and "
                 "the candidate with the most support wins the role."),
    "math": ("Math is the study of numbers, shapes and patterns. Arithmetic, "
             "algebra and geometry are its branches. It solves problems with "
             "logical steps and exact rules."),
    "chess": ("Chess is a board game for two players. Each controls sixteen "
              "pieces with different moves; the goal is to checkmate the "
              "opponent's king through strategy and tactics."),
    "geology": ("Geology is the science of the Earth: its rocks, minerals and "
                "layers, and the forces like volcanoes and erosion that shape "
                "its surface over long periods of time."),
    "philosophy": ("Philosophy is the study of fundamental questions about "
                   "existence, knowledge, values and reason. It uses careful "
                   "argument and reflection instead of experiment alone."),
    "sum": ("A sum is the result of adding numbers together. For 3 + 5 the sum "
            "is 8; order does not change it. Sums appear in counting, totals "
            "and averages all across math."),
    "health": ("Health is the state of being physically and mentally well. "
               "Good sleep, nutrition and exercise support it, while illness "
               "and stress can weaken it."),
    "economy": ("Economy is how people produce, trade and use goods and money. "
                "Markets, prices, supply and demand, and national budgets shape "
                "wealth and choices in society."),
    "astronomy": ("Astronomy is the study of everything beyond Earth: stars, "
                  "planets, galaxies and the universe. It uses telescopes and "
                  "physics to understand how celestial objects move and evolve."),
    "botany": ("Botany is the science of plants. It studies leaves, roots and "
               "flowers, how plants grow and make food through photosynthesis, "
               "and their role in ecosystems and food chains."),
    "city": ("A city is a large, densely populated settlement with homes, "
             "businesses and services. People live close together and share "
             "transport, schools, shops and public infrastructure."),
"zoology": ("Zoology is the science of animals. It studies their bodies, "
                 "behavior and habitats, how they adapt and live in groups, "
                 "from tiny insects to large mammals."),
    "country": ("A country is a land with its own government, borders and laws. "
                "People share a common history and culture within it. Countries "
                "trade, cooperate and sometimes compete with each other."),
    "moon": ("The Moon is Earth's natural satellite. It orbits Earth and its "
             "gravity causes tides. Sunlight reflects from it, giving us "
             "phases from new moon to full moon."),
    "magnet": ("A magnet attracts iron and other magnets. It has two poles, "
               "north and south; opposite poles pull together and like poles "
               "push apart. Magnetism powers motors and compasses."),
    "volcano": ("A volcano is an opening in Earth's crust that lets magma, ash "
                "and gases escape. When it erupts, lava flows out and builds new "
                "land; some volcanoes are active, others dormant or extinct."),
    "island": ("An island is a piece of land surrounded by water. It can be big "
               "or small, formed by volcanoes, reefs or rising land. Islands "
               "have unique plants and animals."),
    "skyscraper": ("A skyscraper is a very tall building with many floors. "
                   "Steel frames and elevators let towers rise high in cities, "
                   "packing offices and homes into a small footprint."),
    "desert": ("A desert is a dry region that gets very little rain. It can be "
               "hot or cold, with sand, rock or ice. Plants and animals there "
               "adapt to save water and survive extreme heat or cold."),
    "journey": ("A journey is travel from one place to another. People travel "
                "for work, family or discovery, by foot, road, sea or air. "
                "Journeys can be short trips or long adventures."),
    "river": ("A river is a natural stream of water flowing toward a sea, lake "
              "or another river. It shapes valleys, carries nutrients and "
              "supplies water that people and wildlife depend on."),
    "wheat": ("Wheat is a cereal crop grown for its grain, which is milled into "
              "flour for bread, pasta and many foods. It is one of the most "
              "important crops in the world."),
    "forest": ("A forest is a large area covered with trees and other plants. "
               "It gives oxygen, shelters wildlife and cools the climate. Many "
               "animals and people depend on forests for food and shelter."),
    "lake": ("A lake is a large body of water surrounded by land. It can be "
             "fresh or salty, fed by rivers and rain. Lakes store water, "
             "support wildlife and are used for fishing and recreation."),
    "hill": ("A hill is a raised area of land, lower and gentler than a mountain. "
             "Hills are formed by erosion, glaciers or volcanoes. They give good "
             "views and are common in rolling countryside."),
    "coal": ("Coal is a black, burnable rock formed from ancient plants under "
             "heat and pressure. For centuries it has fuelled power plants and "
             "industry, though it releases carbon dioxide when burned."),
    "meteor": ("A meteor is a streak of light in the sky caused by a small space "
               "rock burning up in Earth's atmosphere. If a piece survives and "
               "lands, it is called a meteorite."),
    "comet": ("A comet is a small icy body from the outer solar system. Near the "
              "Sun, heat turns its ice into gas and dust, forming a bright head "
              "and a long glowing tail."),
    "glacier": ("A glacier is a slow-moving mass of ice formed where snow piles "
                "up and compresses over many years. It flows downhill, carving "
                "valleys and reshaping the landscape as it melts."),
    "plan": ("A plan is an organized set of steps toward a goal. It lists what "
             "to do, when, and how. Good plans are flexible and are updated as "
             "situations change or new information appears."),
    "routine": ("A routine is a regular, repeated way of doing something. Daily "
                "habits like waking, eating and studying form a routine that "
                "saves time and brings stability to life."),
    "upbringing": ("Upbringing is how a child is raised and guided by family. "
                   "It includes values, habits and education learned at home, "
                   "shaping character and how a person deals with the world."),
    "memory": ("Memory is the ability to store and recall information. Working "
               "memory holds what we use now; long-term memory keeps facts and "
               "skills over time. Repetition and rest help strengthen it."),
    "society": ("A society is a group of people living together and sharing "
                "rules, culture and institutions. People cooperate through "
                "laws, work and trade to meet common needs and goals."),
    "souvenir": ("A souvenir is an object kept to remember a place, event or "
                 "person. People buy them while traveling as a reminder of "
                 "experiences or to give as small gifts."),
    "possibility": ("A possibility is something that may happen or be true. "
                    "It is an option or chance among several outcomes. We weigh "
                    "probabilities to decide how likely a possibility is."),
    "dialogue": ("A dialogue is a conversation between two or more people. "
                 "Speakers take turns sharing ideas and questions. Good "
                 "dialogue builds understanding and resolves disagreements."),
    "achievement": ("An achievement is something accomplished through effort or "
                    "skill, like finishing a goal or passing a test. It brings "
                    "a sense of progress and is often recognized by others."),
    "character": ("A character is the set of qualities that define how a person "
                  "thinks, feels and acts. Honesty, patience and courage are "
                  "parts of it; character is shaped by choices and experience."),
    "priority": ("A priority is what matters most and should be done first. "
                 "When resources or time are limited, priority helps decide "
                 "the order of tasks and where to focus attention."),
    "reaction": ("A reaction is a response to an event, word or change. In "
                 "chemistry it is a process where substances change into others. "
                 "In life, a reaction shows how someone feels or acts."),
    "horizon": ("The horizon is the line where the sky seems to meet the ground "
                "or sea. It is an apparent edge created by the curvature of the "
                "Earth, and it shifts as the viewer moves or height changes."),
    "scales": ("Scales are tools or systems for measuring or weighing. A balance "
               "compares masses; rating scales order opinions or sizes. In music "
               "and in charts, scales set the steps between values."),
    "treasure": ("Treasure is a collection of valuable things, such as gold, gems "
                 "or precious objects. It can be buried, found or inherited, and "
                 "it holds worth to both its owners and historians."),
    "motion": ("Motion is the change in position of an object over time. Speed "
               "and direction describe it; acceleration changes motion. Forces "
               "like gravity and push cause objects to start, stop or turn."),
    "task": ("A task is a piece of work to be done, with a clear goal or outcome. "
             "Tasks can be small or large, personal or shared. Breaking work "
             "into tasks makes big jobs easier to manage."),
    "machinery": ("Machinery is a set of machines that do work using power. "
                  "It can include engines, tools and equipment in factories or "
                  "farms. Machines multiply human strength and speed up tasks."),
    "orbit": ("An orbit is the curved path an object takes around another in space. "
              "Planets orbit stars and moons orbit planets, held by gravity. "
              "Orbits can be round or oval and take different amounts of time."),
    "repair": ("A repair is the act of fixing something that is broken or worn. "
               "It may be done by replacing parts, joining pieces or tuning "
               "settings. Repairing saves resources and extends what we use."),
    "process": ("A process is a series of steps that turn inputs into a result. "
                "Workflows, chemical reactions and learning are all processes. "
                "Understanding each step helps improve speed and quality."),
    "packet": ("A packet is a unit of data sent over a network. Messages are "
               "split into packets that travel through routers and are reordered "
               "at the destination. This makes transfer reliable and efficient."),
    "evidence": ("Evidence is information that supports a claim or conclusion. "
                 "It can be facts, data, observations or documents. Strong "
                 "evidence helps people judge what is true and decide wisely."),
"complaint": ("A complaint is when someone says they are unhappy with a "
                   "product, service or situation. It raises a problem so it can "
                   "be examined and fixed. Fair complaints lead to improvements."),
    "comfort": ("Comfort is a pleasant feeling of ease and well-being. It comes "
                "from cozy places, kind words or safety. Comfort helps people "
                "relax, recover and feel at home in a situation."),
    "correction": ("A correction is a change that fixes a mistake or error. It "
                   "can apply to writing, data, behavior or a course of action. "
                   "Making corrections improves accuracy and helps prevent future "
                   "errors."),
    "perception": ("Perception is how we take in and interpret the world through "
                   "the senses. Sight, hearing and touch give signals that the "
                   "brain turns into meaning; you can be active literal or "
                   "shaped by experience."),
    "universe": ("The universe is everything that exists: all matter, energy, "
                 "space and time. It holds galaxies, stars and planets and has "
                 "been expanding since the Big Bang about 14 billion years ago."),
    "skill": ("A skill is an ability to do something well, learned through "
              "practice and experience. It can be practical, social or mental. "
              "Skills grow with training and open doors to new tasks and jobs."),
    "migration": ("Migration is the movement of people or animals from one place "
                  "to another. People migrate for work, safety or family; birds "
                  "and fish migrate with seasons to find food and climate."),
    "belonging": ("Belonging is the feeling of being accepted and connected to a "
                  "group, place or community. It comes from shared identity and "
                  "trust, and it gives people a sense of security and purpose."),
    "balance": ("Balance is the state of being steady and even. A scale balances "
                "weights, and our bodies balance while we walk. In life, balance "
                "means giving time and energy to different needs fairly."),
    "contrast": ("Contrast is the difference between two things, ideas or colors. "
                 "It makes them easier to tell apart and highlights their features. "
                 "Contrast is used in design, in writing and in comparing choices."),
    "torque": ("Torque is a rotational force that makes an object spin. It equals "
               "force multiplied by the distance from the pivot. Torque turns "
               "wheels, tightens bolts and powers many machines."),
    "questionnaire": ("A questionnaire is a set of written questions used to "
                      "collect information from people. It can be on paper or "
                      "online, with closed or open answers. Analysis of replies "
                      "helps research and decision-making."),
    "manual": ("A manual is a book or guide that explains how to use or fix "
               "something. It gives step-by-step instructions, warnings and "
               "tips. Manuals help both beginners and experts work correctly."),
    "echo": ("An echo is a reflected sound that returns after hitting a surface. "
             "Hearing it depends on distance and time; echoes help ships measure "
             "depth and bats navigate in the dark. They reveal the shape around us."),
    "fermentation": ("Fermentation is a natural process where microorganisms break "
                     "down sugars into alcohol, gases or acids. It preserves food, "
                     "adds flavor and is used to make bread, yogurt and beer."),
    "recipe": ("A recipe is a set of instructions for preparing a dish or drink. "
               "It lists ingredients, amounts and steps in order. Following a "
               "recipe carefully helps get a consistent, tasty result."),
    "breeze": ("A breeze is a gentle wind, softer than a gale. It moves leaves, "
               "spreads smells and cools the air on warm days. Breezes can be "
               "steady and light or come in short gusts."),
    "storm": ("A storm is a violent weather event with strong winds, rain, snow "
              "or thunder. It can bring lightning and flooding. Storms form when "
              "warm and cold air meet; they vary from mild to severe."),
    "cactus": ("A cactus is a plant adapted to dry deserts. Its thick stem stores "
               "water, and spines reduce water loss and guard it from animals. "
               "Cacti flower and some live for many decades."),
    "dawn": ("Dawn is the time of day when the sky grows light before sunrise. "
             "It comes with soft colors and quiet calm. Dawn marks the beginning "
             "of a new day and the start of daily routines."),
    "contradiction": ("A contradiction happens when two statements cannot both be "
                      "true at the same time. Spotting contradictions helps find "
                      "errors in logic and forces us to rethink ideas."),
    "vacuum": ("A vacuum is a space with very little or no matter inside. Sound "
               "cannot travel through a perfect vacuum, and objects fall freely "
               "in it. Vacuums are used in bulbs, packaging and scientific tools."),
    "silence": ("Silence is the absence of sound or noise. It can bring calm and "
                "focus, or it can feel awkward in conversation. In music, rests "
                "and quiet pauses shape rhythm and mood just like the notes do."),
    "ambition": ("Ambition is a strong wish to achieve something important or "
                 "to improve in life. It gives direction and energy for hard "
                 "work. Used well, ambition pushes people to grow and succeed."),
    "courage": ("Courage is the ability to face danger, difficulty or fear with "
                "resolve. It is not the absence of fear but acting despite it. "
                "Acts of courage, large and small, build confidence and respect."),
    "winner": ("A winner is the person or team that comes first in a contest or "
               "achieves a goal. Winning often follows effort and preparation. "
               "A good winner shows respect and uses success to inspire others."),
    "humanity": ("Humanity refers to all people as a whole, and to the qualities "
                 "that make us kind and caring, such as empathy and compassion. "
                 "It also names the study and care of people's welfare and rights."),
    "diligence": ("Diligence is steady and careful effort in work or study. It "
                  "means paying attention to details and not giving up easily. "
                  "Diligent people build trust and often reach results with care."),
    "symmetry": ("Symmetry is balance in shape or structure, where parts mirror "
                 "each other around a line or point. It appears in nature, art "
                 "and geometry, and often makes things look balanced and orderly."),
    "law": ("Law is a system of rules that governments make and enforce. It "
            "keeps order, protects rights and settles disputes fairly. Laws "
            "apply to everyone and can be changed through proper process."),
    "pneumatics": ("Pneumatics is the use of compressed air to do work. "
                   "Air-driven tools and brakes use pressure stored in tanks. "
                   "Pneumatic systems are clean, simple and common in industry."),
    "equilibrium": ("Equilibrium is a state of balance where forces or factors "
                    "cancel each other out. A market, a body or a chemical system "
                    "can be in equilibrium when opposing influences are equal."),
    "prosperity": ("Prosperity is a state of being successful and having plenty, "
                   "especially in wealth or well-being. It comes from growth, "
                   "opportunity and good health. Prosperity can be personal or "
                   "shared across a whole society."),
    "resilience": ("Resilience is the ability to recover quickly from hard times "
                   "or setbacks. It involves staying flexible and positive under "
                   "pressure. Resilient people adapt, learn and keep going."),
    "humility": ("Humility is a modest view of one's own importance. It means "
                 "being open to feedback and not seeing yourself as better than "
                 "others. Humble people listen, learn and stay approachable."),
    "gratitude": ("Gratitude is the feeling of being thankful for what you have. "
                  "It focuses attention on the good things in life, from small "
                  "kindness to big support. Practicing it lifts mood and bonds."),
    "curiosity": ("Curiosity is a strong desire to learn or know more about "
                  "the world. It drives questions, exploration and discovery. "
                  "Curious minds stay open to new ideas and grow faster."),
    "patience": ("Patience is the capacity to stay calm while waiting or dealing "
                 "with delay and difficulty. It helps keep focus and avoid rash "
                 "reactions. Patient people persevere and reach long-term goals."),
    "kindness": ("Kindness is a quality of being friendly, generous and considerate. "
                 "It shows in small acts of care and in how we treat others. "
                 "Kindness builds trust and makes communities stronger."),
    "determination": ("Determination is the firm resolve to keep pursuing a goal "
                      "despite obstacles and setbacks. It fuels effort and "
                      "persistence. Determined people turn plans into results."),
    "optimism": ("Optimism is a hopeful outlook that focuses on good possibilities "
                 "and positive outcomes. It supports motivation during hard times. "
                 "Optimistic people tend to cope better and try more often."),
    "freedom": ("Freedom is the state of being able to act, think and choose "
                "without unfair limits. It comes with responsibility for your "
                "choices. Freedom is a base for creativity and dignity."),
    "endurance": ("Endurance is the strength to keep going through difficult or "
                  "prolonged effort. It blends physical stamina with mental "
                  "resolve. Enduring effort is what makes long battles winnable."),
    "serenity": ("Serenity is a state of calmness and peace of mind. It comes from "
                 "accepting what you cannot change and letting go of inner turmoil. "
                 "Serene people stay balanced in the middle of stress."),
    "humor": ("Humor is the ability to see and express the funny side of life. "
              "It lightens hard moments and helps people connect. Humor builds "
              "warmth and makes even serious talks feel human."),
    "integrity": ("Integrity is the quality of being honest and having strong moral "
                  "principles. It means doing the right thing even when nobody "
                  "watches. Integrity earns lasting trust and respect."),
    "generosity": ("Generosity is the willingness to give time, money or kindness "
                   "freely. It grows out of caring for others, not obligation. "
                   "Giving generously builds connection and shared joy."),
    "grit": ("Grit is the mix of passion and perseverance toward long-term goals. "
             "It is about steady effort over months and years, not just talent. "
             "Gritty people finish what they start and improve over time."),
    "prudence": ("Prudence is the careful use of good judgment before acting. "
                 "It weighs risks and consequences instead of rushing in. "
                 "Prudent choices protect your health, money and relationships."),
    "courtesy": ("Courtesy is polite and considerate behavior toward other people. "
                 "It is shown in small gestures like greeting, thanking and waiting "
                 "your turn. Courtesy makes daily life smoother and kinder."),
    "forgiveness": ("Forgiveness is the act of letting go of anger and resentment "
                    "toward someone who wronged you. It heals both sides and frees "
                    "the forgiver from a heavy emotional burden."),
    "bravery": ("Bravery is the courage to face danger, pain or fear without giving "
                "up. It is not the absence of fear but acting despite it. Brave "
                "deeds protect others and grow inner strength."),
    "compassion": ("Compassion is awareness of others' suffering together with the "
                   "wish to relieve it. It moves a person from feeling to action. "
                   "Compassion connects people and eases pain in the world."),
    "altruism": ("Altruism is selfless concern for the welfare of others. It is "
                 "acting to help someone without expecting anything in return. "
                 "Altruistic deeds make society more humane and connected."),
    "tact": ("Tact is the skill of saying the right thing at the right time so as "
             "not to offend. It blends honesty with kindness and awareness. Tactful "
             "people give feedback that helps instead of hurting."),
    "forbearance": ("Forbearance is patient self-control in the face of annoyance "
                    "or provocation. It means holding back anger and giving second "
                    "chances. Forbearing people keep peace and stay fair under stress."),
    "resoluteness": ("Resoluteness is firmness of purpose and decisiveness in action. "
                     "It is the quiet determination behind a clear decision. Resolute "
                     "people do not waver once they have set a course."),
    "compromise": ("A compromise is an agreement made by mutual adjustment, where "
                   "each side gives up something to reach a shared goal. It takes "
                   "seeing the other view and seeking a fair middle ground."),
    "equanimity": ("Equanimity is calmness and composure, especially in difficult "
                   "situations. It means keeping a steady mind whether you win or "
                   "lose. Equanimity protects wisdom from being swept by emotion."),
    "conscientiousness": ("Conscientiousness is the trait of being careful, thorough "
                          "and responsible in your duties. It means doing things well "
                          "and on time, not just quickly. Conscientious people are "
                          "dependable and take pride in their work."),
    "discipline": ("Discipline is the practice of training yourself to follow rules "
                   "or a code of conduct consistently. It turns good intentions into "
                   "steady habits. Discipline is the bridge between goals and results."),
    "diligence": ("Diligence is steady and earnest effort in one's work or duties. "
                  "It means applying constant care and attention over time. Diligent "
                  "workers produce quality and earn trust through reliability."),
    "mercy": ("Mercy is compassion shown toward someone who has power over you or "
              "who has done wrong. It means choosing kindness over punishment when "
              "you have the right to be harsh. Mercy restores dignity and offers a "
              "second chance."),
    "fervour": ("Fervour is intense and passionate enthusiasm for a cause, idea or "
                "belief. It comes from deep conviction rather than surface emotion. "
                "Fervour energizes people and drives them to act boldly."),
    "zest": ("Zest is a vigorous, eager enjoyment of life and activity. It is the "
             "energetic curiosity that turns ordinary moments into adventures. People "
             "with zest meet each day with energy and involvement."),
    "mettle": ("Mettle is strength of character and the courage to keep going under "
               "pressure. It is what is revealed when a person is tested by hardship. "
               "Mettle shows true character in difficult circumstances."),
    "vigilance": ("Vigilance is careful watchfulness for possible dangers or errors. "
                  "It means staying alert and attentive over long periods. Vigilant "
                  "people notice problems early and prevent small issues from growing."),
    "hope": ("Hope is the belief that a desired outcome is possible in the future. "
             "It lets people endure hardship and keep striving despite difficulties. "
             "Hope fuels motivation and opens the door to real change."),
    "fortitude": ("Fortitude is mental and emotional strength in facing difficulty "
                  "or adversity. It is the courage to endure pain without complaint. "
                  "Fortitude helps people carry on when everything else is heavy."),
    "magnanimity": ("Magnanimity is the quality of being generous in spirit, especially "
                    "toward rivals or those who have wronged you. It is nobility of mind "
                    "that lets a person act with grace instead of revenge. Magnanimous "
                    "people rise above petty grievances."),
    "insight": ("Insight is the deep and clear understanding of the nature of things. "
                "It is seeing connections that are not obvious at first. Insight comes "
                "from reflection and experience, and it often leads to smart decisions."),
    "lenity": ("Lenity is the quality of being gentle and merciful in judgment. It is "
               "the mildness that avoids harsh punishment when it is not needed. Lenity "
               "corrects with care and tempering, without cruelty."),
    "tenacity": ("Tenacity is the quality of holding firmly to a course of action or "
                 "belief. It means refusing to give up even when success seems slow or "
                 "far away. Tenacious people keep trying long after others have stopped."),
    "prowess": ("Prowess is great skill or ability, especially in battle or in one's "
                "chosen field of endeavor. It is the excellence that comes from talent "
                "combined with hard practice. Prowess wins respect and opens doors to "
                "hard-won achievement."),
    "pride": ("Pride is the sense of satisfaction and dignity that comes from your own "
              "achievements or from a group you belong to. When balanced, it builds "
              "self-respect; when excessive, it can blind a person to their faults. "
              "Right pride respects others and stays grounded."),
"modesty": ("Modesty is a humble estimate of one's own importance and worth. It is "
                 "the opposite of showing off or demanding attention. Modest people let "
                 "their actions speak rather than their words, and remain teachable."),
    "sagacity": ("Sagacity is the quality of being wise, keen and judicious in judgment. "
                 "It comes from experience, learning and a sharp perception of detail. "
                 "Sagacious people see through appearances to the heart of a matter."),
    "resolution": ("Resolution is the firmness and steadfastness of intent to see a thing "
                    "through. It is the inner decision that turns a wish into a vow to act. "
                    "People of resolution do not abandon their aim at the first obstacle; "
                    "they carry their purpose to completion."),
    "promise": ("A promise is a declaration that one will or will not do something. "
                "Keeping a promise builds trust and shows that your word can be relied "
                "upon. Broken promises, by contrast, break relationships and reputations. "
                "The keeping of promises is the foundation of honor and accountability."),
    "sentiment": ("Sentiment is a view or attitude shaped by emotion rather than reason "
                  "alone. It is the feeling that colors how a person sees a situation or "
                  "person. Healthy sentiment enriches life, while unchecked sentiment can "
                  "cloud judgment, so wisdom seeks a fair balance between the heart and "
                  "the head."),
    "chivalry": ("Chivalry is the medieval code of honor that expected knights to be "
                 "brave, courteous and loyal and to defend the weak. In a broader sense, "
                 "it means generous and polite behavior, especially toward those in need. "
                 "True chivalry pairs strength with gentleness and duty with honor."),
    "savvy": ("Savvy is practical intelligence and shrewd understanding of how to get "
              "things done, especially in business or daily dealings. It is street-smart "
              "know-how rather than book learning alone. Savvy people read situations "
              "quickly and find workable solutions where others are stuck."),
    "equity": ("Equity is the quality of being fair and impartial, giving everyone what "
               "is justly their due rather than treating everyone exactly the same. It "
               "recognizes that different situations may need different treatment to reach "
               "an equal outcome. Equity anchors society in justice and mutual respect."),
    "staunchness": ("Staunchness is the quality of being loyal, committed and reliable, "
                    "especially in the face of difficulty or opposition. It is a steadfast "
                    "allegiance to a person, cause or belief that does not waver easily. "
                    "Staunch friends and allies remain true when it is costly to do so."),
"acumen": ("Acumen is the ability to make good judgments and quick, accurate decisions, "
              "especially in practical or business matters. It is refined through experience "
              "and observation rather than formal study alone. Those with acumen spot "
              "opportunities and pitfalls that others overlook, and act on them decisively."),
    "merit": ("Merit is the quality of being deserving reward or praise based on one's "
              "actions, skills or achievements. It is what makes a person worthy of "
              "recognition, promotion or reward. A system that honors merit encourages "
              "effort, talent and honest work over favoritism or chance."),
    "sapience": ("Sapience is the quality of being wise, with deep understanding and good "
                 "judgment applied to real life. Whereas knowledge is information, sapience "
                 "is the wisdom that knows how to use it well. A sapient person grasps the "
                 "bigger picture and offers counsel that stands the test of time."),
    "tolerance": ("Tolerance is the willingness to accept and respect the beliefs, practices "
                  "or behaviors of others even when they differ from your own. It does not "
                  "mean agreeing with everything, but it means coexisting peacefully and "
                  "granting everyone room to live by their convictions. Tolerance is essential "
                  "to any free and diverse society."),
    "dependability": ("Dependability is the quality of being reliable and trustworthy in "
                      "what you say and do. A dependable person keeps promises, meets deadlines "
                      "and can be counted on in a crisis. Dependability is built slowly through "
                      "consistent action and is quickly lost through a single act of betrayal."),
    "reliability": ("Reliability is the quality of consistently delivering what is expected over "
                    "time. It is the technical cousin of trustworthiness, applied to machines and "
                    "systems as much as to people. A reliable engine, report or colleague performs "
                    "the same way on the tenth use as on the first, giving others a foundation to "
                    "build upon without fear of sudden failure."),
    "sublimity": ("Sublimity is the quality of being so grand, beautiful or inspiring that it "
                  "overwhelms the senses and lifts the spirit. It is found in great natural views, "
                  "in profound art and in acts of extraordinary courage. Encountering the sublime "
                  "reminds us how small we are, but also how much greatness we are capable of."),
    "heroism": ("Heroism is the display of exceptional courage and selflessness in the face of "
                "danger or adversity. It is measured not by strength alone but by acting for the "
                "good of others at personal risk. Heroes rise to occasions that demand more than "
                "self-interest, and their deeds inspire courage in those who witness them."),
    "forthrightness": ("Forthrightness is the quality of speaking and acting directly and honestly "
                       "without evasion or pretense. A forthright person says what they mean in a "
                       "clear and straightforward way, even when the message is uncomfortable. This "
                       "honesty wins trust, saves time and prevents the confusion that comes from "
                       "hidden agendas."),
    "munificence": ("Munificence is great generosity, shown in giving money, gifts or aid on a "
                    "lavish scale. It goes beyond ordinary kindness by being remarkably bountiful. "
                    "A munificent patron or donor gives without hoarding, using wealth to elevate "
                    "others and to fund works that benefit the public good."),
    "prosperity": ("Prosperity is the state of being financially successful, thriving and in good "
                   "health. It is more than mere wealth; it includes a sense of well-being, security "
                   "and abundance in one's life. Prosperity can be personal, communal or national, and "
                   "it is sustained by sound habits, honest work and wise management of resources."),
    "devotion": ("Devotion is the quality of being ardently loyal to a person, cause or religious "
                 "faith. It goes beyond duty into wholehearted dedication of heart and mind. Devotion "
                 "shows itself in consistent acts of service, faithfulness over time and a genuine love "
                 "for what one serves. It is the emotional bedrock of true commitment."),
    "steadfastness": ("Steadfastness is the quality of being firm and unshakable in purpose, belief or "
                      "loyalty. A steadfast person does not give way under pressure, temptation or doubt. "
                      "It is the discipline that keeps a commitment alive when it would be easier to walk "
                      "away, and it is what makes promises trustworthy and character reliable."),
    "heedfulness": ("Heedfulness is the quality of paying careful and constant attention to what one is "
                    "doing or to the needs of others. A heedful person notices what most people miss and "
                    "acts with care rather than haste. It is the attentive alertness that prevents mistakes, "
                    "avoids accidents and helps one respond properly to the needs of the moment."),
    "dutifulness": ("Dutifulness is the quality of fulfilling one's obligations and responsibilities with "
                    "reliability and respect. A dutiful person does what is required without complaint, out "
                    "of a sense of duty toward family, work or society. It is not glamorous, but it is the "
                    "quiet engine that keeps families, institutions and communities functioning."),
    "confidence": ("Confidence is trust in one's own abilities, judgment or powers and the courage that grows "
                   "from that trust. It is not arrogance, which dismisses others, but a calm self-assurance "
                   "that comes from competence and preparation. Confident people try new things, speak their "
                   "mind and recover quickly from failure, because they believe in themselves and their goals."),
}

# англ. стоп-слова, чтобы не срабатывать на русских вопросах с латиницей (код и т.п.)
_EN_COMMON = ("what", "which", "how", "why", "who", "when", "where", "is", "are",
              "the", "a", "an", "of", "in", "on", "to", "for", "i", "you", "explain",
              "tell", "about", "that", "do", "does", "can", "please", "me", "my",
              "than", "there", "your", "it", "also", "not", "could", "would",
              "should", "know", "want", "what's", "how's", "define", "mean",
              "actually", "basically", "rather", "however", "maybe", "perhaps",
              "still", "though", "well", "since", "because", "before", "after",
              "always", "usually", "often", "sometimes", "many", "much",
              "with", "from", "over", "under", "between", "without", "into", "off")


_EN_MARKER_SET = frozenset(_EN_COMMON)

# тема -> ключевые англ. слова (основа)
_TOPIC_TEST = [
    ("neural", ("neural", "network", "perceptron", "machine learn", "deep learn", "neuron", "gradient", "backprop")),
    ("algorithm", ("algorithm", "sort", "complexity", "procedure", "bubble", "search", "data structure")),
    ("memory", ("memory", "remember", "recall", "store info")),
    ("graph", ("graph", "node", "edge", "vertex", "connected")),
    ("dna", ("dna", "gene", "genetic", "heredit")),
    ("gravity", ("gravity", "gravitation", "fall", "attraction", "orbit")),
    ("cell", ("cell", "cell division", "organ", "nucleus", "tissue")),
    ("photon", ("photon", "light quantum", "electromagnetic")),
    ("pyramid", ("pyramid", "clamp", "tomb", "sphinx")),
    ("internet", ("internet", "web", "http", "network", "protocol")),
    ("energy", ("energy", "work", "kinetic", "potential", "electric", "power")),
    ("database", ("database", "table", "sql", "query", "record", "index")),
    ("robot", ("robot", "machine", "automation", "automaton", "mechatronic")),
    ("bacteria", ("bacteria", "microbe", "microorganism", "germ", "single-celled")),
    ("light", ("light", "photon", "electromagnetic radiation", "optics", "wavelength")),
    ("psychology", ("psychology", "mind", "behavior", "behaviour", "brain", "cognition")),
    ("genetics", ("genetics", "gene", "heredity", "dna", "inheritance", "chromosome")),
    ("stem cell", ("stem cell", "stem cells", "regenerative", "unspecialized")),
    ("illness", ("illness", "disease", "infection", "disorder", "allergy")),
    ("programming", ("programming", "code", "program", "python", "compiler", "source")),
    ("operating system", ("operating system", "os", "kernel", "linux", "windows", "files")),
    ("photosynthesis", ("photosynthesis", "chlorophyll", "glucose", "oxygen", "plants")),
    ("climate change", ("climate change", "global warming", "greenhouse", "carbon dioxide", "emissions")),
    ("wave", ("wave", "sound", "frequency", "amplitude", "wavelength")),
    ("biology", ("biology", "organism", "species", "ecosystem", "living")),
    ("weather", ("weather", "rain", "wind", "temperature", "forecast", "climate")),
    ("space", ("space", "star", "galaxy", "planet", "universe", "orbit")),
    ("history", ("history", "ancient", "civilization", "empire", "medieval", "era")),
    ("literature", ("literature", "novel", "poem", "poetry", "author", "genre")),
    ("art", ("art", "painting", "sculpture", "music", "artist", "canvas", "color")),
    ("music", ("music", "melody", "harmony", "rhythm", "song", "instrument", "guitar")),
    ("math", ("math", "algebra", "arithmetic", "geometry", "fraction", "equation")),
    ("chess", ("chess", "checkmate", "rook", "queen", "knight", "pawn", "board")),
    ("geology", ("geology", "rock", "mineral", "mantle", "crust", "volcano", "erosion")),
    ("philosophy", ("philosophy", "ethics", "logic", "existence", "knowledge", "reason")),
    ("health", ("health", "nutrition", "exercise", "sleep", "wellness", "immune")),
    ("economy", ("economy", "market", "money", "inflation", "trade", "budget", "price")),
    ("astronomy", ("astronomy", "planet", "star", "galaxy", "nebula", "telescope", "comet")),
    ("botany", ("botany", "plant", "leaf", "root", "flower", "photosynthesis", "tree")),
    ("zoology", ("zoology", "animal", "mammal", "insect", "bird", "habitat", "reptile")),
    ("mercy", ("mercy", "forgive", "compassion", "spare", "pardon")),
    ("mettle", ("mettle", "courage", "resolve", "stamina", "fortitude")),
    ("vigilance", ("vigilance", "alert", "watchful", "vigilant", "attentive")),
    ("discipline", ("discipline", "self-control", "training", "habit", "consistent")),
    ("diligence", ("diligence", "careful", "earnest", "thorough", "persistent")),
    ("kindness", ("kindness", "gentle", "friendly", "considerate", "warm")),
    ("honesty", ("honesty", "truth", "truthful", "sincere", "candid", "upright")),
    ("hope", ("hope", "faith", "optimism", "expectation", "positive")),
    ("fortitude", ("fortitude", "strength", "endurance", "courage under", "brave heart")),
    ("magnanimity", ("magnanimity", "generous spirit", "noble", "forgiving", "high-minded")),
    ("insight", ("insight", "understanding", "discernment", "deep perception", "clear seeing")),
    ("lenity", ("lenity", "gentle", "mild", "merciful", "tender", "forgiving heart")),
    ("tenacity", ("tenacity", "persevere", "persistent", "stubborn", "determined", "unrelenting")),
    ("prowess", ("prowess", "skillful", "adept", "masterful", "expert", "dexterous")),
    ("compassion", ("compassion", "sympathy", "kindness toward", "care for", "empathy")),
    ("generosity", ("generosity", "giving", "bountiful", "liberal", "open-handed")),
    ("grit", ("grit", "perseverance", "passion", "long-term goal", "hardy")),
    ("patience", ("patience", "calm", "wait calmly", "long-suffering", "even-tempered")),
    ("bravery", ("bravery", "courageous", "fearless", "bold", "heroic", "intrepid")),
    ("temperance", ("temperance", "moderation", "restraint", "self-control", "balanced")),
    ("pride", ("pride", "self-esteem", "dignity", "self-respect", "satisfaction")),
    ("modesty", ("modesty", "humble", "unassuming", "quiet", "down-to-earth", "reserved")),
    ("sagacity", ("sagacity", "wise", "judicious", "perceptive", "shrewd", "discerning")),
    ("resolution", ("resolution", "determination", "firmness", "resolve", "steadfastness", "conclusive")),
    ("promise", ("promise", "vow", "pledge", "word of honor", "commitment", "engagement")),
    ("sentiment", ("sentiment", "feeling", "attitude", "emotion", "inclination", "mood")),
    ("chivalry", ("chivalry", "gallant", "courteous", "honorable", "knightly", "noble conduct")),
    ("savvy", ("savvy", "shrewd", "street-smart", "practical", "business-smooth", "astute")),
    ("equity", ("equity", "fairness", "impartial", "justice", "even-handed", "righteous")),
    ("staunchness", ("staunchness", "loyal", "steadfast", "committed", "reliable", "unwavering")),
    ("acumen", ("acumen", "insightful", "keen judgment", "sharp-witted", "perceptive", "shrewd mind")),
    ("merit", ("merit", "deserving", "worthiness", "excellence", "distinction", "credit")),
    ("sapience", ("sapience", "wisdom", "insightful judgment", "profound understanding", "wise counsel")),
    ("tolerance", ("tolerance", "acceptance", "open-minded", "permitting", "broad-minded", "indulgent")),
    ("dependability", ("dependability", "reliable", "trustworthy", "dependable", "responsible", "consistent")),
    ("reliability", ("reliability", "dependable", "consistent", "predictable", "steady", "uniform")),
    ("sublimity", ("sublimity", "grandeur", "exalted", "lofty", "awe-inspiring", "majestic")),
    ("heroism", ("heroism", "heroic", "courageous act", "selfless", "gallantry", "valor")),
    ("forthrightness", ("forthrightness", "direct", "candid", "honest speech", "blunt", "straightforward")),
    ("munificence", ("munificence", "lavish generosity", "bountiful", "open-handed", "largess", "generous giving")),
    ("prosperity", ("prosperity", "flourishing", "thriving", "successful", "affluent", "well-off")),
    ("devotion", ("devotion", "dedicated", "committed to", "faithful", "loyal service", "wholehearted")),
    ("steadfastness", ("steadfastness", "unshakable", "firm in purpose", "immovable", "constant", "unwavering")),
    ("heedfulness", ("heedfulness", "attentive", "watchful care", "mindful", "alert attention", "careful observance")),
    ("dutifulness", ("dutifulness", "obedient to duty", "responsible", "conscientious", "compliant", "respectful of duty")),
    ("confidence", ("confidence", "self-assured", "assertive", "certain of oneself", "self-belief", "trust in abilities")),
]


def _is_english_query(q):
    """Похож ли вопрос на английский. Минимальная длина латиницы — 6 символов
    (чтобы одиночные «what?/hi» не срабатывали). Не-строка → False.
    Один return: bool."""
    if not isinstance(q, str):
        return False
    q = (q or "").strip()
    if not q:
        return False
    latin = sum(1 for c in q if 'a' <= c.lower() <= 'z')
    cyr = sum(1 for c in q if '\u0400' <= c <= '\u04FF')
    words = q.split()
    # англ-вопрос: заметная доля латиницы (>=6), нет кириллицы, есть англ. маркер.
    # Одиночное «what?/hi» игнорируются (нет латинских слов повсюду ≥4)
    has_full_word = any(len(w) >= 4 for w in words if w.isalpha())
    enough_latin = latin >= 6 and has_full_word
    # англ. маркер должен быть отдельным словом, а не частью большего
    # (снимаем хвостовую пунктуацию, чтобы «why?» матчилось как «why»)
    toks = {w.strip(".,!?;:'\"()") for w in q.lower().split()}
    has_marker = bool(toks & _EN_MARKER_SET)
    return (enough_latin and cyr == 0 and has_marker)


def try_english(query):
    """Точка входа: отвечает по-английски, если вопрос английский.
    Пустой/не-строковый/слишком короткий запрос → None. Один return: str/None.
    None = вопрос не англ. (нужно другое)."""
    if not isinstance(query, str) or len(query.strip()) < 6:
        return None
    if len(query) > 5000:
        return None
    if not _is_english_query(query):
        return None
    if not isinstance(_EN_KB, dict):
        return None
    q_low = (query or "").lower()
    answer = None
    # поиск темы по ключевым словам; при нескольких совпадениях выбираем тему с
# самым длинным совпавшим ключом (чтобы «stem cell» не съедала «cell»)
    topics_test = _TOPIC_TEST if isinstance(_TOPIC_TEST, (list, tuple)) else []
    best_len = -1
    for topic, keys in topics_test:
        for k in (keys or []):
            if isinstance(k, str) and k and k in q_low and len(k) > best_len:
                best_len = len(k)
                answer = _EN_KB.get(topic)
    # fallback: прямое вхождение ключа-темы как отдельного слова
    if not answer:
        q_toks = set()
        for t in q_low.replace("-", " ").split():
            w = t.strip(".,!?;:'\"()")
            if w:
                q_toks.add(w)
        for topic in _EN_KB:
            if isinstance(topic, str) and topic and topic in q_toks:
                answer = _EN_KB.get(topic)
                break
    if not answer and _EN_KB:
        answer = ("I understood your question. I'm mainly trained on Russian. "
                  "Tell me the topic and I'll answer in simple English if I can.")
    return (answer if isinstance(answer, str) and answer else None)


if __name__ == "__main__":
    print(try_english("what is a neural network?"))
    print(try_english("what is the fibonacci algorithm and its complexity?"))
    print(try_english("расскажи про нейрон"))  # русский — должно быть None