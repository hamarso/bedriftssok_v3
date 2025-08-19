# 🚀 Deploy til Vercel - Steg for steg

## 📋 Forutsetninger

- GitHub-konto
- Vercel-konto (gratis)
- Python 3.9+ installert lokalt

## 🔧 Steg 1: Opprett GitHub Repository

1. **Gå til GitHub.com og logg inn**
2. **Klikk "New repository"**
3. **Fyll ut:**
   - Repository name: `bedriftssok-v3` (eller hva du vil)
   - Description: `Bedriftssøk app for Brønnøysundregisteret`
   - Public eller Private (valgfritt)
   - Ikke initialiser med README (vi har allerede en)
4. **Klikk "Create repository"**

## 📁 Steg 2: Push kode til GitHub

```bash
# I din lokale mappe (Bedriftssok_v3)
git init
git add .
git commit -m "Initial commit: Bedriftssøk app"
git branch -M main
git remote add origin https://github.com/DITT_BRUKERNAVN/bedriftssok-v3.git
git push -u origin main
```

## 🌐 Steg 3: Deploy til Vercel

1. **Gå til [vercel.com](https://vercel.com)**
2. **Logg inn med GitHub**
3. **Klikk "New Project"**
4. **Velg ditt repository:**
   - Import Git Repository
   - Velg `bedriftssok-v3` (eller ditt repo-navn)
   - Klikk "Import"

## ⚙️ Steg 4: Konfigurer Vercel

Vercel vil automatisk oppdage at det er en Python-app. Du trenger ikke endre noe:

- **Framework Preset:** Python (automatisk)
- **Root Directory:** `./` (standard)
- **Build Command:** Vercel håndterer dette automatisk
- **Output Directory:** Vercel håndterer dette automatisk

## 🚀 Steg 5: Deploy

1. **Klikk "Deploy"**
2. **Vent på at bygget fullføres** (1-2 minutter)
3. **Du får en URL:** `https://ditt-prosjekt.vercel.app`

## ✅ Steg 6: Test appen

1. **Åpne URL-en du fikk**
2. **Test søkefunksjonen:**
   - NACE-kode: `70.220`
   - Min ansatte: `100`
3. **Klikk "Søk etter bedrifter"**
4. **Test Excel-eksport**

## 🔄 Steg 7: Oppdateringer

For å oppdatere appen:

```bash
# Gjør endringer lokalt
git add .
git commit -m "Oppdatering: [beskrivelse]"
git push origin main

# Vercel deployer automatisk når du pusher til main
```

## 🐛 Feilsøking

### Appen fungerer ikke
- Sjekk at alle filer er pushet til GitHub
- Sjekk Vercel build logs
- Sjekk at `vercel.json` er korrekt

### API-feil
- Sjekk at Brønnøysundregisteret er tilgjengelig
- Sjekk rate limiting
- Sjekk at NACE-koden er gyldig

### Excel-eksport fungerer ikke
- Sjekk at `openpyxl` er i `requirements.txt`
- Sjekk at dataene er korrekt formatert

## 📞 Hjelp

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **GitHub Help:** [help.github.com](https://help.github.com)
- **Python Flask:** [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

**🎉 Gratulerer! Din app er nå live på internett!**
