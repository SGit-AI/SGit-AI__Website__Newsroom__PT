#!/usr/bin/env python3
"""pt.newsroom.sgit.ai — ler o texto de um PDF congelado, incluindo os do Diário da República.

    python3 build/pdf.py <ficheiro.pdf>      # imprime o texto visível

PORQUE É QUE ISTO EXISTE, e porque não é acessório.

A primeira história que o resumo de comissionamento encomenda (§11) é que *a agenda nacional de
IA existe e o seu instrumento legal não pôde ser confirmado no registo público*, porque o diário
oficial renderiza por script e devolve um corpo vazio a um leitor automático. Isso é verdade e
esta redação mediu-o: `dre.pt` devolveu 2 346 bytes e 22 caracteres visíveis.

Mas a versão da história que ficava por essa medição estaria incompleta de uma maneira que
importa. O Diário da República **publica o texto integral em PDF**, num endereço construível
(`files.diariodarepublica.pt/1s/<ano>/<mês>/...`), e esse PDF contém o diploma. O que impede um
leitor automático de o ler não é o HTML: é que o PDF vem **cifrado com o manipulador de segurança
padrão** — palavra-passe de utilizador vazia, apenas restrições de permissões. Qualquer visualizador
o abre; uma biblioteca genérica de extração falha, e falha em silêncio, devolvendo zero caracteres.

Um zero devolvido por uma limitação do leitor é indistinguível, no ficheiro de resultados, de um
zero devolvido por uma página vazia — e essa confusão faria esta redação publicar «não se
consegue ler o registo nacional» quando a verdade é «não implementámos o decifrador». A diferença
entre as duas frases é a diferença entre uma reportagem e uma desculpa, por isso o decifrador
está implementado aqui.

O que está implementado: o algoritmo 2 da norma (chave do documento a partir de /O, /P e do /ID),
o algoritmo 1 (chave por objeto), RC4 e AES-128-CBC (AESV2), e AES-256 (AESV3/R6) para quando o
diário mudar de versão. Só se tenta a palavra-passe de utilizador VAZIA: contornar uma palavra-passe
que alguém escolheu seria outra coisa, e esta redação não a faz.

Se um PDF não abrir assim, `texto()` devolve uma cadeia vazia e `porque_nao()` diz qual foi a
razão — cifrado com palavra-passe, um filtro que não conhecemos, ou um PDF digitalizado sem camada
de texto. O chamador regista a razão em vez de a inventar.
"""
import hashlib
import re
import struct
import sys
import zlib

PAD = bytes([
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41, 0x64, 0x00, 0x4E, 0x56,
    0xFF, 0xFA, 0x01, 0x08, 0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A,
])


def _rc4(chave, dados):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + chave[i % len(chave)]) & 0xFF
        s[i], s[j] = s[j], s[i]
    out = bytearray()
    i = j = 0
    for c in dados:
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        out.append(c ^ s[(s[i] + s[j]) & 0xFF])
    return bytes(out)


def _aes_cbc(chave, dados):
    """AES-CBC decrypt: the first 16 bytes of `dados` are the initialisation vector."""
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        try:
            from Crypto.Cipher import AES
        except ImportError:
            return None
    corpo = dados[16:]
    corpo = corpo[:len(corpo) - len(corpo) % 16]     # whole blocks only
    if not corpo:
        return b""
    claro = AES.new(chave, AES.MODE_CBC, dados[:16]).decrypt(corpo)
    if claro and 1 <= claro[-1] <= 16:               # strip PKCS#7 padding
        claro = claro[:-claro[-1]]
    return claro


def _literal(bruto, chave):
    """Read a PDF string — either <hex> or (literal with \\ escapes) — from the Encrypt dict."""
    m = re.search(rb"/" + chave + rb"\s*<([0-9A-Fa-f\s]+)>", bruto)
    if m:
        return bytes.fromhex(re.sub(rb"\s", b"", m.group(1)).decode())
    m = re.search(rb"/" + chave + rb"\s*\(", bruto)
    if not m:
        return None
    i = m.end()
    out, nivel = bytearray(), 1
    while i < len(bruto):
        c = bruto[i]
        if c == 0x5C:                      # backslash
            nxt = bruto[i + 1]
            mapa = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
            if nxt in mapa:
                out.append(mapa[nxt]); i += 2
            elif 0x30 <= nxt <= 0x37:      # octal
                oct_ = bruto[i + 1:i + 4]
                k = 0
                while k < 3 and k < len(oct_) and 0x30 <= oct_[k] <= 0x37:
                    k += 1
                out.append(int(oct_[:k], 8) & 0xFF); i += 1 + k
            else:
                out.append(nxt); i += 2
            continue
        if c == 0x28:
            nivel += 1
        elif c == 0x29:
            nivel -= 1
            if nivel == 0:
                break
        out.append(c); i += 1
    return bytes(out)


