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
                "Vinaris aiuta a centralizzare bottiglie, posizioni, quantità e note essenziali in un unico spazio chiaro."
            ),
            "cta": "Scopri come organizzare la tua cantina privata con più precisione.",
            "hashtags": "#Vinaris #CantinaPrivata #WineCollection #GestioneCantina",
            "angle": "collector reviewing an elegant private cellar inventory on smartphone",
        },
        {
            "title": "Ogni bottiglia ha un posto, ogni informazione anche",
            "short": "Una cantina ben gestita semplifica scelte, acquisti e aperture.",
            "medium": (
                "La differenza tra accumulare bottiglie e gestire una cantina privata sta nella qualità delle informazioni. "
                "Con Vinaris puoi tenere sotto controllo dove si trova ogni vino e consultarlo in pochi secondi."
            ),
            "cta": "Richiedi l’accesso beta e prova un approccio più ordinato.",
            "hashtags": "#PrivateCellar #VinarisApp #WineLovers #Cantina",
            "angle": "refined cellar shelves with discrete app interface in foreground",
        },
    ],
    "errori comuni dei collezionisti": [
        {
            "title": "Tre errori silenziosi che indeboliscono una collezione",
            "short": "Il problema spesso non è comprare troppo, ma perdere visibilità su ciò che si possiede.",
            "medium": (
                "Duplicare acquisti, dimenticare finestre di beva e non tracciare il valore della cantina sono errori frequenti. "
                "Vinaris nasce per ridurre questi attriti con una gestione più lucida e continua."
            ),
            "cta": "Vuoi evitare errori ricorrenti? Entra nella beta di Vinaris.",
            "hashtags": "#WineCollector #Vinaris #CollezioneVini #WineTech",
            "angle": "premium visual comparing disorganized notes and clean digital cellar overview",
        }
    ],
    "finestre di beva": [
        {
            "title": "Aprire troppo presto è un costo invisibile",
            "short": "La finestra di beva è una scelta strategica, non un dettaglio secondario.",
            "medium": (
                "Una bottiglia aperta nel momento sbagliato perde parte del suo potenziale. "
                "Monitorare le finestre di beva significa valorizzare meglio ogni acquisto e ogni occasione."
            ),
            "cta": "Scopri come Vinaris può aiutarti a decidere quando stappare.",
            "hashtags": "#WineDrinkingWindow #Vinaris #FineWine #CantinaIntelligente",
            "angle": "sommelier style scene with mature bottle and subtle timing cues on app",
        }
    ],
    "valore della cantina": [
        {
            "title": "Conosci davvero il valore della tua cantina?",
            "short": "Una collezione privata non è solo passione: è anche patrimonio.",
            "medium": (
                "Quando la cantina cresce, avere una visione chiara del suo valore diventa utile per acquisti, priorità e consapevolezza. "
                "Vinaris supporta una lettura più strutturata del patrimonio enologico personale."
            ),
            "cta": "Prova Vinaris e dai più contesto al valore della tua collezione.",
            "hashtags": "#WineCellarValue #Vinaris #WineCollection #PatrimonioEnologico",
            "angle": "luxury cellar with analytical but elegant digital valuation concept",
        }
    ],
    "wishlist": [
        {
            "title": "Le grandi bottiglie iniziano spesso da una wishlist ben fatta",
            "short": "Desiderare un vino è facile. Ricordarsi perché lo si vuole comprare, meno.",
            "medium": (
                "Una wishlist utile non è una lista casuale, ma uno strumento per confrontare annate, produttori e priorità. "
                "Vinaris aiuta a mantenere questa visione con ordine e continuità."
            ),
            "cta": "Organizza la tua wishlist da collezionista con l’accesso beta.",
            "hashtags": "#WineWishlist #Vinaris #WineCollector #PrivateCellar",
            "angle": "elegant collector building a wine wishlist on mobile near tasting table",
        }
    ],
    "consegne": [
        {
            "title": "Anche la consegna fa parte dell’esperienza di cantina",
            "short": "Sapere cosa arriva, quando arriva e dove collocarlo riduce attrito e disordine.",
            "medium": (
                "Ogni nuova consegna merita una registrazione pulita. "
                "Una gestione precisa in ingresso aiuta a mantenere affidabile l’intera fotografia della cantina."
            ),
            "cta": "Scopri come Vinaris semplifica il passaggio dalla consegna alla scaffalatura.",
            "hashtags": "#WineDelivery #Vinaris #CantinaPrivata #WineManagement",
            "angle": "premium home delivery of fine wine entering an organized private cellar",
        }
    ],
    "beta tester": [
        {
            "title": "La beta Vinaris è pensata per chi prende sul serio la propria cantina",
            "short": "Accesso anticipato, feedback diretto e 2 mesi gratuiti escluso AI Pack.",
            "medium": (
                "Stiamo aprendo la beta di Vinaris a un gruppo selezionato di appassionati e collezionisti privati. "
                "Il piano beta parte da CHF 6/mese o CHF 60/anno, con 2 mesi gratuiti escluso AI Pack per i beta tester."
            ),
            "cta": "Candidati come beta tester e prova Vinaris in anteprima.",
            "hashtags": "#VinarisBeta #BetaTester #WineApp #PrivateCellarIntelligence",
            "angle": "exclusive beta invitation for a premium wine-tech product",
        }
    ],
    "funzioni Vinaris": [
        {
            "title": "Vinaris non è una semplice lista bottiglie",
            "short": "È uno spazio pensato per dare contesto operativo alla tua cantina privata.",
            "medium": (
                "Gestione inventario, wishlist, controllo delle finestre di beva e maggiore visibilità sul valore della collezione: "
                "Vinaris mette ordine dove spesso esistono strumenti separati."
            ),
            "cta": "Esplora le funzioni Vinaris e richiedi l’accesso beta.",
            "hashtags": "#VinarisFeatures #WineTech #CantinaPrivata #PrivateCellar",
            "angle": "clean premium product showcase of wine cellar app features",
        }
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
                platform = str(item["platform"])
                category = str(item["category"])
                title = str(item["title_internal"])
                short = str(item["text_short"])
                medium = str(item["text_medium"])
                cta = str(item["cta"])
                hashtags = str(item["hashtags"])
                angle = str(item.get("image_angle", category))
            except (KeyError, TypeError, ValueError):
                continue

            created_at = datetime.now().isoformat(timespec="seconds")
            scheduled_at = suggest_scheduled_date(index).isoformat(timespec="seconds")
            profile = get_platform_profile(platform)
            posts.append(
                GeneratedPost(
                    platform=platform,
                    category=category,
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
                        platform,
                        category,
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
        category = category or CATEGORIES[index % len(CATEGORIES)]
        platform = platform or PLATFORMS[index % len(PLATFORMS)]
        template = random.choice(MOCK_ANGLES[category])
        created_at = datetime.now().isoformat(timespec="seconds")
        scheduled_at = suggest_scheduled_date(index).isoformat(timespec="seconds")
        profile = get_platform_profile(platform)

        platform_suffix = {
            "Facebook": "con taglio informativo e accessibile",
            "Instagram": "con taglio visivo e sintetico",
            "LinkedIn": "con taglio più strategico e professionale",
        }[platform]

        short = f"{template['short']} {self.brand.name} lo racconta {platform_suffix}."
        medium = (
            f"{template['medium']} {self.brand.name} porta questo approccio nel digitale "
            f"per offrire private cellar intelligence a collezionisti esigenti."
        )
        title = self._apply_editorial_tone_to_title(template["title"], seriousness_level)
        short = self._apply_editorial_tone_to_copy(
            short,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            short_form=True,
        )
        medium = self._apply_editorial_tone_to_copy(
            medium,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            short_form=False,
        )
        cta = self._apply_editorial_tone_to_cta(
            template["cta"],
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
        )

        return GeneratedPost(
            platform=platform,
            category=category,
            platform_aspect_ratio=profile.recommended_aspect_ratio,
            seriousness_level=seriousness_level,
            tone_warmth=tone_warmth,
            promotional_intensity=promotional_intensity,
            title_internal=title,
            text_short=short,
            text_medium=medium,
            cta=cta,
            hashtags=template["hashtags"],
            image_prompt=generate_image_prompt(
                platform,
                category,
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
    def _apply_editorial_tone_to_title(title: str, seriousness_level: str) -> str:
        if seriousness_level == "leggero":
            return f"{title} Senza appesantire il piacere di collezionare."
        if seriousness_level == "alto":
            return title
        return f"{title} Con il giusto equilibrio."

    @staticmethod
    def _apply_editorial_tone_to_copy(
        text: str,
        *,
        seriousness_level: str,
        tone_warmth: str,
        promotional_intensity: str,
        short_form: bool,
    ) -> str:
        seriousness_addition = {
            "alto": " Il tono resta misurato, lucido e orientato al valore della cantina.",
            "equilibrato": " Il messaggio resta chiaro, credibile e facile da leggere.",
            "leggero": " Il messaggio resta curato ma con un passo piu leggero e naturale.",
        }[seriousness_level]
        warmth_addition = {
            "sobrio": " Nessun eccesso, solo contesto utile e ben calibrato.",
            "caldo": " Con una voce piu vicina a chi vive davvero la cantina ogni giorno.",
            "coinvolgente": " Con un invito piu vivo a immaginare una gestione della cantina piu semplice.",
        }[tone_warmth]
        promotional_addition = {
            "discreto": " L'invito finale rimane misurato.",
            "equilibrato": " L'invito finale e presente ma non invadente.",
            "deciso": " L'invito finale e piu esplicito e orientato all'azione.",
        }[promotional_intensity]
        additions = seriousness_addition + warmth_addition
        if not short_form:
            additions += promotional_addition
        return f"{text}{additions}"

    @staticmethod
    def _apply_editorial_tone_to_cta(
        cta: str,
        *,
        seriousness_level: str,
        tone_warmth: str,
        promotional_intensity: str,
    ) -> str:
        del seriousness_level
        if promotional_intensity == "deciso":
            return cta.replace("Scopri", "Richiedi").replace("Prova", "Attiva").replace("Esplora", "Richiedi")
        if tone_warmth == "coinvolgente":
            return f"{cta} In modo semplice e diretto."
        return cta
