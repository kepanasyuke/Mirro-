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
    "mirth": ("Mirth is the cheerful and jolly happiness expressed in laughing and fun. "
              "It is the light, spontaneous joy that lifts a room and warms those around you. "
              "Unlike deep sorrow or fake gaiety, mirth is genuine and contagious, helping "
              "people bond and turning ordinary moments into happy ones."),
    "sincerity": ("Sincerity is the quality of being honest and free from hypocrisy or pretense in what "
                  "you say and do. A sincere person means what they say and says what they mean, with no "
                  "hidden agenda. Sincerity builds the deepest form of trust, because it is the foundation "
                  "of authentic relationships and honest communication."),
    "zeal": ("Zeal is eager and energetic devotion to a cause, activity or pursuit. It is the passionate "
             "drive that makes work feel like a calling rather than a chore. Zeal can be a tremendous force "
             "for good — pushing people to achieve great things — but it must be guided by wisdom and truth, "
             "for unchecked zeal can become fanaticism."),
    "assiduousness": ("Assiduousness is the quality of applying oneself with constant and unremitting care "
                      "to one's tasks. An assiduous worker is steady, thorough and persistent, giving close "
                      "attention to every detail. It is diligence raised to its highest pitch, and it is the "
                      "behavior, more than raw talent, that most reliably produces excellence."),
    "discernment": ("Discernment is the ability to judge well and to distinguish the fine differences "
                    "between things that may look alike. It is the trained skill of telling what is true "
                    "from what is merely plausible, and what is valuable from what is merely attractive. "
                    "A discerning person sees with clarity and chooses with wisdom, guided by principle and "
                    "experience rather than by impulse or surface impression."),
    "stamina": ("Stamina is the physical or moral strength to sustain prolonged effort or to withstand "
                "hardship. It is the durable energy that lets an athlete finish a marathon or a worker "
                "persist through a long task without flagging. More broadly, stamina refers to the inner "
                "reserve that carries someone through difficulty when would-be competitors have given up."),
    "gentleness": ("Gentleness is the quality of being mild in temperament and soft in manner, showing "
                   "kindness rather than force. A gentle person is tender toward others' feelings and "
                   "avoid violence or harshness even when provoked. Far from weakness, true gentleness "
                   "requires great strength and self-control, and it can calm the most heated conflicts."),
    "quietness": ("Quietness is the state of being free from noise, disturbance or commotion. It can refer "
                  "both to an outer condition of silence and to an inner state of calm and stillness. "
                  "A quiet mind is better able to think clearly, listen deeply and act with intention. "
                  "In a noisy world, cultivating quietness is a strength that fosters focus and peace."),
    "hardihood": ("Hardihood is the quality of being bold and fearless in daring undertakings, combined "
                  "with enough strength to endure hardship. It is a blend of audacity and endurance — the "
                  "courage to attempt difficult things and the toughness to see them through. Hardiness of "
                  "spirit lets a person step beyond comfort to attempt what others would not dare."),
"fellowship": ("Fellowship is a feeling of shared interest and mutual support among people who work, "
                   "worship or travel together. It is the warm bond that grows when shared experiences, "
                   "common goals or a common purpose draw people into a real community. Fellowship turns a "
                   "group of individuals into a family of choice, making each person stronger through the "
                   "loyalty, help and company of the others."),
    "nobility": ("Nobility is the quality of being elevated in character, generous in spirit and free from "
                 "anything petty or selfish. Historically it named a rank of titled families, but its true "
                 "meaning is moral rather than social. Noble people act with integrity and compassion because "
                 "it is right, not because it is profitable, and this inward nobility is available to anyone "
                 "regardless of birth."),
"virtue": ("Virtue is a quality of moral excellence, righteousness and goodness in a person. It is the "
               "habit of choosing the right action in the right way for the right reason. Virtues such as "
               "courage, honesty, temperance, justice and compassion are the building blocks of a trustworthy "
               "character. To be virtuous is to become the kind of person who does good naturally and reliably, "
               "not occasionally by chance."),
    "benevolence": ("Benevolence is the disposition to do good and the desire to promote the happiness of "
                    "others. It is kindness translated into action, a readiness to help that asks for nothing "
                    "in return. Benevolence differs from mere generosity in its motivation — it is not about "
                    "giving things but about wishing others well and acting on that wish. It is one of the most "
                    "practical forms of love."),
    "largess": ("Largess is generous bestowal of gifts or money, usually to those in need or for public good. "
                "It carries a sense of nobility and abundance, as when a king grants lands to a loyal servant "
                "or a wealthy patron endows a school. While largess is lavish, it should never be merely for show — "
                "true largess seeks to do real good and to lift others up."),
    "civility": ("Civility is the practice of behaving in a polite, respectful and courteous manner toward "
                 "others, even toward those with whom one disagrees. It is the basic glue of a functioning "
                 "society, making it possible for strangers to cooperate and for opponents to disagree without "
                 "disrespect. Civility is not weakness or the absence of conviction; it is the willingness to "
                 "treat every person with basic dignity."),
    "moderation": ("Moderation is the avoidance of excess and the practice of keeping everything in its proper "
                   "measure. It is the golden mean between deficiency and excess that guides sound living in all "
                   "things — eating, working, speaking, spending and even in showing emotion. Moderation is not "
                   "timidity or mediocrity; it is the disciplined wisdom that gives a person balance and self-control."),
    "tranquility": ("Tranquility is a state of quiet peacefulness and calm, free from agitation or disturbance. "
                    "It is the serene stillness of a lake at dawn or the settled ease of a mind at rest. "
                    "Achieving tranquility often requires turning inward and letting go of racing thoughts. In a "
                    "hurried world, it is a precious state that restores clarity, health and perspective."),
    "nurturance": ("Nurturance is the act of caring for and encouraging the growth and well-being of another — "
                   "of a child, a student, a partner or an idea. It combines patience, gentleness and attentive "
                   "love, giving what is needed for someone to thrive. The nurturing person does not dominate or "
                   "smother, but creates the safe conditions in which growth can naturally unfold."),
    "serendipity": ("Serendipity is the happy faculty of discovering valuable or pleasant things by chance. "
                    "It is the unexpected good fortune that comes when a fortunate accident meets a prepared mind. "
                    "While the event itself is a matter of luck, recognizing and capitalizing on it is a skill — "
                    "curious, observant people are the ones most likely to turn a lucky break into an opportunity."),
    "warmth": ("Warmth is the quality of being friendly, affectionate and genuinely welcoming toward others. "
               "It is the human glow that makes people feel at ease, accepted and valued in your presence. "
               "Warmth is often underestimated because it is quiet, yet it is one of the most powerful forces "
               "for connection — it melts reserve, softens conflict and opens the door to trust."),
"magnificence": ("Magnificence is the quality of being grand in scale, impressive in beauty or generous in "
                     "display, without sacrificing dignity. It is seen in architecture, ceremony and the works "
                     "of art or nature that leave people in awe. True magnificence is not empty ostentation; it "
                     "combines noble ambition with impeccable taste, so that grandeur serves beauty rather than "
                     "garish display."),
    "sageness": ("Sageness is the wisdom that comes from long experience and deep reflection — the kind of hard-won "
                 "sense that belongs to a mature and judicious mind. It is what separates the merely clever from the "
                 "truly wise. A sage does not merely know facts; they know how to apply knowledge to real life, and "
                 "their counsel is valued precisely because it has been tested by seasons of trial and error."),
    "eloquence": ("Eloquence is fluent, persuasive and graceful use of language. An eloquent speaker chooses words "
                  "that move the emotions, sharpen the mind and stir the will of the listener. Eloquence is not mere "
                  "verbal trickery; at its best it is truth expressed with such power and beauty that it can change a "
                  "person's mind or move a crowd to action. It is the crowning skill of the capable communicator."),
    "wit": ("Wit is the quick, clever humor that springs from intelligence and sharp perception. A witty remark "
            "joins amusing ideas in a surprising way, delighting the listener with its truth and timing. Wit is "
            "more than the ability to tell jokes; it is a way of thinking — agile and associative — that sees "
            "unexpected connections others miss. In the right hands, wit disarms hostility, eases tension and makes "
            "company delightful."),
    "charisma": ("Charisma is an attractive quality in a person that inspires devotion, trust and enthusiasm in "
                 "others. It is a magnetic charm that draws people in and makes them willing to follow. Charisma is "
                 "not mere physical attractiveness or celebrity; it is a blend of presence, confidence, warmth and a "
                 "genuine interest in other people. Those who possess it can move others to great achievement, but it "
                 "carries an ethical responsibility to use that power wisely."),
    "earnestness": ("Earnestness is the quality of being sincere, serious and wholehearted in purpose or feeling. "
                    "An earnest person cares deeply about truth and does not treat important matters lightly or with "
                    "irony. It is the opposite of flippancy and half-heartedness. Earnestness gives weight to words and "
                    "actions, so that promises mean something and efforts are not wasted on pretense. It is the fuel of "
                    "conviction and the mark of a trustworthy heart."),
    "honor": ("Honor is a code of personal integrity that compels a person to do what is right, even when no one is "
              "watching and even when it is costly. It is the inner sense of worth that comes from living up to one's "
              "own principles and the outward reputation that follows. In its deepest sense, honor is not about praise or "
              "elevated titles but about keeping faith with what one has promised and respecting the dignity of others. A "
              "person of honor would rather suffer loss than betray their word."),
    "decorum": ("Decorum is behavior in keeping with good taste, propriety and the accepted standards of polite "
                "society. It is the outward expression of an inward respect for others and for oneself. Acting with "
                "decorum means knowing what is appropriate in any situation — when to speak, when to be silent, when to "
                "act and when to hold back. Far from being mere etiquette, decorum is a form of kindness that makes people "
                "around one comfortable and respected."),
"finesse": ("Finesse is refined and delicate skill in handling a difficult or delicate task with ease and subtlety. "
                "It is the art of doing something difficult so smoothly that it looks effortless, without clumsy force. "
                "Finesse appears in the deft touch of a surgeon, the gentle persuasion of a diplomat and the polished grace "
                "of a dancer. It is the quality that turns competence into mastery and marks the difference between merely "
                "getting something done and doing it beautifully."),
    "guilelessness": ("Guilelessness is the quality of being free from cunning, deceit or treachery. A guileless person is "
                      "open, honest and without hidden malice, simple in word and in deed. It is not the same as naivety, "
                      "which comes from not knowing better; rather, it is a chosen innocence that refuses to manipulate or "
                      "deceive. In a world full of stratagem, guilelessness is a refreshing and disarming honesty that invites "
                      "trust and demonstrates true moral simplicity."),
    "neighborliness": ("Neighborliness is the friendly and cooperative spirit that exists among people who live or work "
                       "near one another. It is the small kindnesses exchanged across a fence or a hallway, the helping hand "
                       "in a time of need, and the quiet watchfulness that keeps a community safe. Neighborliness turns a mere "
                       "collection of private houses into a real neighborhood where people know each other and look out for "
                       "one another."),
    "affability": ("Affability is the quality of being easy to approach and pleasant to talk with. An affable person is "
                   "genuinely friendly, courteous and interested in others, so that people feel comfortable in their company. "
                   "It is a social warmth that lowers barriers and builds rapport quickly. Affability differs from mere good "
                   "manners in its sincerity; it is a natural warmth of disposition that makes strangers feel at ease and turns "
                   "casual acquaintances into lasting friends."),
"timeliness": ("Timeliness is the quality of being well-timed, punctual and appropriate to the moment at hand. A timely "
                   "action occurs at the exact right moment to be useful; a timely word is spoken when it can do the most good. "
                   "Timeliness shows respect for others' schedules, foresight about upcoming needs and a practical grasp of the "
                   "situation. In nearly every field, from medicine to business to diplomacy, doing the right thing at the right "
                   "time can be just as important as doing the right thing at all."),
    "steadiness": ("Steadiness is the quality of being firmly fixed, dependable and constant in behavior, emotions or aim. "
                    "A steady person is not easily swayed by sudden fear, flattery or provocation; their judgment remains clear "
                    "and their hand remains sure under pressure. It is seen in the craftsman whose hand does not shake, the "
                    "leader who remains calm in a crisis, and the worker who completes the same honest task day after day. "
                    "Steadiness is the root of reliability and the steadying hand of every enduring endeavor."),
    "fidelity": ("Fidelity is strict faithfulness to obligations, duties or the person one has pledged loyalty to, and, by "
                 "extension, the exactness with which something is reproduced or copied. It is the quality that keeps a spouse "
                 "true, a soldier loyal to their country, and a translator faithful to the original text. Fidelity is the binding "
                 "thread of every lasting trust, for it assures others that your word is dependable and your promises will be kept "
                 "even at a cost to yourself."),
    "probity": ("Probity is the quality of having strong moral principles and complete honesty in dealing with money, power or "
                "public office. It is integrity in its most practical form, where a person can be trusted absolutely because their "
                "handling of resources is beyond reproach. Probity is the foundation of professional reputation and the attribute "
                "that most makes people willing to entrust their interests to you. It is what keeps judges impartial, auditors reliable "
                "and leaders honest."),
    "goodness": ("Goodness is the quality of being morally excellent, kindhearted and beneficial in one's actions and intentions. "
                 "A good person is one whose character is marked by virtue and whose life is a positive influence on those around them. "
                 "Goodness is not a single act but a consistent pattern of seeing the best in others, telling the truth and lending a "
                 "helping hand. In its simplest form, goodness is the desire to make things better and the daily commitment to act on "
                 "that desire."),
    "kindred spirit": ("A kindred spirit is a person whose nature, tastes or sensibilities are very similar to your own, so that "
                       "understanding between you is immediate and deep. Meeting a kindred spirit is rare enough to feel like a small "
                       "miracle — someone who intuits what you mean before you finish speaking, who laughs at the same things and values "
                       "the same truths. Such connections are the heart of friendship, offering the comfort of being truly known and the "
                       "rare joy of finding a companion for the road of life."),
    "amiability": ("Amiability is the quality of being pleasant, good-natured and easy to get along with. An amiable person has a "
                   "sweet and agreeable disposition that makes others comfortable in their presence. It is a quieter and more passive "
                   "form of warmth than affability — where the affable person actively reaches out to others, the amiable person's very "
                   "nature is mild, gentle and likable. Amiability smooths everyday interactions and is one of the most endearing of "
                   "human qualities."),
    "stalwartness": ("Stalwartness is stubborn and hearty loyalty combined with physical or moral strength. A stalwart supporter "
                     "is one who can be relied upon completely, in good times and in bad, without wavering. The word conjures the image of "
                     "a robust and resolute figure who stands firm against the storm. Stalwartness is the quality of the friend who never "
                     "deserts you, the employee who stays loyal through adversity, and the soldier who holds the line when it matters most."),
    "phronesis": ("Phronesis is the ancient Greek virtue of practical wisdom — the ability to think about how and why one "
                  "should act in order to achieve a good life. Unlike theoretical knowledge, phronesis is concerned with action "
                  "in particular situations and with what is good and bad for humans. It is the wisdom of the experienced "
                  "statesman, the skilled artisan and the mature counselor, embodying good judgment in everyday decision-making."),
    "peaceableness": ("Peaceableness is the disposition to live in harmony with others and to avoid quarrels, conflict and "
                      "violence whenever possible. A peaceable person is not necessarily passive; they are simply wiser in "
                      "choosing their battles and more skilled at resolving differences through words rather than force. Peacefulness "
                      "at the personal level makes homes happier, and at the national level it is what makes diplomacy and lasting "
                      "agreements possible between peoples."),
    "harmony": ("Harmony is the pleasing arrangement of parts into a cohesive and balanced whole, whether in music, in a "
                "community or in one's own life. In music, harmonious notes combine to create chords that resonate beautifully; "
                "in society, harmony exists when diverse people live together in agreement and mutual respect. Harmony does not mean "
                "uniformity or the absence of disagreement, but the resolution of differences into a state of balance and concord "
                "where every part fittingly contributes to the well-being of the whole."),
    "comity": ("Comity is courteous respect and mutual consideration between nations, groups or individuals, especially the "
               "willingness to honor one another's laws, customs and institutions out of mutual goodwill. In the language of "
               "international law, comity is the principle by which one state recognizes the legal acts of another as a matter of "
               "courtesy rather than obligation. On a personal level, it is the politeness that makes civilized dealings possible even "
               "between strangers or rivals, smoothing the friction of everyday life."),
    "pleasantness": ("Pleasantness is the quality of being agreeable, cheerful and genial in manner, so that one's company and "
                     "words give simple pleasure to others. A pleasant person is easy to be around because they spread good cheer, "
                     "speak kindly and carry themselves with an attractive warmth. It is the everyday polish that makes interactions "
                     "smooth and is closely related to charm and likeability. Cultivating pleasantness costs nothing, yet it makes the "
                     "world a friendlier and more livable place for everyone encountered."),
    "warmheartedness": ("Warmheartedness is the quality of being kind, affectionate and genuinely caring toward others. A warmhearted "
                        "person feels deep concern for the welfare of people and lets that concern show through in spontaneous kindness. "
                        "It is closeness kin to compassion and brotherly love, expressed both in warm words and in tangible acts of help. "
                        "What distinguishes the warmhearted is the readiness of their affection — they do not wait to be asked, but reach out "
                        "freely, making the lonely feel remembered and the hurting feel cared for."),
