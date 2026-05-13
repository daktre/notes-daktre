# **IPH Bengaluru IEC Digital Workflow Blueprint**

## **Aligned to IPH SOPs, ICMR National Ethical Guidelines, and PMU Governance Requirements**

# **1. Purpose**

This document proposes a digital workflow for the IPH Bengaluru Institutional Ethics Committee (IEC). The workflow is designed to:

- align with ICMR National Ethical Guidelines;
- operationalize IPH IEC SOPs;
- integrate PMU-related governance and administrative controls;
- support public health, implementation research, demonstration projects, community-based research, and multicentric studies;
- provide a basis for implementation using modern workflow platforms such as Directus + PostgreSQL, Django, or similar systems.

Written platform-agnostic at the workflow level so that institutional processes remain independent of software choice. And potentially expandable to any otehr institute and for purposes of open documentation. 

# **2. Design Principles**

## **2.1 Institutional Principles**

The system should:

- prioritize participant and participant data protection
- maintain auditability and transparency
- support decentralized and implementation-oriented public health research
- reduce administrative delays
- maintain confidentiality
- support long-term archival and retrieval
- support both academic and programmatic/public health research
- enable institutional governance as well as document storage

## **2.2 Technical Principles**

The platform should:

- be browser-based
- support role-based access control
- support secure file uploads and archival
- maintain  audit trails
- support structured workflows and approvals
- support automated reminders and escalations

# **3. Recommended Technical Architecture**

## **Preferred Stack** (ideated via AI)

| **Layer**               | **Recommended Technology** |
| ----------------------- | -------------------------- |
| Workflow/Admin Platform | Directus                   |
| Database                | PostgreSQL                 |
| Object Storage          | MinIO / S3                 |
| Reverse Proxy           | Caddy / Nginx              |
| Background Jobs         | Redis + Queue              |
| Email                   | SMTP                       |
| Authentication          | Local + SSO-ready          |
| Deployment              | Docker Compose             |

# **4. Core User Roles**

## **4.1 External Roles**

### **Principal Investigator (PI)**

Can:

- create submissions
- upload documents
- respond to IEC queries
- submit amendments
- submit continuing review reports
- submit SAE/protocol deviation reports
- view status of own studies

### **Co-Investigator**

Can:

- collaborate on submissions by approving their participation in the grant
- upload designated documents
- respond to assigned action items


# **5. Internal IEC Roles**

## **5.1 IEC Secretariat**

Operational administrative unit.

Responsibilities:

- intake validation
- completeness screening
- communication with investigators
- scheduling
- agenda generation
- tracking timelines
- archival management
- maintaining audit documentation

System permissions:

- create/edit workflow states
- assign reviewers
- return submissions
- generate meeting agendas
- manage records


## **5.2 Member Secretary**

Responsibilities:

- scientific and ethical triage
- classify review category
- identify primary/secondary reviewers
- authorize expedited review
- oversee minutes and communication
- ensure SOP compliance

## **5.3 Chairperson**

Responsibilities:

- approve agenda
- oversee deliberation
- resolve conflicts of interest
- authorize expedited decisions
- approve final decisions and letters

## **5.4 IEC Members**

Can:

- access assigned protocols
- submit structured reviews
- record conflict of interest declarations
- vote/comment during meetings

## **5.5 External Subject Experts**

Temporary restricted-access role.

Can:

- review assigned protocol
- upload expert comments

Cannot:

- vote
- access unrelated submissions


# **6. PMU Integration Layer**

## **6.1 Rationale**

IPH’s PMU has categorising/admin oversight/approval authority on pre-sub. These require differentiated governance pathways while maintaining ethical oversight.

## **6.2 PMU Research Classification**

The system should classify PMU-linked activities into:

| **Category**                                             | **Example**                         | **IEC Pathway**                               |
| -------------------------------------------------------- | ----------------------------------- | --------------------------------------------- |
| Administrative analytics                                 | Routine programme dashboards        | Exemption or administrative determination     |
| Secondary analysis                                       | De-identified programme data        | Expedited review                              |
| Implementation research                                  | Health systems intervention studies | Full or expedited review depending on risk    |
| Demonstration projects                                   | Pilot district interventions        | Full committee review                         |
| Community interventions                                  | Public health field implementation  | Full review                                   |
| Quality improvement/student projects/internship projects | Internal service improvement        | Administrative screening + possible exemption |


