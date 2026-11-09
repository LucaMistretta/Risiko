"""
Estrae i 42 territori da risiko.jpg tramite componenti connesse colorate.
Genera PNG, SVG (XML) con path vettoriali e manifest in territori/.
"""

from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

CARTELLA_PROGETTO = Path(__file__).resolve().parent
IMMAGINE_ORIGINALE = CARTELLA_PROGETTO / "risiko.jpg"
CARTELLA_TERRITORI = CARTELLA_PROGETTO / "territori"
MANIFEST = CARTELLA_TERRITORI / "manifest.json"
MAPPA_SVG = CARTELLA_TERRITORI / "mappa.svg"

SOGLIA_AREA_CONTORNO = 40
SEMPLIFICAZIONE_CONTORNO = 1.6
SPESSORE_BORDO_SVG = 1.4
COLORE_BORDO_SVG = "#1a1a1a"
COLORE_SFONDO_SVG = "#efe3c8"

COORDINATE_TERRITORI = {
    "Alaska": {"top": 5.8927294398092975, "left": 5.662866449511402, "width": 9, "height": 8},
    "Territori del Nord-Ovest": {"top": 7.799761620977355, "left": 15.760586319218241, "width": 11, "height": 8},
    "Groenlandia": {"top": 5.799761620977355, "left": 26.83387622149837, "width": 12, "height": 12},
    "Alberta": {"top": 17.64600715137068, "left": 10.136807817589577, "width": 8, "height": 10},
    "Ontario": {"top": 19, "left": 18, "width": 8, "height": 14},
    "Quebec": {"top": 27.30035756853397, "left": 26.509771986970687, "width": 8, "height": 16},
    "Stati Uniti Orientali": {"top": 36.908224076281286, "left": 15.260586319218241, "width": 10, "height": 12},
    "Stati Uniti Occidentali": {"top": 32, "left": 6, "width": 9, "height": 12},
    "America Centrale": {"top": 48.84743742550656, "left": 6.684039087947884, "width": 8, "height": 6},
    "Venezuela": {"top": 58.81287246722288, "left": 9.745928338762214, "width": 8, "height": 8},
    "Brasile": {"top": 66.34803337306317, "left": 17.061889250814332, "width": 8, "height": 12},
    "Perù": {"top": 68.06912991656733, "left": 7.009771986970684, "width": 8, "height": 10},
    "Argentina": {"top": 86.17997616209773, "left": 8.985342019543975, "width": 9, "height": 10},
    "Islanda": {"top": 9.395709177592371, "left": 40.25732899022801, "width": 6, "height": 6},
    "Gran Bretagna": {"top": 26.058998808104885, "left": 37.02117263843648, "width": 7, "height": 7},
    "Europa Settentrionale": {"top": 31.63766388557807, "left": 43.100977198697066, "width": 8, "height": 8},
    "Europa Meridionale": {"top": 44.86769964243147, "left": 44.013029315960914, "width": 8, "height": 8},
    "Ucraina": {"top": 24.97497020262217, "left": 52.700325732899024, "width": 7, "height": 23},
    "Europa Occidentale": {"top": 42.12634088200238, "left": 34.08957654723127, "width": 7, "height": 8},
    "Scandinavia": {"top": 16.69249106078665, "left": 44.16449511400652, "width": 9, "height": 10},
    "Egitto": {"top": 58.030989272943984, "left": 49.48534201954397, "width": 8, "height": 8},
    "Africa Settentrionale": {"top": 58.883194278903, "left": 33.47882736156352, "width": 12, "height": 10},
    "Congo": {"top": 72.52562574493444, "left": 43.361563517915314, "width": 8, "height": 10},
    "Africa Orientale": {"top": 70.56615017878427, "left": 52.568403908794785, "width": 9, "height": 10},
    "Africa Meridionale": {"top": 85.27890345649584, "left": 44.81596091205211, "width": 9, "height": 10},
    "Madagascar": {"top": 83.06078665077473, "left": 54.5, "width": 7, "height": 8},
    "Siberia": {"top": 11.924910607866508, "left": 58.90879478827362, "width": 10, "height": 10},
    "Irkutsk": {"top": 16.954112038140643, "left": 69.22475570032573, "width": 8, "height": 9},
    "Yakutsk": {"top": 1.5786650774731825, "left": 66.90065146579805, "width": 9, "height": 9},
    "Kamchatka": {"top": 2.2938021454112043, "left": 76.52117263843648, "width": 8, "height": 9},
    "Mongolia": {"top": 26.608462455303933, "left": 74.58794788273616, "width": 9, "height": 9},
    "Cina": {"top": 37.00119189511323, "left": 72.63192182410424, "width": 12, "height": 12},
    "Giappone": {"top": 22, "left": 87, "width": 6, "height": 7},
    "Medio Oriente": {"top": 51.9958283671037, "left": 58.30130293159609, "width": 9, "height": 9},
    "India": {"top": 57.216924910607865, "left": 68.4641693811075, "width": 9, "height": 10},
    "Siam": {"top": 53.92610250297974, "left": 77.04234527687296, "width": 8, "height": 8},
    "Urali": {"top": 21.93682955899881, "left": 59.32247557003258, "width": 8, "height": 10},
    "Afghanistan": {"top": 35.9284862932062, "left": 60.82084690553745, "width": 8, "height": 8},
    "Australia Orientale": {"top": 87.9678188319428, "left": 87.74755700325733, "width": 9, "height": 10},
    "Indonesia": {"top": 68.34803337306317, "left": 81.53745928338762, "width": 8, "height": 8},
    "Nuova Guinea": {"top": 74.42669845053635, "left": 89.98534201954396, "width": 7, "height": 8},
    "Australia Occidentale": {"top": 81.7699642431466, "left": 77.19381107491857, "width": 9, "height": 10},
}

