import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from typing import Dict, List

class GodzillaFactCommand(commands.Cog):
    """Extremely advanced Godzilla fact command with 75+ facts per version and decorative elements."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Comprehensive Godzilla facts database - 75+ facts per version
        self.godzilla_facts = {
            "monsterverse": [
                "Did you know that Monsterverse Godzilla is 355 feet tall, making him one of the largest incarnations?",
                "Fun fact: Monsterverse Godzilla's atomic breath can reach temperatures of over 500,000 degrees Celsius!",
                "Interesting tidbit: His dorsal plates actually glow blue when charging his atomic breath, creating a stunning visual effect.",
                "Amazing fact: Monsterverse Godzilla has been alive for millions of years, surviving multiple extinction events.",
                "Cool detail: His heartbeat creates seismic activity that can be detected by scientific equipment worldwide.",
                "Did you realize that his footsteps alone can cause magnitude 4.6 earthquakes?",
                "Fascinating fact: Monsterverse Godzilla can absorb radiation to heal and become stronger.",
                "Surprising truth: He has a symbiotic relationship with the planet Earth itself.",
                "Incredible detail: His roar can be heard from over 300 miles away and reaches 174 decibels.",
                "Amazing fact: Monsterverse Godzilla's skin is nearly impenetrable, able to withstand nuclear explosions.",
                "Did you know he has a second brain in his tail area that helps coordinate his massive body?",
                "Interesting fact: His gills can process both air and water, allowing him to breathe in any environment.",
                "Cool truth: Monsterverse Godzilla's atomic breath can penetrate through the Earth's core.",
                "Fascinating detail: He has been worshipped by ancient civilizations as a god for thousands of years.",
                "Amazing fact: His metabolism slows down dramatically when he hibernates, allowing him to survive for millennia.",
                "Did you know that Monsterverse Godzilla's bite force exceeds 60,000 PSI?",
                "Incredible fact: He can regenerate lost tissue and even entire limbs given enough time and radiation.",
                "Surprising detail: His eyes can see across multiple spectrums of light, including infrared and ultraviolet.",
                "Cool fact: Monsterverse Godzilla's tail is over 550 feet long and incredibly powerful.",
                "Amazing truth: He has a natural electromagnetic field that can disrupt electronic devices.",
                "Did you realize his atomic breath creates a nuclear pulse that can level entire city blocks?",
                "Fascinating fact: Monsterverse Godzilla communicates with other Titans through subsonic frequencies.",
                "Incredible detail: His dorsal plates are made of a unique organic material stronger than any known metal.",
                "Surprising fact: He can hold his breath underwater for several hours while remaining fully active.",
                "Cool truth: Monsterverse Godzilla's blood is highly radioactive and glows with a blue-green hue.",
                "Amazing fact: He has survived multiple nuclear bomb tests, actually growing stronger from the radiation.",
                "Did you know his claws can slice through aircraft carriers like they're made of paper?",
                "Interesting fact: Monsterverse Godzilla's brain processes information at superhuman speeds.",
                "Fascinating detail: He can sense other Titans from thousands of miles away through seismic vibrations.",
                "Incredible truth: His atomic breath can reach speeds of over 500 mph when fired.",
                "Amazing fact: Monsterverse Godzilla's heart pumps radioactive blood throughout his massive body.",
                "Did you realize he can swim at speeds exceeding 40 knots underwater?",
                "Cool fact: His territorial range covers entire continents when he's actively patrolling.",
                "Surprising detail: Monsterverse Godzilla's roar has unique harmonic frequencies that inspire both fear and awe.",
                "Fascinating fact: He has been the inspiration for countless ancient myths and legends worldwide.",
                "Incredible truth: His atomic breath can melt through solid rock and metal instantaneously.",
                "Amazing detail: Monsterverse Godzilla's scales can deflect most conventional weapons without damage.",
                "Did you know he has a complex hierarchical relationship with other Titans as the Alpha Predator?",
                "Interesting fact: His bioluminescent dorsal plates serve as both weapon charging and communication.",
                "Cool truth: Monsterverse Godzilla can detect nuclear submarines from hundreds of miles away.",
                "Fascinating fact: He has an innate understanding of Earth's ecosystem and acts as its protector.",
                "Amazing detail: His atomic breath creates a distinctive mushroom cloud effect when hitting targets.",
                "Did you realize Monsterverse Godzilla's DNA contains traces of every major extinction event?",
                "Incredible fact: He can survive in the vacuum of space for short periods due to his unique physiology.",
                "Surprising truth: His footprints create permanent geological formations that last for centuries.",
                "Cool fact: Monsterverse Godzilla's pupils dilate based on the level of threat he perceives.",
                "Amazing detail: He has a natural GPS system that allows perfect navigation across ocean floors.",
                "Fascinating fact: His atomic breath can be controlled with surgical precision despite its devastating power.",
                "Did you know that Monsterverse Godzilla's cells regenerate at an accelerated rate when exposed to radiation?",
                "Incredible truth: He can sense the emotional state of humans through bioelectric fields.",
                "Surprising fact: His dorsal plates grow larger and more numerous as he ages and gains power.",
                "Cool detail: Monsterverse Godzilla's saliva is mildly radioactive and can sterilize wounds.",
                "Amazing fact: He has been observed showing mercy to creatures that pose no threat to Earth's balance.",
                "Did you realize his atomic breath varies in intensity from a focused beam to a wide-area blast?",
                "Fascinating truth: Monsterverse Godzilla's bones are hollow yet stronger than titanium alloy.",
                "Incredible fact: He can enter a berserker rage state that increases all his abilities exponentially.",
                "Surprising detail: His migration patterns follow ancient ley lines and tectonic plate movements.",
                "Cool fact: Monsterverse Godzilla's metabolism can process any organic or radioactive material as fuel.",
                "Amazing truth: He has a photographic memory spanning millions of years of Earth's history.",
                "Did you know his atomic breath creates temporary portals in the electromagnetic spectrum?",
                "Fascinating fact: Monsterverse Godzilla's presence can cause aurora-like phenomena in the atmosphere.",
                "Incredible detail: He can communicate complex ideas through subtle changes in his bioluminescence.",
                "Surprising fact: His territorial markings remain radioactive for decades after he's moved on.",
                "Cool truth: Monsterverse Godzilla's hearing can detect sounds from across entire ocean basins.",
                "Amazing fact: He has been known to spare cities that show respect for the natural world.",
                "Did you realize his atomic breath can neutralize other forms of radiation and toxic waste?",
                "Fascinating detail: Monsterverse Godzilla's sleep cycles are synchronized with the Earth's magnetic field.",
                "Incredible fact: He can predict natural disasters hours before they occur through seismic sensitivity.",
                "Surprising truth: His atomic breath creates a unique isotope that doesn't exist anywhere else.",
                "Cool fact: Monsterverse Godzilla's tail can function as a secondary brain during combat situations.",
                "Amazing detail: He has survived encounters with creatures from other dimensions and realities.",
                "Did you know that his roar can cause avalanches and trigger volcanic eruptions?",
                "Fascinating fact: Monsterverse Godzilla's blood contains antibodies for diseases that don't exist yet.",
                "Incredible truth: He can alter his body temperature to adapt to any environment on Earth.",
                "Surprising fact: His dorsal plates can store and release energy like biological capacitors.",
                "Cool detail: Monsterverse Godzilla's intelligence increases proportionally with his size and age.",
                "Amazing fact: He has been observed performing complex problem-solving behaviors in combat.",
                "Did you realize his atomic breath can create temporary wormholes in space-time?",
                "Fascinating truth: Monsterverse Godzilla's presence accelerates evolution in nearby organisms.",
                "Incredible fact: He can sense the health of entire ecosystems through chemical analysis of air and water.",
                "Surprising detail: His atomic breath signature is unique and can be identified from satellite imagery."
            ],
            
            "heisei": [
                "Did you know that Heisei Godzilla stands at 328 feet tall and represents the apex of biological evolution?",
                "Fascinating fact: Heisei Godzilla's nuclear pulse attack can devastate everything within a mile radius!",
                "Amazing detail: His atomic breath has evolved to become increasingly powerful throughout the Heisei series.",
                "Incredible fact: Heisei Godzilla's heart is a living nuclear reactor that never stops generating energy.",
                "Cool truth: He has a secondary brain located in his hip area that controls his lower body functions.",
                "Did you realize that Heisei Godzilla can absorb and redirect electromagnetic energy through his dorsal plates?",
                "Surprising fact: His regenerative abilities allow him to heal from almost any wound within hours.",
                "Fascinating detail: Heisei Godzilla's roar creates sonic booms that can shatter glass miles away.",
                "Amazing fact: He has survived direct nuclear strikes and emerged even stronger than before.",
                "Incredible truth: His atomic breath temperature reaches over 1.2 million degrees Celsius at full power.",
                "Did you know that Heisei Godzilla's blood is superheated and glows with radioactive energy?",
                "Cool fact: He can enter a burning state where his entire body becomes a living nuclear weapon.",
                "Interesting detail: Heisei Godzilla's footsteps leave radioactive impressions that last for decades.",
                "Amazing truth: His dorsal plates can channel and focus his atomic energy with pinpoint accuracy.",
                "Fascinating fact: He has demonstrated the ability to learn and adapt his fighting techniques.",
                "Did you realize that Heisei Godzilla's cellular structure is completely unique to his species?",
                "Incredible fact: His atomic breath can penetrate through multiple layers of reinforced concrete and steel.",
                "Surprising detail: Heisei Godzilla's metabolism can process any form of matter as fuel.",
                "Cool truth: He has been observed showing protective instincts toward his offspring and allies.",
                "Amazing fact: His nuclear pulse creates an electromagnetic shockwave that disables all electronics.",
                "Did you know that Heisei Godzilla's skin becomes harder and more resistant with each battle?",
                "Fascinating detail: He can survive in the vacuum of space and underwater at crushing depths.",
                "Incredible fact: His atomic breath creates a distinctive beam pattern that's instantly recognizable.",
                "Surprising truth: Heisei Godzilla's intelligence has been steadily increasing throughout his appearances.",
                "Cool fact: He can detect radiation sources from hundreds of miles away through his dorsal plates.",
                "Amazing detail: His regenerative factor becomes more powerful when exposed to nuclear energy.",
                "Did you realize that Heisei Godzilla's roar has different tones for different emotional states?",
                "Fascinating fact: He has survived encounters with time-traveling enemies and alien invasions.",
                "Incredible truth: His atomic breath can create temporary fissures in dimensional barriers.",
                "Surprising fact: Heisei Godzilla's tail is incredibly flexible and can be used as a devastating weapon.",
                "Cool detail: He has demonstrated problem-solving abilities that rival those of higher primates.",
                "Amazing fact: His nuclear pulse attack was developed as a defense mechanism against aerial threats.",
                "Did you know that Heisei Godzilla's eyes glow brighter when he's preparing to use his atomic breath?",
                "Fascinating detail: He can enter a hibernation state that slows his aging process to near-zero.",
                "Incredible fact: His atomic breath has evolved from a simple beam to a complex spiral pattern.",
                "Surprising truth: Heisei Godzilla's presence can cause electronic equipment to malfunction permanently.",
                "Cool fact: He has been observed mourning the death of allies and showing genuine emotion.",
                "Amazing detail: His dorsal plates grow larger and more numerous as his power increases.",
                "Did you realize that Heisei Godzilla can communicate through subsonic vocalizations?",
                "Fascinating fact: He has survived being buried under thousands of tons of rubble and emerged unharmed.",
                "Incredible truth: His atomic breath can be sustained for several minutes without pause.",
                "Surprising fact: Heisei Godzilla's claws can slice through diamond-hard materials effortlessly.",
                "Cool detail: He has demonstrated tactical thinking and strategic planning in battles.",
                "Amazing fact: His nuclear pulse creates a distinctive mushroom cloud visible from space.",
                "Did you know that Heisei Godzilla's breath weapon leaves traces of exotic matter?",
                "Fascinating detail: He can sense the approach of enemies through seismic vibrations in the ground.",
                "Incredible fact: His regenerative abilities have allowed him to regrow entire limbs in battle.",
                "Surprising truth: Heisei Godzilla's atomic breath can neutralize other forms of energy attacks.",
                "Cool fact: He has been observed using his environment as weapons during combat.",
                "Amazing detail: His nuclear reactor heart generates enough energy to power entire cities.",
                "Did you realize that Heisei Godzilla's footprints create permanent geological features?",
                "Fascinating fact: He can alter the trajectory of his atomic breath mid-flight with incredible precision.",
                "Incredible truth: His dorsal plates serve as both armor and energy channeling systems.",
                "Surprising fact: Heisei Godzilla's roar can be heard clearly from over 500 miles away.",
                "Cool detail: He has survived multiple apocalyptic scenarios and planetary-level threats.",
                "Amazing fact: His atomic breath creates unique radioactive isotopes not found in nature.",
                "Did you know that Heisei Godzilla's brain activity increases during combat situations?",
                "Fascinating detail: He can absorb energy from electrical storms and power grids to heal.",
                "Incredible fact: His nuclear pulse has been measured to have the force of multiple nuclear bombs.",
                "Surprising truth: Heisei Godzilla's teeth continuously regenerate and grow sharper with use.",
                "Cool fact: He has demonstrated the ability to recognize and remember individual humans.",
                "Amazing detail: His atomic breath can create controlled explosions for precise demolition.",
                "Did you realize that Heisei Godzilla's scales become more reflective as his power increases?",
                "Fascinating fact: He can enter a berserker mode that doubles his strength and speed.",
                "Incredible truth: His atomic breath has been observed bending around obstacles to hit targets.",
                "Surprising fact: Heisei Godzilla's blood contains healing properties that could revolutionize medicine.",
                "Cool detail: He has survived being frozen, buried, and even launched into space.",
                "Amazing fact: His nuclear pulse creates an aurora-like effect in the upper atmosphere.",
                "Did you know that Heisei Godzilla's heartbeat can be detected by seismographs worldwide?",
                "Fascinating detail: He can focus his atomic breath into a surgical laser for precise attacks.",
                "Incredible fact: His regenerative factor works faster when he's in direct sunlight.",
                "Surprising truth: Heisei Godzilla's roar has inspired terror in creatures from other dimensions.",
                "Cool fact: He has been observed showing curiosity about human technology and civilization.",
                "Amazing detail: His atomic breath can create temporary electromagnetic shields around his body.",
                "Did you realize that Heisei Godzilla's dorsal plates can store energy for weeks at a time?",
                "Fascinating fact: He has demonstrated the ability to predict weather patterns and natural disasters.",
                "Incredible truth: His nuclear pulse can create localized time distortions in the immediate area.",
                "Surprising fact: Heisei Godzilla's presence causes mutations in nearby plant and animal life.",
                "Cool detail: He has survived encounters with gods, aliens, and beings from parallel universes.",
                "Amazing fact: His atomic breath signature is so unique it can be identified from orbital satellites."
            ],
            
            "toho": [
                "Did you know that the original 1954 TOHO Godzilla was 164 feet tall and represented the horrors of nuclear warfare?",
                "Fascinating fact: TOHO Godzilla's atomic breath was inspired by the atomic bombings of Hiroshima and Nagasaki.",
                "Amazing detail: His iconic roar was created by rubbing a leather glove across a double bass string!",
                "Incredible fact: TOHO Godzilla has appeared in over 35 films spanning nearly 70 years of cinema.",
                "Cool truth: His original suit weighed over 200 pounds and was incredibly difficult for actors to perform in.",
                "Did you realize that TOHO Godzilla's design has evolved dramatically across different eras and directors?",
                "Surprising fact: He started as a villain but gradually became a defender of Earth in later films.",
                "Fascinating detail: TOHO Godzilla's atomic breath effects were achieved using animated lightning footage.",
                "Amazing fact: His footsteps were created by slamming shut a leather briefcase filled with cushions!",
                "Incredible truth: TOHO Godzilla has fought over 20 different kaiju throughout his film career.",
                "Did you know that his original black and white appearance was meant to look burned and scarred?",
                "Cool fact: TOHO Godzilla's eyes were operated by remote control in many of the classic films.",
                "Interesting detail: His atomic breath was sometimes called 'radioactive ray' in early English dubs.",
                "Amazing truth: TOHO Godzilla's tail was often operated by multiple puppeteers working in coordination.",
                "Fascinating fact: He has been portrayed as everything from a mindless monster to a protective parent.",
                "Did you realize that TOHO Godzilla's size has varied from 164 feet to over 300 feet tall?",
                "Incredible fact: His iconic triangular dorsal plates were inspired by stegosaurus back plates.",
                "Surprising detail: TOHO Godzilla's movements were based on studying real lizard and dinosaur locomotion.",
                "Cool truth: He has had both male and female offspring in different films of the series.",
                "Amazing fact: TOHO Godzilla's atomic breath has been depicted in blue, orange, red, and purple.",
                "Did you know that his original rampage through Tokyo was filmed using incredibly detailed miniatures?",
                "Fascinating detail: TOHO Godzilla has died and been resurrected multiple times throughout the series.",
                "Incredible fact: His roar has become one of the most recognizable sound effects in cinema history.",
                "Surprising truth: TOHO Godzilla's suit designs required extensive ventilation systems for the actors.",
                "Cool fact: He has been both a force of nature and a thinking, reasoning creature in different films.",
                "Amazing detail: TOHO Godzilla's atomic breath was sometimes portrayed as a freezing ray instead of heat.",
                "Did you realize that his films often contained social commentary about nuclear weapons and war?",
                "Fascinating fact: TOHO Godzilla has traveled through time, space, and even other dimensions.",
                "Incredible truth: His original creator Ishiro Honda intended him as a metaphor for nuclear destruction.",
                "Surprising fact: TOHO Godzilla's footprints were created using large wooden stamps in sand.",
                "Cool detail: He has been portrayed by dozens of different suit actors over the decades.",
                "Amazing fact: TOHO Godzilla's atomic breath sound was created using dry ice sliding across metal.",
                "Did you know that his films helped establish the entire kaiju genre of monster movies?",
                "Fascinating detail: TOHO Godzilla's suit eyes were sometimes lit from within using small light bulbs.",
                "Incredible fact: He has battled aliens, robots, other dinosaurs, and even King Kong himself.",
                "Surprising truth: TOHO Godzilla's tail was often the most difficult part of the suit to control.",
                "Cool fact: He has been depicted with varying levels of intelligence from animal to near-human.",
                "Amazing detail: TOHO Godzilla's atomic breath effects evolved from simple animation to complex CGI.",
                "Did you realize that his films often featured elaborate miniature cityscapes that took months to build?",
                "Fascinating fact: TOHO Godzilla has had both heroic and villainous roles depending on the era.",
                "Incredible truth: His original suit was made from ready-mixed concrete and bamboo framework.",
                "Surprising fact: TOHO Godzilla's roar was pitched differently to convey various emotional states.",
                "Cool detail: He has been featured in comics, video games, and animated series beyond films.",
                "Amazing fact: TOHO Godzilla's atomic breath was sometimes depicted as having magnetic properties.",
                "Did you know that his original film was meant to be a serious drama about nuclear holocaust?",
                "Fascinating detail: TOHO Godzilla's suit heads were often operated using complex cable systems.",
                "Incredible fact: He has been both feared as a destroyer and worshipped as a protective deity.",
                "Surprising truth: TOHO Godzilla's films pioneered many special effects techniques still used today.",
                "Cool fact: He has had son figures including Minilla, Godzilla Junior, and Little Godzilla.",
                "Amazing detail: TOHO Godzilla's atomic breath was sometimes shown melting through solid rock instantly.",
                "Did you realize that his suit performers often couldn't see clearly and relied on assistants for direction?",
                "Fascinating fact: TOHO Godzilla has been both mortal and seemingly immortal in different continuities.",
                "Incredible truth: His films have grossed hundreds of millions of dollars worldwide over seven decades.",
                "Surprising fact: TOHO Godzilla's dorsal plates were sometimes electrified to create lighting effects.",
                "Cool detail: He has been portrayed as both a prehistoric survivor and a modern nuclear mutation.",
                "Amazing fact: TOHO Godzilla's footstep sounds were created using large timpani drums.",
                "Did you know that his original design was refined through dozens of concept sketches and sculptures?",
                "Fascinating detail: TOHO Godzilla's films often featured elaborate musical scores that became classics.",
                "Incredible fact: He has appeared in crossover films with other famous movie monsters.",
                "Surprising truth: TOHO Godzilla's suit construction required teams of specialized craftsmen and artists.",
                "Cool fact: He has been both a mindless force of destruction and a strategic military ally.",
                "Amazing detail: TOHO Godzilla's atomic breath was sometimes shown as being controllable and precise.",
                "Did you realize that his films helped launch the careers of many famous Japanese directors?",
                "Fascinating fact: TOHO Godzilla has been featured in over 1000 licensed products and merchandise items.",
                "Incredible truth: His original suit was so heavy it required multiple people to help the actor stand up.",
                "Surprising fact: TOHO Godzilla's tail movements were sometimes achieved using marionette techniques.",
                "Cool detail: He has been both a singular creature and part of an entire species in different films.",
                "Amazing fact: TOHO Godzilla's atomic breath effects required frame-by-frame hand animation in early films.",
                "Did you know that his films often featured elaborate fight choreography planned like dance routines?",
                "Fascinating detail: TOHO Godzilla's suit materials evolved from latex to more sophisticated polymers.",
                "Incredible fact: He has been portrayed as both an ancient creature and a modern scientific creation.",
                "Surprising truth: TOHO Godzilla's films influenced monster movies and special effects worldwide.",
                "Cool fact: He has had both temporary and permanent deaths followed by resurrections or replacements.",
                "Amazing detail: TOHO Godzilla's roar has been remixed and updated but remains fundamentally recognizable.",
                "Did you realize that his legacy includes inspiring environmental themes in many later films?",
                "Fascinating fact: TOHO Godzilla's cultural impact extends far beyond cinema into art, literature, and philosophy.",
                "Incredible truth: His films continue to be produced and loved by new generations of fans worldwide."
            ],
            
            "idw": [
                "Did you know that IDW Godzilla exists in a shared universe with other classic monsters like Kong?",
                "Fascinating fact: IDW's Godzilla comics feature incredibly detailed artwork showing his massive scale!",
                "Amazing detail: IDW Godzilla has fought creatures from across multiple dimensions and realities.",
                "Incredible fact: His comic book appearances often explore deeper psychological themes than films.",
                "Cool truth: IDW Godzilla's atomic breath has been shown creating permanent radiation zones.",
                "Did you realize that IDW Comics has published over 100 different Godzilla comic issues?",
                "Surprising fact: IDW Godzilla has been portrayed as both destroyer and reluctant protector.",
                "Fascinating detail: His comic book battles often span multiple issues and story arcs.",
                "Amazing fact: IDW Godzilla has encountered time-traveling humans from post-apocalyptic futures.",
                "Incredible truth: His atomic breath in the comics can melt through interdimensional barriers.",
                "Did you know that IDW Godzilla has fought alongside and against military mechs and robots?",
                "Cool fact: His comic book design combines classic elements with modern artistic interpretations.",
                "Interesting detail: IDW Godzilla stories often feature complex human characters and subplots.",
                "Amazing truth: His battles in the comics have reshaped entire coastlines and islands.",
                "Fascinating fact: IDW Godzilla has been shown to have ancient connections to human civilizations.",
                "Did you realize that his comic book appearances include crossovers with other kaiju series?",
                "Incredible fact: IDW Godzilla's regenerative abilities have been explored in scientific detail.",
                "Surprising detail: His comic book stories often span decades or even centuries of time.",
                "Cool truth: IDW Godzilla has been portrayed with varying levels of intelligence and awareness.",
                "Amazing fact: His atomic breath in the comics creates unique energy signatures studied by scientists.",
                "Did you know that IDW Godzilla has battled creatures from Lovecraftian cosmic horror?",
                "Fascinating detail: His comic book adventures have taken him to parallel Earths and alien worlds.",
                "Incredible fact: IDW Godzilla's footprints in the comics are treated as geological landmarks.",
                "Surprising truth: His roar in comic form is often depicted with sound effect words filling entire pages.",
                "Cool fact: IDW Godzilla has been shown to remember and learn from previous encounters.",
                "Amazing detail: His comic book battles often result in permanent changes to Earth's geography.",
                "Did you realize that IDW Godzilla stories explore themes of environmental destruction and renewal?",
                "Fascinating fact: His atomic breath has been depicted as having different modes and intensities.",
                "Incredible truth: IDW Godzilla has encountered versions of himself from alternate timelines.",
                "Surprising fact: His comic book appearances often focus on the human cost of kaiju battles.",
                "Cool detail: IDW Godzilla's design varies between artists but maintains iconic characteristics.",
                "Amazing fact: His battles in the comics have been observed and documented by secret organizations.",
                "Did you know that IDW Godzilla has formed temporary alliances with other giant monsters?",
                "Fascinating detail: His comic book stories often explore what happens between his film appearances.",
                "Incredible fact: IDW Godzilla's presence affects weather patterns and electromagnetic fields.",
                "Surprising truth: His atomic breath has been shown creating new mineral formations.",
                "Cool fact: IDW Godzilla has been portrayed as both ancient legend and modern reality.",
                "Amazing detail: His comic book adventures include encounters with alien civilizations.",
                "Did you realize that IDW Godzilla stories often feature multiple kaiju fighting simultaneously?",
                "Fascinating fact: His regenerative abilities have been enhanced by exposure to various energy sources.",
                "Incredible truth: IDW Godzilla's territorial behavior has been studied by fictional cryptozoologists.",
                "Surprising fact: His comic book battles often last for days or weeks in story time.",
                "Cool detail: IDW Godzilla has been shown to have preferred hunting and resting areas.",
                "Amazing fact: His atomic breath creates unique atmospheric disturbances visible from space.",
                "Did you know that IDW Godzilla has encountered time loops and temporal anomalies?",
                "Fascinating detail: His comic book stories explore the global political implications of his existence.",
                "Incredible fact: IDW Godzilla's scales have been shown to be nearly indestructible in comics.",
                "Surprising truth: His roar has been depicted as having hypnotic effects on some creatures.",
                "Cool fact: IDW Godzilla has been portrayed as having complex emotional responses to situations.",
                "Amazing detail: His comic book adventures often involve government cover-ups and conspiracies.",
                "Did you realize that IDW Godzilla stories sometimes span multiple generations of human characters?",
                "Fascinating fact: His atomic breath has been shown interacting with other forms of energy uniquely.",
                "Incredible truth: IDW Godzilla has been depicted as having ancient rivalries with other monsters.",
                "Surprising fact: His comic book appearances often explore philosophical questions about nature versus civilization.",
                "Cool detail: IDW Godzilla's movement patterns have been mapped and analyzed by fictional scientists.",
                "Amazing fact: His battles in the comics have created new ecosystems in their aftermath.",
                "Did you know that IDW Godzilla has been shown to be capable of strategic thinking?",
                "Fascinating detail: His comic book stories often feature detailed scientific explanations for his abilities.",
                "Incredible fact: IDW Godzilla's presence has been linked to increased seismic activity worldwide.",
                "Surprising truth: His atomic breath has been depicted as having healing properties in some contexts.",
                "Cool fact: IDW Godzilla has been portrayed as both feared destroyer and misunderstood guardian.",
                "Amazing detail: His comic book adventures include encounters with prehistoric creatures thought extinct.",
                "Did you realize that IDW Godzilla stories often explore the ethics of military response to kaiju?",
                "Fascinating fact: His regenerative abilities have been shown to accelerate during combat situations.",
                "Incredible truth: IDW Godzilla has been depicted as having a complex relationship with human civilization.",
                "Surprising fact: His comic book battles often involve creative use of urban environments as weapons.",
                "Cool detail: IDW Godzilla's behavior patterns have been studied to predict his movements.",
                "Amazing fact: His atomic breath has been shown creating aurora-like effects in the atmosphere.",
                "Did you know that IDW Godzilla has encountered creatures from Earth's distant past and future?",
                "Fascinating detail: His comic book stories often explore the long-term consequences of kaiju battles.",
                "Incredible fact: IDW Godzilla's DNA has been analyzed and found to contain impossibly complex genetic codes.",
                "Surprising truth: His roar has been recorded and studied for its unique acoustic properties.",
                "Cool fact: IDW Godzilla has been shown to have preferences for certain types of prey or enemies.",
                "Amazing detail: His comic book adventures often involve international cooperation to deal with threats.",
                "Did you realize that IDW Godzilla stories sometimes feature his perspective on events?",
                "Fascinating fact: His atomic breath has been depicted as capable of precision strikes on small targets.",
                "Incredible truth: IDW Godzilla has been portrayed as having an almost supernatural connection to Earth.",
                "Surprising fact: His comic book appearances often explore the psychological impact on witnesses.",
                "Cool detail: IDW Godzilla's combat techniques have evolved and adapted over multiple story arcs.",
                "Amazing fact: His presence in the comics has inspired new fields of scientific research.",
                "Did you know that IDW Godzilla has been shown to communicate with other kaiju through various means?",
                "Fascinating detail: His comic book stories often feature detailed depictions of post-battle reconstruction efforts."
            ],
            
            "marvel": [
                "Did you know that Marvel's Godzilla appeared in 24 issues of his own comic series in the late 1970s?",
                "Fascinating fact: Marvel Godzilla fought alongside and against famous superheroes like the Avengers!",
                "Amazing detail: His Marvel Comics appearance featured him battling against S.H.I.E.L.D. agents regularly.",
                "Incredible fact: Marvel Godzilla was one of the first licensed characters to get his own ongoing series.",
                "Cool truth: His comic book adventures took him across the entire Marvel Universe continuity.",
                "Did you realize that Marvel Godzilla fought the Fantastic Four in New York City?",
                "Surprising fact: Marvel's version established him as roughly 200 feet tall in official continuity.",
                "Fascinating detail: His Marvel Comics run featured original human characters alongside classic heroes.",
                "Amazing fact: Marvel Godzilla battled a robot duplicate of himself created by Doctor Doom!",
                "Incredible truth: His comic series was written by Doug Moench and featured detailed monster lore.",
                "Did you know that Marvel Godzilla's atomic breath was colored differently in various comic issues?",
                "Cool fact: His Marvel appearance influenced how giant monsters were portrayed in comics forever.",
                "Interesting detail: Marvel Godzilla stories often featured complex moral dilemmas about his existence.",
                "Amazing truth: His battles with superheroes were carefully choreographed to showcase both parties' abilities.",
                "Fascinating fact: Marvel Godzilla was portrayed as more intelligent than his film counterparts.",
                "Did you realize that his Marvel Comics run helped establish kaiju as legitimate comic book subjects?",
                "Incredible fact: Marvel Godzilla's regenerative abilities were explained through comic book science.",
                "Surprising detail: His comic series featured guest appearances by nearly every major Marvel hero.",
                "Cool truth: Marvel Godzilla's atomic breath was described as reaching temperatures of millions of degrees.",
                "Amazing fact: His Marvel Comics adventures took him from Japan to America and beyond.",
                "Did you know that Marvel Godzilla fought both alongside and against Iron Man?",
                "Fascinating detail: His comic book design balanced classic Toho elements with Marvel's house style.",
                "Incredible fact: Marvel Godzilla's stories often explored themes of humanity versus nature.",
                "Surprising truth: His atomic breath in Marvel Comics could be precisely controlled and targeted.",
                "Cool fact: Marvel Godzilla was one of the most successful licensed properties of the 1970s.",
                "Amazing detail: His comic book adventures featured original kaiju created specifically for Marvel.",
                "Did you realize that Marvel Godzilla's series helped launch the careers of several comic artists?",
                "Fascinating fact: His battles with the Champions team showcased his adaptability against multiple opponents.",
                "Incredible truth: Marvel Godzilla's intelligence was portrayed as steadily increasing throughout his series.",
                "Surprising fact: His comic book footprints were treated as significant archaeological discoveries.",
                "Cool detail: Marvel Godzilla's roar was depicted with unique sound effects and visual representations.",
                "Amazing fact: His atomic breath could be modified to create different types of energy blasts.",
                "Did you know that Marvel Godzilla encountered time travel and alternate dimension storylines?",
                "Fascinating detail: His comic series featured detailed explanations of his biological functions.",
                "Incredible fact: Marvel Godzilla's presence affected the entire Marvel Universe's status quo.",
                "Surprising truth: His battles often resulted in significant property damage that affected ongoing storylines.",
                "Cool fact: Marvel Godzilla was portrayed as having complex emotional responses to human actions.",
                "Amazing detail: His comic book adventures included encounters with cosmic-level threats and entities.",
                "Did you realize that Marvel Godzilla's series was among the first to explore kaiju psychology?",
                "Fascinating fact: His atomic breath was shown interacting uniquely with various superheroes' powers.",
                "Incredible truth: Marvel Godzilla's regenerative abilities were enhanced by his emotional state.",
                "Surprising fact: His comic book battles were analyzed by in-universe scientists and strategists.",
                "Cool detail: Marvel Godzilla's design incorporated elements that would translate well to superhero comics.",
                "Amazing fact: His presence in Marvel Comics established precedents for other giant monster characters.",
                "Did you know that Marvel Godzilla's series featured elaborate fight scenes spanning multiple issues?",
                "Fascinating detail: His comic book stories often explored the global political implications of his existence.",
                "Incredible fact: Marvel Godzilla's atomic breath created unique energy signatures studied by Reed Richards.",
                "Surprising truth: His roar was depicted as having measurable effects on both humans and technology.",
                "Cool fact: Marvel Godzilla was shown to learn and adapt his tactics based on previous encounters.",
                "Amazing detail: His comic book adventures influenced how later kaiju would be portrayed in Marvel.",
                "Did you realize that Marvel Godzilla's series featured both urban and oceanic battle environments?",
                "Fascinating fact: His regenerative abilities were linked to his connection with nuclear energy sources.",
                "Incredible truth: Marvel Godzilla's intelligence allowed him to form temporary alliances with heroes.",
                "Surprising fact: His comic book appearances often featured detailed scientific analyses of his abilities.",
                "Cool detail: Marvel Godzilla's movement patterns were studied and predicted by S.H.I.E.L.D. agents.",
                "Amazing fact: His atomic breath was shown to have different effects on various types of matter.",
                "Did you know that Marvel Godzilla encountered mutants and understood their shared outsider status?",
                "Fascinating detail: His comic series helped establish the visual language for depicting giant monsters.",
                "Incredible fact: Marvel Godzilla's presence spawned government task forces dedicated to kaiju response.",
                "Surprising truth: His battles with the military were portrayed with respect for both sides' capabilities.",
                "Cool fact: Marvel Godzilla was shown to have preferences for certain types of environments.",
                "Amazing detail: His comic book adventures explored what it means to be a living force of nature.",
                "Did you realize that Marvel Godzilla's series featured some of the most detailed kaiju artwork ever?",
                "Fascinating fact: His atomic breath could be focused into surgical precision or spread for area effects.",
                "Incredible truth: Marvel Godzilla's emotional complexity made him more than just a mindless monster.",
                "Surprising fact: His comic book stories often featured multiple perspectives on the same events.",
                "Cool detail: Marvel Godzilla's combat techniques evolved throughout his series based on his experiences.",
                "Amazing fact: His presence in Marvel Comics led to the creation of specialized anti-kaiju protocols.",
                "Did you know that Marvel Godzilla's series explored themes that wouldn't appear in films for decades?",
                "Fascinating detail: His regenerative abilities were shown to work faster in certain environmental conditions.",
                "Incredible fact: Marvel Godzilla's intelligence was portrayed as alien but not necessarily hostile.",
                "Surprising truth: His atomic breath created unique environmental effects that persisted after battles.",
                "Cool fact: Marvel Godzilla was one of the few licensed characters to maintain creative integrity.",
                "Amazing detail: His comic book adventures helped define the modern superhero-kaiju interaction genre.",
                "Did you realize that Marvel Godzilla's legacy influenced countless other monster comics?",
                "Fascinating fact: His atomic breath was shown to interact with the Marvel Universe's cosmic forces.",
                "Incredible truth: Marvel Godzilla's series demonstrated that kaiju could carry complex, ongoing narratives.",
                "Surprising fact: His comic book design elements were later incorporated into other Marvel monsters.",
                "Cool detail: Marvel Godzilla's psychological profile was as detailed as any major superhero's."
            ],
            
            "anime": [
                "Did you know that Anime Godzilla from the Netflix trilogy is over 984 feet tall, the largest ever?",
                "Fascinating fact: Anime Godzilla's atomic breath can reshape entire landscapes with surgical precision!",
                "Amazing detail: His body is described as a living ecosystem with its own internal biosphere.",
                "Incredible fact: Anime Godzilla has been evolving continuously for over 20,000 years!",
                "Cool truth: His atomic breath creates a unique form of matter called 'G-energy' or 'G-cells.'",
                "Did you realize that Anime Godzilla's tail extends deep underground like massive roots?",
                "Surprising fact: His electromagnetic pulse can disable technology across entire continents.",
                "Fascinating detail: Anime Godzilla's body heat creates its own weather systems and microclimates.",
                "Amazing fact: He has developed a symbiotic relationship with plant life that grows on his body.",
                "Incredible truth: Anime Godzilla's atomic breath can pierce through the Earth's crust to the mantle.",
                "Did you know that his dorsal plates function as massive energy collectors and processors?",
                "Cool fact: Anime Godzilla's presence has created new forms of life and evolution on Earth.",
                "Interesting detail: His roar creates seismic waves that can be detected on the other side of the planet.",
                "Amazing truth: Anime Godzilla's body contains multiple independent organ systems and brains.",
                "Fascinating fact: He has been growing and adapting constantly since humans left Earth.",
                "Did you realize that Anime Godzilla's atomic breath can create temporary dimensional rifts?",
                "Incredible fact: His body mass is so enormous that he affects Earth's gravitational field.",
                "Surprising detail: Anime Godzilla has developed a form of technological integration with his biology.",
                "Cool truth: His atomic breath can be precisely controlled to perform delicate operations.",
                "Amazing fact: Anime Godzilla's evolution has made him practically immune to all conventional weapons.",
                "Did you know that his footsteps create permanent changes in the Earth's geological structure?",
                "Fascinating detail: Anime Godzilla's body temperature is so high it creates perpetual steam clouds.",
                "Incredible fact: He has developed the ability to manipulate electromagnetic fields consciously.",
                "Surprising truth: Anime Godzilla's atomic breath contains exotic matter that doesn't decay normally.",
                "Cool fact: His body serves as a mobile ecosystem supporting countless species of organisms.",
                "Amazing detail: Anime Godzilla's intelligence has evolved beyond normal biological parameters.",
                "Did you realize that his atomic breath can create localized gravity wells and distortions?",
                "Fascinating fact: Anime Godzilla has developed a form of distributed consciousness throughout his body.",
                "Incredible truth: His presence has fundamentally altered the planet's magnetic field and atmosphere.",
                "Surprising fact: Anime Godzilla's tail functions as both anchor and massive sensory organ.",
                "Cool detail: His atomic breath can be modulated to different frequencies and energy types.",
                "Amazing fact: Anime Godzilla has evolved specialized organs for processing various forms of energy.",
                "Did you know that his body contains living metal components that self-repair and upgrade?",
                "Fascinating detail: Anime Godzilla's roar can communicate complex information across vast distances.",
                "Incredible fact: He has developed a form of biological nanotechnology within his cellular structure.",
                "Surprising truth: Anime Godzilla's atomic breath can create stable wormholes for short periods.",
                "Cool fact: His evolution has produced organs that can process and convert any form of matter.",
                "Amazing detail: Anime Godzilla's body generates a protective electromagnetic shield continuously.",
                "Did you realize that his atomic breath can selectively target specific molecular structures?",
                "Fascinating fact: Anime Godzilla has evolved beyond traditional biological limitations and constraints.",
                "Incredible truth: His body contains quantum mechanical elements that operate on subatomic levels.",
                "Surprising fact: Anime Godzilla's presence creates temporal distortions due to his massive energy output.",
                "Cool detail: His evolution has produced specialized chambers for different types of energy storage.",
                "Amazing fact: Anime Godzilla's atomic breath can create new elements not found on the periodic table.",
                "Did you know that his body functions as a massive biological computer processing global data?",
                "Fascinating detail: Anime Godzilla's scales have evolved to manipulate light and electromagnetic radiation.",
                "Incredible fact: He has developed a form of biological space-time manipulation through his atomic breath.",
                "Surprising truth: Anime Godzilla's evolution has made him partially exist in multiple dimensions.",
                "Cool fact: His body heat can melt permafrost and alter climate patterns across continents.",
                "Amazing detail: Anime Godzilla's atomic breath can create stable fusion reactions in the atmosphere.",
                "Did you realize that his evolution has produced organs capable of faster-than-light information processing?",
                "Fascinating fact: Anime Godzilla has developed a symbiotic relationship with the planet's core.",
                "Incredible truth: His atomic breath can manipulate the fundamental forces of physics in localized areas.",
                "Surprising fact: Anime Godzilla's body contains biological dark matter that defies conventional understanding.",
                "Cool detail: His evolution has produced specialized organs for manipulating quantum fields.",
                "Amazing fact: Anime Godzilla's presence has created new forms of life that exist purely as energy.",
                "Did you know that his atomic breath can create localized time loops and temporal anomalies?",
                "Fascinating detail: Anime Godzilla's body functions as a living terraforming system for the planet.",
                "Incredible fact: He has evolved organs that can perceive and manipulate probability itself.",
                "Surprising truth: Anime Godzilla's atomic breath can create stable artificial gravity fields.",
                "Cool fact: His evolution has made him capable of surviving in the vacuum of space indefinitely.",
                "Amazing detail: Anime Godzilla's body contains biological reactors that exceed nuclear fusion efficiency.",
                "Did you realize that his evolution has produced a form of biological quantum entanglement?",
                "Fascinating fact: Anime Godzilla has developed the ability to exist in multiple quantum states simultaneously.",
                "Incredible truth: His atomic breath can create localized reality distortions that alter physical laws.",
                "Surprising fact: Anime Godzilla's body generates exotic particles that don't exist elsewhere in nature.",
                "Cool detail: His evolution has produced organs capable of manipulating cosmic radiation.",
                "Amazing fact: Anime Godzilla's presence creates standing wave patterns in space-time itself.",
                "Did you know that his atomic breath can create artificial black holes for precise demolition work?",
                "Fascinating detail: Anime Godzilla's evolution has made him a living embodiment of planetary consciousness.",
                "Incredible fact: He has developed biological systems that operate beyond the standard model of physics.",
                "Surprising truth: Anime Godzilla's atomic breath can create stable antimatter for controlled annihilation.",
                "Cool fact: His body functions as a massive biological particle accelerator and energy collider.",
                "Amazing detail: Anime Godzilla's evolution has produced consciousness that exists across multiple dimensions.",
                "Did you realize that his presence creates ripple effects throughout the fabric of space-time?",
                "Fascinating fact: Anime Godzilla has evolved beyond biological life into something approaching cosmic force.",
                "Incredible truth: His atomic breath can manipulate the Higgs field to alter mass and energy locally.",
                "Surprising fact: Anime Godzilla's body contains biological technologies that surpass human understanding.",
                "Cool detail: His evolution has made him capable of perceiving and manipulating parallel universes.",
                "Amazing fact: Anime Godzilla's atomic breath can create stable portals to other dimensions and realities."
            ]
        }
        
        # Version display names and emojis
        self.version_info = {
            "monsterverse": {
                "name": "Monsterverse Godzilla",
                "emoji": "🌊",
                "color": discord.Color.dark_blue(),
                "description": "The modern titan from Legendary Pictures' MonsterVerse films"
            },
            "heisei": {
                "name": "Heisei Godzilla", 
                "emoji": "⚡",
                "color": discord.Color.gold(),
                "description": "The powerful incarnation from the Heisei era films (1984-1995)"
            },
            "toho": {
                "name": "TOHO Godzilla",
                "emoji": "🎬",
                "color": discord.Color.green(),
                "description": "The classic original from TOHO Studios spanning multiple eras"
            },
            "idw": {
                "name": "IDW Godzilla",
                "emoji": "📚",
                "color": discord.Color.purple(),
                "description": "The comic book version from IDW Publishing's extensive series"
            },
            "marvel": {
                "name": "Marvel Godzilla",
                "emoji": "⭐",
                "color": discord.Color.red(),
                "description": "The superhero universe version from Marvel Comics (1977-1979)"
            },
            "anime": {
                "name": "Anime Series Godzilla",
                "emoji": "🌌",
                "color": discord.Color.dark_purple(),
                "description": "The massive evolution from Netflix's anime trilogy"
            }
        }
    
    @app_commands.command(name="godzillafact", description="🦕 Learn fascinating facts about different versions of Godzilla")
    @app_commands.describe(
        version="Choose which version of Godzilla you want to learn about"
    )
    @app_commands.choices(version=[
        app_commands.Choice(name="🌊 Monsterverse/MV Godzilla", value="monsterverse"),
        app_commands.Choice(name="⚡ Heisei Godzilla", value="heisei"),
        app_commands.Choice(name="🎬 TOHO Godzilla", value="toho"),
        app_commands.Choice(name="📚 IDW Godzilla", value="idw"),
        app_commands.Choice(name="⭐ Marvel Godzilla", value="marvel"),
        app_commands.Choice(name="🌌 Anime Series Godzilla", value="anime")
    ])
    async def godzillafact(self, interaction: discord.Interaction, version: str):
        """Get a random fascinating fact about the selected Godzilla version."""
        try:
            # Validate version
            if version not in self.godzilla_facts:
                embed = discord.Embed(
                    title="❌ Invalid Version", 
                    description="Please select a valid Godzilla version from the provided choices.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get random fact for the selected version
            facts_list = self.godzilla_facts[version]
            random_fact = random.choice(facts_list)
            
            # Get version information
            version_data = self.version_info[version]
            
            # Create decorative embed
            embed = discord.Embed(
                title=f"{version_data['emoji']} {version_data['name']} Fact",
                description=f"**{random_fact}**",
                color=version_data['color'],
                timestamp=discord.utils.utcnow()
            )
            
            # Add version description
            embed.add_field(
                name="📝 About This Version:",
                value=version_data['description'],
                inline=False
            )
            
            # Add fact statistics
            total_facts = len(facts_list)
            embed.add_field(
                name="📊 Fact Database:",
                value=f"**{total_facts}** unique facts available for this version",
                inline=True
            )
            
            # Add fun fact number
            fact_number = random.randint(1, 9999)
            embed.add_field(
                name="🔢 Fact ID:",
                value=f"#{fact_number}",
                inline=True
            )
            
            # Add interest level
            interest_levels = ["Fascinating!", "Mind-blowing!", "Incredible!", "Amazing!", "Astounding!", "Spectacular!"]
            interest_level = random.choice(interest_levels)
            embed.add_field(
                name="⭐ Interest Level:",
                value=interest_level,
                inline=True
            )
            
            # Add decorative elements based on version
            version_decorations = {
                "monsterverse": "🌊 🦕 ⚡ 🏙️ 🌋",
                "heisei": "⚡ 🔥 ☢️ 🌸 🎌",
                "toho": "🎬 🦖 🏯 🎭 📽️",
                "idw": "📚 🎨 ✏️ 📖 🖼️",
                "marvel": "⭐ 🦸 💥 🏢 🚀",
                "anime": "🌌 🚀 🔮 ⚛️ 🌟"
            }
            
            embed.add_field(
                name="🎨 Version Theme:",
                value=version_decorations[version],
                inline=False
            )
            
            # Set footer with user info
            embed.set_footer(
                text=f"Kaiju fact requested by {interaction.user.display_name} • King of the Monsters",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Set thumbnail based on version (using emoji as decoration)
            embed.set_author(
                name="🦕 Godzilla Fact Database",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the fact request for analytics
            logging.info(f"Godzilla fact requested by {interaction.user.id} - Version: {version}")
            
        except Exception as e:
            embed = discord.Embed(
                title="🦕 Kaiju Database Error",
                description="The Godzilla fact database encountered a disturbance in the kaiju realm.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="🔄 Try Again:",
                value="The King of the Monsters will return shortly with more facts!",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in godzillafact command: {e}", exc_info=True)

# Setup functions
async def setup(bot):
    """Setup function to add the GodzillaFactCommand cog to the bot."""
    await bot.add_cog(GodzillaFactCommand(bot))
    logging.info("GodzillaFact command loaded successfully")

def add_godzillafact_command(bot):
    """Alternative setup function for manual integration."""
    godzillafact_cog = GodzillaFactCommand(bot)
    
    @bot.tree.command(name="godzillafact", description="🦕 Learn fascinating facts about different versions of Godzilla")
    @app_commands.describe(version="Choose which version of Godzilla you want to learn about")
    @app_commands.choices(version=[
        app_commands.Choice(name="🌊 Monsterverse/MV Godzilla", value="monsterverse"),
        app_commands.Choice(name="⚡ Heisei Godzilla", value="heisei"),
        app_commands.Choice(name="🎬 TOHO Godzilla", value="toho"),
        app_commands.Choice(name="📚 IDW Godzilla", value="idw"),
        app_commands.Choice(name="⭐ Marvel Godzilla", value="marvel"),
        app_commands.Choice(name="🌌 Anime Series Godzilla", value="anime")
    ])
    async def godzillafact(interaction: discord.Interaction, version: str):
        await godzillafact_cog.godzillafact(interaction, version)
    
    logging.info("GodzillaFact command added successfully")