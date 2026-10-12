# Sito chiuso

Il sito non è pubblicato: Firebase Hosting serve solo la cartella `chiuso/`,
quindi ogni URL di heyrent.it risponde 404 (pagina vuota, `noindex`) e Google
rimuove le pagine dai risultati.

## Per riaprire

1. `cp firebase.sito-attivo.json firebase.json`
2. Elimina la cartella `chiuso/` e questo file
3. Commit e push su `main` (il deploy parte da GitHub Actions)
