"""Testit.

Ajetaan aina repon juuresta, koska testit ja skriptit lukevat tiedostoja
suhteellisilla poluilla:

    python3 -m unittest discover -s testit -t .

`-t .` pitää juuren sys.pathissa, jotta `import yhdista` toimii, ja tämä
tiedosto tekee hakemistosta tuotavan, mitä Python 3.9:n discover vaatii.
"""
