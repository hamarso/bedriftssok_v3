# 🔍 Bedriftssøk - Brønnøysundregisteret

En moderne web-app for å søke etter bedrifter i Brønnøysundregisteret basert på bransje (NACE-kode) og antall ansatte.

## ✨ Funksjoner

- 🔍 Søk etter bedrifter basert på NACE-kode og minimum antall ansatte
- 📊 Vis resultater i en oversiktlig tabell
- 📥 Eksporter resultater til Excel-fil
- 📱 Responsivt design som fungerer på alle enheter
- 🚀 Enkel deploy til Vercel

## 🚀 Kom i gang

### Lokal utvikling

1. **Klon repositoriet:**
   ```bash
   git clone <ditt-repo-url>
   cd Bedriftssok_v3
   ```

2. **Installer avhengigheter:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Kjør appen lokalt:**
   ```bash
   python app.py
   ```

4. **Åpne nettleseren:**
   Gå til `http://localhost:5000`

### Deploy til Vercel

1. **Push koden til GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Koble til Vercel:**
   - Gå til [vercel.com](https://vercel.com)
   - Logg inn med GitHub
   - Klikk "New Project"
   - Velg ditt repository
   - Vercel vil automatisk oppdage at det er en Python-app

3. **Deploy:**
   - Vercel vil automatisk bygge og deploye appen
   - Du får en URL som `https://ditt-prosjekt.vercel.app`

## 🛠️ Teknisk informasjon

### Struktur
```
Bedriftssok_v3/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Frontend
├── requirements.txt     # Python avhengigheter
├── vercel.json         # Vercel konfigurasjon
└── README.md           # Denne filen
```

### API-endepunkter

- `GET /` - Hovedside
- `POST /api/sok` - Søk etter bedrifter
- `POST /api/eksporter` - Eksporter til Excel

### Brukte teknologier

- **Backend:** Python Flask
- **Frontend:** HTML, CSS, JavaScript (vanlig)
- **Excel:** openpyxl
- **HTTP requests:** requests
- **Deploy:** Vercel

## 📝 Bruk av appen

1. **Angi søkekriterier:**
   - NACE-kode (f.eks. 70.220 for konsulentvirksomhet)
   - Minimum antall ansatte

2. **Klikk "Søk etter bedrifter"**
   - Appen henter data fra Brønnøysundregisteret
   - Resultatene vises i en tabell

3. **Eksporter til Excel:**
   - Klikk "Eksporter til Excel" for å laste ned dataene

## 🔧 Konfigurasjon

### NACE-koder (eksempler)
- `70.220` - Konsulentvirksomhet innen forretningsadministrasjon
- `62.010` - Programvareutvikling
- `43.210` - Elektrisk installasjon
- `41.200` - Bygging av boliger

### Standardverdier
- Standard NACE-kode: `70.220`
- Standard minimum ansatte: `100`

## 🚨 Begrensninger

- Brønnøysundregisteret har rate limiting
- Store datasett kan ta tid å hente
- Excel-eksport har en maksimal størrelse

## 🤝 Bidrag

1. Fork prosjektet
2. Opprett en feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit endringene (`git commit -m 'Add some AmazingFeature'`)
4. Push til branchen (`git push origin feature/AmazingFeature`)
5. Opprett en Pull Request

## 📄 Lisens

Dette prosjektet er lisensiert under MIT-lisensen.

## 📞 Support

Hvis du har spørsmål eller problemer, opprett en issue på GitHub.

---

**Laget med ❤️ for enklere bedriftssøk**
