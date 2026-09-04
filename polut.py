#!/usr/bin/env python3
"""Mistä hakemistosta mikäkin nuottitiedosto löytyy.

Tiedostonimi kertoo sen itse. Projektin nimeämiskäytäntö on ollut sama
alusta asti: johdetut tiedostot päättyvät -kasin.mxl tai -OMR-korjattu.mxl,
stemmat alkavat sanalla stemma, ja kaikki muu on lähdeaineistoa. Kun
hakemisto luetaan nimestä, skriptien taulukot (MOVEMENTS, MAPPING,
korjaa_kasin.py:n Osa-rivit) säilyvät luettavina paljaine tiedostonimineen
eikä hakemistoa tarvitse toistaa yli sadassa kohdassa.

Tämä koskee vain nuottiaineistoa. Työkalutiedostoilla kuten tiivistys.mss
on omat vakionsa eikä niitä reititetä tämän kautta.
"""

import os

LAHTEET = "lahteet"
JOHDETUT = "johdetut"
STEMMAT = "stemmat"
HARJOITUS = "harjoitus"

# Johdetun tiedoston tunnistaa päätteestä tai alkuosasta.
JOHDETUN_PAATTEET = ("-kasin.mxl", "-OMR-korjattu.mxl")
KOKO_PARTITUURI = "Verdi-Requiem-koko"


def hakemisto(nimi):
    """Hakemisto, johon paljas tiedostonimi kuuluu."""
    if nimi.endswith(JOHDETUN_PAATTEET) or nimi.startswith(KOKO_PARTITUURI):
        return JOHDETUT
    if nimi.startswith("stemma"):
        return STEMMAT
    if nimi.startswith("harjoitus-"):
        return HARJOITUS
    return LAHTEET


def polku(nimi):
    """Täysi polku nuottitiedostolle.

    Jos nimessä on jo hakemisto, se palautetaan sellaisenaan — komentoriviltä
    pitää voida antaa mikä tahansa tiedosto mistä tahansa.
    """
    if os.sep in nimi or (os.altsep and os.altsep in nimi):
        return nimi
    return os.path.join(hakemisto(nimi), nimi)
