# Skisse til CAD

A workflow by Iver Finne for sketch → Tripo → segmented model → mechanical CAD → print files → isometric assembly instructions.

## Install the skill

Download the [standalone skill](../../dist/skisse-til-cad-0.1.2.skill) or [portable plugin ZIP, version 0.1.2](../../dist/skisse-til-cad-0.1.2.zip), or copy the `skills/skisse-til-cad` folder into your agent environment's skill directory. Use the download button on GitHub's file page. The `.skill` file is a ZIP archive containing one skill directory. In Codex, the usual user directory is `~/.codex/skills/skisse-til-cad`. Skill upload and plugin installation options depend on the client you use. Restart or reload the client after installation when required.

Invoke `$skisse-til-cad` and attach one selected sketch or reference image. The portable plugin ZIP includes the same skill and its support files. This repository distributes the package publicly; an OpenAI directory listing requires a separate submission and approval. A private ChatGPT plugin link does not install the plugin for other accounts.

## What it does

- Prepare a clear shape reference and preserve the selected design.
- Choose documented Tripo generation, segmentation or mesh-reduction operations.
- Preserve the master and record parameters, task IDs and actual charges.
- Model measured mechanical interfaces in CAD and prepare small fit tests.
- Build final technical assembly illustrations from actual model geometry.

Image generation can provide form and layout drafts. It is not the source of precise final technical diagrams. A generated mesh is not automatically a dimensionally accurate editable CAD solid.

## Tools and accounts

This package contains instructions and references, not a hosted MCP service or a CAD engine. Use your own compatible agent, Tripo account and supported CLI/API access, CAD software, rendering/PDF tools and file storage. External providers may charge for their services. The package includes no payment system, publisher-operated backend, API keys or credentials. ChatGPT Space and Library are used when available; other clients use the project's selected durable output location.

The existing [tool source and requirements](../../verktoy/README.md), including the [Tripo client](../../verktoy/tripo.py) and [job runner](../../verktoy/kjor.py), are available in the same repository. They are separate from the portable instructions package. Keep your own credentials outside source control.

Review the proposed operation and cost before paid Tripo tasks. Failed or rejected output must be reported; a new generation must not be silently substituted for an approved model. Physical fit and printer setup still require verification.

The detailed workflow is written in Nynorsk and includes English tool and API names.

## Version 0.1.2

Includes the latest documented Tripo recipes, a required comparison of the generated form before segmentation, manufacturer-dimension lookup before requesting measurements, reference-based assembly-layout drafts, and portable file delivery. The existing Tripo tools are unchanged by this package release. Package validation does not claim that a new paid generation, CAD build or physical print has been performed.

Source licence: [Apache-2.0](LICENSE).

[Support](SUPPORT.md) · [Privacy](PRIVACY.md) · [Usage terms](TERMS.md)
