#!/usr/bin/env python3
"""
deobfuscate_pyobf.py

PyObfuscate için tersine çevirme aracı (güvenli, kodu çalıştırmaz).
Kullanım: python3 deobfuscate_pyobf.py obf_file.py [-o output.py]
"""

import re
import sys
import argparse
import base64
import zlib
import marshal
import binascii
import dis
from typing import Optional

MAX_ROUNDS = 50

def extract_heading_and_body(text: str):
    # note satırının altındaki heading'i ve body'yi bul
    # heading şuna benzer: "_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));"
    m = re.search(r"_\s*=\s*lambda\s+__\s*:\s*(.+?);", text, flags=re.S)
    heading = m.group(0) if m else None
    # body: heading sonrası kalan kod
    if m:
        body = text[m.end():]
    else:
        # eğer heading yoksa tüm text'i body say
        heading = None
        body = text
    return heading, body

def find_literal_bytes(body: str) -> Optional[bytes]:
    # exec((_)(b'...')) veya exec((_)( '...' )) gibi literal arar
    m = re.search(r"exec\(\s*\(_\)\s*\(\s*(b?)(?P<qquote>[rubfRUBF]?['\"])(?P<lit>.+?)(?P=qquote)\s*\)\s*\)", body, flags=re.S)
    if not m:
        # bazen doğrudan exec((_)(<literal>)) değil, başka yapıda olabilir; başka b'...' arama
        m2 = re.search(r"(b?)(?P<quote>['\"])(?P<lit>.+?)(?P=quote)", body, flags=re.S)
        if not m2:
            return None
        lit = m2.group('lit')
        is_bytes = bool(m2.group(1))
    else:
        lit = m.group('lit')
        is_bytes = bool(m.group(1))
    # Python repr tarafından escape edilmiş olabilir; güvenli şekilde eval etmeyeceğiz.
    # Bunun yerine çift kaçışları düzeltip hex veya ascii decode deneyeceğiz.
    # Eğer b'...' ise içinde \x.. kaçışları olabilir -> decode via latin-1 with unicode-escape
    if is_bytes:
        # restore Python byte-literal style: interpret escape sequences
        try:
            b = bytes(lit, "utf-8").decode("unicode_escape").encode("latin-1")
            return b
        except Exception:
            # fallback: try ascii literal
            try:
                return ast_literal_bytes(lit)
            except Exception:
                return None
    else:
        # string literal (muhtemelen bir byte string encoded with .encode('utf8') earlier)
        try:
            s = bytes(lit, "utf-8").decode("unicode_escape")
            return s.encode("utf-8")
        except Exception:
            return None

def ast_literal_bytes(s: str) -> bytes:
    # En basit güvenli parser: '\x41\x42' gibi hex kaçışları varsa işle
    hex_matches = re.findall(r"\\x([0-9A-Fa-f]{2})", s)
    if hex_matches:
        return bytes(int(h, 16) for h in hex_matches)
    # yoksa doğrudan ascii kabul et
    return s.encode("utf-8", errors="replace")

def build_ops_from_heading(heading: Optional[str]):
    """
    Heading stringindeki hangi işlemlerin uygulandığını kabaca tespit eder.
    Örnek heading'ler:
      "__import__('base64').b64decode(__[::-1])"
      "__import__('zlib').decompress(__import__('base64').b16decode(__[::-1]))"
      "__import__('marshal').loads(__[::-1])"
    Dönüş: liste halinde ops: e.g. ['reverse','b64decode','zlib_decompress','marshal_loads']
    """
    ops = []
    if not heading:
        return ops
    s = heading.lower()
    # Her zaman tersleme varsa reverse önce
    if "__[::-1]" in s or "[::-1]" in s:
        ops.append("reverse")
    # base64 türleri
    if "b64decode" in s:
        ops.append("b64")
    if "b16decode" in s or "b16" in s and "b16decode" in s:
        # base16 may be written as b16decode
        if "b16decode" in s:
            ops.append("b16")
    if "b32decode" in s:
        ops.append("b32")
    # zlib
    if "zlib" in s and "decompress" in s:
        ops.append("zlib")
    # marshal
    if "marshal" in s and "loads" in s:
        ops.append("marshal")
    return ops

