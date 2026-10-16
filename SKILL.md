---
name: "tokeniza-ia"
description: "Estima, escala y compara el costo de llamadas a modelos de IA (tokens de entrada/salida × precio por millón). Úsala para costear prompts, respuestas o chatbots y comparar modelos antes de automatizar."
---

# Tokeniza-IA | Estimación y escalamiento de costos de modelos de IA

Skill acotado a **un solo tipo de análisis**: el costo por API de una interacción pregunta→respuesta y su escalamiento por volumen. No evalúa calidad, latencia ni suscripciones.

Se activa con: "cuántos tokens", "costo por llamada", "costo de la API", "cuánto cuesta escalar", "comparar modelos por precio", "tokenizer", "precio por millón de tokens", "costo de un chatbot", "presupuesto de IA".

---

## 1. Propósito

Calcular y comparar el costo de una interacción con un modelo de IA y su escalamiento (p. ej. 1,000 / 10,000 / 1,000,000 llamadas), identificar **qué variable explica la mayor parte del costo** y cerrar con una acción de control de costos con indicador.

Responde: ¿cuánto cuesta una llamada?, ¿cuánto cuesta a escala?, ¿qué modelo es el más barato y por cuánto?, ¿qué mueve más el costo: entrada, salida o modelo?

## 2. Alcance

**Sí cubre**
- Conteo de tokens de textos reales (preguntas, respuestas, prompts de sistema).
- Escenarios combinados (p. ej. pregunta corta/larga × respuesta corta/larga).
- Costo por llamada, escalamiento, diferencias absolutas y porcentuales vs. un modelo base.
- Sensibilidad: largo de salida, largo de entrada, elección de modelo.

**No cubre**
- Calidad, exactitud o latencia de los modelos.
- Planes de suscripción (ChatGPT Plus, Claude Pro, etc.): no se mezclan con precios de API.
- Costos de infraestructura, desarrollo o personal.
- Imágenes, audio o embeddings (salvo que se den tarifas y tokens específicos).

## 3. Entradas

| Campo | Obligatorio | Nota |
|---|---|---|
| Texto de entrada (pregunta y, si existe, prompt de sistema e historial) | Sí, o tokens ya contados | Texto exacto, no paráfrasis |
| Texto de salida esperada o muestra | Sí, o tokens ya contados | Usar una respuesta real como muestra |
| Tokens (si el usuario ya los tiene) | Opcional | Indicar con qué tokenizer se contaron |
| Modelos a comparar | Sí | Nombre exacto del modelo |
| Precio de entrada y de salida por modelo | Sí | Unidad (por 1M o 1K tokens), fuente y fecha |
| Moneda | Sí (default USD) | Si se pide MXN, se necesita tipo de cambio con fecha y fuente |
| Volúmenes | Sí (default 1,000 / 10,000 / 1,000,000) | |
| Fecha del análisis | Sí | Los precios cambian |
| Modelo base para comparar | Opcional | Default: el más caro |

**Regla de paro:** si falta un precio, un conteo de tokens o la unidad del precio, **se detiene el cálculo y se pide el dato**. Nunca se rellena con un valor "típico" o de memoria.

## 4. Procedimiento (Proceso)

**Tokenizar/estimar → obtener tarifas → calcular → escalar → comparar → validar.**

### Paso 1. Tokenizar / estimar
1. Guardar cada texto en un archivo `.txt` exacto (incluye markdown, porque la API lo devuelve).
2. Contar con el tokenizer de OpenAI `o200k_base` (el de platform.openai.com/tokenizer para GPT-4o y la familia GPT-5). Opciones:
   - Python: `pip install tiktoken` → `tiktoken.get_encoding("o200k_base")` (necesita descargar el vocabulario; si la red lo bloquea, usar Node).
   - Node (vocabulario incluido, funciona sin red externa): `npm install gpt-tokenizer@2.9.0` y el script `contar_tokens.mjs` de abajo.
3. Registrar por texto: caracteres, palabras, tokens y codificación usada.
4. Si hay modelos de otros proveedores (Claude, Gemini, etc.), **marcar su conteo como aproximación**: usan tokenizers propios. Si se tiene acceso a su API de conteo, usarla.
5. Armar los escenarios (tokens de entrada, tokens de salida). Declarar qué incluye la entrada: ¿solo la pregunta o también prompt de sistema e historial?

### Paso 2. Obtener tarifas
1. Consultar la fuente indicada por el usuario (p. ej. gptforwork.com) y, si es posible, la página oficial del proveedor.
2. Registrar por modelo: precio de entrada, precio de salida, unidad, fuente, fecha de consulta.
3. Si la fuente no muestra fecha de actualización, decirlo en Alertas.

### Paso 3. Calcular
**Costo por llamada = (tokens_entrada × precio_entrada ÷ U) + (tokens_salida × precio_salida ÷ U)**, con U = 1,000,000 (o 1,000 si la tarifa es por mil).

