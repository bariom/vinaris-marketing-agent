from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.brand_profile import BrandProfile, VINARIS_BRAND, brand_context
from app.image_prompt_generator import generate_image_prompt
from app.platform_profiles import get_platform_profile
from app.social_calendar import suggest_scheduled_date

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


PLATFORMS = ("Facebook", "Instagram", "LinkedIn")
CATEGORIES = (
    "gestione cantina",
    "errori comuni dei collezionisti",
    "finestre di beva",
    "valore della cantina",
    "wishlist",
    "consegne",
    "beta tester",
    "funzioni Vinaris",
)
SERIOUSNESS_LEVELS = ("alto", "equilibrato", "leggero")
WARMTH_LEVELS = ("sobrio", "caldo", "coinvolgente")
PROMOTIONAL_LEVELS = ("discreto", "equilibrato", "deciso")
TARGET_AGE_RANGES = ("25-34", "35-44", "45-54", "55-64", "65+", "misto")
TARGET_GENDERS = ("uomo", "donna", "misto")
TARGET_EXPERTISE_LEVELS = ("neofita", "appassionato", "collezionista esperto", "misto")
TARGET_SPENDING_POWERS = ("medio", "medio-alto", "alto", "luxury")

MOCK_ANGLES: dict[str, list[dict[str, str]]] = {
    "gestione cantina": [
        {
            "title": "Una cantina privata merita ordine, non memoria",
            "short": "Sapere cosa hai in cantina non dovrebbe dipendere da fogli sparsi o note improvvisate.",
            "medium": (
                "Molti appassionati costruiscono una collezione di valore, ma la gestiscono ancora in modo frammentato. "
                "Vinaris aiuta a centralizzare bottiglie, posizioni, quantita e note essenziali in un unico spazio chiaro."
            ),
            "cta": "Scopri come organizzare la tua cantina privata con piu precisione.",
            "hashtags": "#Vinaris #CantinaPrivata #WineCollection #GestioneCantina",
            "angle": "collector reviewing an elegant private cellar inventory on smartphone",
        },
        {
            "title": "Ogni bottiglia ha un posto, ogni informazione anche",
            "short": "Una cantina ben gestita semplifica scelte, acquisti e aperture.",
            "medium": (
                "La differenza tra accumulare bottiglie e gestire una cantina privata sta nella qualita delle informazioni. "
                "Con Vinaris puoi tenere sotto controllo dove si trova ogni vino e consultarlo in pochi secondi."
            ),
            "cta": "Richiedi l'accesso beta e prova un approccio piu ordinato.",
            "hashtags": "#PrivateCellar #VinarisApp #WineLovers #Cantina",
            "angle": "refined cellar shelves with discrete app interface in foreground",
        },
    ],
    "errori comuni dei collezionisti": [
        {
            "title": "Tre errori silenziosi che indeboliscono una collezione",
            "short": "Il problema spesso non e comprare troppo, ma perdere visibilita su cio che si possiede.",
            "medium": (
                "Duplicare acquisti, dimenticare finestre di beva e non tracciare il valore della cantina sono errori frequenti. "
                "Vinaris nasce per ridurre questi attriti con una gestione piu lucida e continua."
            ),
            "cta": "Vuoi evitare errori ricorrenti? Entra nella beta di Vinaris.",
            "hashtags": "#WineCollector #Vinaris #CollezioneVini #WineTech",
            "angle": "premium visual comparing disorganized notes and clean digital cellar overview",
        },
        {
            "title": "Una collezione ordinata non dipende solo dalla memoria",
            "short": "Quando le bottiglie aumentano, gli errori iniziano spesso da dettagli non tracciati.",
            "medium": (
                "Una cantina privata perde valore operativo quando acquisti, posizioni e tempi di beva restano dispersi. "
                "Mettere ordine presto evita decisioni deboli e doppioni inutili."
            ),
            "cta": "Scopri come Vinaris aiuta a tenere insieme questi passaggi.",
            "hashtags": "#WineCollector #CantinaPrivata #Vinaris #WineManagement",
            "angle": "private cellar records contrasted with a clean, premium digital inventory flow",
        },
    ],
    "finestre di beva": [
        {
            "title": "Aprire troppo presto e un costo invisibile",
            "short": "La finestra di beva e una scelta strategica, non un dettaglio secondario.",
            "medium": (
                "Una bottiglia aperta nel momento sbagliato perde parte del suo potenziale. "
                "Monitorare le finestre di beva significa valorizzare meglio ogni acquisto e ogni occasione."
            ),
            "cta": "Scopri come Vinaris puo aiutarti a decidere quando stappare.",
            "hashtags": "#WineDrinkingWindow #Vinaris #FineWine #CantinaIntelligente",
            "angle": "sommelier style scene with mature bottle and subtle timing cues on app",
        },
        {
            "title": "Sapere quando stappare cambia il valore dell'esperienza",
            "short": "Non tutte le bottiglie sono pronte quando arriva l'occasione.",
            "medium": (
                "Tenere d'occhio le finestre di beva aiuta a non sprecare bottiglie promettenti e a scegliere meglio cosa aprire. "
                "E un vantaggio pratico, non solo teorico."
            ),
            "cta": "Approfondisci come leggere meglio i tempi della tua cantina.",
            "hashtags": "#FineWine #DrinkingWindow #Vinaris #WineCollection",
            "angle": "mature bottle selection in a refined cellar with subtle timing and readiness cues",
        },
    ],
    "valore della cantina": [
        {
            "title": "Conosci davvero il valore della tua cantina?",
            "short": "Una collezione privata non e solo passione: e anche patrimonio.",
            "medium": (
                "Quando la cantina cresce, avere una visione chiara del suo valore diventa utile per acquisti, priorita e consapevolezza. "
                "Vinaris supporta una lettura piu strutturata del patrimonio enologico personale."
            ),
            "cta": "Prova Vinaris e dai piu contesto al valore della tua collezione.",
            "hashtags": "#WineCellarValue #Vinaris #WineCollection #PatrimonioEnologico",
            "angle": "luxury cellar with analytical but elegant digital valuation concept",
        },
        {
            "title": "Una cantina importante merita numeri leggibili",
            "short": "Capire il valore della collezione aiuta a fare scelte piu lucide nel tempo.",
            "medium": (
                "Quando acquisti e bottiglie maturano, una vista chiara del valore complessivo smette di essere un extra. "
                "Diventa uno strumento utile per priorita, confronto e gestione."
            ),
            "cta": "Guarda come Vinaris puo dare piu contesto a questa lettura.",
            "hashtags": "#WineValue #PrivateCellar #Vinaris #FineWine",
            "angle": "premium cellar valuation overview with discreet analytical interface",
        },
    ],
    "wishlist": [
        {
            "title": "Le grandi bottiglie iniziano spesso da una wishlist ben fatta",
            "short": "Desiderare un vino e facile. Ricordarsi perche lo si vuole comprare, meno.",
            "medium": (
                "Una wishlist utile non e una lista casuale, ma uno strumento per confrontare annate, produttori e priorita. "
                "Vinaris aiuta a mantenere questa visione con ordine e continuita."
            ),
            "cta": "Organizza la tua wishlist da collezionista con l'accesso beta.",
            "hashtags": "#WineWishlist #Vinaris #WineCollector #PrivateCellar",
            "angle": "elegant collector building a wine wishlist on mobile near tasting table",
        },
        {
            "title": "Una wishlist seria evita acquisti confusi",
            "short": "Tenere traccia dei desideri giusti aiuta a comprare con piu criterio.",
            "medium": (
                "Tra produttori, annate e opportunita, una wishlist ben tenuta riduce dispersione e ripensamenti. "
                "Diventa una guida concreta per i prossimi acquisti."
            ),
            "cta": "Esplora un modo piu ordinato di costruire la tua wishlist.",
            "hashtags": "#WishlistVini #Vinaris #WineCollector #CantinaPrivata",
            "angle": "carefully curated wine wishlist workflow in a refined private cellar setting",
        },
    ],
    "consegne": [
        {
            "title": "Anche la consegna fa parte dell'esperienza di cantina",
            "short": "Sapere cosa arriva, quando arriva e dove collocarlo riduce attrito e disordine.",
            "medium": (
                "Ogni nuova consegna merita una registrazione pulita. "
                "Una gestione precisa in ingresso aiuta a mantenere affidabile l'intera fotografia della cantina."
            ),
            "cta": "Scopri come Vinaris semplifica il passaggio dalla consegna alla scaffalatura.",
            "hashtags": "#WineDelivery #Vinaris #CantinaPrivata #WineManagement",
            "angle": "premium home delivery of fine wine entering an organized private cellar",
        },
        {
            "title": "La cantina si complica spesso nel momento dell'arrivo",
            "short": "Se l'ingresso delle bottiglie e confuso, il resto si trascina dietro lo stesso disordine.",
            "medium": (
                "Registrare bene le consegne significa sapere subito cosa e entrato, dove andra e come tenerlo tracciato. "
                "E una disciplina piccola che migliora tutta la gestione."
            ),
            "cta": "Approfondisci come rendere piu lineare questo passaggio.",
            "hashtags": "#WineLogistics #Vinaris #PrivateCellar #Cantina",
            "angle": "refined wine delivery intake process moving into a well-organized private cellar",
        },
    ],
    "beta tester": [
        {
            "title": "La beta Vinaris e pensata per chi prende sul serio la propria cantina",
            "short": "Accesso anticipato, feedback diretto e 2 mesi gratuiti escluso AI Pack.",
            "medium": (
                "Stiamo aprendo la beta di Vinaris a un gruppo selezionato di appassionati e collezionisti privati. "
                "Il piano beta parte da CHF 6/mese o CHF 60/anno, con 2 mesi gratuiti escluso AI Pack per i beta tester."
            ),
            "cta": "Candidati come beta tester e prova Vinaris in anteprima.",
            "hashtags": "#VinarisBeta #BetaTester #WineApp #PrivateCellarIntelligence",
            "angle": "exclusive beta invitation for a premium wine-tech product",
        },
        {
            "title": "La beta Vinaris e per chi vuole un metodo, non solo un'app",
            "short": "Accesso anticipato e spazio per incidere davvero sul prodotto.",
            "medium": (
                "La fase beta e pensata per raccogliere feedback utili da chi vive la cantina con attenzione. "
                "L'obiettivo non e testare rumore, ma abitudini reali di gestione."
            ),
            "cta": "Richiedi l'accesso beta se vuoi provare Vinaris da vicino.",
            "hashtags": "#BetaVinaris #WineApp #PrivateCellar #BetaTester",
            "angle": "premium beta access invitation for a refined wine-tech platform",
        },
    ],
    "funzioni Vinaris": [
        {
            "title": "Vinaris non e una semplice lista bottiglie",
            "short": "E uno spazio pensato per dare contesto operativo alla tua cantina privata.",
            "medium": (
                "Gestione inventario, wishlist, controllo delle finestre di beva e maggiore visibilita sul valore della collezione: "
                "Vinaris mette ordine dove spesso esistono strumenti separati."
            ),
            "cta": "Esplora le funzioni Vinaris e richiedi l'accesso beta.",
            "hashtags": "#VinarisFeatures #WineTech #CantinaPrivata #PrivateCellar",
            "angle": "clean premium product showcase of wine cellar app features",
        },
        {
            "title": "Una cantina privata ha bisogno di contesto, non solo elenco",
            "short": "Sapere cosa possiedi e utile. Capire come usarlo meglio lo e ancora di piu.",
            "medium": (
                "Quando inventario, wishlist e tempi di beva restano scollegati, la gestione perde forza. "
                "Unire questi elementi aiuta a leggere meglio ogni decisione."
            ),
            "cta": "Guarda piu da vicino cosa puo fare Vinaris.",
            "hashtags": "#WineTech #Vinaris #CellarManagement #PrivateCellar",
            "angle": "premium product interface showing connected cellar management capabilities",
        },
    ],
}