## **6.3 PMU Administrative Clearance Layer**

Before IEC review, PMU may require:

- internal programme clearance by IPH/ADR/ADP
- Mou/collaboration mentioned to be approved by IPH authority
- budgetary approval
- operational feasibility review
- HMSC, FCRA and any other applicable law ccompliance

This should be implemented as a PRE-IEC governance check

## **6.4 PMU Governance Workflow**

### **PMU Pre-Screening Cell**

Role:

- determine whether proposal involves:
    - government datasets, permissions
    - programme operations/Mou?collaborations to be set up
    - district-level implementation & approvals if needed
    - external reporting obligations
    - vulnerable community implications
    - political/administrative sensitivities.

Outputs:

- cleared for IEC submission
- requires programme modification
- requires government/parnter/admin clearannce
- not feasible operationally

This is a governance and implementation review.

# **7. Submission Lifecycle**

# **3A. Authentication and Identity Management**

## **3A.1 Approved Authentication Modes**

The system should enforce authenticated identity-based access. Only the following login pathways to be permitted:

|**Method**|**Eligibility**|
|---|---|
|ORCID OAuth Login|External researchers and collaborators|
|@iphbengaluru.res.in institutional email login|Internal IPH users|


## **3A.2 ORCID Integration**

The platform should integrate with:

ORICID via OAuth2 authentication.

### **Purpose**

This ensures:

- researcher identity;
- standardized PI/Co-I metadata;
- easier multicentric collaboration;
- reduced fake/duplicate accounts.

## **3A.3 Institutional Login Rules**

### **Internal IPH Users**

Users with:

```text
@iphbengaluru.res.in
```

addresses should authenticate using institutional email verification.

Future-ready support should exist for:

- LDAP;
- Google Workspace SSO;
- SAML/OIDC.

## **3A.4 Restricted Account Creation**

The system shall NOT permit anonymous self-registration.
### **Allowed Modes**

| **User Type**           | **Registration Mode** |
| ----------------------- | --------------------- |
| Internal IPH researcher | Institutional email   |
| External collaborator   | ORCID + IEC approval  |
| collaborator            | Invitation-based      |
| IEC Member/PMU          | Admin-created         |

## **3A.5 Account Approval Workflow**

For external users:

```text
ORCID Login
→ Identity Verification
→ Secretariat Review
→ Approval/Rejection
→ Account Activation
```

The Secretariat shall verify:

- institutional affiliation
- legitimacy of collaboration
- role in study

# **3B. SOP Management Layer**

## **3B.1 Rationale**

The IEC platform should not only process submissions but also function as a governance repository. The system should therefore include a structured SOP management module.

## **3B.2 SOP Repository**

The system should maintain version-controlled SOPs including:

|**SOP Category**|
|---|
|Constitution of IEC|
|Conflict of Interest|
|Submission Procedures|
|Full Committee Review|
|Expedited Review|
|Exemption Procedures|
|SAE Handling|
|Protocol Deviations|
|Continuing Review|
|Monitoring Visits|
|Archival|
|Data Confidentiality|
|PMU Governance|
|Public Health Research|
|Vulnerable Populations|
|Community-Based Research|
|Implementation Research|
|Demonstration Projects|

## **3B.3 SOP Features**

The SOP module should support:

- versioning;
- effective dates;
- superseded versions;
- approval workflows;
- downloadable PDFs;
- acknowledgment tracking;
- search and tagging;
- role-specific visibility.

---

## **3B.4 SOP Acknowledgement Workflow**

Before accessing reviewer functions, users should digitally acknowledge:

- confidentiality agreement
- conflict of interest policy
- relevant SOPs

The system should maintain:

- timestamped acknowledgements
- version history
- renewal reminders

# **3C. Research Ethics Training and Certification Module**