class Cifra:
    """The document's standard security handler, resolved for the EMPTY user password."""

    def __init__(self, bruto):
        self.ok = False
        self.porque = None
        self.metodo = None
        d = re.search(rb"/Filter\s*/Standard(.{0,900}?)>>\s*(?:endobj|stream)", bruto, re.S)
        if not d:
            d = re.search(rb"<<([^<>]{0,900}?/Filter\s*/Standard[^<>]{0,900}?)>>", bruto, re.S)
        if not d:
            self.porque = "cifrado, mas o dicionário de cifra não foi localizado"
            return
        dic = d.group(1)
        # the Encrypt dict often begins BEFORE the /Filter key, so widen to the whole object
        i = bruto.rfind(b"<<", 0, d.start() + 1)
        if i != -1:
            dic = bruto[i:d.end()]

        def num(k, omissao=0):
            m = re.search(rb"/" + k + rb"\s*(-?\d+)", dic)
            return int(m.group(1)) if m else omissao

        self.R = num(b"R", 2)
        self.V = num(b"V", 1)
        self.P = num(b"P", -1)
        # /Length appears twice and means different things in the two places: inside the crypt
        # filter (/StdCF<</CFM/AESV2/Length 16>>) it is BYTES, and at the top level of the
        # Encrypt dict it is BITS. Taking the first match found the crypt filter's 16 and read it
        # as bits, producing a 2-byte key; every AES call then failed on key length. Both are
        # normalised here — anything above 40 is bits — and the largest wins.
        comprimentos = [int(x) for x in re.findall(rb"/Length\s*(\d+)", dic)]
        self.n = max([c // 8 if c > 40 else c for c in comprimentos] + [5])
        self.O = _literal(dic, b"O")
        self.U = _literal(dic, b"U")
        cfm = re.search(rb"/CFM\s*/(\w+)", dic)
        self.cfm = cfm.group(1).decode() if cfm else ("V2" if self.V in (1, 2) else None)
        mid = re.search(rb"/ID\s*\[\s*<([0-9A-Fa-f]+)>", bruto)
        self.id0 = bytes.fromhex(mid.group(1).decode()) if mid else b""
        self.metadata_cifrada = b"/EncryptMetadata false" not in dic

        if self.O is None:
            self.porque = "cifrado, mas o dicionário não traz /O"
            return
        if self.R >= 5:
            self._chave_r6()
        else:
            self._chave_r234()

    def _chave_r234(self):
        h = hashlib.md5()
        h.update(PAD)
        h.update(self.O[:32])
        h.update(struct.pack("<i", self.P))
        h.update(self.id0)
        if self.R >= 4 and not self.metadata_cifrada:
            h.update(b"\xff\xff\xff\xff")
        chave = h.digest()
        if self.R >= 3:
            for _ in range(50):
                chave = hashlib.md5(chave[:self.n]).digest()
        self.chave = chave[:self.n]
        self.ok = True

    def _chave_r6(self):
        """AES-256 (R5/R6). The empty user password validates against /U's salts."""
        if not self.U or len(self.U) < 48:
            self.porque = "cifrado em AES-256, mas /U está truncado"
            return
        sal_val, sal_chave = self.U[32:40], self.U[40:48]
        if self.R == 5:
            confirma = hashlib.sha256(b"" + sal_val).digest()
        else:
            confirma = self._hash_r6(b"", sal_val, b"")
        if confirma != self.U[:32]:
            self.porque = ("cifrado com uma palavra-passe de utilizador; este leitor só tenta a "
                           "palavra-passe vazia e não contorna a que alguém escolheu")
            return
        ik = (hashlib.sha256(b"" + sal_chave).digest() if self.R == 5
              else self._hash_r6(b"", sal_chave, b""))
        ue = _literal_none = None
        self.porque = None
        try:
            from Cryptodome.Cipher import AES
        except ImportError:
            self.porque = "AES-256 precisa de pycryptodome, que não está instalado"
            return
        if not hasattr(self, "UE") or self.UE is None:
            self.porque = "cifrado em AES-256 e /UE não foi localizado"
            return
        self.chave = AES.new(ik, AES.MODE_CBC, b"\x00" * 16).decrypt(self.UE[:32])
        self.cfm, self.ok = "AESV3", True

    @staticmethod
    def _hash_r6(pw, sal, udata):
        from Cryptodome.Cipher import AES
        k = hashlib.sha256(pw + sal + udata).digest()
        i = 0
        while True:
            k1 = (pw + k + udata) * 64
            e = AES.new(k[:16], AES.MODE_CBC, k[16:32]).encrypt(
                k1[:len(k1) - len(k1) % 16])
            mod = sum(e[:16]) % 3
            k = [hashlib.sha256, hashlib.sha384, hashlib.sha512][mod](e).digest()
            i += 1
            if i >= 64 and e[-1] <= i - 32:
                break
        return k[:32]

    def decifrar(self, dados, obj, ger):
        if not self.ok:
            return dados
        if self.cfm == "AESV3":
            return _aes_cbc(self.chave, dados) or b""
        h = hashlib.md5()
        h.update(self.chave)
        h.update(struct.pack("<i", obj)[:3])
        h.update(struct.pack("<i", ger)[:2])
        if self.cfm == "AESV2":
            h.update(b"sAlT")
        k = h.digest()[:min(len(self.chave) + 5, 16)]
        if self.cfm == "AESV2":
            return _aes_cbc(k, dados) or b""
        return _rc4(k, dados)


# ------------------------------------------------------ codificação de tipos ---
# Um PDF de tipos subconjuntados não guarda texto: guarda códigos de glifo. Num diploma do Diário
# da República esses códigos vêm deslocados — «OLFHQFLDPHQWR» são os bytes de «licenciamento» —
# e um leitor que os despeje tal como estão produz linhas que parecem texto corrompido e não
# correspondem a excerto nenhum. O mapa que os traduz está no próprio ficheiro: cada tipo pode
# trazer um fluxo `/ToUnicode`, um CMap que diz que código dá que carácter.
#
# Lê-se esse mapa em vez de se adivinhar o deslocamento. Um deslocamento adivinhado acertaria
# neste diploma e falharia no seguinte, e falharia em silêncio — que é a espécie de erro que este
# site existe para não cometer.
_BFCHAR = re.compile(rb"beginbfchar(.*?)endbfchar", re.S)
_BFRANGE = re.compile(rb"beginbfrange(.*?)endbfrange", re.S)
_HEX = re.compile(rb"<([0-9A-Fa-f]+)>")


def _utf16(h):
    b = bytes.fromhex(h.decode())
    try:
        return b.decode("utf-16-be") if len(b) % 2 == 0 else b.decode("latin-1")
    except UnicodeDecodeError:
        return ""


def _cmap(fluxo):
    """Parse a /ToUnicode CMap into {glyph code: text}."""
    mapa = {}
    for m in _BFCHAR.finditer(fluxo):
        pares = _HEX.findall(m.group(1))
        for i in range(0, len(pares) - 1, 2):
            mapa[int(pares[i], 16)] = _utf16(pares[i + 1])
    for m in _BFRANGE.finditer(fluxo):
        corpo = m.group(1)
        for lo, hi, alvo in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", corpo):
            base = int(alvo, 16)
            for k, c in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                mapa[c] = chr(base + k) if base + k < 0x110000 else ""
        for lo, hi, lista in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", corpo, re.S):
            alvos = _HEX.findall(lista)
            for k, c in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                if k < len(alvos):
                    mapa[c] = _utf16(alvos[k])
    return mapa


def _largura_do_codigo(mapa):
    """1 for a simple font, 2 for a CID font — decided by the codes the CMap actually carries."""
    return 2 if mapa and max(mapa) > 0xFF else 1


# --------------------------------------------------------- extração de texto ---
_TJ = re.compile(rb"\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>")


def _bytes_do_operando(s):
    """The raw glyph-code bytes of one show-text operand, hex or literal."""
    if s.startswith(b"<"):
        hx = re.sub(rb"\s", b"", s[1:-1])
        if len(hx) % 2:
            hx += b"0"
        try:
            return bytes.fromhex(hx.decode())
        except ValueError:
            return b""
    cru = s[1:-1]
    cru = re.sub(rb"\\([nrtbf()\\])",
                 lambda x: {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
                            b"f": b"\f"}.get(x.group(1), x.group(1)), cru)
    return re.sub(rb"\\([0-7]{1,3})", lambda x: bytes([int(x.group(1), 8) & 0xFF]), cru)


def _descodificar(bruto, mapa):
    """Glyph codes to text, through the font's own /ToUnicode map when it has one."""
    if not mapa:
        return bruto.decode("latin-1", "replace")
    largura = _largura_do_codigo(mapa)
    fora = []
    if largura == 2:
        for i in range(0, len(bruto) - 1, 2):
            fora.append(mapa.get((bruto[i] << 8) | bruto[i + 1], ""))
    else:
        for c in bruto:
            fora.append(mapa.get(c, chr(c)))
    return "".join(fora)


def _texto_de_conteudo(fluxo, mapas, omissao=None):
    """Pull the show-text operands out of a decoded content stream, following the active font.

    `Tf` names the font resource in force; `mapas` maps that name to that font's /ToUnicode table,
    so each run of text is decoded through the map that actually applies to it rather than through
    a single guess for the whole document.

    Deliberately not a layout engine: it reads Tj / TJ / ' / " in the order the producer wrote
    them, so a two-column gazette page comes out in production order, not reading order. That is
    enough for the only question asked of it — is this excerpt in this document — and claiming
    more would be claiming a typesetter."""
    out = []
    activo = omissao
    padrao = rb"(?:/([^\s/<>\[\]()]+)\s+[\d.]+\s+Tf)|(?:\[(.*?)\]\s*TJ)|(?:(\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]*>)\s*(?:Tj|'|\"))"
    for m in re.finditer(padrao, fluxo, re.S):
        if m.group(1):
            activo = m.group(1).decode("latin-1")
            continue
        bloco = m.group(2) or m.group(3) or b""
        mapa = mapas.get(activo) or {}
        pedacos = [_descodificar(_bytes_do_operando(t.group(0)), mapa)
                   for t in _TJ.finditer(bloco)]
        if pedacos:
            out.append("".join(pedacos))
    return " ".join(out)


def texto(caminho):
    """The visible text of a PDF, or an empty string. `porque_nao` says why when it is empty."""
    bruto = caminho.read_bytes() if hasattr(caminho, "read_bytes") else open(caminho, "rb").read()
    cifra = Cifra(bruto) if b"/Encrypt" in bruto else None
    if cifra and not cifra.ok:
        texto.porque = cifra.porque or "cifrado de uma forma que este leitor não reconhece"
        return ""

    # every indirect object, decrypted and inflated once
    objectos, fluxos = {}, {}
    for m in re.finditer(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", bruto, re.S):
        obj, ger, corpo = int(m.group(1)), int(m.group(2)), m.group(3)
        s = re.search(rb"stream\r?\n", corpo)
        objectos[obj] = corpo[:s.start()] if s else corpo
        if not s:
            continue
        fim = corpo.find(b"endstream", s.end())
        dados = corpo[s.end():fim if fim != -1 else len(corpo)].rstrip(b"\r\n")
        if cifra:
            dados = cifra.decifrar(dados, obj, ger)
        if b"/FlateDecode" in objectos[obj]:
            try:
                dados = zlib.decompress(dados)
            except zlib.error:
                try:
                    dados = zlib.decompressobj().decompress(dados)
                except zlib.error:
                    continue
        fluxos[obj] = dados

    def ref(dic, chave):
        m = re.search(rb"/" + chave + rb"\s+(\d+)\s+\d+\s+R", dic)
        return int(m.group(1)) if m else None

    # the /ToUnicode map of every font, keyed by the resource name a content stream calls it by
    mapas_por_fonte, cache = {}, {}
    for corpo in objectos.values():
        mf = re.search(rb"/Font\s*<<(.*?)>>", corpo, re.S)
        if not mf:
            continue
        for nome, num in re.findall(rb"/([^\s/<>\[\]()]+)\s+(\d+)\s+\d+\s+R", mf.group(1)):
            tu = ref(objectos.get(int(num), b""), b"ToUnicode")
            if tu is None:
                # a composite font keeps its /ToUnicode on the descendant
                desc = re.search(rb"/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R",
                                 objectos.get(int(num), b""))
                if desc:
                    tu = ref(objectos.get(int(desc.group(1)), b""), b"ToUnicode")
            if tu is not None and tu in fluxos:
                if tu not in cache:
                    cache[tu] = _cmap(fluxos[tu])
                if cache[tu]:
                    mapas_por_fonte[nome.decode("latin-1")] = cache[tu]

    partes = []
    for obj, dados in fluxos.items():
        if b"Tj" in dados or b"TJ" in dados:
            partes.append(_texto_de_conteudo(dados, mapas_por_fonte))

    t = " ".join(" ".join(partes).split())
    if not t:
        texto.porque = ("nenhuma camada de texto foi encontrada — é provavelmente um PDF "
                        "digitalizado, que precisaria de reconhecimento ótico")
    else:
        texto.porque = None
    return t


texto.porque = None


def porque_nao():
    return texto.porque


if __name__ == "__main__":
    from pathlib import Path
    t = texto(Path(sys.argv[1]))
    print(f"[{len(t)} caracteres] {porque_nao() or ''}")
    print(t[:3000])
