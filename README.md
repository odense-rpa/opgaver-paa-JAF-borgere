## Opgaver på JAF-borgere

Automatisering der identificerer borgere i målgruppe 6.7 (jobafklaringsforløb), som snart nærmer sig fristen for forelæggelse for sundhedskoordinator, og opretter en opgave til den primære sagsbehandler i Momentum, hvis opgaven ikke allerede eksisterer.

## Hvad gør robotten?

1. **Finder borgere** i målgruppe 6.7 med en målgruppestartdato mellem 1.400 og 1.600 dage siden via Momentum API
2. **Kontrollerer** om borgeren allerede har en opgave med titlen _"Forlæggelse for sundhedskoordinator senest om 4 mdr"_
3. **Tilføjer borgeren til arbejdskøen**, hvis opgaven mangler
4. **Finder den primære ansvarlige aktør** og slår sagsbehandleren op via e-mail/initialer
5. **Opretter opgaven** i Momentum med forfaldsdato 1.160 dage efter målgruppestartdatoen
6. **Registrerer aktiviteten** i aktivitetssporingen

## Forudsætninger

* Python ≥ 3.13
* [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
* Adgang til **Automation Server** (arbejdskø og legitimationsoplysninger)
* Adgang til **Momentum** (produktion)
* En **Odense SQL Server**-konto til aktivitetssporing

## Installation

```sh
uv sync
```

## Konfiguration

Legitimationsoplysninger hentes udelukkende fra Automation Server Credentials og må aldrig hardkodes eller lægges i filer:

| Credential-navn          | Beskrivelse                                      |
|--------------------------|--------------------------------------------------|
| `Momentum - produktion`  | Klient-id, klient-hemmelighed, API-nøgle og URL til Momentum |
| `Odense SQL Server`      | Brugernavn og adgangskode til aktivitetssporing  |

## Kørsel

```sh
# Fyld arbejdskøen med nye borgere
uv run python main.py --queue

# Behandl arbejdskøen
uv run python main.py
```

### Argumenter

| Argument  | Beskrivelse                                              |
|-----------|----------------------------------------------------------|
| `--queue` | Fyld arbejdskøen og afslut (kør ingen opgaveoprettelse) |

## Afhængigheder

| Pakke                      | Formål                              |
|----------------------------|-------------------------------------|
| `automation-server-client` | Arbejdskø- og credential-håndtering |
| `momentum-client`          | Integration med Momentum            |
| `odk-tools`                | Aktivitetssporing                   |

## Persondatasikkerhed

Robotten behandler personoplysninger på vegne af Odense Kommune, herunder CPR-numre, som er fortrolige oplysninger.

* Ingen personoplysninger må lægges i dette repository — hverken som testdata, i kode eller i kommentarer
* CPR-numre indgår udelukkende som reference i arbejdskøen under kørsel og gemmes ikke i filer eller logs
* Legitimationsoplysninger håndteres udelukkende via Automation Server Credentials
* Adgang til Momentum og SQL Server styres via rollebaserede tjenestekonti med mindst-privilegium-princippet

