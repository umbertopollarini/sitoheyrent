# Come rimettere online il sito quando riapriamo

In questo momento il sito pubblico mostra **solo** la pagina di chiusura temporanea
(`manutenzione/index.html`). Tutti i file del sito sono ancora qui nel repository:
non è stato cancellato nulla, è solo cambiato ciò che viene pubblicato.

## Per tornare online (2 comandi)

Dalla cartella del progetto:

```bash
cp firebase.sito-attivo.json firebase.json
git add -A && git commit -m "Riapertura: sito online" && git push
```

Il push su `main` fa partire GitHub Actions che ripubblica il sito completo su Firebase
Hosting. Ci vogliono circa 1-2 minuti. Puoi seguire l'avanzamento qui:
https://github.com/umbertopollarini/sitoheyrent/actions

## Per tornare in modalità "chiuso"

```bash
git revert <commit-della-riapertura>   # oppure rimetti a mano la config di manutenzione
```

## File coinvolti

| File | A cosa serve |
| --- | --- |
| `manutenzione/index.html` | La pagina di chiusura temporanea che vedono i visitatori |
| `firebase.json` | Configurazione **attuale**: pubblica solo la cartella `manutenzione/` |
| `firebase.sito-attivo.json` | Configurazione del **sito completo**, da ripristinare alla riapertura |

## Note

- La pagina di chiusura non usa Google Analytics/Ads né form: non raccoglie alcun dato.
- Ogni indirizzo del sito (es. `/noleggio-furgoni-modena`) mostra la pagina di chiusura.
- Alla riapertura tutti gli URL, i redirect e la SEO tornano esattamente come prima.
