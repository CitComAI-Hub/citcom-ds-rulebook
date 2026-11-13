# CitCom data space rulebook — v0.3 (draft)

**Status:** draft written by the VRAIN team (UPV). The first decisions were taken on
2026-11-11 and are listed in the [decisions log](#decisions-log). The rulebook is not
binding until the governance authority (R2.1) adopts a tagged version. Items marked
**DECISION** are still open.

The structure follows the DSSC Blueprint v3.0 (the final version of the DSSC project):
governance (organisational form and governance authority, participation management)
and legal (regulatory compliance, contractual framework). It is cut down to what a
pilot needs.

## How to read this rulebook

This document is for every participant, technical or not. It says **what** holds in
the data space, not how the software does it. Three other places complete it:

- **Policy classes** ([`classes/`](../classes/)): the terms of use of each kind of
  offering. Every offering in the marketplace links to its class.
- **Technical annex** ([`docs/`](../docs/)): how the software enforces these rules,
  for the people who run a connector.
- **Each participant's conformance evidence**: how its own connector and data meet
  §8, kept by the participant and reviewed by the operator.
- **Accession agreement** ([`agreements/`](../agreements/accession-agreement.md)): what
  an organisation signs to join (R4.1).

Every rule has an id and one of three kinds:

| Kind | Meaning |
|---|---|
| **enforced** | The data space's software checks it on every access and blocks what breaks it. |
| **audited** | Not blocked, but recorded or checkable afterwards. Breaking it has consequences under §11. |
| **contractual** | An obligation of the parties. No system checks it. |

A rule is only labelled *enforced* if the software really blocks what breaks it.

---

## 1. Purpose and scope

**R1.1** The CitCom data space lets cities, research centres and companies taking part
in CitCom.ai share urban data and AI services in a trusted and controlled way. It is
open to any organisation that meets §4. The first participants (early adopters) have
the same rights and duties as any later participant. The only exception is the
operator's role (R2.2, R2.5).

**R1.2** This rulebook covers the participants, the data and services offered through the
data space and its marketplace, and the terms under which they are used. It does not
cover data exchanged outside the data space, even between the same participants.

**R1.3** The data space is a **pilot** (testing and experimentation facility). It does not
promise production-grade availability (§10).

## 2. Governance

**R2.1** The **governance authority** is the **CitCom.ai consortium**, acting under its
consortium agreement, with no new legal entity (a cooperation agreement in DSSC terms).
It adopts and changes this rulebook, admits and excludes participants, and settles
disputes. The CitCom.ai partners are the data space's **members**: they govern it
through the consortium. Any other organisation can be a **participant** (§4) without
being a member. The consortium's own internal rules (how it decides, votes, signs) are
in its consortium agreement, not in this rulebook.

**R2.2** The **operator** runs the shared services: the trust anchor (the list of
organisations the data space trusts), the onboarding portal, the marketplace and the
documentation. It acts on behalf of the governance authority. The operator is
**VRAIN (UPV)**. In practice the operator controls the trust anchor, so it decides
technically who can take part (R2.5 limits that power).

**R2.3** Changes: a change to this rulebook is proposed in this repository and approved
by the governance authority. Each adopted version is tagged (`rulebook-vX.Y`) and
announced to participants at least **30 days** before it takes effect, unless it fixes
a security problem.

**R2.4** Policies follow the rulebook. The access rules running on the connectors are
generated from this repository. An access rule written by hand that this repository
does not produce is a breach of §8 *(audited: two daily automatic checks, one
between this repository and the operator's deployment, one of every offering published
in the marketplace against its class)*.

**R2.5** Operator neutrality. The operator is also a participant. As operator:
- it adds or removes organisations in the trust anchor only to carry out a decision of
  the governance authority, or R4.1 / R4.3 / R9.1;
- it treats every participant the same way, including itself;
- it does not use its position to access other participants' data or services;
- it keeps a record of every change to the trust anchor (who, when, why) and shares it
  with the governance authority on request *(audited: the trust anchor and the
  onboarding portal keep a history of changes)*;
- changes it makes by hand, outside the onboarding portal, are only for early adopters
  or emergencies, and are written down in
  [`trust-anchor-changes.md`](../trust-anchor-changes.md).

## 3. Participants and roles

| Role | Does | Example |
|---|---|---|
| **Data provider** | Publishes datasets and offers them in the marketplace | A city council offering sensor data |
| **Service provider** | Publishes services (web apps, APIs, AI models) and offers them in the marketplace | A research centre offering a route-planning tool |
| **Consumer** (data recipient or service user) | Acquires offerings and uses the data or services, with its software (machine access) or its people (user access) | A company that reads a dataset from its own application |
| **Data rights holder** | Holds rights over data that a provider offers, and can set conditions on its use. It need not be a participant. | The owner of a sensor network whose data a city offers |
| **Operator** | Provides the shared (enabling) services, see R2.2 | |

A participant can hold several roles. The DSSC Blueprint calls the consumer of data a
*data recipient*; this rulebook says *consumer* for both data and services.

**R3.1** Every participant is an organisation, with a digital identity of its own (or one
given by the onboarding portal). Individuals take part only on behalf of an
organisation *(enforced: each organisation issues the credentials of its own people
and software, and every access is tied to the organisation)*.

**R3.2** Each participant names a **contact** for operations and security incidents
*(contractual)*.

**R3.3** A participant answers for its users and machines. It only issues credentials to
people and software it controls, and revokes them when that stops being true
*(contractual)*.

**R3.4** Access roles. Each offering names a role. The buying organisation gives that
role to the people or software it allows to use what it bought, and only they get
access *(enforced: access needs both the organisation's credential and the role)*.
The role never extends access beyond what the organisation bought (R5.1).
- Each **service** has its own role, so the buyer chooses who uses each service.
- All **datasets** share one role for software access. Software that holds it can read
  every dataset its organisation bought.

The role names are in each class (§7).

## 4. Joining and leaving

**R4.1** To join, an organisation registers through the onboarding portal and its legal
representative signs the [**accession agreement**](../agreements/accession-agreement.md):
it says which roles the organisation intends to take (§3) and accepts this rulebook as
in force at each moment (R2.3). The governance authority (or the operator, by
delegation) approves the registration, which concludes the agreement, and the
organisation is then added to the trust anchor *(enforced:
credentials of organisations that are not in the trust anchor are rejected
everywhere)*.

Admission criteria:
- it is an organisation, able to issue credentials to its own people and software
  (R3.1, R3.3);
- it names a contact (R3.2);
- to publish offerings, it meets §8 and keeps the conformance evidence of R8.7.

**R4.2** A participant can leave at any time by asking the operator. The governance
authority can exclude a participant that seriously or repeatedly breaks this rulebook
(§11).

**R4.3** On leaving or exclusion, the operator removes the participant from the trust
anchor *(enforced: from then on its credentials are rejected everywhere)*. Within
**5 working days**, its purchases as a consumer are cancelled, which also removes the
access each of them gave *(enforced once cancelled; audited)*.

**R4.4** Leaving does not end obligations that apply to data already received, such as
attribution, confidentiality or deletion (§7) *(contractual)*.

**R4.5** A single purchase ends when its order is cancelled, by the consumer or by the
provider (for a breach, §11). The access it gave is removed automatically and nothing
else is affected *(enforced)*. Orders do not expire on their own: time-limited access
needs a class with an end date.

**R4.6** The applicant is told the decision on its registration. A denial states the
reasons, with reference to the criteria of R4.1 *(audited: the onboarding portal
records every decision and its reason)*.

**R4.7** Participants keep meeting the criteria while they take part. The operator
checks it through the conformity scheme (R8.7) and the daily comparison of access
rules (R2.4). A participant that stops meeting them is handled under §11.

## 5. Agreements

The DSSC contractual framework sorts agreements into three categories:
**institutional** agreements bind everyone in the data space, **data-sharing**
agreements bind only the parties to one data exchange, and **services** agreements
cover services provided in or to the data space.

| Category | Agreement | In this data space |
|---|---|---|
| Institutional | Founding agreement | The CitCom.ai consortium agreement (R2.1). |
| Institutional | Accession agreement | The [accession agreement](../agreements/accession-agreement.md), signed at onboarding: it accepts this rulebook as in force at each moment (R4.1). |
| Institutional | General terms and conditions | This rulebook, including the policy classes (§7). |
| Data sharing | Data product contract | The marketplace **order** of a dataset offering, between provider and consumer. Its terms are those of the offering's policy class (§7) plus the provider's additional requirements (R5.3). |
| Services | Value-creation service agreement | The marketplace **order** of a service offering (class `service-access`), between service provider and consumer. Same rules as a data product contract. |
| Services | Enabling services agreement | The operator provides the shared services (R2.2) on behalf of the governance authority. **DECISION:** today only R2.2 and R2.5 cover it, with no written agreement (open decision 10). |

The licence of every offering is fixed by its policy class. Providers choose a class
and do not write their own (R7.1).

**R5.1** An order is completed only by the provider (or, for free offerings,
automatically). Completing it gives the consumer's organisation access to that offering,
and to nothing else *(enforced)*.

**R5.2** Every offering states its policy class and links to it *(audited)*. Its terms
and conditions are generated from the class, so they cannot contradict it. The
marketplace shows them as the offering's "License" and its class as "Policy class".

**R5.3** A provider can set **additional requirements** for an offering, for example
civil liability insurance, a signed agreement or a declared purpose of use. They must:
- be stated in the offering before anyone acquires it;
- not contradict this rulebook;
- apply equally to every consumer of that offering.

The provider checks them before completing the order *(contractual)*. Requirements
that a credential can prove (for example, an insurance certificate) can later be
checked automatically with a dedicated class.

## 6. Data categories

**R6.1** Each dataset falls into one category, chosen by its provider:

| Category | What | Allowed in v0.3 |
|---|---|---|
| **Open** | Already published as open data (e.g. under CC BY 4.0) | Yes. The data space adds service (standard formats, a verified provider), not restrictions (R6.2). |
| **Shared** | Not public, but not personal and not confidential to third parties | Yes |
| **Confidential** | Trade secrets, security-relevant infrastructure details | No, until rules for it are agreed |
| **Personal** | Personal data (GDPR) | No. Any dataset that may contain personal data must be anonymised before it is offered. |

**R6.2** Open data stays open. The data space cannot add usage restrictions to data whose
licence already grants them (Open Data Directive; for mobility and environment data,
also the High-Value Datasets regulation (EU) 2023/138). It can only ask consumers to
identify themselves and accept the service terms of the data space *(contractual)*.

**R6.3** A provider is responsible for having the right to offer each dataset, including
the permission of its data rights holders and any conditions they set, and for its
category being correct *(contractual)*.

**R6.4** The category depends on **where the data comes from**, not on whether a similar
dataset exists elsewhere:
- data the data space takes from a provider's **public source** is **Open**;
- data it takes from a provider's **internal platform** is **Shared**. A similar
  dataset may be on an open data portal, but that feed (frequency, attributes,
  history) is not the public one.

*Provisional:* still being agreed with the first data provider. Until then, R6.4
applies.

Each provider records the category of each of its datasets, and why, in its
conformance evidence (§8).

## 7. Usage terms (policy classes)

**R7.1** Every offering uses one of the classes below. A new class is a change to this
rulebook (R2.3).

| Class | For | Who | What | Licence and duties |
|---|---|---|---|---|
| [`open-data`](../classes/open-data.md) | Open datasets | Any participant that acquires it (free) | Read one dataset | The source's open licence (CC BY 4.0: attribute the provider). No extra restrictions (R6.2). |
| [`dataset-access`](../classes/dataset-access.md) | Shared datasets | The acquiring organisation's software | Read one dataset | Use within CitCom activities only; do not share raw data outside the data space; attribute the provider; delete on request at the end of the order. |
| [`service-access`](../classes/service-access.md) | Services | The people of the acquiring organisation that it authorises | Use one service | The service's terms of use (in its offering). Inputs the user gives the service are not reused for anything else. |

**R7.2** What each class *enforces* is listed in its file. Everything else in the table is
*contractual*. In particular, attribution, "within CitCom" and deletion cannot be
checked by the software.

**R7.3** Consumers access data **read only**. No offering lets anyone change or delete a
provider's data *(enforced)*.

**R7.4** Results derived from data (aggregates, models, maps) belong to whoever produces
them, but must attribute the source and must not let anyone rebuild the raw data of a
*shared* dataset *(contractual)*.

**R7.5** Fair use. Each class sets how many requests a buying organisation can make to
an offering in a time window: 60 per minute for data (`open-data`, `dataset-access`),
600 per minute for services (`service-access`, because a web page makes many requests).
A provider can set a different limit for one of its offerings. Requests over the limit
are refused until the window ends *(enforced: counted per buying organisation, so
logging in again does not reset the count)*.

## 8. Technical rules

The [technical annex](../docs/) explains how each kind of software meets these rules.

**R8.1** Data is offered in the data space's standard format (NGSI-LD) and follows the
common data models for cities (Smart Data Models) where one exists *(audited: the
provider checks its data against the official models)*.

**R8.2** Identity and access use the CitCom trust framework: digital identities and
verifiable credentials, the trust anchor, and each provider's list of the organisations
that bought from it *(enforced)*.

**R8.3** Each connector exposes only what its offerings need, and never allows more than
the classes allow (for example, nobody can write to a provider's data) *(audited: the
operator reviews it)*.

**R8.4** Access rules are produced by this repository and deployed through the
marketplace (R2.4).

**R8.5** Each offering defines precisely the data it covers: what kind of data and what
delimits it within the provider's systems (source, area, collection). The access an
offering gives must not reach data outside that definition, **whatever the consumer
writes in its requests**. Data that is not offered must not be reachable through the
data space, and new data that the provider's systems start publishing is not served
until it is assigned to an offering *(audited)*.

**R8.6** Minimum security baseline for every connector *(audited: the operator reviews
it)*:
- data can only be read, and only the parts the offerings need are exposed (R7.3,
  R8.3);
- an access decision never relies on information the consumer can change, unless the
  system behind the connector checks that same information;
- no test or default accounts, and no shared default passwords or keys;
- software kept at versions without known exploitable vulnerabilities.

**R8.7** Conformity scheme. Each participant keeps **conformance evidence**: how its
connector and data meet §8 (the category of each dataset, the checks it ran and their
results, known non-conformities and their fix). It keeps it up to date. The operator
reviews it **once per provider**, before the participant can publish offerings (it then
gets the provider role in the marketplace), and again after relevant changes to its
connector *(audited)*. Each offering is then published directly: its policies and
terms come from its class (R2.4), so it needs no review of its own. The [technical annex](../docs/) says what each kind of
connector has to show.

**R8.8** Data space registry. Anyone taking part can check the rules and who takes
part: the trust anchor lists the participants, this repository holds the rules, the
policy classes and the conformity scheme, and the marketplace lists the offerings with
their class.

## 9. Security and incidents

**R9.1** A participant that finds a security incident or a vulnerability affecting the data
space tells the operator and the affected providers within **72 hours** *(contractual)*.
The operator can suspend any access while it is handled.

**R9.2** Credentials are not shared between organisations *(partly enforced: access is
tied to the organisation that issued the credential)*.

**R9.3** When the operator learns of a vulnerability in software that several
participants run, it tells every participant that runs it, with the fix or the
mitigation, and reports it privately to the software's maintainers. It does not
publish exploit details before a fix is available *(contractual)*.

## 10. Availability and liability

**R10.1** Data and services are offered **as is**, on a best-effort basis, without
availability or quality guarantees, because this is a pilot. An offering can promise
more in its description.

**R10.2** **DECISION (sensitive, in progress):** liability between participants is not
settled. Providers of shared data are likely to ask their consumers for civil
liability insurance and other conditions (R5.3). The general clause is being worked
out with the first data provider and the partners' legal services. Until then there
is no general liability clause: R10.1 and each offering's additional requirements
apply.

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
| 2026-11-11 | *Provisional:* data from a provider's public source is Open; data from its internal platform is Shared, within the data space only. | R6.4 |
| 2026-11-11 | Offering terms are generated from the class templates, and every offering shows its class ("Policy class"). | R5.2 |
| 2026-11-11 | Open-data offerings do not ban redistribution in their terms. Shared-data offerings keep the terms they had until their provider agrees (open decision 5). | R6.2, R7 |
| 2026-11-12 | An offering reaches only the data it defines, whatever the consumer writes in its requests; minimum security baseline for every connector; shared vulnerabilities are reported to participants and maintainers. | R8.5, R8.6, R9.3 |
| 2026-11-12 | Request limits per buying organisation: 60/min for data, 600/min for services. | R7.5 |
| 2026-11-12 | Service terms state that what users enter is used only to provide the service (clause 8). | R7.1 |
| 2026-11-12 | Structure aligned with the DSSC Blueprint v3.0 (rulebook v0.3): agreements as institutional, data sharing and services; members and participants; data rights holders; admission criteria and reasons for a denial; conformity scheme and data space registry. | R2.1, §3, R4.1, R4.6, R4.7, §5, R6.3, R8.7, R8.8 |
| 2026-11-12 | Access roles: the buyer gives them to its people or software; one role per service, one shared role for software access to datasets. | R3.4 |
| 2026-11-12 | Offerings are published without manual review: their content comes from a class. The operator reviews each provider's connector once, before it gets the provider role, and after relevant changes. | R8.7 |
| 2026-11-12 | The rulebook is generic and readable by non-technical people: no participant's datasets or deployments, no technical detail in the rules. Each participant keeps its conformance evidence. | R6.4, R8.7 |
| 2026-11-13 | Accession agreement of our own, written in this repository (its PDF is generated from it). It refers to the rulebook in force at each moment, not to a version; R2.3 (30-day notice) and the right to leave protect participants. | R4.1, §5 |

## Open decisions

1. Final agreement on R6.4 (category by source) with the first data provider.
2. Liability between participants, and the requirements providers of shared data may
   set (insurance, others) (R10.2, R5.3). Sensitive, in progress.
3. ~~Automatic revocation (R4.3)~~: done 2026-11-11. It works per purchase (cancel the
   order) and per participant (remove it from the trust anchor). Verified end to end.
4. ~~Record of trust-anchor changes (R2.5)~~: done 2026-11-11.
5. Terms of the `dataset-access` offerings: add the class's "use within CitCom
   activities only" and "delete the data on the provider's request when the order
   ends". Waiting for the provider, together with decisions 1 and 2.
6. ~~Terms of the `service-access` offerings~~: done 2026-11-12. Clause 8 of the terms
   says that what users enter is used only to provide the service.
7. R9.3 for the audit of 2026-11-11: report a vulnerability in the access-policy
   software privately to its maintainers, and tell the participants that run their own
   connector. Not done yet.
8. Known non-conformities of the operator's own deployment (default secrets), listed
   in its conformance evidence.
9. ~~What access roles mean~~: done 2026-11-12 (R3.4). The dataset role keeps its
   technical name; renaming it would mean migrating live purchases, so it waits until
   the realms or the onboarding portal change for another reason.
10. Enabling services agreement (§5): a written agreement between the governance
    authority and the operator for the shared services (scope, availability, what
    happens if the operator changes, R2.5 neutrality).
