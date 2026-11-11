# CitCom data space rulebook — v0.1 (proposal)

**Status:** proposal written by the VRAIN team (UPV) on 2026-11-11. Nobody in CitCom
has approved it yet. Nothing here binds anyone until the governance authority (§2)
adopts it. Items marked **DECISION** need someone with authority to decide them.

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
in CitCom.ai share urban data and AI services in a trusted and controlled way. Today
that means the València data space: Ajuntament de València and VRAIN (UPV).

**R1.2** This rulebook covers the participants, the data and services offered through the
data space connectors and the CitCom marketplace, and the terms under which they are
used. It does not cover data exchanged outside the data space, even between the same
participants.

**R1.3** The data space is a **pilot** (testing and experimentation facility). It does not
promise production-grade availability (§10).

## 2. Governance

**R2.1** The **governance authority** adopts and changes this rulebook, admits and
excludes participants, and settles disputes. **DECISION:** who it is. Proposal: the
CitCom.ai partners operating the data space, under the existing consortium agreement,
with no new legal entity. That is a cooperation-agreement form in DSSC terms.

**R2.2** The **operator** runs the shared services: trust anchor (trusted issuers
registry), onboarding portal, marketplace and documentation. It acts on behalf of the
governance authority. Today: VRAIN (UPV).

**R2.3** Changes: a change to this rulebook is a pull request to this repository,
approved by the governance authority. Each adopted version is tagged (`rulebook-vX.Y`)
and announced to participants at least **30 days** before it takes effect, unless it
fixes a security problem. **DECISION:** notice period.

**R2.4** Policies follow the rulebook. The access policies deployed on the connectors
are generated from this repository (`offers/` + `classes/`). A connector policy written
by hand that this repository does not produce is a breach of §8 *(audited:
`rulebook_gen check`)*.

## 3. Participants and roles

| Role | Does | Example |
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

**R4.3** On leaving or exclusion, the operator removes its issuer from the trusted issuers
registry. Each provider removes it from its trusted issuers list and deletes its access
policies within **5 working days** *(audited)*. **Gap:** this is manual today.
contract-management does not revoke anything when an order is cancelled; to be
checked (PLAN, phase 3).

**R4.4** Leaving does not end obligations that apply to data already received, such as
attribution, confidentiality or deletion (§7) *(contractual)*.

## 5. Agreements

Following the DSSC contractual framework:

| DSSC category | In this data space |
|---|---|
| Founding agreement | **DECISION** (R2.1). Proposal: the CitCom.ai consortium agreement. |
| Accession agreement | Acceptance of this rulebook at onboarding (R4.1). |
| General terms and conditions | This rulebook. |
| Data product contract | The marketplace **order** of an offering. Its terms are those of the offering's policy class (§7) plus anything the offering adds in its description. |
| Licence | Fixed by the policy class. Providers choose a class and do not write their own (R7.1). |

**R5.1** An order is completed only by the provider (or, for free offers, automatically).
Completing it creates the consumer's access *(enforced: contract-management adds the
consumer to the provider's trusted issuers list and instantiates the class policy bound
to the consumer's DID)*.

**R5.2** Every offering states its policy class and links to it from its description
*(audited)*.

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

Current datasets, checked against the VLCi open data portal (opendata.vlci.valencia.es)
on 2026-11-11:

| Offer | Source on the portal | Category |
|---|---|---|
| traffic-state | `estat-transit-temps-real` (CC BY 4.0) | Open |
| traffic-flow | `intensitat-transit-trams` / traffic measurement points (CC BY 4.0) | Open |
| air-quality | `estacions-contaminacio-atmosferiques` (CC BY 4.0) | Open |
| waste-containers | Container locations are open (CC BY 4.0). Fill levels are **not** on the portal. | Shared (**DECISION**, Ajuntament) |

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

**R10.2** No participant is liable to another for damages caused by unavailability or by
errors in the data, except for wilful misconduct or gross negligence. **DECISION:** to
be checked by the partners' legal services.

## 11. Breaches and disputes

**R11.1** Parties first try to settle disputes between themselves. If they cannot, the
governance authority decides.

**R11.2** Possible measures, in order: warning, suspension of access to the affected
offerings, exclusion (R4.2).

---

## Open decisions (summary)

1. Governance authority and founding agreement (R2.1, §5).
2. Notice period for changes (R2.3).
3. Category of the waste-container fill levels (§6). The Ajuntament decides.
4. Liability clause (R10.2): legal services.
5. Automatic revocation when an order ends or a participant leaves (R4.3): technical,
   to be investigated.