## **3C.1 Purpose**

IPH should institutionalize mandatory ethics orientation and competency assessment for:

- PIs & Co-Is
- students
- PMU 
- IEC members
- external collaborators

## **3C.2 Training Components**

The module should support:

|**Component**|**Description**|
|---|---|
|Video lectures|Recorded ethics modules|
|Reading material|SOPs/guidelines/manuals|
|MCQ assessments|Structured evaluation|
|Scenario-based questions|Ethics case discussions|
|Attempt tracking|Pass/fail monitoring|
|Certification workflow|Human-approved certificates|


## **3C.3 Training Categories**

Separate tracks should exist for:

|**Track**|
|---|
|General Human Research Ethics|
|Public Health Research Ethics|
|PMU and Administrative Data Governance|
|Vulnerable Populations|
|Implementation Research|
|Community Engagement|
|Clinical Research/GCP|
|IEC Member Orientation|
|Data Privacy and Confidentiality|
|AI/Digital Health Ethics|


## **3C.4 Mandatory Certification Rules**

The system should enforce:

|**Role**|**Requirement**|
|---|---|
|PI|Valid ethics certification mandatory|
|Co-I|Recommended or mandatory depending on study|
|IEC Member|Mandatory|
|PMU-linked researchers|Mandatory PMU governance module|


## **3C.5 Training Workflow**

```text
User Enrollment
→ Video Completion Tracking
→ MCQ Assessment
→ Score Evaluation
→ Human Review Queue
→ Certificate Approval
→ Certificate Generation
```


## **3C.6 MCQ and Assessment Engine**

Features:

- randomized questions;
- configurable passing threshold;
- time-limited attempts;
- question banks;
- scenario-based ethics questions;
- explanation feedback.


## **3C.7 Human Approval Layer**

Even after passing MCQs, certificates shall be issued upon apporoval/verification.

Instead:

```text
Passed Assessment
→ Pending Human Approval
→ IEC Admin / Member Secretary / Chair Review
→ Approve or Return for Reattempt
→ Certificate Issuance
```

This ensures:

- institutional accountability;
- prevention of superficial certification;
- contextual review where needed.

## **3C.8 Certificate Features**

Certificates should include:

- unique certificate ID
- QR verification code
- validity period
- training content
- issue date
- approving authority


## **3C.9 Certification Validity**

Recommended validity:

| **Certification**      | **Validity** |
| ---------------------- | ------------ |
| General Ethics         | 3 years      |
| GCP-related            | 3 years      |
| PMU Governance         | 2 years      |
| IEC Member Orientation | 2 years      |

Auto-reminders should trigger before expiry.


## **3C.10 Integration with Submission Workflow**

During submission:

The system should automatically validate:

- PI certification validity;
- required PMU modules;
- IEC member training status.

If invalid:

```text
Submission Blocked
OR
Conditional Submission Allowed
```

based on approval/exemption by Chair/Memb-sec/Dir?

# **STAGE 1 — ACCOUNT CREATION**

## **Workflow**

PI registers account.

Mandatory:

- institutional affiliation;
- designation;
- email verification;
- mobile verification;
- ORCID;
- CV upload.


# **STAGE 2 — NEW SUBMISSION**

## **Submission Types**

System should support:

- New proposal
- Amendment
- Continuing review
- SAE report
- Protocol deviation
- Study completion
- Site addition
- Multicentric collaboration
- Data access request
- Waiver request
- Exemption request

## **Dynamic Submission Forms**

Forms should adapt based on study type.

- can be based on IPH SOP or ICMR guideliens

## **Required Uploads**

Mandatory document matrix should include:

- protocol
- informed consent documents
- participant information sheet
- tools/questionnaires
- investigator CVs
- funding details
- COI declarations
- regulatory approvals
- collaboration MoUs
- PMU/government approvals where relevant

# **STAGE 3 — SECRETARIAT COMPLETENESS SCREENING**

## **Timeline**

Target:

- within 5 working days.

## **Secretariat Checklist**

Verify:

- all mandatory documents uploaded
- signatures complete
- translations attached
- consent forms appropriate
- funding declared
- PMU approvals attached if needed