CREATIVE_DIRECTIONS = (
    "apertura netta e quasi aforistica",
    "taglio osservazionale con dettaglio concreto",
    "impostazione consulenziale da collezionista esperto",
    "ritmo breve, teso, con una chiusa pulita",
    "struttura piu narrativa e meno promozionale",
    "impostazione analitica con lessico semplice",
    "taglio elegante ma non istituzionale",
    "angolo controintuitivo che ribalta un luogo comune",
)

FORBIDDEN_META_PATTERNS = (
    "spunto leggero",
    "ma non superficiale",
    "il messaggio resta",
    "con un invito",
    "Vinaris lo racconta",
    "in altre parole",
    "senza essere banale",
)

PLATFORM_HASHTAG_COUNTS = {
    "Instagram": 5,
    "Facebook": 5,
    "LinkedIn": 4,
}

INSTAGRAM_FIXED_HASHTAGS = (
    "#winecellar",
    "#winecollector",
    "#finewine",
    "#winelover",
    "#vinaris",
)

CORE_HASHTAGS = {
    "Instagram": ("#Vinaris", "#WineCollection", "#CantinaPrivata"),
    "Facebook": ("#Vinaris", "#CantinaPrivata", "#WineCollector"),
    "LinkedIn": ("#Vinaris", "#WineTech", "#PrivateCellar"),
}

