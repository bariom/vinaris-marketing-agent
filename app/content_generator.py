from __future__ import annotations

import json
import random
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


@dataclass(slots=True)
class GeneratedPost:
    platform: str
    category: str
    platform_aspect_ratio: str
    seriousness_level: str
    tone_warmth: str
    promotional_intensity: str
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

        ai_posts = self._generate_with_openai(
            count,
            platform=platform,
            category=category,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )
        if ai_posts:
            return ai_posts
        return [
            self._build_mock_post(
                index,
                platform=platform,
                category=category,
                seriousness_level=seriousness_level,
                tone_warmth=tone_warmth,
                promotional_intensity=promotional_intensity,
            )
            for index in range(count)
        ]

    def _generate_with_openai(
        self,
        count: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
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
        )

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )
            raw_text = getattr(response, "output_text", "").strip()
            data = json.loads(raw_text)
        except Exception:
            return []

        if not isinstance(data, list):
            return []

        posts: list[GeneratedPost] = []
        for index, item in enumerate(data[:count]):
            try:
                platform_name = str(item["platform"])
                category_name = str(item["category"])
                title = str(item["title_internal"])
                short = str(item["text_short"])
                medium = str(item["text_medium"])
                cta = str(item["cta"])
                hashtags = str(item["hashtags"])
                angle = str(item.get("image_angle", category_name))
            except (KeyError, TypeError, ValueError):
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
        return posts

    def _build_mock_post(
        self,
        index: int,
        platform: str | None = None,
        category: str | None = None,
        seriousness_level: str = "equilibrato",
        tone_warmth: str = "sobrio",
        promotional_intensity: str = "discreto",
    ) -> GeneratedPost:
        category_name = category or CATEGORIES[index % len(CATEGORIES)]
        platform_name = platform or PLATFORMS[index % len(PLATFORMS)]
        template = random.choice(MOCK_ANGLES[category_name])
        created_at = datetime.now().isoformat(timespec="seconds")
        scheduled_at = suggest_scheduled_date(index).isoformat(timespec="seconds")
        profile = get_platform_profile(platform_name)

        short = template["short"]
        medium = template["medium"]
        cta = self._apply_editorial_tone_to_cta(
            template["cta"],
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )

        return GeneratedPost(
            platform=platform_name,
            category=category_name,
            platform_aspect_ratio=profile.recommended_aspect_ratio,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            title_internal=template["title"],
            text_short=short,
            text_medium=medium,
            cta=cta,
            hashtags=template["hashtags"],
            image_prompt=generate_image_prompt(
                platform_name,
                category_name,
                template["angle"],
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
- lingua italiana
- includi un riferimento credibile alla beta tester offer: {self.brand.beta_offer}
- non usare tono aggressivo
- evita formule ripetitive tra un post e l'altro
- non scrivere meta-commenti o frasi interne tipo "il messaggio resta", "Vinaris lo racconta", "con un invito"
- non spiegare il tono: applicalo direttamente nella copy
- non aggiungere la stessa coda standard su ogni testo
- varia in modo netto apertura, ritmo, struttura e CTA tra i post dello stesso batch
- evita di riusare la stessa CTA, la stessa frase finale o lo stesso schema di due frasi in post consecutivi

Per ogni oggetto JSON usa queste chiavi:
platform, category, title_internal, text_short, text_medium, cta, hashtags, image_angle

Regole:
- text_short massimo 320 caratteri
- text_medium massimo 700 caratteri
- hashtags in una singola stringa
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
