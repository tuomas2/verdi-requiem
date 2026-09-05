#!/bin/bash
# 65-musescore — MuseScore Studio 4 komentorivikäyttöön, AppImagesta purettuna.
# Env: MUSESCORE_VERSION (valinnainen, esim. "4.7.4"; tyhjänä uusin julkaisu)
# Installs: /opt/musescore, /usr/local/bin/{mscore,musescore}
#
# Numero 65 on tarkoituksella 60-gui-libs.sh:n jälkeen: AppImage nojaa sen
# asentamiin kirjastoihin (fontconfig, libasound2t64, fontit) ja lopun
# savutesti ajaa mscoren oikeasti — se ei toimisi ennen niitä.
#
# AppImagea ei ajeta AppImagena vaan puretaan (--appimage-extract), koska
# kontissa ei ole FUSEa. Purettu puu toimii täsmälleen samoin.
set -euo pipefail

echo "==> Installing MuseScore Studio 4"

# AppImage tuo mukanaan Qt:n mutta ei GLX:ää, eikä 60-gui-libs asenna sitä:
# kuvassa on libglvnd0 ja libEGL, muttei libGLX.so.0:aa, jolloin mscore
# kaatuu heti käynnistyksessä "cannot open shared object file: libGLX.so.0".
# libopengl0 poistaa AppRunin fallback-varoituksen samalla.
DEBIAN_FRONTEND=noninteractive apt-get install -y libgl1 libopengl0

api="https://api.github.com/repos/musescore/MuseScore/releases/latest"
if [ -n "${MUSESCORE_VERSION:-}" ]; then
    api="https://api.github.com/repos/musescore/MuseScore/releases/tags/v${MUSESCORE_VERSION}"
fi

# Julkaisun liitetiedoston nimi vaihtelee versioittain (mukana on build-numero),
# joten URL luetaan julkaisusta eikä kirjoiteta tähän kovakoodattuna.
url="$(curl -fsSL "$api" | grep -o 'https://[^"]*x86_64\.AppImage' | head -1)"
if [ -z "$url" ]; then
    echo "!! MuseScoren AppImagea ei löytynyt julkaisusta: $api" >&2
    exit 1
fi
echo "    $url"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/musescore.AppImage" "$url"
chmod +x "$tmp/musescore.AppImage"
( cd "$tmp" && ./musescore.AppImage --appimage-extract >/dev/null )

rm -rf /opt/musescore
mv "$tmp/squashfs-root" /opt/musescore
chmod -R a+rX /opt/musescore

# Kääre eikä symlinkki: päättömässä kontissa Qt yrittää muuten avata näytön
# ja kaatuu, vaikka kyse olisi pelkästä tiedostomuunnoksesta.
#
# Ratkaiseva muuttuja on MU_QT_QPA_PLATFORM, ei QT_QPA_PLATFORM: MuseScore
# asettaa jälkimmäisen itse omasta muuttujastaan, joten pelkkä
# QT_QPA_PLATFORM=offscreen ei tepsi — se yrittää silti xcb:tä ja kaatuu
# "could not connect to display". Mitattu, ei arvattu.
cat > /usr/local/bin/mscore <<'WRAP'
#!/bin/bash
# MuseScore ilman näyttöä. Arvot asetetaan vain jos kutsuja ei ole niitä itse
# asettanut, jotta GUI:n voi silti avata X11/Wayland-soketin läpi.
export MU_QT_QPA_PLATFORM="${MU_QT_QPA_PLATFORM:-offscreen}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
exec /opt/musescore/AppRun "$@"
WRAP
chmod +x /usr/local/bin/mscore
ln -sf /usr/local/bin/mscore /usr/local/bin/musescore

# Savutesti. Tässä katsotaan vain että binääri ylipäätään käynnistyy:
# ilman libGLX:ää se kaatuu linkkerivirheeseen paluuarvolla 127, ja se on
# nimenomaan se vika joka pitää huomata buildissa eikä vasta renderöidessä.
# Tulostetta ei tarkisteta, koska MuseScoren CLI kirjoittaa AppRunin
# fallback-varoitukset stderriin ja kaatuu tunnetusti purkuvaiheessa
# (exit 134) vaikka olisi tehnyt työnsä — sama "katso tulosta, älä
# paluuarvoa" -sääntö kuin CLAUDE.md:ssä.
if version="$(mscore --version 2>/dev/null)"; then
    echo "    ${version:-mscore käynnistyy}"
else
    echo "!! mscore ei käynnisty:" >&2
    mscore --version >&2 || true
    exit 1
fi