TERRITORI_MULTI_ISOLA = {"Indonesia", "Giappone", "Gran Bretagna", "Kamchatka"}

# Componenti connesse aggiuntive (stesso territorio, blob separati dalla segmentazione)
COMPONENTI_EXTRA: dict[str, list[int]] = {
    "Alberta": [425, 1149],
}

# Componenti da escludere se assegnate erroneamente a un vicino
RIMUOVI_COMPONENTI: dict[str, list[int]] = {
    "Territori del Nord-Ovest": [425],
}

# Semi manuali per territori piccoli o ambigui (x, y, tolleranza)
SEMI_MANUALI: dict[str, list[tuple[int, int, int]]] = {
    # Semi solo sul corpo dell'isola, non sul lobo settentrionale spurio
    "Islanda": [(880, 200, 10), (865, 210, 8)],
    "America Centrale": [(145, 707, 10), (169, 719, 10)],
    "Yakutsk": [(1474, 126, 10), (1462, 126, 10)],
}

SOGLIA_PIXEL_MINIMA_QUALITA = 5000
TERRITORI_PICCOLI_AMMESSI = {"Islanda", "Madagascar", "Giappone"}

SOGLIA_BORDO = 42
SOGLIA_SATURAZIONE = 25
MAX_PERCENTUALE_COMPONENTE = 0.06
MIN_PIXEL_RETTANGOLO = 150
MIN_PIXEL_TERRITORIO = 400
MIN_PIXEL_ISOLA = 120


def nome_file_sicuro(nome_territorio: str) -> str:
    testo = unicodedata.normalize("NFKD", nome_territorio)
    testo = testo.encode("ascii", "ignore").decode("ascii")
    testo = testo.lower()
    testo = re.sub(r"[^a-z0-9]+", "-", testo).strip("-")
    return testo or "territorio"