Possible outcomes:

|**Outcome**|**Action**|
|---|---|
|Complete|Forward to Member Secretary|
|Minor deficiency|Return for correction|
|Major deficiency|Reject before review|


# **STAGE 4 — REVIEW CATEGORY DETERMINATION**

## **Conducted By**

Member Secretary + Secretariat.


## **Categories**

| **Category**              | **Description**                    |
| ------------------------- | ---------------------------------- |
| Exempt                    | Minimal/no-risk eligible proposals |
| Expedited                 | Minimal-risk review                |
| Full Committee            | More than minimal risk             |
| Emergency Review          | Disaster/emergency research        |
| PMU Governance Escalation | Operational/statuory implications  |


## **Automated Risk Flags**

System should auto-flag:

- vulnerable populations
- tribal/adivasi communities
- minors
- mental health populations
- biological samples
- geo-tagged data
- AI/algorithmic tools
- international collaboration
- government datasets
- intervention studies
- compensation requirements


# **STAGE 5 — REVIEWER ASSIGNMENT**

## **Member Secretary Assigns**

- primary reviewer;
- secondary reviewer;
- optional external expert.


## **Reviewer Access Rules**

Reviewers only access:

- assigned proposals;
- relevant attachments.

System logs:

- access timestamps;
- downloads;
- review submissions.


## **Conflict of Interest Workflow**

Before viewing documents:

- reviewer must declare:
    - no conflict;
    - potential conflict;
    - recusal.

Recused members lose access automatically.


# **STAGE 6 — PRE-MEETING REVIEW**

## **Reviewer Interface**

Structured review form including:

- scientific validity
- social valu
- participant risk
- benefit-risk assessment
- consent quality
- privacy/confidentiality
- compensation (if pplicable)
- vulnerable population safeguards
- community considerations
- implementation feasibility
- PMU/government implications

## **Output Types**

|**Recommendation**|
|---|
|Approve|
|Minor revision|
|Major revision|
|Defer|
|Reject|


# **STAGE 7 — IEC MEETING MANAGEMENT**

## **Agenda Automation**

System auto-generates:

- meeting agenda
- reviewer summaries
- protocol packet
- attendance sheet
- conflict declarations


## **Quorum Logic**

System should validate quorum before decision recording OR memb-sec confirms quorum

Required:

- minimum members;
- medical + non-medical representation;
- non-affiliated member;
- preferably lay representation.

No decision can be finalized without quorum validation.


## **Meeting Workflow**

During meeting:

- proposal presentation
- reviewer comments
- PI clarification (if invited)
- discussion
- decision recording

PI excluded during final decision-making.


## **Decision Categories**

|**Decision**|**Workflow**|
|---|---|
|Approved|Approval letter generation|
|Minor Revision|Secretariat review after response|
|Major Revision|Return to full committee|
|Deferred|Additional information requested|
|Rejected|Closure with reasons|


# **STAGE 8 — COMMUNICATION**

## **Automated Letter Generation**

Templates:

- approval
- conditional approval
- revision request
- rejection
- continuing review reminder
- SAE acknowledgement


## **Digital Signatures**

Chairperson/Member Secretary approval via:

- digital signature;
- authenticated approval workflow.


# **STAGE 9 — POST-APPROVAL MANAGEMENT**

## **Continuing Review Tracking**

System auto-tracks:

- annual review dates
- quarterly monitoring where required
- study expiry

Auto-reminders:

- 60 days
- 30 days
- 7 days before expiry


## **Amendment Workflow**

PI submits:

- revised documents
- change summary
- justification

System determines:

- expedited vs full review.

## **SAE Reporting Workflow**

Mandatory fields:

- event description
- causality
- severity
- management
- compensation status

Auto-escalation:

- Chairperson
- Member Secretary
- SAE subcommittee



## **Protocol Deviation Workflow**

Deviation categories:

- minor
- major
- serious non-compliance

System supports:

- correction action/mitigation tracking
- escalation
- monitoring recommendations

# **STAGE 10 — SITE MONITORING**

