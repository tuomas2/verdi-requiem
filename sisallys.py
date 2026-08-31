"""Rakenna stemmat-sisallys.txt: kummalla sivulla kukin osa alkaa kussakin
kahdeksassa stemma-PDF:ssä. Sivu löytyy etsimällä osan otsikkoteksti
("V  Agnus Dei") PDF:n tekstisisällöstä sivu kerrallaan."""
import re, subprocess, sys

from yhdista import MOVEMENTS

ULOS = 'stemmat-sisallys.txt'

STEMMAT = [("S I", "stemma-sopraano-1.pdf"), ("S II", "stemma-sopraano-2.pdf"),
           ("A I", "stemma-altto-1.pdf"),    ("A II", "stemma-altto-2.pdf"),
           ("T I", "stemma-tenori-1.pdf"),   ("T II", "stemma-tenori-2.pdf"),
           ("B I", "stemma-basso-1.pdf"),    ("B II", "stemma-basso-2.pdf")]


def sivujen_teksti(pdf):
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


def main():
    kaikki = {}
    for lyh, pdf in STEMMAT:
        sivut = sivujen_teksti(pdf)
        kaikki[lyh] = (sivut, len(sivut))
        print(f'  luettu {pdf} ({len(sivut)} sivua)', file=sys.stderr)

    rivit = ['SISÄLLYS - Verdi: Messa da Requiem, kuorostemmat',
             'sivunumerot kussakin stemma-PDF:ssä',
             '=' * 83,
             ' ' * 7 + 'osa'.ljust(20) + ''.join(f'{l:>7}' for l, _ in STEMMAT),
             '-' * 83]
    for _, num, nimi in MOVEMENTS:
        solut = ''
        for lyh, _ in STEMMAT:
            sivut, _n = kaikki[lyh]
            s = etsi(sivut, nimi)
            solut += f'{s if s else "?":>7}'
        rivit.append(f'  {num:<5}{nimi:<20}{solut}')
    rivit += ['-' * 83,
              ' ' * 7 + 'sivuja'.ljust(20) + ''.join(f'{kaikki[l][1]:>7}' for l, _ in STEMMAT),
              '']
    out = '\n'.join(rivit)
    open(ULOS, 'w').write(out)
    print(out)


if __name__ == '__main__':
    main()