Mostrar al menos un ejemplo desarrollado paso a paso.

### Paso 4. Escalar
**Costo total = costo por llamada × N**, para cada volumen.

### Paso 5. Comparar
- Diferencia absoluta = costo_base − costo_modelo.
- Ahorro % = diferencia ÷ costo_base × 100.
- "Veces más barato" = costo_base ÷ costo_modelo.
- Mejor costo por escenario.
- Sensibilidad: efecto de alargar la salida, de alargar la entrada y de cambiar de modelo; % del costo que es salida.

### Paso 6. Validar
Correr las validaciones de la sección 5 antes de entregar.

### Script de cálculo (recomendado)
Guardar como `tokeniza_costos.py` y correr con `python3 tokeniza_costos.py config.json`. Usa `Decimal` y redondeo comercial (half-up), y se detiene si falta un dato.

```python
#!/usr/bin/env python3
import json, sys
from decimal import Decimal as D, ROUND_HALF_UP

def r(x, n): return x.quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)
def fmt(x, n): return f"{r(x, n):,.{n}f}"

cfg = json.load(open(sys.argv[1], encoding="utf-8"))
mon = cfg.get("moneda", "USD"); unidad = D(cfg.get("unidad_precio", 1_000_000))
vols = cfg["volumenes"]; mods = cfg["modelos"]
base = cfg.get("modelo_base", mods[0]["nombre"]); err = []
for m in mods:
    for k in ("precio_entrada", "precio_salida", "fuente", "fecha_precio"):
        if m.get(k) in (None, ""): err.append(f"Falta '{k}' en modelo {m.get('nombre')}")
for e in cfg["escenarios"]:
    for k in ("tokens_entrada", "tokens_salida"):
        if not isinstance(e.get(k), int) or e[k] < 0: err.append(f"'{k}' inválido en escenario {e.get('nombre')}")
if base not in [m["nombre"] for m in mods]: err.append(f"modelo_base '{base}' no está en la lista")
if err: print("DETENIDO — faltan datos:\n- " + "\n- ".join(err)); sys.exit(1)

hdr = ["Escenario", "Tokens entrada / salida", "Modelo", f"Costo por llamada ({mon})"] + \
      [f"{v:,} llamadas" for v in vols] + ["% costo de salida", f"Dif. abs. vs {base}", f"Ahorro % vs {base}"]
print("| " + " | ".join(hdr) + " |"); print("|" + "---|" * len(hdr))
mejores = []
for e in cfg["escenarios"]:
    ti, to = D(e["tokens_entrada"]), D(e["tokens_salida"]); cs = {}
    for m in mods:
        ci = ti * D(str(m["precio_entrada"])) / unidad; co = to * D(str(m["precio_salida"])) / unidad
        cs[m["nombre"]] = (ci, co, ci + co)
    cb = cs[base][2]
    for m in mods:
        ci, co, c = cs[m["nombre"]]; dif = cb - c
        ah = "—" if m["nombre"] == base else f"{fmt(dif / cb * 100, 1)}%"
        row = [e["nombre"], f"{int(ti):,} / {int(to):,}", m["nombre"], fmt(c, 6)] + \
              [fmt(c * v, 2) for v in vols] + [f"{fmt(co / c * 100, 1)}%", fmt(dif, 6), ah]
        print("| " + " | ".join(row) + " |")
    b = min(cs, key=lambda k: cs[k][2]); mejores.append((e["nombre"], b, cs[b][2]))
print("\n**Mejor costo por escenario:** " + "; ".join(f"{n} → {b} ({fmt(c,6)} {mon}/llamada)" for n, b, c in mejores))
print("\n**Precios usados:** " + "; ".join(f"{m['nombre']} {m['precio_entrada']}/{m['precio_salida']} {mon} por {int(unidad):,} tokens ({m['fuente']}, {m['fecha_precio']})" for m in mods))
```

`config.json` de ejemplo:
```json
{"moneda": "USD", "unidad_precio": 1000000, "volumenes": [1000, 10000, 1000000],
 "modelo_base": "gpt-5.6-sol",
 "escenarios": [{"nombre": "E1: QC+RC", "tokens_entrada": 34, "tokens_salida": 343}],
 "modelos": [{"nombre": "gpt-5.6-sol", "precio_entrada": 5, "precio_salida": 30,
              "fuente": "gptforwork.com", "fecha_precio": "2026-10-09"}]}
```

### Script de conteo de tokens (Node, sin descarga de vocabulario)
```js
// contar_tokens.mjs — uso: node contar_tokens.mjs archivo1.txt archivo2.txt ...
import fs from 'fs';
import * as o200 from 'gpt-tokenizer/encoding/o200k_base';
for (const f of process.argv.slice(2)) {
  const t = fs.readFileSync(f, 'utf8');
  console.log(f, {caracteres: t.length, palabras: t.trim().split(/\s+/).length, tokens_o200k: o200.encode(t).length});
}
```

