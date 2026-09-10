"""Testit PDF-sivun palan rajaamiselle PNG:ksi.

Tämä on tarkistustyökalu eikä tuotantoketjun osa, mutta juuri siksi sen pitää
toimia: se on se viimeinen vaihe, jossa korjaus katsotaan valmiilta sivulta.
Ilman testiä sen rikkoutuminen huomataan vasta kun kuvaa tarvitsee.
"""
import os
import struct
import subprocess
import unittest

import rajaa

PDF = os.path.join("stemmat", "stemma-basso-1.pdf")


def on_mutool():
    try:
        subprocess.run(["mutool", "-v"], capture_output=True)
        return True
    except FileNotFoundError:
        return False


class PpmLukija(unittest.TestCase):
    def test_otsikko_puretaan_valimerkeista_riippumatta(self):
        data = b"P6\n3 2\n255\n" + b"\x01\x02\x03" * 6
        self.assertEqual(rajaa.lue_ppm(data), (3, 2, b"\x01\x02\x03" * 6))

    def test_muu_kuin_p6_kaataa(self):
        with self.assertRaises(AssertionError):
            rajaa.lue_ppm(b"P5\n3 2\n255\n" + b"\x01" * 6)

    def test_muu_kuin_kahdeksanbittinen_kaataa(self):
        with self.assertRaises(AssertionError):
            rajaa.lue_ppm(b"P6\n3 2\n65535\n")


class PngKirjoitin(unittest.TestCase):
    def test_tulos_on_kelvollinen_png(self):
        data = rajaa.png(2, 1, [b"\x00" + b"\xff\x00\x00" * 2])
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        # IHDR: pituus, tunnus, leveys, korkeus, bittisyvyys, väritila
        self.assertEqual(data[12:16], b"IHDR")
        leveys, korkeus, syvyys, tila = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((leveys, korkeus, syvyys, tila), (2, 1, 8, 2))
        # IEND on 12 tavua: pituus, tunnus, tyhjä sisältö, CRC.
        self.assertEqual(data[-8:-4], b"IEND")

    def test_jokaisen_lohkon_crc_taysmaa(self):
        import zlib
        data = rajaa.png(2, 1, [b"\x00" + b"\xff\x00\x00" * 2])
        i = 8
        lohkot = []
        while i < len(data):
            pituus = struct.unpack(">I", data[i:i + 4])[0]
            tunnus = data[i + 4:i + 8]
            sisalto = data[i + 8:i + 8 + pituus]
            crc = struct.unpack(">I", data[i + 8 + pituus:i + 12 + pituus])[0]
            self.assertEqual(crc, zlib.crc32(tunnus + sisalto), tunnus)
            lohkot.append(tunnus)
            i += 12 + pituus
        self.assertEqual(lohkot, [b"IHDR", b"IDAT", b"IEND"])


@unittest.skipUnless(on_mutool() and os.path.exists(PDF),
                     "vaatii mutoolin ja rakennetun stemman")
class OikeaSivu(unittest.TestCase):
    def test_rajaus_skaalautuu_dpi_n_mukaan(self):
        ulos = os.path.join(os.environ.get("TMPDIR", "/tmp"), "rajaa-koe.png")
        # 72 pisteen levyinen pala on 72 dpi:llä 72 pikseliä ja 144:llä 144.
        self.assertEqual(rajaa.rajaa(PDF, 1, 100, 100, 172, 172, ulos, dpi=72),
                         (72, 72))
        self.assertEqual(rajaa.rajaa(PDF, 1, 100, 100, 172, 172, ulos, dpi=144),
                         (144, 144))
        os.remove(ulos)

    def test_tyhja_rajaus_kaataa(self):
        ulos = os.path.join(os.environ.get("TMPDIR", "/tmp"), "rajaa-koe2.png")
        with self.assertRaises(AssertionError):
            rajaa.rajaa(PDF, 1, 100, 100, 100, 172, ulos, dpi=72)


if __name__ == "__main__":
    unittest.main()