def rettangolo_pixel(coordinate: dict, larghezza: int, altezza: int) -> tuple[int, int, int, int]:
    x1 = int(coordinate["left"] / 100 * larghezza)
    y1 = int(coordinate["top"] / 100 * altezza)
    x2 = int((coordinate["left"] + coordinate["width"]) / 100 * larghezza)
    y2 = int((coordinate["top"] + coordinate["height"]) / 100 * altezza)
    return max(0, x1), max(0, y1), min(larghezza, x2), min(altezza, y2)


def prepara_componenti(immagine_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    grigio = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2HSV)
    maschera_bordi = grigio < SOGLIA_BORDO

    candidati = (
        (hsv[:, :, 1] > SOGLIA_SATURAZIONE)
        & (hsv[:, :, 2] > 35)
        & (hsv[:, :, 2] < 252)
        & (~maschera_bordi)
    )

    _, etichette = cv2.connectedComponents(candidati.astype(np.uint8))
    dimensioni = np.bincount(etichette.ravel())
    massimo_componente = int(immagine_bgr.shape[0] * immagine_bgr.shape[1] * MAX_PERCENTUALE_COMPONENTE)
    return maschera_bordi, etichette, dimensioni, massimo_componente


def candidati_nel_rettangolo(
    etichette: np.ndarray,
    dimensioni: np.ndarray,
    rettangolo: tuple[int, int, int, int],
    massimo_componente: int,
    minimo_pixel: int,
) -> list[tuple[int, int]]:
    x1, y1, x2, y2 = rettangolo
    regione = etichette[y1:y2, x1:x2]
    valori_unici, conteggi = np.unique(regione, return_counts=True)

    candidati: list[tuple[int, int]] = []
    for etichetta, conteggio in zip(valori_unici, conteggi):
        if etichetta == 0:
            continue
        if dimensioni[etichetta] > massimo_componente:
            continue
        if conteggio < minimo_pixel:
            continue
        candidati.append((int(etichetta), int(conteggio)))

    candidati.sort(key=lambda elemento: elemento[1], reverse=True)
    return candidati


def assegna_componenti_ai_territori(
    etichette: np.ndarray,
    dimensioni: np.ndarray,
    massimo_componente: int,
    larghezza: int,
    altezza: int,
) -> dict[str, list[int]]:
    rivendicazioni: list[tuple[str, int, float]] = []

    for nome_territorio, coordinate in COORDINATE_TERRITORI.items():
        rettangolo = rettangolo_pixel(coordinate, larghezza, altezza)
        minimo = MIN_PIXEL_ISOLA if nome_territorio in TERRITORI_MULTI_ISOLA else MIN_PIXEL_RETTANGOLO
        candidati = candidati_nel_rettangolo(etichette, dimensioni, rettangolo, massimo_componente, minimo)
        limite = 8 if nome_territorio in TERRITORI_MULTI_ISOLA else 3

        for etichetta, conteggio in candidati[:limite]:
            rapporto = conteggio / dimensioni[etichetta]
            rivendicazioni.append((nome_territorio, etichetta, rapporto))

    rivendicazioni.sort(key=lambda elemento: elemento[2], reverse=True)

    etichette_assegnate: set[int] = set()
    assegnazioni: dict[str, list[int]] = {nome: [] for nome in COORDINATE_TERRITORI}

    for nome_territorio, etichetta, _ in rivendicazioni:
        if etichetta in etichette_assegnate:
            continue
        etichette_assegnate.add(etichetta)
        assegnazioni[nome_territorio].append(etichetta)

    return assegnazioni


def crea_maschera_pergamena(immagine_bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2HSV)
    saturazione = hsv[:, :, 1]
    valore = hsv[:, :, 2]
    blu, verde, rosso = cv2.split(immagine_bgr)
    pergamena_chiara = (saturazione < 28) & (valore > 175)
    quasi_bianco = (
        (rosso > 210)
        & (verde > 195)
        & (blu > 165)
        & (saturazione < SOGLIA_SATURAZIONE)
    )
    return pergamena_chiara | quasi_bianco