**Prueba de calibración** (caso de referencia, renta de autos, precios al 09-oct-2026): 34 tokens de entrada / 343 de salida con gpt-5.6-sol ($5/$30) debe dar **0.010460 USD por llamada** y **10,460.00 USD por 1,000,000 de llamadas**. Si el script no reproduce eso, no usarlo.

## 5. Validaciones

Antes de entregar, comprobar y reportar:

| Validación | Qué se revisa |
|---|---|
| Unidades | Precio por 1M vs. por 1K tokens; U correcto en la fórmula; moneda declarada |
| Precios | Cada precio tiene fuente y fecha; entrada y salida no están invertidas |
| Fecha | Fecha de consulta registrada; advertir si la fuente no tiene fecha de actualización |
| Tokens | Tokenizer y codificación declarados; qué incluye la entrada (sistema, historial) |
| Redondeos | Cálculo con precisión completa; redondeo comercial solo al mostrar (6 decimales por llamada, 2 a escala) |
| Fórmulas | Un ejemplo recalculado a mano coincide con la tabla |
| Totales | Entrada + salida = total; costo × N = escalado; la prueba de calibración pasa |

## 6. Evidencia

Cuenta como soporte únicamente:
- **Registro de tokens:** archivo de texto + tokenizer + codificación + conteo.
- **Registro de tarifas:** modelo + precio de entrada/salida + unidad + URL de la fuente + fecha de consulta.
- **Métrica calculada:** salida del script o cálculo reproducible, con fórmula mostrada.

Cada afirmación del reporte ("la salida explica el X% del costo", "el modelo Y ahorra Z%") debe apuntar a una fila de la tabla o a un registro.

## 7. Salida

Entregar, en este orden:
1. **Tabla comparativa única:** escenario | tokens entrada/salida | modelo | costo por llamada | costo por cada volumen | % del costo que es salida | diferencia absoluta y ahorro % vs. base.
2. **Mejor costo** por escenario.
3. **Sensibilidad:** cuánto cambia el costo al alargar la salida, al alargar la entrada y al cambiar de modelo; qué variable domina.
4. **Advertencias:** supuestos y datos por verificar (sección 8).
5. **Fuentes:** lista de URLs con fecha de consulta.
6. **Recomendación** con formato acción + evidencia + indicador, que cierre con: *¿Qué se hará, con qué evidencia y cómo sabremos si funcionó?*

Separar explícitamente **dato / inferencia / supuesto / límite**.

## 8. Alertas

Señalar siempre que apliquen:
- **Tokenizer distinto:** Claude, Gemini y otros no usan `o200k_base`; su conteo es aproximado.
- **Tokenizer de modelos nuevos no documentado:** si se asume `o200k_base`, decirlo.
- **Tokens ocultos de razonamiento:** modelos con razonamiento cobran tokens de salida no visibles; el costo real puede ser mayor.
- **Prompt de sistema e historial:** si no se incluyeron, el costo de entrada está subestimado.
- **Sobrecarga de formato de chat:** unos pocos tokens por mensaje (normalmente menos del 1%).
- **Descuentos no aplicados:** entrada en caché, Batch API, precios por horario (p. ej. DeepSeek pico/valle), niveles por volumen.
- **Fuente de terceros:** contrastar con la página oficial del proveedor.
- **Tipo de cambio:** si se convierte a otra moneda, fijar fecha y fuente.
- **Variabilidad de la salida:** una sola respuesta de muestra no representa el promedio; idealmente medir varias.

## 9. Límites

- **No inventar tarifas ni tokens.** Si falta un dato, detener y pedirlo.
- **No evaluar la calidad de un modelo solo por su precio.** "Más barato" no es "mejor"; la recomendación de modelo económico debe ir acompañada de un indicador de calidad.
- **No mezclar suscripción con API.**
- **No afirmar causalidad** sobre comportamiento de usuarios o ahorros futuros; son proyecciones bajo supuestos.
- **No extrapolar** a otros idiomas, tipos de contenido o modelos sin recontar.
- No usar precios de memoria; siempre consultados con fecha.
## 10. Archivos incluidos en esta carpeta

| Archivo | Uso |
|---|---|
| `scripts/tokeniza_costos.py` | Calculadora de costos: `python3 scripts/tokeniza_costos.py ejemplos/config_renta_autos.json` |
| `scripts/contar_tokens.mjs` | Conteo de tokens con o200k_base (requiere `npm install gpt-tokenizer@2.9.0`) |
| `ejemplos/config_renta_autos.json` | Configuración del caso de referencia (4 escenarios, 5 modelos) |
| `ejemplos/q_*.txt`, `ejemplos/r_*.txt` | Textos del caso de referencia (preguntas y respuestas) |
| `herramienta/tokeniza-ia.html` | Terminal web: sube archivos de un proyecto y saca el costeo completo en el navegador |
