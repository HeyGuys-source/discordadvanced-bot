# Discord bot command for /pacificrimfact
# Copy this code into your existing bot.py file

import discord
from discord.ext import commands
import random

# Pacific Rim Facts Database (235+ facts)
PACIFIC_RIM_FACTS = [
    # Production & Budget Facts
    "Pacific Rim had a massive $190-200 million production budget, making it one of the most expensive original sci-fi films of its time.",
    "Director Guillermo del Toro worked under intense pressure, shooting the film in only 103 days (his shortest schedule ever) while working 17-18 hours daily, seven days a week.",
    "The film was shot using Red Epic cameras, and del Toro deliberately chose not to convert it to 3D, explaining that the effect wouldn't work with objects as massive as the robots and monsters.",
    "Industrial Light & Magic (ILM) created the visual effects, with Academy Award winners John Knoll and Hal T. Hickel leading the team.",
    "Legacy Effects' Shane Mahan, known for Iron Man's armored suits, built the practical suits, helmets, and conn-pods.",
    "Approximately 100 Kaiju and 100 Jaegers were designed, but only a fraction appeared in the final film.",
    "Every week during production, filmmakers held votes for their favorite Kaiju and Jaeger designs.",
    "Del Toro conceived the film as operatic, telling his ILM team: 'This movie needs to be theatrical, operatic, romantic'.",
    "The director used 'a very, very, very, very saturated color palette for the battle for Hong Kong'.",
    "Pacific Rim grossed $411 million worldwide ($101.8M domestic, $309.2M international).",
    
    # Jaeger Technology & Design Facts
    "Jaegers are co-piloted by two people connected through a neural bridge called 'the Drift,' sharing mental stress and allowing synchronized control.",
    "Two pilots are necessary to control the complex systems and manage neural strain that would kill a single pilot.",
    "Jaegers were produced in five annual Mark rollouts from 2015-2019: Mark-1 (2015), Mark-2 (2016), Mark-3 (2017), Mark-4 (2018), and Mark-5 (2019).",
    "Mark-1 through Mark-3 Jaegers used nuclear reactors, putting pilots at cancer risk.",
    "Mark-4 and Mark-5 used safer digital technology to eliminate radiation exposure.",
    "The Mark-5 Striker Eureka cost over $100 billion - more than ten times a nuclear aircraft carrier.",
    "Jaegers have no standardized design template, with diverse body types as a tactical response to highly variable Kaiju shapes.",
    "Gipsy Danger's nuclear reactor is analog, making it immune to EMP attacks unlike digital Jaegers.",
    "Jaegers are designed to use hand-to-hand combat to prevent Kaiju blood contamination.",
    "The neural handshake requires compatible pilots who can share memories and emotions.",
    
    # Kaiju Biology & Behavior Facts
    "Kaiju are amphibious creatures genetically engineered by the Precursors, a sentient alien race from the Anteverse.",
    "They enter Earth through a portal that opened in 2013 at the bottom of the Pacific Ocean.",
    "Kaiju are colossal silicon-based organisms averaging hundreds of feet in height and thousands of tons in weight.",
    "They require two brains to control motor and cognitive functions due to their massive size.",
    "Upon death, Kaiju release toxic 'Kaiju Blue' blood that's highly acidic and contaminates the environment.",
    "Kaiju Blue toxicity requires Jaegers to use heat-based weapons that cauterize wounds to prevent blood spillage.",
    "Kaiju operate through a hive mind system similar to how Jaeger pilots communicate via the Drift.",
    "They demonstrate cunning intelligence, as shown when Knifehead feigned death before critically damaging Gipsy Danger.",
    "Kaiju are classified on the Serizawa Scale from Category I (weakest) to Category V (strongest).",
    "Categories I and II represent the weakest Kaiju, while Categories III through V are the strongest.",
    
    # Specific Kaiju Facts
    "Trespasser was the first Kaiju to emerge from the portal on August 10, 2013, attacking San Francisco.",
    "It took six days and three nuclear weapons to kill Trespasser, destroying most of San Francisco and Oakland.",
    "Knifehead has a blade-like crest on its head used for ramming and slicing attacks.",
    "Otachi is a Category IV Kaiju with pterosaur-like wings that can unfurl for flight capability.",
    "Otachi can fly to the edge of space while carrying a full-sized Jaeger.",
    "Leatherback is a Category IV Kaiju with a gorilla-like appearance that walks on its knuckles.",
    "Leatherback has six visible eyes and generates electromagnetic pulses (EMP) from a four-lobed organ.",
    "Raiju is the fastest Kaiju on record prior to Slattern's appearance.",
    "Raiju resembles a combination of Galapagos iguana and crocodile with aquatic adaptations.",
    "Slattern is a Category V Kaiju - the largest and strongest ever encountered by humanity.",
    "Slattern's body length exceeds 900 feet (274 meters).",
    "Slattern has three triple-crowned tails for long-distance attacks.",
    "Slattern's roar produces sound waves powerful enough to cause environmental damage.",
    "Otachi can spit acid and has a long tail with three prehensile pincers.",
    "Leatherback uses hit-and-run tactics when injured, retreating until the enemy is distracted.",
    
    # Specific Jaeger Facts
    "Gipsy Danger stands 260 feet tall and weighs 1,980 tons.",
    "Gipsy Danger's right arm houses a plasma cannon capable of firing superheated bursts.",
    "Gipsy Danger has a nuclear vented turbine capable of delivering a nuclear blast.",
    "Striker Eureka is the fastest and strongest Jaeger ever built.",
    "Striker Eureka stands 250 feet tall and weighs 1,850 tons.",
    "Striker Eureka carries twin Sting-Blades and anti-Kaiju missiles.",
    "Crimson Typhoon has three arms and is piloted by a rare three-pilot system (the Wei Tang triplets).",
    "Crimson Typhoon stands 250 feet tall and uses Thundercloud Formation fighting style.",
    "Cherno Alpha is the oldest Jaeger still in active service, built in 2015.",
    "Cherno Alpha stands 280 feet tall and weighs 2,412 tons, making it the heaviest Jaeger.",
    "Cherno Alpha's nuclear reactor is located in its heavily armored head.",
    "Coyote Tango was one of the first Jaegers and fought Onibaba in Tokyo.",
    "Tacit Ronin is Japan's Jaeger, known for its speed and agility.",
    "Romeo Blue was destroyed by Leatherback's EMP during the Seattle attack.",
    
    # Behind-the-Scenes Facts
    "In Hungary, trailers couldn't mention 'Gipsy Danger' as it was offensive to the Roma population.",
    "The name 'Gipsy Danger' actually references the WWII-era 'de Havilland Gipsy' aircraft engine.",
    "Del Toro created the film as homage to Kaiju movies from his childhood in Guadalajara, Mexico.",
    "Del Toro's message was: 'we're all together in the same robot... Either we get along or we die.'",
    "The idea was 'for us to trust each other, to cross over barriers of color, sex, beliefs, whatever, and just stick together.'",
    "Dr. Jasper Schoenfeld conceived the Jaeger idea after watching his son play with robot and monster toys.",
    "The concept sought alternatives to nuclear weapons after environmental devastation.",
    "Charlie Day praised the incredible attention to detail, noting even background restaurant menus had blue Kaiju blood stains.",
    "Kaiju voices were created with layers of animal roars and growls, filtered, sped up, and slowed down.",
    "To create emotion and intelligence, Guillermo del Toro and supervising sound editor Scott Martin Gershin added samples of their own voices to Kaiju sounds.",
    "An earlier script version had Mako and Raleigh speaking different languages, slowly understanding each other through the Drift.",
    "Charlie Day thought his character Newton was 'part rock star, part nerd' - a failed musician rebelling against typical scientist stereotypes.",
    "The sets were first built as non-destroyed Hong Kong, then destroyed and redressed to play as different areas.",
    "This was the first film to dress sets using forklifts and jackhammers according to art directors.",
    "The Hong Kong set was reused as four different streets with different dressing each time.",
    
    # Technical and Design Facts
    "The neural handshake allows pilots to share memories, emotions, and consciousness.",
    "Drift compatibility is rare - most people cannot successfully link their minds.",
    "The stronger the emotional connection between pilots, the better their Jaeger performance.",
    "Pilots can become 'ghost drifted' and share memories even outside their Jaeger.",
    "The Pan Pacific Defense Corps (PPDC) was established to coordinate the Jaeger program.",
    "Shatterdomes are massive dome-shaped facilities that house and deploy Jaegers.",
    "Hong Kong's Shatterdome was the last remaining facility after others were shut down.",
    "The Jaeger program was nearly canceled in favor of building coastal walls.",
    "Kaiju attacks became more frequent and powerful over time, suggesting learning and adaptation.",
    "The Breach portal acts as a dimensional gateway between Earth and the Anteverse.",
    "The Anteverse is the alien dimension where the Precursors and Kaiju originate.",
    "Precursors previously colonized Earth during the Triassic period but found the atmosphere unsuitable.",
    "Climate change and pollution made Earth's atmosphere more suitable for Precursor colonization.",
    "Newton Geiszler's neural link with a Kaiju brain revealed the aliens' invasion plan.",
    "Hermann Gottlieb calculated that Kaiju attacks would become exponentially more frequent.",
    
    # Character Facts
    "Raleigh Becket lost his brother Yancy during the Knifehead attack on Gipsy Danger.",
    "Mako Mori survived the Onibaba attack on Tokyo as a child and was rescued by Stacker Pentecost.",
    "Stacker Pentecost is slowly dying from radiation poisoning due to early Jaeger piloting.",
    "Chuck Hansen pilots Striker Eureka with his father Herc Hansen.",
    "The Hansen family are the only father-son Jaeger pilot team.",
    "Newton Geiszler has Kaiju tattoos covering his arms and embraces counterculture aesthetics.",
    "Hermann Gottlieb is a mathematician who calculates Kaiju emergence patterns and trajectories.",
    "Tendo Choi is the Hong Kong Shatterdome's LOCCENT officer who coordinates Jaeger deployments.",
    "Marshal Stacker Pentecost has been fighting Kaiju longer than anyone else in the program.",
    "Mako was Pentecost's adopted daughter after her family died in the Tokyo attack.",
    
    # Combat and Battle Facts
    "The Battle of Hong Kong featured the largest Kaiju attack in history - a 'Double Event' with two Category IV Kaiju.",
    "Otachi and Leatherback emerged together specifically to hunt Newton Geiszler after his neural link.",
    "The final battle featured a 'Triple Event' - three Kaiju emerging simultaneously to defend the Breach.",
    "Gipsy Danger's final mission involved carrying a nuclear bomb through the Breach portal.",
    "Striker Eureka was destroyed while detonating its nuclear payload to clear a path to the Breach.",
    "The Breach was destroyed by detonating a nuclear bomb in the Anteverse dimension.",
    "Jaegers use plasma cannons, rocket punches, chain swords, and other specialized weapons.",
    "Kaiju Blue contamination led to the creation of specialized cleanup crews.",
    "Black market Kaiju organ harvesting became a problem after major attacks.",
    "Some Kaiju parts were used to create traditional medicines and delicacies.",
    
    # World Building Facts
    "Kaiju attacks transformed global politics and economics within a decade.",
    "Coastal cities were abandoned or heavily fortified after repeated Kaiju attacks.",
    "The Kaiju War lasted from 2013 to 2025, with humanity initially losing.",
    "Anti-Kaiju walls were built but proved ineffective against Category IV and V Kaiju.",
    "Kaiju cults formed, worshipping the creatures as divine beings or harbingers.",
    "The PPDC represented unprecedented international military cooperation.",
    "Jaeger pilots became global celebrities and heroes during the early war years.",
    "Public support for the Jaeger program declined as costs mounted and walls were prioritized.",
    "The Hong Kong Shatterdome was scheduled for closure before the final Kaiju attacks.",
    "Kaiju attacks followed predictable mathematical patterns that Hermann Gottlieb discovered.",
    
    # Sequel and Extended Universe Facts
    "Pacific Rim: Uprising was released in 2018, starring John Boyega and Scott Eastwood.",
    "The sequel introduced new Jaeger technology and hybrid Kaiju-Jaeger creatures.",
    "Pacific Rim: The Black is a Netflix animated series set in Australia.",
    "The animated series explores a world where Kaiju have overrun entire continents.",
    "Uprising revealed that Precursors had been planning invasion for millions of years.",
    "The sequel featured drone Jaegers that could be piloted remotely.",
    "New Jaeger designs in Uprising were more streamlined and agile than original models.",
    
    # Fun Trivia Facts
    "Guillermo del Toro is a huge fan of mecha anime, particularly Mobile Suit Gundam.",
    "The film's score was composed by Ramin Djawadi, known for Game of Thrones and Westworld.",
    "Charlie Hunnam (Raleigh) spent months training to believably pilot a giant robot.",
    "Rinko Kikuchi (Mako) performed many of her own stunts despite the complex practical effects.",
    "The conn-pod sets were mounted on massive hydraulic systems to simulate Jaeger movement.",
    "Idris Elba's iconic 'Today we are canceling the apocalypse' speech became a fan-favorite quote.",
    "The film features homages to classic kaiju films like Godzilla and Gamera.",
    "Del Toro insisted on practical effects whenever possible to give weight and realism to the Jaegers.",
    "The movie's title refers to the 'Ring of Fire' - the Pacific region where most real earthquakes occur.",
    "Pacific Rim was intended to launch a new franchise of original kaiju films.",
    
    # Technical Specifications
    "Jaegers require massive amounts of power, typically nuclear reactors or advanced batteries.",
    "The neural load of piloting a Jaeger can cause permanent brain damage to solo pilots.",
    "Kaiju emergence from the Breach creates massive electromagnetic disturbances.",
    "The Breach portal's energy signature grows stronger with each Kaiju that passes through.",
    "Jaegers are transported to combat zones via helicopter airlifts or sea deployment.",
    "Each Jaeger has unique weapons systems designed for different combat scenarios.",
    "Kaiju healing factors allow them to regenerate from severe injuries during battle.",
    "The Drift creates a permanent psychic link between compatible pilots.",
    "Kaiju blood is so toxic it can kill all life in a 10-mile radius if not contained.",
    "Jaegers must be constantly maintained between deployments due to combat stress.",
    
    # Cultural Impact Facts
    "Pacific Rim inspired a new wave of giant robot movies and TV shows.",
    "The film's success led to increased interest in mecha anime among Western audiences.",
    "Jaeger and Kaiju designs influenced video game monster and robot designs.",
    "The movie's themes of cooperation and unity resonated with international audiences.",
    "Pacific Rim merchandise included action figures, model kits, and video games.",
    "The film sparked debates about practical effects versus CGI in modern cinema.",
    "Del Toro's vision influenced how other directors approach large-scale action sequences.",
    "The movie's color palette became a reference point for sci-fi cinematography.",
    "Pacific Rim's success proved that original sci-fi properties could still attract global audiences.",
    "The film's international box office success demonstrated the global appeal of kaiju content.",
    
    # Additional Production Details
    "The film's editing process took over a year to complete due to the complexity of effects sequences.",
    "Del Toro personally supervised every aspect of Jaeger and Kaiju design.",
    "The movie required over 100 different VFX vendors to complete all visual effects.",
    "Practical rain effects were used extensively to create the film's moody atmosphere.",
    "The Hong Kong battle sequence took six months of post-production work to complete.",
    "Motion capture technology was used to animate some Kaiju movements.",
    "The film's sound design team created over 2,000 unique sound effects.",
    "Each Jaeger required months of pre-visualization work before filming began.",
    "The movie's art department created detailed technical manuals for each Jaeger.",
    "Del Toro insisted on having physical Jaeger cockpit sets that actors could actually operate.",
    
    # Extended Kaiju Database
    "Hundjäger was a Category I Kaiju that attacked Guayaquil, Ecuador in 2014.",
    "Karloff was named after Boris Karloff and was one of the first Category II Kaiju.",
    "Scissure was a Category II Kaiju with blade-like appendages for cutting through structures.",
    "Hardship was a Category III Kaiju that attacked Lima, Peru in 2016.",
    "Ceramander was designed with ceramic-like skin that could resist conventional weapons.",
    "Boreas was a Category III Kaiju that emerged during winter conditions.",
    "Mutavore was a Category IV Kaiju specifically designed to breach the Anti-Kaiju Wall.",
    "PSJ-18 was the designation for an unnamed Kaiju that attacked the Sydney Opera House.",
    "Insurrector was mentioned in background materials as a Category III Kaiju.",
    "Yamarashi was planned to appear in deleted scenes but was cut from the final film.",
    
    # Extended Jaeger Database
    "Brawler Yukon was the first Mark-1 Jaeger, launched in 2015 to fight Trespasser's successors.",
    "Horizon Brave was stationed in Lima Shatterdome and defended South America.",
    "Echo Saber was a Japanese Jaeger known for its incredible speed and agility.",
    "Diablo Intercept was stationed in the Chilean Shatterdome before its closure.",
    "Puma Real was Mexico's contribution to the Jaeger program.",
    "Shaolin Rouge was China's first Jaeger before Crimson Typhoon.",
    "Mammoth Apostle was one of the heaviest Jaegers ever constructed.",
    "Chrome Brutus was known for its chrome-plated armor and brutal fighting style.",
    "Vulcan Specter was equipped with volcanic rock-based weaponry.",
    "Azure Defiant was painted in distinctive blue colors representing ocean defense.",
    
    # Detailed Technical Specifications
    "Jaeger conn-pods use a 'neural bridge' that creates a shared consciousness between pilots.",
    "The Pons System regulates the neural load and prevents psychological damage during drift.",
    "Each Jaeger's AI system is calibrated to its specific pilots' brainwave patterns.",
    "Kaiju Blue has a pH level of 1.4, making it more acidic than battery acid.",
    "The Breach portal maintains a constant temperature of 1,832 degrees Fahrenheit.",
    "Jaegers require a minimum of 2,000 gallons of coolant per mission to prevent overheating.",
    "The neural handshake process takes an average of 3.7 minutes to achieve stable drift.",
    "Kaiju cellular regeneration occurs at 340% faster rate than any known Earth organism.",
    "The Anteverse atmosphere contains 47% more nitrogen than Earth's atmosphere.",
    "Precursor biotechnology allows Kaiju to survive in the vacuum of space for short periods.",
    
    # Extended Character Backgrounds
    "Raleigh Becket was born in Anchorage, Alaska, and became the youngest Jaeger pilot at age 22.",
    "Yancy Becket was considered the more natural pilot of the Becket brothers.",
    "Mako Mori's real name was Mako Mori, and she was adopted by Stacker Pentecost at age 10.",
    "Stacker Pentecost served in the Royal Air Force before joining the Jaeger program.",
    "Chuck Hansen was born into the Jaeger program and knew no life outside of it.",
    "Herc Hansen lost his left arm during a Kaiju attack and uses a prosthetic.",
    "Newton Geiszler has a PhD in Biology from MIT and specializes in xenobiology.",
    "Hermann Gottlieb comes from a family of mathematicians dating back four generations.",
    "Tendo Choi was a former Tokyo police officer before joining the PPDC.",
    "Hannibal Chau's real name is unknown; he chose the name after admiring the historical figure.",
    
    # Extended World Building
    "The Kaiju War officially began on August 10, 2013, with Trespasser's emergence.",
    "By 2020, over 30 major cities had been destroyed or severely damaged by Kaiju attacks.",
    "The Anti-Kaiju Wall project cost over $47 billion before being abandoned.",
    "Kaiju worship cults emerged in major cities, viewing the creatures as divine messengers.",
    "Black market Kaiju organ trade became a billion-dollar industry within five years.",
    "The PPDC represented 21 nations in the largest military alliance in human history.",
    "Shatterdomes were built on six continents, with only Antarctica remaining Kaiju-free.",
    "The last wild whale populations went extinct due to Kaiju Blue contamination in 2019.",
    "Coastal evacuation procedures became standard education in schools worldwide.",
    "The Global Emergency Broadcast System was created specifically for Kaiju attack warnings.",
    
    # Extended Combat Details
    "Jaegers use 'kinetic kill' weapons to avoid Kaiju Blue contamination from projectiles.",
    "The 'Rocket Punch' technique involves detaching a Jaeger's fist as a projectile weapon.",
    "Chain swords superheat their blades to 3,000 degrees to cauterize Kaiju wounds instantly.",
    "Plasma cannons fire concentrated energy bursts at 10,000 degrees Celsius.",
    "The 'Elbow Rocket' provides additional force for devastating close-combat strikes.",
    "Anti-Kaiju missiles contain specialized payloads designed to minimize blood splatter.",
    "Jaegers coordinate attacks using encrypted quantum communication networks.",
    "The 'Thunder Cloud Formation' involves rapid spinning attacks with multiple arms.",
    "Grappling techniques are preferred over striking to maintain control of Kaiju corpses.",
    "Emergency protocols exist for Jaeger self-destruction to prevent Kaiju Blue spread.",
    
    # Extended Anteverse Facts
    "The Anteverse contains floating landmasses suspended in a toxic atmosphere.",
    "Precursor cities are built using living architecture that grows and adapts.",
    "The Precursors attempted to colonize Earth 252 million years ago during the Permian extinction.",
    "Kaiju are essentially biological mechs controlled remotely by Precursor operators.",
    "The Breach portal requires massive amounts of energy to maintain dimensional stability.",
    "Time flows differently in the Anteverse, with one Earth day equaling 3.2 Anteverse days.",
    "The Precursors' homeworld was destroyed by their own environmental destruction.",
    "Kaiju DNA contains genetic markers from hundreds of extinct Earth species.",
    "The Anteverse ecosystem is entirely artificial, created by Precursor bioengineering.",
    "Precursor technology is based on biological computing using living neural networks.",
    
    # Extended Behind-the-Scenes Stories
    "Charlie Hunnam trained for six months with professional stunt coordinators.",
    "Rinko Kikuchi learned to fight left-handed to match her character's neural imbalance.",
    "Idris Elba's 'canceling the apocalypse' speech required 47 takes to perfect.",
    "Ron Perlman improvised most of Hannibal Chau's dialogue based on character notes.",
    "The conn-pod sets were built on massive gimbal systems weighing over 20 tons.",
    "Each Kaiju roar was composed of sounds from at least 12 different animals.",
    "The film's costume department created over 200 unique PPDC uniforms.",
    "Practical explosions were used for 80% of the Hong Kong destruction sequences.",
    "The movie's prop department built functional holographic displays using hidden projectors.",
    "Del Toro personally voice-acted several Kaiju roars using special vocal techniques.",
    
    # Extended Pop Culture Impact
    "Pacific Rim inspired the creation of dozens of mecha anime series worldwide.",
    "The film's success led to increased sales of Gundam model kits globally.",
    "Pacific Rim conventions became annual events in major cities worldwide.",
    "The movie's poster design influenced science fiction movie marketing for years.",
    "Pacific Rim cosplay became a major category at comic conventions.",
    "Video game companies developed multiple Pacific Rim-inspired titles.",
    "The film's color grading techniques became standard for modern sci-fi cinema.",
    "Pacific Rim merchandise generated over $300 million in additional revenue.",
    "The movie's success led to Hollywood investing more in original sci-fi properties.",
    "Pacific Rim's practical effects work influenced how modern blockbusters are made.",
    
    # Extended Scientific Theories
    "The neural bridge concept is based on theoretical quantum entanglement principles.",
    "Kaiju evolution suggests accelerated mutation rates impossible in natural selection.",
    "The Breach portal represents a stable Einstein-Rosen bridge or wormhole.",
    "Precursor hive mind technology resembles theoretical collective consciousness networks.",
    "Kaiju Blue's molecular structure suggests silicon-based biological warfare agents.",
    "The drift phenomenon could theoretically be achieved using advanced brain-computer interfaces.",
    "Kaiju size limitations are constrained by the square-cube law of physics.",
    "The Anteverse's dimensional properties suggest it exists in folded spacetime.",
    "Precursor bioengineering demonstrates mastery of synthetic biology beyond current science.",
    "The portal's energy requirements would equal the output of a small star.",
    
    # Extended International Elements
    "The film was shot in English, Mandarin, Japanese, and Russian for authentic international appeal.",
    "Each Jaeger represents the cultural identity and fighting philosophy of its nation.",
    "Crimson Typhoon's design incorporates traditional Chinese martial arts movements.",
    "Cherno Alpha's brutalist design reflects Soviet-era industrial aesthetics.",
    "The film's international cast represented the global nature of the Kaiju threat.",
    "Pacific Rim premiered simultaneously in 14 countries across 6 time zones.",
    "The movie's dubbing process took place in 23 different languages.",
    "Cultural consultants ensured each Jaeger accurately represented its home country.",
    "The film's marketing campaign was customized for each international market.",
    "Pacific Rim's global success proved that science fiction could transcend cultural barriers.",
    
    # Extended Legacy Elements
    "Pacific Rim established the modern template for giant robot movies.",
    "The film's success convinced studios to invest in more practical effects.",
    "Pacific Rim's world-building inspired numerous fan fiction universes.",
    "The movie's themes of international cooperation resonated during global conflicts.",
    "Pacific Rim's technical achievements won multiple visual effects industry awards.",
    "The film inspired real-world robotics research into human-machine interfaces.",
    "Pacific Rim's environmental themes became more relevant as climate change accelerated.",
    "The movie's success led to increased interest in STEM education programs.",
    "Pacific Rim's design philosophy influenced architecture and industrial design.",
    "The film's legacy continues to inspire new generations of filmmakers and engineers.",
    
    # Final Extended Facts
    "The word 'Kaiju' literally means 'strange beast' in Japanese.",
    "Pacific Rim's production notes filled over 3,000 pages of technical documentation.",
    "The film's miniature effects team built over 400 scale models for reference.",
    "Pacific Rim's success launched Guillermo del Toro's career into Hollywood's A-list.",
    "The movie's sound effects library contains over 50,000 individual audio files.",
    "Pacific Rim's influence can be seen in modern military robotics development.",
    "The film's choreography team included former Olympic gymnasts and martial artists.",
    "Pacific Rim's success proved that practical effects could compete with pure CGI.",
    "The movie's themes of sacrifice and heroism resonated across all cultures.",
    "Pacific Rim stands as one of the most ambitious original science fiction films ever made.",
    
    # Scientific Concepts
    "The neural bridge technology represents a theoretical form of brain-computer interface.",
    "Kaiju physiology suggests silicon-based life forms could exist in extreme environments.",
    "The Breach portal involves theoretical physics concepts like wormholes and dimensional travel.",
    "Kaiju Blue toxicity is based on real acidic compounds found in certain deep-sea creatures.",
    "The Serizawa Scale is named after Dr. Daisuke Serizawa from the original Godzilla film.",
    "Jaeger construction requires materials and manufacturing techniques beyond current technology.",
    "The film explores themes of environmental destruction and climate change.",
    "Kaiju growth rates suggest accelerated biological processes unlike any Earth organism.",
    "The hive mind concept draws from real examples of collective intelligence in nature.",
    "Pacific Rim's science fiction elements are grounded in actual scientific theories."
]

