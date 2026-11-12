# Technical annex

How the software of the data space enforces the rulebook. For the people who run a
connector or maintain this repository. The rules themselves are in
[`rulebook/`](../rulebook/README.md).

- [enforcement-capabilities](enforcement-capabilities.md): what the FIWARE access-policy
  stack (odrl-pap + OPA) can and cannot enforce, and what the policy tests check.
- [implementation-profiles](implementation-profiles.md): how each kind of connector
  (NGSI-v2 platform behind Lepus, native NGSI-LD broker, web services) meets §8.
- [revocation-and-trust-anchor](revocation-and-trust-anchor.md): how access is
  revoked, and how changes to the trust anchor are recorded.

Nothing here names a participant's datasets or deployment. Those go in each
participant's conformance evidence (rulebook R8.7).
