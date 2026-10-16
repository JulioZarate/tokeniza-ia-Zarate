// contar_tokens.mjs — uso: npm install gpt-tokenizer@2.9.0 && node contar_tokens.mjs archivo1.txt archivo2.txt ...
import fs from 'fs';
import * as o200 from 'gpt-tokenizer/encoding/o200k_base';
for (const f of process.argv.slice(2)) {
  const t = fs.readFileSync(f, 'utf8');
  console.log(f, {caracteres: t.length, palabras: t.trim().split(/\s+/).length, tokens_o200k: o200.encode(t).length});
}