"perspicacity": ("Perspicacity is the quality of showing keen mental discernment and penetrating insight into things. A perspicacious "
                     "person sees quickly and clearly to the heart of a matter, catching implications and possibilities that escape slower or "
                    "more superficial observers. It is the intellectual sharpness that lets one judge situations accurately at first glance and "
                    "make wise decisions on the basis of partial information. Allied with good sense, perspicacity becomes one of the most powerful "
                    "tools of the successful strategist, investor or detective."),
    "conviviality": ("Conviviality is the quality of being festive, sociable and filled with the warmth of good company. A convivial person "
                    "is one who enjoys and creates joyful social gatherings, making others feel welcome and at ease in their presence. The word "
                    "encourages an atmosphere of cheerfulness and shared enjoyment, as when friends gather over a meal or neighbors celebrate a happy "
                    "occasion together. Cultivating conviviality enriches life, for it is in such shared moments of laughter and fellowship that "
                    "the deepest bonds of friendship are formed."),
    "innocence": ("Innocence is the state of being free from guilt, sin or moral wrong, and free from cunning or malice toward others. In a child, "
                  "it is the natural and charming purity that comes before the world teaches deceit; in an adult, it is the deliberate choice to live "
                  "without pretense or cruelty. Innocence is often prized for its simplicity and its power to disarm hostility, for an innocent heart "
                  "trusts rather than suspects and offers friendship without expecting betrayal. Above all, it is a reminder that integrity and goodness "
                  "are not weaknesses, but the very substance of a life well-lived."),
    "verity": ("Verity is truthfulness and conformity to fact or reality. It is the quality of being true and accurate, whether in speech, thought or "
               "account given. To act with verity is to be honest and to reflect things as they truly are, not as one might wish them to be. In logic and "
               "philosophy, the pursuit of verity is the pursuit of what is real and can be established beyond doubt. In daily life, it is the simple discipline "
               "of not deceiving others or oneself, and of standing firmly on the side of what is true."),
    "purity": ("Purity is the state of being free from contamination, whether physical or moral, and of being unmixed with what is foreign or base. In a "
               "physical sense, it is the condition of substance free from impurities; in a moral sense, it is the cleanness of heart that comes from "
               "avoiding what corrupts. Purity should not be confused with naivety or prudishness; rather, it is the strength to keep oneself untainted by the "
               "corrupting influences of the surrounding world. It is the quality that lets the light of a person's character shine through undistorted."),
    "newness": ("Newness is the quality of being recently made or unused, or of being novel and fresh in character. In an everyday sense, it is the excitement "
                "of a thing that has not yet been worn down by habit or time, or of an idea that has not yet grown stale. Newness brings with it freshness of "
                "perspective, vigor of effort and the promise of untried potential. It is the beginning of every journey and the blank canvas of every creation, "
                "and as such it is treasured not for its own sake but for the promise it carries of what is yet to come."),
    "genuineness": ("Genuineness is the quality of being real, authentic and true to one's actual nature, thoughts and feelings. A genuine person does not wear "
                    "a mask or pretend to be what they are not, but lets their true self show in all their dealings. In a world of polished surfaces and careful "
                    "posturing, genuine sincerity stands out as a rare and refreshing virtue. Genuineness builds trust because it reveals no discrepancy between "
                    "the person one appears to be and the person one actually is, and it is the foundation of all honesty in personal relationships."),
    "righteousness": ("Righteousness is the quality of being morally right, just and virtuous; of doing what is right in the sight of God and fellow humans. "
                      "A righteous person acts with moral integrity, upholding what is just even when it is costly or unpopular. It is not to be confused with "
                      "self-righteousness, which is the smug pretense of one's own goodness; rather, true righteousness is the humble and faithful pursuit of "
                      "right conduct in all things. History and scripture alike hold up the righteous as those who walk the straight path, whose lives testify to "
                      "the power of walking uprightly."),
    "equanimity": ("Equanimity is mental calmness and composure, especially in times of stress. It is the evenness of temper that keeps a person's mind steady "
                  "and clear whether they face triumph or disaster. The practice of equanimity does not mean being indifferent to what happens, but instead means "
                  "not being ruled by fleeting passions and shocks. It allows one to view situations with wisdom and to act with sobriety, and it is a quality prized "
                  "by philosophers and warriors alike as a mark of true poise and inner strength."),
    "philanthropy": ("Philanthropy is the love of humankind, expressed through practical acts of goodwill toward one's fellow beings. It is the desire and practice of "
                     "promoting the welfare of others, often through charitable gifts of money, time or effort to those in need. Philanthropy is distinguished from mere "
                     "charity by its breadth and purpose: it seeks not merely to relieve immediate suffering but to address the causes of that suffering and to improve the "
                     "human condition on a larger scale. In its grandest form, it is the engine of hospitals, universities and libraries; in its simplest form, it is one "
                     "stranger helping another."),
    "bereavement": ("Bereavement is the state of deep loss felt when death takes someone dear, and the process of grief that follows. It is one of the heaviest and most "
                    "universal human experiences, affecting people in body, mind and spirit. Though painful, bereavement is not a sign of weakness; it is the natural "
                    "response of a heart that has loved deeply. Supporting someone through it, or enduring it with dignity ourselves, requires patience, compassion and time, "
                    "and often brings a renewed sense of the value of life and the ties that bind us."),
    "yearning": ("Yearning is a strong, persistent longing or desire for something deeply felt but not yet possessed. It can reach toward a far place, a lost love, a better "
                 "self or a distant goal. Yearning is more intense than wishing; it has the ache of absence in it and the hope of fulfillment pushing against it. Though it "
                 "can cause restless dissatisfaction, yearnings are not to be dismissed, for they reveal what the heart truly values and give direction to a life. When "
                 "rightly directed, they become the fuel of passionate accomplishment."),
    "unselfishness": ("Unselfishness is the quality of putting the needs and interests of others before one's own comfort or gain. An unselfish person gives freely of time, "
                      "energy or possessions without expecting anything in return, finding joy in the happiness they bring to others. It is the practical opposite of selfishness "
                      "and a mark of a mature heart, for it reflects an understanding that we are not isolated selves but members of families, communities and a common humanity. "
                      "The truly unselfish do not merely sacrifice; they give from a place of fullness, and their generosity of spirit has a way of coming back to bless them."),
    "foresight": ("Foresight is the ability to anticipate what will happen or what is likely to be needed in the future. It is the forewarned caution that allows a person to plan "
                  "ahead, avoid hazards and seize opportunities before they are obvious to others. Foresight is a mark of wisdom, for it joins a realistic understanding of the present "
                  "with a shrewd guess about the morrow. It is what saves a business from an unwise venture, what keeps a family from financial ruin, and what allows a leader to see "
                  "the shape of coming events."),
    "intrepidity": ("Intrepidity is fearlessness in the face of danger or daunting odds, a courage that is not shaken by threats or hardships. An intrepid person advances where others "
                    "would hesitate, driven by a fortitude that goes beyond natural boldness. It appears in the mountaineer who scales a sheer cliff without a net, the firefighter who "
                    "charges into a burning building, and the leader who stands by a conviction though it costs them everything. Intrepidity is not recklessness, which ignores danger; it is "
                    "courage that fully sees the danger and chooses to proceed anyway."),
    "fealty": ("Fealty is the oath-bound loyalty that a vassal pledges to a lord in medieval feudalism, and by extension any faithful allegiance to a person, cause or country. It is a "
               "heartfelt and solemn promise to be faithful, to keep one's word and to stand by one's obligations even at great personal cost. Fealty goes beyond mere obedience or friendship; "
               "it is a sacred trust that binds individuals together in a relation of mutual duty and honor. In its deepest sense, true fealty means being loyal when it is easiest to betray, "
               "and remaining true when all the rewards lie in defection."),
    "loyalty": ("Loyalty is the quality of being firmly and wholeheartedly dedicated to a person, group, cause or country. It is the steadfast attachment that makes someone stand by the ones "
                "they love through thick and thin, through good times and bad. Loyalty is expressed in constancy of friendship, in keeping promises, and in defending the honor of those to whom "
                "one is attached. It is one of the most valued of human virtues because it is tested in adversity: a loyal friend is proven not when everything goes smoothly, but precisely when "
                "the bonds of loyalty are hardest to maintain."),
    "unfailingness": ("Unfailingness is the quality of never ceasing, never running out, or never letting one down. It describes a supply that does not fail, a patience that does not give out, "
                      "or an optimism that does not fade. To be unfailing in something is to be constant in it without exception or interruption, as in unfailing kindness, unfailing courage or "
                      "unfailing support. It is a quiet but powerful guarantee, for it tells others that you can count on it not only today but every day, and that goodwill will not be exhausted no "
                      "matter how often it is called upon."),
    "solidity": ("Solidity is the quality of being firm, substantial and dependable, whether in physical structure or in character. A solid structure does not bend or break under pressure; a solid "
                 "argument is one that cannot be refuted; and a solid friendship is one that survives misunderstanding and time. Solidity is the opposite of flimsiness, weakness or instability. It is what "
                 "gives confidence, because one can build on a solid foundation, lean on a solid support or trust a solid promise. In human terms, it is the dependability that makes a person a rock of "
                 "strength to others."),
    "directness": ("Directness is the quality of being straightforward and unswerving in speech or action, without ambiguity or evasion. A direct person says what they mean and means what they say, "
                   "avoiding hints, half-truths and hidden agendas. Directness is not the same as rudeness; it can be expressed with perfect courtesy even while being perfectly clear. It saves time, prevents "
                   "misunderstanding and earns respect, for others always know where they stand with a direct interlocutor. It is prized in business, in friendship and in diplomacy as the surest way to the "
                   "real issue."),
    "candor": ("Candor is the quality of being open, honest and frank in expression, and free from bias, reservation or deception. A candid person says what they genuinely think, without hiding behind "
               "flattery or oblique hints. Candor is the foundation of genuine communication and is essential for clearing away the mists of ambiguity and misunderstanding that cloud so many conversations. "
               "At its best, candor is tempered with tact, so that the truth is spoken directly yet in love, making it a quality that is as precious in personal friendships as it is in professional dealings."),
    "plainness": ("Plainness is the quality of being simple, unadorned and easy to understand, without unnecessary ornamentation or embellishment. A plain style of speech is direct and clear, and a plain "
                  "manner of living is unpretentious and free from artificial pomp. In an age of hype and exaggeration, plainness is a kind of virtue, for it keeps language honest and intentions visible. "
                  "The plain speaker may not dazzle with rhetorical flourish, but their words carry weight because they are trusted to be exactly what they appear to be."),
    "simplicity": ("Simplicity is the quality of being uncomplicated, straightforward and free from vain ornament or excess. It denotes a purity of motive and a reduction of one's life to what is truly "
                   "essential, freeing the mind from useless clutter and deceit. In design, simplicity is elegance reached by subtraction; in conduct, it is honesty achieved by the absence of pretense. "
                   "Simple living is not the same as living poorly; rather, it is living deliberately and contentedly with less, so that what remains is all the more meaningful."),
"unaffectedness": ("Unaffectedness is the quality of being genuine and spontaneous in manner, without artificiality or contrivance. An unaffected person does not put on airs, does not perform for others, "
                       "and does not try to be what they are not, but acts with a natural ease that is free of self-consciousness. It is a rare and refreshing quality in a world of carefully cultivated images, "
                       "and it is the simplest road to authenticity in personal relationships, for it lets others see the true person behind the social mask."),
"veracity": ("Veracity is habitual truthfulness and the disposition to always tell the truth, even when a lie would be easier or more convenient. It is the daily practice of accuracy in reporting facts "
                 "and the refusal to distort, exaggerate or withhold what is known to be true. Veracity is the bedrock of all reliability and the foundation of credibility, for a person's word is only as good "
                 "as the truth it carries. In law, in journalism and in daily life, veracity is what makes testimony trustworthy, reports reliable and relationships honest."),
    "comprehensiveness": ("Comprehensiveness is the quality of including, involving or dealing with all or nearly all elements, aspects or possibilities of something. A comprehensive study, plan or treatment covers "
                         "all of the relevant ground and leaves no important part unconsidered. It is the opposite of narrowness and partial treatment, which look at only one facet of a many-sided matter. "
                         "Comprehensiveness requires both breadth of knowledge and thoroughness of method, and it is the quality that distinguishes the considered overview from the hasty partial glance."),
    "thoroughness": ("Thoroughness is the quality of doing something carefully and completely, leaving no detail unchecked and no stone unturned. A thorough worker does not rush through a task, but takes the time "
                     "to do it fully and correctly the first time, attending to details that others might overlook. It is the practical side of conscientiousness, the disciplined follow-through that converts good intentions "
                     "into finished and reliable results. Thoroughness is what separates the excellent craftsman from the careless one, and it is essential in any field where accuracy and completeness matter more than speed."),
    "good faith": ("Good faith is honesty of intention and sincerity of motive, especially in business transactions, contracts and negotiations. To act in good faith means to deal with others fairly and openly, honestly "
                   "following through on promises and agreements without deception or hidden self-interest. The concept is central to law, where contracts imply a duty of good faith, and to all healthy relationships, which "
                   "cannot survive without it. It is the opposite of fraud, duplicity and bad faith, and its presence is what makes trust possible between strangers."),
"good humor": ("Good humor is a cheerful and pleasant state of mind that makes a person easy to laugh and enjoyable to be around. It is the good-natured disposition that turns a simple joke into an occasion for happy "
                "laughter and keeps one's spirits up through trying times. A person of good humor is quick to laugh at the incongruities of life and slow to become angry, spreading goodwill wherever they go. It is closely "
                "akin to cheerfulness, mirth and joviality, and it is one of the most magnetic of human qualities, for it makes the whole world seem brighter and more friendly."),
    "attentiveness": ("Attentiveness is the act of paying close and careful attention to what is happening, being said or being done around one. An attentive person listens fully, notices details others miss, and responds promptly to "
                      "the needs of the moment. It is the opposite of distraction and absent-mindedness. In the classroom, attentiveness makes learning effective; in personal relationships, it makes the other person feel valued and heard; "
                      "in the workshop, it prevents accidents and errors. Attentiveness is the practical foundation upon which care, courtesy and understanding are all built."),
    "wakefulness": ("Wakefulness, in its figurative sense, is alertness of mind and quickness of perception, free from drowsiness or dullness. The wakeful person is not merely awake but stays mentally sharp, aware of what is going on "
                    "around them and ready to act. It is the mental vigilance that allows one to catch an error before it becomes a disaster or to notice an opportunity before it passes. Wakefulness of spirit is closely tied to "
                    "watchfulness, and it is essential to anyone whose work demands sustained attention, from the night-shift doctor to the security guard."),
    "watchfulness": ("Watchfulness is the state of keeping careful guard over something or someone, and of being constantly aware of what may happen. The watchful person is on the lookout for danger, opportunity or change, and is ready "
                     "to respond at a moment's notice. It is the attentive vigilance of a sentinel, the caution of a lookout at sea, and the alertness of a mother over a sleeping child. Watchfulness is not the same as anxiety or paranoia; "
                     "it is an even and expectant attention that neither relaxes its guard nor is alarmed without cause. Used rightly, it is the guardian of safety and the first line of defense in every kind of vigilance."),
"surveillance": ("Surveillance is close observation kept over someone or something, usually to watch for activity, wrongdoing or change. In modern life it is most often associated with cameras, monitoring systems and intelligence-gathering, "
                     "but in its simplest form it is the careful watching that any responsible person does to keep a situation under control. Surveillance can be a force for good or ill, protecting the innocent and catching wrongdoers, or "
                     "invading privacy and chilling free speech. Its morality depends entirely on who is watched, by whom and for what purpose, for it is the same tool that can preserve order or become an instrument of oppression."),
    "benignity": ("Benignity is the quality of being kind, gentle, gracious and favorable, and of lacking any disposition to harm or do evil. A benign presence is warm and soothing, the opposite of harmful or threatening. The word is used of "
                  "a benign tumor that does not spread harmfully, of a benign climate that is mild and favorable, and of a benign ruler whose governance is mild and just. Benignity is the gentle face of goodness, touching everything around it "
                  "with an unmistakable grace and doing good almost as a natural force, rather than as a calculated act."),
"verve": ("Verve is energy and enthusiasm in the expression of thought or in the pursuit of activity, a lively forcefulness that infuses one's words and deeds with spirit and vitality. A person of verve attacks every task with gusto and "
               "lives each moment with intensity, so that their very presence is charged with animation. It is what makes a dancer's movement electrifying, a writer's prose crackle with life, and an athlete's play burst with flair. Verve is the "
               "alive quality that separates the merely competent from the inspired, and the routine from the memorable."),
"ardor": ("Ardor is intensity of passion, heat of feeling or great eagerness in the pursuit of a cause, person or ambition. The word literally means a burning, and figuratively it names the fire of romantic love, the fervor of devotion and "
                "the fierce energy of a committed struggle. An ardent supporter is one who cares unreservedly, and her or his ardor enlivens everything from the pages of love letters to the roar of a stadium. Ardor is the fuel that sustains "
                "long effort and the warmth that makes passionate engagement with the world possible at all."),
"passion": ("Passion is a very strong emotion, an intense drive or enthusiasm, or the object of such intense feeling. It can be felt for a person, a purpose, a sport or a call in life. Passion is the fire in the belly that pushes artists to "
                 "create, scientists to discover and activists to persist. It is the difference between engaging with the world and merely passing through it. When directed well, passion gives meaning and color to existence and impels people toward "
                 "their deepest achievements; when uncontrolled, it leads to obsession and excess, reminding us that this potent and double-edged force must be held in check with wisdom and balance."),
"vim": ("Vim is robust energy and vitality, the brisk liveliness that spurs one into action. It is a quality of being full of life and ready for anything, suggesting great vigor and force. To have vim is to display a zestful, breezy energy in "
             "whatever one undertakes, and to perform it with spring and stamina. In phrases like 'vim and vigor' it stands for the twin necessities of spirited activity, and it is the kind of liveliness that keeps old hands young and makes hard "
             "work feel effortless. Vim is the heartiness of the healthy body and the briskness of the awake mind working together in an untiring rhythm."),
"firmness": ("Firmness is the quality of being solidly established, resolute and unyielding, whether in material structure, in purpose or in principle. A firm resolve does not waver, a firm grip does not slip, and a firm decision is not revised "
                  "at the first sign of difficulty. It is the strength that comes from knowing what one stands for, and the consistency that comes from refusing to be blown about by every wind of opinion. Firmness is what allows a leader to hold a "
                  "course against opposition and a moral agent to resist temptation, and it is misapplied only when it hardens into mere obstinacy."),
