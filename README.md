# Tokeniza-IA

Terminal web para estimar, escalar y comparar el costo de llamadas a modelos de IA.

**Página en vivo:** https://juliozarate.github.io/tokeniza-ia-Zarate/

- Sube los textos de un proyecto (preguntas, prompt de sistema, respuestas de muestra) y la página cuenta los tokens con `o200k_base`, el tokenizer de OpenAI.
- Calcula el costo por llamada, el costo a 1,000 / 10,000 / 1,000,000 llamadas, la comparación contra un modelo base, la sensibilidad, las advertencias y una recomendación.
- Fórmula: `costo/llamada = tokens_entrada × precio_entrada ÷ 1,000,000 + tokens_salida × precio_salida ÷ 1,000,000`.
- Tarifas precargadas de gptforwork.com (consultadas el 09-oct-2026), editables.

## Archivos del skill

| Archivo | Uso |
|---|---|
| `SKILL.md` | Skill Tokeniza-IA completo |
| `tokeniza_costos.py` | Calculadora: `python3 tokeniza_costos.py config_renta_autos.json` |
| `contar_tokens.mjs` | Conteo de tokens (requiere `npm install gpt-tokenizer@2.9.0`) |
| `config_renta_autos.json` | Caso de referencia: renta de autos, 4 escenarios |

Curso AI Tools · Julio Alejandro Zárate García