## **Monitoring Types**

|**Type**|**Trigger**|
|---|---|
|Routine|Scheduled|
|For Cause|SAE/deviation/complaint|
|PMU Operational Monitoring|Programme-sensitive studies|


## **Monitoring Module**

Monitors can:

- upload reports
- upload photos/documents
- record observations
- assign corrective actions to be taken based on assessment of SAEs/reports to PI


# **STAGE 11 — STUDY CLOSURE**

## **Closure Requirements**

PI uploads:

- final report
- dissemination summary
- publications
- data deposit summary

## **PMU-Specific Closure**

For all studies:

- programme dissemination note
- district/parnter/collaborator feedback summary
- implementation lessons
- policy implications


# **STAGE 12 — ARCHIVAL**

## **Retention Rules**

| **Study Type**    | **Retention**   |
| ----------------- | --------------- |
| General studies   | Minimum 3 years |
| Regulatory trials | Minimum 5 years |
|                   |                 |


## **Archival Features**

- immutable archive
- encrypted storage
- indexed retrieval
- audit logs
- restricted access


# **8. Workflow State Machine**

## **Core States**

```text
Draft
→ Submitted
→ Completeness Screening
→ Returned for Clarification
→ Under Review
→ Reviewer Assignment
→ Scheduled for Meeting
→ IEC Decision Pending
→ Approved
→ Conditionally Approved
→ Major Revision Required
→ Deferred
→ Rejected
→ Active Study
→ Continuing Review
→ Closed
→ Archived
```


# **9. PMU-Specific Special Logic**

## **High-Sensitivity Flagging**

Automatic escalation if proposal involves:

- government data/surveillance systems
- district comparative performance
- vulnerable or stigmatized populations
- AI/algorithmic governance
- large-scale implementation pilots
- inter-state datasets
- external donor reporting

## **Data Governance Controls**

Mandatory:

- data sharing agreement
- de-identification plan
- access logging
- role-based download permissions


# **10. Dashboards**

## **Secretariat Dashboard**

Displays:

- pending submissions
- upcoming reviews
- overdue actions
- incomplete applications


## **Chairperson Dashboard**

Displays:

- pending approvals
- quorum alerts
- escalated protocols
- SAE notifications


## **PMU Dashboard**

Displays:

- PMU-linked studies
- district distribution
- operational burden
- government collaboration studies
- SAEs and mitigation status


# **11. Analytics Layer**

## **Institutional Metrics**

Track:

- turnaround time
- review duration
- number of active studies
- vulnerable population studies
- implementation research volume
- PMU-linked activities
- protocol deviations
- SAE trends


# **12. Security and Compliance**

## **Mandatory Controls**

- encrypted HTTPS
- role-based permissions
- audit logs
- immutable timestamps
- secure password policies
- optional two-factor authentication
- automatic backups
- versioned document history

# **13. Recommended Directus Data Model**

## **Core Collections**

- users
- investigators
- institutions
- proposals
- proposal_versions
- review_assignments
- reviews
- IEC_meetings
- decisions
- amendments
- SAE_reports
- protocol_deviations
- monitoring_visits
- continuing_reviews
- PMU_clearances
- documents
- communications
- audit_logs
- archival_records


# **14. Recommended Implementation Phases**

## **Phase 1 — Core Submission System**

Timeline:  
6–8 weeks.

Includes:

- accounts
- submissions
- uploads
- review workflow
- meetings
- approval letters

## **Phase 2 — Monitoring + PMU Integration**

Includes:

- continuing review
- SAE workflows
- corrective action;
- PMU governance layer
- dashboards.


## **Phase 3 — Advanced Governance**

Includes:

- analytics
- interoperability APIs
- digital signatures
- advanced archival
- mobile optimization


**Plan**

Implement:

- Directus
- PostgreSQL
- MinIO/S3
- Docker-based deployment

with the workflow architecture described above.

If IPH later requires:

- multi-institutional federation
- at scale interoperability
- advanced regulatory workflows
- complex automation

then migrate incrementally toward Django-based custom governance platform.

Last updated: 2026-05-13 21:32