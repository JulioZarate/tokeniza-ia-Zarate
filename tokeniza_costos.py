#!/usr/bin/env python3
"""Tokeniza-IA: calcula costo por llamada, escalamiento, comparación y sensibilidad.
Uso: python3 tokeniza_costos.py config.json  > resultado.md"""
import json, sys
from decimal import Decimal as D, ROUND_HALF_UP

def r(x, n):  # redondeo comercial (half-up), no bancario
    return x.quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)

def fmt(x, n):
    return f"{r(x, n):,.{n}f}"

cfg = json.load(open(sys.argv[1], encoding="utf-8"))
mon = cfg.get("moneda", "USD")
unidad = D(cfg.get("unidad_precio", 1_000_000))   # precios por 1M tokens
vols = cfg["volumenes"]
mods = cfg["modelos"]
base = cfg.get("modelo_base", mods[0]["nombre"])
err = []
# ---------- validaciones ----------
for m in mods:
    for k in ("precio_entrada", "precio_salida", "fuente", "fecha_precio"):
        if m.get(k) in (None, ""):
            err.append(f"Falta '{k}' en modelo {m.get('nombre')}")
for e in cfg["escenarios"]:
    for k in ("tokens_entrada", "tokens_salida"):
        if not isinstance(e.get(k), int) or e[k] < 0:
            err.append(f"'{k}' inválido en escenario {e.get('nombre')}")
if base not in [m["nombre"] for m in mods]:
    err.append(f"modelo_base '{base}' no está en la lista de modelos")
if err:
    print("DETENIDO — faltan datos:\n- " + "\n- ".join(err)); sys.exit(1)

hdr = ["Escenario", "Tokens entrada / salida", "Modelo", f"Costo por llamada ({mon})"] + \
      [f"{v:,} llamadas" for v in vols] + ["% costo de salida", f"Dif. abs. vs {base} / llamada", f"Ahorro % vs {base}"]
print("| " + " | ".join(hdr) + " |"); print("|" + "---|" * len(hdr))
checks = []
for e in cfg["escenarios"]:
    ti, to = D(e["tokens_entrada"]), D(e["tokens_salida"])
    costos = {}
    for m in mods:
        ci = ti * D(str(m["precio_entrada"])) / unidad
        co = to * D(str(m["precio_salida"])) / unidad
        costos[m["nombre"]] = (ci, co, ci + co)
    cb = costos[base][2]
    for m in mods:
        ci, co, c = costos[m["nombre"]]
        assert ci + co == c  # validación de totales
        pct_out = co / c * 100 if c else D(0)
        dif = cb - c
        ahorro = "—" if m["nombre"] == base else f"{fmt(dif / cb * 100, 1)}%"
        row = [e["nombre"], f"{int(ti):,} / {int(to):,}", m["nombre"], fmt(c, 6)] + \
              [fmt(c * v, 2) for v in vols] + [f"{fmt(pct_out, 1)}%", fmt(dif, 6), ahorro]
        print("| " + " | ".join(row) + " |")
    # el mejor costo por escenario
    best = min(costos, key=lambda k: costos[k][2])
    checks.append((e["nombre"], best, costos[best][2]))

print("\n**Mejor costo por escenario:** " + "; ".join(f"{n} → {b} ({fmt(c,6)} {mon}/llamada)" for n, b, c in checks))

# ---------- sensibilidad: ¿qué variable mueve más el costo? ----------
esc = cfg["escenarios"]
if len(esc) >= 2:
    pm = next(m for m in mods if m["nombre"] == base)
    pi, po = D(str(pm["precio_entrada"])), D(str(pm["precio_salida"]))
    def costo(e): return (D(e["tokens_entrada"]) * pi + D(e["tokens_salida"]) * po) / unidad
    lo_out = min(esc, key=lambda e: e["tokens_salida"]); hi_out = max(esc, key=lambda e: e["tokens_salida"])
    lo_in = min(esc, key=lambda e: e["tokens_entrada"]); hi_in = max(esc, key=lambda e: e["tokens_entrada"])
    print(f"\n**Sensibilidad (modelo {base}):**")
    print(f"- Salida {lo_out['tokens_salida']:,}→{hi_out['tokens_salida']:,} tokens: costo ×{fmt(costo(hi_out)/costo(lo_out),2)} (escenarios {lo_out['nombre']} → {hi_out['nombre']})")
    print(f"- Entrada {lo_in['tokens_entrada']:,}→{hi_in['tokens_entrada']:,} tokens: costo ×{fmt(costo(hi_in)/costo(lo_in),2)} (escenarios {lo_in['nombre']} → {hi_in['nombre']}; incluye diferencia de salida si la hay)")
    ratios = [D(str(m['precio_salida']))/D(str(m['precio_entrada'])) for m in mods if D(str(m['precio_entrada']))>0]
    print(f"- Precio de salida / entrada entre modelos: de {fmt(min(ratios),1)}× a {fmt(max(ratios),1)}×")
    cmods = [ (D(esc[0]['tokens_entrada'])*D(str(m['precio_entrada']))+D(esc[0]['tokens_salida'])*D(str(m['precio_salida'])))/unidad for m in mods]
    print(f"- Cambio de modelo (escenario {esc[0]['nombre']}): del más caro al más barato ×{fmt(max(cmods)/min(cmods),1)}")

print("\n**Precios usados:** " + "; ".join(f"{m['nombre']} {m['precio_entrada']}/{m['precio_salida']} {mon} por {int(unidad):,} tokens ({m['fuente']}, {m['fecha_precio']})" for m in mods))