def pulisci_maschera_territorio(
    immagine_bgr: np.ndarray,
    maschera: np.ndarray,
    maschera_bordi: np.ndarray,
    maschera_pergamena: np.ndarray,
) -> np.ndarray:
    """Rimuove bordi neri, pergamena e pixel quasi bianchi dalla maschera."""
    hsv = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2HSV)
    saturazione = hsv[:, :, 1]
    return (
        maschera
        & (~maschera_bordi)
        & (~maschera_pergamena)
        & (saturazione > SOGLIA_SATURAZIONE)
    )


def mantieni_componente_massima(maschera: np.ndarray) -> np.ndarray:
    """Mantiene solo la componente connessa più grande della maschera."""
    numero, etichette = cv2.connectedComponents(maschera.astype(np.uint8))
    if numero <= 1:
        return maschera
    indice_massimo = max(
        range(1, numero),
        key=lambda indice: int((etichette == indice).sum()),
    )
    return etichette == indice_massimo


def rifinisci_maschera_territorio(
    maschera: np.ndarray,
    nome_territorio: str,
) -> np.ndarray:
    """Correzioni manuali per artefatti noti su singoli territori."""
    altezza, larghezza = maschera.shape
    maschera_rifinita = maschera.copy()

    if nome_territorio == "Islanda":
        # Rimuove il lobo settentrionale spurio (pergamena con solo bordo nero)
        maschera_rifinita[:168, :] = False
        maschera_rifinita = mantieni_componente_massima(maschera_rifinita)

    if nome_territorio == "Groenlandia":
        # Rimuove la punta meridionale che invade lo spazio sopra l'Islanda
        griglia_y = np.arange(altezza)[:, None]
        griglia_x = np.arange(larghezza)[None, :]
        zona_spur = (griglia_y >= 115) & (griglia_y < 175) & (griglia_x > 800)
        maschera_rifinita &= ~zona_spur

    if nome_territorio == "Europa Meridionale":
        # Rimuove l'isola orientale (Cipro) e lo spur marino tra Grecia ed Egitto
        griglia_y = np.arange(altezza)[:, None]
        griglia_x = np.arange(larghezza)[None, :]
        zona_spur = (griglia_y >= 770) & (griglia_x >= 1048)
        maschera_rifinita &= ~zona_spur

    return maschera_rifinita