CATEGORY_HASHTAGS = {
    "gestione cantina": ("#GestioneCantina", "#CellarManagement", "#InventarioVini", "#WineInventory"),
    "errori comuni dei collezionisti": ("#WineCollector", "#CollezioneVini", "#CollectorMistakes", "#FineWine"),
    "finestre di beva": ("#DrinkingWindow", "#FineWine", "#WineReadiness", "#MomentoGiusto"),
    "valore della cantina": ("#WineCellarValue", "#PatrimonioEnologico", "#WineAssets", "#PrivateCellarValue"),
    "wishlist": ("#WineWishlist", "#WishlistVini", "#WineBuying", "#CollectorGoals"),
    "consegne": ("#WineDelivery", "#WineLogistics", "#CantinaOrganizzata", "#CellarWorkflow"),
    "beta tester": ("#VinarisBeta", "#BetaTester", "#WineApp", "#ProductFeedback"),
    "funzioni Vinaris": ("#VinarisFeatures", "#WineTech", "#PrivateCellarIntelligence", "#CellarTools"),
}

QUALITY_HASHTAGS = {
    "alto": ("#FineWine", "#CollectionStrategy"),
    "equilibrato": ("#WineCollection", "#CellarInsights"),
    "leggero": ("#WineLovers", "#CellarLife"),
}

CATEGORY_KEYWORDS = {
    "gestione cantina": ("cantina vini", "inventario vini", "gestione cantina", "cantina privata"),
    "errori comuni dei collezionisti": ("collezione vini", "wine collector", "errori di cantina", "gestione bottiglie"),
    "finestre di beva": ("finestra di beva", "quando stappare", "maturazione vino", "fine wine"),
    "valore della cantina": ("valore della cantina", "collezione vini", "fine wine", "patrimonio enologico"),
    "wishlist": ("wishlist vini", "acquisto vino", "collezione vini", "fine wine"),
    "consegne": ("consegna vino", "cantina privata", "registrazione bottiglie", "inventario vini"),
    "beta tester": ("app per cantina", "cantina vini", "wine collector", "beta tester"),
    "funzioni Vinaris": ("app cantina vini", "gestione cantina", "inventario vini", "collezione vini"),
}