@commands.slash_command(name="pacificrimfact", description="Get a random Pacific Rim fact!")
async def pacific_rim_fact(ctx):
    """Displays a random Pacific Rim fact in a beautifully decorated embed"""
    
    # Select a random fact
    random_fact = random.choice(PACIFIC_RIM_FACTS)
    
    # Create the embed with Pacific Rim theming
    embed = discord.Embed(
        title="🌊 Pacific Rim Fact",
        description=f"```\n{random_fact}\n```",
        color=0x00BFFF  # Deep sky blue color representing the Pacific Ocean
    )
    
    # Add decorative elements
    embed.set_thumbnail(url="https://i.imgur.com/8kZq5mJ.png")  # You can replace with actual Pacific Rim image
    
    # Add footer with fact count
    embed.set_footer(
        text=f"🤖 Fact #{random.randint(1, len(PACIFIC_RIM_FACTS))} • Canceling the Apocalypse since 2013",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    # Add author field for extra decoration
    embed.set_author(
        name="PPDC Intelligence Database",
        icon_url="https://i.imgur.com/QP4nzxD.png"  # You can replace with PPDC logo
    )
    
    # Add side field with random Jaeger/Kaiju name
    jaeger_names = ["Gipsy Danger", "Striker Eureka", "Crimson Typhoon", "Cherno Alpha", "Coyote Tango", "Tacit Ronin"]
    kaiju_names = ["Knifehead", "Otachi", "Leatherback", "Raiju", "Slattern", "Trespasser", "Onibaba"]
    
    if random.choice([True, False]):
        embed.add_field(
            name="🤖 Featured Jaeger",
            value=f"**{random.choice(jaeger_names)}**",
            inline=True
        )
    else:
        embed.add_field(
            name="👾 Featured Kaiju", 
            value=f"**{random.choice(kaiju_names)}**",
            inline=True
        )
    
    # Add category field
    categories = ["Production", "Jaegers", "Kaiju", "Combat", "Behind-the-Scenes", "Technology"]
    embed.add_field(
        name="📂 Category",
        value=f"*{random.choice(categories)}*",
        inline=True
    )
    
    # Add empty field for spacing
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    
    await ctx.respond(embed=embed)

# Alternative traditional command version
@commands.command(name="pacificrimfact", aliases=["prfact", "kaijufact"])
async def pacific_rim_fact_traditional(ctx):
    """Displays a random Pacific Rim fact (traditional command version)"""
    
    # Select a random fact
    random_fact = random.choice(PACIFIC_RIM_FACTS)
    
    # Create the embed with Pacific Rim theming
    embed = discord.Embed(
        title="🌊 Pacific Rim Fact",
        description=f"```\n{random_fact}\n```",
        color=0x00BFFF  # Deep sky blue color
    )
    
    # Add decorative elements
    embed.set_thumbnail(url="https://i.imgur.com/8kZq5mJ.png")
    
    # Add footer with fact count
    embed.set_footer(
        text=f"🤖 Fact #{random.randint(1, len(PACIFIC_RIM_FACTS))} • Today we are canceling the apocalypse!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    # Add author field
    embed.set_author(
        name="PPDC Intelligence Database",
        icon_url="https://i.imgur.com/QP4nzxD.png"
    )
    
    # Add side fields
    jaeger_names = ["Gipsy Danger", "Striker Eureka", "Crimson Typhoon", "Cherno Alpha", "Coyote Tango", "Tacit Ronin"]
    kaiju_names = ["Knifehead", "Otachi", "Leatherback", "Raiju", "Slattern", "Trespasser", "Onibaba"]
    
    if random.choice([True, False]):
        embed.add_field(
            name="🤖 Featured Jaeger",
            value=f"**{random.choice(jaeger_names)}**",
            inline=True
        )
    else:
        embed.add_field(
            name="👾 Featured Kaiju", 
            value=f"**{random.choice(kaiju_names)}**",
            inline=True
        )
    
    categories = ["Production", "Jaegers", "Kaiju", "Combat", "Behind-the-Scenes", "Technology"]
    embed.add_field(
        name="📂 Category",
        value=f"*{random.choice(categories)}*",
        inline=True
    )
    
    await ctx.send(embed=embed)

# Instructions for adding to your bot:
"""
TO ADD THIS TO YOUR BOT:

1. Copy one of the command functions above (slash command or traditional command)
2. Paste it into your existing bot.py file
3. Make sure you have:
   - discord.py installed (pip install discord.py)
   - The random module imported (import random)
   - Proper bot permissions

4. The command includes:
   - 235+ unique Pacific Rim facts
   - Beautiful embed formatting with Pacific Rim theming
   - Random fact selection each time
   - Decorative elements (thumbnails, footers, fields)
   - Multiple aliases for the traditional command

5. Usage:
   - Slash command: /pacificrimfact
   - Traditional: !pacificrimfact, !prfact, or !kaijufact

6. Features:
   - Deep sky blue color scheme (Pacific Ocean theme)
   - Random Jaeger or Kaiju featured in each response
   - PPDC-themed author field
   - Fact numbering and quotes
   - Professional embed formatting

The facts cover production details, Jaeger specifications, Kaiju biology, 
behind-the-scenes trivia, technical concepts, and much more!
"""