def genera_griglia_semi(rettangolo: tuple[int, int, int, int], passo: int = 10) -> list[tuple[int, int]]:
    x1, y1, x2, y2 = rettangolo
    semi = []
    for y in range(y1 + passo // 2, y2, passo):
        for x in range(x1 + passo // 2, x2, passo):
            semi.append((x, y))
    semi.insert(0, ((x1 + x2) // 2, (y1 + y2) // 2))
    return semi


def flood_fill_da_seme(
    immagine_bgr: np.ndarray,
    maschera_bordi: np.ndarray,
    seme: tuple[int, int],
    tolleranza: int = 12,
) -> np.ndarray:
    altezza, larghezza = immagine_bgr.shape[:2]
    maschera = np.zeros((altezza + 2, larghezza + 2), dtype=np.uint8)
    copia = immagine_bgr.copy()
    differenza = (tolleranza, tolleranza, tolleranza)
    flag = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
    cv2.floodFill(copia, maschera, seme, (0, 0, 0), differenza, differenza, flag)
    return (maschera[1:-1, 1:-1] > 0) & (~maschera_bordi)


def maschera_con_flood_fill(
    immagine_bgr: np.ndarray,
    maschera_bordi: np.ndarray,
    maschera_pergamena: np.ndarray,
    rettangolo: tuple[int, int, int, int],
    maschera_esclusa: np.ndarray,
    massimo_pixel: int,
    nome_territorio: str = "",
) -> np.ndarray | None:
    hsv = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2HSV)
    miglior_maschera = None
    miglior_conteggio = float("inf") if nome_territorio not in SEMI_MANUALI else 0
    ignora_esclusione = nome_territorio in SEMI_MANUALI
    preferisci_maggiore = nome_territorio in SEMI_MANUALI

    semi_da_provare: list[tuple[tuple[int, int], int | None]] = []

    for x, y, tolleranza in SEMI_MANUALI.get(nome_territorio, []):
        semi_da_provare.append(((x, y), tolleranza))

    if not preferisci_maggiore:
        for seme in genera_griglia_semi(rettangolo):
            semi_da_provare.append((seme, None))

    for seme, tolleranza_fissa in semi_da_provare:
        x, y = seme
        if maschera_bordi[y, x] or maschera_pergamena[y, x]:
            continue
        if hsv[y, x, 1] < 20 and nome_territorio not in SEMI_MANUALI:
            continue

        tolleranze = (tolleranza_fissa,) if tolleranza_fissa else (10, 14, 18)
        for tolleranza in tolleranze:
            maschera = flood_fill_da_seme(immagine_bgr, maschera_bordi, seme, tolleranza)
            if not ignora_esclusione:
                maschera &= ~maschera_esclusa
            maschera = pulisci_maschera_territorio(
                immagine_bgr, maschera, maschera_bordi, maschera_pergamena
            )
            conteggio = int(maschera.sum())
            if not (MIN_PIXEL_TERRITORIO <= conteggio <= massimo_pixel):
                continue
            if preferisci_maggiore and conteggio > miglior_conteggio:
                miglior_maschera = maschera
                miglior_conteggio = conteggio
            elif not preferisci_maggiore and conteggio < miglior_conteggio:
                miglior_maschera = maschera
                miglior_conteggio = conteggio

    return miglior_maschera


def costruisci_maschera(etichette: np.ndarray, etichette_assegnate: list[int]) -> np.ndarray:
    maschera = np.zeros(etichette.shape, dtype=bool)
    for etichetta in etichette_assegnate:
        if isinstance(etichetta, int):
            maschera |= etichette == etichetta
    return maschera


def etichette_effettive_territorio(nome_territorio: str, etichette_assegnate: list) -> list[int]:
    """Unisce assegnazione automatica, componenti extra e rimozioni manuali."""
    etichette_valide: list[int] = []
    for etichetta in etichette_assegnate:
        if isinstance(etichetta, int):
            etichette_valide.append(etichetta)

    etichette_valide = [
        etichetta
        for etichetta in etichette_valide
        if etichetta not in RIMUOVI_COMPONENTI.get(nome_territorio, [])
    ]

    for etichetta in COMPONENTI_EXTRA.get(nome_territorio, []):
        if etichetta not in etichette_valide:
            etichette_valide.append(etichetta)

    return etichette_valide


def rgb_a_hex(rosso: int, verde: int, blu: int) -> str:
    return f"#{rosso:02x}{verde:02x}{blu:02x}"


def calcola_colore_mediano(immagine_bgr: np.ndarray, maschera: np.ndarray) -> str:
    pixel = immagine_bgr[maschera]
    if len(pixel) == 0:
        return "#cccccc"
    mediana = np.median(pixel, axis=0).astype(int)
    blu, verde, rosso = mediana
    return rgb_a_hex(int(rosso), int(verde), int(blu))


def maschera_a_path_svg(maschera: np.ndarray, offset_x: int = 0, offset_y: int = 0) -> str:
    maschera_uint8 = maschera.astype(np.uint8) * 255
    contorni, _ = cv2.findContours(maschera_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    segmenti: list[str] = []

    for contorno in contorni:
        if cv2.contourArea(contorno) < SOGLIA_AREA_CONTORNO:
            continue
        approssimato = cv2.approxPolyDP(contorno, SEMPLIFICAZIONE_CONTORNO, True)
        punti = approssimato.reshape(-1, 2)
        if len(punti) < 3:
            continue

        primo_x = int(punti[0][0] - offset_x)
        primo_y = int(punti[0][1] - offset_y)
        comando = f"M {primo_x},{primo_y}"
        for x, y in punti[1:]:
            comando += f" L {int(x - offset_x)},{int(y - offset_y)}"
        comando += " Z"
        segmenti.append(comando)

    return " ".join(segmenti)


def calcola_centroide(maschera: np.ndarray) -> tuple[int, int]:
    coordinate_y, coordinate_x = np.where(maschera)
    if len(coordinate_x) == 0:
        return 0, 0
    return int(coordinate_x.mean()), int(coordinate_y.mean())


def crea_elemento_path_svg(
    identificativo: str,
    nome_territorio: str,
    comando_path: str,
    colore_riempimento: str,
    centro_x: int,
    centro_y: int,
) -> ElementTree.Element:
    elemento = ElementTree.Element(
        "path",
        {
            "id": identificativo,
            "class": "territorio",
            "data-nome": nome_territorio,
            "data-colore-originale": colore_riempimento,
            "fill": colore_riempimento,
            "stroke": COLORE_BORDO_SVG,
            "stroke-width": str(SPESSORE_BORDO_SVG),
            "stroke-linejoin": "round",
            "stroke-linecap": "round",
            "d": comando_path,
        },
    )
    elemento.set("data-centro-x", str(centro_x))
    elemento.set("data-centro-y", str(centro_y))
    return elemento


def salva_svg_su_file(radice: ElementTree.Element, percorso: Path) -> None:
    albero = ElementTree.ElementTree(radice)
    ElementTree.indent(albero, space="  ")
    albero.write(percorso, encoding="utf-8", xml_declaration=True)


def genera_svg_territorio(
    immagine_bgr: np.ndarray,
    maschera_pulita: np.ndarray,
    nome_territorio: str,
    nome_file: str,
    x_min: int,
    y_min: int,
    larghezza_ritaglio: int,
    altezza_ritaglio: int,
) -> dict:
    colore_originale = calcola_colore_mediano(immagine_bgr, maschera_pulita)
    comando_globale = maschera_a_path_svg(maschera_pulita)
    centro_x, centro_y = calcola_centroide(maschera_pulita)

    maschera_ritaglio = maschera_pulita[y_min : y_min + altezza_ritaglio, x_min : x_min + larghezza_ritaglio]
    comando_locale = maschera_a_path_svg(maschera_ritaglio)

    identificativo = nome_file
    elemento_path = crea_elemento_path_svg(
        identificativo,
        nome_territorio,
        comando_locale,
        colore_originale,
        centro_x - x_min,
        centro_y - y_min,
    )

    radice = ElementTree.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {larghezza_ritaglio} {altezza_ritaglio}",
            "width": str(larghezza_ritaglio),
            "height": str(altezza_ritaglio),
        },
    )
    radice.append(elemento_path)
    salva_svg_su_file(radice, CARTELLA_TERRITORI / f"{nome_file}.svg")

    return {
        "idSvg": identificativo,
        "fileSvg": f"{nome_file}.svg",
        "coloreOriginale": colore_originale,
        "pathD": comando_globale,
        "centroX": centro_x,
        "centroY": centro_y,
    }


def genera_mappa_svg_completa(territori_dati: list[dict], larghezza: int, altezza: int) -> None:
    radice = ElementTree.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {larghezza} {altezza}",
            "width": str(larghezza),
            "height": str(altezza),
        },
    )

    stile = ElementTree.Element(
        "style",
        {},
    )
    stile.text = """
      .territorio {
        cursor: pointer;
        transition: fill 0.2s ease, filter 0.15s ease;
      }
      .territorio:hover {
        filter: brightness(1.12);
      }
    """
    radice.append(stile)

    sfondo = ElementTree.Element(
        "rect",
        {
            "id": "sfondo-pergamena",
            "x": "0",
            "y": "0",
            "width": str(larghezza),
            "height": str(altezza),
            "fill": COLORE_SFONDO_SVG,
        },
    )
    radice.append(sfondo)

    gruppo = ElementTree.Element("g", {"id": "territori"})
    for dati in sorted(territori_dati, key=lambda elemento: elemento["nome"]):
        elemento = crea_elemento_path_svg(
            dati["idSvg"],
            dati["nome"],
            dati["pathD"],
            dati["coloreOriginale"],
            dati["centroX"],
            dati["centroY"],
        )
        gruppo.append(elemento)

    radice.append(gruppo)
    salva_svg_su_file(radice, MAPPA_SVG)