def apply_ops(b: bytes, ops):
    data = b
    for op in ops:
        if op == "reverse":
            data = data[::-1]
        elif op == "b64":
            try:
                data = base64.b64decode(data)
            except Exception:
                # try with ascii string if bytes are quoted ascii
                try:
                    data = base64.b64decode(data.decode('utf-8', errors='ignore'))
                except Exception:
                    raise
        elif op == "b16":
            try:
                data = binascii.unhexlify(data)
            except Exception:
                try:
                    data = base64.b16decode(data)
                except Exception:
                    data = binascii.unhexlify(data.decode('utf-8', errors='ignore'))
        elif op == "b32":
            try:
                data = base64.b32decode(data)
            except Exception:
                data = base64.b32decode(data.decode('utf-8', errors='ignore'))
        elif op == "zlib":
            try:
                data = zlib.decompress(data)
            except Exception:
                # bazen data str halinde
                try:
                    data = zlib.decompress(data.decode('utf-8', errors='ignore').encode('latin-1'))
                except Exception:
                    raise
        elif op == "marshal":
            # marshal.loads returns a code object (or other python object)
            try:
                obj = marshal.loads(data)
            except Exception as e:
                raise RuntimeError("marshal.loads failed: %s" % e)
            return obj  # burada artık bytes yerine code objesi dönüyoruz
        else:
            raise RuntimeError("Bilinmeyen op: %s" % op)
    return data

def is_probable_python_source(b: bytes) -> bool:
    try:
        s = b.decode('utf-8', errors='ignore')
    except Exception:
        return False
    keywords = ['def ', 'import ', 'class ', 'exec(', 'print(', 'if __name__', '__name__', 'from ']
    score = sum(1 for k in keywords if k in s)
    return score >= 1

def main():
    p = argparse.ArgumentParser(description="Deobfuscate PyObfuscate outputs (safe, non-executing).")
    p.add_argument('file', help='Obfuscated python file')
    p.add_argument('-o', '--out', help='Write best-effort deobfuscated source to this file')
    args = p.parse_args()

    with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    heading, body = extract_heading_and_body(text)
    ops = build_ops_from_heading(heading)
    print("Detected heading:", heading)
    print("Guessed ops order:", ops)

    # Her döngüde body'den en dıştaki literal'i al, ops uygula, tekrar dene.
    current_body = body
    round = 0
    last_bytes = None
    recovered_source = None
    recovered_bytecode_obj = None

    while round < MAX_ROUNDS:
        round += 1
        lit = find_literal_bytes(current_body)
        if lit is None:
            print(f"[{round}] No literal bytes found in current body. Stopping.")
            break
        print(f"[{round}] Found {len(lit)} bytes literal. Applying ops...")
        try:
            res = apply_ops(lit, ops)
        except Exception as e:
            print(f"Operation failed: {e}")
            break

        # Eğer marshal op sonucu bir code objesi döndüyse
        if not isinstance(res, (bytes, bytearray)):
            # Muhtemelen marshal.loads sonucuydu -> code object veya başka python objesi
            recovered_bytecode_obj = res
            print(f"[{round}] Op produced Python object of type: {type(res)}")
            # disassemble code object if possible
            if hasattr(res, 'co_code') or isinstance(res, type((lambda:0).__code__)):
                print(f"[{round}] Disassembling code object (first 100 lines):")
                try:
                    # disassembly -> capture as string
                    dis.dis(res)
                except Exception as e:
                    print("disassembly failed:", e)
            else:
                print("Result is python object but not code object. repr():")
                print(repr(res)[:1000])
            # after marshal, there is usually no further plain-text source here
            break

        # res is bytes
        last_bytes = res
        if is_probable_python_source(res):
            print(f"[{round}] Recovered probable python source (len={len(res)}). Showing first 400 chars:\n")
            try:
                txt = res.decode('utf-8', errors='replace')
            except Exception:
                txt = res.decode('latin-1', errors='replace')
            print(txt[:400])
            recovered_source = txt
            # try to find new body inside txt (in case multiple layers)
            current_body = txt
            # attempt to find next literal if it's wrapped multiple times
            continue
        else:
            # res may be another encoded blob (e.g. nested loops), so set current_body to repr of bytes
            # Use repr to mimic how the original encoder inserted it
            current_body = repr(res)
            print(f"[{round}] Decoded bytes did not look like plain Python source. Continuing with repr(res).")

    # output results
    if args.out:
        if recovered_source:
            with open(args.out, 'w', encoding='utf-8') as f:
                f.write("# Deobfuscated best-effort output\n")
                f.write(recovered_source)
            print("Wrote best-effort deobfuscated source to:", args.out)
        elif last_bytes:
            # dump last bytes as binary
            with open(args.out, 'wb') as f:
                f.write(last_bytes)
            print("Wrote last recovered bytes to:", args.out)
        elif recovered_bytecode_obj:
            # try to marshal.dumps the code object into a .pyc-like file headerless
            try:
                dumped = marshal.dumps(recovered_bytecode_obj)
                with open(args.out, 'wb') as f:
                    f.write(dumped)
                print("Wrote marshaled code object to", args.out, "(may be .pyc body, no header).")
            except Exception as e:
                print("Cannot write recovered object:", e)
    else:
        print("No -o specified; to save output pass -o filename")

if __name__ == '__main__':
    main()
