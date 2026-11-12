# Verified Jev interface (17 October 2026)

## Authority and version

Use TypeSafe's `api.typesafe.ai`, linked from [typesafe.ai](https://typesafe.ai/). The supplied [jevtypesafeai.com page](https://www.jevtypesafeai.com/jev/ai-agent) identifies itself as an independent CODEFASHION TECH LTD playground, explicitly unaffiliated with TypeSafe. Its endpoint, key prefix and pricing are not used here.

The [official model page](https://docs.typesafe.ai/models) lists `jev-1.14.0`, released **14 October 2026**, as newest; `jev-preview` resolves to it, while `jev-latest` remains `jev-1.13.0`. Pin `jev-1.14.0` and reject a response with a different `model`. Price is **$0.042 per million input tokens**, output free. Context limits are 64k per request/32k per question by default; rate limits are organization-specific requests/second and tokens/second, visible in the console. A model list need not enumerate versioned IDs. The page's “Text” input table is incomplete relative to the dedicated image documentation, so record this documentation inconsistency rather than disabling documented image support.

## Three different outputs

| Question | Request | Response used |
|---|---|---|
| Visible presence | `type: noul` with yes/no instructions | `noul`: yes probability; no separate confidence |
| Match-count category | `type: choice`, criteria `none`, `one`, `several` | `choice`, `probabilities`, `confidence`; use probability of **one**, not confidence in whichever option wins |
| Localization | `type: box`, instructions, no criteria | `box` with left/top/right/bottom fractions and `confidence` |

[Noul](https://docs.typesafe.ai/primitives/noul) is probabilistic yes/no, not a Boolean. [Choice](https://docs.typesafe.ai/primitives/choice) is a caller-defined categorical question, not a special native exact-count primitive. [Confidence](https://docs.typesafe.ai/confidence) documents Choice confidence as `(p_max - 1/n)/(1 - 1/n)`; this is distinct from correctness probability. No independent-presence/uniqueness assumption is justified.

The [Box page](https://docs.typesafe.ai/primitives/box) specifies top-left origin, coordinates in [0,1], positive box dimensions, and one box per question. **Box always returns a box, including for absent targets.** The page already recommends a presence Noul and a `none/one/several` Choice beside Box. Therefore this combination is not a new method. Box confidence is described as certainty, with no recommended threshold or documented event such as `P(IoU ≥ .5)`; that interpretation requires empirical calibration. Image/Box functionality is explicitly experimental (“Dreamer-ready”); schema and behavior can change.

## Transport, limits and errors

[Images](https://docs.typesafe.ai/images): POST `/v1/systemone`, Bearer API key and `TypeSafe-Danger-Zone-Images: true`. Place each image in `assets`, reference its UUID once in `state`, then refer to state paths in questions. Multipart is recommended; this client implements the also-documented JSON `data_base64` plus lowercase `format`. Still PNG/JPEG only, **280–1568 pixels each side**, ≤16 MiB/image, ≤32 MiB body, processed images and expanded request limits. No automatic server resizing. Repeated image references expand tokens/size; shared state avoids duplication. Image tokens use the ordinary input price and are included in usage.

[API reference](https://docs.typesafe.ai/api) returns `model`, `answers`, `usage.input_tokens`, `usage.output_tokens`. Errors have JSON bodies, but no single fixed error-object schema is promised here: retain the entire body. Documented codes include 400 invalid request/context/image, 401 credentials, 413 size, 415 compression, 422 validation, 429 rate limit, 529 overload. The client records each attempt, raw response, resolved version, timing, usage and list-price cost estimate. Transport exceptions and invalid responses fail closed. Retries default to zero; explicit limited retries handle 429/529 and selected server errors, respecting numeric Retry-After. Unknown retry timing stops rather than guessing. Unknown billing on failures remains null, not zero.

## Execution status and implementation scope

`TYPESAFE_API_KEY` presence-only check returned **false**. No credential value was read into a report; **zero real Jev API calls were made**. Live schema confirmation and all Jev performance results remain **NOT RUN**. `src/jev_client.py` and `src/parse_outputs.py` implement the documented interface; `tests/test_jev_interface.py` uses explicit hand-authored schema fixtures and mocked transport, never fabricated model predictions. Successful local tests establish parser/client behavior only. Input validation currently propagates an exception before a network attempt; the pilot runner must record that local validation failure as an excluded/failed case, with zero calls.

Required access: set `TYPESAFE_API_KEY` privately to a valid TypeSafe console key with applicable account credit/access. Account status and effective limits cannot be verified without it. Run one smoke request, inspect the actual returned schema/version, then freeze prompts before a pilot. Do not reuse the documentation's example probabilities as experimental observations.