def estrai_e_salva(
    immagine_bgr: np.ndarray,
    maschera_territorio: np.ndarray,
    maschera_bordi: np.ndarray,
    maschera_pergamena: np.ndarray,
    nome_territorio: str,
    nome_file: str,
) -> tuple[dict | None, np.ndarray | None]:
    maschera_pulita = pulisci_maschera_territorio(
        immagine_bgr, maschera_territorio, maschera_bordi, maschera_pergamena
    )
    if int(maschera_pulita.sum()) < MIN_PIXEL_TERRITORIO:
        return None, None

    coordinate = np.argwhere(maschera_pulita)
    y_min, x_min = coordinate.min(axis=0)
    y_max, x_max = coordinate.max(axis=0)
    larghezza_ritaglio = int(x_max - x_min + 1)
    altezza_ritaglio = int(y_max - y_min + 1)

    altezza, larghezza = immagine_bgr.shape[:2]
    rgba = np.zeros((altezza, larghezza, 4), dtype=np.uint8)
    rgba[:, :, :3] = cv2.cvtColor(immagine_bgr, cv2.COLOR_BGR2RGB)
    rgba[:, :, 3] = np.where(maschera_pulita, 255, 0).astype(np.uint8)

    ritaglio = rgba[y_min : y_max + 1, x_min : x_max + 1]
    percorso = CARTELLA_TERRITORI / f"{nome_file}.png"
    Image.fromarray(ritaglio).save(percorso, optimize=True)

    metadati = {
        "nome": nome_territorio,
        "file": f"{nome_file}.png",
        "x": int(x_min),
        "y": int(y_min),
        "larghezza": larghezza_ritaglio,
        "altezza": altezza_ritaglio,
        "pixel": int(maschera_pulita.sum()),
    }

    dati_svg = genera_svg_territorio(
        immagine_bgr,
        maschera_pulita,
        nome_territorio,
        nome_file,
        int(x_min),
        int(y_min),
        larghezza_ritaglio,
        altezza_ritaglio,
    )
    metadati.update(dati_svg)

    return metadati, maschera_pulita


