"""Rakenna stemmat-sisallys.txt: kummalla sivulla kukin osa alkaa kussakin
kahdeksassa stemma-PDF:ssä. Sivu löytyy etsimällä osan otsikkoteksti
("V  Agnus Dei") PDF:n tekstisisällöstä sivu kerrallaan.

Sama tieto kirjoitetaan myös **stemmaan itseensä**: klikattava
sisällysluettelo sivun 1 tyhjään tilaan ja PDF:n kirjanmerkit. Sen tekee
`linkit.py`; tämä skripti on se, joka tietää mistä sivulta mikä osa alkaa,
joten se myös ajaa sen. `--ei-linkkeja` jättää PDF:t koskematta.

Järjestys on pakollinen: luettelo sisältää kaikkien osien nimet sivulla 1,
joten `etsi` löytäisi seuraavalla ajolla joka osan sivulta 1. Siksi vanha
luettelo riisutaan ennen kuin sivujen teksti luetaan — `linkit.riisu`
tunnistaa omat lisäyksensä merkinnästä eikä paikasta.
"""
import re, subprocess, sys

import linkit
import polut
from yhdista import MOVEMENTS

ULOS = 'stemmat-sisallys.txt'

STEMMAT = [("S I", "stemma-sopraano-1.pdf"), ("S II", "stemma-sopraano-2.pdf"),
           ("A I", "stemma-altto-1.pdf"),    ("A II", "stemma-altto-2.pdf"),
           ("T I", "stemma-tenori-1.pdf"),   ("T II", "stemma-tenori-2.pdf"),
           ("B I", "stemma-basso-1.pdf"),    ("B II", "stemma-basso-2.pdf")]


def sivujen_teksti(pdf):
    pdf = polut.polku(pdf)
    n = int(re.search(r'Pages: (\d+)',
            subprocess.run(['mutool', 'info', pdf], capture_output=True,
                           text=True).stdout).group(1))
    sivut = []
    for s in range(1, n + 1):
        t = subprocess.run(['mutool', 'draw', '-F', 'txt', '-o', '-', pdf, str(s)],
                           capture_output=True, text=True).stdout
        # otsikot ovat sanoja, mutta poiminta sekoittaa järjestyksen;
        # riittää että osan nimen sanat esiintyvät samalla sivulla
        sivut.append(re.sub(r'\s+', ' ', t))
    return sivut


def etsi(sivut, nimi):
    sanat = [w for w in re.split(r'[^\w·]+', nimi, flags=re.UNICODE) if w]
    for i, t in enumerate(sivut, start=1):
        if all(re.search(r'\b' + re.escape(w) + r'\b', t) for w in sanat):
            return i
    return None


def kohdat(sivut):
    """[(numero, nimi, alkusivu)]; sivu on None jos otsikkoa ei löytynyt."""
    return [(num, nimi, etsi(sivut, nimi)) for _t, num, nimi in MOVEMENTS]


def lisaa_yhteen(pdf):
    """Kirjoita yhden stemman sisällysluettelo ja kirjanmerkit."""
    linkit.riisu(pdf)
    return linkit.lisaa(pdf, kohdat(sivujen_teksti(pdf)), riisuttu=True)


def main(argv=()):
    linkita = '--ei-linkkeja' not in argv
    kaikki = {}
    for lyh, pdf in STEMMAT:
        if linkita:
            linkit.riisu(pdf)          # ennen lukemista, ks. moduulin ohje
        sivut = sivujen_teksti(pdf)
        kaikki[lyh] = (kohdat(sivut), len(sivut))
        print(f'  luettu {pdf} ({len(sivut)} sivua)', file=sys.stderr)
        if linkita:
            linkit.lisaa(pdf, kaikki[lyh][0], riisuttu=True)

    rivit = ['SISÄLLYS - Verdi: Messa da Requiem, kuorostemmat',
             'sivunumerot kussakin stemma-PDF:ssä',
             '=' * 83,
             ' ' * 7 + 'osa'.ljust(20) + ''.join(f'{l:>7}' for l, _ in STEMMAT),
             '-' * 83]
    for i, (_, num, nimi) in enumerate(MOVEMENTS):
        solut = ''
        for lyh, _ in STEMMAT:
            s = kaikki[lyh][0][i][2]
            solut += f'{s if s else "?":>7}'
        rivit.append(f'  {num:<5}{nimi:<20}{solut}')
    rivit += ['-' * 83,
              ' ' * 7 + 'sivuja'.ljust(20) + ''.join(f'{kaikki[l][1]:>7}' for l, _ in STEMMAT),
              '']
    out = '\n'.join(rivit)
    open(polut.polku(ULOS), 'w').write(out)
    print(out)


if __name__ == '__main__':
    main(sys.argv[1:])
