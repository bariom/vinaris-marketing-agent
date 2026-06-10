from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BrandProfile:
    name: str
    payoff: str
    target: str
    tone_of_voice: str
    primary_language: str
    monthly_price: str
    yearly_price: str
    beta_offer: str


VINARIS_BRAND = BrandProfile(
    name="Vinaris",
    payoff="Private cellar intelligence",
    target="appassionati e collezionisti privati di vino",
    tone_of_voice="premium, competente, sobrio, non aggressivo",
    primary_language="italiano",
    monthly_price="CHF 6/mese",
    yearly_price="CHF 60/anno",
    beta_offer="2 mesi gratuiti escluso AI Pack",
)


def brand_context(profile: BrandProfile = VINARIS_BRAND) -> str:
    return (
        f"{profile.name} | {profile.payoff} | target: {profile.target} | "
        f"tono: {profile.tone_of_voice} | lingua: {profile.primary_language} | "
        f"beta: {profile.monthly_price}, {profile.yearly_price}, offerta {profile.beta_offer}"
    )