"certitude": ("Certitude is the state of being completely certain about the truth of a matter, free from doubt or hesitation. It is more than mere confidence, which can rest on feeling alone; certitude is grounded in knowledge, evidence or "
                   "conviction that leaves no room for equivocation. It brings with it a settled peace of mind and a clear direction for action. Certitude must be distinguished from its counterfeit, certitude without grounds, which is dogmatism, and "
                   "be held with the humility that no human certainty is immune to revision before new evidence."),
    "devotement": ("Devotement is the state of being deeply devoted, the whole-hearted giving of oneself over to a person, a purpose or a cause. It is stronger than mere liking or mild interest, for it implies a settled and unwavering turning of the "
                   "heart and mind toward its object, whether that object be a loved one, a faith, a craft or a calling. Devotement carries with it constancy and sacrifice, for the devoted give up alternatives and endure difficulty gladly. It is the "
                   "bond that holds friendships firm across years, the fuel of the serious artist and the foundation of every long and faithful commitment in human life."),
    "resoluteness": ("Resoluteness is the determined firmness with which one pursues a decision or a course of action, refusing to be swayed, discouraged or turned aside. A resolute person has settled what must be done and intends to see it through, "
                     "meeting obstacles as tests rather than as reasons to retreat. It is the backbone of courage, the steadiness behind every long campaign, and the quality that lets good intentions harden into actual achievement. Resoluteness differs "
                     "from stubbornness in that it aims at a considered goal and adapts its means, while holding its chosen direction with unwavering fixity."),
    "contentment": ("Contentment is the state of being satisfied with what one has and at peace with one's circumstances, free from restless craving for more. The contented person enjoys the present rather than resenting it, finding quiet pleasure in order, sufficiency and the simple good of the day. It is not complacency or indifference to improvement, but a settled gratitude that keeps happiness from being hostage to fortune. Contentment is the sane calm that lies between the anxiety of ambition and the listlessness of despair, and it is widely counted among the deepest sources of steady human happiness."),
    "prudence": ("Prudence is the quality of exercising sound foresight and cautious good judgment in practical affairs, weighing means against ends and consequences before acting. The prudent person does not leap blindly at opportunity but considers timing, cost, risk and the view of the longer road, avoiding needless harm while not shrinking from what must be done. It is one of the classic cardinal virtues, the practical intelligence that governs desire and imprudent impulse. Prudence is the steady hand that guides ambition, the careful planning that turns foresight into safety, and the moderation that refuses to trade a sure good for a glittering risk."),
    "justice": ("Justice is the moral quality of giving every person what is due to them, of treating equals equally and proportioning rights, rewards and punishments to desert. It is the virtue that upholds fairness in the dealings of individuals and the laws and institutions of a community, and it is traditionally ranked with prudence, temperance and courage as one of the four cardinal virtues. Justice demands impartiality, for the truly just person applies the same standard to friend and stranger, to themselves and to others, without regard to rank or favor. It is the bedrock of lawful order and of every relationship that can remain stable and trusted over time."),
    "clemency": ("Clemency is the disposition to be merciful, lenient and mild in the use of power, especially in sparing an offender from the full severity of deserved punishment. The clement judge, ruler or friend holds back from harshness where mercy can be shown without harm, softening strict desert with compassion. It is a mark of magnanimity and self-command, for it requires enough strength to be lenient and enough wisdom to know when mercy does not invite abuse. Clemency differs from weakness in that it is a deliberate choice made from a position of strength, and it is what allows justice to be tempered with humanity."),
    "temperance": ("Temperance is the virtue of moderation and self-restraint, especially in the indulgence of appetite, desire and pleasure. The temperate person neither denies the body all satisfaction nor surrenders to every impulse, but governs appetites with reason and habit so that they serve life rather than master it. It is one of the four classic cardinal virtues along with prudence, justice and courage, and it is the foundation of self-command and durable health in body, temper and fortune. Temperance is not austerity but balance, the measured exercise of freedom that keeps one from the tyranny of excess on either side."),
    "endurance": ("Endurance is the power to bear prolonged hardship, strain or suffering without giving way, and to keep on steadily through difficulty until the goal is reached. The enduring person does not merely survive a single trial but holds out through long campaigns of effort, pain or waiting, drawing on patience, stamina and firm resolve. It is the virtue that underlies every marathon, every long illness borne with grace, and every years-long struggle toward a distant aim. Endurance is the quiet companion of courage, for courage strikes the blow but endurance holds the line when the blow cannot be struck again."),
    "serenity": ("Serenity is the state of being calm, peaceful and untroubled, a quiet composure of mind that is not easily disturbed by agitation or alarm. The serene person can sit in the midst of noise and difficulty yet remain inwardly composed, regarding passing turmoil with steady and unruffled poise. It is deeper than a passing mood of relief, for it rests on a settled trust and a disciplined attention to what can and cannot be controlled. Serenity is the stillness of the deep water beneath the waves, and it is cultivated by patience, acceptance and the sane conviction that most storms simply pass."),
    "patience": ("Patience is the capacity to accept delay, difficulty or provocation without becoming annoyed, hasty or compelled to act too soon. The patient person can wait calmly for the right time, endure repeated setbacks without weariness of spirit, and forbear provocation without breaking into anger. It is not passivity, for patience often holds one steady for a long campaign and the exact moment of decisive action. Patience is a cardinal social and practical virtue, the steady companion of hope, endurance and diligence, and it is the quality that lets time and effort accomplish what force and hurry cannot."),
    "forbearance": ("Forbearance is the patient self-restraint that holds back from retaliation or complaint even when one has grounds for resentment or anger. The forbearing person endures provocation, injury or demands without breaking out in harsh repayment or demanding immediate satisfaction, so as to preserve peace or give room for improvement. It is a virtue of strength rather than weakness, for it requires the power to strike or demand and the self-command to refrain. Forbearance is the office of mercy in daily life, the tolerance that keeps families and friendships whole, and the patience with which a society learns to live with imperfection."),
    "longanimity": ("Longanimity is patient endurance of suspense, provocation or suffering over a long stretch of time, the forbearance that does not merely endure a single blow but holds its composure through years of delay, disappointment or trial. It is a lofty form of patience, carrying with it a serene equanimity that outlasts ordinary endurance. The longanimous spirit keeps its hope and good temper alive when the desired end is slow to come, preserving both dignity and kindness under prolonged strain. Longanimity is the patience of the long view, and it is the steady power behind every vow kept across the years and every labor finally crowned with results."),
    "equity": ("Equity is the quality of being just and fair beyond the letter of a rule, the principle of treating each person according to what is actually due to them under the circumstances. Where strict law or literal fairness might work hardship, equity looks to the spirit and the underlying intent, correcting what is too rigid and supplying what is left out. In law it gave rise to the courts of equity that softened the common law; in ordinary life it is the practical fairness that goes beyond mere equality of form. Equity is justice tempered with understanding, and it is what lets rules serve people rather than people being sacrificed to rules."),
    "munificence": ("Munificence is the quality of being extremely generous in giving, lavishing gifts and support on a princely scale. The munificent giver does not merely share out of abundance but gives splendidly, fitting the size and dignity of the gift to the occasion and the need. It is generosity elevated by magnificence, carried out on such a scale that the giving itself becomes a kind of spectacle. Munificence has built libraries, endowed academies and founded charities that outlive their founders, and it is the generosity of the great-hearted, tempered only by prudence lest liberality outrun means and turn into ruin."),
    "valor": ("Valor is the courageous strength of spirit in the face of danger, the personal bravery that stands firm when threatened or goes boldly forward in peril. It is courage felt as a positive quality of the heart, distinct from mere recklessness, because it is joined with judgment and a sense of what is worth defending. The valorous person does not hide from fear but meets it with resolution, whether on the battlefield, in the defense of the weak or in the endurance of personal loss. Valor has been sung by poets in every age, and it remains the moral backbone that lets individuals and nations face hard necessity without flinching."),
    "bravery": ("Bravery is the bold courage and daring that faces danger, difficulty or pain without retreat, acting steadily even in the midst of fear. Unlike mere recklessness, bravery is joined with purpose and a measure of self-possession, so that the brave person does what is required despite the natural shrinking of the heart. It shows itself in countless forms, from the soldier on the field to the ordinary person who speaks truth at personal cost or endures hardship for another's sake. Bravery is right courage at the right time, and it is one of the most admired and most needful of all the human virtues."),
    "courage": ("Courage is the moral strength to confront fear, danger, difficulty or uncertainty and to act in spite of them in service of what is right or necessary. It is not the absence of fear but the masterly command of it, for the truly courageous are often afraid and yet do what must be done. Courage takes many forms, from the valor of the battlefield to the quieter bravery of speaking truth, admitting error, standing alone or enduring long misfortune without despair. It is ranked as a cardinal virtue, for without it few of the other virtues can long survive. Courage is the resolve of the human spirit that refuses to let danger or dread dictate the right course of action."),
    "fortitude": ("Fortitude is the strength of mind and spirit that enables a person to endure adversity, pain and hardship with firm and patient courage. It is a cardinal virtue that joins endurance with courage, so that one not only confronts danger in a single act but also bears prolonged suffering, disappointment and loss without losing composure or giving in to despair. Fortitude does not make the suffering lighter in itself, but it makes the sufferer able to carry it, steadying the will when circumstances offer no way forward but through. It is the quiet firmness of those who endure what cannot be changed and keep their moral bearing even when hope is slow to return."),
    "graciousness": ("Graciousness is the quality of being kind, courteous and dignified in one's dealings with others, marked by an easy politeness that springs from goodwill rather than convention. The gracious person offers consideration and charm without effort, putting others at ease, granting favors and praise freely, and bearing both success and refusal with equal poise. It is the polished courtesy of the well-disposed, showing courtesy to the lowly as readily as to the great. Graciousness warms all social life, for it is the outer grace of an inner generosity, and it makes the firmness of a host, a superior or a victor gentle and humane."),
    "decisiveness": ("Decisiveness is the readiness to come to a clear determination promptly and to act on it once made, without endless delay, vacillation or second-guessing. The decisive person weighs the options, chooses a course and moves forward with confidence, accepting the small risk of error as the price of progress. It is not headlong rashness, for sound decisiveness rests on due reflection, but it refuses to let the fear of being wrong freeze judgment. Decisiveness is what turns deliberation into achievement, and it is indispensable in leadership, medicine and the emergencies of daily life, where a timely imperfect decision is worth more than a perfect one that comes too late."),
    "sang-froid": ("Sang-froid is the coolness and self-possession with which one meets danger, difficulty or sudden crisis without panic or loss of composure. The person of sang-froid keeps a clear head and steady hand when others lose theirs, acting with the same presence of mind under pressure as in ordinary moments. It is a seasoned and deliberate calm, the fruit of training, temperament and self-command, and it is the executive in the storm, the surgeon at the operating table, and the commander in the field at their best. Sang-froid is courage's cooler brother, the composed readiness that turns steadiness itself into a decisive advantage in moments of peril."),
    "complacency": ("Complacency is a smug and self-satisfied state of mind in which one is so pleased with one's present position or achievements that one sees no need for effort, improvement or watchfulness. The complacent person rests on what has been done and assumes that all will continue smoothly, taking comfort instead of taking stock. It is a quiet danger, for it robs one of the healthy discontent that spurs learning and the vigilance that forestalls failure, making disaster all the more sudden when it comes. Complacency differs from honest contentment in that contentment enjoys the present willingly, whereas complacency leaves duty and readiness asleep."),
    "piety": ("Piety is a due and reverent devotion, whether to the divine, to religion or to family, country and the sacred duties of one's station. The pious person renders with heartfelt sincerity the honor and service owed to what is greater than oneself, treating worship and obligation not as burdens but as the proper ordering of life. In its broadest sense it is dutiful reverence toward God, parents, ancestors and the institutions on which order depends. Piety is the virtue that binds the generations together and keeps the awe, gratitude and obedience of the heart alive amid the distractions of ordinary life."),
    "reverence": ("Reverence is a feeling of deep respect and awe mingled with wonder, directed toward what one holds sacred, excellent or greatly superior, whether deity, nature, tradition, a person or truth itself. The reverent person approaches the object of regard with humility and solemn attention, not as something to be used or mastered but as something to be honored for its own worth. It lies behind worship, filial regard, patriotism and the scientist's awe before the order of the universe. Reverence tempers boldness with respect and power with humility, and it is the attitude that keeps human beings from reducing everything to utility and routine."),
    "zealousness": ("Zealousness is the eager and ardent energy with which one pursues a cause, belief, task or duty, marked by warmth, enthusiasm and whole-hearted devotion. The zealous person does not merely agree with a purpose but throws the full force of temperament behind it, often impelling others by example. Zealousness can spill its beneficence from the worthy promotion of good causes and crafts to the fierce partisanship that blinds and overshoots, and it must therefore be directed with wisdom and moderated with charity. Well governed, it is the driving fire of reform, art and faithful service; ungoverned, it becomes fanaticism. Zealousness is ardor put to work, and it is invaluable when its object is true and its bounds humane."),
    "deference": ("Deference is the courteous yielding to the judgment, wishes or wishes of another out of respect for their age, rank, wisdom or authority, a willingness to let another take the lead where such leading is fitting. The deferential person honors proper precedence, listening and submitting gracefully to legitimate superiority of position or knowledge, without servility or the abandonment of one's own honest judgment. It is the lubricant of all ordered society, smoothing every master and servant, teacher and student, elder and youth relation. Deference differs from subservience in that it is a voluntary courtesy rendered from respect, not a cringing surrender made from fear."),
    "austerity": ("Austerity is a strict and severe simplicity of life which denies unnecessary comfort and luxury, whether chosen as a discipline of spirit or imposed by hard necessity. The austere person lives plainly, contenting the wants of the body with little, and ordering conduct by a strict and sparing rule. As a deliberate practice austerity is valued by ascetics, philosophers and reformers for the self-command and singleness of purpose it cultivates, freeing attention from appetite. It becomes a vice only when turned into mere harshness or when imposed without regard to genuine need. Austerity is frugality carried to the level of a principle, and its proper fruit is freedom rather than privation."),
    "pride": ("Pride is the feeling of satisfaction, worth and elevated self-regard that arises from one's own achievements, qualities or connections, and it carries a double character in moral thought. Rightly held, pride is the proper self-respect that takes healthy satisfaction in honest work well done, that guards one's dignity and refuses servile conduct, and that rejoices without envy in the attainments of those one loves. Wrongly held, it becomes haughtiness, the over-weening conceit that despises others and overrates oneself, which the wise have long counted a snare. Pride is a self-regarding sentiment, dangerous when it turns outward in contempt but noble when it keeps a person faithful to their own best standard."),
    "vainglory": ("Vainglory is excessive, empty and boastful pride in oneself, one's deeds or one's appearance, a vanity that seeks applause more than it seeks worth. The vainglorious person is puffed up with self-conceit, eager for praise and quick to compare himself or herself favorably with others, while build such fame on fragile and passing grounds. It is the love of glory for its own sake, without the solid achievement that alone can earn and sustain true honor. Vainglory is the hollow counterfeit of pride, feeding on the opinion of others and leaving the soul dependent upon their flattery, and the wise have always warned that those who live for applause may be both most pleased and most easily destroyed by it."),
    "humility": ("Humility is the modest and unassuming estimation of oneself, the clear-eyed sense of one's own limitations, errors and dependence that prevents pride from puffing one up. The humble person does not belittle their real gifts, but neither does they overrate themselves, receiving praise without inflation and criticism without resentment. It is a cardinal virtue in many moral and religious traditions, valued as the root of teachableness, of forgiveness and of truthful self-knowledge. Humility is not self-abasement or weakness, for it can coexist with great courage and achievement; it is rather the accuracy of self-appraisal that keeps greatness gentle and learning perpetual."),
    "modesty": ("Modesty is the quality of being unassuming and free from vanity, restraining the impulse to display one's merits, appearance or attainments, and behaving with propriety and simplicity. The modest person does not seek to be thrust forward, lets accomplishments speak rather than trumpet them, and shows restraint in speech, dress and manner. It is closely bound to humility, shamefastness and decorum, and it is prized as the becoming dignity that makes merit attractive and self-promotion unnecessary. Modesty is not the denial of one's gifts but the good manners of the spirit, which keeps its possessor approachable and its praise credible by never having been courted."),
    "dignity": ("Dignity is the quality of worth and honor inherent in a person, office or thing, together with the composed and self-respecting bearing that befits such worth. The dignified person carries an air of calm self-possession, treats others with due respect and expects respect in return, and refuses to be reduced to cringing, clowning or indignity even under pressure. It also marks the intrinsic value that belongs to every human being simply as such, which forbids treating anyone as a mere means. Dignity grounds the claims of human rights, steadies the conduct of the great, and preserves a person's self-respect through reversals of fortune, for it resides in the soul rather than in circumstance."),
    "gallantry": ("Gallantry is the brave, chivalrous and spirited conduct especially associated with courtesy toward women, courage in the face of danger and a readiness to risk oneself for others. The gallant person behaves with a polished and dashing courtesy, combining boldness with a gracious consideration that turns ordinary gestures into acts of respect. In its older and stricter sense gallantry names the courage of the knight or officer, while in common speech it leans toward the charming attentiveness of polite heroic conduct. Gallantry is valor clothed in grace, and at its best it couples the heart of a fighter with the good manners of a gentleman."),
    "splendor": ("Splendor is the quality of shining with brilliant and often magnificent beauty, grandeur or glory, whether in the blaze of the sun, the glow of ceremony, the richness of art or the luster of a noble spirit. What is splendid attracts the eye and the admiration by an intensity of light and distinction that sets it apart from the merely showy. Splendor can be the outward pomp of a court or the inward glory of a virtue or achievement, and it is usually a matter of genuine magnificence rather than gaudy display. It is the radiance that makes excellence visibly excellent, lending weight to occasions and nobility to deeds of more than ordinary worth."),
    "radiance": ("Radiance is the emission of bright light and warmth, or figuratively the glowing brightness of countenance, beauty, health or joy that seems to give off light of its own. What radiates sends beams outward, illuminating everything around it rather than merely reflecting borrowed light. In persons, radiance names that inner health and happiness that makes the face shine and the presence welcoming. In things, it speaks of the sun, the glow of dawn and the shimmer of water in light. Radiance is brightness in its most generous form, for it does not dazzle selfishly but pours itself out to make the world around it visible and warm."),
    "grace": ("Grace is elegance and beauty of form, movement or manner, and in its deeper sense the unmerited favor, kindness and beauty of spirit that freely blesses others. In the physical sense a graceful dancer or gesture moves with effortless ease and poise; in the moral and religious sense grace is goodwill shown undeservedly and the beauty of character that such kindness bestows and reflects. Grace is also said of courteous conduct that puts others at ease, and of the unearned gifts that make labor one's own a pleasure. It binds together the elegant and the benevolent, reminding us that what is truly graceful is both beautiful to behold and generous to give."),
    "amiability": ("Amiability is the quality of being friendly, pleasant and good-natured, so that one is easy to like and agreeable to be with. The amiable person has a sweet and genial disposition, quick to smile, slow to offend, and never seeking to cross or dominate others, as a result of which company is sought and quarrels are few. It is a social virtue that greases the wheels of everyday intercourse, for the amiable turn an ordinary meeting into a pleasant one and take the sting out of disagreement. Amiability is not weakness, for the genuinely amiable can be firm in principle while remaining kind in manner, but it is the bloom of a disposition inclined to goodwill."),
    "sociability": ("Sociability is the disposition to seek, enjoy and fit readily into the company of others, together with the ease of manner that makes one a pleasant companion. The sociable person is drawn to fellowship, converses easily, joins readily in the life of a group and finds genuine satisfaction in shared activity. It is a gift for the collective life of humanity, lying at the root of friendship, cooperation and community, and it has made possible all that civilization builds on the willing association of people. Sociability is not mere talkativeness, for it rests on a genuine interest in others, but it is the natural love of human company that makes society not only necessary but agreeable."),
    "cordiality": ("Cordiality is the warmth and sincerity of feeling with which one greets and treats others, a heartfelt friendliness that goes beyond mere politeness to genuine goodwill. The cordial person receives others gladly, speaking not from form but from true earnestness, and offers welcome, sympathy and encouragement as from the heart. It is felt in the handshake, the tone of voice and the readiness to help, and it is the quality that makes a stranger feel at home. Cordiality is friendship's outward grace, the marriage of warmth and openness that seals good relations and makes hospitality a real rather than an empty word."),
    "solicitude": ("Solicitude is a caring and concerned attention to the welfare of another, a thoughtful watchfulness that seeks to prevent harm and provide help. The solicitous person gives careful heed to the needs and troubles of those under their care, anticipating difficulties and offering comfort before it is asked. It springs from genuine affection and responsibility, and it shows itself in small acts of attention as well as great ones of rescue. Solicitude is the practical face of love and friendship, lying close to concern, tenderness and vigilance, and it is what makes the cared-for feel safe and valued in the world."),
    "consideration": ("Consideration is thoughtful and caring regard for the feelings, needs and interests of others, together with the habit of thinking before acting so as not to offend or inconvenience. The considerate person remembers the preferences and sensitivities of companions, makes room for them, and refrains from word or deed that would needlessly hurt them. It is one of the simplest and most powerful of social virtues, for it costs little and confers comfort out of proportion to its size. Consideration is kindness made practical and foresight applied to manners, and it is the foundation upon which civility, tact and genuine courtesy are all built."),
    "urbanity": ("Urbanity is the polished refinement and suave courtesy of manner that comes of life in a cultivated society, an easy and sophisticated charm in both speech and deportment. The urbane person is at ease in all company, tactful in delivery and free from both the clumsiness of the provincial and the stiffness of the pedant, making even difficult exchanges smooth and pleasant. It is the graceful culture of manners, combining civility with wit and polish with warmth. Urbanity is the ornament of civilized life, for it is the ease of the world refined into a courtesy that puts every interlocutor at their ease."),
    "courtesy": ("Courtesy is the courteous and considerate behavior that shows politeness, respect and good manners toward others, the practiced grace of civil society that greases the wheels of daily dealing. The courteous person speaks and acts with due regard for the comfort and dignity of those met, observing the small decencies of word and gesture that make intercourse smooth and pleasant. It proceeds from an inner disposition of respect as well as outer form, and it is the cheapest and most available of all the graces, open to rich and poor alike. Courtesy is the everyday school of morality, for in its small acts of deference and kindness the citizen practices the larger virtues."),
    "etiquette": ("Etiquette is the customary code of polite behavior governing social interaction, the body of rules that prescribes how one should behave at table, in formal occasions, in correspondence and in the thousand small ceremonies of civil life. It exists to spare awkwardness and to show respect, marking out the conduct that keeps society from jarring friction and giving form to courtesy. While etiquette may be a matter of mere convention, and while its details vary by time and place, its spirit is universal, for it is politeness reduced to agreed practice. There is subtle wisdom in etiquette, for knowing and observing its forms is a way of showing that one cares enough about others to be at pains for their comfort."),
    "tact": ("Tact is the delicate and sure sense of what to say and do in the presence of others so as to avoid giving offence, causing embarrassment or bruising feelings, while still achieving one's own purpose. The tactful person has a ready perception of the moods, sensibilities and circumstances of those around them and shapes speech accordingly, knowing when to be silent, when to defer and how to frame an unwelcome truth kindly. It is a quick and social intelligence, closely allied to discretion and diplomacy. Tact is what allows a person to be honest without being hurtful and considerate without being false, and it is among the most valued arts of practical life."),
    "polish": ("Polish is the quality of smoothness, refinement and cultivated finish in manners, style or performance, the last burnish that removes the rough and crude from what one does and how one appears. A polished speaker, writer, performer or manner has passed beyond mere competence into an almost effortless smoothness, free from awkwardness and false notes. It is acquired by training, practice and taste, and it distinguishes the finished from the merely adequate. Polish must be distinguished from shallowness, for the truly polished retain substance beneath the gloss. It is the sheen of culture, the civilized grace that makes excellence both effective and agreeable."),
    "mannerliness": ("Mannerliness is the habitual practice of polite and respectful behavior, the easy and consistent observance of good manners in the ordinary run of life. The mannerly person behaves with courtesy as a matter of course, greeting, listening, thanking and deferring naturally, so that good conduct becomes second nature rather than a strain. It is the outward or habitual form of civility, distinct from the inward disposition of courtesy though normally its companion. Mannerliness smooths every interchange, for it signals respect for others in each small transaction, and it is among the first lessons of upbringing and the surest marks of a civilized person."),
    "propriety": ("Propriety is the quality of being fitting, proper and decent, whether as conformity to the established rules of acceptable behavior or as the inner fitness of means to ends and conduct to circumstance. The propriety of an action lies in its accord with what decorum, good sense and the expectations of a well-ordered society require, so that nothing offends by being out of place. In persons, propriety shows as a reserve and correctness of demeanor that keeps within proper bounds of modesty and seemliness. Propriety is the guardian of social harmony and the sense of what is appropriate, quietly keeping the world of conduct in its right order."),
    "decency": ("Decency is the quality of conforming to accepted standards of modesty, fairness and good behavior, and of manifesting a basic respect for what is proper and humane. The decent person behaves toward others with honesty, fairness and a regard for their feelings, and conducts himself or herself with appropriate modesty and decorum. It is the moral floor of a civil society, the standard below which conduct should not fall, and it has both a public and a private face, governing how one treats strangers and how one behaves when unobserved. Decency is the quiet price of living together, and its presence is what makes ordinary human life reasonably safe, fair and tolerable."),
    "composure": ("Composure is the settled calmness and self-possession with which one meets excitement, disturbance or crisis, keeping the mind unflustered and the manner steady. The composed person is not easily thrown into agitation, retaining command of thought, speech and action even under stress or surprise. It is a state of collected equanimity that arises from strength of temperament, self-confidence and preparedness, and it is the opposite of fluster and agitation. Composure is what enables clear judgment and steady hands in time of trouble, and it is cultivated by practice, discipline and the habit of keeping one's attention on the matter in hand rather than on passing alarm."),
    "repose": ("Repose is a state of rest, calm and quiet, free from disturbance, agitation or labor, whether of body or of mind. It is the tranquil relief that follows work and toil, and the dignified stillness that a face or a landscape can wear in its untroubled calm. In the deeper sense it is peace of mind, the inner quiet of a soul at rest with itself and its circumstances, which is the reward of a well-ordered life. Repose is not idleness or stagnation, for it is the necessary breathing space that restores strength for action; it is the settled quiet that lets a person return to the world refreshed and unanxious."),
    "placidness": ("Placidness is the quality of being calm, peaceful and untroubled, with a mild and even temper that is not easily ruffled or provoked. The placid person meets the ordinary currents of life with a serene and undisturbed easiness, neither quick to anger nor apt to be flustered. It is the gentle counterpart of patience and composure, more like the stillness of a smooth lake than the guard of a sentry. Placidness must be distinguished from sluggishness, for the placid can be active and capable while remaining outwardly calm. It is the even-minded sweetness of disposition that makes its possessor a haven of quiet in a world of noise."),
    "imperturbability": ("Imperturbability is the quality of remaining calm and unshaken under any circumstance, however trying, exciting or surprising, so that one's composure is never disturbed from without. The imperturbable person keeps an even keel through success and failure alike, meeting temptation, provocation and calamity with the same stoic and level ground. It is the deepest form of self-possession, an unshakable calm that arises from a firm spirit, a disciplined mind and a settled scale of values. Imperturbability is not insensibility, for the imperturbable feel keenly, but it is the mastery that keeps feeling from destroying judgment, and it is the serenity of the unswayable soul."),
    "frankness": ("Frankness is the open, honest and unreserved directness with which one speaks one's mind, free from hiding, evasion or deceptive politeness. The frank person says what they truly think and mean, plainly and clearly, without pretense or equivocation, dealing straight with others and expecting the same in return. It is the quality that makes dealings transparent and inquiries answerable, and it is prized in friendship, business and deliberation. Frankness must be distinguished from rudeness or harshness, for true frankness is compatible with kindness and tact, speaking the truth plainly but not needlessly woundingly. It is the candor of the honest heart, and it is the foundation of trust between people."),
    "plain-spokenness": ("Plain-spokenness is the quality of speaking in a direct, simple and forthright manner, without flourish, ambiguity or evasion. The plain-spoken person says what is meant in plain language that all can understand, wasting no words on ornament or dodge. It is the plainness of the field and the market rather than the court, and for that reason it carries a conviction that flowery speech often lacks. Plain-spokenness is valued in soldiers, scientists and honest friends, who trust the unadorned word because it has nothing to hide. It is sincerity made eloquent through simple speech, and it stands in fruitful contrast to the evasions of diplomacy."),
    "openheartedness": ("Openheartedness is the quality of being candid, generous and unreserved in one's affections and dealings, wearing one's heart on one's sleeve and meeting others with frank warmth. The open-hearted person hides little, keeps no grudging reserve, and gives of time, feeling and help freely as the moment requires. It is the frankness of the affections joined to genuine generosity, and it makes its possessor transparent, approachable and easy to trust. Openheartedness must be distinguished from indiscretion, for it is fullness of feeling, not want of prudence, and at its best it is the very opposite of the cold, calculating secrecy that poisons relationship."),
    "artlessness": ("Artlessness is the quality of being free from cunning, guile or artifice, natural and unstudied in manner, and innocent of display or design. The artless person acts and speaks simply, without craft or pretension, behaving as spontaneously and openly as a child apart from a wish to impress or deceive. In a person it is simplicity of nature, and in a performance or piece of work it is an unaffected ease that conceals its own skill. Artlessness is the charm of transparency, but it must be distinguished from artlessness properly so called; it is not lack of skill but the absence of deceit, and it is counted a lovely rather than a naive quality."),
    "candidness": ("Candidness is the quality of being honest and outspoken in stating what one truly thinks or sees, free from hypocrisy, reserve or the bias of self-interest. The candid observer or adviser gives a fair and unbiased report, speaking honestly about merits and faults alike, unswayed by favor or fear. It differs from frankness in stressing the impartial accuracy of the report as much as the plainness of its delivery. Candidness is the virtue of the honest witness and fair critic, the openness that lets truth be heard, and it is indispensable in counsel, judgment and friendship, where nothing is so useless as pleasing deceits."),
    "bluntness": ("Bluntness is the quality of speaking or dealing with an abrupt and forthright directness that makes little effort to soften or disguise, so that one's meaning is plain even when it stings. The blunt person says exactly what is on the mind, without the polite hedging that might spare the hearer's feelings, which can be refreshingly honest or needlessly wounding depending on the occasion. It is the rough honesty of the plain speaker and straight dealer, prized in urgent counsel where plain truth is needed. Bluntness must be tempered with tact, for served cold without regard for others it can pass into rudeness, but used aright it is the antidote to flattery and evasion."),
    "outspokenness": ("Outspokenness is the quality of speaking one's mind freely and boldly, without afraid of the consequences, often to state what is true, critical or unpopular. The outspoken person refuses to remain silent on matters that ought to be discussed, saying openly what others only whisper, and so is frequently the one to raise the uncomfortable question. It is frankness pushed to the point of public and fearless expression, and it is vital to liberty, for without the outspoken the abuses of power go unchallenged. Outspokenness must be balanced with judgment, for freely spoken does not mean heedlessly spoken, but it is a quality without which conscience remains mute and inquiry stalls."),
    "straightforwardness": ("Straightforwardness is the quality of being honest, direct and without guile in one's dealings, going straight to the point and acting plainly rather than by crooked means. The straightforward person avoids the hidden designs, evasions and double-dealing that complicate trust, saying plainly what is meant and doing plainly what is promised. It makes one's character legible to others and one's word reliable, the very opposite of deviousness or obliquity. Straightforwardness is prized in dealing, friendship and judgment, for it spares others the labor of guessing one's real intent, and it is the steady virtue of the honest and undecent person."),
    "upstandingness": ("Upstandingness is the quality of being honest, morally upright and respectable, standing firmly for what is right in character, conduct and reputation. The upstanding person keeps an unimpeachable character, meets obligations squarely, and neither takes low advantage nor submits to corrupt practice, so that his or her standing in the community rests on well-deserved trust. It is probity made visible and dependable, the integrity that others can count on over the long run. Upstandingness is the citizen's virtue, the inward worth matched to outward good name, and it is the moral example that gives a society its steadiness."),
    "truthfulness": ("Truthfulness is the steady disposition to speak and act in accordance with truth, to tell what is true, to keep promises and to refrain from deception. The truthful person conforms words and deeds to reality, so that others may rely on what they hear and see from him or her without constant doubt. It is the foundation virtue without which trust, and with it all commerce of society, becomes impossible, and it is accordingly ranked among the first duties in every serious ethical system. Truthfulness is not merely the negative avoidance of lies but the active service of honesty, and its costlessness in ease is far outweighed by the confidence it builds."),
    "accuracy": ("Accuracy is the quality of being exact, correct and free from error, whether in statement, measurement, calculation or description, so that what is said or done corresponds precisely to the fact. The accurate person, instrument or account gives the true and exact figure, the correct detail, the faithful rendition, without approximation or distortion. It is achieved by care, attention and the disciplined checking of one's work, and it is the standard of the sciences, of bookkeeping and of every reliable report. Accuracy is the servant of truth, for it is exactness of the particulars that makes a whole statement dependable, and it is the quiet excellence that builds trust."),
    "competence": ("Competence is the possession of the necessary knowledge, skill and ability to perform a task or fill a role to an acceptable standard, the practical command of one's craft that lets theory issue in capable work. The competent person knows what to do and can actually do it, combining understanding with reliable execution, and so is trusted with responsibilities that the merely confident cannot bear. It is acquired by training, practice and experience, and it is attested only in performance, not in claim. Competence is the working dignity of the skilled, and it is the foundation of all merit, for good intentions and bold words are nothing without the power to bring them about."),
    "industry": ("Industry is steady and assiduous application to work, the habit of using one's time and energies for productive and useful labor rather than idle repose. The industrious person works diligently and systematically, persisting in tasks without slackening or procrastination, and so accomplishes far more than the talented but lazy. It is the virtue of the artisan, the scholar and the builder, and it is the engine of all earthly progress, whether in a craft, a trade or a profession. Industry must be matched with judgment, for sheer busyness can waste energy in wrong directions, but rightly directed it is next to talent in securing distinction and prosperity."),
    "sedulousness": ("Sedulousness is the quality of working with persistent care and diligence, applying oneself attentively and untiringly to the task in hand until it is done. The sedulous person does not merely labor hard but labors carefully and constantly, giving close and sustained attention to the details of the work rather than hurrying it through. It goes a step beyond industry in stressing the patience and assiduity with which a task is pursued to completion. Sedulousness is the mark of the serious craftsman and the devoted scholar, to whom the slow accretion of careful effort brings results that dash and genius alone cannot achieve, and it is the quiet workhorse of all lasting accomplishment."),
    "exactness": ("Exactness is the quality of being precise and correct in every particular, matching one's statement, measure or work to the fact with no departure or looseness. The exact person, instrument or account admits no approximation, giving the precise figure, the correct word, the faithful detail. It is a stricter, more rigorous quality than mere accuracy, reaching for the very point of truth in measurement, language and record. Exactness is demanded of the scientist, the surveyor, the copyist and the accountant, and it is cultivated by careful attention and the habit of verifying. In matters where small errors compound into great ones, exactness is not pedantry but prudence."),
    "scrutiny": ("Scrutiny is the close, searching and careful examination of something, with a view to discovering its true nature, faults or worth rather than resting content with appearances. To subject a matter to scrutiny is to look at it minutely and critically, checking every claim, figure or detail and allowing no defect to pass unnoticed. It is the method of the careful auditor, the watchful inspector and the sober judge, and it tempers trust with verification. Scrutiny may be the strict and patient attention that prevents error and fraud, or the rigorous public examination that keeps power and practice honest. It is the discipline of looking twice and looking closely."),
    "observance": ("Observance is the careful and faithful keeping of laws, rules, customs or religious duties, together with the attentive respect paid to occasions, persons and conventions. The observant keeper of rules does not merely know them but honors them in practice, celebrating what ought to be celebrated and abstaining where duty requires. It is the outward respect that gives order and solemnity to life, from the observance of a feast day to the observance of a treaty or the rites of mourning. Observance binds communities across time, for it keeps the traditions alive that a people's ceremonies and obligations embody, and it is the loyalty of the faithful to the forms that hold them together."),
    "punctiliousness": ("Punctiliousness is the strict and fussy attention to the smallest details of form, etiquette or duty, a meticulous care that observes every nicety of ceremony and exactness of obligation. The punctilious person never overlooks a point of honor or a rule of etiquette, being precise even about matters that others would pass by as trivial. It is closely allied to scrupulousness and exactness, and in the affairs of ceremony, diplomacy and law such care preserves due respect and propriety. Punctiliousness can become an excessive and irritating pedantry when carried beyond its purpose, but within bound it is the guardian of the formal courtesies and standards that keep poise in their right order."),
    "scrupulousness": ("Scrupulousness is the careful and conscientious exactness with which one attends to duty, honesty and the finer questions of right and wrong, not content with a loose or easy conscience. The scrupulous person is at pains to keep every promise, to deal with strict fairness, and to avoid even the appearance of wrongdoing or neglect. It is the vigilance of a tender conscience, the exactness of the honest soul, and it is prized in every trust where integrity over the small as well as the great is required. Scrupulousness can harden into an over-anxious or too-nice rigor, but its proper fruit is that tested probity which others can safely rely upon."),
    "punctuality": ("Punctuality is the habit of being exactly on time, of arriving at or doing an appointed thing at the appointed hour, neither early enough to waste nor late enough to keep others waiting. The punctual person respects the time of others as their own, honoring engagements and appointments with reliable exactness. It is one of the small but significant marks of good character, for it shows order, consideration and the keeping of one's word, and it is the courteous and efficient cousin of good timekeeping. Punctuality enables the smooth working of every plan that depends on many people, and its lack, chronically indulged, is a quiet disrespect that reads as unreliability."),
    "promptness": ("Promptness is the readiness and speed with which one answers a call, seizes an opportunity or performs a duty, acting at once rather than delaying or dallying. The prompt person does not put off to a later hour what can properly be done now, and responds to summons, bargains and emergencies with becoming dispatch. It is the practical excellence that complements punctuality, turning readiness of will into action in good time and often catching fleeting opportunity by the forelock. Promptness shows that one's word and willingness are to be depended upon, and it is the favorite virtue of those who would not have deliberation outrun decision and lose the occasion."),
    "deliberation": ("Deliberation is careful and unhurried consideration of a matter before acting or deciding, weighing the reasons, consequences and alternatives so as to choose well rather than to rush. The deliberative person does not proceed on impulse or first impression but turns the question over, consulting judgment and evidence before making up the mind. It is the caution that lies between rash haste and paralyzing doubt, and it is essential to prudence, to justice and to sound statesmanship, where a decision too quickly made is often a decision wrongly made. Deliberation is the pause that lets reason catch up with desire, and its fruit is wisdom and reliable choice."),
    "circumspection": ("Circumspection is the careful looking about on every side before acting, a prudent and vigilant wariness that surveys the circumstances, risks and possibilities so as not to be taken unawares or to act blindly. The circumspect person proceeds with caution, keeping watch over both opportunities and dangers, and so avoids the errors of the heedless and the overconfident. It is prudence in its attitudinal aspect, the constant habit of paying attention to the whole situation rather than to a single favorable fact. Circumspection is the watchfulness of the wise, and it is what keeps boldness from becoming rashness and hope from becoming delusion."),
    "wariness": ("Wariness is the quality of being cautious and on one's guard, alive to the possibility of danger, deceit or disappointment in dealing with the world. The wary person does not trust blindly or walk heedlessly, but holds a measured reserve until ground for confidence appears, alert to signs of trouble. It is a distrustful and watchful prudence, the wise suspicion that has learned from experience not to take every appearance at face value. Wariness must be distinguished from timidity, for the wary can be bold when warranted; it is rather the refusal to be caught off guard. It is the sentinel of self-preservation, keeping the prudent safe amid the guile and hazard of the world."),
    "providence": ("Providence is the quality of making timely and prudent provision for the future, of foreseeing needs and hazards and laying in the resources and measures to meet them. The provident person does not live merely for the present but saves, plans and prepares, so that sudden misfortune finds them ready rather than unprovided. It is foresight in its practical and protective aspect, the prudence that stores grain against the winter and lays up strength for the rainy day. Providence is the virtue of the wise householder and the farsighted statesman, and it is the prudent answer to the unpredictability of fortune. It springs from reflection on the future and it shields its possessor from the worst blows of chance."),
    "anticipation": ("Anticipation is the act of looking forward to and preparing for something to come, a tending of the mind toward the future with expectation or provision. It may be the eager and pleasurable looking-forward to an event, or the practical foresight that acts in advance of a probable need or result. The anticipative mind is ahead of the occasion, ready to receive or to resist what is coming rather than to be taken by surprise. Anticipation is a necessary ingredient of planning, enterprise and hope, for it brings the future into present thought and lets one meet it on one's own terms. It is the attentive forward glance that turns foresight into readiness."),
    "suspicion": ("Suspicion is an instinctive or reasoned distrust of a person, motive or thing, a tendency to believe that something hidden and unfavorable may be the case. The suspicious mind is quick to question appearances and to doubt the good faith of others, sometimes as a safeguard and sometimes to its own cost. In its moderate form suspicion is a form of prudent caution that keeps one from being deceived; in its excessive form it becomes a groundless distrust that poisons relations and corrupts judgment. Suspicion turns readily to both, on evidence or on mere fancy, and it is the painful shadow cast by deceit and the anxious guard of the deceived."),
    "self-restraint": ("Self-restraint is the voluntary hold one places upon one's own impulses, appetites and passions, refusing to act upon every desire or to give way to every provocation. The self-restrained person exercises command over the self, checking the temper, the tongue, the appetite and the urge to take forbidden indulgence, so that conduct is governed by reason and conscience rather than by momentary impulse. It is the practical power behind temperance, patience and continence, and it is the master-virtue of character, for without it no other resolution can be relied upon. Self-restraint is not suppression that wrecks cheerfulness, but the disciplined strength of one who rules the self."),
    "restraint": ("Restraint is the act or habit of holding something in check, of preventing a movement, urge, passion or expenditure from going beyond proper bounds. As applied to persons, restraint is the tempering of action, speech or appetite by deliberation and self-command. It is also applied to things, as the restraint that keeps a horse, a force or a budget from running away with its user. Restraint is the safeguard of every enterprise, for it prevents excess, which is the ruin of all things, and keeps proportion and measure in conduct. Rightly practiced it is prudence and self-control in act, and it is the discipline that lets freedom persist without sliding into license."),
    "measure": ("Measure is the due limit, proportion or balance assigned to anything, whether in extent, degree, conduct or character, and the sense that keeps one within that bound. The word speaks of a fit and fitting quantity, the right amount that neither overreaches nor falls short, and by extension the moderation that observes it. A person who acts with measure takes neither too much of indulgence nor too little of enjoyment, order or effort, and so keeps life in its proper frame. Measure is the golden mean of the ancients, the safeguard against the excess that turns pleasure into pain and ambition into ruin, and it is the constant companion of propriety and good sense."),
    "equilibrium": ("Equilibrium is a state of balance and stability in which opposing forces or tendencies hold each other in check, so that a system, body or mind remains steady and well-poised. In the physical world it is the balance of forces that keeps a structure standing or a scale level; in the mental and moral world it is the even poise of the mind and temper that neither elation nor depression, success nor failure, can upset. The person of equilibrium keeps steady under strain and judicious in judgment, resisting both the pull of panic and the push of overconfidence. Equilibrium is the desired end of self-regulation and composure, and it is the stable footing from which clear thought and sound action issue."),
    "constancy": ("Constancy is the quality of being steadfast and unchanging in attachment, purpose, opinion or loyalty, remaining true to persons, beliefs and courses of action despite temptation, discouragement or the lapse of time. The constant person is reliable in affection and resolved in purpose, neither swayed by novelty nor shaken by difficulty, so that friends, comrades and employers can depend on their devotion holding firm. It is the virtue that gives duration to all the others, for it is constancy that keeps courage, love and honest resolution from being exhausted by delay. Constancy is the steady flame that outlasts both the blaze of first passion and the chill of hard times."),
    "consistency": ("Consistency is the quality of holding together and agreeing with itself, so that one's conduct, beliefs or products are uniform and in accord across time and circumstance. A consistent person acts today as yesterday and believes as he or she speaks, so that others can foresee and rely upon their behavior; consistent reasoning draws the same conclusions from the same premises without arbitrary contradiction. It is the opposite of caprice, fluctuation and self-contradiction, and it is the foundation of clarity and trust in both character and thought. Consistency must not be mistaken for rigidity, for the consistent may revise in the face of new evidence, but the wise consistency lies in dealing with like cases alike and serving one true purpose."),
    "resilience": ("Resilience is the capacity to recover quickly from misfortune, shock, illness or adversity, and to spring back into shape, function and spirit after being bent or broken down. The resilient person, system or community does not merely survive a setback but rebounds from it, adapting and carrying on with strength renewed. It is the elasticity of the healthy mind and body, the property of a material that returns to its form, and figuratively the buoyancy of a disposition that refuses to remain crushed. Resilience is built by experience, support and inner resources, and it is what lets the beaten rise again, the bereaved reach forward, and nations recover from disaster."),
    "recuperation": ("Recuperation is the process of recovering health, strength, energy or position after illness, exhaustion, loss or setback, the gradual return to one's former state of well-being or vigor. The person in recuperation convalesces, regaining strength step by step rather than all at once, and resting and nourishing the powers that have been spent. It is the healing phase that follows injury or strain, whether of the body, the mind or a career, and it demands patience, care and time. Recuperation is the natural partner of the body's self-healing and the spirit's rebound; it is the slow and steady recovery that turns a defeated state into a restored one, and it is as vital to life as exertion itself."),
    "self-reliance": ("Self-reliance is the quality of depending upon one's own powers, judgment and resources rather than leaning on others for what one can do or decide for oneself. The self-reliant person trusts the sufficiency of their own mind and hands, is willing and able to act without constant support, and takes responsibility for the consequences of that independence. It is not the foolish refusal of all help, for the truly self-reliant know their limits and accept just assistance, but it is the sturdy confidence that stands on its own feet first. Self-reliance is the foundation of personal dignity and initiative, and it is what turns capability into achievement and freedom into self-government."),
    "autonomy": ("Autonomy is the right and power of self-government, the condition of being self-directing and free from external control or undue influence in one's own affairs. In persons, autonomy is the capacity to form and act upon one's own choices, to guide conduct by self-chosen principles rather than by coercion, and to exercise that freedom with responsibility. In communities and institutions, it is the self-rule that allows a group to manage its own life within its proper sphere. Autonomy is the political and personal ideal of the free, standing against servitude and imposed rule, and it is the foundation of both personal dignity and political liberty."),
    "persistence": ("Persistence is the continuance of effort toward a goal in the face of obstacles, discouragement or slow progress, refusing to give up when the end is not yet gained. The persistent person returns again and again to the task, trying new means when the old fail, and enduring the long interval between resolve and reward without losing heart. It is the practical stay of ambition and the enemy of giving up, and it lies at the heart of nearly every great achievement, since few valuable ends are gained by the first attempt. Persistence is not obstinate refusal to change when change is wise, but the sturdy patience that keeps striving intelligently, and it is the quality that turns intending into getting things done."),
    "doggedness": ("Doggedness is a stubborn and tenacious persistence that clings to a purpose or course through difficulty, fatigue and repeated failure without surrendering. The dogged person is not easily shaken off, holding on grimly and pressing on steadily even when progress is slow or the odds are poor. It is the quality of a pursuit that refuses to let go, and it is the force behind the slow victories of repair, reform and endurance that flashy effort cannot win. Doggedness is allied to obstinacy but is redeemed from mere stubbornness by being directed at a worthy goal and by working as well as insisting. It is the tenacity of the bulldog applied to the work of life."),
    "perseverance": ("Perseverance is the steady and unremitting continuance in a course of action in pursuit of a purpose, the patient determination to keep going until the object is attained. The persevering person does not turn aside or slacken on the road to a chosen end, enduring delay, disappointment and toil with unshaken constancy. It is persistence refined by steadiness and combined with patience, and it is counted among the surest roads to achievement, for it carries the modest but relentless through what brilliance and luck cannot finish. Perseverance is the staying power of the soul, and many of the greatest works of art, science and reform have been the fruit of its long unglamorous labor."),
    "assiduity": ("Assiduity is constant and diligent attention to a task, the habitual and unremitting application of the mind and hands to one's work or duty. The assiduous person is always at the work, attending to it closely and regularly rather than fitfully, so that steady progress is made by the constancy of the endeavor. It is diligence in the habit of constant care, the quality of the worker whose presence and attention to the task never slacken. Assiduity lies close to industry and sedulousness but stresses the constancy of the attention itself. It is the ornament of the scholar and the foundation of the craftsman, and it is by assiduity that facility and mastery are gradually acquired."),
    "application": ("Application is the close and steady attention and effort directed to a task or study, the deliberate devoting of one's mind and energy to the work in hand. The person of application applies themselves closely and continuously to their object, shutting out distraction and bringing persistent energy to bear, so that progress follows from directed and concentrated effort. It is the act of laying the whole mind upon a task, and it is the practical key to learning and skill, for it converts mere industry into effective attention. Application is the steady force of the self applied to a chosen end, and it is the humble but essential engine of all serious mastery."),
    "thrift": ("Thrift is the careful, frugal and economical management of one's resources, especially money, so that means are not wasted and provision can be laid by for need. The thrifty person spends only where it is needful and worthwhile, avoids extravagance and waste, and sets something aside against the future, so that nothing is lost and the household or purse is kept sound. It is the practical virtue of prudence applied to property, and it is the groundwork of independence, for it is by saving that the poor rise and the comfortable weather hard times. Thrift is not meanness, for the truly thrifty spend freely where it is fitting, but it is the guardian of sufficiency and the enemy of ruinous waste."),
    "economy": ("Economy is the careful and efficient management of resources, expenditure and effort, so that the utmost is obtained for the least unnecessary cost and nothing is wantonly thrown away. As a personal virtue it is the ordering of one's house and means with prudence, avoiding both extravagance and meanness, and as a science it is the art of administering the common resources of a family, business or state. Economy means getting good value for money and sparing energy for what matters, and it is often harnessed to frugality and thrift. It is economy that makes sufficiency secure, efficiency possible and plenty enduring, and it is the prudent steward's first rule. It must not be confused with avarice, for economy aims at fitness of use, not mere hoarding."),
    "husbandry": ("Husbandry is the careful and thrifty management of resources and means, whether of a farm, a household or a fortune, so that they are preserved, improved and used to the best advantage. The good husband cultivates the soil and his assets alike, tending them steadily, spending on them what keeps them productive and never wasting their yield. It combines cultivation, economy and provident care, and it is the term by which the farmer's whole craft is known. Husbandry is the virtue of the careful steward who multiplies what is entrusted to them, and it is the practical art of making resources last, grow and serve their owner and community."),
    "stewardship": ("Stewardship is the responsible management and care of something entrusted to one, whether property, resources, an office, a trust or the natural world, held on behalf of another or of future generations. The good steward does not treat what is committed to his or her care as if it could be recklessly spent, but tends it faithfully, preserves and improves it, and accounts for its use. It is the virtue of the trustee, the manager and the guardian, who serve the true interest of what they hold rather than their own immediate advantage. Stewardship is the ethically charged form of management, calling us to use power and plenty with far-sighted responsibility, and it is the foundation of a just and enduring relation to both property and planet."),
    "beneficence": ("Beneficence is the active doing of well, the habitual disposition to perform good and helpful deeds for others and to contribute to their happiness and welfare. It is more than benevolence, which is the good will or disposition, for beneficence carries virtue into action, actually conferring benefits rather than merely wishing them. The beneficent person seeks occasions to do good, helping the needy, advancing the good of the community and lending strength, means and time to worthy ends. Beneficence is one of the chief of the social virtues, for it is by the concrete help of the beneficent that the suffering are relieved and the quality of collective life is raised."),
    "charity": ("Charity is kindness and generosity of spirit extended to others, especially to the needy, together with the alms, help and compassion that flow from it. In its broadest moral and religious sense charity is that love of one's neighbor which is the root of all good will; in its practical sense it is the giving of relief, aid and support to those in want. The charitable person is moved by another's need to give freely, without contempt or expectation of return, and to judge others with benevolence. Charity is honored as one of the greatest of virtues, for it is benevolence in its warmest and most self-forgetful form, and it is the force that binds a community to the relief of its suffering members."),
    "generosity": ("Generosity is the quality of being ready and eager to give freely of one's means, time, praise or spirit, and of showing a noble largeness of heart rather than a petty clinging to what one has. The generous person gives without grudging, shares goodwill, and resists the mean promptings of avarice and narrow self-interest, meeting the world with open hands and an open mind. It is a liberality that extends beyond money to forgiveness, understanding and encouragement, and it is distinguished from mere lavishness by being governed by good sense and genuine feeling. Generosity warms society and elevates the giver, for it is the hospitality of the heart that makes both giving and receiving glad."),
    "altruism": ("Altruism is the principle and practice of disinterested concern for the welfare of others, acting for the good of others even at some cost or sacrifice to oneself. The altruistic person puts the needs and happiness of other beings ahead of their own advantage, moved by sympathy and duty rather than by self-interest. It is the moral opposite of egoism, and it is the generative force behind charity, self-sacrifice, care of the vulnerable and the building of community. Altruism, even when imperfect, is the ethical summit of social feeling, for it asks what is good for all and for the other, and it is the disposition upon which a humane and cooperative society rests."),
    "magnanimity": ("Magnanimity is greatness of soul, a lofty and generous spirit that rises above petty resentment, meanness and revenge to act nobly even toward those who have wronged one. The magnanimous person holds a large-minded view of life, is above vindictiveness and smallness, forgives readily, and pursues honor and the good rather than advantage. It is close to nobility and generosity of heart, and the ancient philosophers ranked it with the highest virtues, for it is the strength that lets the great of spirit be gentle and the injured be merciful. Magnanimity dignifies victory, softens defeat and raises the whole tenor of a life above the level of pettiness."),
    "forgiveness": ("Forgiveness is the act of pardoning an offender, of giving up resentment and the desire for punishment or revenge against one who has wronged one, and of restoring goodwill toward them. The forgiving person releases the wrongdoer from the burden of his or her guilt in one's own heart, choosing reconciliation over rancor and mercy over strict desert. It is a healing virtue for both parties, freeing the forgiver from corrosive bitterness and giving the forgiven a second start, and it is the answer to the endless cycle of retaliation. Forgiveness is not the same as forgetting or condoning the wrong, but it is the willing surrender of vengeance that restores human relationship."),
    "reconciliation": ("Reconciliation is the restoration of friendly and harmonious relations between persons, parties or groups that were at odds, so that estrangement is ended and a common footing regained. It may follow a quarrel or break between individuals, or a deeper division within a community or between nations, and it requires the mending of trust on both sides. Reconciliation is the positive and forward-looking act that forgiveness makes possible, for while forgiveness releases one from resentment, reconciliation rebuilds the broken bond. It is prized as a healing and peacemaking virtue, the force that turns enemies into companions and divided houses into united ones again."),
    "amends": ("Amends is the reparation or compensation made for a wrong, injury or breach of duty, the action taken to repair the damage one has caused and to set things right again. To make amends is to acknowledge a fault and to do what lies in one's power to undo its ill effects, whether by restitution, apology or corrective effort. It is the practical companion of repentance and apology, for words of regret are hollow without the endeavor to make reparation. Amends restores what was lost or broken, so far as the thing can be repaired, and it is the honest road by which the wrongdoer works back toward the injured party's trust and one's own peace."),
    "peace": ("Peace is the state of tranquility, freedom from disturbance, war or conflict, whether within a person, among people or between nations. Inwardly, peace is the calm serenity of a mind at rest with itself and reconciled to its lot; outwardly, it is the harmonious living of communities in concord and security from violence. It is not mere absence or passivity, for true peace is a positive and ordered good, the quiet fruit of justice, goodwill and the settled arrangements of a well-governed life. Peace is one of the deepest of human aspirations, for it is the condition under which life flourishes, families are secure and the face of society is unclouded by fear."),
    "concord": ("Concord is the state of harmony and agreement among persons, groups or nations, the willing union of hearts and minds in a common understanding or purpose. It is more than mere absence of discord, for concord is a positive accord in which differences are reconciled and there is a settled co-operation. The spirit of concord draws parties together, fosters friendship and community, and keeps the affairs of a household or state running smoothly without civil strife. Concord is the prize of diplomacy and the cement of community, and it is the sweet accord that makes a group more than the sum of its members."),
    "comradery": ("Comradery is the confident trust and good fellowship that grows among companions who share trials, aims or labors together, a warm and easy solidarity that binds those who stand side by side. It is the spirit of the camp, the workplace and the shared enterprise, where mutual reliance and shared experience forge bonds of loyalty and good cheer. Comradery eases hardship by sharing it, and it makes the common even, the effort light and the victory sweeter, because it is borne among friends. It is the social joy of fellowship and the practical support of the group, and it is one of the sweetest comforts of human life."),
    "docility": ("Docility is the quality of being teachable and disposed to learn, that easy and willing readiness to be instructed, guided or directed by those who know better. The docile person is not stubbornly set against new knowledge or advice, but listens with a teachable spirit, takes direction gladly and profits from the experience of others. It is the receptive posture of the learner, the humility that admits one does not yet know, and it is counted the first step of wisdom, for no one can be taught who will not receive teaching. Docility is not weakness or blind obedience, for it is the open mind's willingness to learn, and it is the beginning of every discipline and skill."),
    "obedience": ("Obedience is the act or habit of complying with authority, law, instruction or command, a willing submission of one's will to a rightful rule. The obedient person follows the direction of legitimate superiors, keeps the laws of the community and honors the understandable requirements of order, so that the coordination of collective life goes forward smoothly. It is the counterpart of authority and a foundation of discipline, education and governance. Obedience is not the abdication of conscience, for it is due only to rightful authority and within proper bounds, but where so rendered it is the willing and intelligent compliance that holds families, institutions and societies together."),
    "respectfulness": ("Respectfulness is the quality of showing due consideration and honor toward persons, institutions, opinions, rules and the feelings of others, treating them as having worth that is not to be trifled with. The respectful person observes the proper forms of regard, listens to elders and authorities with attention, honors the individual dignity of everyone, and refrains from contempt and disparagement. It is the disposition that acknowledges the value and rights of that which stands above one's own immediate interest. Respectfulness is the groundwork of courtesy, decency and civility, and it is what makes mutual recognition and peaceful co-existence possible among equals and unequals alike."),
    "veneration": ("Veneration is a deep and reverent respect, approaching awe and worship, felt for what is held particularly sacred, holy or greatly honored, whether a deity, a saint, a founder, an institution or a memoried person. The venerating heart is filled with solemn wonder and gratitude, bowing the mind before an object of surpassing worth and refusing the easy levity that familiarity breeds. It is the highest degree of respect, lying beyond mere reverence in its warmth and seriousness. Veneration preserves the sanctity of what a people holds dearest, and it is the attitude by which the great and holy are kept from being cheapened by the passing of time."),
    "worship": ("Worship is the reverent homage, adoration and devotion rendered to a deity or to what is regarded as supremely worthy, whether in private prayer or public ceremony. It is the act or spirit of ascribing highest honor and glory, an attitude of the whole self before what is held sacred. In its formal sense worship is expressed in the hymns, prayers, rites and observances of a religion; in its widest sense it is the devotion one gives to whatever one holds supreme, be it God, an ideal, a person or a cause. Worship lifts the mind to what is greater than itself and draws the worshiper into communion with the object of deepest reverence."),
    "tenet": ("Tenet is a principle, belief or doctrine that is held firmly as true by a person, school of thought or faith, an article of conviction regarded as fundamental and not to be lightly surrendered. Every religion, philosophy, science and political creed rests on a body of tenets that give it coherence and identity. To hold a tenet is to affirm it as a settled ground of belief and action, even though it may itself rest on faith, evidence or authority. A tenet is the intellectual lynchpin of a worldview, and the steadiness with which holders cleave to their tenets measures both their conviction and their openness to revision."),
    "ambition": ("Ambition is the eager desire for achievement, distinction, honor, rank or power, and the active striving to attain it. The ambitious person sets high ends and pursues them with determination, seeking to rise in the world, to excel in a craft or to command great affairs. It is a driving and double-edged force, for rightly directed ambition raises art, enterprise and the state, while unbridled ambition brings recklessness, envy and the trampling of rivals. Ambition is the spur that has built empires and ruined them, and its worth depends wholly upon the ends it seeks and the means it employs. It is the fuel of great endeavor, and it must be governed by principle."),
    "aspiration": ("Aspiration is a hopeful longing or ambition toward something higher, the reaching of the mind and heart toward an aim, ideal or condition that is not yet attained. The aspiring person looks upward and forward, cherishing elevated hopes and directing effort toward their realization, whether for a career, an excellence, a better society or a nobler self. It differs from idle wishing in that it is usually joined to striving and effort. Aspiration lifts the soul beyond present circumstance and is one of the wellsprings of progress, invention and moral growth, for it is by aspirations that the achievable is gradually pulled down into the reach of the striving."),
    "enterprise": ("Enterprise is the spirit of readiness to undertake new and difficult tasks or ventures, together with the bold initiative and energy with which one sets them in motion. The enterprising person does not wait for opportunity to thrust itself forward but seeks and creates it, launching undertakings, taking measured risks and pushing boldly toward goals. It is the active and adventurous quality of mind that founds businesses, explores frontiers and starts reforms, and it is the engine of progress in every field. Enterprise is initiative armed with resolution, and it is distinguished from mere restlessness by being directed at ends of real effect and pursued with sustained effort."),
    "heroism": ("Heroism is courage, endurance and devotion carried to an extraordinary and self-forgetful pitch, great and noble action in the face of danger, suffering or overwhelming odds. The hero acts for a cause, the safety of others or the promptings of honor beyond the ordinary demands of self-preservation, often at great personal risk. It is the quality that inspires emulation and is celebrated in song and story, and it does not require the battlefield, for heroism appears in the rescuer, the martyr, the exhausted caretaker and the unyielding reformer. Heroism is the summit of valor and virtue, and it is what makes a life memorable beyond its span."),
    "perfectionism": ("Perfectionism is the aspiration to attain the highest standard of excellence and the refusal to be satisfied with anything short of it, whether in one's work, one's self or one's aims. The perfectionist holds an exacting ideal and labors with scrupulous care to reach it, polishing and revising until the result is as flawless as effort can make it. In its healthy form it is the serious pursuit of excellence that produces great craft and meticulous work. In its excessive form it becomes a disabling anxiety, setting impossible standards, magnifying small faults and paralyzing action. Perfectionism, properly tempered, is the virtue of the finished and excellent; unbalanced, it is the enemy of completion and peace."),
    "excellence": ("Excellence is the quality of being surpassingly good, the possession of great merit and the attainment of a high degree of skill, virtue or worth in some field or respect. The excellent thing or person stands above the ordinary by the superior fineness of its qualities, whether in craft, intellect, conduct or art. Excellence is not a single act but a sustained standard, the habit of doing well what one sets out to do, and it is pursued through discipline, care and the steady expectation of one's best. It is the goal of all serious training and the reward of those who refuse mediocrity, and it shines by merit rather than by display."),
    "worthiness": ("Worthiness is the quality of being deserving of esteem, trust or reward, the possession of merit that fits a person or thing for good opinion, honor or a particular end. It rests on genuine desert rather than on wealth, rank or claim, for the worthy are good enough in character and deed to be looked up to and relied upon. Worthiness may be applied to persons who by virtue and conduct have earned respect, to causes that deserve support, and to objects that justify their value. It is the solid foundation of reputation, for those proved worthy are honored not as a favor but as a due, and it is the desert of the truly good."),
    "capability": ("Capability is the power, skill or ability to do something, the quality of being capable of performing a task, achieving an end or meeting a challenge. It is the practical potential that combines natural talent, training and fitness, and it is proved in performance rather than claimed in words. A capable person, machine or system can be relied upon to do the work required, and capability is the measure of effective power available for a purpose. It is the general name for the ability that makes competence actual, and it underlies all achievement, for what one cannot do one cannot accomplish, however great the intention."),
    "versatility": ("Versatility is the ability to adapt readily to many different tasks, roles or situations, and to turn one's hand to a wide range of employments with skill. The versatile person is flexible in talent and preparation, equally at ease in diverse fields, and able to meet the changing demands of circumstance by shifting method and role without loss of competence. It is the quality of being many-sided, the talent that can be applied in more than one direction, and it is the prized resource of the leader, the teacher and the creative mind. Versatility is not shallowness, for it rests on real ability in each direction, and it is the flexibility that keeps one useful as conditions change."),
    "flexibility": ("Flexibility is the quality of being able to bend, adapt or be changed in response to new conditions without breaking, whether of body, mind or arrangement. In the body it is suppleness of limb; in the mind it is openness to new ideas and the readiness to revise plans or opinions; in things it is the capacity to be bent or adjusted to different uses. The flexible person is not rigid or brittle, but can accommodate change, compromise and surprise with ease, adjusting means without abandoning ends. Flexibility is the practical virtue of adaptability, and it is what allows individuals and institutions to survive and thrive amid change."),
    "adaptability": ("Adaptability is the capacity to adjust oneself, one's plans or one's methods to new conditions, environments or demands, so as to continue functioning well as circumstances alter. The adaptable person reads the changed situation and responds fittingly, altering approach, timing or role with readiness rather than clinging to what no longer serves. It is the intelligence of the organism and the mark of the resilient, for nature itself favors those who can change to meet the world. Adaptability is not surrender of principle, for one may hold the same ends while changing the means, and it is the practical key to survival and success in a shifting world."),
    "inventiveness": ("Inventiveness is the quality of being productive in new ideas, devices, methods or expressions, the readiness of mind to devise what has not been made or thought before. The inventive person is fertile in resource, quick to find original solutions, and able to see connections and possibilities that escape the routine eye. It is the wellspring of discovery, art and technology, and it combines imagination with practical sense, for the invention must not only be conceived but made to work. Inventiveness is not the same as mere novelty, for it must prove useful as well as new, and it is the creative force that pushes human power and understanding forward."),
    "creativity": ("Creativity is the power of the mind to bring into being something new and original, whether a work of art, a discovery, a design or a fresh way of seeing things. The creative person does not merely reproduce or repeat but transforms, combining elements in novel ways and giving birth to what did not exist before. It draws on imagination, insight and the willingness to break with the familiar, and it is the source of all art, invention and cultural progress. Creativity is not the possession of a gifted few alone, for it is a capacity to be cultivated, and it is what makes human beings able to remake their world rather than merely endure it."),
    "originality": ("Originality is the quality of being new and independent in thought, imagination or expression, of proceeding from one's own mind rather than from imitation or precedent. The original person or work is marked by a fresh and native character, owing its distinctive features to its own invention and not to the copying of others. It is the power to see and do what has not been merely borrowed, and it is the element of genius that gives the world underived truth and beauty. Originality is not the pursuit of novelty for its own sake, for the genuinely original is also sound and serviceable, but it is what keeps each contribution from being a mere repetition of the past."),
    "ingenuity": ("Ingenuity is the quality of being clever, original and resourceful in devising ways to meet needs, solve problems or achieve ends, the skill of the mind in constructing effective contrivances. The ingenious person sees the way round an obstacle or the means to a purpose that escapes the plodding, turning available materials and knowledge to brilliant account. It is a union of intelligence, imagination and practical wit, and it is the quality that makes the inventor, the strategist and the resourceful problem-solver. Ingenuity is the art of finding the cunning path, and it is the practical genius that turns obstacles into opportunities."),
    "resourcefulness": ("Resourcefulness is the ability to find quick and clever ways to overcome difficulties or to supply a need, making the most of whatever means are at hand even when they are scarce or inadequate. The resourceful person is ingenious in emergencies, improvises solutions, and turns apparent lacks into advantages by wit and enterprise. It is the practical intelligence of the improviser and the survivor, who is never long at a loss because they can see and create the means to an end from slender materials. Resourcefulness is resourceful efficiency in crisis, and it is the capability that enables someone to cope and prevail when conditions are against them."),
    "pragmatism": ("Pragmatism is the practical and matter-of-fact approach to problems that judges ideas, policies and actions chiefly by their practical consequences and actual working rather than by abstract theory or fixed principle. The pragmatist asks, in effect, whether a course works in practice and serves real ends, and is ready to try whatever is effectual, setting aside doctrinaire attachment to any single scheme. It is the temper of the practical man and a major philosophy of the nineteenth and twentieth centuries, and it prizes outcome over orthodoxy. Pragmatism must be guarded against the mere expediency that abandons all principle, but within bounds it is the working wisdom that gets real results."),
    "sobriety": ("Sobriety is the quality of being sober, serious and self-controlled, whether in the literal sense of freedom from intoxication or in the figurative sense of a grave and steady temper of mind. The sober person is moderate in appetite, calm in judgment and free from the extravagance of illusion or excessive emotion, keeping a level head in the midst of excitement or temptation. It is the bodily and mental counterpart of temperance, and it is essential to clear thought and sound decision. Sobriety, properly understood, is not the dullness that denies all pleasure, but the steady self-command that refuses to let appetite or passion cloud the mind."),
    "soundness": ("Soundness is the quality of being free from defect, error, decay or unsoundness, whether in body, mind, judgment, argument or material structure. A sound body is whole and healthy, a sound mind is sane and well-balanced, a sound argument is valid and well-grounded, and a sound investment or structure is reliable and secure. Soundness implies solidity, reliability and the absence of hidden weakness, and it is the quality that lets a thing be trusted to stand and to work. In character, soundness is the trustworthy good sense and integrity of one on whom reliance is not misplaced, and it is the foundation of all durable confidence."),
    "wholesomeness": ("Wholesomeness is the quality of being healthful, sound and morally beneficial, whether of food, conduct, environment or character, so that what is wholesome makes for the good of body and mind. Wholesome things heal, nourish and strengthen rather than corrupt or harm, and wholesome people are of a pure and healthy disposition that is good for others to be near. It suggests a natural and unspoiled freshness that is free from what is noxious, morbid or depraved. Wholesomeness is the healthiness of the normal and the good, and it is prized in food, teaching and company alike as that which builds up rather than tears down."),
    "vitality": ("Vitality is the state of being full of life, vigor and energy, the native strength and liveliness that animates body, mind and spirit. The vital person possesses abundant energy and zest, moving with life and quickness and meeting the demands of the day with a fund of power. Vitality is the very force of life itself, and it shows in health, animation, stamina and a buoyant presence that is felt by others. It is the reserve of strength that sustains effort and resistance to fatigue, and the inner flame that gives color and impetus to all one does. Vitality, though partly a gift of constitution, is kept and increased by healthy living and active use."),
    "vigor": ("Vigor is the active power and force of body or mind, the energetic strength with which one acts, works or thinks, free from languor and weakness. The vigorous person is strong and brisk in action, applies force and spirit to what is done, and shows a healthy robustness of constitution and exertion. It is energy in motion, the muscular strength of the body and the quick force of the mind, and it is the quality that makes effort telling and life effective. Vigor is related to vitality but points more to the active exercise of strength than to the mere fund of life, and it is the force that carries undertakings through to fulfillment."),
    "spunk": ("Spunk is courage and spirit, a plucky and lively boldness in meeting difficulties, danger or challenge, with a touch of fire in the temper. The person of spunk is not easily cowed, answering discouragement with spirit and setbacks with renewed determination, and often showing a cheerful defiance of odds. It is a bracing and spirited courage, more familiar and rough-hewn than lofty heroism, and it is the grit that gets one through scrapes and keeps one fighting when the heart would flag. Spunk is the fire of the plucky, and it is the quality that makes the underdog refuse to be counted out."),
    "fiber": ("Fiber, in its moral sense, is the inherent strength and stamina of character, the firm inner sinew of one's nature that underlies conduct and endurance. A person of strong fiber has a well-forged constitution of mind and will, able to bear strain, resist corruption and hold a course because the very grain of their character is sound and tough. It is the substance of moral and physical backbone, the quality that there is in a person when tested, and it is often contrasted with weakness or flaccidity. Fiber is the hidden mettle of a person, the fabric of resoluteness and principle that determines how they will wear under the stresses of life."),
    "grit": ("Grit is firmness of character and indomitable spirit, the stubborn courage and perseverance that keeps one going in the face of hardship and long odds. The gritty person has toughness of mind and will, refusing to quit when discouraged, weary or beaten down, and pressing on with unyielding resolve. It is the quality of the plainsman and the pioneer, the refusal to be broken, and it is seen in those who chip away at a hard task day after day until it yields. Grit is perseverance mixed with courage and stamina, and it is what separates those who finish long struggles from those who abandon them."),
    "panache": ("Panache is a flamboyant and dashing manner, the spirited and confident flair with which one carries oneself, speaks or acts, so that style itself becomes a kind of power. The person of panache performs with bravura, adding tasteful flourish and a touch of dramatic bravado to what might otherwise be plain, and so commands attention and admiration by sheer spirited manner. It is the art of doing things with dash, of making even the ordinary seem vivid and gallant. Panache must be distinguished from mere ostentation, for true panache is carried easily and with self-possession, and it is the confident grace that turns action into performance."),
    "intrepidness": ("Intrepidness is the quality of being fearless and undaunted in the face of danger, difficulty or risk, a bold courage that presses forward without being checked by threats or alarms. The intrepid person shows no sign of fear, meeting peril with steady nerve and resolute action, whether in adventure, exploration, battle or the hazards of duty. It is a lofty and dauntless valor, stronger than mere bravery in its suggestion of utter freedom from fear. Intrepidness is the courage of the bold spirit that refuses to be deterred, and it is the quality of those who venture where others dare not and persist where others retreat."),
    "daredevilry": ("Daredevilry is reckless and showy daring, the bold and often foolhardy courting of danger for excitement, adventure or applause. The daredevil delights in taking extraordinary risks, performing feats that the cautious would refuse, and flaunts a contempt for fear that can be thrilling or alarming. It is courage without the ballast of prudence, a spirit of adventure carried to the point of heedlessness, and it is as likely to end in a triumph of nerve as in disaster. Daredevilry is the bright and dangerous side of boldness, and while it may entertain and impress, it is to be admired with caution and never mistaken for the sober valor of the hero."),
    "fearlessness": ("Fearlessness is the absence of fear, the state of being without dread or apprehension in the face of danger, difficulty or the unknown. The fearless person is not driven back by threats or panic-stricken by peril, but meets what comes with a calm and steady courage. Fearlessness may proceed from native hardihood, from faith, from ignorance of danger or from the mastery of fear by a disciplined will. It is the ground on which bravery stands, though courage is nobler, for courage acts in spite of fear while fearlessness is untroubled by it. Fearlessness is the composure of the hero's spirit, and it is both a gift of temperament and an attainment of resolution."),
    "audacity": ("Audacity is bold and daring presumption, a fearless and often cheeky readiness to venture into what others would not dare, or to assert what others would not presume. The audacious person is venturesome and forward, unafraid to attempt the difficult, challenge the established or seize an opportunity, and can carry off with nerve what shyness or caution would shrink from. It is courage with a touch of impudence, and it is sometimes admirable in the pioneer and reformer, sometimes reckless or offensive in the insolent. Audacity is boldness pushed past prudence, and its moral worth depends wholly on what it dares and how."),
    "temerity": ("Temerity is reckless boldness or rash presumption, the imprudent daring that rushes into action or speech without due regard for the risks or consequences. The person of temerity ventures where prudence would counsel caution, and is apt to undertake what is beyond their power or disturb what should be left alone. It is courage without the counterpoise of judgment, and it is the mother of many a disaster, for the rash and the foolhardy buy their boldness with loss. Temerity is audacity in its most dangerous form, and it stands in direct opposition to the well-considered courage of the wise."),
    "rashness": ("Rashness is the quality of acting too quickly and without sufficient thought, of rushing into decisions or undertakings before the facts are weighed and the consequences foreseen. The rash person is hasty and precipitate, governed by impulse rather than reflection, and so is prone to errors from which deliberate action would have saved them. It is the vice opposite to prudence and deliberation, and it is attended by overconfidence and the neglect of necessary caution. Rashness has ruined many a plan and person, and its remedy lies in the acquired habit of pausing to consider before one leaps."),
    "understanding": ("Understanding is the power to perceive the meaning, nature or significance of something, and to grasp how things are related and why they happen. It goes beyond mere knowledge of facts to a grasp of connections and causes, so that the understanding person comprehends not only that a thing is so but why it is so. It is the faculty that interprets, explains and reckons, being the active and insightful faculty of the intelligence. Understanding is also used of the sympathetic and careful comprehension of another's position or feelings, and in this sense it is the ground of kindness and forbearance. It is the deepest and most generous form of intelligence."),
    "perception": ("Perception is the act of becoming aware of something through the senses, or the intuitive and quick recognition of a truth, quality or situation. It is the mental process by which the mind takes in and interprets the impressions of the world, and in its keener sense it is the insight that sees what is not obvious to the inattentive eye. The perceiving mind notices detail, reads meaning into events and detects the reality beneath appearance. Perception is the gateway of all knowledge, for without the faithful registering of what is before us neither thought nor skill can begin, and sharpened perception makes the difference between the acute and the dull."),
    "acumen": ("Acumen is sharpness of mind or quickness of perception, the keen and penetrating intelligence that sees quickly into the heart of a matter and makes sound, shrewd judgments. The person of acumen is alert and penetrating in practical affairs, unerringly spotting the essential point, the hidden motive or the promising opportunity that escapes slower minds. It is the sagacious skill of the capable judge, the successful merchant and the effective strategist, combining insight with worldly shrewdness. Acumen is the fine edge of intelligence, and it is the quality that turns knowledge into decisive and profitable understanding."),
    "shrewdness": ("Shrewdness is keen-witted and practical cleverness in business and worldly affairs, a sharp and often crafty estimate of persons and situations that knows how to turn them to one's advantage. The shrewd person is astute and hard to deceive, quick to see the practical worth of things and the likely moves of others, and expert at driving a favorable bargain. It is a worldly intelligence tinged with cunning, and it is as often used to advantage as it is admired. Shrewdness, at its best, is insight steered by prudence; at its worst, it passes into the sharp practice of the overreacher, and its value depends on the honesty of its ends."),
    "canniness": ("Canniness is the quality of being shrewd, cautious and astute in practical matters, combining native cleverness with a wary good sense of one's own interest. The canny person is not easily fooled, keeps a sharp eye on the main chance, and avoids being taken in either by others or by their own hopes, so that he or she deals with the world on favorable and safe terms. It is a deft and prudent cunning, characteristic of the experienced and quick-witted in the world of affairs, and it is the practical wisdom of the clever and the saved. Canniness is shrewdness made steady by caution, and it is the sure-footed intelligence of the careful trader of life."),
    "judiciousness": ("Judiciousness is the quality of having or exercising sound judgment, of weighing matters with prudence and good sense and coming to wise and well-balanced conclusions. The judicious person is marked by a soundness of counsel and a discretion that takes account of all relevant considerations, avoiding both the rash and the weak, and settles on what is fitting and right. It is more than cleverness, for it is the application of intelligence to choice, the wise ordering of means in relation to ends. Judiciousness is the virtue of the good judge, counselor and governor, and it is the practical fruit of prudence in action."),
    "sound-mindedness": ("Sound-mindedness is the quality of having a sane, sensible and well-balanced mind, of judging and acting in accordance with reality and good sense rather than with delusion or frenzy. The sound-minded person is free from egregious error and aberration, reasoning clearly, estimating things at their true worth, and conducting life in a rational and sober manner. It is the mental health that underlies all right decision and conduct, the foundation of common sense and reliable counsel. Sound-mindedness is the condition a rational being, balanced between undue optimism and anxiety, thinks clearly and looks at the world with open and trustworthy eyes."),
    "comprehension": ("Comprehension is the act or power of grasping fully and including within the mind, whether the whole meaning of a thing, the full extent of a subject or the range of a word or idea. It is the capacity to take in and hold together many parts in a single view, so that one sees not only the parts but their relation and totality. To comprehend a subject is to understand it thoroughly and in all its bearings, not merely to know isolated facts about it. Comprehension is understanding raised to completeness, and it is the intellectual faculty that surveys the whole field and brings its parts into a coherent unity."),
    "apprehension": ("Apprehension is the act of catching hold of a thing by the mind, the quick and clear perception or understanding of a fact, idea or situation. In its intellectual sense it is the grasp of the mind upon something perceived or conceived, the awareness that takes a thing in, and in its emotional sense it is the fear or dread of what is to come, a foreboding anxiousness. The word thus unites the idea of mental seizure with the idea of emotional trembling. Apprehension is the faculty of quick comprehension, and in its fearful mood it is the uneasy anticipation that looks forward to some coming ill."),
    "cognition": ("Cognition is the mental action or process of acquiring knowledge and understanding through thought, experience and the senses, encompassing perception, attention, memory, reasoning, judgment and problem-solving. It is the whole apparatus of knowing and thinking by which the mind takes in information and works it up into knowledge and belief. Cognition is the subject of cognitive science, the study of the processes of knowing, and it underlies every act of learning and every exercise of intelligence. It is the general name for the mental machinery that turns the raw data of experience into the web of understanding with which we meet the world."),
    "intellect": ("Intellect is the faculty of the mind by which it knows, reasons and understands, the power of thought, conception and comprehension as distinguished from mere feeling or will. It is the seat of reasoning and understanding, the capacity to grasp general ideas, to reason from premises to conclusions, and to penetrate to the principles of things. The intellect, in the phrase of the philosophers, is the highest and most characteristically human of the mental powers, and in its cultivation lies the advancement of knowledge and wisdom. A person of intellect is one in whom this power is notably developed, and it is the measure of a mind's reach and profundity."),
    "reason": ("Reason is the power of the mind to think, judge and draw conclusions in a logical and orderly way, and the ground or motive by which a belief is justified or an action explained. As a faculty, reason is the capacity for intelligent and unconceived thinking that distinguishes human beings from brutes; as a ground, a reason is the explanation that makes a thing intelligible or defensible. To reason is to move in thought from what is known to what is inferred, and to give reasons is to offer grounds for judgment or action. Reason is at once the instrument of truth and the common standard by which claims are measured."),
    "logic": ("Logic is the science of right reasoning, the systematic study of the principles and methods by which valid inference is made and sound argument is distinguished from fallacy. It teaches how to proceed from premises to conclusions in a way that the conclusion follows necessarily, and it provides the rules of correct thinking applicable to every field of inquiry. In a wider sense, logic is the quality of a train of thought that hangs together and follows, and good sense in argument. Logic is the guardian of rationality, for without it reasoning is at the mercy of confusion and error, and it is the common instrument of all sound science and philosophy."),
    "reasoning": ("Reasoning is the process of drawing conclusions from premises or of thinking through a question systematically, the mental activity of connecting ideas by inference so as to reach a judgment. It is the act of reason in operation, whether in the strict deduction of logic, the plausible argumentation of rhetoric, or the everyday weighing of evidence and considerations. Good reasoning is orderly, relevant and sound, moving from accepted grounds to tenable conclusions, and it is the method by which belief is justified and knowledge advanced. Reasoning is the tool of all serious inquiry, and its excellence lies in reaching true and defensible results by valid steps."),
    "sophistication": ("Sophistication is the quality of being refined, worldly-wise and urbane, marked by a cultivated subtlety of mind and taste that comes of education, experience and acquaintance with the world. The sophisticated person has moved beyond the naive and the crude to a polished and knowing subtlety, understanding the complexity of things, appreciating refinements, and carrying culture with ease. It implies discrimination and polish, and it is the mark of one who has lost the provincial roughness and the simple credulousness of inexperience. Sophistication can also suggest an over-refined complexity that lacks sincerity, but at its best it is the grace of a cultivated and subtle intelligence."),
    "sagaciousness": ("Sagaciousness is the quality of being wise, shrewd and far-seeing in practical judgment, of understanding people and situations with penetration and acting with prudence and good sense. The sagacious person combines keen wit with experience, seeing to the heart of matters and anticipating consequences, so that counsel and decision are marked by an almost instinctive soundness. It is wisdom in action, the practical sagacity that perceives the prudent course in difficulty and the true character behind seeming. Sagaciousness is the virtue of the wise old counselor and the experienced man of affairs, and it is the practical fruit of insight ripened by the years."),
    "erudition": ("Erudition is extensive and deep learning, the possession of wide and accurate knowledge gained by profound study and reading, especially in books, scholarship and the humanities. The erudite person is learned to a high degree, versed in the literature and learning of many fields, and able to bring a wealth of acquired knowledge to bear upon any question. It is scholarship in its fullest sense, the stored and digested learning of the student and the savant, distinguished from mere superficial information by its depth and range. Erudition is the treasure of the scholar, the deep and broad foundation upon which authority of knowledge is built."),
    "scholarship": ("Scholarship is the character and activity of the scholar, the possession of learning and the practice of careful and accurate study in a field of knowledge, together with the expert knowledge so acquired. It denotes both the erudition of the learned and the methodical and critical habits by which that learning is established and advanced. A work of scholarship is one of serious research and exact scholarship, and a scholarly person is one who studies with depth and rigor. Scholarship is the disciplined pursuit of truth in a special field, and it is the foundation of all academic authority and of the trustworthy transmission of knowledge."),
    "literacy": ("Literacy is the ability to read and write, and more broadly the state of being educated and informed in the use of language and the understanding of written forms of knowledge. A literate person can read and write with fluency and comprehension, and in the extended and figurative sense is well-versed in the intellectual and cultural resources of civilization. It is the fundamental skill that unlocks learning and participation in the world of letters, and its absence, illiteracy, shuts its victims out of the rich communication and knowledge of books. Literacy is the first key to education and the foundation of an informed citizenry, and it has been the great engine of modern civilization."),
    "enlightenment": ("Enlightenment is the act or state of being enlightened, of having the darkness of ignorance or confusion removed by the light of understanding, and the knowledge, insight or wisdom that results. It may be applied to the individual who has come to a clearer and truer comprehension of things, and historically to the great eighteenth-century movement of thought that sought to banish superstition and error through reason and science. To enlighten is to bring light to the mind, dispelling error and furnishing sound knowledge. Enlightenment is the dawn of reason and understanding in the soul, and it stands for the liberation of the intellect from ignorance and prejudice."),
    "learning": ("Learning is the acquisition of knowledge or skill through study, experience, instruction or investigation, and the knowledge or skill so acquired. It is at once the process of coming to know and the body of what is known, from the first lessons of the child to the vast erudition of the scholar. Learning is the lifelong activity of the mind that accumulates information, forms judgment and builds competence, and it is the chief means by which the human species transmits and enlarges its heritage of knowledge and art. Learning is the road from ignorance to understanding, and it is both the discipline of the student and the treasury of the learned."),
    "education": ("Education is the process of receiving or giving systematic instruction, especially in schools and universities, and the development of character, knowledge and skill that results from it. It is the bringing up and training of the young, and more broadly the whole cultivation of the faculties of mind and body by instruction and discipline. Education has both a general sense, as the whole course of intellectual and moral formation, and a technical sense, as schooling in a particular subject or skill. It is the great means of transmitting civilization, forming the mind, fitting the person for life and work, and preparing each generation to take up the heritage of the last. Education is the deliberate shaping of the human being for individual fulfillment and social good."),
    "aptitude": ("Aptitude is a natural ability or capacity for learning or doing something, a native fitness or quickness in a particular field of activity. It is the inborn proneness to acquire certain skills or knowledge readily, so that the person of aptitude learns quickly and performs with facility in that direction. Aptitude differs from achievement, which is what one has actually learned, being the potential that promise holds out for what may be accomplished with training. It is the seed of talent, the natural readiness of the mind or hand that, when cultivated, grows into skill and excellence. Aptitude is the foundation upon which education and practice build real capability."),
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
    ("mirth", ("mirth", "cheerfulness", "jovial", "lighthearted", "merry", "joyful laughter")),
    ("sincerity", ("sincerity", "genuine", "open-heart", "honest feeling", "unforced truth", "unaffected")),
    ("zeal", ("zeal", "passionate energy", "eager enthusiasm", "burning ardor", "fervent application", "devoted energy")),
    ("assiduousness", ("assiduousness", "diligent attention", "unremitting care", "thorough application", "steady hard work", "constant effort")),
    ("discernment", ("discernment", "fine judgment", "perceptive insight", "discerning eye", "good taste", "clear-sighted choice")),
    ("stamina", ("stamina", "enduring energy", "prolonged effort", "physical endurance", "sustained patience", "tireless energy")),
    ("gentleness", ("gentleness", "mild temperament", "tender spirit", "soft-spoken kindness", "meekness", "gentle nature")),
    ("quietness", ("quietness", "stillness", "inner calm", "tranquil quiet", "hushed stillness", "peaceful silence")),
    ("hardihood", ("hardihood", "bold daring", "audacious courage", "intrepid spirit", "daring resolve", "fearless enterprise")),
    ("fellowship", ("fellowship", "companionship", "comradeship", "mutual support", "shared purpose", "brotherhood")),
    ("gallantry", ("gallantry", "chivalrous courtesy", "brave conduct", "heroic courtesy", "gentlemanly valor", "courtly bravery")),
    ("nobility", ("nobility", "high character", "moral excellence", "noble-mindedness", "princely valor", "elevated soul")),
    ("virtue", ("virtue", "moral excellence", "righteousness", "goodness", "uprightness", "right living")),
    ("benevolence", ("benevolence", "kind disposition", "goodwill", "charitable heart", "beneficent action", "well-wishing")),
    ("largess", ("largess", "lavish giving", "liberal gifts", "bountiful bestowal", "munificent grant", "generous endowment")),
    ("civility", ("civility", "polite respect", "courteous behavior", "civilized manners", "decent conduct", "gracious etiquette")),
    ("moderation", ("moderation", "temperate living", "balanced habit", "restraint in excess", "measured conduct", "golden mean")),
    ("tranquility", ("tranquility", "serene calm", "peaceful stillness", "untroubled quiet", "unruffled calm", "placid repose")),
    ("nurturance", ("nurturance", "fostering care", "mothering warmth", "growth-nourishing love", "protective tenderness", "developmental attention")),
    ("serendipity", ("serendipity", "happy accident", "fortunate discovery", "lucky find", "unexpected blessing", "chance fortune")),
    ("warmth", ("warmth", "hearty friendliness", "affectionate manner", "welcoming kindness", "cordial disposition", "genial heat")),
    ("magnificence", ("magnificence", "grandeur", "splendor", "impressive beauty", "stately grace", "majestic display")),
    ("spirit", ("spirit", "vital force", "liveliness", "enthusiasm", "animation", "inner energy")),
    ("sageness", ("sageness", "deep wisdom", "seasoned judgment", "worldly prudence", "mature insight", "tried and tested wisdom")),
    ("eloquence", ("eloquence", "persuasive speech", "fluent tongue", "silver tongue", "artful expression", "captivating rhetoric")),
    ("wit", ("wit", "quick humor", "clever repartee", "sharp banter", "ingenious humor", "nimble mind")),
    ("charisma", ("charisma", "magnetic presence", "personal magnetism", "compelling charm", "force of personality", "winning charm")),
    ("earnestness", ("earnestness", "sincere seriousness", "wholehearted purpose", "deep conviction", "unfeigned warmth", "grave sincerity")),
    ("honor", ("honor", "uprightness", "integrity of spirit", "faith in one's word", "principle above profit", "stainless reputation")),
    ("decorum", ("decorum", "propriety", "proper behavior", "social grace", "polite formality", "appropriate conduct")),
    ("finesse", ("finesse", "subtle skill", "delicate handling", "fine touch", "exquisite craft", "polished art")),
    ("invention", ("invention", "new creation", "innovative device", "novel idea", "ingenious contrivance", "clever construction")),
    ("guilelessness", ("guilelessness", "candid openness", "artless honesty", "unworldly simplicity", "innocent frankness", "transparent plainness")),
    ("neighborliness", ("neighborliness", "helpful companionship", "community spirit", "friendly cooperation", "neighborly goodwill", "kindred community")),
    ("affability", ("affability", "easy approach", "pleasant manner", "genial courtesy", "open friendliness", "warm approachability")),
    ("timeliness", ("timeliness", "punctuality", "well-timed action", "opportune moment", "seasonable promptness", "at-hand readiness")),
    ("steadiness", ("steadiness", "level-headed composure", "unflappable calm", "constant purpose", "steady nerve", "unbroken resolve")),
    ("fidelity", ("fidelity", "steadfast loyalty", "faithful devotion", "exact faithfulness", "unswerving allegiance", "true-hearted constancy")),
    ("probity", ("probity", "proven integrity", "uncompromising honesty", "unblemished record", "blameless conduct", "faithful dealing")),
    ("goodness", ("goodness", "moral excellence", "beneficent nature", "kindhearted virtue", "upright dealing", "wholesome character")),
    ("kindred spirit", ("kindred spirit", "soul mate", "fellow traveler", "like-minded companion", "twin soul", "auspicious affinity")),
    ("phronesis", ("phronesis", "practical wisdom", "sage counsel", "good judgment", "discerning prudence", "shrewd deliberation")),
    ("peaceableness", ("peaceableness", "amicable disposition", "exeamic harmony", "nonviolent nature", "tranquil spirit", "concordant temperament")),
    ("harmony", ("harmony", "concordant agreement", "melodious accord", "balanced co-existence", "sympathetic consonance", "communal harmony")),
    ("comity", ("comity", "mutual courtesy", "interstate goodwill", "reciprocal respect", "polite regard", "friendly courtesy between nations")),
    ("pleasantness", ("pleasantness", "agreeable manner", "cheerful disposition", "genial warmth", "sweet temper", "winsome charm")),
    ("warmheartedness", ("warmheartedness", "affectionate kindness", "gentle benevolence", "tender compassion", "open-hearted love", "loving care")),
    ("perspicacity", ("perspicacity", "keen insight", "penetrating discernment", "sharp perception", "quick-witted sagacity", "subtle understanding")),
    ("conviviality", ("conviviality", "festive cheer", "sociable warmth", "jovial fellowship", "merry companionship", "convivial good humor")),
    ("innocence", ("innocence", "guiltless purity", "harmless simplicity", "untainted virtue", "naive candidness", "blameless innocence")),
    ("verity", ("verity", "truthful accuracy", "unvarnished fact", "plain truth", "unfailing honesty", "sober reality")),
    ("purity", ("purity", "immaculate cleanliness", "unsullied whiteness", "spotless chasteness", "unalloyed wholeness", "clear transparency")),
    ("newness", ("newness", "unworn freshness", "novel character", "pristine novelty", "unspoiled beginning", "nascent quality")),
    ("genuineness", ("genuineness", "authentic reality", "unaffected sincerity", "true-hearted candor", "honest openness", "unfeigned nature")),
    ("righteousness", ("righteousness", "moral uprightness", "just dealing", "virtuous conduct", "blameless integrity", "God-fearing honesty")),
    ("equanimity", ("equanimity", "composed balance", "imperturbable calm", "serene poise", "unvarying temper", "steadied composure")),
    ("philanthropy", ("philanthropy", "generous giving", "benevolent charity", "humanitarian aid", "philanthropic concern", "public-spirited kindness")),
    ("bereavement", ("bereavement", "personal grief", "sorrowing loss", "mourning the departed", "grieving heart", "internal affliction")),
    ("yearning", ("yearning", "ardent desire", "intense longing", "soulful craving", "longing after", "wistful aspiration")),
    ("unselfishness", ("unselfishness", "altruistic giving", "selfless generosity", "unsparing devotion", "disinterested kindness", "heedless-of-self charity")),
    ("foresight", ("foresight", "far-sightedness", "forward planning", "wise anticipation", "prudent foresight", "long-range vision")),
    ("intrepidity", ("intrepidity", "undaunted courage", "dauntless bravery", "fearless daring", "stout-hearted valor", "unblenching resolution")),
    ("fealty", ("fealty", "oath-bound loyalty", "sworn allegiance", "feudal fidelity", "pledged devotion", "solemn promise of loyalty")),
    ("loyalty", ("loyalty", "steadfast devotion", "constant allegiance", "unshakable faithfulness", "true-hearted fidelity", "firm attachment")),
    ("unfailingness", ("unfailingness", "never-failing supply", "inexhaustible patience", "unending constancy", "ceaseless devotion", "tireless persistence")),
    ("solidity", ("solidity", "firm substance", "sturdy reliability", "rock-solid stability", "dependable mass", "unshakeable firmness")),
    ("directness", ("directness", "unswerving frankness", "straightforward clarity", "direct approach", "plain-spoken honesty", "undeviating course")),
    ("candor", ("candor", "frank openness", "free-spoken honesty", "unreserved truthfulness", "guileless sincerity", "plain dealing")),
    ("plainness", ("plainness", "unadorned simplicity", "severity of style", "artless clarity", "unpolished candor", "homely plainness")),
    ("simplicity", ("simplicity", "uncomplicated ease", "plain integrity", "guileless plainness", "elemental purity", "severe truthfulness")),
    ("unaffectedness", ("unaffectedness", "spontaneous sincerity", "artless naturalness", "untutored genuineness", "unforced candor", "ingenuous simplicity")),
    ("veracity", ("veracity", "truth-telling habit", "accurate truthfulness", "unerring honesty", "guileless truth", "sincerity of statement")),
    ("comprehensiveness", ("comprehensiveness", "all-embracing scope", "full coverage", "exhaustive treatment", "all-encompassing view", "whole-scale breadth")),
    ("thoroughness", ("thoroughness", "painstaking care", "scrupulous detail", "rigorous completeness", "exhaustive precision", "minute exactness")),
    ("good faith", ("good faith", "honest intent", "bona fide dealing", "sincere motive", "fair dealing", "honest bargaining")),
    ("good humor", ("good humor", "cheerful disposition", "sunny temper", "good-natured mirth", "jovial spirits", "lighthearted cheer")),
    ("attentiveness", ("attentiveness", "close attention", "heedful regard", "alert listening", "careful observation", "mindful awareness")),
    ("wakefulness", ("wakefulness", "alert vigilance", "waking awareness", "sleepless watch", "lucid alertness", "unremitting attention")),
    ("watchfulness", ("watchfulness", "vigilant guard", "sentry duty", "alert lookout", "circumspect observation", "continuous surveillance")),
    ("surveillance", ("surveillance", "close watch", "systematic monitoring", "electronic oversight", "careful observation", "continuous tracking")),
    ("devotement", ("devotement", "whole-hearted giving", "deep devotion", "faithful dedication", "self-surrendering love", "steadfast commitment")),
    ("resoluteness", ("resoluteness", "determined firmness", "unwavering purpose", "settled decision", "fixed resolve", "unshakable determination")),
    ("contentment", ("contentment", "quiet satisfaction", "peaceful sufficiency", "settled contentment", "grateful ease", "tranquil satisfaction")),
    ("prudence", ("prudence", "sound foresight", "cautious judgment", "careful planning", "practical wisdom", "wise moderation")),
    ("justice", ("justice", "fair dealing", "impartial treatment", "due desert", "equitable judgment", "rightful recompense")),
    ("clemency", ("clemency", "merciful leniency", "sparing forgiveness", "gentle pardon", "compassionate moderation", "humane mercy")),
    ("temperance", ("temperance", "measured moderation", "self-restraint", "balanced appetite", "governed desire", "sober self-control")),
    ("endurance", ("endurance", "prolonged stamina", "patient forbearance", "long-suffering constancy", "steady holding out", "durable fortitude")),
    ("serenity", ("serenity", "untroubled calm", "quiet composure", "peaceful stillness", "unruffled poise", "serene repose")),
    ("patience", ("patience", "calm forbearance", "steady waiting", "unruffled tolerance", "long-suffering endurance", "unhasty composure")),
    ("forbearance", ("forbearance", "patient self-restraint", "holding back resentment", "enduring provocation", "gentle long-suffering", "mercy in patience")),
    ("longanimity", ("longanimity", "prolonged forbearance", "long-suffering patience", "patient endurance", "serene constancy", "steadfast long-suffering")),
    ("equity", ("equity", "fair dealing", "natural justice", "just proportion", "even-handed fairness", "equitable judgment")),
    ("munificence", ("munificence", "princely generosity", "lavish giving", "splendid bounty", "liberal largess", "great-hearted liberality")),
    ("valor", ("valor", "personal bravery", "courageous spirit", "fearless resolution", "gallant courage", "bold daring")),
    ("bravery", ("bravery", "bold courage", "daring fortitude", "fearless resolution", "steadfast courage", "valiant spirit")),
    ("courage", ("courage", "mastery of fear", "moral resolve", "valiant daring", "resolute spirit", "bold fortitude")),
    ("fortitude", ("fortitude", "patient courage", "enduring strength", "firm-spirited endurance", "steadfast hardihood", "moral constancy")),
    ("graciousness", ("graciousness", "easy courtesy", "kindly dignity", "polished goodwill", "gentle charm", "courteous grace")),
    ("decisiveness", ("decisiveness", "prompt resolution", "firm determination", "clear-cut judgment", "unwavering decision", "resolute promptness")),
    ("sang-froid", ("sang-froid", "cool composure", "unruffled calm", "steady self-possession", "imperturbable coolness", "collected presence")),
    ("complacency", ("complacency", "smug self-satisfaction", "smug content", "resting on laurels", "uncritical ease", "self-satisfied calm")),
    ("piety", ("piety", "due reverence", "devout devotion", "filial duty", "sacred obedience", "devoted reverence")),
    ("reverence", ("reverence", "deep respect", "awe-struck regard", "solemn veneration", "humble admiration", "sacred honor")),
    ("zealousness", ("zealousness", "ardent eagerness", "fiery devotion", "whole-hearted fervor", "passionate diligence", "burning enthusiasm")),
    ("deference", ("deference", "courteous yielding", "respectful submission", "honored precedence", "graceful compliance", "respectful regard")),
    ("austerity", ("austerity", "strict simplicity", "severe frugality", "sparse living", "ascetic plainness", "spartan restraint")),
    ("pride", ("pride", "self-respect", "proud satisfaction", "due self-regard", "elevated dignity", "honest self-worth")),
    ("vainglory", ("vainglory", "empty boastfulness", "vain self-conceit", "hollow glory", "idle vanity", "boastful silly-pride")),
    ("humility", ("humility", "modest self-estimation", "unassuming lowliness", "due self-appraisal", "gentle self-knowledge", "unpretentious plainness")),
    ("modesty", ("modesty", "unassuming reserve", "freedom from vanity", "becoming reticence", "unpretentious dignity", "shy decorum")),
    ("dignity", ("dignity", "inherent worth", "self-respecting bearing", "becoming gravity", "composed self-possession", "honored stature")),
    ("gallantry", ("gallantry", "chivalrous courage", "dashing courtesy", "valiant grace", "courtly boldness", "heroic politeness")),
    ("splendor", ("splendor", "brilliant magnificence", "dazzling grandeur", "radiant glory", "gorgeous luster", "shining excellence")),
    ("radiance", ("radiance", "glowing brightness", "shining warmth", "joyous lustre", "incandescent glow", "beaming light")),
    ("grace", ("grace", "effortless elegance", "poised beauty", "unmerited kindness", "easy charm", "gracious poise")),
    ("amiability", ("amiability", "pleasant good-nature", "genial friendliness", "sweet disposition", "agreeable warmth", "likeable kindness")),
    ("sociability", ("sociability", "love of company", "easy fellowship", "ready conviviality", "social disposition", "companionable openness")),
    ("cordiality", ("cordiality", "hearty warmth", "sincere friendliness", "genuine goodwill", "open-hearted welcome", "hearty earnestness")),
    ("solicitude", ("solicitude", "caring concern", "attentive watchfulness", "thoughtful worry", "considerate care", "anxious kindness")),
    ("consideration", ("consideration", "thoughtful regard", "caring attentiveness", "gentle heedfulness", "mindful courtesy", "kindly foresight")),
    ("urbanity", ("urbanity", "polished refinement", "suave courtesy", "sophisticated ease", "witty polish", "graceful civility")),
    ("courtesy", ("courtesy", "polite consideration", "gracious manners", "civil respect", "courteous decency", "gentle politeness")),
    ("etiquette", ("etiquette", "social convention", "code of manners", "polite custom", "courtesy rules", "proper form")),
    ("tact", ("tact", "delicate perception", "sure discretion", "social tact", "adroit handling", "diplomatic delicacy")),
    ("polish", ("polish", "refined finish", "cultivated smoothness", "urbane gloss", "finished elegance", "sleek refinement")),
    ("mannerliness", ("mannerliness", "habitual politeness", "good breeding", "courteous habit", "civil demeanor", "polite conduct")),
    ("propriety", ("propriety", "fitting decency", "seemly correctness", "proper bound", "decorous fitness", "social decency")),
    ("decency", ("decency", "basic fairness", "modest propriety", "honest dealing", "humane behavior", "proper conduct")),
    ("composure", ("composure", "settled calm", "steady self-possession", "collected ease", "unflustered poise", "tranquil command")),
    ("repose", ("repose", "restful quiet", "tranquil stillness", "untroubled calm", "peaceful rest", "serene rest")),
    ("placidness", ("placidness", "untroubled calm", "mild evenness", "serene unruffledness", "gentle peace", "quiet composure")),
    ("imperturbability", ("imperturbability", "unshakable calm", "settled stoicism", "unmoved composure", "impervious serenity", "level poise")),
    ("frankness", ("frankness", "open directness", "unreserved honesty", "plain speaking", "blunt sincerity", "unvarnished candor")),
    ("plain-spokenness", ("plain-spokenness", "direct simple speech", "forthright words", "unadorned clarity", "honest plainness", "straightforward talk")),
    ("openheartedness", ("openheartedness", "candid warmth", "frank generosity", "unreserved affections", "transparent kindness", "whole-hearted openness")),
    ("artlessness", ("artlessness", "unaffected simplicity", "natural candor", "guileless openness", "unstudied ease", "spontaneous sincerity")),
    ("candidness", ("candidness", "unbiased honesty", "fair outspokenness", "impartial truth-telling", "open sincerity", "plainhearted veracity")),
    ("bluntness", ("bluntness", "abrupt directness", "forthright plainness", "unvarnished speech", "rough honesty", "unsparing candor")),
    ("outspokenness", ("outspokenness", "fearless candor", "bold speaking out", "plain-spoken truth", "unflinching frankness", "forthright boldness")),
    ("straightforwardness", ("straightforwardness", "honest directness", "guileless plainness", "straight dealing", "undeniable openness", "plain-dealing honesty")),
    ("upstandingness", ("upstandingness", "moral uprightness", "unimpeachable integrity", "solid respectability", "honorable standing", "steady probity")),
    ("truthfulness", ("truthfulness", "habitual veracity", "unstinting honesty", "reliable truth-telling", "scrupulous sincerity", "dutiful candor")),
    ("accuracy", ("accuracy", "exact correctness", "freedom from error", "precise fidelity", "careful exactness", "true correspondence")),
    ("competence", ("competence", "practical command", "reliable skill", "sufficient ability", "capable know-how", "trustworthy proficiency")),
    ("industry", ("industry", "steady diligence", "assiduous labor", "productive application", "systematic work", "untiring application")),
    ("sedulousness", ("sedulousness", "persistent care", "untiring diligence", "close attention", "patient assiduity", "careful constancy")),
    ("exactness", ("exactness", "precise correctness", "strict fidelity", "rigorous accuracy", "faithful precision", "minute exactness")),
    ("scrutiny", ("scrutiny", "close examination", "searching enquiry", "critical inspection", "minute review", "watchful examination")),
    ("observance", ("observance", "faithful keeping", "due respect", "ceremonial honor", "dutiful practice", "careful compliance")),
    ("punctiliousness", ("punctiliousness", "strict attention to detail", "fussy exactness", "meticulous ceremony", "scrupulous precision", "nice observance")),
    ("scrupulousness", ("scrupulousness", "conscientious exactness", "tender-liberal honesty", "strict integrity", "careful probity", "rigorous conscientiousness")),
    ("punctuality", ("punctuality", "exact timekeeping", "prompt attendance", "timely arrival", "reliable exactness", "unfail-being on time")),
    ("promptness", ("promptness", "ready dispatch", "quick response", "timely action", "no delay", "alert alacrity")),
    ("deliberation", ("deliberation", "careful weighing", "unhurried consideration", "pausing reason", "measured reflection", "circumspect thought")),
    ("circumspection", ("circumspection", "vigilant wariness", "prudent caution", "looking on all sides", "watchful circumspect", "careful surveying")),
    ("wariness", ("wariness", "guarded caution", "wise suspicion", "watchful reserve", "prudent distrust", "alert wariness")),
    ("providence", ("providence", "prudent provision", "farsighted planning", "timely preparation", "wise forethought", "saving prudence")),
    ("anticipation", ("anticipation", "forward-looking", "prepared expectation", "eager looking-forward", "advance readiness", "presentiment of what comes")),
    ("suspicion", ("suspicion", "instinctive distrust", "doubtful mistrust", "questioning mind", "guarded skepticism", "wary doubt")),
    ("self-restraint", ("self-restraint", "voluntary self-command", "mastered impulse", "checked appetite", "governed passion", "disciplined forbearance")),
    ("restraint", ("restraint", "holding in check", "tempered moderation", "bounded action", "prudent measure", "control of excess")),
    ("measure", ("measure", "due proportion", "fitting degree", "golden mean", "right bound", "temperate balance")),
    ("equilibrium", ("equilibrium", "steady balance", "stable poise", "even temper", "counterweighted calm", "settled steadiness")),
    ("constancy", ("constancy", "steadfast loyalty", "unchanging fidelity", "firm attachment", "fixed resolve", "dependable devotion")),
    ("consistency", ("consistency", "uniform reliability", "self-agreement", "steady uniformity", "accordant conduct", "inward congruity")),
    ("resilience", ("resilience", "quick recovery", "refusal to stay down", "elastic fortitude", "bounce-back strength", "renewed resistance")),
    ("recuperation", ("recuperation", "regained strength", "gradual recovery", "convalescent healing", "restored vigor", "renewed well-being")),
    ("self-reliance", ("self-reliance", "sturdy independence", "self-sufficing power", "own-two-feet strength", "inner resources", "standing alone")),
    ("autonomy", ("autonomy", "self-government", "self-direction", "free self-rule", "independent control", "self-determining power")),
    ("persistence", ("persistence", "unfailing continuance", "refusing to give up", "patient striving", "dogged continuation", "steady endurance")),
    ("doggedness", ("doggedness", "stubborn tenacity", "grim persistence", "refusing to let go", "unrelenting pursuit", "bulldog steadiness")),
    ("perseverance", ("perseverance", "unremitting continuance", "patient constancy", "unshaken determination", "steadfast onward going", "long-enduring resolve")),
    ("assiduity", ("assiduity", "constant diligence", "unfailing attention", "steady application", "unremitting care", "habitual industry")),
    ("application", ("application", "close effort", "steady attention", "concentrated energy", "devoted study", "persistent focus")),
    ("thrift", ("thrift", "frugal care", "economic management", "saving prudence", "careful husbandry", "wise saving")),
    ("economy", ("economy", "careful management", "efficient use", "prudent spending", "good husbandry", "judicious thrift")),
    ("husbandry", ("husbandry", "thrifty management", "careful cultivation", "provident stewardship", "resource preservation", "frugal farming")),
    ("stewardship", ("stewardship", "responsible care", "trusted management", "faithful guardianship", "accountable administration", "far-sighted custody")),
    ("beneficence", ("beneficence", "active doing of good", "conferred benefit", "helpful deeds", "positive desert", "welfare-promoting action")),
    ("charity", ("charity", "neighborly love", "alms-giving", "generous compassion", "relief of the poor", "benevolent kindness")),
    ("generosity", ("generosity", "noble giving", "open-handed bounty", "large-hearted spirit", "liberal kindness", "unselfish bounty")),
    ("altruism", ("altruism", "disinterested benevolence", "self-sacrificing care", "concern for others", "unselfish action", "other-regarding love")),
    ("magnanimity", ("magnanimity", "greatness of soul", "noble generosity", "lofty spirit", "gentle forgiveness", "high-hearted nobleness")),
    ("forgiveness", ("forgiveness", "pardoning mercy", "renounced vengeance", "relinquished resentment", "restored goodwill", "reconciling pardon")),
    ("reconciliation", ("reconciliation", "restored harmony", "mended friendship", "ended estrangement", "rebuilt trust", "renewed concord")),
    ("amends", ("amends", "reparation made", "compensation offered", "apology with repair", "corrective restitution", "healing reparation")),
    ("peace", ("peace", "tranquil harmony", "freedom from conflict", "inward calm", "concord among peoples", "secure repose")),
    ("concord", ("concord", "willing agreement", "harmonious accord", "united purpose", "reciprocal harmony", "settled co-operation")),
    ("comradery", ("comradery", "shared fellowship", "warm solidarity", "mutual reliance", "good comradeship", "band-of-brothers spirit")),
    ("docility", ("docility", "teachable spirit", "ready to learn", "open to instruction", "willing guidance", "receptive humility")),
    ("obedience", ("obedience", "willing compliance", "submission to rule", "dutiful compliance", "law-abiding conduct", "heeding command")),
    ("respectfulness", ("respectfulness", "due honor", "considerate regard", "dignified deference", "courteous esteem", "high regard")),
    ("veneration", ("veneration", "deep reverence", "awed respect", "solemn honoring", "sacred worship", "profound regard")),
    ("worship", ("worship", "reverent homage", "devout adoration", "sacred ceremony", "supreme devotion", "holy veneration")),
    ("tenet", ("tenet", "core belief", "held principle", "established doctrine", "firm conviction", "basic tenet")),
    ("ambition", ("ambition", "eager striving", "high goal-setting", "desire for distinction", "purposeful drive", "rise and excel")),
    ("aspiration", ("aspiration", "hopeful longing", "lofty aim", "upward reaching", "cherished hope", "noble yearning")),
    ("enterprise", ("enterprise", "bold initiative", "readiness to venture", "active undertaking", "enterprising spirit", "measured risk-taking")),
    ("heroism", ("heroism", "extraordinary valor", "self-forgetful daring", "noble courage", "great-hearted bravery", "surpassing devotion")),
    ("perfectionism", ("perfectionism", "highest-standard pursuit", "flawless ambition", "exacting ideal", "relentless refinement", "spotless excellence")),
    ("excellence", ("excellence", "surpassing merit", "superior quality", "high attainment", "sustained standard", "singular virtue")),
    ("worthiness", ("worthiness", "deserved esteem", "genuine merit", "earned honor", "due regard", "proved desert")),
    ("capability", ("capability", "practical power", "skill to perform", "effective potential", "fitness to act", "ready ability")),
    ("versatility", ("versatility", "many-sided talent", "ready adaptability", "flexible skill", "wide range of use", "turning hand to all")),
    ("flexibility", ("flexibility", "bending without breaking", "ready adaptability", "open-mindedness", "supple adjustment", "accommodating nature")),
    ("adaptability", ("adaptability", "ready adjustment", "fit to conditions", "responsive change", "changed-method skill", "environmental fit")),
    ("inventiveness", ("inventiveness", "fertile new ideas", "resourceful originality", "fresh devices", "creative solution-finding", "productive imagination")),
    ("creativity", ("creativity", "original generation", "novel combination", "imaginative force", "fresh seeing", "new-formed expression")),
    ("originality", ("originality", "native freshness", "independent invention", "undervived creation", "striking novelty", "own-mind character")),
    ("ingenuity", ("ingenuity", "clever resourcefulness", "inventive wit", "cunning contrivance", "practical genius", "adroit solution")),
    ("resourcefulness", ("resourcefulness", "quick improvising", "making the most", "turning lacks to profit", "slender-means skill", "clever coping")),
    ("pragmatism", ("pragmatism", "practical handling", "consequences-first", "means-fit-to-ends", "workable solution", "outcome-focused temper")),
    ("sobriety", ("sobriety", "serious calm", "steady self-command", "moderate temper", "level-headedness", "unclouded sobriety")),
    ("soundness", ("soundness", "freedom from defect", "valid reasoning", "reliable solidity", "unshakeable health", "trustworthy integrity")),
    ("wholesomeness", ("wholesomeness", "healthful soundness", "moral purity", "nourishing goodness", "unspoiled freshness", "beneficial nature")),
    ("vitality", ("vitality", "abundant energy", "buoyant liveliness", "native vigor", "zestful force", "animating life")),
    ("vigor", ("vigor", "active strength", "forceful energy", "brisk robustness", "energetic exertion", "sturdy liveliness")),
    ("spunk", ("spunk", "plucky spirit", "fire of temper", "cheerful defiance", "lively boldness", "dauntless grit")),
    ("fiber", ("fiber", "inner strength of character", "sturdy moral sinew", "firm backbone", "tested mettle", "resolute grain")),
    ("grit", ("grit", "indomitable spirit", "unyielding resolve", "tough-minded courage", "stubborn stamina", "refusing to quit")),
    ("panache", ("panache", "dashing flair", "flamboyant style", "spirited dash", "confident bravura", "tasteful flourish")),
    ("intrepidness", ("intrepidness", "fearless daring", "undaunted courage", "bold disregard of danger", "steady nerve", "dauntless valor")),
    ("daredevilry", ("daredevilry", "reckless showiness", "fool-hardy daring", "courted danger", "thrilling bravado", "needless risk-taking")),
    ("fearlessness", ("fearlessness", "absence of dread", "untroubled courage", "steady composure in danger", "undaunted spirit", "still nerve")),
    ("audacity", ("audacity", "daring presumption", "bold venturesomeness", "forward nerve", "cheeky courage", "unabashed boldness")),
    ("temerity", ("temerity", "reckless rashness", "imprudent daring", "foolhardy boldness", "needless hazard", "rash presumption")),
    ("rashness", ("rashness", "hasty precipitation", "impulsive haste", "unreflecting quickness", "thoughtless rush", "unwise speed")),
    ("understanding", ("understanding", "grasp of meaning", "comprehension of causes", "sympathetic insight", "interpretive intelligence", "generous discernment")),
    ("perception", ("perception", "sensory awareness", "quick insight", "sharp detection", "keen observation", "intuitive recognition")),
    ("acumen", ("acumen", "sharp discernment", "quick penetration", "shrewd judgment", "keen insight", "worldly wisdom")),
    ("shrewdness", ("shrewdness", "keen practical cleverness", "astute judgment", "worldly cunning", "sharp dealing", "astute foresight")),
    ("canniness", ("canniness", "wary shrewdness", "prudent cunning", "sure-footed cleverness", "careful astuteness", "guarded good sense")),
    ("judiciousness", ("judiciousness", "sound discretion", "wise deliberation", "well-balanced judgment", "prudent choice", "good counsel")),
    ("sound-mindedness", ("sound-mindedness", "sane judgment", "sensible reasoning", "sober balance of mind", "mental health", "clear-eyed common sense")),
    ("comprehension", ("comprehension", "full grasp", "inclusive understanding", "wholeness of view", "thorough insight", "coherent grasp")),
    ("apprehension", ("apprehension", "quick perception", "mental grasp", "dreadful anticipation", "clear awareness", "foreboding anxiousness")),
    ("cognition", ("cognition", "mental process of knowing", "perception and reasoning", "thoughtful understanding", "cognitive activity", "knowing faculty")),
    ("intellect", ("intellect", "power of reasoning", "faculty of thought", "seat of understanding", "capacity for insight", "rational faculty")),
    ("reason", ("reason", "logical thought", "justifying ground", "rational faculty", "sound inference", "explanatory motive")),
    ("logic", ("logic", "science of reasoning", "valid inference", "sound argument", "rule of thought", "rational method")),
    ("reasoning", ("reasoning", "drawing conclusions", "inferential thought", "logical deduction", "weighing evidence", "connecting ideas")),
    ("sophistication", ("sophistication", "worldly refinement", "urbane polish", "cultivated subtlety", "knowing taste", "complex understanding")),
    ("sagaciousness", ("sagaciousness", "practical wisdom", "far-seeing judgment", "shrewd perception", "ripe good sense", "insightful prudence")),
    ("erudition", ("erudition", "deep learning", "extensive scholarship", "profound reading", "broad knowledge", "stored wisdom")),
    ("scholarship", ("scholarship", "scholarly learning", "critical study", "expert erudition", "academic excellence", "disciplined research")),
    ("literacy", ("literacy", "ability to read and write", "learned fluency", "informed understanding", "scholarly acquaintance", "educated skill")),
    ("enlightenment", ("enlightenment", "dispelled ignorance", "dawn of reason", "intellectual liberation", "brought insight", "clarity of mind")),
    ("learning", ("learning", "acquired knowledge", "studied skill", "instructed understanding", "accumulated wisdom", "cultivated erudition")),
    ("education", ("education", "systematic instruction", "intellectual formation", "character training", "scholarly cultivation", "disciplined upbringing")),
    ("aptitude", ("aptitude", "natural capacity", "inborn readiness", "quick learning ability", "native fitness", "potential talent")),
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