CATEGORY_BUILDING_BLOCKS: dict[str, dict[str, tuple[str, ...]]] = {
    "gestione cantina": {
        "titles": (
            "La cantina inizia a migliorare quando smette di vivere in pezzi sparsi",
            "Ordine di cantina non significa rigidita, significa chiarezza",
            "Una collezione ben gestita riduce attrito prima ancora degli errori",
        ),
        "hooks": (
            "Molte cantine private crescono bene ma si consultano male.",
            "Il disordine di una cantina rara comincia quasi sempre dall'informazione.",
            "Quando trovare una bottiglia richiede memoria, il sistema non sta aiutando.",
        ),
        "bodies": (
            "Sapere dove si trova ogni etichetta, cosa e finito e cosa resta da registrare rende piu semplice decidere cosa comprare, cosa spostare e cosa aprire.",
            "Inventario, posizione e note operative hanno piu valore quando convivono nello stesso flusso, invece di restare tra fogli, chat e memoria.",
            "Una vista pulita della cantina evita passaggi inutili e restituisce continuita a decisioni che oggi spesso dipendono da appunti dispersi.",
        ),
        "ctas": (
            "Scopri come Vinaris puo dare piu ordine operativo alla tua cantina.",
            "Richiedi l'accesso beta se vuoi gestire la cantina con un metodo piu leggibile.",
            "Approfondisci come rendere piu lineare la gestione quotidiana della cantina.",
        ),
        "angles": (
            "private cellar inventory clarity with elegant mobile workflow",
            "organized wine cellar records replacing fragmented notes",
            "premium cellar management scene with clean digital tracking",
        ),
    },
    "errori comuni dei collezionisti": {
        "titles": (
            "Gli errori piu costosi iniziano spesso da dettagli trascurati",
            "Una collezione non perde lucidita in un giorno, ma per piccole omissioni",
            "Il doppione non e sfortuna: spesso e solo mancanza di visibilita",
        ),
        "hooks": (
            "I collezionisti esperti sbagliano meno sull'acquisto che sul tracciamento.",
            "Le frizioni piu noiose di una cantina privata arrivano quasi sempre in silenzio.",
            "Quando i dettagli non restano leggibili, gli errori ricompaiono.",
        ),
        "bodies": (
            "Doppioni, bottiglie dimenticate e priorita confuse non dipendono dalla passione, ma da un sistema che non restituisce abbastanza contesto al momento giusto.",
            "Un errore ricorrente non e solo operativo: modifica il modo in cui leggi gli acquisti futuri e l'intera collezione.",
            "Registrare bene posizione, quantita e tempi di beva riduce gli errori prima che diventino abitudine.",
        ),
        "ctas": (
            "Scopri come Vinaris aiuta a ridurre questi attriti nella pratica.",
            "Entra nella beta se vuoi una gestione piu lucida della collezione.",
            "Guarda da vicino un approccio pensato per evitare errori ripetuti.",
        ),
        "angles": (
            "fine wine collection errors contrasted with precise digital tracking",
            "collector avoiding duplicate purchases through clean cellar overview",
            "premium cellar management highlighting hidden collector mistakes",
        ),
    },
    "finestre di beva": {
        "titles": (
            "Il momento giusto non e un'intuizione: e una lettura",
            "La finestra di beva cambia piu dell'apertura, cambia il senso dell'acquisto",
            "Non tutte le bottiglie chiedono pazienza allo stesso modo",
        ),
        "hooks": (
            "Una buona bottiglia aperta nel momento sbagliato racconta solo una parte di se.",
            "Aspettare troppo o troppo poco ha lo stesso effetto: riduce il potenziale.",
            "La finestra di beva e pratica, non teorica, quando devi scegliere cosa aprire.",
        ),
        "bodies": (
            "Tenere sotto controllo la maturazione aiuta a dare priorita alle bottiglie giuste e a far coincidere occasione, prontezza e valore dell'esperienza.",
            "Sapere quali etichette stanno entrando nel momento ideale evita aperture premature e indecisioni davanti alla cantina.",
            "Una lettura ordinata dei tempi di beva rende la scelta piu coerente con il percorso di ogni bottiglia.",
        ),
        "ctas": (
            "Approfondisci come Vinaris puo aiutarti a leggere meglio questi tempi.",
            "Scopri un modo piu chiaro di decidere quando stappare.",
            "Richiedi l'accesso beta se vuoi portare piu precisione in questa scelta.",
        ),
        "angles": (
            "mature bottle readiness cues in an elegant private cellar",
            "refined wine drinking window concept with subtle timing interface",
            "premium cellar scene focused on bottle readiness and timing",
        ),
    },
    "valore della cantina": {
        "titles": (
            "Il valore di una cantina conta anche quando non pensi di venderla",
            "Patrimonio enologico significa anche visione, non solo possesso",
            "Una collezione importante merita una lettura economica all'altezza",
        ),
        "hooks": (
            "Una collezione privata non e solo emozione: richiede anche chiarezza.",
            "Quando una cantina cresce, il suo valore smette di essere un dettaglio laterale.",
            "Capire il peso reale di una collezione aiuta a decidere con piu precisione.",
        ),
        "bodies": (
            "Avere una vista leggibile del valore complessivo aiuta a dare priorita agli acquisti, contestualizzare le annate e muoversi con maggiore consapevolezza.",
            "Il valore della cantina non serve solo a misurare: serve a leggere meglio il patrimonio che stai costruendo nel tempo.",
            "Una metrica chiara non raffredda la passione, la rende piu informata quando devi confrontare, conservare o pianificare.",
        ),
        "ctas": (
            "Scopri come Vinaris puo dare piu contesto al valore della tua collezione.",
            "Richiedi l'accesso beta se vuoi una lettura piu strutturata del patrimonio in cantina.",
            "Approfondisci come trasformare il valore della cantina in una vista utile, non astratta.",
        ),
        "angles": (
            "luxury wine cellar valuation with discreet analytical interface",
            "private cellar wealth overview in an elegant editorial style",
            "premium fine wine collection value analysis concept",
        ),
    },
    "wishlist": {
        "titles": (
            "Una wishlist utile riduce impulsi, non desiderio",
            "Comprare meglio spesso inizia molto prima dell'acquisto",
            "La wishlist giusta non accumula nomi: costruisce priorita",
        ),
        "hooks": (
            "Tra desiderio e acquisto c'e uno spazio che merita metodo.",
            "Una wishlist seria non serve a ricordare tutto, serve a scegliere meglio.",
            "Le grandi bottiglie non entrano in cantina per caso quando le priorita sono chiare.",
        ),
        "bodies": (
            "Annotare produttori, annate e motivi dell'interesse rende piu facile confrontare occasioni reali e difendere scelte meno impulsive.",
            "Una wishlist ben tenuta diventa uno strumento di selezione, non solo una lista di tentazioni in attesa.",
            "Quando il desiderio ha contesto, gli acquisti diventano piu coerenti con la direzione della collezione.",
        ),
        "ctas": (
            "Esplora un modo piu ordinato di costruire la tua wishlist.",
            "Richiedi l'accesso beta per dare continuita alle tue priorita d'acquisto.",
            "Scopri come Vinaris puo rendere piu utile la tua wishlist da collezionista.",
        ),
        "angles": (
            "elegant wine wishlist planning near a private tasting table",
            "collector curating fine wine wishlist with premium mobile interface",
            "refined wishlist workflow for a serious wine collector",
        ),
    },
    "consegne": {
        "titles": (
            "La precisione di una cantina si misura anche all'arrivo delle bottiglie",
            "Una consegna gestita male continua a creare attrito per mesi",
            "La logica della cantina comincia dall'ingresso, non dallo scaffale",
        ),
        "hooks": (
            "Le consegne sono un dettaglio solo finche non generano confusione.",
            "Ogni nuova bottiglia entra in un sistema, non solo in uno spazio fisico.",
            "L'arrivo di un vino e il primo momento in cui la cantina puo restare chiara oppure complicarsi.",
        ),
        "bodies": (
            "Registrare subito cosa e arrivato, dove andra e come integrarlo nell'inventario riduce dispersione e rende piu affidabile tutto il resto.",
            "Una procedura semplice in ingresso evita che il disordine si trascini poi tra scaffali, acquisti futuri e controllo disponibilita.",
            "La qualita della gestione si vede anche da quanto velocemente una consegna diventa informazione leggibile.",
        ),
        "ctas": (
            "Scopri come Vinaris semplifica il passaggio dalla consegna alla cantina.",
            "Approfondisci un flusso di ingresso piu ordinato e meno dispersivo.",
            "Richiedi l'accesso beta se vuoi dare piu precisione a questo passaggio.",
        ),
        "angles": (
            "fine wine delivery intake into a meticulously organized private cellar",
            "premium wine arrival workflow with elegant digital registration",
            "private cellar receiving process rendered with refined logistics cues",
        ),
    },
    "beta tester": {
        "titles": (
            "La beta Vinaris cerca collezionisti che vogliono incidere sul metodo",
            "Entrare in beta ha senso solo se il feedback migliora davvero il prodotto",
            "Non una prova generica, ma un accesso anticipato con utilita concreta",
        ),
        "hooks": (
            "La beta e piu utile quando coinvolge chi vive la cantina con continuita.",
            "Stiamo cercando feedback che nascano da abitudini reali, non da curiosita superficiale.",
            "Un buon beta tester non prova tutto: mette alla prova cio che conta davvero.",
        ),
        "bodies": (
            "L'accesso anticipato a Vinaris e pensato per appassionati e collezionisti privati che vogliono contribuire con osservazioni concrete su inventario, wishlist e gestione.",
            "La proposta beta include accesso iniziale e contatto diretto con il prodotto, con 2 mesi gratuiti escluso AI Pack per chi entra in questa fase.",
            "Cerchiamo un confronto utile sul lavoro quotidiano di cantina, non solo un test veloce delle schermate.",
        ),
        "ctas": (
            "Candidati alla beta se vuoi provare Vinaris in una fase ancora plasmabile.",
            "Richiedi l'accesso anticipato se vuoi contribuire con feedback concreto.",
            "Scopri se la beta Vinaris e il contesto giusto per il tuo modo di gestire la cantina.",
        ),
        "angles": (
            "exclusive beta access invitation for a premium wine-tech platform",
            "refined product beta program for serious private cellar collectors",
            "premium early access campaign for wine collectors and beta testers",
        ),
    },
    "funzioni Vinaris": {
        "titles": (
            "Vinaris collega decisioni che di solito restano separate",
            "Una buona app di cantina non archivia soltanto: orienta",
            "Le funzioni utili sono quelle che restituiscono contesto, non solo dati",
        ),
        "hooks": (
            "Un elenco bottiglie da solo raramente basta a gestire bene una cantina.",
            "Il valore di uno strumento si vede quando collega inventario, scelta e priorita.",
            "Le funzioni contano davvero quando riducono passaggi e chiariscono decisioni.",
        ),
        "bodies": (
            "Inventario, wishlist, finestre di beva e visione del valore della collezione funzionano meglio quando smettono di vivere in strumenti separati.",
            "L'obiettivo non e aggiungere schermate, ma costruire una lettura piu continua della cantina privata.",
            "Unire dati e contesto permette di usare la cantina con maggiore lucidita, non solo di registrarla.",
        ),
        "ctas": (
            "Guarda piu da vicino cosa puo fare Vinaris.",
            "Richiedi l'accesso beta per esplorare le funzioni in modo concreto.",
            "Scopri come le funzioni Vinaris possono dare piu continuita alla gestione.",
        ),
        "angles": (
            "premium wine cellar app feature overview with connected workflows",
            "clean editorial product showcase for private cellar intelligence",
            "refined interface presenting connected wine collection features",
        ),
    },
}