def main() -> None:
    if not IMMAGINE_ORIGINALE.exists():
        raise FileNotFoundError(f"Immagine non trovata: {IMMAGINE_ORIGINALE}")

    CARTELLA_TERRITORI.mkdir(parents=True, exist_ok=True)

    immagine_bgr = cv2.imread(str(IMMAGINE_ORIGINALE))
    if immagine_bgr is None:
        raise RuntimeError("Impossibile leggere risiko.jpg")

    altezza, larghezza = immagine_bgr.shape[:2]
    maschera_bordi, etichette, dimensioni, massimo_componente = prepara_componenti(immagine_bgr)
    maschera_pergamena = crea_maschera_pergamena(immagine_bgr)
    maschera_esclusa_globale = np.zeros((altezza, larghezza), dtype=bool)
    massimo_flood = int(altezza * larghezza * 0.08)

    assegnazioni = assegna_componenti_ai_territori(etichette, dimensioni, massimo_componente, larghezza, altezza)

    manifest: dict = {
        "sorgente": "risiko.jpg",
        "larghezzaMappa": larghezza,
        "altezzaMappa": altezza,
        "territori": [],
        "errori": [],
    }

    for nome_territorio in COORDINATE_TERRITORI:
        nome_file = nome_file_sicuro(nome_territorio)
        etichette_territorio = assegnazioni.get(nome_territorio, [])

        if nome_territorio in SEMI_MANUALI:
            rettangolo = rettangolo_pixel(COORDINATE_TERRITORI[nome_territorio], larghezza, altezza)
            maschera_manuale = maschera_con_flood_fill(
                immagine_bgr,
                maschera_bordi,
                maschera_pergamena,
                rettangolo,
                maschera_esclusa_globale,
                massimo_flood,
                nome_territorio,
            )
            if maschera_manuale is not None:
                maschera = maschera_manuale
                etichette_territorio = ["manuale"]
            elif etichette_territorio:
                etichette_finale = etichette_effettive_territorio(nome_territorio, etichette_territorio)
                maschera = costruisci_maschera(etichette, etichette_finale)
            else:
                manifest["errori"].append(nome_territorio)
                print(f"  ERRORE: nessuna componente assegnata a {nome_territorio}")
                continue
        elif not etichette_territorio:
            rettangolo = rettangolo_pixel(COORDINATE_TERRITORI[nome_territorio], larghezza, altezza)
            maschera_fallback = maschera_con_flood_fill(
                immagine_bgr,
                maschera_bordi,
                maschera_pergamena,
                rettangolo,
                maschera_esclusa_globale,
                massimo_flood,
                nome_territorio,
            )
            if maschera_fallback is None:
                manifest["errori"].append(nome_territorio)
                print(f"  ERRORE: nessuna componente assegnata a {nome_territorio}")
                continue

            maschera = maschera_fallback
            etichette_territorio = ["flood-fill"]
        else:
            etichette_finale = etichette_effettive_territorio(nome_territorio, etichette_territorio)
            maschera = costruisci_maschera(etichette, etichette_finale)

        pixel_maschera = int(maschera.sum())
        if (
            nome_territorio not in TERRITORI_PICCOLI_AMMESSI
            and pixel_maschera < SOGLIA_PIXEL_MINIMA_QUALITA
        ):
            rettangolo = rettangolo_pixel(COORDINATE_TERRITORI[nome_territorio], larghezza, altezza)
            maschera_migliore = maschera_con_flood_fill(
                immagine_bgr,
                maschera_bordi,
                maschera_pergamena,
                rettangolo,
                maschera_esclusa_globale,
                massimo_flood,
                nome_territorio,
            )
            if maschera_migliore is not None and int(maschera_migliore.sum()) > pixel_maschera:
                maschera = maschera_migliore
                etichette_territorio = ["flood-fill-qualita"]

        maschera = rifinisci_maschera_territorio(maschera, nome_territorio)

        metadati, _ = estrai_e_salva(
            immagine_bgr, maschera, maschera_bordi, maschera_pergamena, nome_territorio, nome_file
        )

        if metadati is None:
            manifest["errori"].append(nome_territorio)
            print(f"  ERRORE: export fallito per {nome_territorio}")
            continue

        maschera_esclusa_globale |= maschera
        manifest["territori"].append(metadati)
        print(
            f"  OK: {nome_territorio} -> {nome_file}.png + {nome_file}.svg "
            f"({metadati['pixel']} px, {metadati['coloreOriginale']})"
        )

    manifest["territori"].sort(key=lambda elemento: elemento["nome"])
    manifest["totaleTerritori"] = len(manifest["territori"])
    manifest["formatoSvg"] = True
    manifest["mappaSvg"] = "mappa.svg"

    if manifest["territori"]:
        genera_mappa_svg_completa(manifest["territori"], larghezza, altezza)
        print(f"  Mappa SVG: {MAPPA_SVG}")

    for territorio in manifest["territori"]:
        territorio.pop("pathD", None)

    with MANIFEST.open("w", encoding="utf-8") as file_manifest:
        json.dump(manifest, file_manifest, ensure_ascii=False, indent=2)

    print(f"\nCompletato: {manifest['totaleTerritori']}/42 territori in {CARTELLA_TERRITORI}")
    if manifest["errori"]:
        print(f"Territori falliti: {', '.join(manifest['errori'])}")


if __name__ == "__main__":
    main()
