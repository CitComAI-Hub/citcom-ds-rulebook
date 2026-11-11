# CitCom data space rulebook — v0.2 (draft)

**Status:** draft written by the VRAIN team (UPV). The first decisions were taken on
2026-11-11 and are listed in the [decisions log](#decisions-log). The rulebook is not
binding until the governance authority (R2.1) adopts a tagged version. Items marked
**DECISION** are still open.

The structure follows the DSSC Blueprint v2.0: governance (organisational form,
participant management) and legal (regulatory compliance, contractual framework).
It is cut down to what a pilot needs.

Every rule has an id and one of three kinds:

| Kind | Meaning |
|---|---|
| **enforced** | Checked on every request by the connectors (APISIX + OPA, from ODRL). See [enforcement-capabilities](../docs/enforcement-capabilities.md). |
| **audited** | Not blocked, but logged or checkable afterwards. Breaking it has consequences under §11. |
| **contractual** | An obligation of the parties. No system checks it. |

A rule is only labelled *enforced* if the code in this repo generates the policy
that enforces it.

---

## 1. Purpose and scope

**R1.1** The CitCom data space lets cities, research centres and companies taking part
in CitCom.ai share urban data and AI services in a trusted and controlled way. It is
open to any organisation that meets §4. The first participants (early adopters) are
the Ajuntament de València and VRAIN (UPV), but no rule depends on who they are: they
have the same rights and duties as any later participant, except for VRAIN's role as
operator (R2.2, R2.5).

**R1.2** This rulebook covers the participants, the data and services offered through the
data space connectors and the CitCom marketplace, and the terms under which they are
used. It does not cover data exchanged outside the data space, even between the same
participants.

**R1.3** The data space is a **pilot** (testing and experimentation facility). It does not
promise production-grade availability (§10).

## 2. Governance

**R2.1** The **governance authority** is the **CitCom.ai consortium**, acting under its
consortium agreement, with no new legal entity (a cooperation agreement in DSSC terms).
It adopts and changes this rulebook, admits and excludes participants, and settles
disputes.

**R2.2** The **operator** runs the shared services: trust anchor (trusted issuers
registry), onboarding portal, marketplace and documentation. It acts on behalf of the
governance authority. The operator is **VRAIN (UPV)**. In practice VRAIN controls the
trust anchor, so it decides technically who can take part (R2.5 limits that power).

**R2.3** Changes: a change to this rulebook is a pull request to this repository,
approved by the governance authority. Each adopted version is tagged (`rulebook-vX.Y`)
and announced to participants at least **30 days** before it takes effect, unless it
fixes a security problem.

**R2.4** Policies follow the rulebook. The access policies deployed on the connectors
are generated from this repository (`offers/` + `classes/`). A connector policy written
by hand that this repository does not produce is a breach of §8 *(audited:
`rulebook_gen check`)*.

**R2.5** Operator neutrality. VRAIN is both the operator and a participant. As operator:
- it adds or removes issuers in the trust anchor only to carry out a decision of the
  governance authority, or R4.1 / R4.3 / R9.1;
- it treats every participant the same way, including itself;
- it does not use its position to access other participants' data or services;
- it keeps a record of every change to the trust anchor (who, when, why) and shares it
  with the governance authority on request *(audited: database audit log on the trust
  anchor, plus portal history; to be set up, see
  [revocation-and-trust-anchor](../docs/revocation-and-trust-anchor.md))*;
- changes it makes by hand, outside the onboarding portal, are only for early adopters
  or emergencies, and are written down in `trust-anchor-changes.md` in this repository.

## 3. Participants and roles

| Role | Does | Example (early adopters) |
|---|---|---|
| **Data provider** | Publishes datasets through its connector and offers them in the marketplace | Ajuntament de València |
| **Service provider** | Publishes services (web apps, APIs, AI models) through its connector | VRAIN (MIAIS, container location, tourism) |
| **Consumer** | Acquires offers and uses data or services, with its machines (MachineCredential) or its people (ServiceCredential) | VRAIN reading waste containers |
| **Operator** | See R2.2 | VRAIN |

A participant can hold several roles.

**R3.1** Every participant is an organisation, identified by a `did:web` (its own, or one
given by the onboarding portal). Individuals take part only on behalf of an
organisation *(enforced: credentials are issued by the organisation's Keycloak and
policies bind to its DID)*.

**R3.2** Each participant names a **contact** for operations and security incidents
*(contractual)*.

**R3.3** A participant answers for its users and machines. It only issues credentials to
people and services it controls, and revokes them when that stops being true
*(contractual)*.

## 4. Joining and leaving

**R4.1** To join, an organisation registers through the onboarding portal and accepts this
rulebook. That acceptance is the **accession agreement**. The governance authority (or
the operator, by delegation) approves it, and the organisation's issuer is then added
to the trusted issuers registry *(enforced: credentials of non-registered issuers are
rejected by every verifier)*.

**R4.2** A participant can leave at any time by asking the operator. The governance
authority can exclude a participant that seriously or repeatedly breaks this rulebook
(§11).

**R4.3** On leaving or exclusion, the operator removes the participant from the trust
anchor (onboarding portal: registration out of `active`) *(enforced: from then on every
verifier rejects its credentials)*. Within **5 working days**, its orders as a consumer
are set to `cancelled`, which removes its entries from the providers' trusted issuers
lists and its access policies *(enforced by contract-management once cancelled;
audited)*. Details: [revocation-and-trust-anchor](../docs/revocation-and-trust-anchor.md).

**R4.5** A single purchase ends by setting its order to `cancelled`, either by the
consumer or by the provider (for a breach, §11). Access to that offering is revoked
automatically and nothing else is affected *(enforced)*. Orders do not expire on their
own. Time-limited access needs a class with an end date.

**R4.4** Leaving does not end obligations that apply to data already received, such as
attribution, confidentiality or deletion (§7) *(contractual)*.

## 5. Agreements

Following the DSSC contractual framework:

| DSSC category | In this data space |
|---|---|
| Founding agreement | The CitCom.ai consortium agreement (R2.1). |
| Accession agreement | Acceptance of this rulebook at onboarding (R4.1). |
| General terms and conditions | This rulebook. |
| Data product contract | The marketplace **order** of an offering. Its terms are those of the offering's policy class (§7) plus the provider's additional requirements (R5.3). |
| Licence | Fixed by the policy class. Providers choose a class and do not write their own (R7.1). |

**R5.1** An order is completed only by the provider (or, for free offers, automatically).
Completing it creates the consumer's access *(enforced: contract-management adds the
consumer to the provider's trusted issuers list and instantiates the class policy bound
to the consumer's DID)*.

**R5.2** Every offering states its policy class and links to it from its description
*(audited)*.

**R5.3** A provider can set **additional requirements** for an offering, for example
civil liability insurance, a signed agreement or a declared purpose of use. They must:
- be stated in the offering before anyone acquires it;
- not contradict this rulebook;
- apply equally to every consumer of that offering.

The provider checks them before completing the order *(contractual)*. Requirements
that can be expressed as a credential claim (e.g. an insurance attestation) can later
be enforced with a dedicated class (`ovc:leftOperand`, see PLAN).

## 6. Data categories

**R6.1** Each dataset falls into one category, chosen by its provider:

| Category | What | Allowed in v0.1 |
|---|---|---|
| **Open** | Already published as open data (e.g. under CC BY 4.0) | Yes. The data space adds service (NGSI-LD, Smart Data Models, a verified provider), not restrictions (R6.2). |
| **Shared** | Not public, but not personal and not confidential to third parties | Yes |
| **Confidential** | Trade secrets, security-relevant infrastructure details | No, until rules for it are agreed |
| **Personal** | Personal data (GDPR) | No. Any dataset that may contain personal data must be anonymised before it is offered. |

**R6.2** Open data stays open. The data space cannot add usage restrictions to data whose
licence already grants them (Open Data Directive; for mobility and environment data,
also the High-Value Datasets regulation (EU) 2023/138). It can only ask consumers to
identify themselves and accept the service terms of the connector *(contractual)*.

**R6.3** A provider is responsible for having the right to offer each dataset, and for
its category being correct *(contractual)*.

**R6.4** The category depends on **where the data comes from**, not on whether a similar
dataset exists elsewhere:
- data the data space takes from a provider's **public endpoint** is **Open**;
- data it takes from a provider's **internal platform** is **Shared**. For the
  Ajuntament de València that is the VLCi platform, reached through Lepus. A similar
  dataset may be on the open data portal, but this feed (frequency, attributes,
  history) is not the public one.

*Provisional:* the Ajuntament and VRAIN are still agreeing on this. Until they do, R6.4
applies.

Current datasets (2026-11-11):

| Offer | Source | Category |
|---|---|---|
| traffic-state | Public endpoint (open data `estat-transit-temps-real`, CC BY 4.0), loaded by the provider's ingestion | Open |
| traffic-flow | VLCi platform, through Lepus | Shared |
| air-quality | VLCi platform, through Lepus | Shared |
| waste-containers | VLCi platform, through Lepus | Shared |

## 7. Usage terms (policy classes)

**R7.1** Every offering uses one of the classes below. A new class is a change to this
rulebook (R2.3).

| Class | For | Who | What | Licence and duties |
|---|---|---|---|---|
| [`open-data`](../classes/open-data.md) | Open datasets | Any participant that acquires it (free) | Read (GET) one entity type | The source's open licence (CC BY 4.0: attribute the provider). No extra restrictions (R6.2). |
| [`dataset-access`](../classes/dataset-access.md) | Shared datasets | The acquiring organisation's machines | Read (GET) one entity type | Use within CitCom activities only; do not share raw data outside the data space; attribute the provider; delete on request at the end of the order. |
| [`service-access`](../classes/service-access.md) | Services | The acquiring organisation's users, given the service role by their organisation | The service under its path | The service's terms of use (in its offering). Inputs the user gives the service are not reused for anything else. |

**R7.2** What each class *enforces* is listed in its file. Everything else in the table is
*contractual*. In particular, attribution, "within CitCom" and deletion cannot be
checked by the connectors.

**R7.3** Consumers access data **read only**. Writing to a provider's data is not possible
through any offering *(enforced: `odrl:read` and GET-only routes)*.

**R7.4** Results derived from data (aggregates, models, maps) belong to whoever produces
them, but must attribute the source and must not let anyone rebuild the raw data of a
*shared* dataset *(contractual)*.

## 8. Technical rules

**R8.1** Data is offered as NGSI-LD, following Smart Data Models where one exists.

**R8.2** Identity and access use the CitCom trust framework: `did:web`, verifiable
credentials (OID4VCI / OID4VP), the trust anchor's registry, and each provider's
trusted issuers list *(enforced)*.

**R8.3** Each connector exposes only what its offerings need, and its gateway routes must
not allow more than the classes allow (for example, no write methods on data routes)
*(audited: route review in dataspace-on-upv)*.

**R8.4** Access policies are produced by this repository and deployed through the
marketplace (R2.4).

## 9. Security and incidents

**R9.1** A participant that finds a security incident or a vulnerability affecting the data
space tells the operator and the affected providers within **72 hours** *(contractual)*.
The operator can suspend any access while it is handled.

**R9.2** Credentials and tokens are not shared between organisations *(partly enforced:
policies bind to the issuing organisation)*.

## 10. Availability and liability

**R10.1** Data and services are offered **as is**, on a best-effort basis, without
availability or quality guarantees, because this is a pilot. An offering can promise
more in its description.

**R10.2** **DECISION (sensitive, in progress):** liability between participants is not
settled. The Ajuntament, as a provider like any other, is likely to ask consumers of
its Lepus data for civil liability insurance and other conditions (R5.3). The general
clause is being worked out with the Ajuntament and the partners' legal services. Until
then there is no general liability clause: R10.1 and each offering's additional
requirements apply.

## 11. Breaches and disputes

**R11.1** Parties first try to settle disputes between themselves. If they cannot, the
governance authority decides.

**R11.2** Possible measures, in order: warning, suspension of access to the affected
offerings, exclusion (R4.2).

---

## Decisions log

| Date | Decision | Rules |
|---|---|---|
| 2026-11-11 | Governance authority: the CitCom.ai consortium, under its consortium agreement. Operator: VRAIN, which controls the trust anchor. | R2.1, R2.2, R2.5, §5 |
| 2026-11-11 | Notice period for rulebook changes: 30 days (security fixes exempt). | R2.3 |
| 2026-11-11 | *Provisional:* data from public endpoints is Open; data from the provider's internal platform (Lepus) is Shared, within the data space only. | R6.4 |

## Open decisions

1. Final agreement with the Ajuntament on R6.4 (category by source).
2. Liability between participants and the Ajuntament's requirements for its Lepus data
   (insurance, others) (R10.2, R5.3). Sensitive, in progress.
3. ~~Automatic revocation (R4.3)~~: investigated 2026-11-11. It exists per order
   (cancel the order) and per participant (deactivate in the portal). R4.3 and R4.5
   are rewritten. Verified end to end on 2026-11-11.
4. Trust-anchor change record (R2.5): proposal in
   [revocation-and-trust-anchor](../docs/revocation-and-trust-anchor.md), to implement.