@dataclass(slots=True)
class GeneratedPost:
    platform: str
    category: str
    platform_aspect_ratio: str
    seriousness_level: str
    tone_warmth: str
    promotional_intensity: str
    target_age_range: str | None
    target_gender: str | None
    target_region: str | None
    target_expertise: str | None
    target_spending_power: str | None
    title_internal: str
    text_short: str
    text_medium: str
    cta: str
    hashtags: str
    image_prompt: str
    status: str
    created_at: str
    scheduled_at: str
    published_at: str | None = None
    image_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "category": self.category,
            "platform_aspect_ratio": self.platform_aspect_ratio,
            "seriousness_level": self.seriousness_level,
            "tone_warmth": self.tone_warmth,
            "promotional_intensity": self.promotional_intensity,
            "target_age_range": self.target_age_range,
            "target_gender": self.target_gender,
            "target_region": self.target_region,
            "target_expertise": self.target_expertise,
            "target_spending_power": self.target_spending_power,
            "title_internal": self.title_internal,
            "text_short": self.text_short,
            "text_medium": self.text_medium,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "image_prompt": self.image_prompt,
            "status": self.status,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "published_at": self.published_at,
            "image_path": self.image_path,
        }


class ContentGenerator:
    def __init__(self, openai_api_key: str | None, brand: BrandProfile = VINARIS_BRAND) -> None:
        self.openai_api_key = openai_api_key
        self.brand = brand

    def generate_posts(
        self,
        count: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
        target_age_range: str | None = None,
        target_gender: str | None = None,
        target_region: str | None = None,
        target_expertise: str | None = None,
        target_spending_power: str | None = None,
        recent_history: list[dict[str, str]] | None = None,
    ) -> list[GeneratedPost]:
        if count < 1:
            raise ValueError("count deve essere maggiore di zero.")
        if platform and platform not in PLATFORMS:
            raise ValueError(f"Piattaforma non valida: {platform}")
        if category and category not in CATEGORIES:
            raise ValueError(f"Categoria non valida: {category}")
        if seriousness_level not in SERIOUSNESS_LEVELS:
            raise ValueError(f"Livello di serieta non valido: {seriousness_level}")
        if tone_warmth not in WARMTH_LEVELS:
            raise ValueError(f"Livello di calore non valido: {tone_warmth}")
        if promotional_intensity not in PROMOTIONAL_LEVELS:
            raise ValueError(f"Livello promozionale non valido: {promotional_intensity}")
        if target_age_range and target_age_range not in TARGET_AGE_RANGES:
            raise ValueError(f"Fascia eta target non valida: {target_age_range}")
        if target_gender and target_gender not in TARGET_GENDERS:
            raise ValueError(f"Genere target non valido: {target_gender}")
        if target_expertise and target_expertise not in TARGET_EXPERTISE_LEVELS:
            raise ValueError(f"Esperienza target non valida: {target_expertise}")
        if target_spending_power and target_spending_power not in TARGET_SPENDING_POWERS:
            raise ValueError(f"Potere d'acquisto target non valido: {target_spending_power}")

        ai_posts = self._generate_with_openai(
            count,
            platform=platform,
            category=category,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            target_age_range=target_age_range,
            target_gender=target_gender,
            target_region=target_region,
            target_expertise=target_expertise,
            target_spending_power=target_spending_power,
            recent_history=recent_history or [],
        )
        if len(ai_posts) >= count:
            return ai_posts[:count]

        existing_signatures = {
            self._signature_from_parts(
                item.get("title_internal", ""),
                item.get("text_short", ""),
                item.get("cta", ""),
            )
            for item in (recent_history or [])
        }
        existing_signatures.update(
            self._signature_from_parts(post.title_internal, post.text_short, post.cta)
            for post in ai_posts
        )
        posts = list(ai_posts)
        for index in range(len(posts), count):
            mock_post = self._build_mock_post(
                index,
                platform=platform,
                category=category,
                seriousness_level=seriousness_level,
                tone_warmth=tone_warmth,
                promotional_intensity=promotional_intensity,
                target_age_range=target_age_range,
                target_gender=target_gender,
                target_region=target_region,
                target_expertise=target_expertise,
                target_spending_power=target_spending_power,
                used_signatures=existing_signatures,
            )
            posts.append(mock_post)
            existing_signatures.add(
                self._signature_from_parts(mock_post.title_internal, mock_post.text_short, mock_post.cta)
            )
        return posts

    def _generate_with_openai(
        self,
        count: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
        target_age_range: str | None = None,
        target_gender: str | None = None,
        target_region: str | None = None,
        target_expertise: str | None = None,
        target_spending_power: str | None = None,
        recent_history: list[dict[str, str]] | None = None,
    ) -> list[GeneratedPost]:
        if not self.openai_api_key or OpenAI is None:
            return []

        client = OpenAI(api_key=self.openai_api_key)
        prompt = self._build_openai_prompt(
            count,
            platform=platform,
            category=category,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            target_age_range=target_age_range,
            target_gender=target_gender,
            target_region=target_region,
            target_expertise=target_expertise,
            target_spending_power=target_spending_power,
            recent_history=recent_history or [],
        )

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )
            raw_text = getattr(response, "output_text", "").strip()
            data = json.loads(self._extract_json_payload(raw_text))
        except Exception:
            return []

        if not isinstance(data, list):
            return []

        posts: list[GeneratedPost] = []
        seen_signatures = {
            self._signature_from_parts(
                item.get("title_internal", ""),
                item.get("text_short", ""),
                item.get("cta", ""),
            )
            for item in (recent_history or [])
        }
        for index, item in enumerate(data[:count]):
            try:
                platform_name = str(item["platform"])
                category_name = str(item["category"])
                title = self._clean_generated_text(str(item["title_internal"]))
                short = self._clean_generated_text(str(item["text_short"]))
                medium = self._clean_generated_text(str(item["text_medium"]))
                cta = self._clean_generated_text(str(item["cta"]))
                hashtags = self._normalize_hashtags(
                    platform_name,
                    category_name,
                    str(item["hashtags"]),
                    seriousness_level=seriousness_level,
                )
                angle = self._clean_generated_text(str(item.get("image_angle", category_name)))
            except (KeyError, TypeError, ValueError):
                continue

            signature = self._signature_from_parts(title, short, cta)
            if not title or not short or not medium or not cta or signature in seen_signatures:
                continue

            created_at = datetime.now().isoformat(timespec="seconds")
            scheduled_at = suggest_scheduled_date(index).isoformat(timespec="seconds")
            profile = get_platform_profile(platform_name)
            posts.append(
                GeneratedPost(
                    platform=platform_name,
                    category=category_name,
                    platform_aspect_ratio=profile.recommended_aspect_ratio,
                    seriousness_level=seriousness_level,
                    tone_warmth=tone_warmth,
                    promotional_intensity=promotional_intensity,
                    target_age_range=target_age_range,
                    target_gender=target_gender,
                    target_region=target_region,
                    target_expertise=target_expertise,
                    target_spending_power=target_spending_power,
                    title_internal=title,
                    text_short=short,
                    text_medium=medium,
                    cta=cta,
                    hashtags=hashtags,
                    image_prompt=generate_image_prompt(
                        platform_name,
                        category_name,
                        angle,
                        seriousness_level=seriousness_level,
                        tone_warmth=tone_warmth,
                        promotional_intensity=promotional_intensity,
                    ),
                    status="draft",
                    created_at=created_at,
                    scheduled_at=scheduled_at,
                )
            )
            seen_signatures.add(signature)
        return posts

    def _build_mock_post(
        self,
        index: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
        target_age_range: str | None = None,
        target_gender: str | None = None,
        target_region: str | None = None,
        target_expertise: str | None = None,
        target_spending_power: str | None = None,
        used_signatures: set[str] | None = None,
    ) -> GeneratedPost:
        category_name = category or CATEGORIES[index % len(CATEGORIES)]
        platform_name = platform or PLATFORMS[index % len(PLATFORMS)]
        created_at = datetime.now().isoformat(timespec="seconds")
        scheduled_at = suggest_scheduled_date(index).isoformat(timespec="seconds")
        profile = get_platform_profile(platform_name)
        used_signatures = used_signatures or set()

        for _ in range(12):
            post_payload = self._compose_mock_payload(
                platform_name,
                category_name,
                seriousness_level=seriousness_level,
                tone_warmth=tone_warmth,
                promotional_intensity=promotional_intensity,
                target_region=target_region,
                target_expertise=target_expertise,
                target_spending_power=target_spending_power,
            )
            signature = self._signature_from_parts(
                post_payload["title"],
                post_payload["short"],
                post_payload["cta"],
            )
            if signature not in used_signatures:
                break
        else:
            template = random.choice(MOCK_ANGLES[category_name])
            post_payload = {
                "title": template["title"],
                "short": template["short"],
                "medium": template["medium"],
                "cta": self._apply_editorial_tone_to_cta(
                    template["cta"],
                    seriousness_level=seriousness_level,
                    tone_warmth=tone_warmth,
                    promotional_intensity=promotional_intensity,
                ),
                "hashtags": template["hashtags"],
                "angle": template["angle"],
            }

        return GeneratedPost(
            platform=platform_name,
            category=category_name,
            platform_aspect_ratio=profile.recommended_aspect_ratio,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            target_age_range=target_age_range,
            target_gender=target_gender,
            target_region=target_region,
            target_expertise=target_expertise,
            target_spending_power=target_spending_power,
            title_internal=post_payload["title"],
            text_short=post_payload["short"],
            text_medium=post_payload["medium"],
            cta=post_payload["cta"],
            hashtags=post_payload["hashtags"],
            image_prompt=generate_image_prompt(
                platform_name,
                category_name,
                post_payload["angle"],
                seriousness_level=seriousness_level,
                tone_warmth=tone_warmth,
                promotional_intensity=promotional_intensity,
            ),
            status="draft",
            created_at=created_at,
            scheduled_at=scheduled_at,
        )

    def _build_openai_prompt(
        self,
        count: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
        target_age_range: str | None = None,
        target_gender: str | None = None,
        target_region: str | None = None,
        target_expertise: str | None = None,
        target_spending_power: str | None = None,
        recent_history: list[dict[str, str]] | None = None,
    ) -> str:
        platform_rule = (
            f"- usa solo la piattaforma: {platform}"
            if platform
            else "- piattaforme possibili: Facebook, Instagram, LinkedIn"
        )
        category_rule = (
            f"- usa solo la categoria: {category}"
            if category
            else f"- categorie possibili: {', '.join(CATEGORIES)}"
        )
        seriousness_rule = {
            "alto": "tono molto serio, autorevole, misurato; niente ironia o leggerezza marcata",
            "equilibrato": "tono premium ma non rigido; credibile, chiaro, con una lieve naturalezza",
            "leggero": "tono piu leggero e arioso, elegante, con una nota piu colloquiale; niente meme o comicita eccessiva",
        }[seriousness_level]
        warmth_rule = {
            "sobrio": "registro distaccato e composto, poco confidenziale",
            "caldo": "registro piu umano e vicino, senza perdere eleganza",
            "coinvolgente": "registro piu energico e invitante, pur restando premium",
        }[tone_warmth]
        promotional_rule = {
            "discreto": "CTA soft, orientata alla scoperta, evita pressione commerciale",
            "equilibrato": "CTA chiara ma non insistente, con invito esplicito all'azione",
            "deciso": "CTA piu netta e orientata alla conversione, senza diventare aggressiva",
        }[promotional_intensity]
        creative_mix = random.sample(CREATIVE_DIRECTIONS, k=min(max(count, 2), len(CREATIVE_DIRECTIONS)))
        creative_bullets = "\n".join(f"- {item}" for item in creative_mix)
        recent_examples = self._format_recent_history_examples(recent_history or [])
        audience_constraints = self._build_audience_constraints(
            target_age_range=target_age_range,
            target_gender=target_gender,
            target_region=target_region,
            target_expertise=target_expertise,
            target_spending_power=target_spending_power,
        )
        keyword_rule = self._build_keyword_rule(category)
        return f"""
Genera {count} post social in JSON puro come array.

Contesto brand:
{brand_context(self.brand)}

Vincoli:
{platform_rule}
{category_rule}
- tono premium, competente, sobrio
- serieta richiesta: {seriousness_level} -> {seriousness_rule}
- calore del tono: {tone_warmth} -> {warmth_rule}
- intensita promozionale: {promotional_intensity} -> {promotional_rule}
- audience target: {audience_constraints}
- lingua italiana
- puoi citare la beta offer ({self.brand.beta_offer}) solo se coerente con il singolo post
- non usare tono aggressivo
- evita formule ripetitive tra un post e l'altro
- non scrivere meta-commenti o frasi interne tipo "il messaggio resta", "Vinaris lo racconta", "con un invito"
- non chiudere il testo con valutazioni editoriali del tipo "spunto leggero", "ma non superficiale", "senza essere banale" o formule da copy review
- non spiegare il tono: applicalo direttamente nella copy
- non aggiungere la stessa coda standard su ogni testo
- varia in modo netto apertura, ritmo, struttura e CTA tra i post dello stesso batch
- evita di riusare la stessa CTA, la stessa frase finale o lo stesso schema di due frasi in post consecutivi
- rendi ogni post distinto per prospettiva: alcuni piu analitici, altri piu osservazionali, altri piu concreti
- se menzioni la beta, fallo solo quando serve davvero al post: non renderla il centro obbligatorio di ogni copy
- priorita discovery: inserisci le keyword principali nel titolo, nel text_short e nel text_medium in modo naturale, senza keyword stuffing
- keyword guide: {keyword_rule}

Direzioni creative da distribuire nel batch:
{creative_bullets}

Post recenti da non imitare o parafrasare:
{recent_examples}

Per ogni oggetto JSON usa queste chiavi:
platform, category, title_internal, text_short, text_medium, cta, hashtags, image_angle

Regole:
- text_short massimo 320 caratteri
- text_medium massimo 700 caratteri
- hashtags in una singola stringa
- per Instagram usa esattamente questi 5 hashtag, nello stesso ordine: #winecellar #winecollector #finewine #winelover #vinaris
- per Facebook e LinkedIn usa pochi hashtag pertinenti e credibili
- evita hashtag inutili o troppo vaghi tipo #love #passion #luxurylife #winetime
- image_angle descrive il concetto visivo in inglese
- nessun testo fuori dal JSON
""".strip()

    @staticmethod
    def _apply_editorial_tone_to_cta(
        cta: str,
        *,
        seriousness_level: str,
        tone_warmth: str,
        promotional_intensity: str,
    ) -> str:
        del seriousness_level, tone_warmth
        if promotional_intensity == "equilibrato":
            return cta

        if promotional_intensity == "discreto":
            replacements = (
                ("Richiedi l'accesso beta", "Scopri la beta"),
                ("Richiedi l'accesso anticipato", "Scopri l'accesso anticipato"),
                ("Richiedi", "Scopri"),
                ("Attiva", "Valuta"),
                ("Candidati", "Approfondisci"),
                ("Entra", "Scopri"),
            )
        else:
            replacements = (
                ("Scopri", "Richiedi ora"),
                ("Approfondisci", "Richiedi ora"),
                ("Guarda", "Valuta ora"),
                ("Esplora", "Richiedi ora"),
                ("Prova", "Attiva"),
                ("Richiedi", "Richiedi ora"),
            )

        for source, target in replacements:
            if cta.startswith(source):
                return cta.replace(source, target, 1)
        return cta

    def _compose_mock_payload(
        self,
        platform_name: str,
        category_name: str,
        *,
        seriousness_level: str,
        tone_warmth: str,
        promotional_intensity: str,
        target_region: str | None = None,
        target_expertise: str | None = None,
        target_spending_power: str | None = None,
    ) -> dict[str, str]:
        blocks = CATEGORY_BUILDING_BLOCKS[category_name]
        title = random.choice(blocks["titles"])
        hook = random.choice(blocks["hooks"])
        body = random.choice(blocks["bodies"])
        cta = self._apply_editorial_tone_to_cta(
            random.choice(blocks["ctas"]),
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )
        audience_hint = self._build_audience_hint(
            target_region=target_region,
            target_expertise=target_expertise,
            target_spending_power=target_spending_power,
        )
        keyword_hint = self._build_keyword_hint(category_name)
        medium = f"{hook} {body}{audience_hint}{keyword_hint}"
        hashtags = self._build_hashtag_string(
            platform_name,
            category_name,
            seriousness_level=seriousness_level,
        )
        return {
            "title": title,
            "short": hook,
            "medium": medium,
            "cta": cta,
            "hashtags": hashtags,
            "angle": random.choice(blocks["angles"]),
        }

    @staticmethod
    def _extract_json_payload(raw_text: str) -> str:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @classmethod
    def _clean_generated_text(cls, text: str) -> str:
        compact = re.sub(r"\s+", " ", text).strip(" \n\t\"'")
        sentences = re.split(r"(?<=[.!?])\s+", compact)
        filtered = [sentence.strip() for sentence in sentences if not cls._looks_like_meta_comment(sentence)]
        cleaned = " ".join(filtered).strip()
        return cleaned.rstrip(",:;- ")

    @staticmethod
    def _looks_like_meta_comment(text: str) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in FORBIDDEN_META_PATTERNS)

    @staticmethod
    def _signature_from_parts(title: str, short: str, cta: str) -> str:
        del cta
        base = f"{title} {short}".lower()
        return re.sub(r"[^a-z0-9]+", " ", base).strip()

    @staticmethod
    def _format_recent_history_examples(recent_history: list[dict[str, str]]) -> str:
        if not recent_history:
            return "- nessun esempio recente disponibile"
        examples = []
        for item in recent_history[:10]:
            examples.append(
                f'- [{item.get("platform", "-")} / {item.get("category", "-")}] '
                f'titolo="{item.get("title_internal", "")}" short="{item.get("text_short", "")}" '
                f'target="{item.get("target_age_range", "")} {item.get("target_gender", "")} {item.get("target_region", "")}"'
            )
        return "\n".join(examples)

    @staticmethod
    def _build_audience_constraints(
        *,
        target_age_range: str | None,
        target_gender: str | None,
        target_region: str | None,
        target_expertise: str | None,
        target_spending_power: str | None,
    ) -> str:
        parts = [
            f"eta {target_age_range}" if target_age_range else None,
            f"genere {target_gender}" if target_gender else None,
            f"regione {target_region}" if target_region else None,
            f"esperienza {target_expertise}" if target_expertise else None,
            f"spesa {target_spending_power}" if target_spending_power else None,
        ]
        filtered = [item for item in parts if item]
        return ", ".join(filtered) if filtered else "non specificata"

    @staticmethod
    def _build_audience_hint(
        *,
        target_region: str | None,
        target_expertise: str | None,
        target_spending_power: str | None,
    ) -> str:
        hints = []
        if target_region:
            hints.append(f"con sensibilita adatta a un pubblico in {target_region}")
        if target_expertise:
            hints.append(f"pensato per un livello {target_expertise}")
        if target_spending_power:
            hints.append(f"coerente con un target di spesa {target_spending_power}")
        if not hints:
            return ""
        return " " + ". ".join(hints) + "."

    @staticmethod
    def _build_keyword_rule(category_name: str | None) -> str:
        if category_name:
            keywords = CATEGORY_KEYWORDS.get(category_name, ())
            if keywords:
                return ", ".join(keywords)
        fallback: list[str] = []
        for items in CATEGORY_KEYWORDS.values():
            fallback.extend(items[:2])
        deduped = list(dict.fromkeys(fallback))
        return ", ".join(deduped[:10])

    @staticmethod
    def _build_keyword_hint(category_name: str) -> str:
        keywords = CATEGORY_KEYWORDS.get(category_name, ())
        if not keywords:
            return ""
        return f" Keyword narrative da mantenere naturale nel testo: {keywords[0]}, {keywords[1]}."

    def _normalize_hashtags(
        self,
        platform_name: str,
        category_name: str,
        raw_hashtags: str,
        *,
        seriousness_level: str,
    ) -> str:
        if platform_name == "Instagram":
            return " ".join(INSTAGRAM_FIXED_HASHTAGS)

        found = re.findall(r"#?[A-Za-z0-9_À-ÿ]+", raw_hashtags)
        cleaned: list[str] = []
        for tag in found:
            normalized = tag if tag.startswith("#") else f"#{tag}"
            normalized = normalized.replace("##", "#")
            if len(normalized) <= 1:
                continue
            if normalized.lower() in {"#love", "#luxurylife", "#winetime", "#passion"}:
                continue
            if normalized.lower() not in {item.lower() for item in cleaned}:
                cleaned.append(normalized)

        required = self._build_hashtag_candidates(
            platform_name,
            category_name,
            seriousness_level=seriousness_level,
        )
        combined: list[str] = []
        seen: set[str] = set()
        for tag in cleaned + list(required):
            key = tag.lower()
            if key in seen:
                continue
            combined.append(tag)
            seen.add(key)

        limit = PLATFORM_HASHTAG_COUNTS.get(platform_name, 5)
        return " ".join(combined[:limit])

    def _build_hashtag_string(
        self,
        platform_name: str,
        category_name: str,
        *,
        seriousness_level: str,
    ) -> str:
        candidates = list(
            self._build_hashtag_candidates(
                platform_name,
                category_name,
                seriousness_level=seriousness_level,
            )
        )
        limit = PLATFORM_HASHTAG_COUNTS.get(platform_name, 5)
        return " ".join(candidates[:limit])

    @staticmethod
    def _build_hashtag_candidates(
        platform_name: str,
        category_name: str,
        *,
        seriousness_level: str,
    ) -> tuple[str, ...]:
        if platform_name == "Instagram":
            return INSTAGRAM_FIXED_HASHTAGS

        pool = list(CORE_HASHTAGS.get(platform_name, ("#Vinaris",)))
        pool.extend(CATEGORY_HASHTAGS.get(category_name, ()))
        pool.extend(QUALITY_HASHTAGS.get(seriousness_level, ()))
        random.shuffle(pool)
        ordered = ["#Vinaris"]
        ordered.extend(pool)

        result: list[str] = []
        seen: set[str] = set()
        for tag in ordered:
            key = tag.lower()
            if key in seen:
                continue
            result.append(tag)
            seen.add(key)
        return tuple(result)
