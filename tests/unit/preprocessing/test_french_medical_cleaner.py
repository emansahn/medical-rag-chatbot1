"""Unit tests for FrenchMedicalCleaner."""
from src.preprocessing.cleaning.french_medical_cleaner import FrenchMedicalCleaner
from src.preprocessing.interfaces.document_loader_interface import TextCleaner


def test_removes_isolated_page_number_lines():
    text = (
        "PARTIE 1. RAPPELS SUR L'HVC\n"
        "12\n"
        "Virologie de l'HVC : le virus se transmet par voie sanguine.\n"
        "- 12 -\n"
        "Page 12\n"
        "12 / 340\n"
        "Fin de la partie 1."
    )

    cleaner = FrenchMedicalCleaner()
    assert isinstance(cleaner, TextCleaner)
    cleaned = cleaner.clean(text)

    assert "12" not in cleaned.split("\n")
    assert "- 12 -" not in cleaned
    assert "Page 12" not in cleaned
    assert "12 / 340" not in cleaned
    assert "Virologie de l'HVC" in cleaned
    assert "Fin de la partie 1." in cleaned


def test_keeps_numbers_within_normal_text():
    text = "Le patient a 12 ans et pese 40 kg."

    cleaned = FrenchMedicalCleaner().clean(text)

    assert cleaned == text


def test_normalizes_multiple_spaces_and_blank_lines():
    text = "Le  diabete    de type 2\n\n\n\nse previent   par une bonne hygiene de vie.   "

    cleaned = FrenchMedicalCleaner().clean(text)

    assert cleaned == "Le diabete de type 2\n\nse previent par une bonne hygiene de vie."


def test_removes_web_noise_lines():
    text = (
        "Journee mondiale de la Sante : ensemble contre le diabete\n"
        "Recherche\n"
        "Filtrer par date:\n"
        "Le diabete cause 1,5 million de deces chaque annee."
    )

    cleaned = FrenchMedicalCleaner().clean(text)

    assert "Recherche" not in cleaned
    assert "Filtrer par date" not in cleaned
    assert "Journee mondiale de la Sante" in cleaned
    assert "Le diabete cause 1,5 million de deces chaque annee." in cleaned


def test_removes_emro_who_int_search_widget_noise():
    text = (
        "Ouvrir le calendrier\n"
        "Rechercher:\n"
        "Tous les mots\n"
        "N'importe quel mot\n"
        "Phrase exacte\n"
        "Préfixe de phrase\n"
        "Sélectionnez votre langue\n"
        "Le diabete cause 1,5 million de deces chaque annee."
    )

    cleaned = FrenchMedicalCleaner().clean(text)

    assert "Ouvrir le calendrier" not in cleaned
    assert "Rechercher:" not in cleaned
    assert "Tous les mots" not in cleaned
    assert "N'importe quel mot" not in cleaned
    assert "Phrase exacte" not in cleaned
    assert "Préfixe de phrase" not in cleaned
    assert "Sélectionnez votre langue" not in cleaned
    assert cleaned == "Le diabete cause 1,5 million de deces chaque annee."


def test_clean_text_is_unchanged():
    text = (
        "Le diabete de type 2 peut etre prevenu par une alimentation equilibree.\n"
        "Il touche particulierement les adultes en surpoids.\n\n"
        "Une activite physique reguliere est recommandee."
    )

    assert FrenchMedicalCleaner().clean(text) == text


def test_empty_string_returns_empty_string():
    assert FrenchMedicalCleaner().clean("") == ""


def test_custom_web_noise_phrases_replace_the_default_list():
    text = "Recherche\nMenu principal\nContenu utile a propos du vaccin."

    cleaner = FrenchMedicalCleaner(web_noise_phrases=["Menu principal"])
    cleaned = cleaner.clean(text)

    assert "Recherche" in cleaned
    assert "Menu principal" not in cleaned
    assert "Contenu utile a propos du vaccin." in cleaned
