# skisse-til-cad

Ein [Agent Skill](https://agentskills.io) for å gå frå skisse eller produktbilete til ferdig produkt: Tripo image-to-3D, segmentering eller lågpoly, mekanisk CAD, printfiler og monteringsrettleiing i IKEA-stil.

*An Agent Skill (Norwegian Nynorsk) for going from a sketch or product image to a physical product: Tripo image-to-3D, segmentation or low poly, mechanical CAD, print files and IKEA-style assembly instructions. Includes a Tripo API recipe checked against the full official documentation.*

## Innhald

| Fil | Innhald |
| --- | --- |
| [`skills/skisse-til-cad/SKILL.md`](skills/skisse-til-cad/SKILL.md) | Arbeidsgangen frå bilete til montering |
| [`references/tripo-bruk.md`](skills/skisse-til-cad/references/tripo-bruk.md) | Korleis Tripo bør brukast. Kontrollert mot heile v3- og v2-dokumentasjonen og tripo-cli 0.7.2, med kostnad og grenser per steg |
| [`references/tripo-og-cad.md`](skills/skisse-til-cad/references/tripo-og-cad.md) | Frå Tripo-mesh til mekanisk CAD og eksport |
| [`references/ikea-assembly.md`](skills/skisse-til-cad/references/ikea-assembly.md) | Stil og sidefølgje for IKEA-liknande monteringsrettleiingar |
| [`scripts/`](skills/skisse-til-cad/scripts) | Tripo v3-klient (`tripo.py`, `kjor.py`) og `tripo_docs.sh`, som hentar heile Tripo-dokumentasjonen på nytt |

## Installering

**Claude Code** (plugin):

```bash
claude plugin marketplace add lukketsvane/skisse-til-cad
claude plugin install skisse-til-cad@formnerd
```

Eller inne i ei økt: `/plugin marketplace add lukketsvane/skisse-til-cad` og `/plugin install skisse-til-cad@formnerd`. Utan SSH-nøkkel til GitHub: set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.

**Andre agentar** ([skills-CLI](https://github.com/vercel-labs/skills)):

```bash
npx skills add lukketsvane/skisse-til-cad
```

**Codex:** kopier `skills/skisse-til-cad` til `.agents/skills/` i prosjektet ditt.

**claude.ai:** last ned [`dist/skisse-til-cad.skill`](dist/skisse-til-cad.skill) og last han opp under Settings → Capabilities → Skills.

## Krav

Tripo-kall krev `TRIPO_API_KEY` i miljøet. Skillen tilrår den offisielle `tripo-cli@0.7.2` (Node 20+), og `scripts/` krev Python med `requests`. Skillen opprettar aldri betalte Tripo-jobbar utan at brukaren har godkjent kostnaden.

## Lisens

[Apache-2.0](LICENSE).

## Opphav

Utvikla i [lukketsvane/formnerd](https://github.com/lukketsvane/formnerd), der dei gjennomførte prosjekta skillen viser til ligg (A1, A2, A4 og Entropi).
