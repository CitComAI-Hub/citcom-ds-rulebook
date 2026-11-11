# Implementation profiles

How each kind of connector meets the technology-neutral rules of the rulebook, mainly
R8.5 (an offering reaches only the data it defines) and R8.6 (minimum security
baseline). The rulebook says *what* must hold; this page says *how* for each stack.
A participant with a different stack adds its own profile here before its offerings
are published.

## Background: why the request is not enough

The policy engine (odrl-pap → OPA) decides **before** the request reaches the data, so it
can only check what the consumer wrote in the request: the path, the `?type=` parameter,
the type inside an `urn:ngsi-ld:<type>:<id>` id. Any part of the data's location that a
policy does not check, and that the consumer can choose, must be fixed by the
connector. Otherwise an offering for one type reaches every collection that holds that
type. See the audit of 2026-11-11 (dataspace-on-upv, findings 1 and 2).

## NGSI-v2 platform through Lepus (townhall-vlc, VLCi)

VLCi is NGSI-v2. Lepus translates NGSI-LD requests to it: the NGSI-LD tenant
(`NGSILD-Tenant`) becomes `Fiware-Service`, and the NGSI-LD scope filter (`scopeQ`)
becomes `Fiware-ServicePath`. VLCi publishes one collection per servicePath, and the
same entity type can live in several servicePaths (AirQualityObserved is in
`/calidad_aire_vlc` and in the internal `/calidad_aire_emt_vlc`).

| Requirement | How it is met |
|---|---|
| R8.5: only the offered collection | Lepus serves only the servicePaths listed for each type in its map (`lib/entityServicePaths.js` in CitComAI-Hub/lepus, v1.4). `scopeQ` naming any other one gets 400. A new servicePath in VLCi is not served until it is added to the map on purpose. |
| R8.5: only the offered type | Lepus makes Orion enforce the type the policy checked, including the one written in an entity id (v1.3). |
| R8.6: no consumer-chosen tenant | The gateway removes `NGSILD-Tenant`, `Fiware-Service` and `Fiware-ServicePath`; Lepus uses its default tenant. |
| R8.6: trusted values removed | The gateway removes `X-Stripped-Path`, which odrl-pap would otherwise take as the request path. |
| R8.6: only the needed endpoints | Data routes match only `/ngsi-ld/v1/entities` and `/ngsi-ld/v1/entities/*`, GET only. |

If two collections of the same type must become **different** offerings (or one of them
stays internal while the other is offered), a type-based policy cannot tell them apart.
Then each collection gets its own gateway path (for example
`/lepus/air-quality-emt/ngsi-ld/…`), the gateway fixes the collection server side, and
the policy checks that path.

## Native NGSI-LD broker (Orion-LD, Scorpio)

| Requirement | How it is met |
|---|---|
| R8.5: only the offered collection | Keep each offered collection in its own tenant, or use scopes and make sure the consumer cannot reach a scope or tenant that is not offered (the gateway fixes or removes `NGSILD-Tenant`; `scopeQ` is restricted or the broker holds only offered data). |
| R8.6 | Same gateway rules as above: GET only, entity endpoints only, `X-Stripped-Path` and tenant headers removed. |

Today the townhall-vlc Orion-LD (traffic-state) and the vrain Scorpio hold only offered
data in their default tenant.
